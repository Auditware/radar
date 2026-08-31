use anchor_lang::prelude::*;
use borsh::{BorshDeserialize, BorshSerialize};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod type_cosplay {
    use super::*;

    pub fn update_user(ctx: Context<UpdateUser>) -> Result<()> {
        // Vulnerable: the raw account is deserialized as User with no type
        // discriminant check, so a different account type with a compatible
        // layout can masquerade as a User.
        let user = User::try_from_slice(&ctx.accounts.user.data.borrow()).unwrap();
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
    pub authority: Pubkey,
}

#[error_code]
pub enum ErrorCode {
    #[msg("unauthorized")]
    Unauthorized,
}
