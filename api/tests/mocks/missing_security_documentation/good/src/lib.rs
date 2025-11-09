#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Contract {
    owner: Address,
}

#[public]
impl Contract {
    pub fn transfer_ownership(&mut self, new_owner: Address) {
        self.owner.set(new_owner);
    }
}
