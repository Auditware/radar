use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod closing_accounts {
    use super::*;

    pub fn close_account(ctx: Context<CloseAccount>) -> Result<()> {
        let account_lamports = ctx.accounts.user_account.to_account_info().lamports();
        **ctx.accounts.user_account.to_account_info().lamports.borrow_mut() = 0; // Vulnerable: Direct zero assignment without proper close
        **ctx.accounts.destination.lamports.borrow_mut() += account_lamports;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CloseAccount<'info> {
    #[account(mut)]
    pub user_account: Account<'info, UserData>,
    #[account(mut)]
    pub destination: AccountInfo<'info>,
}

#[account]
pub struct UserData {
    pub data: u64,
}
