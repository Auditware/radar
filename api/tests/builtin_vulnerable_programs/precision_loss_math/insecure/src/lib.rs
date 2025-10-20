use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

#[program]
pub mod precision_loss_insecure {
    use super::*;

    pub fn calculate_swap_output(ctx: Context<CalculateSwap>, sol_in: u64) -> Result<()> {
        let pool = &mut ctx.accounts.pool;
        
        // VULNERABLE: Division before multiplication loses precision
        let tokens_out = sol_in / pool.virtual_sol_reserves * pool.virtual_token_reserves;
        
        // VULNERABLE: Integer division in price calculation
        let price_per_token = pool.total_sol / pool.total_tokens; // Loses fractional SOL
        
        // VULNERABLE: Multiple divisions compound precision loss
        let adjusted_amount = sol_in / pool.scale_factor / pool.time_factor;
        
        pool.last_swap_output = tokens_out;
        pool.current_price = price_per_token;
        pool.adjusted_input = adjusted_amount;
        
        Ok(())
    }

    pub fn calculate_fees(ctx: Context<CalculateFees>, amount: u64) -> Result<()> {
        let config = &mut ctx.accounts.config;
        
        // VULNERABLE: Division before multiplication in fee calculation
        let fee = amount / 10000 * config.fee_rate; // If amount < 10000, fee becomes 0
        
        // VULNERABLE: Accumulated precision loss
        let platform_fee = fee / 100 * config.platform_rate;
        let liquidity_fee = fee / 100 * config.liquidity_rate;
        
        config.last_fee = fee;
        config.platform_portion = platform_fee;
        config.liquidity_portion = liquidity_fee;
        
        Ok(())
    }

    pub fn update_bonding_curve(ctx: Context<UpdateCurve>, token_amount: u64) -> Result<()> {
        let curve = &mut ctx.accounts.curve;
        
        // VULNERABLE: Price calculation with precision loss
        let sol_cost = token_amount * curve.virtual_sol_reserves / curve.virtual_token_reserves;
        
        // VULNERABLE: Direct integer division
        curve.virtual_token_reserves -= token_amount;
        curve.virtual_sol_reserves += sol_cost;
        curve.real_token_reserves -= token_amount;
        
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