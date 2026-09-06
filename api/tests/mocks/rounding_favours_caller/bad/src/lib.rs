// A fee owed *to* the protocol computed with floor division. Every call rounds
// the protocol's share down, so the shortfall is free to the caller and
// repeating the operation harvests it.
pub struct Fee { pub numerator: u64, pub denominator: u64 }

impl Fee {
    pub fn apply(&self, amount: u64) -> Option<u64> {
        if self.denominator == 0 {
            return Some(0);
        }
        // VULN: floor. The protocol is owed the ceiling of this quotient.
        (amount as u128)
            .checked_mul(self.numerator as u128)?
            .checked_div(self.denominator as u128)
            .and_then(|v| u64::try_from(v).ok())
    }
}
