#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::call::Call;

#[storage]
#[entrypoint]
pub struct Contract {
    balance: StorageMap<Address, U256>,
}

#[public]
impl Contract {
    pub fn withdraw(&mut self, recipient: Address) -> Result<(), Vec<u8>> {
        let amount = self.balance.get(msg::sender());
        Call::new().value(amount).call(recipient, &[])?; // VULN: External call before state update (reentrancy risk)
        self.balance.insert(msg::sender(), U256::from(0));
        Ok(())
    }
}
