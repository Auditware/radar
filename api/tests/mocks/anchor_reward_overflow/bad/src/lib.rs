use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

const PRECISION: u64 = 1_000_000_000;

#[program]
pub mod anchor_reward_overflow {
    use super::*;

    pub fn claim_rewards(ctx: Context<ClaimRewards>) -> Result<()> {
        let reward = ctx.accounts.user.staked_amount * ctx.accounts.pool.reward_rate / PRECISION;
        ctx.accounts.user.pending_rewards = reward;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ClaimRewards<'info> {
    #[account(mut)]
    pub user: Account<'info, UserState>,
    pub pool: Account<'info, PoolState>,
    pub authority: Signer<'info>,
}

#[account]
pub struct UserState {
    pub staked_amount: u64,
    pub pending_rewards: u64,
}

#[account]
pub struct PoolState {
    pub reward_rate: u64,
}
