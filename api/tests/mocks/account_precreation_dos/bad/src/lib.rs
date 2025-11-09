#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    owners: StorageMap<Address, Address>,
}

#[public]
impl Contract {
    pub fn assign_owner(&mut self, account: Address, owner: Address) { // VULN: No check if account already has owner
        self.owners.insert(account, owner);
    }
}
