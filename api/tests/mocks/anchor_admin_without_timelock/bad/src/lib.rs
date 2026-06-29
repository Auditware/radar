use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod anchor_admin_without_timelock {
    use super::*;

    pub fn update_withdraw_threshold(ctx: Context<AdminAction>, new_threshold: u64) -> Result<()> {
        ctx.accounts.state.withdraw_threshold = new_threshold;
        Ok(())
    }

    pub fn update_fee_rate(ctx: Context<AdminAction>, new_fee: u64) -> Result<()> {
        ctx.accounts.state.fee_rate = new_fee;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct AdminAction<'info> {
    #[account(constraint = admin.key() == state.admin)]
    pub admin: Signer<'info>,
    #[account(mut)]
    pub state: Account<'info, ProtocolState>,
}

#[account]
pub struct ProtocolState {
    pub admin: Pubkey,
    pub withdraw_threshold: u64,
    pub fee_rate: u64,
}
