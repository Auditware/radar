// The instructions sysvar is read to inspect a neighbouring instruction, and
// the instruction it finds is trusted without checking which program it belongs
// to. Anyone can put an instruction at that index; making it *look* like the
// expected one is the whole attack.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::sysvar::instructions::load_instruction_at_checked;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod guarded_mint {
    use super::*;
    pub fn mint_with_proof(ctx: Context<MintWithProof>) -> Result<()> {
        let sysvar = &ctx.accounts.instructions.to_account_info();
        let previous = load_instruction_at_checked(0, sysvar)?;

        // VULN: the payload is read straight off an instruction whose program
        // was never established.
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
