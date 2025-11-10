use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod cpi_authority_bypass {
    use super::*;

    pub fn create_authority(ctx: Context<CreateAuthority>) -> Result<()> {
        let authority = Pubkey::new_unique();
        ctx.accounts.config.authority = authority;
        msg!("Created authority: {:?}", authority);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CreateAuthority<'info> {
    #[account(mut)]
    pub config: Account<'info, Config>,
    pub admin: Signer<'info>,
}

#[account]
pub struct Config {
    pub authority: Pubkey,
}
