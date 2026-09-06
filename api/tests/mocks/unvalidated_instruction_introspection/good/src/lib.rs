// Fixed: the introspected instruction must belong to the program that is
// supposed to have produced it, before any of its bytes are believed.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::sysvar::instructions::load_instruction_at_checked;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod guarded_mint {
    use super::*;
    pub fn mint_with_proof(ctx: Context<MintWithProof>) -> Result<()> {
        let sysvar = &ctx.accounts.instructions.to_account_info();
        let previous = load_instruction_at_checked(0, sysvar)?;

        require_keys_eq!(previous.program_id, anchor_spl::token::ID, ErrorCode::ForeignInstruction);

        let paid = u64::from_le_bytes(previous.data[1..9].try_into().unwrap());
        ctx.accounts.receipt.credited = paid;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct MintWithProof<'info> {
    #[account(mut)]
    pub receipt: Account<'info, Receipt>,
    /// CHECK: instructions sysvar
    pub instructions: UncheckedAccount<'info>,
}

#[account]
pub struct Receipt { pub credited: u64 }

#[error_code]
pub enum ErrorCode { #[msg("foreign instruction")] ForeignInstruction }
