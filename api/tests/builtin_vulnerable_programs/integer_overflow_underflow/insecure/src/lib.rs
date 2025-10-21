use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

#[program]
pub mod integer_overflow_insecure {
    use super::*;

    pub fn withdraw_tokens(ctx: Context<WithdrawTokens>, amount: u64) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        
        // VULNERABLE: Direct arithmetic operations without checked math
        vault.token_balance -= amount; // Can underflow
        vault.total_withdrawn += amount; // Can overflow
        
        // VULNERABLE: Multiplication that can overflow
        let fee = amount * vault.fee_rate; // No overflow protection
        
        // VULNERABLE: Unsafe casting
        let large_amount = (amount as u128) * 1000000;
        let final_amount = large_amount as u64; // Can truncate/overflow
        
        vault.last_withdrawal = final_amount;
        Ok(())
    }

    pub fn calculate_rewards(ctx: Context<CalculateRewards>, multiplier: u64) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        
        // VULNERABLE: Direct multiplication without overflow check
        vault.pending_rewards = vault.stake_amount * multiplier;
        
        // VULNERABLE: Division before multiplication (precision loss + potential overflow)
        let adjusted_rewards = vault.pending_rewards / 10000 * vault.bonus_rate;
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