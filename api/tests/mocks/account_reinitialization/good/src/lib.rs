use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod account_reinitialization {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, owner: Pubkey) -> Result<()> {
        let config = &mut ctx.accounts.config;
        
        require!(!config.initialized, ErrorCode::AlreadyInitialized); // Fix: Check prevents reinitialization
        
        config.owner = owner;
        config.initialized = true;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = payer, space = 8 + 33)]
    pub config: Account<'info, Config>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Config {
    pub owner: Pubkey,
    pub initialized: bool,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Already initialized")]
    AlreadyInitialized,
}
