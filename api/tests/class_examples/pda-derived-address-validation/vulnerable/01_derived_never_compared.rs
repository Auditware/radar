// The program derives the PDA it expects and then never compares it to the
// account it was actually handed. Deriving proves what the address *should* be;
// only the comparison makes that mean anything.
use anchor_lang::prelude::*;
declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod lending {
    use super::*;
    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        let (_expected, _bump) = Pubkey::find_program_address(
            &[b"reserve", ctx.accounts.market.key().as_ref()],
            ctx.program_id,
        );

        // VULN: `_expected` is discarded; any account of the right type passes.
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
