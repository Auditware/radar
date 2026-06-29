use anchor_lang::prelude::*;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod unvalidated_cpi_context_program {
    use super::*;

    pub fn issue_tokens(ctx: Context<IssueTokens>, amount: u64) -> Result<()> {
        let external_program = &ctx.remaining_accounts[0];
        require_keys_eq!(
            external_program.key(),
            expected_program::ID,
            ErrorCode::InvalidProgram
        );

        external_program::cpi::transfer(
            CpiContext::new_with_signer(
                external_program.to_account_info(),
                external_program::cpi::accounts::Transfer {
                    from: ctx.accounts.vault.to_account_info(),
                    to: ctx.accounts.recipient.to_account_info(),
                },
                &[&[b"vault", &[ctx.bumps.vault]]],
            ),
            amount,
        )?;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct IssueTokens<'info> {
    #[account(mut, seeds = [b"vault"], bump)]
    pub vault: Account<'info, Vault>,
    pub recipient: AccountInfo<'info>,
}

#[account]
pub struct Vault {
    pub balance: u64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid CPI program")]
    InvalidProgram,
}

mod expected_program {
    use anchor_lang::prelude::*;

    pub const ID: Pubkey = Pubkey::new_from_array([7u8; 32]);
}

mod external_program {
    pub mod cpi {
        use anchor_lang::prelude::*;

        pub mod accounts {
            use anchor_lang::prelude::*;

            pub struct Transfer<'info> {
                pub from: AccountInfo<'info>,
                pub to: AccountInfo<'info>,
            }
        }

        use accounts::Transfer;

        pub fn transfer<'info>(
            _ctx: CpiContext<'_, '_, '_, 'info, Transfer<'info>>,
            _amount: u64,
        ) -> Result<()> {
            Ok(())
        }
    }
}
