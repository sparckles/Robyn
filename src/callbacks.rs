use pyo3::{IntoPyObjectExt, exceptions::PyStopIteration, prelude::*};
use std::sync::{Arc, OnceLock, RwLock, atomic};
use tokio::sync::Notify;

use crate::conversion::FutureResultToPy;

#[pyclass(frozen, freelist = 128, module = "robyn._robyn")]
pub(crate) struct PyEmptyAwaitable;

#[pymethods]
impl PyEmptyAwaitable {
    fn __await__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }

    fn __iter__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }

    fn __next__(&self) -> Option<()> {
        None
    }
}

#[pyclass(frozen, module = "robyn._robyn")]
pub(crate) struct PyDoneAwaitable {
    result: PyResult<Py<PyAny>>,
}

impl PyDoneAwaitable {
    pub(crate) fn new(result: PyResult<Py<PyAny>>) -> Self {
        Self { result }
    }
}

#[pymethods]
impl PyDoneAwaitable {
    fn __await__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }

    fn __iter__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }

    fn __next__(&self, py: Python) -> PyResult<Py<PyAny>> {
        self.result
            .as_ref()
            .map_err(|v| v.clone_ref(py))
            .map(|v| Err(PyStopIteration::new_err(v.clone_ref(py))))?
    }
}

#[pyclass(frozen, module = "robyn._robyn")]
pub(crate) struct PyErrAwaitable {
    result: PyResult<()>,
}

impl PyErrAwaitable {
    pub(crate) fn new(result: PyResult<()>) -> Self {
        Self { result }
    }
}

#[pymethods]
impl PyErrAwaitable {
    fn __await__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }

    fn __iter__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }

    fn __next__(&self, py: Python) -> PyResult<()> {
        Err(self.result.as_ref().err().unwrap().clone_ref(py))
    }
}

#[pyclass(frozen, module = "robyn._robyn")]
pub(crate) struct PyIterAwaitable {
    result: OnceLock<PyResult<Py<PyAny>>>,
}

impl PyIterAwaitable {
    pub(crate) fn new() -> Self {
        Self {
            result: OnceLock::new(),
        }
    }

    #[inline]
    pub(crate) fn set_result(pyself: Py<Self>, py: Python, result: FutureResultToPy) {
        _ = pyself.get().result.set(result.into_pyobject(py).map(Bound::unbind));
        pyself.drop_ref(py);
    }
}

#[pymethods]
impl PyIterAwaitable {
    fn __await__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }

    fn __iter__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }

    fn __next__(&self, py: Python) -> PyResult<Option<Py<PyAny>>> {
        if let Some(res) = self.result.get() {
            return res
                .as_ref()
                .map_err(|err| err.clone_ref(py))
                .map(|v| Err(PyStopIteration::new_err(v.clone_ref(py))))?;
        }

        Ok(Some(py.None()))
    }
}

#[repr(u8)]
enum PyFutureAwaitableState {
    Pending = 0,
    Completed = 1,
    Cancelled = 2,
}

#[pyclass(frozen, module = "robyn._robyn")]
pub(crate) struct PyFutureAwaitable {
    state: atomic::AtomicU8,
    result: OnceLock<PyResult<Py<PyAny>>>,
    event_loop: Py<PyAny>,
    cancel_tx: Arc<Notify>,
    cancel_msg: OnceLock<Py<PyAny>>,
    py_block: atomic::AtomicBool,
    ack: RwLock<Option<(Py<PyAny>, Py<pyo3::types::PyDict>)>>,
}

impl PyFutureAwaitable {
    pub(crate) fn new(event_loop: Py<PyAny>) -> Self {
        Self {
            state: atomic::AtomicU8::new(PyFutureAwaitableState::Pending as u8),
            result: OnceLock::new(),
            event_loop,
            cancel_tx: Arc::new(Notify::new()),
            cancel_msg: OnceLock::new(),
            py_block: true.into(),
            ack: RwLock::new(None),
        }
    }

    pub fn to_spawn(self, py: Python) -> PyResult<(Py<PyFutureAwaitable>, Arc<Notify>)> {
        let cancel_tx = self.cancel_tx.clone();
        Ok((Py::new(py, self)?, cancel_tx))
    }

    pub(crate) fn set_result(pyself: Py<Self>, py: Python, result: FutureResultToPy) {
        let rself = pyself.get();

        _ = rself.result.set(result.into_pyobject(py).map(Bound::unbind));
        if rself
            .state
            .compare_exchange(
                PyFutureAwaitableState::Pending as u8,
                PyFutureAwaitableState::Completed as u8,
                atomic::Ordering::Release,
                atomic::Ordering::Relaxed,
            )
            .is_err()
        {
            pyself.drop_ref(py);
            return;
        }

        {
            let ack = rself.ack.read().unwrap();
            if let Some((cb, ctx)) = &*ack {
                _ = rself.event_loop.clone_ref(py).call_method(
                    py,
                    pyo3::intern!(py, "call_soon_threadsafe"),
                    (cb, pyself.clone_ref(py)),
                    Some(ctx.bind(py)),
                );
            }
        }
        pyself.drop_ref(py);
    }
}

#[pymethods]
impl PyFutureAwaitable {
    fn __await__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }
    fn __iter__(pyself: PyRef<'_, Self>) -> PyRef<'_, Self> {
        pyself
    }

    fn __next__(pyself: PyRef<'_, Self>) -> PyResult<Option<PyRef<'_, Self>>> {
        if pyself.state.load(atomic::Ordering::Acquire) == PyFutureAwaitableState::Completed as u8 {
            let py = pyself.py();
            return pyself
                .result
                .get()
                .unwrap()
                .as_ref()
                .map_err(|err| err.clone_ref(py))
                .map(|v| Err(PyStopIteration::new_err(v.clone_ref(py))))?;
        }

        Ok(Some(pyself))
    }

    #[getter(_asyncio_future_blocking)]
    fn get_block(&self) -> bool {
        self.py_block.load(atomic::Ordering::Relaxed)
    }

    #[setter(_asyncio_future_blocking)]
    fn set_block(&self, val: bool) {
        self.py_block.store(val, atomic::Ordering::Relaxed);
    }

    fn get_loop(&self, py: Python) -> Py<PyAny> {
        self.event_loop.clone_ref(py)
    }

    #[pyo3(signature = (cb, context=None))]
    fn add_done_callback(pyself: PyRef<'_, Self>, cb: Py<PyAny>, context: Option<Py<PyAny>>) -> PyResult<()> {
        let py = pyself.py();
        let kwctx = pyo3::types::PyDict::new(py);
        kwctx.set_item(pyo3::intern!(py, "context"), context)?;

        let state = pyself.state.load(atomic::Ordering::Acquire);
        if state == PyFutureAwaitableState::Pending as u8 {
            let mut ack = pyself.ack.write().unwrap();
            *ack = Some((cb, kwctx.unbind()));
        } else {
            let event_loop = pyself.event_loop.clone_ref(py);
            event_loop.call_method(py, pyo3::intern!(py, "call_soon"), (cb, pyself), Some(&kwctx))?;
        }

        Ok(())
    }

    #[allow(unused)]
    fn remove_done_callback(&self, cb: Py<PyAny>) -> i32 {
        let mut ack = self.ack.write().unwrap();
        *ack = None;
        1
    }

    #[allow(unused)]
    #[pyo3(signature = (msg=None))]
    fn cancel(pyself: PyRef<'_, Self>, msg: Option<Py<PyAny>>) -> bool {
        if pyself
            .state
            .compare_exchange(
                PyFutureAwaitableState::Pending as u8,
                PyFutureAwaitableState::Cancelled as u8,
                atomic::Ordering::Release,
                atomic::Ordering::Relaxed,
            )
            .is_err()
        {
            return false;
        }

        if let Some(cancel_msg) = msg {
            _ = pyself.cancel_msg.set(cancel_msg);
        }
        pyself.cancel_tx.notify_one();

        let ack = pyself.ack.read().unwrap();
        if let Some((cb, ctx)) = &*ack {
            let py = pyself.py();
            let event_loop = pyself.event_loop.clone_ref(py);
            let cb = cb.clone_ref(py);
            let ctx = ctx.clone_ref(py);
            drop(ack);

            let _ = event_loop.call_method(py, pyo3::intern!(py, "call_soon"), (cb, pyself), Some(ctx.bind(py)));
        }

        true
    }

    fn done(&self) -> bool {
        self.state.load(atomic::Ordering::Acquire) != PyFutureAwaitableState::Pending as u8
    }

    fn result(&self, py: Python) -> PyResult<Py<PyAny>> {
        let state = self.state.load(atomic::Ordering::Acquire);

        if state == PyFutureAwaitableState::Completed as u8 {
            return self
                .result
                .get()
                .unwrap()
                .as_ref()
                .map(|v| v.clone_ref(py))
                .map_err(|err| err.clone_ref(py));
        }
        if state == PyFutureAwaitableState::Cancelled as u8 {
            let msg = self
                .cancel_msg
                .get()
                .unwrap_or(&"Future cancelled.".into_py_any(py).unwrap())
                .clone_ref(py);
            return Err(pyo3::exceptions::asyncio::CancelledError::new_err(msg));
        }
        Err(pyo3::exceptions::asyncio::InvalidStateError::new_err(
            "Result is not ready.",
        ))
    }

    fn exception(&self, py: Python) -> PyResult<Py<PyAny>> {
        let state = self.state.load(atomic::Ordering::Acquire);

        if state == PyFutureAwaitableState::Completed as u8 {
            return self
                .result
                .get()
                .unwrap()
                .as_ref()
                .map(|_| py.None())
                .map_err(|err| err.clone_ref(py));
        }
        if state == PyFutureAwaitableState::Cancelled as u8 {
            let msg = self
                .cancel_msg
                .get()
                .unwrap_or(&"Future cancelled.".into_py_any(py).unwrap())
                .clone_ref(py);
            return Err(pyo3::exceptions::asyncio::CancelledError::new_err(msg));
        }
        Err(pyo3::exceptions::asyncio::InvalidStateError::new_err(
            "Exception is not set.",
        ))
    }
}

#[pyclass(frozen)]
pub(crate) struct PyFutureDoneCallback {
    pub cancel_tx: Arc<Notify>,
}

#[pymethods]
impl PyFutureDoneCallback {
    pub fn __call__(&self, fut: Bound<PyAny>) -> PyResult<()> {
        let py = fut.py();

        if { fut.getattr(pyo3::intern!(py, "cancelled"))?.call0()?.is_truthy() }.unwrap_or(false) {
            self.cancel_tx.notify_one();
        }

        Ok(())
    }
}

#[pyclass(frozen)]
pub(crate) struct PyFutureResultSetter;

#[pymethods]
impl PyFutureResultSetter {
    pub fn __call__(&self, target: Bound<PyAny>, value: Bound<PyAny>) {
        let _ = target.call1((value,));
    }
}

