use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_bump_seed_canonicalization {
    use super::*;

    pub fn create_pda(ctx: Context<CreatePDA>, bump: u8) -> Result<()> {
        let seeds = &[
            b"pda",
            ctx.accounts.authority.key.as_ref(),
            &[bump],
        ];
        let pda = Pubkey::create_program_address(seeds, ctx.program_id)?;
        msg!("Created PDA: {:?}", pda);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CreatePDA<'info> {
    #[account(mut)]
    pub pda_account: AccountInfo<'info>,
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}
