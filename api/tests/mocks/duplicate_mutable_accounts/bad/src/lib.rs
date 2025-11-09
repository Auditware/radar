#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {
    balance_a: StorageMap<Address, U256>,
    balance_b: StorageMap<Address, U256>,
}

#[public]
impl Contract {
    pub fn transfer(&mut self, account: Address, amount: U256) { // VULN: Same account used for both balance_a and balance_b without check
        let bal_a = self.balance_a.get(account);
        self.balance_a.insert(account, bal_a - amount);
        let bal_b = self.balance_b.get(account);
        self.balance_b.insert(account, bal_b + amount);
    }
}
