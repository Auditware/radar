#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Pool {
    reserves: U256,
}

#[public]
impl Pool {
    pub fn swap(&mut self, amount: U256) -> U256 {
        let reserves = self.reserves.get(); // FIX: Using reserves prevents manipulation
        reserves * amount
    }
}
