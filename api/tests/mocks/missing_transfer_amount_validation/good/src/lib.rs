use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod missing_transfer_amount_validation {
    use super::*;

    pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
        // Fix: the caller-supplied amount is checked against the deposit this
        // caller is actually entitled to before the vault is drained.
        require!(
            amount <= ctx.accounts.position.deposited,
            ErrorCode::AmountExceedsDeposit
        );

        let position = &mut ctx.accounts.position;
        position.deposited = position.deposited - amount;

        let seeds = &[b"vault".as_ref(), &[ctx.accounts.vault_authority.bump]];
        let signer = &[&seeds[..]];
        let cpi_accounts = token::Transfer {
            from: ctx.accounts.vault.to_account_info(),
            to: ctx.accounts.destination.to_account_info(),
            authority: ctx.accounts.vault_authority.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer);
        token::transfer(cpi_ctx, amount)?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub vault: Account<'info, TokenAccount>,
    #[account(mut)]
    pub destination: Account<'info, TokenAccount>,
    #[account(mut, has_one = user)]
    pub position: Account<'info, Position>,
    pub vault_authority: Account<'info, VaultAuthority>,
    pub user: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct Position {
    pub user: Pubkey,
    pub deposited: u64,
}

#[account]
pub struct VaultAuthority {
    pub bump: u8,
}

#[error_code]
pub enum ErrorCode {
    #[msg("amount exceeds deposit")]
    AmountExceedsDeposit,
}
