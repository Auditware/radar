use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

const PRECISION: u128 = 1_000_000_000; // 9 decimal places for precision

#[program]
pub mod precision_loss_secure {
    use super::*;

    pub fn calculate_swap_output(ctx: Context<CalculateSwap>, sol_in: u64) -> Result<()> {
        let pool = &mut ctx.accounts.pool;
        
        // SECURE: Multiplication before division to preserve precision
        let tokens_out = (sol_in as u128)
            .checked_mul(pool.virtual_token_reserves as u128)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(pool.virtual_sol_reserves as u128)
            .ok_or(ErrorCode::DivisionByZero)?
            as u64;
        
        // SECURE: Use higher precision for price calculations
        let price_per_token = (pool.total_sol as u128)
            .checked_mul(PRECISION)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(pool.total_tokens as u128)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        // SECURE: Single division with combined factors
        let combined_factor = pool.scale_factor
            .checked_mul(pool.time_factor)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
        let adjusted_amount = sol_in
            .checked_div(combined_factor)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        pool.last_swap_output = tokens_out;
        pool.current_price = (price_per_token / PRECISION) as u64;
        pool.adjusted_input = adjusted_amount;
        
        Ok(())
    }

    pub fn calculate_fees(ctx: Context<CalculateFees>, amount: u64) -> Result<()> {
        let config = &mut ctx.accounts.config;
        
        // SECURE: Multiplication before division
        let fee = amount
            .checked_mul(config.fee_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(10000)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        // SECURE: Calculate sub-fees from total fee, not compounding divisions
        let platform_fee = fee
            .checked_mul(config.platform_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(100)
            .ok_or(ErrorCode::DivisionByZero)?;
            
        let liquidity_fee = fee
            .checked_mul(config.liquidity_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(100)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        config.last_fee = fee;
        config.platform_portion = platform_fee;
        config.liquidity_portion = liquidity_fee;
        
        Ok(())
    }

    pub fn update_bonding_curve(ctx: Context<UpdateCurve>, token_amount: u64) -> Result<()> {
        let curve = &mut ctx.accounts.curve;
        
        // SECURE: Use higher precision for bonding curve calculations
        let sol_cost = (token_amount as u128)
            .checked_mul(curve.virtual_sol_reserves as u128)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(curve.virtual_token_reserves as u128)
            .ok_or(ErrorCode::DivisionByZero)?
            as u64;
        
        // SECURE: Checked arithmetic for reserve updates
        curve.virtual_token_reserves = curve.virtual_token_reserves
            .checked_sub(token_amount)
            .ok_or(ErrorCode::ArithmeticUnderflow)?;
            
        curve.virtual_sol_reserves = curve.virtual_sol_reserves
            .checked_add(sol_cost)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
            
        curve.real_token_reserves = curve.real_token_reserves
            .checked_sub(token_amount)
            .ok_or(ErrorCode::ArithmeticUnderflow)?;
        
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CalculateSwap<'info> {
    #[account(mut)]
    pub pool: Account<'info, SwapPool>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct CalculateFees<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    pub admin: Signer<'info>,
}

#[derive(Accounts)]
pub struct UpdateCurve<'info> {
    #[account(mut)]
    pub curve: Account<'info, BondingCurve>,
    pub user: Signer<'info>,
}

#[account]
pub struct SwapPool {
    pub virtual_sol_reserves: u64,
    pub virtual_token_reserves: u64,
    pub total_sol: u64,
    pub total_tokens: u64,
    pub scale_factor: u64,
    pub time_factor: u64,
    pub last_swap_output: u64,
    pub current_price: u64,
    pub adjusted_input: u64,
}

#[account]
pub struct FeeConfig {
    pub fee_rate: u64,
    pub platform_rate: u64,
    pub liquidity_rate: u64,
    pub last_fee: u64,
    pub platform_portion: u64,
    pub liquidity_portion: u64,
}

#[account]
pub struct BondingCurve {
    pub virtual_sol_reserves: u64,
    pub virtual_token_reserves: u64,
    pub real_token_reserves: u64,
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