#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use alloy_primitives::keccak256;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn generate_authority(&self) -> Address {
        let unique_bytes = keccak256(b"random"); // VULN: Generating random authority bypasses proper validation
        Address::from_slice(&unique_bytes[0..20])
    }
}
