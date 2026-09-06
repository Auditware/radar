// Fixed: the derived address is compared to the account before it is used.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    pubkey::Pubkey,
};

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo], bump: u8) -> ProgramResult {
    let iter = &mut accounts.iter();
    let market_info = next_account_info(iter)?;
    let reserve_info = next_account_info(iter)?;

    let derived = Pubkey::create_program_address(
        &[b"reserve", market_info.key.as_ref(), &[bump]],
        program_id,
    )?;
    if &derived != reserve_info.key {
        return Err(solana_program::program_error::ProgramError::InvalidSeeds);
    }

    credit_reserve(reserve_info)?;
    Ok(())
}
