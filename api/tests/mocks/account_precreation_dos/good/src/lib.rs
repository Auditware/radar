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
    pub fn assign_owner(&mut self, account: Address, owner: Address) -> Result<(), Vec<u8>> {
        if self.owners.get(account) != Address::default() { // FIX: Prevents reassignment DoS
            return Err(vec![1]);
        }
        self.owners.insert(account, owner);
        Ok(())
    }
}
