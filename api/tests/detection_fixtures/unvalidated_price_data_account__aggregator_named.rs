use anchor_lang::prelude::*;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");
#[program]
pub mod prog {
    use super::*;
    // VULN: reads oracle data from an unvalidated account
    pub fn read_rate(ctx: Context<ReadRate>) -> Result<()> {
        let data = ctx.accounts.aggregator.try_borrow_data()?;
        msg!("rate bytes {}", data.len());
        Ok(())
    }
}
#[derive(Accounts)]
pub struct ReadRate<'info> {
    /// CHECK: unvalidated
    pub aggregator: AccountInfo<'info>,
    pub authority: Signer<'info>,
}
