#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::prelude::*;
use stylus_sdk::call::Call;

#[storage]
#[entrypoint]
pub struct Contract {
    trusted_target: Address,
}

#[public]
impl Contract {
    pub fn invoke(&self, data: alloc::vec::Vec<u8>) -> Result<(), Vec<u8>> {
        let target = self.trusted_target.get(); // FIX: Uses trusted target from storage
        Call::new().call(target, &data)?;
        Ok(())
    }
}
