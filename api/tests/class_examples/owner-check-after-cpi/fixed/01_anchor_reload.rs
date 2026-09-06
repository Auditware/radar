// Fixed: ownership is re-established after the CPI, before the reloaded data is
// used for anything.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::program::invoke;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod settle {
    use super::*;
    pub fn settle(ctx: Context<Settle>) -> Result<()> {
        invoke(&ctx.accounts.hook_ix(), &[ctx.accounts.pool.to_account_info()])?;

        ctx.accounts.pool.reload()?;
        require_keys_eq!(
            *ctx.accounts.pool.to_account_info().owner,
            crate::ID,
            ErrorCode::PoolReassigned
        );

        let owed = ctx.accounts.pool.balance;
        ctx.accounts.treasury.balance += owed;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Settle<'info> {
    #[account(mut)]
    pub pool: Account<'info, Pool>,
    #[account(mut)]
    pub treasury: Account<'info, Pool>,
    pub authority: Signer<'info>,
}

#[account]
pub struct Pool { pub balance: u64 }

#[error_code]
pub enum ErrorCode { #[msg("pool reassigned")] PoolReassigned }
