// Same class through the relative-introspection helper, and reading the
// following instruction rather than the preceding one.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::sysvar::instructions::get_instruction_relative;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod settlement {
    use super::*;
    pub fn settle(ctx: Context<Settle>) -> Result<()> {
        let sysvar = &ctx.accounts.instructions.to_account_info();
        let next = get_instruction_relative(1, sysvar)?;

        // VULN: the accounts of an unverified instruction decide who gets paid.
        ctx.accounts.escrow.beneficiary = next.accounts[0].pubkey;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Settle<'info> {
    #[account(mut)]
    pub escrow: Account<'info, Escrow>,
    /// CHECK: instructions sysvar
    pub instructions: UncheckedAccount<'info>,
}

#[account]
pub struct Escrow { pub beneficiary: Pubkey }
