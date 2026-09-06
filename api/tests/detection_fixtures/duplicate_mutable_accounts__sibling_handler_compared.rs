// Two instructions, each taking two mutable accounts of the same type. One
// distinguishes them with a key comparison; the other does not.
//
// Both instructions name their fields the same way, which is ordinary. The
// comparison in `swap` is a real defence - for `swap`. Searched across the whole
// file it matched on field *name*, so it excused `merge`'s identically-named
// fields too, and the instruction that can be handed the same account twice
// reported nothing in a file that visibly contains the right check.
use anchor_lang::prelude::*;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod prog {
    use super::*;

    // Correct: the two vaults are proved distinct before either is written.
    pub fn swap(ctx: Context<Swap>, amount: u64) -> Result<()> {
        if ctx.accounts.vault_a.key() == ctx.accounts.vault_b.key() {
            return Err(ProgramError::InvalidArgument.into());
        }
        ctx.accounts.vault_a.balance -= amount;
        ctx.accounts.vault_b.balance += amount;
        Ok(())
    }

    // VULN: nothing here proves the two vaults are different accounts, so
    // one account passed twice has its balance both debited and credited.
    pub fn merge(ctx: Context<Merge>, amount: u64) -> Result<()> {
        ctx.accounts.vault_a.balance -= amount;
        ctx.accounts.vault_b.balance += amount;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Swap<'info> {
    #[account(mut)]
    pub vault_a: Account<'info, Vault>,
    #[account(mut)]
    pub vault_b: Account<'info, Vault>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct Merge<'info> {
    #[account(mut)]
    pub vault_a: Account<'info, Vault>,
    #[account(mut)]
    pub vault_b: Account<'info, Vault>,
    pub authority: Signer<'info>,
}

#[account]
pub struct Vault { pub balance: u64 }
