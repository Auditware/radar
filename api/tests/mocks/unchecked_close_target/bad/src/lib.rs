use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod unchecked_close_target {
    use super::*;

    pub fn close_account(ctx: Context<CloseAccount>) -> Result<()> {
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CloseAccount<'info> {
    #[account(mut, close = target)]
    pub user_account: Account<'info, UserData>,
    /// CHECK: target receives lamports
    pub target: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[account]
pub struct UserData {
    pub authority: Pubkey,
    pub value: u64,
}
