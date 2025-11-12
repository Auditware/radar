#![cfg_attr(not(feature = "export-abi"), no_main)]
extern crate alloc;

use stylus_sdk::{alloy_primitives::U256, prelude::*};

#[storage]
#[entrypoint]
pub struct TokenContract {
    max_supply: StorageU256,
}

#[public]
impl TokenContract {
    pub fn check_mint_limit(&mut self, amount: U256) -> Result<(), Vec<u8>> {
        let max = self.max_supply.get();
        
        // FIX: <= correctly includes the boundary value
        if amount <= max {
            Ok(())
        } else {
            Err(b"Exceeds max supply".to_vec())
        }
    }
}
