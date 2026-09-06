use anchor_lang::prelude::*;

// The test module sits ABOVE the production code on purpose. Pruning items
// before span enrichment would shift every line below this block, so the
// finding would move when --include-tests is off. It must not.
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reuses_a_pda_and_skips_the_owner_check() {
        let vault = AccountInfo::default();
        let data = vault.try_borrow_data().unwrap();
        assert!(data.len() > 0);
    }
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    pub authority: Signer<'info>,
    /// CHECK: deliberately unvalidated - this is the finding under test
    pub vault: UncheckedAccount<'info>,
}

pub fn withdraw(ctx: Context<Withdraw>) -> Result<()> {
    let vault = &ctx.accounts.vault;
    let raw = vault.try_borrow_data()?;
    let state = VaultState::try_from_slice(&raw)?;
    msg!("balance {}", state.balance);
    Ok(())
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct VaultState {
    pub balance: u64,
}
