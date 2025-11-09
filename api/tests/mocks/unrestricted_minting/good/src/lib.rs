#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Token {
    owner: Address,
    total_supply: U256,
}

#[public]
impl Token {
    pub fn mint(&mut self, amount: U256) -> Result<U256, Vec<u8>> {
        if msg::sender() != self.owner.get() { // FIX: Only owner can mint
            return Err(vec![1]);
        }
        let new_supply = self.total_supply.get() + amount;
        self.total_supply.set(new_supply);
        Ok(new_supply)
    }
}
