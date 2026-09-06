// `init_if_needed` does not guarantee creation - the account may already exist.
// Two such fields of the same type can therefore be handed the same existing
// account, which is exactly this bug, so `init_if_needed` must not be treated
// as proof of distinctness the way plain `init` is.
use anchor_lang::prelude::*;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod prog {
    use super::*;
    // VULN: pass the same existing account twice and the second credit lands on
    // the balance the first one already read.
    pub fn settle(ctx: Context<Settle>, amount: u64) -> Result<()> {
        ctx.accounts.from.balance -= amount;
        ctx.accounts.into.balance += amount;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Settle<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    #[account(init_if_needed, payer = payer, space = 16)]
    pub from: Account<'info, Slot>,
    #[account(init_if_needed, payer = payer, space = 16)]
    pub into: Account<'info, Slot>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Slot { pub balance: u64 }
