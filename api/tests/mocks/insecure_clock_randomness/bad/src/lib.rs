use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod insecure_clock_randomness {
    use super::*;

    pub fn pick_winner(ctx: Context<PickWinner>, participant_count: u64) -> Result<()> {
        let clock = Clock::get()?;
        let winner_index = (clock.unix_timestamp as u64) % participant_count;
        ctx.accounts.lottery.winner_index = winner_index;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct PickWinner<'info> {
    #[account(mut)]
    pub lottery: Account<'info, Lottery>,
    pub authority: Signer<'info>,
}

#[account]
pub struct Lottery {
    pub winner_index: u64,
}
