#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn calculate(&self, amount: U256, divisor: U256) -> Result<U256, Vec<u8>> {
        amount.checked_div(divisor).ok_or(vec![1]) // FIX: checked_div prevents panic
    }
}
