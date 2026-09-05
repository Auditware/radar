// Real shape, and the one a function-scoped exemption gets wrong: two accounts
// are unpacked, one of them is proved and the other is not.
//
// The rule asks whether *this* account was checked, not whether the function
// checked something. Asking per function lets `check_account_owner(mint_info)`
// stand in for the `evil_info` unpacked right beside it - which is how this bug
// gets past review in the first place, since the file plainly contains an owner
// check.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    pubkey::Pubkey,
};
use spl_token::state::Mint;

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let mint_info = next_account_info(account_info_iter)?;
    let evil_info = next_account_info(account_info_iter)?;

    // This one is proved.
    check_account_owner(program_id, mint_info)?;
    let mint_data = mint_info.data.borrow();
    let _mint = Mint::unpack(&mint_data)?;

    // VULN: and this one is not. Nothing says `evil_info` is a mint this
    // program owns, but its bytes are read as one anyway.
    let _evil = Mint::unpack(&evil_info.data.borrow())?;

    Ok(())
}

fn check_account_owner(program_id: &Pubkey, account_info: &AccountInfo) -> ProgramResult {
    if account_info.owner != program_id {
        return Err(solana_program::program_error::ProgramError::IllegalOwner);
    }
    Ok(())
}
