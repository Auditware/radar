// Safe pattern - sealevel-attacks 4-initialization/secure.
//
// The authority lives in a RAW `AccountInfo` that the handler deserializes by
// hand and *assigns* from the signer (an initialization/claim). `has_one` is not
// even expressible on a raw account, and nothing here trusts a pre-existing
// stored authority for a privileged action, so "Missing has_one Constraint" must
// stay silent. It used to fire here because a Signer named `authority` sat beside
// a `Pubkey authority` field anywhere in the file.
use anchor_lang::prelude::*;
use borsh::{BorshDeserialize, BorshSerialize};
use std::ops::DerefMut;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod reinitialization_secure_recommended {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> ProgramResult {
        let mut user = User::try_from_slice(&ctx.accounts.user.data.borrow()).unwrap();
        if !user.discriminator {
            return Err(ProgramError::InvalidAccountData);
        }

        user.authority = ctx.accounts.authority.key();
        user.discriminator = true;

        let mut storage = ctx.accounts.user.try_borrow_mut_data()?;
        user.serialize(storage.deref_mut()).unwrap();

        msg!("GM");
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    user: AccountInfo<'info>,
    authority: Signer<'info>,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct User {
    discriminator: bool,
    authority: Pubkey,
}
