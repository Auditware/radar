// The account a CPI is dispatched to is supplied by the caller and never tied
// to a known program. Anchor's `Program<'info, T>` exists precisely to make
// that check declarative; an `UncheckedAccount` in that slot means whoever
// builds the transaction chooses which program runs.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::program::invoke;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod router {
    use super::*;
    pub fn forward(ctx: Context<Forward>, amount: u64) -> Result<()> {
        // VULN: `target_program` is whatever was passed in.
        let ix = build_transfer(ctx.accounts.target_program.key, amount);
        invoke(&ix, &[ctx.accounts.source.to_account_info()])?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Forward<'info> {
    #[account(mut)]
    pub source: Account<'info, Vault>,
    /// CHECK: dispatched to without validation
    pub target_program: UncheckedAccount<'info>,
    pub authority: Signer<'info>,
}

#[account]
pub struct Vault { pub balance: u64 }
