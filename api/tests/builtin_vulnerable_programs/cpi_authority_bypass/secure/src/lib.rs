use anchor_lang::prelude::*;

declare_id!("11111111111111111111111111111111");

const ADMIN_PUBKEY: &str = "11111111111111111111111111111112";
const AUTHORIZED_CALLER: &str = "11111111111111111111111111111113";

#[program]
pub mod cpi_authority_bypass_secure {
    use super::*;

    pub fn secure_transfer(ctx: Context<SecureTransfer>, amount: u64) -> Result<()> {
        // SECURE: Validate authority before any operation
        require!(
            ctx.accounts.authority.is_signer,
            ErrorCode::MissingSignature
        );
        
        require!(
            is_valid_authority(&ctx.accounts.authority.key()),
            ErrorCode::UnauthorizedAuthority
        );
        
        // SECURE: Check account ownership
        require!(
            ctx.accounts.account.owner == ctx.program_id,
            ErrorCode::InvalidAccountOwnership
        );
        
        msg!("Secure transfer of {} tokens authorized", amount);
        Ok(())
    }

    pub fn secure_delegate(ctx: Context<SecureDelegate>, new_authority: Pubkey) -> Result<()> {
        // SECURE: Validate current authority signature
        require!(
            ctx.accounts.current_authority.is_signer,
            ErrorCode::MissingSignature
        );
        
        // SECURE: Validate delegation permissions
        require!(
            ctx.accounts.caller.key() == ctx.accounts.current_authority.key() ||
            is_authorized_delegator(&ctx.accounts.caller.key()),
            ErrorCode::UnauthorizedDelegation
        );
        
        // SECURE: Validate new authority is not zero
        require!(
            new_authority != Pubkey::default(),
            ErrorCode::InvalidAuthority
        );
        
        msg!("Authority delegated securely to {}", new_authority);
        Ok(())
    }

    pub fn secure_privileged_operation(ctx: Context<SecurePrivilegedOperation>) -> Result<()> {
        // SECURE: Validate caller authority
        require!(
            is_authorized_caller(&ctx.accounts.caller.key()),
            ErrorCode::Unauthorized
        );
        
        // SECURE: Validate caller is signer
        require!(
            ctx.accounts.caller.is_signer,
            ErrorCode::MissingSignature
        );
        
        // SECURE: Validate PDA ownership
        require!(
            ctx.accounts.pda_account.vault == ctx.accounts.vault.key(),
            ErrorCode::InvalidVaultAuthority
        );
        
        // SECURE: Validate PDA bump and seeds
        let (expected_pda, _) = Pubkey::find_program_address(
            &[b"vault_auth", ctx.accounts.vault.key().as_ref()],
            &ctx.program_id
        );
        
        require!(
            ctx.accounts.pda_account.key() == expected_pda,
            ErrorCode::InvalidPDA
        );
        
        msg!("Privileged operation executed securely");
        Ok(())
    }

    pub fn secure_cross_program_call(ctx: Context<SecureCrossProgramCall>) -> Result<()> {
        // SECURE: Validate PDA ownership and seeds
        require!(
            ctx.accounts.pda.owner == ctx.program_id,
            ErrorCode::InvalidPDAOwnership
        );
        
        // SECURE: Validate caller authority
        require!(
            ctx.accounts.user.is_signer,
            ErrorCode::MissingSignature
        );
        
        let (expected_pda, _bump) = Pubkey::find_program_address(
            &[b"cross_program", ctx.accounts.user.key().as_ref()],
            &ctx.program_id
        );
        
        require!(
            ctx.accounts.pda.key() == expected_pda,
            ErrorCode::InvalidPDA
        );
        
        msg!("Cross-program call executed securely");
        Ok(())
    }
}

fn is_authorized_delegator(pubkey: &Pubkey) -> bool {
    // SECURE: Check against whitelist of authorized delegators
    pubkey.to_string() == ADMIN_PUBKEY || pubkey.to_string() == AUTHORIZED_CALLER
}

fn is_valid_authority(pubkey: &Pubkey) -> bool {
    // SECURE: Validate authority is in allowed list
    pubkey.to_string() == ADMIN_PUBKEY || pubkey.to_string() == AUTHORIZED_CALLER
}

fn is_authorized_caller(pubkey: &Pubkey) -> bool {
    // SECURE: Validate caller is authorized
    pubkey.to_string() == ADMIN_PUBKEY || pubkey.to_string() == AUTHORIZED_CALLER
}

#[derive(Accounts)]
pub struct SecureTransfer<'info> {
    #[account(mut)]
    /// CHECK: Account validation in instruction
    pub account: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct SecureDelegate<'info> {
    #[account(mut)]
    /// CHECK: Account validation in instruction
    pub account: AccountInfo<'info>,
    pub current_authority: Signer<'info>,
    pub caller: Signer<'info>,
}

#[derive(Accounts)]
pub struct SecurePrivilegedOperation<'info> {
    #[account(mut)]
    /// CHECK: Vault validation in instruction
    pub vault: AccountInfo<'info>,
    #[account(
        seeds = [b"vault_auth", vault.key().as_ref()],
        bump = pda_account.bump
    )]
    pub pda_account: Account<'info, VaultAuthority>,
    pub caller: Signer<'info>,
}

#[derive(Accounts)]
pub struct SecureCrossProgramCall<'info> {
    #[account(
        seeds = [b"cross_program", user.key().as_ref()],
        bump
    )]
    /// CHECK: PDA validation in instruction
    pub pda: AccountInfo<'info>,
    pub user: Signer<'info>,
}

#[account]
pub struct VaultAuthority {
    pub bump: u8,
    pub vault: Pubkey,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Unauthorized authority")]
    UnauthorizedAuthority,
    #[msg("Missing signature")]
    MissingSignature,
    #[msg("Unauthorized delegation")]
    UnauthorizedDelegation,
    #[msg("Unauthorized")]
    Unauthorized,
    #[msg("Invalid vault authority")]
    InvalidVaultAuthority,
    #[msg("Invalid PDA ownership")]
    InvalidPDAOwnership,
    #[msg("Invalid PDA")]
    InvalidPDA,
    #[msg("Invalid account ownership")]
    InvalidAccountOwnership,
    #[msg("Invalid authority")]
    InvalidAuthority,
}