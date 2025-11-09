#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Pool {
    balance: U256,
}

#[public]
impl Pool {
    pub fn swap(&mut self, amount: U256) -> U256 {
        let balance = self.balance.get(); // VULN: Using balance instead of reserves allows price manipulation
        balance * amount
    }
}
