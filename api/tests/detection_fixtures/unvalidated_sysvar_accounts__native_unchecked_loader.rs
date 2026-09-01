// Real vuln - native (non-Anchor) instructions-sysvar introspection.
//
// The program reads the Instructions sysvar straight from a raw account with the
// unchecked loaders. Nothing pins the account to the real sysvar address, so a
// caller can substitute an account and control what the program sees. This is the
// native form of the Unvalidated Sysvar Account class; the `_checked` variants
// exist to reject a substituted account. The rule MUST report it.
use solana_program::account_info::{next_account_info, AccountInfo};
use solana_program::entrypoint::ProgramResult;
use solana_program::pubkey::Pubkey;
use solana_program::sysvar::instructions::{load_current_index, load_instruction_at};

pub fn process(_program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let instructions_account = next_account_info(account_info_iter)?;

    let index = load_current_index(&instructions_account.try_borrow_data()?);
    let _current = load_instruction_at(
        (index as usize).saturating_sub(1),
        &instructions_account.try_borrow_data()?,
    );

    Ok(())
}
