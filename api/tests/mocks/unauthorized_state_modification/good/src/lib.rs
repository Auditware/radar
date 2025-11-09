#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Contract {
    owner: Address,
    value: U256,
}

#[public]
impl Contract {
    pub fn set_value(&mut self, new_value: U256) -> Result<(), Vec<u8>> {
        if msg::sender() != self.owner.get() { // FIX: Only owner can modify state
            return Err(vec![1]);
        }
        self.value.set(new_value);
        Ok(())
    }
}
