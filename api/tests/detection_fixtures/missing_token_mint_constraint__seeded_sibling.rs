use anchor_lang::prelude::*;
use anchor_spl::token::{Token, TokenAccount};
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");
#[program]
pub mod prog {
    use super::*;
    pub fn swap(ctx: Context<Swap>, amount: u64) -> Result<()> { Ok(()) }
}
#[derive(Accounts)]
pub struct Swap<'info> {
    #[account(seeds = [b"pool"], bump)]
    pub pool: Account<'info, Pool>,
    // VULN: no token::mint - caller can pass a wrong-mint token account
    #[account(mut)]
    pub user_token: Account<'info, TokenAccount>,
    pub authority: Signer<'info>,
    pub token_program: Program<'info, Token>,
}
#[account]
pub struct Pool { pub v: u64 }
