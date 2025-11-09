#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use alloc::vec::Vec;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn validate(&self, values: Vec<U256>) -> Result<(), Vec<u8>> {
        for val in values.iter() {
            if *val == U256::from(0) {
                break; // VULN: break exits early, skipping remaining validation
            }
        }
        Ok(())
    }
}
