use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_pyth_confidence_interval {
    use super::*;

    pub fn update_price(ctx: Context<UpdatePrice>) -> Result<()> {
        let price_data = get_price_no_older_than(
            &ctx.accounts.price_account,
            &Clock::get()?,
            60,
        )?;
        let conf_pct = price_data.conf.checked_mul(100).unwrap() / price_data.price.unsigned_abs() as u64;
        require!(conf_pct <= 5, ErrorCode::ConfidenceTooWide);
        let price = price_data.price as u64;
        ctx.accounts.vault.cached_price = price;
        Ok(())
    }
}

fn get_price_no_older_than(
    price_account: &AccountInfo,
    clock: &Clock,
    max_age: u64,
) -> Result<PriceData> {
    let _ = (price_account, clock, max_age);
    Ok(PriceData { price: 100, conf: 2 })
}

#[derive(Accounts)]
pub struct UpdatePrice<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    pub price_account: AccountInfo<'info>,
}

#[account]
pub struct Vault {
    pub cached_price: u64,
}

pub struct PriceData {
    pub price: i64,
    pub conf: u64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Confidence interval too wide")]
    ConfidenceTooWide,
}
