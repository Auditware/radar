// Safe pattern - native instructions-sysvar introspection done correctly.
//
// Same shape as the unchecked fixture, but using the `_checked` loaders, which
// verify the account is the real Instructions sysvar before reading it. The rule
// must stay silent: the `_checked` names are distinct identifiers, so a name
// match on the unchecked loaders never fires here.
use solana_program::account_info::{next_account_info, AccountInfo};
use solana_program::entrypoint::ProgramResult;
use solana_program::pubkey::Pubkey;
use solana_program::sysvar::instructions::{load_current_index_checked, load_instruction_at_checked};

pub fn process(_program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let instructions_account = next_account_info(account_info_iter)?;

    let index = load_current_index_checked(instructions_account)?;
    let _current = load_instruction_at_checked(
        (index as usize).saturating_sub(1),
        instructions_account,
    )?;

    Ok(())
}
