// Native spelling. The system program is taken from the account list and used
// to create an account, with nothing pinning it to the real system program.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program::invoke_signed,
    pubkey::Pubkey,
    system_instruction,
};

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let iter = &mut accounts.iter();
    let payer_info = next_account_info(iter)?;
    let new_account_info = next_account_info(iter)?;
    // VULN: never compared against `system_program::ID`.
    let system_program_info = next_account_info(iter)?;

    let ix = system_instruction::create_account(payer_info.key, new_account_info.key, 1, 0, program_id);
    invoke_signed(
        &ix,
        &[payer_info.clone(), new_account_info.clone(), system_program_info.clone()],
        &[],
    )?;
    Ok(())
}
