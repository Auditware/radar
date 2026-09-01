use anchor_lang::prelude::*;
use anchor_spl::token::{Mint, Token, TokenAccount};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_token_mint_constraint {
    use super::*;

    pub fn record_deposit(ctx: Context<RecordDeposit>) -> Result<()> {
        // Fix: the credited token account is pinned to the expected mint, so a
        // worthless-mint account cannot be credited against the real one.
        let position = &mut ctx.accounts.position;
        position.credited = ctx.accounts.user_token.amount;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct RecordDeposit<'info> {
    #[account(mut)]
    pub position: Account<'info, Position>,
    #[account(mut, token::mint = expected_mint)]
    pub user_token: Account<'info, TokenAccount>,
    pub expected_mint: Account<'info, Mint>,
    pub authority: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct Position {
    pub credited: u64,
}
