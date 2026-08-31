use anchor_lang::prelude::*;
use borsh::{BorshDeserialize, BorshSerialize};
use std::ops::DerefMut;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod account_reinitialization {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        // Fix: an already-initialized guard (a discriminator flag) rejects a
        // caller that passes an account which was already initialized.
        let mut user = User::try_from_slice(&ctx.accounts.user.data.borrow()).unwrap();
        if user.discriminator {
            return Err(ErrorCode::AlreadyInitialized.into());
        }
        user.discriminator = true;
        user.authority = ctx.accounts.authority.key();

        let mut storage = ctx.accounts.user.try_borrow_mut_data()?;
        user.serialize(storage.deref_mut()).unwrap();
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    /// CHECK: raw account, deserialized manually
    #[account(mut)]
    pub user: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct User {
    pub discriminator: bool,
    pub authority: Pubkey,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Already initialized")]
    AlreadyInitialized,
}
