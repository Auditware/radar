use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod anchor_admin_without_timelock {
    use super::*;

    pub fn execute_withdraw_threshold(ctx: Context<AdminAction>) -> Result<()> {
        let now = Clock::get()?.unix_timestamp;
        require!(now >= ctx.accounts.state.execute_after, ProgramError::Custom(0));
        ctx.accounts.state.withdraw_threshold = ctx.accounts.pending.new_threshold;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct AdminAction<'info> {
    #[account(constraint = admin.key() == state.admin)]
    pub admin: Signer<'info>,
    #[account(mut)]
    pub state: Account<'info, ProtocolState>,
    pub pending: Account<'info, PendingAction>,
}

#[account]
pub struct ProtocolState {
    pub admin: Pubkey,
    pub withdraw_threshold: u64,
    pub execute_after: i64,
}

#[account]
pub struct PendingAction {
    pub new_threshold: u64,
}
