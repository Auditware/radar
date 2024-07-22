use anchor_lang::prelude::*;

declare_id!("2dw63oeymi8aCrAAXQ2Wy54nYk8epKqwBD5wjPbdppKy");

#[program]
pub mod anchor_test {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize {}