use pyo3::{IntoPyObjectExt, prelude::*};
use std::{
    future::Future,
    sync::Arc,
};
use tokio::{
    runtime::Builder as RuntimeBuilder,
    task::JoinHandle,
};
use futures::FutureExt;

#[cfg(unix)]
use super::callbacks::PyFutureAwaitable;
#[cfg(windows)]
use super::callbacks::{PyFutureDoneCallback, PyFutureResultSetter};

use super::blocking::BlockingRunner;
use super::callbacks::{PyDoneAwaitable, PyEmptyAwaitable, PyErrAwaitable, PyIterAwaitable};
use super::conversion::FutureResultToPy;

pub trait JoinError {
    #[allow(dead_code)]
    fn is_panic(&self) -> bool;
}

pub trait Runtime: Send + 'static {
    type JoinError: JoinError + Send;
    type JoinHandle: Future<Output = Result<(), Self::JoinError>> + Send;

    fn spawn<F>(&self, fut: F) -> Self::JoinHandle
    where
        F: Future<Output = ()> + Send + 'static;

    fn spawn_blocking<F>(&self, task: F)
    where
        F: FnOnce(Python) + Send + 'static;
}

pub trait ContextExt: Runtime {
    fn py_event_loop(&self, py: Python) -> Py<PyAny>;
}

pub(crate) struct RuntimeWrapper {
    pub inner: tokio::runtime::Runtime,
    br: Arc<BlockingRunner>,
    pr: Arc<Py<PyAny>>,
}

impl RuntimeWrapper {
    pub fn new(
        blocking_threads: usize,
        py_threads: usize,
        py_threads_idle_timeout: u64,
        py_loop: Arc<Py<PyAny>>,
    ) -> Self {
        Self {
            inner: default_runtime(blocking_threads),
            br: BlockingRunner::new(py_threads, py_threads_idle_timeout).into(),
            pr: py_loop,
        }
    }

    pub fn with_runtime(
        rt: tokio::runtime::Runtime,
        py_threads: usize,
        py_threads_idle_timeout: u64,
        py_loop: Arc<Py<PyAny>>,
    ) -> Self {
        Self {
            inner: rt,
            br: BlockingRunner::new(py_threads, py_threads_idle_timeout).into(),
            pr: py_loop,
        }
    }

    pub fn handler(&self) -> RuntimeRef {
        RuntimeRef::new(self.inner.handle().clone(), self.br.clone(), self.pr.clone())
    }
}

#[derive(Clone)]
pub struct RuntimeRef {
    pub inner: tokio::runtime::Handle,
    innerb: Arc<BlockingRunner>,
    innerp: Arc<Py<PyAny>>,
}

impl RuntimeRef {
    pub fn new(rt: tokio::runtime::Handle, br: Arc<BlockingRunner>, pyloop: Arc<Py<PyAny>>) -> Self {
        Self {
            inner: rt,
            innerb: br,
            innerp: pyloop,
        }
    }
}

impl JoinError for tokio::task::JoinError {
    fn is_panic(&self) -> bool {
        tokio::task::JoinError::is_panic(self)
    }
}

impl Runtime for RuntimeRef {
    type JoinError = tokio::task::JoinError;
    type JoinHandle = JoinHandle<()>;

    fn spawn<F>(&self, fut: F) -> Self::JoinHandle
    where
        F: Future<Output = ()> + Send + 'static,
    {
        self.inner.spawn(fut)
    }

    #[inline]
    fn spawn_blocking<F>(&self, task: F)
    where
        F: FnOnce(Python) + Send + 'static,
    {
        _ = self.innerb.run(task);
    }
}

impl ContextExt for RuntimeRef {
    fn py_event_loop(&self, py: Python) -> Py<PyAny> {
        self.innerp.clone_ref(py)
    }
}

fn default_runtime(blocking_threads: usize) -> tokio::runtime::Runtime {
    RuntimeBuilder::new_current_thread()
        .max_blocking_threads(blocking_threads)
        .enable_all()
        .build()
        .unwrap()
}

#[inline(always)]
pub(crate) fn empty_future_into_py(py: Python) -> PyResult<Bound<PyAny>> {
    PyEmptyAwaitable.into_bound_py_any(py)
}

#[inline(always)]
pub(crate) fn done_future_into_py(py: Python, result: PyResult<Py<PyAny>>) -> PyResult<Bound<PyAny>> {
    PyDoneAwaitable::new(result).into_bound_py_any(py)
}

#[inline(always)]
pub(crate) fn err_future_into_py(py: Python, err: PyResult<()>) -> PyResult<Bound<PyAny>> {
    PyErrAwaitable::new(err).into_bound_py_any(py)
}

// NOTE: ~55% faster than pyo3_asyncio.future_into_py
#[allow(dead_code, unused_must_use)]
pub(crate) fn future_into_py_iter<R, F>(rt: R, py: Python, fut: F) -> PyResult<Bound<PyAny>>
where
    R: Runtime + ContextExt + Clone,
    F: Future<Output = FutureResultToPy> + Send + 'static,
{
    let aw = Py::new(py, PyIterAwaitable::new())?;
    let py_fut = aw.clone_ref(py);
    let rth = rt.clone();

    rt.spawn(async move {
        let result = fut.await;
        rth.spawn_blocking(move |py| PyIterAwaitable::set_result(aw, py, result));
    });

    Ok(py_fut.into_any().into_bound(py))
}

// NOTE: ~38% faster than pyo3_asyncio.future_into_py
#[allow(unused_must_use)]
#[cfg(unix)]
pub(crate) fn future_into_py_futlike<R, F>(rt: R, py: Python, fut: F) -> PyResult<Bound<PyAny>>
where
    R: Runtime + ContextExt + Clone,
    F: Future<Output = FutureResultToPy> + Send + 'static,
{
    let event_loop = rt.py_event_loop(py);
    let (aw, cancel_tx) = PyFutureAwaitable::new(event_loop).to_spawn(py)?;
    let py_fut = aw.clone_ref(py);
    let rth = rt.clone();

    rt.spawn(async move {
        tokio::select! {
            biased;
            result = fut => rth.spawn_blocking(move |py| PyFutureAwaitable::set_result(aw, py, result)),
            () = cancel_tx.notified() => rth.spawn_blocking(move |py| aw.drop_ref(py)),
        }
    });

    Ok(py_fut.into_any().into_bound(py))
}

#[allow(unused_must_use)]
#[cfg(windows)]
pub(crate) fn future_into_py_futlike<R, F>(rt: R, py: Python, fut: F) -> PyResult<Bound<PyAny>>
where
    R: Runtime + ContextExt + Clone,
    F: Future<Output = FutureResultToPy> + Send + 'static,
{
    let event_loop = rt.py_event_loop(py);
    let event_loop_ref = event_loop.clone_ref(py);
    let cancel_tx = Arc::new(tokio::sync::Notify::new());
    let rth = rt.clone();

    let py_fut = event_loop.call_method0(py, pyo3::intern!(py, "create_future"))?;
    py_fut.call_method1(
        py,
        pyo3::intern!(py, "add_done_callback"),
        (PyFutureDoneCallback {
            cancel_tx: cancel_tx.clone(),
        },),
    )?;
    let fut_ref = py_fut.clone_ref(py);

    rt.spawn(async move {
        tokio::select! {
            biased;
            result = fut => {
                rth.spawn_blocking(move |py| {
                    let pyres = result.into_pyobject(py).map(Bound::unbind);
                    let (cb, value) = match pyres {
                        Ok(val) => (fut_ref.getattr(py, pyo3::intern!(py, "set_result")).unwrap(), val),
                        Err(err) => (fut_ref.getattr(py, pyo3::intern!(py, "set_exception")).unwrap(), err.into_py_any(py).unwrap())
                    };
                    let _ = event_loop_ref.call_method1(py, pyo3::intern!(py, "call_soon_threadsafe"), (PyFutureResultSetter, cb, value));
                    fut_ref.drop_ref(py);
                    event_loop_ref.drop_ref(py);
                });
            },
            () = cancel_tx.notified() => {
                rth.spawn_blocking(move |py| {
                    fut_ref.drop_ref(py);
                    event_loop_ref.drop_ref(py);
                });
            }
        }
    });

    Ok(py_fut.into_bound(py))
}

// Wrapper function to replace pyo3_async_runtimes::tokio::future_into_py
// This function matches the signature and converts Result<T, E> to FutureResultToPy
pub fn future_into_py<F>(py: Python, fut: F) -> PyResult<Bound<PyAny>>
where
    F: Future<Output = Result<(), anyhow::Error>> + Send + 'static,
{
    // Try to get the tokio runtime handle
    // When called from Python code, we might not be in a tokio async context
    // So we try try_current() first, and if that fails, fall back to pyo3_async_runtimes
    match tokio::runtime::Handle::try_current() {
        Ok(rt_handle) => {
            // We have a handle, use our optimized implementation
            // Get the event loop from Python
            let asyncio = py.import("asyncio")?;
            let event_loop = asyncio.call_method0("get_event_loop")
                .or_else(|_| asyncio.call_method0("new_event_loop"))?;
            let event_loop: Py<PyAny> = event_loop.unbind();

            // Create a simple blocking runner (1 thread, 30s timeout)
            let blocking_runner = Arc::new(BlockingRunner::new(1, 30));
            
            // Create RuntimeRef
            let rt_ref = RuntimeRef::new(rt_handle, blocking_runner, Arc::new(event_loop));

            // Convert the future to use FutureResultToPy
            let wrapped_fut = async move {
                match fut.await {
                    Ok(()) => FutureResultToPy::None,
                    Err(e) => FutureResultToPy::Err(Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        format!("Future error: {}", e)
                    ))),
                }
            };

            // Use the futlike implementation (better for most cases)
            future_into_py_futlike(rt_ref, py, wrapped_fut)
        }
        Err(_) => {
            // Fall back to pyo3_async_runtimes when we can't get the handle
            // This happens when called from Python code that's not in a tokio async context
            // Convert Result<(), anyhow::Error> to PyResult<()> for pyo3_async_runtimes
            let py_fut = fut.map(|result| {
                result.map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    format!("Future error: {}", e)
                ))
            });
            pyo3_async_runtimes::tokio::future_into_py(py, py_fut)
        }
    }
}

