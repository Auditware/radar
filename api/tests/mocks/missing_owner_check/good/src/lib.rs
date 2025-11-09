#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Contract {
    owner: Address,
    data: StorageMap<Address, U256>,
}

#[public]
impl Contract {
    pub fn update(&mut self, account: Address, value: U256) -> Result<(), Vec<u8>> {
        if msg::sender() != self.owner.get() { // FIX: Verifies caller is the owner
            return Err(vec![1]);
        }
        self.data.insert(account, value);
        Ok(())
    }
}
