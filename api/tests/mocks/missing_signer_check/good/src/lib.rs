use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_signer_check {
    use super::*;

    pub fn update_authority(ctx: Context<UpdateAuthority>, new_authority: Pubkey) -> Result<()> {
        ctx.accounts.config.authority = new_authority;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct UpdateAuthority<'info> {
    #[account(mut)]
    pub config: Account<'info, Config>,
    #[account(constraint = authority.key() == config.authority)]
    pub authority: Signer<'info>,
}

#[account]
pub struct Config {
    pub authority: Pubkey,
}
