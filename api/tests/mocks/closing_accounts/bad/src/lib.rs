#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    balance: StorageMap<Address, U256>,
}

#[public]
impl Contract {
    pub fn close_account(&mut self, account: Address) { // VULN: Zeroing balance without proper closure markers
        self.balance.insert(account, U256::from(0));
    }
}
