use anchor_lang::prelude::*;
use anchor_spl::token::{Token, TokenAccount};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_owner_check {
    use super::*;
    use spl_token::state::Account as SplTokenAccount;

    pub fn process_token(ctx: Context<ProcessToken>) -> Result<()> {
        let token_account_info = &ctx.accounts.token_account.to_account_info();
        let token_account = SplTokenAccount::unpack(&token_account_info.data.borrow())?;
        
        require!(
            token_account.owner == *ctx.accounts.authority.key,
            ErrorCode::InvalidOwner
        );
        
        msg!("Processing token account with owner: {:?}", token_account.owner);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ProcessToken<'info> {
    #[account(mut)]
    pub token_account: Account<'info, TokenAccount>,
    pub authority: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid owner")]
    InvalidOwner,
}
