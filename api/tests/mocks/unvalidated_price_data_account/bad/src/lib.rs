use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod unvalidated_price_data_account {
    use super::*;

    pub fn update_collateral(ctx: Context<UpdateCollateral>) -> Result<()> {
        let price_data = ctx.accounts.price_account.try_borrow_data()?;
        let price = u64::from_le_bytes(price_data[..8].try_into().unwrap());
        ctx.accounts.vault.collateral_value = price;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct UpdateCollateral<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    pub price_account: AccountInfo<'info>,
}

#[account]
pub struct Vault {
    pub collateral_value: u64,
}
