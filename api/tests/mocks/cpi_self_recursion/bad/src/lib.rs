// An executor that invokes a caller-supplied instruction and permits that
// instruction to target itself, with nothing constraining which of its own
// entry points may be re-entered.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::program::invoke_signed;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod executor {
    use super::*;
    pub fn execute(ctx: Context<Execute>) -> Result<()> {
        let ix = ctx.accounts.transaction.to_instruction();
        if &ix.program_id != ctx.program_id {
            return err!(ErrorCode::WrongProgram);
        }
        // VULN: self-targeting allowed, entry point unconstrained.
        invoke_signed(&ix, &ctx.remaining_accounts, &[])?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Execute<'info> {
    #[account(mut)]
    pub transaction: Account<'info, StoredTransaction>,
    pub authority: Signer<'info>,
}

#[account]
pub struct StoredTransaction { pub payload: Vec<u8> }

#[error_code]
pub enum ErrorCode { #[msg("wrong program")] WrongProgram }
