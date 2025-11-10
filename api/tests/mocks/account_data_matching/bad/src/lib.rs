use anchor_lang::prelude::*;
use anchor_spl::token::{Token, TokenAccount};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod account_data_matching {
    use super::*;
    use spl_token::state::Account as SplTokenAccount;

    pub fn process_transfer(ctx: Context<TransferAccounts>) -> Result<()> {
        let token_account_info = &ctx.accounts.token_account.to_account_info();
        let token_account = SplTokenAccount::unpack(&token_account_info.data.borrow())?;
        
        // VULN: No authority verification after unpacking
        msg!("Token account owner: {:?}", token_account.owner);
        
        Ok(())
    }
}

#[derive(Accounts)]
pub struct TransferAccounts<'info> {
    #[account(mut)]
    pub token_account: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
}
