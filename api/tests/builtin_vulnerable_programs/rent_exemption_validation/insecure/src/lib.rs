use anchor_lang::prelude::*;
use anchor_lang::system_program;
use anchor_lang::solana_program::{
    system_instruction,
    program::invoke,
};

declare_id!("11111111111111111111111111111111");

#[program]
pub mod rent_exemption_insecure {
    use super::*;

    pub fn create_account(ctx: Context<CreateAccount>) -> Result<()> {
        // VULNERABLE: Creating account without ensuring rent exemption
        let account_size = 8 + 32 + 64; // discriminator + pubkey + data
        
        let ix = system_instruction::create_account(
            &ctx.accounts.payer.key(),
            &ctx.accounts.new_account.key(),
            1_000_000, // Hardcoded lamports - may not be rent exempt!
            account_size as u64,
            &ctx.program_id,
        );
        
        invoke(
            &ix,
            &[
                ctx.accounts.payer.to_account_info(),
                ctx.accounts.new_account.to_account_info(),
            ],
        )?;
        
        Ok(())
    }

    pub fn withdraw_lamports(ctx: Context<WithdrawLamports>, amount: u64) -> Result<()> {
        // VULNERABLE: Withdrawing lamports without checking rent exemption
        let account_info = ctx.accounts.account.to_account_info();
        **account_info.try_borrow_mut_lamports()? -= amount;
        **ctx.accounts.recipient.try_borrow_mut_lamports()? += amount;
        Ok(())
    }

    pub fn close_account(ctx: Context<CloseAccount>) -> Result<()> {
        // VULNERABLE: Closing account without proper rent handling
        let account = &mut ctx.accounts.account;
        let destination = &mut ctx.accounts.destination;
        
        // Transfer all lamports without validation
        let lamports = account.to_account_info().lamports();
        **account.to_account_info().try_borrow_mut_lamports()? = 0;
        **destination.to_account_info().try_borrow_mut_lamports()? += lamports;
        
        Ok(())
    }

    pub fn resize_account(ctx: Context<ResizeAccount>, new_size: usize) -> Result<()> {
        // VULNERABLE: Resizing account without updating rent exemption
        ctx.accounts.account.to_account_info().realloc(new_size, false)?;
        // New size may require more rent, but we don't add lamports
        Ok(())
    }

    pub fn transfer_with_hardcoded_rent(ctx: Context<TransferWithRent>) -> Result<()> {
        // VULNERABLE: Using hardcoded rent values
        const RENT_EXEMPT_LAMPORTS: u64 = 2_000_000; // Wrong! Rent can change
        
        let account_info = ctx.accounts.account.to_account_info();
        let current_lamports = account_info.lamports();
        
        // Using hardcoded rent threshold
        if current_lamports > RENT_EXEMPT_LAMPORTS {
            let withdrawable = current_lamports - RENT_EXEMPT_LAMPORTS;
            **account_info.try_borrow_mut_lamports()? -= withdrawable;
            **ctx.accounts.recipient.try_borrow_mut_lamports()? += withdrawable;
        }
        
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CreateAccount<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,
    #[account(mut)]
    /// CHECK: New account to be created
    pub new_account: AccountInfo<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct WithdrawLamports<'info> {
    #[account(mut)]
    pub account: Account<'info, UserAccount>,
    #[account(mut)]
    /// CHECK: Recipient account
    pub recipient: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct CloseAccount<'info> {
    #[account(mut)]
    pub account: Account<'info, UserAccount>,
    #[account(mut)]
    /// CHECK: Destination for lamports
    pub destination: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct ResizeAccount<'info> {
    #[account(mut)]
    pub account: Account<'info, UserAccount>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct TransferWithRent<'info> {
    #[account(mut)]
    pub account: Account<'info, UserAccount>,
    #[account(mut)]
    /// CHECK: Recipient account
    pub recipient: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[account]
pub struct UserAccount {
    pub owner: Pubkey,
    pub balance: u64,
    pub data: [u8; 32],
}