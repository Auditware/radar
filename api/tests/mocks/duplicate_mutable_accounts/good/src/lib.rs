#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    balances: StorageMap<Address, U256>,
}

#[public]
impl Contract {
    pub fn transfer(&mut self, from: Address, to: Address, amount: U256) -> Result<(), Vec<u8>> {
        if from == to { // FIX: Prevents duplicate account usage
            return Err(vec![1]);
        }
        let bal_from = self.balances.get(from);
        self.balances.insert(from, bal_from - amount);
        let bal_to = self.balances.get(to);
        self.balances.insert(to, bal_to + amount);
        Ok(())
    }
}
