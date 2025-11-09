#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    balance: U256,
}

#[public]
impl Contract {
    pub fn add(&mut self, amount: U256) -> Result<U256, Vec<u8>> {
        let new_balance = self.balance.get().checked_add(amount).ok_or(vec![1])?; // FIX: checked_add prevents overflow
        self.balance.set(new_balance);
        Ok(self.balance.get())
    }
}
