use anchor_lang::prelude::*;
use anchor_spl::token::{Token, TokenAccount};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_token_mint_constraint {
    use super::*;

    pub fn record_deposit(ctx: Context<RecordDeposit>) -> Result<()> {
        // Vulnerable: the deposit is credited from a token account that is not
        // pinned to the vault's mint, so a caller can present a worthless-mint
        // account and be credited against the real one.
        let position = &mut ctx.accounts.position;
        position.credited = ctx.accounts.user_token.amount;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct RecordDeposit<'info> {
    #[account(mut)]
    pub position: Account<'info, Position>,
    #[account(mut)]
    pub user_token: Account<'info, TokenAccount>,
    pub authority: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct Position {
    pub credited: u64,
}
