/*
    build with cargo and place the .so as rust_syn.so in working directory
    then, from python:
    
    import rust_syn
    ast_json = rust_syn.parse_rust_to_ast(rust_code)
*/

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use pyo3::types::PyModule;
use pyo3::types::PyModule as _PyModule;
use syn::{parse_str, File};
use syn_serde::json;

#[pyfunction]
fn parse_rust_to_ast(rust_code: String) -> PyResult<String> {
    let syn_file: File = parse_str(&rust_code)
        .map_err(|e| PyErr::new::<PyValueError, _>(format!("Error parsing Rust code: {}", e)))?;
    let json_string = json::to_string_pretty(&syn_file);
    Ok(json_string)
}


#[pymodule]
fn rust_syn(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_rust_to_ast, m)?)?;
    Ok(())
}