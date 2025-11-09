#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use alloy_primitives::U256;

#[storage]
#[entrypoint]
pub struct Contract {
    balance: StorageU256,
}

#[public]
impl Contract {
    pub fn add(&mut self, amount: U256) -> U256 {
        self.balance.set(self.balance.get() + amount); // VULN: Unchecked addition can overflow
        self.balance.get()
    }
}
