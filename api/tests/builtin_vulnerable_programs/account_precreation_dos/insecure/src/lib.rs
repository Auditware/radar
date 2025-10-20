use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

#[program]
pub mod account_precreation_dos_insecure {
    use super::*;

    pub fn initialize_user_account(ctx: Context<InitializeUserAccount>) -> Result<()> {
        // VULNERABLE: No validation of account state before initialization
        let user_account = &mut ctx.accounts.user_account;
        
        // Direct initialization without checking if account already exists or is owned
        user_account.owner = ctx.accounts.user.key();
        user_account.balance = 0;
        user_account.initialized = true;
        
        Ok(())
    }

    pub fn create_user_vault(ctx: Context<CreateUserVault>) -> Result<()> {
        // VULNERABLE: Account creation without existence check
        let vault = &mut ctx.accounts.vault;
        vault.owner = ctx.accounts.user.key();
        vault.balance = 0;
        Ok(())
    }

    pub fn initialize_global_config(ctx: Context<InitializeGlobalConfig>) -> Result<()> {
        // VULNERABLE: Global PDA that anyone can create (no access control)
        let config = &mut ctx.accounts.global_config;
        config.admin = ctx.accounts.user.key(); // Anyone can become admin!
        config.fee_rate = 100;
        config.initialized = true;
        Ok(())
    }

    pub fn create_predictable_pda(ctx: Context<CreatePredictablePDA>) -> Result<()> {
        // VULNERABLE: Using only user pubkey as seed (easily predictable)
        let pda_account = &mut ctx.accounts.pda_account;
        pda_account.owner = ctx.accounts.user.key();
        pda_account.data = 42;
        Ok(())
    }

    pub fn initialize_simple_account(ctx: Context<InitializeSimpleAccount>) -> Result<()> {
        // VULNERABLE: Simple seed pattern without randomness
        let account = &mut ctx.accounts.simple_account;
        account.creator = ctx.accounts.user.key();
        account.value = 100;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeUserAccount<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8 + 1,
        seeds = [b"user_account", user.key().as_ref()], // Predictable seeds
        bump
    )]
    pub user_account: Account<'info, UserAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CreateUserVault<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8,
        seeds = [user.key().as_ref()], // Only user key - very predictable
        bump
    )]
    pub vault: Account<'info, UserVault>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct InitializeGlobalConfig<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8 + 1,
        seeds = [b"global_config"], // No user-specific component
        bump
    )]
    pub global_config: Account<'info, GlobalConfig>,
    #[account(mut)]
    pub user: Signer<'info>, // Anyone can be the initializer
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CreatePredictablePDA<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8,
        seeds = [b"pda", user.key().as_ref()], // Simple predictable pattern
        bump
    )]
    pub pda_account: Account<'info, PDAAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct InitializeSimpleAccount<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8,
        seeds = [b"simple", user.key().as_ref()], // Another predictable pattern
        bump
    )]
    pub simple_account: Account<'info, SimpleAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct UserAccount {
    pub owner: Pubkey,
    pub balance: u64,
    pub initialized: bool,
}

#[account]
pub struct UserVault {
    pub owner: Pubkey,
    pub balance: u64,
}

#[account]
pub struct GlobalConfig {
    pub admin: Pubkey,
    pub fee_rate: u64,
    pub initialized: bool,
}

#[account]
pub struct PDAAccount {
    pub owner: Pubkey,
    pub data: u64,
}

#[account]
pub struct SimpleAccount {
    pub creator: Pubkey,
    pub value: u64,
}