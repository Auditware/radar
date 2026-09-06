// Fixed: the mint's decimals must match the pool's configured value.
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint::ProgramResult,
    pubkey::Pubkey,
};
use spl_token::state::Mint;

pub fn process(program_id: &Pubkey, accounts: &[AccountInfo], amount: u64) -> ProgramResult {
    let iter = &mut accounts.iter();
    let pool_info = next_account_info(iter)?;
    let mint_info = next_account_info(iter)?;

    if mint_info.owner != &spl_token::ID {
        return Err(solana_program::program_error::ProgramError::IllegalOwner);
    }
    let mint = Mint::unpack(&mint_info.data.borrow())?;

    if mint.decimals != pool_decimals(pool_info)? {
        return Err(solana_program::program_error::ProgramError::InvalidAccountData);
    }
    credit_pool(pool_info, amount)?;
    Ok(())
}
