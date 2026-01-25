use pyo3::prelude::*;

// Adapted for robyn - returns Py<PyAny> directly
pub(crate) enum FutureResultToPy {
    None,
    Err(PyResult<()>),
    Value(Py<PyAny>),
}

impl<'p> IntoPyObject<'p> for FutureResultToPy {
    type Target = PyAny;
    type Output = Bound<'p, Self::Target>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'p>) -> Result<Self::Output, Self::Error> {
        match self {
            Self::None => Ok(py.None().into_bound(py)),
            Self::Err(res) => Err(res.err().unwrap()),
            Self::Value(val) => {
                let bound = val.bind(py);
                Ok(bound.clone())
            },
        }
    }
}

