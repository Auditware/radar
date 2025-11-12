use anchor_lang::prelude::*;
use anchor_lang::solana_program::{program::invoke, instruction::Instruction};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod arbitrary_cpi {
    use super::*;

    pub fn proxy_invoke(ctx: Context<ProxyInvoke>, data: Vec<u8>) -> Result<()> {
        let ix = Instruction {
            program_id: *ctx.accounts.target_program.key,
            accounts: vec![],
            data,
        };
        invoke(&ix, &[ctx.accounts.target_program.to_account_info()])?; // Vulnerable: No validation of target_program
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ProxyInvoke<'info> {
    pub target_program: AccountInfo<'info>,
    pub signer: Signer<'info>,
}
