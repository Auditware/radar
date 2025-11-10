use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod type_cosplay {
    use super::*;

    pub fn process_account(ctx: Context<ProcessAccount>) -> Result<()> {
        let user_data: Account<UserData> = Account::try_from(&ctx.accounts.user_account)?;
        
        msg!("Processing verified account data: {}", user_data.value);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ProcessAccount<'info> {
    pub user_account: AccountInfo<'info>,
    pub signer: Signer<'info>,
}

#[account]
pub struct UserData {
    pub value: u64,
}
