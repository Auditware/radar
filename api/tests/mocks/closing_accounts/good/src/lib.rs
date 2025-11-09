#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    balance: StorageMap<Address, U256>,
    closed: StorageMap<Address, StorageBool>,
}

#[public]
impl Contract {
    pub fn close_account(&mut self, account: Address) {
        self.balance.insert(account, U256::from(0));
        self.closed.setter(account).set(true); // FIX: Marks account as properly closed
    }
}
