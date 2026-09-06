// Safe patterns - two shapes where a wrap is either impossible or already
// handled, and neither is spelled `checked_add`.
//
// A wrapped index is not a silent wrap: the slice bounds check catches it and
// panics, which is the whole difference between this rule's subject and an
// out-of-range read.
//
// The fallible-operator shape is stronger still. `(a + b)?` does not compile
// for two u64s - `?` needs an Option or a Result - so reaching this line at all
// proves the program overloaded the operator to return one. That is checked
// arithmetic, written through the type system instead of through a method name.
pub struct Lamports(pub u64);

impl core::ops::Add for Lamports {
    type Output = Option<Lamports>;
    fn add(self, other: Lamports) -> Option<Lamports> {
        self.0.checked_add(other.0).map(Lamports)
    }
}

impl core::ops::Sub for Lamports {
    type Output = Option<Lamports>;
    fn sub(self, other: Lamports) -> Option<Lamports> {
        self.0.checked_sub(other.0).map(Lamports)
    }
}

pub fn read_header(data: &[u8], index: usize) -> u16 {
    // Index and slice-bound arithmetic: an overflow here indexes past the end
    // and panics rather than wrapping unseen.
    let first = data[index + 1];
    let pair = &data[index..index + 2];
    u16::from(first).rotate_left(u32::from(pair[0]))
}

pub fn settle(balance: Lamports, amount: Lamports) -> Option<Lamports> {
    let credited = (balance + amount)?;
    let debited = (credited - amount).expect("does not underflow, just credited");
    Some(debited)
}
