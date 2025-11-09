#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Pool {
    fee_rate: U256,
}

#[public]
impl Pool {
    pub fn set_fee_rate(&mut self, new_fee_rate: U256) { // VULN: No validation on fee assignment
        self.fee_rate.set(new_fee_rate);
    }
}
