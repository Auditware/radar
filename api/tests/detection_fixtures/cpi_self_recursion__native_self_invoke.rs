// Native spelling. The instruction to dispatch is decoded from account data and
// invoked with no restriction on re-entering this program's own entry points -
// so the dispatcher can be pointed back at itself while the outer call is still
// on the stack.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    instruction::Instruction,
    program::invoke,
    pubkey::Pubkey,
};

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let iter = &mut accounts.iter();
    let queue_info = next_account_info(iter)?;

    let ix: Instruction = decode_instruction(&queue_info.data.borrow())?;
    if &ix.program_id != program_id {
        return Err(solana_program::program_error::ProgramError::IncorrectProgramId);
    }

    // VULN: nothing says which of this program's instructions may be re-entered.
    invoke(&ix, accounts)?;
    Ok(())
}
