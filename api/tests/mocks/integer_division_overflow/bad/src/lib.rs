#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn calculate(&self, amount: U256, divisor: U256) -> U256 {
        amount / divisor // VULN: Unchecked division can panic on divide-by-zero
    }
}
