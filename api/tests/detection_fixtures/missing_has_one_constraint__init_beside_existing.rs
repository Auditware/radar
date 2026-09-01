use anchor_lang::prelude::*;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");
#[program]
pub mod prog {
    use super::*;
    pub fn create_under(ctx: Context<CreateUnder>) -> Result<()> { Ok(()) }
}
#[derive(Accounts)]
pub struct CreateUnder<'info> {
    #[account(init, payer = authority, space = 64)]
    pub new_item: Account<'info, Item>,
    // VULN: existing vault has a stored authority but no has_one binding it
    #[account(mut)]
    pub vault: Account<'info, Vault>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}
#[account]
pub struct Item { pub v: u64 }
#[account]
pub struct Vault { pub authority: Pubkey, pub balance: u64 }
