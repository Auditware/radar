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
    pub fn initialize(&mut self, owner: Address) { // VULN: No reinitialization check - can be called multiple times
        self.owner.set(owner);
        self.initialized.set(true);
    }
}
