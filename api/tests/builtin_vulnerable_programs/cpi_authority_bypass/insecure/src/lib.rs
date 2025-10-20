use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod cpi_authority_bypass_insecure {
    use super::*;

    pub fn direct_cpi_call(ctx: Context<DirectCPI>, amount: u64) -> Result<()> {
        // VULNERABLE: Direct CPI call without proper authority validation
        msg!("Making direct CPI call without authority check for amount: {}", amount);
        
        // This would be a vulnerable pattern - direct invocation without proper auth checks
        let _ = &ctx.accounts.target_program;
        let _ = &ctx.accounts.vault_authority;
        Ok(())
    }

    pub fn bypass_authority(ctx: Context<BypassAuthority>) -> Result<()> {
        // VULNERABLE: Uses hardcoded authority without validation
        let new_authority = Pubkey::new_unique(); // Hardcoded authority - vulnerable
        
        msg!("Setting authority to: {}", new_authority);
        // This demonstrates vulnerable authority bypass pattern
        let _ = &ctx.accounts.vault_authority;
        Ok(())
    }

    pub fn privileged_operation(ctx: Context<PrivilegedOperation>, amount: u64) -> Result<()> {
        // VULNERABLE: No authority check before privileged operation
        let bump = 255_u8; // hardcoded bump - vulnerable
        let seeds: &[&[u8]] = &[b"vault", &[bump]];
        
        msg!("Privileged operation with seeds: {:?} and amount: {}", seeds, amount);
        let _ = &ctx.accounts.vault;
        Ok(())
    }

    pub fn dangerous_admin_action(_ctx: Context<DangerousAdmin>, amount: u64) -> Result<()> {
        // VULNERABLE: Uses wrong seeds that bypass authority checks
        let seeds: &[&[u8]] = &[b"wrong_seed", &[255]]; // Wrong seeds
        
        msg!("Admin action with amount: {} and seeds: {:?}", amount, seeds);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct DirectCPI<'info> {
    /// CHECK: This account is not validated - vulnerable pattern
    pub target_program: AccountInfo<'info>,
    /// CHECK: Authority not validated - vulnerable pattern  
    pub vault_authority: AccountInfo<'info>,
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct BypassAuthority<'info> {
    /// CHECK: Authority bypass pattern - not validated
    pub vault_authority: AccountInfo<'info>,
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct PrivilegedOperation<'info> {
    #[account(mut)]
    /// CHECK: Vault account not properly validated
    pub vault: AccountInfo<'info>,
    #[account(mut)]
    /// CHECK: Destination not validated  
    pub destination: AccountInfo<'info>,
    /// CHECK: Authority not checked
    pub vault_authority: AccountInfo<'info>,
    pub caller: Signer<'info>,
    /// CHECK: Admin program not validated
    pub admin_program: AccountInfo<'info>,
}

#[derive(Accounts)]  
pub struct DangerousAdmin<'info> {
    /// CHECK: Admin authority not validated
    pub admin_authority: AccountInfo<'info>,
    pub caller: Signer<'info>,
    pub system_program: Program<'info, System>,
}