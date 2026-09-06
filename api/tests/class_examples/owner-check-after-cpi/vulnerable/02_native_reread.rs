// Native. Same class, different spelling: the owner is proved once up front,
// a CPI runs, and the account's data is unpacked again afterwards. The check
// happened before the CPI, so it says nothing about the account after it.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    program::invoke,
    pubkey::Pubkey,
};
use spl_token::state::Account as TokenAccount;

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let iter = &mut accounts.iter();
    let vault_info = next_account_info(iter)?;
    let hook_info = next_account_info(iter)?;

    if vault_info.owner != program_id {
        return Err(solana_program::program_error::ProgramError::IllegalOwner);
    }

    invoke(&build_hook(hook_info), &[hook_info.clone(), vault_info.clone()])?;

    // VULN: re-read after the CPI, still trusting the pre-CPI ownership proof.
    let vault = TokenAccount::unpack(&vault_info.data.borrow())?;
    credit(vault.amount);
    Ok(())
}
