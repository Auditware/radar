// Safe pattern - sealevel-attacks 9-closing-accounts/recommended.
//
// The idiomatic Anchor close. The only `mut` accounts are the account being
// closed (`close = destination`) and the lamport destination - neither is a
// business-state mutation gated on an unproven caller. "Missing Signer Check"
// must stay silent. It used to fire here (and ONLY here among the three close
// variants) because `#[account(mut, close = ..)]` adds a `mut` that the rule
// counted as state at stake - i.e. it flagged exactly the variant auditors
// recommend while staying silent on the insecure/secure ones that omit `mut`.
use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod closing_accounts_recommended {
    use super::*;

    pub fn close(_ctx: Context<Close>) -> ProgramResult {
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Close<'info> {
    #[account(mut, close = destination)]
    account: Account<'info, Data>,
    #[account(mut)]
    destination: AccountInfo<'info>,
}

#[account]
pub struct Data {
    data: u64,
}
