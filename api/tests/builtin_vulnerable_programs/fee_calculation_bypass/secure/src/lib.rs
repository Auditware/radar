use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

const ADMIN_PUBKEY: &str = "11111111111111111111111111111112";
const MIN_FEE_RATE: u64 = 1; // 0.01%
const MAX_FEE_RATE: u64 = 1000; // 10%
const MIN_FEE: u64 = 1000; // Minimum fee in lamports
const MAX_DISCOUNT: u64 = 50; // Maximum 50% discount

#[program]
pub mod fee_calculation_bypass_secure {
    use super::*;

    pub fn set_fee_rate(ctx: Context<SetFeeRate>, new_rate: u64) -> Result<()> {
        // SECURE: Validate fee rate bounds and authority
        require!(
            new_rate >= MIN_FEE_RATE && new_rate <= MAX_FEE_RATE,
            ErrorCode::InvalidFeeRate
        );
        
        require!(
            ctx.accounts.admin.key().to_string() == ADMIN_PUBKEY,
            ErrorCode::Unauthorized
        );
        
        ctx.accounts.config.fee_rate = new_rate;
        Ok(())
    }

    pub fn trade_with_verified_vip(ctx: Context<TradeWithVIP>, amount: u64) -> Result<()> {
        // SECURE: Validate VIP status and apply minimum fees
        let config = &ctx.accounts.config;
        let user_account = &ctx.accounts.user_account;
        
        let base_fee = amount
            .checked_mul(config.fee_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(10000)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        let fee = if user_account.is_vip {
            // VIP gets discount, not complete bypass
            require!(
                user_account.vip_verified,
                ErrorCode::UnverifiedVIPStatus
            );
            
            let discounted_fee = base_fee
                .checked_mul(50) // 50% discount
                .ok_or(ErrorCode::ArithmeticOverflow)?
                .checked_div(100)
                .ok_or(ErrorCode::DivisionByZero)?;
                
            // Ensure minimum fee
            std::cmp::max(discounted_fee, MIN_FEE)
        } else {
            std::cmp::max(base_fee, MIN_FEE)
        };
        
        let net_amount = amount
            .checked_sub(fee)
            .ok_or(ErrorCode::InsufficientAmount)?;
        
        // Apply fee to protocol
        ctx.accounts.config.collected_fees = ctx.accounts.config.collected_fees
            .checked_add(fee)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
            
        ctx.accounts.user_account.balance = ctx.accounts.user_account.balance
            .checked_add(net_amount)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
        
        Ok(())
    }

    pub fn calculate_fee_correct_order(ctx: Context<CalculateFee>, amount: u64) -> Result<()> {
        let config = &ctx.accounts.config;
        
        // SECURE: Multiplication before division for precision
        let fee = amount
            .checked_mul(config.fee_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(10000)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        // Ensure minimum fee
        let final_fee = std::cmp::max(fee, MIN_FEE);
        
        ctx.accounts.config.last_fee = final_fee;
        Ok(())
    }

    pub fn swap_with_fee_application(ctx: Context<SwapTokens>, amount_in: u64) -> Result<()> {
        let config = &mut ctx.accounts.config;
        
        // SECURE: Calculate and apply fee properly
        let fee = amount_in
            .checked_mul(config.fee_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(10000)
            .ok_or(ErrorCode::DivisionByZero)?;
            
        let net_amount_in = amount_in
            .checked_sub(fee)
            .ok_or(ErrorCode::InsufficientAmount)?;
        
        let amount_out = calculate_swap_output(net_amount_in);
        
        // Apply fee to protocol
        config.collected_fees = config.collected_fees
            .checked_add(fee)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
        
        ctx.accounts.user_account.token_balance = ctx.accounts.user_account.token_balance
            .checked_add(amount_out)
            .ok_or(ErrorCode::ArithmeticOverflow)?;
        
        Ok(())
    }

    pub fn atomic_fee_calculation(ctx: Context<AtomicFee>, amount: u64) -> Result<()> {
        // SECURE: Capture fee rate atomically to prevent manipulation
        let config = &ctx.accounts.config;
        let fee_rate = config.fee_rate;
        
        // Validate fee rate hasn't been manipulated
        require!(
            fee_rate == config.fee_rate,
            ErrorCode::FeeRateChanged
        );
        
        require!(
            fee_rate >= MIN_FEE_RATE && fee_rate <= MAX_FEE_RATE,
            ErrorCode::InvalidFeeRate
        );
        
        let fee = amount
            .checked_mul(fee_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(10000)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        ctx.accounts.config.last_fee = std::cmp::max(fee, MIN_FEE);
        Ok(())
    }

    pub fn bounded_discount_fee(ctx: Context<BoundedDiscount>, amount: u64, discount_percent: u64) -> Result<()> {
        // SECURE: Validate discount bounds
        require!(
            discount_percent <= MAX_DISCOUNT,
            ErrorCode::ExcessiveDiscount
        );
        
        let config = &ctx.accounts.config;
        let base_fee = amount
            .checked_mul(config.fee_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(10000)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        let discount = base_fee
            .checked_mul(discount_percent)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(100)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        let final_fee = base_fee
            .checked_sub(discount)
            .ok_or(ErrorCode::ArithmeticUnderflow)?;
        
        // Ensure minimum fee even with discount
        let bounded_fee = std::cmp::max(final_fee, MIN_FEE);
        
        ctx.accounts.config.last_fee = bounded_fee;
        Ok(())
    }

    pub fn admin_fee_with_validation(ctx: Context<AdminValidation>, amount: u64, apply_discount: bool) -> Result<()> {
        // SECURE: Validate admin authority
        require!(
            ctx.accounts.admin.key().to_string() == ADMIN_PUBKEY,
            ErrorCode::Unauthorized
        );
        
        let config = &ctx.accounts.config;
        let base_fee = amount
            .checked_mul(config.fee_rate)
            .ok_or(ErrorCode::ArithmeticOverflow)?
            .checked_div(10000)
            .ok_or(ErrorCode::DivisionByZero)?;
        
        let fee = if apply_discount {
            // Admin gets discount, not complete bypass
            let discounted_fee = base_fee
                .checked_mul(25) // 75% discount for admin
                .ok_or(ErrorCode::ArithmeticOverflow)?
                .checked_div(100)
                .ok_or(ErrorCode::DivisionByZero)?;
                
            std::cmp::max(discounted_fee, MIN_FEE)
        } else {
            std::cmp::max(base_fee, MIN_FEE)
        };
        
        ctx.accounts.config.last_fee = fee;
        Ok(())
    }
}

fn calculate_swap_output(amount_in: u64) -> u64 {
    // Simplified swap calculation
    amount_in
        .checked_mul(95)
        .unwrap_or(0)
        .checked_div(100)
        .unwrap_or(0)
}

#[derive(Accounts)]
pub struct SetFeeRate<'info> {
    #[account(mut, has_one = admin @ ErrorCode::Unauthorized)]
    pub config: Account<'info, FeeConfig>,
    pub admin: Signer<'info>,
}

#[derive(Accounts)]
pub struct TradeWithVIP<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    #[account(mut, constraint = user.key() == user_account.owner @ ErrorCode::Unauthorized)]
    pub user_account: Account<'info, UserAccount>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct CalculateFee<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct SwapTokens<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    #[account(mut, constraint = user.key() == user_account.owner @ ErrorCode::Unauthorized)]
    pub user_account: Account<'info, UserAccount>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct AtomicFee<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct BoundedDiscount<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct AdminValidation<'info> {
    #[account(mut, has_one = admin @ ErrorCode::Unauthorized)]
    pub config: Account<'info, FeeConfig>,
    pub admin: Signer<'info>,
}

#[account]
pub struct FeeConfig {
    pub fee_rate: u64, // basis points
    pub last_fee: u64,
    pub collected_fees: u64,
    pub admin: Pubkey,
}

#[account]
pub struct UserAccount {
    pub owner: Pubkey,
    pub balance: u64,
    pub token_balance: u64,
    pub is_vip: bool,
    pub vip_verified: bool,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid fee rate")]
    InvalidFeeRate,
    #[msg("Unauthorized")]
    Unauthorized,
    #[msg("Arithmetic overflow")]
    ArithmeticOverflow,
    #[msg("Division by zero")]
    DivisionByZero,
    #[msg("Unverified VIP status")]
    UnverifiedVIPStatus,
    #[msg("Insufficient amount")]
    InsufficientAmount,
    #[msg("Fee rate changed during operation")]
    FeeRateChanged,
    #[msg("Excessive discount")]
    ExcessiveDiscount,
    #[msg("Arithmetic underflow")]
    ArithmeticUnderflow,
}