#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn calculate_fee(&self, amount: U256) -> U256 {
        (amount * U256::from(3)) / U256::from(100) // FIX: Multiplication before division preserves precision
    }
}
