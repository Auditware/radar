use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

const ADMIN_PUBKEY: Pubkey = Pubkey::new_from_array([
    17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17,
    17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 18
]);

#[program]
pub mod account_precreation_dos_secure {
    use super::*;

    pub fn initialize_user_account(ctx: Context<InitializeUserAccount>, nonce: u64) -> Result<()> {
        // SECURE: Validate account state before initialization
        let user_account = &mut ctx.accounts.user_account;
        
        require!(
            user_account.owner == Pubkey::default(),
            ErrorCode::AccountAlreadyInitialized
        );
        
        require!(
            !user_account.initialized,
            ErrorCode::AccountAlreadyInitialized
        );
        
        user_account.owner = ctx.accounts.user.key();
        user_account.balance = 0;
        user_account.initialized = true;
        user_account.nonce = nonce;
        
        Ok(())
    }

    pub fn create_user_vault(ctx: Context<CreateUserVault>) -> Result<()> {
        // SECURE: Check account state and add entropy to seeds
        let vault = &mut ctx.accounts.vault;
        
        require!(
            vault.owner == Pubkey::default(),
            ErrorCode::AccountAlreadyInitialized
        );
        
        vault.owner = ctx.accounts.user.key();
        vault.balance = 0;
        Ok(())
    }

    pub fn initialize_global_config(ctx: Context<InitializeGlobalConfig>) -> Result<()> {
        // SECURE: Access control for global PDA creation
        require!(
            ctx.accounts.admin.key() == ADMIN_PUBKEY,
            ErrorCode::Unauthorized
        );
        
        let config = &mut ctx.accounts.global_config;
        
        require!(
            !config.initialized,
            ErrorCode::AccountAlreadyInitialized
        );
        
        config.admin = ctx.accounts.admin.key();
        config.fee_rate = 100;
        config.initialized = true;
        Ok(())
    }

    pub fn create_entropy_pda(ctx: Context<CreateEntropyPDA>, salt: [u8; 32]) -> Result<()> {
        // SECURE: Using entropy/salt to make PDA unpredictable
        let pda_account = &mut ctx.accounts.pda_account;
        
        require!(
            pda_account.owner == Pubkey::default(),
            ErrorCode::AccountAlreadyInitialized
        );
        
        pda_account.owner = ctx.accounts.user.key();
        pda_account.data = 42;
        pda_account.salt = salt;
        Ok(())
    }

    pub fn initialize_versioned_account(ctx: Context<InitializeVersionedAccount>) -> Result<()> {
        // SECURE: Version and slot-based seeds for uniqueness
        let account = &mut ctx.accounts.versioned_account;
        
        require!(
            account.creator == Pubkey::default(),
            ErrorCode::AccountAlreadyInitialized
        );
        
        let clock = Clock::get()?;
        
        account.creator = ctx.accounts.user.key();
        account.value = 100;
        account.creation_slot = clock.slot;
        Ok(())
    }

    pub fn create_time_locked_account(ctx: Context<CreateTimeLockedAccount>) -> Result<()> {
        // SECURE: Time-based component prevents predictable precreation
        let account = &mut ctx.accounts.time_locked_account;
        
        require!(
            account.owner == Pubkey::default(),
            ErrorCode::AccountAlreadyInitialized
        );
        
        let clock = Clock::get()?;
        
        // Ensure account creation is within valid time window
        require!(
            clock.unix_timestamp >= account.unlock_time,
            ErrorCode::AccountNotUnlocked
        );
        
        account.owner = ctx.accounts.user.key();
        account.balance = 0;
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(nonce: u64)]
pub struct InitializeUserAccount<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8 + 1 + 8,
        seeds = [
            b"user_account_v2",
            user.key().as_ref(),
            &nonce.to_le_bytes() // Add nonce for uniqueness
        ],
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
        seeds = [
            b"user_vault_v3",
            user.key().as_ref(),
            &Clock::get().unwrap().slot.to_le_bytes() // Add slot for entropy
        ],
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
        payer = admin,
        space = 8 + 32 + 8 + 1,
        seeds = [b"global_config"],
        bump,
        constraint = admin.key() == ADMIN_PUBKEY @ ErrorCode::Unauthorized
    )]
    pub global_config: Account<'info, GlobalConfig>,
    #[account(mut)]
    pub admin: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(salt: [u8; 32])]
pub struct CreateEntropyPDA<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8 + 32,
        seeds = [
            b"entropy_pda",
            user.key().as_ref(),
            &salt // User-provided entropy
        ],
        bump
    )]
    pub pda_account: Account<'info, EntropyPDAAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct InitializeVersionedAccount<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8 + 8,
        seeds = [
            b"versioned_v1",
            user.key().as_ref(),
            &Clock::get().unwrap().slot.to_le_bytes()
        ],
        bump
    )]
    pub versioned_account: Account<'info, VersionedAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CreateTimeLockedAccount<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8 + 8,
        seeds = [
            b"time_locked",
            user.key().as_ref(),
            &Clock::get().unwrap().unix_timestamp.to_le_bytes()
        ],
        bump
    )]
    pub time_locked_account: Account<'info, TimeLockedAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct UserAccount {
    pub owner: Pubkey,
    pub balance: u64,
    pub initialized: bool,
    pub nonce: u64,
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
pub struct EntropyPDAAccount {
    pub owner: Pubkey,
    pub data: u64,
    pub salt: [u8; 32],
}

#[account]
pub struct VersionedAccount {
    pub creator: Pubkey,
    pub value: u64,
    pub creation_slot: u64,
}

#[account]
pub struct TimeLockedAccount {
    pub owner: Pubkey,
    pub balance: u64,
    pub unlock_time: i64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Account already initialized")]
    AccountAlreadyInitialized,
    #[msg("Unauthorized")]
    Unauthorized,
    #[msg("Account not unlocked yet")]
    AccountNotUnlocked,
}