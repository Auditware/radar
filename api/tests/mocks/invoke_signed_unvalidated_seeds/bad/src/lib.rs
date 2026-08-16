use anchor_lang::prelude::*;
use anchor_lang::solana_program::program;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod invoke_signed_unvalidated_seeds {
    use super::*;

    pub fn withdraw(ctx: Context<Withdraw>, bump: u8) -> Result<()> {
        let ix = build_instruction(&ctx.accounts.vault.key());
        program::invoke_signed(&ix, &[], &[&[b"vault", &[bump]]])?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    /// CHECK: pda vault
    pub vault: UncheckedAccount<'info>,
    pub user: Signer<'info>,
}
