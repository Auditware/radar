use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod division_before_multiplication {
    use super::*;

    pub fn calculate_fee(ctx: Context<CalculateFee>, amount: u64) -> Result<u64> {
        let fee = (amount * 3) / 100; // Fix: Multiplication before division preserves precision
        Ok(fee)
    }
}

#[derive(Accounts)]
pub struct CalculateFee {}
