#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    value: U256,
}

#[public]
impl Contract {
    pub fn set_value(&mut self, new_value: U256, caller: Address) { // VULN: Accepts caller as parameter instead of using msg::sender()
        self.value.set(new_value);
    }
}
