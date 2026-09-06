// A deposit is priced in raw token units while the mint's decimals are never
// checked. Two mints with the same symbol and different decimals value the same
// integer amount a thousandfold apart, so the protocol credits whatever the
// caller's mint says it is worth.
use anchor_lang::prelude::*;
use anchor_spl::token::{Mint, Token, TokenAccount};
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod vault {
    use super::*;
    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        // VULN: `ctx.accounts.mint.decimals` is never consulted.
        ctx.accounts.position.shares += amount;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(mut)]
    pub position: Account<'info, Position>,
    pub mint: Account<'info, Mint>,
    #[account(mut)]
    pub source: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct Position { pub shares: u64 }
