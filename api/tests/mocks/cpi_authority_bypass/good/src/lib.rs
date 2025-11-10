use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod cpi_authority_bypass {
    use super::*;

    pub fn set_authority(ctx: Context<SetAuthority>, new_authority: Pubkey) -> Result<()> {
        require!(
            ctx.accounts.admin.key() == ctx.accounts.config.authority,
            ErrorCode::Unauthorized
        );
        ctx.accounts.config.authority = new_authority;
        msg!("Updated authority to: {:?}", new_authority);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct SetAuthority<'info> {
    #[account(mut)]
    pub config: Account<'info, Config>,
    pub admin: Signer<'info>,
}

#[account]
pub struct Config {
    pub authority: Pubkey,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Unauthorized")]
    Unauthorized,
}
