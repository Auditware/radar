#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use alloy_primitives::keccak256;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    pub fn derive_address(&self, seed: U256, bump: u8) -> Address {
        let mut data = alloc::vec::Vec::new();
        data.extend_from_slice(&seed.to_be_bytes::<32>());
        data.push(bump); // VULN: Using arbitrary bump without canonicalization
        let hash = keccak256(&data);
        Address::from_slice(&hash[0..20])
    }
}
