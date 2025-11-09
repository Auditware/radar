#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    max_supply: U256,
}

#[public]
impl Contract {
    pub fn check_limit(&self, amount: U256) -> Result<(), Vec<u8>> {
        if amount < self.max_supply.get() { // VULN: Should be <= for inclusive limit check
            return Err(vec![1]);
        }
        Ok(())
    }
}
