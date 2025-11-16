use anchor_lang::prelude::*;

declare_id!("5xot9PVkphiX2adznghwrAuxGs2zeWisNSxMW6hU6Hkj");

#[program]
pub mod royalty_splitter {
    use super::*;

    /// Initialize the royalty configuration
    pub fn initialize_config(
        ctx: Context<InitializeConfig>,
        creator_share: u8,
        platform_share: u8,
        treasury_share: u8,
        platform_wallet: Pubkey,
        treasury_wallet: Pubkey,
    ) -> Result<()> {
        require!(
            creator_share + platform_share + treasury_share == 100,
            RoyaltyError::InvalidShareTotal
        );

        let config = &mut ctx.accounts.royalty_config;
        config.creator_share = creator_share;
        config.platform_share = platform_share;
        config.treasury_share = treasury_share;
        config.platform_wallet = platform_wallet;
        config.treasury_wallet = treasury_wallet;
        config.admin = ctx.accounts.admin.key();
        config.total_distributed = 0;
        config.total_transactions = 0;

        let clock = Clock::get()?;
        config.created_at = clock.unix_timestamp;
        config.updated_at = clock.unix_timestamp;

        emit!(RoyaltyConfigInitialized {
            creator_share,
            platform_share,
            treasury_share,
            platform_wallet,
            treasury_wallet,
        });

        Ok(())
    }

    /// Distribute payment according to royalty configuration
    pub fn distribute_payment(
        ctx: Context<DistributePayment>,
        amount: u64,
        creator: Pubkey,
    ) -> Result<()> {
        require!(amount > 0, RoyaltyError::InvalidAmount);

        let config = &mut ctx.accounts.royalty_config;
        
        // Calculate distribution amounts
        let creator_amount = (amount * config.creator_share as u64) / 100;
        let platform_amount = (amount * config.platform_share as u64) / 100;
        let treasury_amount = amount - creator_amount - platform_amount; // Remaining to avoid rounding issues

        // Verify we have enough funds in the source account
        require!(
            ctx.accounts.source_account.lamports() >= amount,
            RoyaltyError::InsufficientFunds
        );

        // Transfer to creator
        **ctx.accounts.source_account.try_borrow_mut_lamports()? -= creator_amount;
        **ctx.accounts.creator_account.try_borrow_mut_lamports()? += creator_amount;

        // Transfer to platform
        **ctx.accounts.source_account.try_borrow_mut_lamports()? -= platform_amount;
        **ctx.accounts.platform_account.try_borrow_mut_lamports()? += platform_amount;

        // Transfer to treasury
        **ctx.accounts.source_account.try_borrow_mut_lamports()? -= treasury_amount;
        **ctx.accounts.treasury_account.try_borrow_mut_lamports()? += treasury_amount;

        // Update statistics
        config.total_distributed += amount;
        config.total_transactions += 1;

        let clock = Clock::get()?;
        config.updated_at = clock.unix_timestamp;

        // Record the distribution
    let distribution_id = ctx.accounts.distribution_record.key();
    let distribution = &mut ctx.accounts.distribution_record;
    distribution.distribution_id = distribution_id;
        distribution.creator = creator;
        distribution.total_amount = amount;
        distribution.creator_amount = creator_amount;
        distribution.platform_amount = platform_amount;
        distribution.treasury_amount = treasury_amount;
        distribution.timestamp = clock.unix_timestamp;

        emit!(PaymentDistributed {
            distribution_id,
            creator,
            total_amount: amount,
            creator_amount,
            platform_amount,
            treasury_amount,
        });

        Ok(())
    }

    /// Update royalty configuration (admin only)
    pub fn update_config(
        ctx: Context<UpdateConfig>,
        creator_share: Option<u8>,
        platform_share: Option<u8>,
        treasury_share: Option<u8>,
        platform_wallet: Option<Pubkey>,
        treasury_wallet: Option<Pubkey>,
    ) -> Result<()> {
        let config = &mut ctx.accounts.royalty_config;

        // Update shares if provided
        if let Some(new_creator_share) = creator_share {
            config.creator_share = new_creator_share;
        }
        if let Some(new_platform_share) = platform_share {
            config.platform_share = new_platform_share;
        }
        if let Some(new_treasury_share) = treasury_share {
            config.treasury_share = new_treasury_share;
        }

        // Verify total still equals 100%
        require!(
            config.creator_share + config.platform_share + config.treasury_share == 100,
            RoyaltyError::InvalidShareTotal
        );

        // Update wallet addresses if provided
        if let Some(new_platform_wallet) = platform_wallet {
            config.platform_wallet = new_platform_wallet;
        }
        if let Some(new_treasury_wallet) = treasury_wallet {
            config.treasury_wallet = new_treasury_wallet;
        }

        let clock = Clock::get()?;
        config.updated_at = clock.unix_timestamp;

        emit!(RoyaltyConfigUpdated {
            creator_share: config.creator_share,
            platform_share: config.platform_share,
            treasury_share: config.treasury_share,
            platform_wallet: config.platform_wallet,
            treasury_wallet: config.treasury_wallet,
        });

        Ok(())
    }

    /// Withdraw accumulated platform fees
    pub fn withdraw_platform_fees(
        ctx: Context<WithdrawPlatformFees>,
        amount: u64,
    ) -> Result<()> {
        require!(amount > 0, RoyaltyError::InvalidAmount);
        require!(
            ctx.accounts.platform_vault.lamports() >= amount,
            RoyaltyError::InsufficientFunds
        );

        // Transfer from platform vault to destination
        **ctx.accounts.platform_vault.try_borrow_mut_lamports()? -= amount;
        **ctx.accounts.destination.try_borrow_mut_lamports()? += amount;

        emit!(PlatformFeesWithdrawn {
            amount,
            destination: ctx.accounts.destination.key(),
            withdrawn_by: ctx.accounts.admin.key(),
        });

        Ok(())
    }

    /// Get distribution statistics
    pub fn get_stats(
        ctx: Context<GetStats>,
    ) -> Result<RoyaltyStats> {
        let config = &ctx.accounts.royalty_config;
        
        Ok(RoyaltyStats {
            total_distributed: config.total_distributed,
            total_transactions: config.total_transactions,
            creator_share: config.creator_share,
            platform_share: config.platform_share,
            treasury_share: config.treasury_share,
        })
    }

    /// Emergency pause (admin only)
    pub fn set_pause_state(
        ctx: Context<SetPauseState>,
        is_paused: bool,
    ) -> Result<()> {
        let config = &mut ctx.accounts.royalty_config;
        config.is_paused = is_paused;

        let clock = Clock::get()?;
        config.updated_at = clock.unix_timestamp;

        emit!(PauseStateChanged {
            is_paused,
            changed_by: ctx.accounts.admin.key(),
        });

        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeConfig<'info> {
    #[account(
        init,
        payer = admin,
        space = 8 + RoyaltyConfig::INIT_SPACE,
        seeds = [b"royalty_config"],
        bump
    )]
    pub royalty_config: Account<'info, RoyaltyConfig>,

    #[account(mut)]
    pub admin: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct DistributePayment<'info> {
    #[account(
        mut,
        seeds = [b"royalty_config"],
        bump,
        constraint = !royalty_config.is_paused @ RoyaltyError::ContractPaused
    )]
    pub royalty_config: Account<'info, RoyaltyConfig>,

    #[account(
        init,
        payer = payer,
        space = 8 + DistributionRecord::INIT_SPACE,
        seeds = [b"distribution", royalty_config.total_transactions.to_le_bytes().as_ref()],
        bump
    )]
    pub distribution_record: Account<'info, DistributionRecord>,

    /// CHECK: Source account holding the funds to distribute
    #[account(mut)]
    pub source_account: UncheckedAccount<'info>,

    /// CHECK: Creator's account to receive their share
    #[account(mut)]
    pub creator_account: UncheckedAccount<'info>,

    /// CHECK: Platform account to receive platform share
    #[account(
        mut,
        constraint = platform_account.key() == royalty_config.platform_wallet @ RoyaltyError::InvalidPlatformWallet
    )]
    pub platform_account: UncheckedAccount<'info>,

    /// CHECK: Treasury account to receive treasury share
    #[account(
        mut,
        constraint = treasury_account.key() == royalty_config.treasury_wallet @ RoyaltyError::InvalidTreasuryWallet
    )]
    pub treasury_account: UncheckedAccount<'info>,

    #[account(mut)]
    pub payer: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateConfig<'info> {
    #[account(
        mut,
        seeds = [b"royalty_config"],
        bump,
        has_one = admin @ RoyaltyError::UnauthorizedAdmin
    )]
    pub royalty_config: Account<'info, RoyaltyConfig>,

    pub admin: Signer<'info>,
}

#[derive(Accounts)]
pub struct WithdrawPlatformFees<'info> {
    #[account(
        seeds = [b"royalty_config"],
        bump,
        has_one = admin @ RoyaltyError::UnauthorizedAdmin
    )]
    pub royalty_config: Account<'info, RoyaltyConfig>,

    /// CHECK: Platform vault holding accumulated fees
    #[account(mut)]
    pub platform_vault: UncheckedAccount<'info>,

    /// CHECK: Destination account for withdrawn fees
    #[account(mut)]
    pub destination: UncheckedAccount<'info>,

    pub admin: Signer<'info>,
}

#[derive(Accounts)]
pub struct GetStats<'info> {
    #[account(
        seeds = [b"royalty_config"],
        bump
    )]
    pub royalty_config: Account<'info, RoyaltyConfig>,
}

#[derive(Accounts)]
pub struct SetPauseState<'info> {
    #[account(
        mut,
        seeds = [b"royalty_config"],
        bump,
        has_one = admin @ RoyaltyError::UnauthorizedAdmin
    )]
    pub royalty_config: Account<'info, RoyaltyConfig>,

    pub admin: Signer<'info>,
}

#[account]
pub struct RoyaltyConfig {
    pub creator_share: u8,          // 1 byte (percentage)
    pub platform_share: u8,         // 1 byte (percentage)
    pub treasury_share: u8,         // 1 byte (percentage)
    pub platform_wallet: Pubkey,    // 32 bytes
    pub treasury_wallet: Pubkey,    // 32 bytes
    pub admin: Pubkey,              // 32 bytes
    pub total_distributed: u64,     // 8 bytes
    pub total_transactions: u64,    // 8 bytes
    pub created_at: i64,            // 8 bytes
    pub updated_at: i64,            // 8 bytes
    pub is_paused: bool,            // 1 byte
}

impl RoyaltyConfig {
    pub const INIT_SPACE: usize = 1 + 1 + 1 + 32 + 32 + 32 + 8 + 8 + 8 + 8 + 1;
}

#[account]
pub struct DistributionRecord {
    pub distribution_id: Pubkey,    // 32 bytes
    pub creator: Pubkey,            // 32 bytes
    pub total_amount: u64,          // 8 bytes
    pub creator_amount: u64,        // 8 bytes
    pub platform_amount: u64,      // 8 bytes
    pub treasury_amount: u64,      // 8 bytes
    pub timestamp: i64,             // 8 bytes
}

impl DistributionRecord {
    pub const INIT_SPACE: usize = 32 + 32 + 8 + 8 + 8 + 8 + 8;
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct RoyaltyStats {
    pub total_distributed: u64,
    pub total_transactions: u64,
    pub creator_share: u8,
    pub platform_share: u8,
    pub treasury_share: u8,
}

#[event]
pub struct RoyaltyConfigInitialized {
    pub creator_share: u8,
    pub platform_share: u8,
    pub treasury_share: u8,
    pub platform_wallet: Pubkey,
    pub treasury_wallet: Pubkey,
}

#[event]
pub struct PaymentDistributed {
    pub distribution_id: Pubkey,
    pub creator: Pubkey,
    pub total_amount: u64,
    pub creator_amount: u64,
    pub platform_amount: u64,
    pub treasury_amount: u64,
}

#[event]
pub struct RoyaltyConfigUpdated {
    pub creator_share: u8,
    pub platform_share: u8,
    pub treasury_share: u8,
    pub platform_wallet: Pubkey,
    pub treasury_wallet: Pubkey,
}

#[event]
pub struct PlatformFeesWithdrawn {
    pub amount: u64,
    pub destination: Pubkey,
    pub withdrawn_by: Pubkey,
}

#[event]
pub struct PauseStateChanged {
    pub is_paused: bool,
    pub changed_by: Pubkey,
}

#[error_code]
pub enum RoyaltyError {
    #[msg("Share percentages must total 100")]
    InvalidShareTotal,
    #[msg("Invalid payment amount")]
    InvalidAmount,
    #[msg("Insufficient funds for distribution")]
    InsufficientFunds,
    #[msg("Unauthorized admin access")]
    UnauthorizedAdmin,
    #[msg("Invalid platform wallet address")]
    InvalidPlatformWallet,
    #[msg("Invalid treasury wallet address")]
    InvalidTreasuryWallet,
    #[msg("Contract is currently paused")]
    ContractPaused,
}