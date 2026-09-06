// Fixed: the mint must have the decimals the protocol prices in.
use anchor_lang::prelude::*;
use anchor_spl::token::{Mint, Token, TokenAccount};
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

pub const EXPECTED_DECIMALS: u8 = 6;

#[program]
pub mod vault {
    use super::*;
    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        require_eq!(ctx.accounts.mint.decimals, EXPECTED_DECIMALS, ErrorCode::WrongDecimals);
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

#[error_code]
pub enum ErrorCode { #[msg("wrong decimals")] WrongDecimals }
