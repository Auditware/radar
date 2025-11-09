#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;

#[storage]
#[entrypoint]
pub struct Contract {}

#[public]
impl Contract {
    #[payable]
    pub fn receive_payment(&self) { // VULN: Payable function doesn't handle received value
    }
}
