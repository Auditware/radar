// Two instructions over the same account type. One checks the stored authority
// by hand; the other binds nothing at all.
//
// The manual check in `close` is a real substitute for `has_one` - but only for
// `close`. Searched across the whole file it excused `withdraw` too, which is
// the file-scope suppression from #23 one level down: the file plainly contains
// an authority check, so the missing one reads as covered.
use anchor_lang::prelude::*;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod prog {
    use super::*;

    // VULN: nothing binds `vault.authority` to the signer, here or anywhere
    // that applies to this instruction.
    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        ctx.accounts.vault.balance -= amount;
        Ok(())
    }

    // Correct: the binding has_one would declare is written out by hand.
    pub fn close(ctx: Context<Close>) -> Result<()> {
        if ctx.accounts.vault.authority != ctx.accounts.authority.key() {
            return Err(ProgramError::IllegalOwner.into());
        }
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    #[account(mut)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct Close<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    #[account(mut)]
    pub authority: Signer<'info>,
}

#[account]
pub struct Vault { pub authority: Pubkey, pub balance: u64 }
