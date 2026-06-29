use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod decimal_to_u64_without_sign_check {
    use super::*;

    pub fn liquidate(ctx: Context<Liquidate>) -> Result<()> {
        let vault = &ctx.accounts.vault;
        if vault.collateral_value > vault.debt_value {
            let profit = vault
                .collateral_value
                .checked_sub(vault.debt_value)
                .unwrap()
                .to_u64()
                .unwrap();
            ctx.accounts.vault.profit = profit;
        }
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Liquidate<'info> {
    #[account(mut)]
    pub vault: Account<'info, Vault>,
}

#[account]
pub struct Vault {
    pub collateral_value: u64,
    pub debt_value: u64,
    pub profit: u64,
}
