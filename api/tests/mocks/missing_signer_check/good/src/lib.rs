#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Contract {
    value: U256,
}

#[public]
impl Contract {
    pub fn set_value(&mut self, new_value: U256) { // FIX: Uses implicit msg::sender() from context
        self.value.set(new_value);
    }
}
