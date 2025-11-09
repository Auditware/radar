#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Contract {
    balance: U256,
}

#[public]
impl Contract {
    #[payable]
    pub fn receive_payment(&mut self) {
        let value = msg::value(); // FIX: Handles received value properly
        self.balance.set(self.balance.get() + value);
    }
}
