#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use alloc::vec::Vec;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn calculate(&self, data: Vec<U256>) -> U256 {
        let mut result = U256::from(0);
        for i in data.iter() { // VULN: Nested iteration with multiplication causes exponential complexity
            for j in data.iter() {
                result = result + (*i * *j);
            }
        }
        result
    }
}
