#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn calculate_shares(&self, total: U256, divisor: U256) -> U256 {
        (total + divisor - U256::from(1)) / divisor // FIX: Ceiling division rounds up
    }
}
