// Derived from Granian (https://github.com/emmett-framework/granian)
// Copyright 2021 Giovanni Barillari
// Licensed under the BSD 3-Clause License
// See: https://github.com/emmett-framework/granian/blob/master/LICENSE

use pyo3::prelude::*;
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
            }
        }
    }
}
