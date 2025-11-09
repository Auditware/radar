#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::msg;

#[storage]
#[entrypoint]
pub struct Pool {
    owner: Address,
    fee_rate: U256,
}

#[public]
impl Pool {
    pub fn set_fee_rate(&mut self, new_fee_rate: U256) -> Result<(), Vec<u8>> {
        if msg::sender() != self.owner.get() { // FIX: Validates owner and fee bounds
            return Err(vec![1]);
        }
        if new_fee_rate > U256::from(1000) {
            return Err(vec![2]);
        }
        self.fee_rate.set(new_fee_rate);
        Ok(())
    }
}
