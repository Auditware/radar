// Fixed: same check, written as an explicit comparison rather than a macro.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::sysvar::instructions::get_instruction_relative;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod settlement {
    use super::*;
    pub fn settle(ctx: Context<Settle>) -> Result<()> {
        let sysvar = &ctx.accounts.instructions.to_account_info();
        let next = get_instruction_relative(1, sysvar)?;

        if next.program_id != anchor_spl::token::ID {
            return err!(ErrorCode::ForeignInstruction);
        }

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

#[error_code]
pub enum ErrorCode { #[msg("foreign instruction")] ForeignInstruction }
