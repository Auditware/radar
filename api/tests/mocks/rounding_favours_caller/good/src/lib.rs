// Fixed: the protocol's fee is rounded up, so no call leaves it short.
pub struct Fee { pub numerator: u64, pub denominator: u64 }

impl Fee {
    pub fn apply(&self, amount: u64) -> Option<u64> {
        if self.denominator == 0 {
            return Some(0);
        }
        let numerator = (amount as u128).checked_mul(self.numerator as u128)?;
        let denominator = self.denominator as u128;
        numerator
            .checked_add(denominator)?
            .checked_sub(1)?
            .checked_div(denominator)
            .and_then(|v| u64::try_from(v).ok())
    }
}
