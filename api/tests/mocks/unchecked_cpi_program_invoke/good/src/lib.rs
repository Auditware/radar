use anchor_lang::prelude::*;
use anchor_lang::solana_program::{instruction::Instruction, program::invoke};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

const EXPECTED_PROGRAM: Pubkey = anchor_lang::solana_program::pubkey!("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA");

#[program]
pub mod unchecked_cpi_program_invoke {
    use super::*;

    pub fn execute(ctx: Context<Execute>, program_id: Pubkey, data: Vec<u8>) -> Result<()> {
        require_keys_eq!(program_id, EXPECTED_PROGRAM, ErrorCode::InvalidProgram);
        let ix = Instruction {
            program_id,
            accounts: vec![],
            data,
        };
        invoke(&ix, &[ctx.accounts.authority.to_account_info()])?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Execute<'info> {
    pub authority: Signer<'info>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid program")]
    InvalidProgram,
}
