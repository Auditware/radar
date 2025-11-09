#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Token {
    balances: StorageMap<Address, U256>,
}

#[public]
impl Token {
    pub fn transfer(&mut self, to: Address, amount: U256) -> Result<(), Vec<u8>> {
        let sender_balance = self.balances.get(msg::sender());
        if amount > sender_balance { // FIX: Validates sufficient balance
            return Err(vec![1]);
        }
        self.balances.insert(msg::sender(), sender_balance - amount);
        let recipient_balance = self.balances.get(to);
        self.balances.insert(to, recipient_balance + amount);
        Ok(())
    }
}
