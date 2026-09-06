// Real shape: a balance updated with a plain operator on primitive integers and
// the result stored. Nothing here returns an Option, nothing indexes, nothing is
// a float, and no `checked_`/`saturating_` call appears - so every exemption the
// rule grew to cut corpus noise has to leave this one alone.
pub struct Vault {
    pub balance: u64,
}

impl Vault {
    pub fn deposit(&mut self, amount: u64) {
        // VULN: wraps to a near-zero balance when the sum exceeds u64::MAX,
        // silently, in release builds without overflow-checks.
        self.balance = self.balance + amount;
    }

    pub fn fee(&self, rate: u64) -> u64 {
        self.balance * rate
    }
}
