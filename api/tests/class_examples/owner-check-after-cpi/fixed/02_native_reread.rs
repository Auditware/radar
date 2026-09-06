// Fixed: the owner is checked again after the CPI, immediately before the data
// is unpacked and trusted.
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

    if vault_info.owner != program_id {
        return Err(solana_program::program_error::ProgramError::IllegalOwner);
    }
    let vault = TokenAccount::unpack(&vault_info.data.borrow())?;
    credit(vault.amount);
    Ok(())
}
