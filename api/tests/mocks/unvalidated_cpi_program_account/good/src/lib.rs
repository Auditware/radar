// Fixed: the CPI target is declared as a typed `Program`, which makes Anchor
// verify its address before the handler runs.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::program::invoke;
use anchor_spl::token::Token;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod router {
    use super::*;
    pub fn forward(ctx: Context<Forward>, amount: u64) -> Result<()> {
        let ix = build_transfer(ctx.accounts.token_program.key, amount);
        invoke(&ix, &[ctx.accounts.source.to_account_info()])?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Forward<'info> {
    #[account(mut)]
    pub source: Account<'info, Vault>,
    pub token_program: Program<'info, Token>,
    pub authority: Signer<'info>,
}

#[account]
pub struct Vault { pub balance: u64 }
