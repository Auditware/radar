// Anchor. A CPI runs, then `reload()` re-reads the account's bytes - but reload
// re-deserializes, it does not re-check who owns the account. A CPI that
// reassigns the account to another program leaves `reload()` succeeding on data
// the attacker now controls, and the balance read afterwards is theirs to pick.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::program::invoke;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod settle {
    use super::*;
    pub fn settle(ctx: Context<Settle>) -> Result<()> {
        invoke(&ctx.accounts.hook_ix(), &[ctx.accounts.pool.to_account_info()])?;

        // VULN: reloaded and trusted, with nothing re-establishing ownership.
        ctx.accounts.pool.reload()?;
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
