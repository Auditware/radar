// Fixed: the executor's own entry points are rejected by discriminator before
// the instruction is invoked.
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
        let execute_discriminator = [231u8, 173, 49, 91, 235, 24, 68, 19];
        if Some(execute_discriminator.as_slice()) == ix.data.get(0..8) {
            return err!(ErrorCode::Recursive);
        }
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
pub enum ErrorCode {
    #[msg("wrong program")] WrongProgram,
    #[msg("recursive execution")] Recursive,
}
