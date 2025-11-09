#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use alloc::vec::Vec;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn deserialize(&self, data: Vec<u8>) -> U256 {
        U256::try_from_be_slice(&data).unwrap_or(U256::from(0)) // VULN: No discriminator check on deserialization
    }
}
