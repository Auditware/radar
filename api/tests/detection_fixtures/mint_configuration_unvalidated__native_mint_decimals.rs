// Native spelling: the mint is unpacked, and its decimals are read but never
// compared against what the pool was configured for.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    pubkey::Pubkey,
};
use spl_token::state::Mint;

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64) -> ProgramResult {
    let iter = &mut accounts.iter();
    let pool_info = next_account_info(iter)?;
    let mint_info = next_account_info(iter)?;

    if mint_info.owner != &spl_token::ID {
        return Err(solana_program::program_error::ProgramError::IllegalOwner);
    }
    let mint = Mint::unpack(&mint_info.data.borrow())?;

    // VULN: `mint.decimals` is loaded and then ignored.
    credit_pool(pool_info, amount)?;
    Ok(())
}
