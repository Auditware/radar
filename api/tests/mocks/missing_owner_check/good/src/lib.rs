use anchor_lang::prelude::*;
use anchor_lang::solana_program::program_pack::Pack;
use spl_token::state::Account as SplTokenAccount;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_owner_check {
    use super::*;

    pub fn log_message(ctx: Context<LogMessage>) -> Result<()> {
        // Fix: verify the account is owned by the SPL token program before
        // trusting its unpacked data.
        if ctx.accounts.token.owner != &spl_token::ID {
            return err!(ErrorCode::InvalidOwner);
        }
        let token = SplTokenAccount::unpack(&ctx.accounts.token.data.borrow())?;
        msg!("Your account balance is: {}", token.amount);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct LogMessage<'info> {
    /// CHECK: raw account, unpacked manually
    pub token: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid account owner")]
    InvalidOwner,
}
