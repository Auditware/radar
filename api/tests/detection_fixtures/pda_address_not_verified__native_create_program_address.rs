// Native spelling, with the caller supplying the bump. The address is derived
// and used to sign, but the account passed in is never checked against it.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    pubkey::Pubkey,
};

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo], bump: u8) -> ProgramResult {
    let iter = &mut accounts.iter();
    let market_info = next_account_info(iter)?;
    let reserve_info = next_account_info(iter)?;

    let _derived = Pubkey::create_program_address(
        &[b"reserve", market_info.key.as_ref(), &[bump]],
        program_id,
    )?;

    // VULN: `_derived` never meets `reserve_info.key`.
    credit_reserve(reserve_info)?;
    Ok(())
}
