use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod division_before_multiplication {
    use super::*;

    pub fn calculate_fee(ctx: Context<CalculateFee>, amount: u64) -> Result<u64> {
        let fee = (amount / 100) * 3; // Vulnerable: Division before multiplication loses precision
        Ok(fee)
    }
}

#[derive(Accounts)]
pub struct CalculateFee {}
