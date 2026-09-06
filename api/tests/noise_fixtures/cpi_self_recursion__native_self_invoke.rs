// Fixed: the dispatcher refuses to re-enter its own dispatch entry point.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    instruction::Instruction,
    program::invoke,
    pubkey::Pubkey,
};

pub const DISPATCH_SELECTOR: u8 = 3;

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let iter = &mut accounts.iter();
    let queue_info = next_account_info(iter)?;

    let ix: Instruction = decode_instruction(&queue_info.data.borrow())?;
    if &ix.program_id != program_id {
        return Err(solana_program::program_error::ProgramError::IncorrectProgramId);
    }
    if ix.data.first() == Some(&DISPATCH_SELECTOR) {
        return Err(solana_program::program_error::ProgramError::InvalidInstructionData);
    }

    invoke(&ix, accounts)?;
    Ok(())
}
