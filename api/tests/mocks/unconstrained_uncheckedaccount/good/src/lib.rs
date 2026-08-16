use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod unconstrained_uncheckedaccount {
    use super::*;

    pub fn read_oracle(ctx: Context<ReadOracle>) -> Result<()> {
        let _oracle = &ctx.accounts.oracle;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct ReadOracle<'info> {
    /// CHECK: validated by address constraint
    #[account(address = crate::ID)]
    pub oracle: UncheckedAccount<'info>,
    pub user: Signer<'info>,
}
