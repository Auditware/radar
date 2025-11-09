#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::call::RawCall;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn make_call(&self, target: Address, data: alloc::vec::Vec<u8>) {
        RawCall::new().call(target, &data); // VULN: Using RawCall without error handling
    }
}
