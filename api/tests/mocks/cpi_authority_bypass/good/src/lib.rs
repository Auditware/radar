#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Contract {
    authority: Address,
}

#[public]
impl Contract {
    pub fn set_authority(&mut self, new_authority: Address) -> Result<(), Vec<u8>> {
        if msg::sender() != self.authority.get() { // FIX: Proper authority validation
            return Err(vec![1]);
        }
        self.authority.set(new_authority);
        Ok(())
    }
}
