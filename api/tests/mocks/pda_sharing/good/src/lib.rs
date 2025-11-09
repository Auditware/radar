#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Contract {
    vault: StorageMap<Address, U256>,
}

#[public]
impl Contract {
    pub fn transfer(&mut self, from: Address, to: Address, amount: U256) -> Result<(), Vec<u8>> {
        if msg::sender() != from { // FIX: Validates sender authority for PDA
            return Err(vec![1]);
        }
        let from_balance = self.vault.get(from);
        self.vault.insert(from, from_balance - amount);
        let to_balance = self.vault.get(to);
        self.vault.insert(to, to_balance + amount);
        Ok(())
    }
}
