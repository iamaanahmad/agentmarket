use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount};
use mpl_token_metadata::instructions::{
    CreateMetadataAccountV3Cpi, CreateMetadataAccountV3CpiAccounts, CreateMetadataAccountV3InstructionArgs,
};
use mpl_token_metadata::types::{Creator, DataV2};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod agent_registry {
    use super::*;

    pub fn register_agent(
        ctx: Context<RegisterAgent>,
        name: String,
        description: String,
        capabilities: Vec<String>,
        pricing: PricingModel,
        endpoint_url: String,
        ipfs_hash: String,
        symbol: String,
        uri: String,
    ) -> Result<()> {
        require!(name.len() <= 50, ErrorCode::NameTooLong);
        require!(description.len() <= 500, ErrorCode::DescriptionTooLong);
        require!(endpoint_url.len() <= 200, ErrorCode::EndpointTooLong);
        require!(capabilities.len() <= 10, ErrorCode::TooManyCapabilities);

    let profile_key = ctx.accounts.agent_profile.key();
    let creator_key = ctx.accounts.creator.key();
    let agent_profile = &mut ctx.accounts.agent_profile;
        let clock = Clock::get()?;

        // Initialize agent profile
    agent_profile.agent_id = profile_key;
    agent_profile.creator = creator_key;
        agent_profile.name = name.clone();
        agent_profile.description = description.clone();
        agent_profile.capabilities = capabilities;
        agent_profile.pricing_model = pricing;
        agent_profile.endpoint_url = endpoint_url;
        agent_profile.ipfs_hash = ipfs_hash;
        agent_profile.reputation_score = 0;
        agent_profile.total_services = 0;
        agent_profile.total_earnings = 0;
        agent_profile.created_at = clock.unix_timestamp;
        agent_profile.is_active = true;
    agent_profile.nft_mint = ctx.accounts.mint.key();

        // Create NFT metadata
        let creator = Creator {
            address: creator_key,
            verified: true,
            share: 100,
        };

        let metadata_args = DataV2 {
            name: format!("AgentMarket: {}", name),
            symbol,
            uri,
            seller_fee_basis_points: 500, // 5% royalty
            creators: Some(vec![creator]),
            collection: None,
            uses: None,
        };
        let metadata_info = ctx.accounts.metadata.to_account_info();
        let mint_info = ctx.accounts.mint.to_account_info();
        let creator_info = ctx.accounts.creator.to_account_info();
        let system_program_info = ctx.accounts.system_program.to_account_info();
        let rent_info = ctx.accounts.rent.to_account_info();
        let metadata_cpi_accounts = CreateMetadataAccountV3CpiAccounts {
            metadata: &metadata_info,
            mint: &mint_info,
            mint_authority: &creator_info,
            payer: &creator_info,
            update_authority: (&creator_info, true),
            system_program: &system_program_info,
            rent: Some(&rent_info),
        };
        let metadata_cpi_args = CreateMetadataAccountV3InstructionArgs {
            data: metadata_args,
            is_mutable: true,
            collection_details: None,
        };
        CreateMetadataAccountV3Cpi::new(
            &ctx.accounts.token_metadata_program.to_account_info(),
            metadata_cpi_accounts,
            metadata_cpi_args,
        )
        .invoke()?;

        // Mint NFT to creator
        let cpi_accounts = token::MintTo {
            mint: ctx.accounts.mint.to_account_info(),
            to: ctx.accounts.token_account.to_account_info(),
            authority: ctx.accounts.creator.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        token::mint_to(cpi_ctx, 1)?;

        emit!(AgentRegistered {
            agent_id: agent_profile.agent_id,
            creator: agent_profile.creator,
            name: agent_profile.name.clone(),
            nft_mint: agent_profile.nft_mint,
            timestamp: clock.unix_timestamp,
        });

        Ok(())
    }

    pub fn update_agent(
        ctx: Context<UpdateAgent>,
        name: Option<String>,
        description: Option<String>,
        pricing: Option<PricingModel>,
        endpoint_url: Option<String>,
        is_active: Option<bool>,
    ) -> Result<()> {
        let agent_profile = &mut ctx.accounts.agent_profile;

        if let Some(name) = name {
            require!(name.len() <= 50, ErrorCode::NameTooLong);
            agent_profile.name = name;
        }
        if let Some(description) = description {
            require!(description.len() <= 500, ErrorCode::DescriptionTooLong);
            agent_profile.description = description;
        }
        if let Some(pricing) = pricing {
            agent_profile.pricing_model = pricing;
        }
        if let Some(endpoint_url) = endpoint_url {
            require!(endpoint_url.len() <= 200, ErrorCode::EndpointTooLong);
            agent_profile.endpoint_url = endpoint_url;
        }
        if let Some(is_active) = is_active {
            agent_profile.is_active = is_active;
        }

        emit!(AgentUpdated {
            agent_id: agent_profile.agent_id,
            creator: agent_profile.creator,
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(())
    }

    pub fn update_reputation(
        ctx: Context<UpdateReputation>,
        new_rating: u32,
        service_count: u64,
    ) -> Result<()> {
        let agent_profile = &mut ctx.accounts.agent_profile;
        
        agent_profile.reputation_score = new_rating;
        agent_profile.total_services = service_count;

        Ok(())
    }
}

#[derive(Accounts)]
pub struct RegisterAgent<'info> {
    #[account(
        init,
        payer = creator,
        space = 8 + AgentProfile::INIT_SPACE,
        seeds = [b"agent", creator.key().as_ref()],
        bump
    )]
    pub agent_profile: Account<'info, AgentProfile>,

    #[account(
        init,
        payer = creator,
        mint::decimals = 0,
        mint::authority = creator,
    )]
    pub mint: Account<'info, Mint>,

    #[account(
        init,
        payer = creator,
        associated_token::mint = mint,
        associated_token::authority = creator,
    )]
    pub token_account: Account<'info, TokenAccount>,

    /// CHECK: This is not dangerous because we don't read or write from this account
    #[account(mut)]
    pub metadata: UncheckedAccount<'info>,

    #[account(mut)]
    pub creator: Signer<'info>,

    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, anchor_spl::associated_token::AssociatedToken>,
    /// CHECK: This is not dangerous because we don't read or write from this account
    pub token_metadata_program: UncheckedAccount<'info>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct UpdateAgent<'info> {
    #[account(
        mut,
        seeds = [b"agent", creator.key().as_ref()],
        bump,
        has_one = creator
    )]
    pub agent_profile: Account<'info, AgentProfile>,

    pub creator: Signer<'info>,
}

#[derive(Accounts)]
pub struct UpdateReputation<'info> {
    #[account(mut)]
    pub agent_profile: Account<'info, AgentProfile>,
}

#[account]
#[derive(InitSpace)]
pub struct AgentProfile {
    pub agent_id: Pubkey,
    pub creator: Pubkey,
    #[max_len(50)]
    pub name: String,
    #[max_len(500)]
    pub description: String,
    #[max_len(10, 20)]
    pub capabilities: Vec<String>,
    pub pricing_model: PricingModel,
    #[max_len(200)]
    pub endpoint_url: String,
    #[max_len(100)]
    pub ipfs_hash: String,
    pub reputation_score: u32,
    pub total_services: u64,
    pub total_earnings: u64,
    pub created_at: i64,
    pub is_active: bool,
    pub nft_mint: Pubkey,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, InitSpace)]
pub enum PricingModel {
    PerQuery { price: u64 },
    Subscription { monthly: u64 },
    Custom { base: u64, variable: u8 },
}

#[event]
pub struct AgentRegistered {
    pub agent_id: Pubkey,
    pub creator: Pubkey,
    pub name: String,
    pub nft_mint: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct AgentUpdated {
    pub agent_id: Pubkey,
    pub creator: Pubkey,
    pub timestamp: i64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Agent name is too long (max 50 characters)")]
    NameTooLong,
    #[msg("Agent description is too long (max 500 characters)")]
    DescriptionTooLong,
    #[msg("Endpoint URL is too long (max 200 characters)")]
    EndpointTooLong,
    #[msg("Too many capabilities (max 10)")]
    TooManyCapabilities,
}