use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

#[program]
pub mod integer_overflow_secure {
    use super::*;

    pub fn withdraw_tokens(ctx: Context<WithdrawTokens>, amount: u64) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        
        // SECURE: Using checked arithmetic operations
        vault.token_balance = vault.token_balance
            .checked_sub(amount)
            .ok_or(ErrorCode::ArithmeticUnderflow)?;
            
        vault.total_withdrawn = vault.total_withdrawn
            .checked_add(amount)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
        
        // SECURE: Checked multiplication with overflow protection
        let fee = amount
            .checked_mul(vault.fee_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
        
        // SECURE: Safe casting with validation
        let large_amount = (amount as u128)
            .checked_mul(1000000)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
            
        let final_amount: u64 = large_amount
            .try_into()
            .map_err(|_| ErrorCode::ArithmeticOverflow)?;
        
        vault.last_withdrawal = final_amount;
        Ok(())
    }

    pub fn calculate_rewards(ctx: Context<CalculateRewards>, multiplier: u64) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        
        // SECURE: Checked multiplication
        vault.pending_rewards = vault.stake_amount
            .checked_mul(multiplier)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
        
        // SECURE: Multiplication before division to preserve precision
        let adjusted_rewards = vault.pending_rewards
            .checked_mul(vault.bonus_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(10000)
            .ok_or(ErrorCode::DivisionByZero)?;
            
        vault.adjusted_rewards = adjusted_rewards;
        
        Ok(())
    }
}

#[derive(Accounts)]
pub struct WithdrawTokens<'info> {
    #[account(mut)]
    pub vault: Account<'info, TokenVault>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct CalculateRewards<'info> {
    #[account(mut)]
    pub vault: Account<'info, TokenVault>,
    pub user: Signer<'info>,
}

#[account]
pub struct TokenVault {
    pub token_balance: u64,
    pub total_withdrawn: u64,
    pub last_withdrawal: u64,
    pub fee_rate: u64,
    pub stake_amount: u64,
    pub pending_rewards: u64,
    pub adjusted_rewards: u64,
    pub bonus_rate: u64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Arithmetic overflow")]
    ArithmeticOverflow,
    #[msg("Arithmetic underflow")]
    ArithmeticUnderflow,
    #[msg("Division by zero")]
    DivisionByZero,
}