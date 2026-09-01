use anchor_lang::prelude::*;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");
#[program]
pub mod prog {
    use super::*;
    // VULN: anyone can call this and rewrite the config. No signature required.
    pub fn set_fee(ctx: Context<SetFee>, new_fee: u64) -> Result<()> {
        ctx.accounts.config.fee = new_fee;
        Ok(())
    }
}
#[derive(Accounts)]
pub struct SetFee<'info> {
    #[account(mut)]
    pub config: Account<'info, Config>,
}
#[account]
pub struct Config { pub fee: u64 }
