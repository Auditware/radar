// Two accounts of the same type, both created by this instruction. They cannot
// be the same account: creating one address twice fails, so the runtime makes
// the duplicate impossible and there is nothing to check.
//
// Anchor's own bench program initialises many accounts this way, and reporting
// them was 168 of this rule's 210 findings on real code.
use anchor_lang::prelude::*;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod prog {
    use super::*;
    pub fn create_two(ctx: Context<CreateTwo>) -> Result<()> { Ok(()) }
}

#[derive(Accounts)]
pub struct CreateTwo<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    #[account(init, payer = payer, space = 16)]
    pub slot_a: Account<'info, Slot>,
    #[account(init, payer = payer, space = 16)]
    pub slot_b: Account<'info, Slot>,
    pub system_program: Program<'info, System>,
}

#[account]
pub struct Slot { pub value: u64 }
