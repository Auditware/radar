#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Token {
    total_supply: U256,
}

#[public]
impl Token {
    pub fn mint(&mut self, amount: U256) -> U256 { // VULN: No access control - anyone can mint
        let new_supply = self.total_supply.get() + amount;
        self.total_supply.set(new_supply);
        new_supply
    }
}
