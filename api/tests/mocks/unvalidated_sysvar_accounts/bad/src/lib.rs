#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::block;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn get_timestamp(&self) -> U256 {
        U256::from(block::timestamp()) // VULN: Using sysvar without validating source
    }
}
