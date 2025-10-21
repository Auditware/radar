use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

#[program]
pub mod fee_calculation_bypass_insecure {
    use super::*;

    pub fn set_fee_rate(ctx: Context<SetFeeRate>, new_rate: u64) -> Result<()> {
        // VULNERABLE: Fee rate can be set to zero or manipulated without validation
        ctx.accounts.config.fee_rate = new_rate; // No bounds checking!
        Ok(())
    }

    pub fn trade_with_vip_bypass(ctx: Context<TradeWithVIP>, amount: u64, is_vip: bool) -> Result<()> {
        // VULNERABLE: Fee can be completely bypassed with VIP flag
        let config = &ctx.accounts.config;
        
        let fee = if is_vip {
            0 // Complete bypass - who controls is_vip?
        } else {
            amount * config.fee_rate / 10000
        };
        
        let net_amount = amount - fee;
        
        // Process trade without properly applying fee
        ctx.accounts.user_account.balance += net_amount;
        
        Ok(())
    }

    pub fn calculate_fee_wrong_order(ctx: Context<CalculateFee>, amount: u64) -> Result<()> {
        let config = &ctx.accounts.config;
        
        // VULNERABLE: Division before multiplication loses precision
        let fee = amount / 10000 * config.fee_rate; // Wrong order!
        
        ctx.accounts.config.last_fee = fee;
        Ok(())
    }

    pub fn swap_without_fee_application(ctx: Context<SwapTokens>, amount_in: u64) -> Result<()> {
        let config = &ctx.accounts.config;
        
        // VULNERABLE: Fee calculated but never applied
        let fee = amount_in * config.fee_rate / 10000;
        
        // Fee calculated but not deducted from swap!
        let amount_out = calculate_swap_output(amount_in); // Should be (amount_in - fee)
        
        ctx.accounts.user_account.token_balance += amount_out;
        // Fee is lost - never transferred to protocol
        Ok(())
    }

    pub fn dynamic_fee_manipulation(ctx: Context<DynamicFee>, amount: u64) -> Result<()> {
        // VULNERABLE: Fee rate can be changed mid-operation
        let fee_rate = ctx.accounts.config.fee_rate;
        
        // Potential for fee_rate to change here via another instruction
        
        // Using potentially stale fee rate
        let fee = amount * fee_rate / 10000;
        
        ctx.accounts.config.last_fee = fee;
        Ok(())
    }

    pub fn percentage_fee_bypass(ctx: Context<PercentageFee>, amount: u64, discount_percent: u64) -> Result<()> {
        let config = &ctx.accounts.config;
        
        // VULNERABLE: Discount can exceed 100%, making fee negative/zero
        let base_fee = amount * config.fee_rate / 10000;
        let discount = base_fee * discount_percent / 100; // No bounds on discount_percent
        let final_fee = base_fee - discount; // Can underflow to very large number
        
        ctx.accounts.config.last_fee = final_fee;
        Ok(())
    }

    pub fn admin_fee_override(ctx: Context<AdminOverride>, amount: u64, override_fee: bool) -> Result<()> {
        // VULNERABLE: Anyone can claim admin status
        let fee = if override_fee {
            0 // Admin bypass without proper validation
        } else {
            amount * ctx.accounts.config.fee_rate / 10000
        };
        
        ctx.accounts.config.last_fee = fee;
        Ok(())
    }
}

fn calculate_swap_output(amount_in: u64) -> u64 {
    // Simplified swap calculation
    amount_in * 95 / 100 // 5% slippage
}

#[derive(Accounts)]
pub struct SetFeeRate<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    pub admin: Signer<'info>,
}

#[derive(Accounts)]
pub struct TradeWithVIP<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    #[account(mut)]
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
    #[account(mut)]
    pub user_account: Account<'info, UserAccount>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct DynamicFee<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct PercentageFee<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct AdminOverride<'info> {
    #[account(mut)]
    pub config: Account<'info, FeeConfig>,
    pub admin: Signer<'info>, // No validation if this is actually admin
}

#[account]
pub struct FeeConfig {
    pub fee_rate: u64, // basis points
    pub last_fee: u64,
    pub admin: Pubkey,
}

#[account]
pub struct UserAccount {
    pub owner: Pubkey,
    pub balance: u64,
    pub token_balance: u64,
    pub is_vip: bool,
}