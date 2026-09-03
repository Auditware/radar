// Safe pattern - a CPI wrapper, which is what most of this rule's noise was.
//
// Every account and the signer seeds arrive as parameters. This function chose
// nothing and so has nothing to prove: whichever handler called it is the one
// that picked the accounts and owes the check. Reporting here asserts the
// program validated nothing, when what actually happened is that the validation
// is one frame up, out of reach.
use solana_program::{
    account_info::AccountInfo, entrypoint::ProgramResult, program::invoke_signed,
    system_instruction,
};

fn create_stake_account(
    stake_account_info: AccountInfo<'_>,
    stake_account_signer_seeds: &[&[u8]],
    stake_space: u64,
) -> ProgramResult {
    invoke_signed(
        &system_instruction::allocate(stake_account_info.key, stake_space),
        &[stake_account_info.clone()],
        &[stake_account_signer_seeds],
    )
}
