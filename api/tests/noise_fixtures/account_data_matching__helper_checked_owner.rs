// Safe pattern - the native spelling of an owner check.
//
// A native Solana program does not write `require!`; it hands the account to a
// named helper. Accepting only the Anchor macro reported every SPL, Solend and
// stake-pool function that verified ownership perfectly well.
//
// The binding hop matters as much as the helper: the guard names `mint_info`
// and the unpack names `mint_data`, so a rule that does not follow the `let`
// once still sees an unproved account.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    pubkey::Pubkey,
};
use spl_token::state::Mint;

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let mint_info = next_account_info(account_info_iter)?;

    check_account_owner(program_id, mint_info)?;

    let mint_data = mint_info.data.borrow();
    let _mint = Mint::unpack(&mint_data)?;

    Ok(())
}

fn check_account_owner(program_id: &Pubkey, account_info: &AccountInfo) -> ProgramResult {
    if account_info.owner != program_id {
        return Err(solana_program::program_error::ProgramError::IllegalOwner);
    }
    Ok(())
}
