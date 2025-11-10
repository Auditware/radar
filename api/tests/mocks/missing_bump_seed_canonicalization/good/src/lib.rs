use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_bump_seed_canonicalization {
    use super::*;

    pub fn create_pda(ctx: Context<CreatePDA>) -> Result<()> {
        let seeds = &[
            b"pda",
            ctx.accounts.authority.key.as_ref(),
            &[ctx.bumps.pda_account],
        ];
        let (pda, _bump) = Pubkey::find_program_address(seeds, ctx.program_id);
        msg!("Created PDA: {:?}", pda);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CreatePDA<'info> {
    #[account(mut, seeds = [b"pda", authority.key().as_ref()], bump)]
    pub pda_account: AccountInfo<'info>,
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}
