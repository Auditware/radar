// Fixed: shares are floored, so the depositor never receives more than paid for.
pub fn shares_for_deposit(amount: u64, total_shares: u64, total_assets: u64) -> Option<u64> {
    if total_assets == 0 {
        return Some(amount);
    }
    (amount as u128)
        .checked_mul(total_shares as u128)?
        .checked_div(total_assets as u128)
        .and_then(|v| u64::try_from(v).ok())
}
