use anchor_lang::prelude::*;

declare_id!("8L8pDf3jutdpdr4m3np68CL9ZroLActrqwxi6s9Sk5ML");

#[program]
pub mod reputation_system {
    use super::*;

    /// Submit a rating for a completed service
    pub fn submit_rating(
        ctx: Context<SubmitRating>,
        request_id: Pubkey,
        stars: u8,
        quality: u8,
        speed: u8,
        value: u8,
        review_text: String,
    ) -> Result<()> {
        require!(stars >= 1 && stars <= 5, ReputationError::InvalidRating);
        require!(quality >= 1 && quality <= 5, ReputationError::InvalidRating);
        require!(speed >= 1 && speed <= 5, ReputationError::InvalidRating);
        require!(value >= 1 && value <= 5, ReputationError::InvalidRating);
        require!(review_text.len() <= 1000, ReputationError::ReviewTooLong);

    let rating_id = ctx.accounts.rating.key();
    let agent_id = ctx.accounts.agent_profile.key();
    let user_key = ctx.accounts.user.key();
    let rating = &mut ctx.accounts.rating;
    let clock = Clock::get()?;

    // Initialize rating
    rating.rating_id = rating_id;
    rating.agent_id = agent_id;
    rating.user = user_key;
        rating.request_id = request_id;
        rating.stars = stars;
        rating.quality = quality;
        rating.speed = speed;
        rating.value = value;
        rating.review_text = review_text.clone();
        rating.created_at = clock.unix_timestamp;

        // Update agent's aggregate rating
        let agent_profile = &mut ctx.accounts.agent_profile;
        let total_ratings = agent_profile.total_ratings + 1;
        
        // Calculate new weighted average
        let current_total_score = (agent_profile.average_rating as u64) * agent_profile.total_ratings;
        let new_total_score = current_total_score + (stars as u64);
        let new_average = (new_total_score / total_ratings) as u32;

        agent_profile.total_ratings = total_ratings;
        agent_profile.average_rating = new_average;
        agent_profile.last_rating_at = clock.unix_timestamp;

        // Update detailed ratings
        agent_profile.quality_score = calculate_weighted_average(
            agent_profile.quality_score,
            agent_profile.total_ratings - 1,
            quality as u32,
        );
        agent_profile.speed_score = calculate_weighted_average(
            agent_profile.speed_score,
            agent_profile.total_ratings - 1,
            speed as u32,
        );
        agent_profile.value_score = calculate_weighted_average(
            agent_profile.value_score,
            agent_profile.total_ratings - 1,
            value as u32,
        );

        emit!(RatingSubmitted {
            rating_id,
            agent_id,
            user: user_key,
            stars: rating.stars,
            new_average: agent_profile.average_rating,
        });

        Ok(())
    }

    /// Initialize agent reputation profile
    pub fn initialize_agent_reputation(
        ctx: Context<InitializeAgentReputation>,
        agent_id: Pubkey,
    ) -> Result<()> {
        let agent_profile = &mut ctx.accounts.agent_profile;
        let clock = Clock::get()?;

        agent_profile.agent_id = agent_id;
        agent_profile.total_ratings = 0;
        agent_profile.average_rating = 0;
        agent_profile.quality_score = 0;
        agent_profile.speed_score = 0;
        agent_profile.value_score = 0;
        agent_profile.created_at = clock.unix_timestamp;
        agent_profile.last_rating_at = 0;

        emit!(AgentReputationInitialized {
            agent_id: agent_profile.agent_id,
        });

        Ok(())
    }

    /// Get agent's rating statistics (view function)
    pub fn get_agent_stats(
        ctx: Context<GetAgentStats>,
    ) -> Result<AgentStats> {
        let agent_profile = &ctx.accounts.agent_profile;
        
        Ok(AgentStats {
            agent_id: agent_profile.agent_id,
            total_ratings: agent_profile.total_ratings,
            average_rating: agent_profile.average_rating,
            quality_score: agent_profile.quality_score,
            speed_score: agent_profile.speed_score,
            value_score: agent_profile.value_score,
        })
    }

    /// Report inappropriate review (moderation)
    pub fn report_rating(
        ctx: Context<ReportRating>,
        reason: String,
    ) -> Result<()> {
        require!(reason.len() <= 500, ReputationError::ReasonTooLong);

        let rating = &mut ctx.accounts.rating;
        rating.is_reported = true;
        rating.report_reason = Some(reason.clone());

        emit!(RatingReported {
            rating_id: rating.rating_id,
            reporter: ctx.accounts.reporter.key(),
            reason,
        });

        Ok(())
    }

    /// Admin function to moderate ratings
    pub fn moderate_rating(
        ctx: Context<ModerateRating>,
        is_valid: bool,
        admin_note: String,
    ) -> Result<()> {
        require!(admin_note.len() <= 500, ReputationError::NoteTooLong);

        let rating = &mut ctx.accounts.rating;
        rating.is_moderated = true;
        rating.is_valid = is_valid;
        rating.admin_note = Some(admin_note);

        // If rating is deemed invalid, adjust agent's reputation
        if !is_valid {
            let agent_profile = &mut ctx.accounts.agent_profile;
            
            // Recalculate average without this rating
            if agent_profile.total_ratings > 1 {
                let current_total = (agent_profile.average_rating as u64) * agent_profile.total_ratings;
                let adjusted_total = current_total - (rating.stars as u64);
                agent_profile.total_ratings -= 1;
                agent_profile.average_rating = (adjusted_total / agent_profile.total_ratings) as u32;
            } else {
                agent_profile.total_ratings = 0;
                agent_profile.average_rating = 0;
            }
        }

        emit!(RatingModerated {
            rating_id: rating.rating_id,
            is_valid,
            moderator: ctx.accounts.admin.key(),
        });

        Ok(())
    }
}

// Helper function to calculate weighted average
fn calculate_weighted_average(current_avg: u32, current_count: u64, new_value: u32) -> u32 {
    if current_count == 0 {
        return new_value;
    }
    
    let total_score = (current_avg as u64) * current_count + (new_value as u64);
    (total_score / (current_count + 1)) as u32
}

#[derive(Accounts)]
#[instruction(request_id: Pubkey)]
pub struct SubmitRating<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + Rating::INIT_SPACE,
        seeds = [b"rating", user.key().as_ref(), request_id.as_ref()],
        bump
    )]
    pub rating: Account<'info, Rating>,

    #[account(
        mut,
        seeds = [b"agent_reputation", agent_profile.agent_id.as_ref()],
        bump
    )]
    pub agent_profile: Account<'info, AgentReputationProfile>,

    #[account(mut)]
    pub user: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(agent_id: Pubkey)]
pub struct InitializeAgentReputation<'info> {
    #[account(
        init,
        payer = creator,
        space = 8 + AgentReputationProfile::INIT_SPACE,
        seeds = [b"agent_reputation", agent_id.as_ref()],
        bump
    )]
    pub agent_profile: Account<'info, AgentReputationProfile>,

    #[account(mut)]
    pub creator: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct GetAgentStats<'info> {
    #[account(
        seeds = [b"agent_reputation", agent_profile.agent_id.as_ref()],
        bump
    )]
    pub agent_profile: Account<'info, AgentReputationProfile>,
}

#[derive(Accounts)]
pub struct ReportRating<'info> {
    #[account(
        mut,
        seeds = [b"rating", rating.user.as_ref(), rating.request_id.as_ref()],
        bump
    )]
    pub rating: Account<'info, Rating>,

    pub reporter: Signer<'info>,
}

#[derive(Accounts)]
pub struct ModerateRating<'info> {
    #[account(
        mut,
        seeds = [b"rating", rating.user.as_ref(), rating.request_id.as_ref()],
        bump
    )]
    pub rating: Account<'info, Rating>,

    #[account(
        mut,
        seeds = [b"agent_reputation", agent_profile.agent_id.as_ref()],
        bump
    )]
    pub agent_profile: Account<'info, AgentReputationProfile>,

    /// CHECK: Admin authority - would be verified off-chain
    pub admin: Signer<'info>,
}

#[account]
pub struct Rating {
    pub rating_id: Pubkey,          // 32 bytes
    pub agent_id: Pubkey,           // 32 bytes
    pub user: Pubkey,               // 32 bytes
    pub request_id: Pubkey,         // 32 bytes
    pub stars: u8,                  // 1 byte (1-5)
    pub quality: u8,                // 1 byte (1-5)
    pub speed: u8,                  // 1 byte (1-5)
    pub value: u8,                  // 1 byte (1-5)
    pub review_text: String,        // 4 + 1000 bytes
    pub created_at: i64,            // 8 bytes
    pub is_reported: bool,          // 1 byte
    pub report_reason: Option<String>, // 1 + 4 + 500 bytes
    pub is_moderated: bool,         // 1 byte
    pub is_valid: bool,             // 1 byte
    pub admin_note: Option<String>, // 1 + 4 + 500 bytes
}

impl Rating {
    pub const INIT_SPACE: usize = 32 + 32 + 32 + 32 + 1 + 1 + 1 + 1 + 1004 + 8 + 1 + 505 + 1 + 1 + 505;
}

#[account]
pub struct AgentReputationProfile {
    pub agent_id: Pubkey,           // 32 bytes
    pub total_ratings: u64,         // 8 bytes
    pub average_rating: u32,        // 4 bytes (stars * 100 for precision)
    pub quality_score: u32,         // 4 bytes
    pub speed_score: u32,           // 4 bytes
    pub value_score: u32,           // 4 bytes
    pub created_at: i64,            // 8 bytes
    pub last_rating_at: i64,        // 8 bytes
}

impl AgentReputationProfile {
    pub const INIT_SPACE: usize = 32 + 8 + 4 + 4 + 4 + 4 + 8 + 8;
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct AgentStats {
    pub agent_id: Pubkey,
    pub total_ratings: u64,
    pub average_rating: u32,
    pub quality_score: u32,
    pub speed_score: u32,
    pub value_score: u32,
}

#[event]
pub struct RatingSubmitted {
    pub rating_id: Pubkey,
    pub agent_id: Pubkey,
    pub user: Pubkey,
    pub stars: u8,
    pub new_average: u32,
}

#[event]
pub struct AgentReputationInitialized {
    pub agent_id: Pubkey,
}

#[event]
pub struct RatingReported {
    pub rating_id: Pubkey,
    pub reporter: Pubkey,
    pub reason: String,
}

#[event]
pub struct RatingModerated {
    pub rating_id: Pubkey,
    pub is_valid: bool,
    pub moderator: Pubkey,
}

#[error_code]
pub enum ReputationError {
    #[msg("Rating must be between 1 and 5")]
    InvalidRating,
    #[msg("Review text is too long (max 1000 characters)")]
    ReviewTooLong,
    #[msg("Report reason is too long (max 500 characters)")]
    ReasonTooLong,
    #[msg("Admin note is too long (max 500 characters)")]
    NoteTooLong,
}