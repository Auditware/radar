// Share issuance that rounds in the depositor's favour. Minting the ceiling of
// the share count hands out marginally more than was paid for, every time.
pub fn shares_for_deposit(amount: u64, total_shares: u64, total_assets: u64) -> Option<u64> {
    if total_assets == 0 {
        return Some(amount);
    }
    let numerator = (amount as u128).checked_mul(total_shares as u128)?;
    let denominator = total_assets as u128;
    // VULN: ceiling, in the direction that favours the depositor.
    numerator
        .checked_add(denominator)?
        .checked_sub(1)?
        .checked_div(denominator)
        .and_then(|v| u64::try_from(v).ok())
}
