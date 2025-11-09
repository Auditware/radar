#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Contract {
    accounts: StorageMap<Address, U256>,
}

#[public]
impl Contract {
    pub fn transfer(&mut self, from: Address, to: Address, amount: U256) -> Result<(), Vec<u8>> {
        if from != msg::sender() { // FIX: Validates sender authorization
            return Err(vec![1]);
        }
        let balance = self.accounts.get(from);
        self.accounts.insert(from, balance - amount);
        self.accounts.insert(to, self.accounts.get(to) + amount);
        Ok(())
    }
}
