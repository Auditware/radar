#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::call::Call;

#[storage]
#[entrypoint]
pub struct Contract {
    balance: StorageMap<Address, U256>,
    locked: StorageBool,
}

#[public]
impl Contract {
    pub fn withdraw(&mut self, recipient: Address) -> Result<(), Vec<u8>> {
        if self.locked.get() {
            return Err(Vec::new());
        }
        self.locked.set(true);
        let amount = self.balance.get(msg::sender());
        self.balance.insert(msg::sender(), U256::from(0));
        Call::new().value(amount).call(recipient, &[])?;
        self.locked.set(false);
        Ok(())
    }
}
