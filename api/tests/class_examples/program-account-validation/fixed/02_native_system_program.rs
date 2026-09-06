// Fixed: the passed program account is compared against the real system program
// before anything is dispatched through it.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program::invoke_signed,
    pubkey::Pubkey,
    system_instruction, system_program,
};

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let iter = &mut accounts.iter();
    let payer_info = next_account_info(iter)?;
    let new_account_info = next_account_info(iter)?;
    let system_program_info = next_account_info(iter)?;

    if system_program_info.key != &system_program::ID {
        return Err(solana_program::program_error::ProgramError::IncorrectProgramId);
    }

    let ix = system_instruction::create_account(payer_info.key, new_account_info.key, 1, 0, program_id);
    invoke_signed(
        &ix,
        &[payer_info.clone(), new_account_info.clone(), system_program_info.clone()],
        &[],
    )?;
    Ok(())
}
