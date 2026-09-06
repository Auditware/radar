// Fixed: the derived address is required to equal the account supplied.
use anchor_lang::prelude::*;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod lending {
    use super::*;
    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        let (expected, _bump) = Pubkey::find_program_address(
            &[b"reserve", ctx.accounts.market.key().as_ref()],
            ctx.program_id,
        );
        require_keys_eq!(expected, ctx.accounts.reserve.key(), ErrorCode::WrongReserve);

        ctx.accounts.reserve.liquidity += amount;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(mut)]
    pub reserve: Account<'info, Reserve>,
    pub market: Account<'info, Market>,
    pub authority: Signer<'info>,
}

#[account]
pub struct Reserve { pub liquidity: u64 }
#[account]
pub struct Market { pub id: u64 }

#[error_code]
pub enum ErrorCode { #[msg("wrong reserve")] WrongReserve }
