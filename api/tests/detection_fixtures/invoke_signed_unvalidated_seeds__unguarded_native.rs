// Real shape: a native handler that picks its own accounts off the instruction
// and lends the program's PDA signature to a target the caller supplied, with
// no check of any kind in between.
//
// This is the case the rule exists for, and it has to survive the exemptions
// added for CPI wrappers and for named `check_*` helpers - there is no wrapper
// here (the accounts come from `next_account_info`) and no helper is called.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    instruction::Instruction,
    program::invoke_signed,
    pubkey::Pubkey,
};

pub fn process(_program_id: &Pubkey, accounts: &[AccountInfo], bump: u8) -> ProgramResult {
    let account_info_iter = &mut accounts.iter();
    let authority_info = next_account_info(account_info_iter)?;
    let target_program_info = next_account_info(account_info_iter)?;

    // VULN: `target_program_info` is whatever the caller passed. Nothing pins
    // it, and the next line signs for it with the program's own PDA.
    let ix = Instruction {
        program_id: *target_program_info.key,
        accounts: vec![],
        data: vec![],
    };

    invoke_signed(
        &ix,
        &[authority_info.clone()],
        &[&[b"authority", &[bump]]],
    )
}
