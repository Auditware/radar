#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    constant_value: U256,
}

#[public]
impl Contract {
    pub fn update(&mut self) {
        self.constant_value.set(U256::from(100)); // VULN: Mutating what appears to be a constant
    }
}
