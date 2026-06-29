use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod anchor_spot_price_oracle {
    use super::*;

    pub fn get_collateral_price(ctx: Context<GetPrice>) -> Result<u64> {
        let pool = &ctx.accounts.amm_pool;
        let base_amount = pool.base_reserve;
        let quote_amount = pool.quote_reserve;
        let price = quote_amount.checked_div(base_amount).ok_or(ProgramError::Custom(0))?;
        Ok(price)
    }
}

#[derive(Accounts)]
pub struct GetPrice<'info> {
    pub amm_pool: Account<'info, AmmPool>,
}

#[account]
pub struct AmmPool {
    pub base_reserve: u64,
    pub quote_reserve: u64,
}
