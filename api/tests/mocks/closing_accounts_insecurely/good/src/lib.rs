use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod closing_accounts {
    use super::*;

    pub fn close_account(ctx: Context<CloseAccount>) -> Result<()> {
        let account_lamports = ctx.accounts.user_account.to_account_info().lamports();
        **ctx.accounts.user_account.to_account_info().lamports.borrow_mut() -= account_lamports; // Fix: Properly drain lamports
        **ctx.accounts.destination.lamports.borrow_mut() += account_lamports;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CloseAccount<'info> {
    #[account(mut, close = destination)] // Fix: Uses close constraint
    pub user_account: Account<'info, UserData>,
    #[account(mut)]
    pub destination: AccountInfo<'info>,
}

#[account]
pub struct UserData {
    pub data: u64,
}
