#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    data: StorageMap<Address, U256>,
}

#[public]
impl Contract {
    pub fn update(&mut self, account: Address, value: U256) { // VULN: No owner check before modifying account data
        self.data.insert(account, value);
    }
}
