use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod type_cosplay {
    use super::*;

    pub fn process_account(ctx: Context<ProcessAccount>) -> Result<()> {
        let account_info = &ctx.accounts.user_account;
        let data = account_info.try_borrow_data()?;
        
        msg!("Processing account data of length: {}", data.len());
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ProcessAccount<'info> {
    pub user_account: AccountInfo<'info>,
    pub signer: Signer<'info>,
}
