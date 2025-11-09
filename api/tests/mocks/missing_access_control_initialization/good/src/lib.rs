#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    owner: Address,
    initialized: StorageBool,
}

#[public]
impl Contract {
    pub fn initialize(&mut self, owner: Address) -> Result<(), Vec<u8>> {
        if self.initialized.get() { // FIX: Prevents reinitialization
            return Err(vec![1]);
        }
        self.owner.set(owner);
        self.initialized.set(true);
        Ok(())
    }
}
