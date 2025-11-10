use anchor_lang::prelude::*;
use anchor_lang::solana_program::sysvar::{clock, Sysvar};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod unvalidated_sysvar_accounts {
    use super::*;

    pub fn get_timestamp(ctx: Context<GetTimestamp>) -> Result<()> {
        require!(
            ctx.accounts.clock.key() == &clock::ID,
            ErrorCode::InvalidSysvar
        );
        
        let clock_data = &ctx.accounts.clock.data.borrow();
        let clock_account = Clock::try_deserialize(&mut &clock_data[..])?;
        
        msg!("Timestamp: {}", clock_account.unix_timestamp);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct GetTimestamp<'info> {
    pub clock: AccountInfo<'info>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid sysvar account")]
    InvalidSysvar,
}
