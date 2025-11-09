#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::block;

#[storage]
#[entrypoint]
pub struct Contract {
    trusted_timestamp_source: Address,
}

#[public]
impl Contract {
    pub fn get_timestamp(&self, source: Address) -> Result<U256, Vec<u8>> {
        if source != self.trusted_timestamp_source.get() { // FIX: Validates sysvar source
            return Err(vec![1]);
        }
        Ok(U256::from(block::timestamp()))
    }
}
