#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use alloc::vec::Vec;

#[storage]
#[entrypoint]
pub struct Contract {
    expected_type: U256,
}

#[public]
impl Contract {
    pub fn deserialize(&self, data: Vec<u8>, type_id: U256) -> Result<U256, Vec<u8>> {
        if type_id != self.expected_type.get() { // FIX: Type discriminator validation
            return Err(vec![1]);
        }
        U256::try_from_be_slice(&data).ok_or(vec![2])
    }
}
