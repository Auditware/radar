#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::call::Call;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn make_call(&self, target: Address, data: alloc::vec::Vec<u8>) -> Result<(), Vec<u8>> {
        Call::new().call(target, &data)?; // FIX: Using Call with proper error handling
        Ok(())
    }
}
