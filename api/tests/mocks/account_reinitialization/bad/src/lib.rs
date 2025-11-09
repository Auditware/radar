#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    initialized: StorageBool,
    owner: Address,
}

#[public]
impl Contract {
    pub fn initialize(&mut self, owner: Address) { // VULN: Can be called multiple times to reinitialize
        self.owner.set(owner);
        self.initialized.set(true);
    }
}
