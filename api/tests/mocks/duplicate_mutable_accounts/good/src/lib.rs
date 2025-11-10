use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod duplicate_mutable_accounts {
    use super::*;

    pub fn transfer(ctx: Context<Transfer>, amount: u64) -> Result<()> {
        ctx.accounts.account_a.balance -= amount;
        ctx.accounts.account_b.balance += amount;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Transfer<'info> {
    #[account(mut)]
    pub account_a: Account<'info, UserAccount>,
    #[account(mut, constraint = account_a.key() != account_b.key())]
    pub account_b: Account<'info, UserAccount>,
}

#[account]
pub struct UserAccount {
    pub balance: u64,
}
