use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod anchor_missing_min_output {
    use super::*;

    pub fn swap(ctx: Context<Swap>, amount_in: u64, min_out: u64) -> Result<()> {
        let out_amount = ctx.accounts.pool.base_reserve
            .checked_div(ctx.accounts.pool.quote_reserve)
            .unwrap()
            .checked_mul(amount_in)
            .unwrap();
        ctx.accounts.pool.quote_reserve -= out_amount;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Swap<'info> {
    #[account(mut)]
    pub pool: Account<'info, Pool>,
    pub signer: Signer<'info>,
}

#[account]
pub struct Pool {
    pub base_reserve: u64,
    pub quote_reserve: u64,
}
