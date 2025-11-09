#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    accounts: StorageMap<Address, U256>,
}

#[public]
impl Contract {
    pub fn transfer(&mut self, from: Address, to: Address, amount: U256) { // VULN: No authorization check on from address
        let balance = self.accounts.get(from);
        self.accounts.insert(from, balance - amount);
        self.accounts.insert(to, self.accounts.get(to) + amount);
    }
}
