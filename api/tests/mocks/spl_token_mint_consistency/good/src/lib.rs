use anchor_lang::prelude::*;
use anchor_spl::token::{Mint, Token, TokenAccount};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod spl_token_mint_consistency {
    use super::*;

    pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
        let _whitelisted_mint: &Account<Mint> = &ctx.accounts.mint;
        let _source_account: &Account<TokenAccount> = &ctx.accounts.from;
        require_keys_eq!(
            ctx.accounts.from.mint,
            ctx.accounts.mint.key(),
            ErrorCode::InvalidMint
        );

        anchor_spl::token::transfer(
            CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                anchor_spl::token::Transfer {
                    from: ctx.accounts.from.to_account_info(),
                    to: ctx.accounts.vault.to_account_info(),
                    authority: ctx.accounts.depositor.to_account_info(),
                },
            ),
            amount,
        )?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Deposit<'info> {
    pub depositor: Signer<'info>,
    #[account(seeds = [b"whitelist", mint.key().as_ref()], bump)]
    pub whitelist: Account<'info, Whitelist>,
    pub mint: Account<'info, Mint>,
    #[account(mut, constraint = from.mint == mint.key())]
    pub from: Account<'info, TokenAccount>,
    #[account(mut)]
    pub vault: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct Whitelist {
    pub authority: Pubkey,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid token mint")]
    InvalidMint,
}
