use anchor_lang::prelude::*;
use anchor_lang::solana_program::{system_instruction, program::invoke};

declare_id!("11111111111111111111111111111111");

#[program]
pub mod rent_exemption_secure {
    use super::*;

    pub fn create_account(ctx: Context<CreateAccount>) -> Result<()> {
        // SECURE: Calculate proper rent exemption
        let account_size = 8 + 32 + 64; // discriminator + pubkey + data
        
        let rent = Rent::get()?;
        let rent_exempt_lamports = rent.minimum_balance(account_size);
        
        // SECURE: Validate minimum rent exemption
        require!(
            ctx.accounts.payer.lamports() >= rent_exempt_lamports,
            ErrorCode::InsufficientFunds
        );
        
        msg!("Creating rent-exempt account with {} lamports", rent_exempt_lamports);
        
        // For demonstration - actual account creation handled by Anchor
        Ok(())
    }

    pub fn withdraw_lamports(ctx: Context<WithdrawLamports>, amount: u64) -> Result<()> {
        // SECURE: Ensure remaining balance is rent exempt
        let account_info = ctx.accounts.account.to_account_info();
        let current_lamports = account_info.lamports();
        
        let rent = Rent::get()?;
        let min_balance = rent.minimum_balance(account_info.data_len());
        
        require!(
            current_lamports.checked_sub(amount).unwrap_or(0) >= min_balance,
            ErrorCode::InsufficientRentExemption
        );
        
        **account_info.try_borrow_mut_lamports()? -= amount;
        **ctx.accounts.recipient.try_borrow_mut_lamports()? += amount;
        
        Ok(())
    }

    pub fn close_account(ctx: Context<CloseAccount>) -> Result<()> {
        // SECURE: Proper account closure with validation
        let account = &mut ctx.accounts.account;
        let destination = &mut ctx.accounts.destination;
        
        // Validate account can be closed
        require!(
            account.owner == ctx.accounts.authority.key(),
            ErrorCode::InvalidAccountOwner
        );
        
        // Transfer all lamports and mark account for closure
        let lamports = account.to_account_info().lamports();
        **account.to_account_info().try_borrow_mut_lamports()? = 0;
        **destination.to_account_info().try_borrow_mut_lamports()? += lamports;
        
        // Zero out account data to prevent reuse
        account.to_account_info().realloc(0, false)?;
        
        Ok(())
    }

    pub fn resize_account(ctx: Context<ResizeAccount>, new_size: usize) -> Result<()> {
        // SECURE: Calculate new rent requirement and ensure sufficient lamports
        let rent = Rent::get()?;
        let current_lamports = ctx.accounts.account.to_account_info().lamports();
        let new_rent_requirement = rent.minimum_balance(new_size);
        
        require!(
            current_lamports >= new_rent_requirement,
            ErrorCode::InsufficientLamportsForResize
        );
        
        ctx.accounts.account.to_account_info().realloc(new_size, false)?;
        
        Ok(())
    }

    pub fn transfer_with_dynamic_rent(ctx: Context<TransferWithRent>) -> Result<()> {
        // SECURE: Use dynamic rent calculation
        let account_info = ctx.accounts.account.to_account_info();
        let current_lamports = account_info.lamports();
        
        // Calculate current rent exemption requirement
        let rent = Rent::get()?;
        let min_balance = rent.minimum_balance(account_info.data_len());
        
        require!(
            current_lamports > min_balance,
            ErrorCode::InsufficientRentExemption
        );
        
        let withdrawable = current_lamports
            .checked_sub(min_balance)
            .ok_or(ErrorCode::ArithmeticUnderflow)?;
        
        if withdrawable > 0 {
            **account_info.try_borrow_mut_lamports()? -= withdrawable;
            **ctx.accounts.recipient.try_borrow_mut_lamports()? += withdrawable;
        }
        
        Ok(())
    }

    pub fn fund_account_for_rent(ctx: Context<FundAccount>, additional_size: usize) -> Result<()> {
        // SECURE: Add lamports when account needs more rent
        let rent = Rent::get()?;
        let current_size = ctx.accounts.account.to_account_info().data_len();
        let new_size = current_size + additional_size;
        
        let current_rent = rent.minimum_balance(current_size);
        let required_rent = rent.minimum_balance(new_size);
        let additional_rent = required_rent.saturating_sub(current_rent);
        
        if additional_rent > 0 {
            // Transfer additional rent from payer
            **ctx.accounts.payer.to_account_info().try_borrow_mut_lamports()? -= additional_rent;
            **ctx.accounts.account.to_account_info().try_borrow_mut_lamports()? += additional_rent;
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
    #[account(mut, constraint = authority.key() == account.owner @ ErrorCode::InvalidAccountOwner)]
    pub account: Account<'info, UserAccount>,
    #[account(mut)]
    /// CHECK: Recipient account
    pub recipient: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct CloseAccount<'info> {
    #[account(mut, constraint = authority.key() == account.owner @ ErrorCode::InvalidAccountOwner, close = destination)]
    pub account: Account<'info, UserAccount>,
    #[account(mut)]
    /// CHECK: Destination for lamports
    pub destination: AccountInfo<'info>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct ResizeAccount<'info> {
    #[account(mut, constraint = authority.key() == account.owner @ ErrorCode::InvalidAccountOwner)]
    pub account: Account<'info, UserAccount>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct TransferWithRent<'info> {
    #[account(mut, constraint = authority.key() == account.owner @ ErrorCode::InvalidAccountOwner)]
    pub account: Account<'info, UserAccount>,
    #[account(mut)]
    /// CHECK: Recipient account
    pub recipient: AccountInfo<'info>,
    #[account(constraint = authority.key() == account.owner)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct FundAccount<'info> {
    #[account(mut)]
    pub account: Account<'info, UserAccount>,
    #[account(mut)]
    pub payer: Signer<'info>,
}

#[account]
pub struct UserAccount {
    pub owner: Pubkey,
    pub balance: u64,
    pub data: [u8; 32],
}

#[error_code]
pub enum ErrorCode {
    #[msg("Insufficient lamports for rent exemption")]
    InsufficientRentExemption,
    #[msg("Invalid account owner")]
    InvalidAccountOwner,
    #[msg("Insufficient lamports for account resize")]
    InsufficientLamportsForResize,
    #[msg("Arithmetic underflow")]
    ArithmeticUnderflow,
    #[msg("Insufficient funds")]
    InsufficientFunds,
}