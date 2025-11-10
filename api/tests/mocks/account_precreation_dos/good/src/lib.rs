use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod account_precreation_dos {
    use super::*;

    pub fn initialize_user(ctx: Context<InitializeUser>, owner: Pubkey) -> Result<()> {
        let user_account = &mut ctx.accounts.user_account;
        
        require!(
            user_account.owner == Pubkey::default(),
            ErrorCode::AlreadyInitialized
        );
        
        user_account.owner = owner;
        user_account.key = *ctx.accounts.payer.key;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeUser<'info> {
    #[account(init, payer = payer, space = 8 + 64)]
    pub user_account: Account<'info, UserAccount>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct UserAccount {
    pub owner: Pubkey,
    pub key: Pubkey,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Account already initialized")]
    AlreadyInitialized,
}
