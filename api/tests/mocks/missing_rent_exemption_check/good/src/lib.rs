use anchor_lang::prelude::*;
use anchor_lang::solana_program::{program::invoke, system_instruction};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_rent_exemption_check {
    use super::*;

    pub fn create_data_account(ctx: Context<CreateDataAccount>, space: u64) -> Result<()> {
        let rent = Rent::get()?;
        let lamports = rent.minimum_balance(space as usize);
        let ix = system_instruction::create_account(
            ctx.accounts.payer.key,
            ctx.accounts.new_account.key,
            lamports,
            space,
            ctx.program_id,
        );
        invoke(
            &ix,
            &[
                ctx.accounts.payer.to_account_info(),
                ctx.accounts.new_account.to_account_info(),
            ],
        )?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CreateDataAccount<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    /// CHECK: new account to create
    #[account(mut)]
    pub new_account: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}
