use anchor_lang::prelude::*;
use borsh::{BorshDeserialize, BorshSerialize};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod type_cosplay {
    use super::*;

    pub fn update_user(ctx: Context<UpdateUser>) -> Result<()> {
        // Fix: a type discriminant is checked before trusting the account, so a
        // different account type cannot masquerade as a User.
        let user = User::try_from_slice(&ctx.accounts.user.data.borrow()).unwrap();
        if user.discriminant != AccountType::User {
            return err!(ErrorCode::WrongType);
        }
        if user.authority != ctx.accounts.authority.key() {
            return err!(ErrorCode::Unauthorized);
        }
        msg!("GM {}", user.authority);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct UpdateUser<'info> {
    /// CHECK: raw account, deserialized manually
    pub user: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[derive(BorshSerialize, BorshDeserialize)]
pub struct User {
    pub discriminant: AccountType,
    pub authority: Pubkey,
}

#[derive(BorshSerialize, BorshDeserialize, PartialEq)]
pub enum AccountType {
    User,
    Metadata,
}

#[error_code]
pub enum ErrorCode {
    #[msg("wrong type")]
    WrongType,
    #[msg("unauthorized")]
    Unauthorized,
}
