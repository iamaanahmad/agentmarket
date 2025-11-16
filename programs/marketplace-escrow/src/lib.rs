use anchor_lang::prelude::*;

declare_id!("2ZuJbvYqvhXq7N7WjKw3r4YqkU3r7CmLGjXXvKhGz3xF");

#[program]
pub mod marketplace_escrow {
    use super::*;

    pub fn create_service_request(
        ctx: Context<CreateServiceRequest>,
        agent_id: Pubkey,
        amount: u64,
        request_data: String,
    ) -> Result<()> {
        require!(amount > 0, ErrorCode::InvalidAmount);
        require!(request_data.len() <= 1000, ErrorCode::RequestDataTooLong);

    let request_key = ctx.accounts.service_request.key();
    let user_key = ctx.accounts.user.key();
    let escrow_key = ctx.accounts.escrow_account.key();
    let service_request = &mut ctx.accounts.service_request;
    let clock = Clock::get()?;

    service_request.request_id = request_key;
    service_request.agent_id = agent_id;
    service_request.user = user_key;
        service_request.amount = amount;
        service_request.status = RequestStatus::Pending;
    service_request.request_data = request_data.clone();
        service_request.result_data = String::new();
        service_request.created_at = clock.unix_timestamp;
        service_request.completed_at = None;
    service_request.escrow_account = escrow_key;

        // Transfer payment to escrow PDA
        let transfer_instruction = anchor_lang::solana_program::system_instruction::transfer(
            &user_key,
            &escrow_key,
            amount,
        );

        anchor_lang::solana_program::program::invoke(
            &transfer_instruction,
            &[
                ctx.accounts.user.to_account_info(),
                ctx.accounts.escrow_account.to_account_info(),
            ],
        )?;

        emit!(ServiceRequestCreated {
            request_id: service_request.request_id,
            agent_id,
            user: user_key,
            amount,
            timestamp: clock.unix_timestamp,
        });

        Ok(())
    }

    pub fn submit_result(
        ctx: Context<SubmitResult>,
        result_data: String,
    ) -> Result<()> {
        require!(result_data.len() <= 2000, ErrorCode::ResultDataTooLong);

        let service_request = &mut ctx.accounts.service_request;
        let clock = Clock::get()?;

        require!(
            service_request.status == RequestStatus::Pending || 
            service_request.status == RequestStatus::InProgress,
            ErrorCode::InvalidRequestStatus
        );

        service_request.result_data = result_data;
        service_request.status = RequestStatus::Completed;
        service_request.completed_at = Some(clock.unix_timestamp);

        emit!(ResultSubmitted {
            request_id: service_request.request_id,
            agent_id: service_request.agent_id,
            timestamp: clock.unix_timestamp,
        });

        Ok(())
    }

    pub fn approve_result(
        ctx: Context<ApproveResult>,
    ) -> Result<()> {
        let service_request = &mut ctx.accounts.service_request;

        require!(
            service_request.status == RequestStatus::Completed,
            ErrorCode::InvalidRequestStatus
        );

        require!(
            service_request.user == ctx.accounts.user.key(),
            ErrorCode::UnauthorizedUser
        );

        service_request.status = RequestStatus::Approved;

        // Calculate payment splits (85% creator, 10% platform, 5% treasury)
        let total_amount = service_request.amount;
        let creator_amount = (total_amount * 85) / 100;
        let platform_amount = (total_amount * 10) / 100;
        let treasury_amount = total_amount - creator_amount - platform_amount;

        let escrow_account = &mut ctx.accounts.escrow_account;
        let creator = &mut ctx.accounts.creator;
        let platform_wallet = &mut ctx.accounts.platform_wallet;
        let treasury_wallet = &mut ctx.accounts.treasury_wallet;

        // Transfer to creator (85%)
        **escrow_account.try_borrow_mut_lamports()? -= creator_amount;
        **creator.try_borrow_mut_lamports()? += creator_amount;

        // Transfer to platform (10%)
        **escrow_account.try_borrow_mut_lamports()? -= platform_amount;
        **platform_wallet.try_borrow_mut_lamports()? += platform_amount;

        // Transfer to treasury (5%)
        **escrow_account.try_borrow_mut_lamports()? -= treasury_amount;
        **treasury_wallet.try_borrow_mut_lamports()? += treasury_amount;

        emit!(PaymentReleased {
            request_id: service_request.request_id,
            creator: creator.key(),
            creator_amount,
            platform_amount,
            treasury_amount,
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(())
    }

    pub fn dispute_result(
        ctx: Context<DisputeResult>,
        reason: String,
    ) -> Result<()> {
        require!(reason.len() <= 500, ErrorCode::DisputeReasonTooLong);

        let service_request = &mut ctx.accounts.service_request;

        require!(
            service_request.status == RequestStatus::Completed,
            ErrorCode::InvalidRequestStatus
        );

        require!(
            service_request.user == ctx.accounts.user.key(),
            ErrorCode::UnauthorizedUser
        );

        service_request.status = RequestStatus::Disputed;

        emit!(ResultDisputed {
            request_id: service_request.request_id,
            user: ctx.accounts.user.key(),
            reason,
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(())
    }

    pub fn cancel_request(
        ctx: Context<CancelRequest>,
    ) -> Result<()> {
        let service_request = &mut ctx.accounts.service_request;

        require!(
            service_request.status == RequestStatus::Pending,
            ErrorCode::CannotCancelRequest
        );

        require!(
            service_request.user == ctx.accounts.user.key(),
            ErrorCode::UnauthorizedUser
        );

        service_request.status = RequestStatus::Cancelled;

        // Refund the user
        let escrow_account = &mut ctx.accounts.escrow_account;
        let user = &mut ctx.accounts.user;

        **escrow_account.try_borrow_mut_lamports()? -= service_request.amount;
        **user.try_borrow_mut_lamports()? += service_request.amount;

        emit!(RequestCancelled {
            request_id: service_request.request_id,
            user: ctx.accounts.user.key(),
            refund_amount: service_request.amount,
            timestamp: Clock::get()?.unix_timestamp,
        });

        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(agent_id: Pubkey)]
pub struct CreateServiceRequest<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + ServiceRequest::INIT_SPACE,
        seeds = [b"request", user.key().as_ref(), agent_id.as_ref()],
        bump
    )]
    pub service_request: Account<'info, ServiceRequest>,

    #[account(
        mut,
        seeds = [b"escrow", service_request.key().as_ref()],
        bump
    )]
    /// CHECK: This is a PDA used for escrow
    pub escrow_account: UncheckedAccount<'info>,

    #[account(mut)]
    pub user: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct SubmitResult<'info> {
    #[account(mut)]
    pub service_request: Account<'info, ServiceRequest>,

    /// CHECK: Agent authority will be verified by the client
    pub agent_authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct ApproveResult<'info> {
    #[account(mut)]
    pub service_request: Account<'info, ServiceRequest>,

    #[account(
        mut,
        seeds = [b"escrow", service_request.key().as_ref()],
        bump
    )]
    /// CHECK: This is a PDA used for escrow
    pub escrow_account: UncheckedAccount<'info>,

    #[account(mut)]
    pub user: Signer<'info>,

    /// CHECK: Creator will receive payment
    #[account(mut)]
    pub creator: UncheckedAccount<'info>,

    /// CHECK: Platform wallet will receive fee
    #[account(mut)]
    pub platform_wallet: UncheckedAccount<'info>,

    /// CHECK: Treasury wallet will receive fee
    #[account(mut)]
    pub treasury_wallet: UncheckedAccount<'info>,
}

#[derive(Accounts)]
pub struct DisputeResult<'info> {
    #[account(mut)]
    pub service_request: Account<'info, ServiceRequest>,

    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct CancelRequest<'info> {
    #[account(mut)]
    pub service_request: Account<'info, ServiceRequest>,

    #[account(
        mut,
        seeds = [b"escrow", service_request.key().as_ref()],
        bump
    )]
    /// CHECK: This is a PDA used for escrow
    pub escrow_account: UncheckedAccount<'info>,

    #[account(mut)]
    pub user: Signer<'info>,
}

#[account]
#[derive(InitSpace)]
pub struct ServiceRequest {
    pub request_id: Pubkey,
    pub agent_id: Pubkey,
    pub user: Pubkey,
    pub amount: u64,
    pub status: RequestStatus,
    #[max_len(1000)]
    pub request_data: String,
    #[max_len(2000)]
    pub result_data: String,
    pub created_at: i64,
    pub completed_at: Option<i64>,
    pub escrow_account: Pubkey,
}

#[derive(AnchorSerialize, AnchorDeserialize, Clone, PartialEq, InitSpace)]
pub enum RequestStatus {
    Pending,
    InProgress,
    Completed,
    Approved,
    Disputed,
    Cancelled,
}

#[event]
pub struct ServiceRequestCreated {
    pub request_id: Pubkey,
    pub agent_id: Pubkey,
    pub user: Pubkey,
    pub amount: u64,
    pub timestamp: i64,
}

#[event]
pub struct ResultSubmitted {
    pub request_id: Pubkey,
    pub agent_id: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct PaymentReleased {
    pub request_id: Pubkey,
    pub creator: Pubkey,
    pub creator_amount: u64,
    pub platform_amount: u64,
    pub treasury_amount: u64,
    pub timestamp: i64,
}

#[event]
pub struct ResultDisputed {
    pub request_id: Pubkey,
    pub user: Pubkey,
    pub reason: String,
    pub timestamp: i64,
}

#[event]
pub struct RequestCancelled {
    pub request_id: Pubkey,
    pub user: Pubkey,
    pub refund_amount: u64,
    pub timestamp: i64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid payment amount")]
    InvalidAmount,
    #[msg("Request data is too long (max 1000 characters)")]
    RequestDataTooLong,
    #[msg("Result data is too long (max 2000 characters)")]
    ResultDataTooLong,
    #[msg("Invalid request status for this operation")]
    InvalidRequestStatus,
    #[msg("Unauthorized user")]
    UnauthorizedUser,
    #[msg("Dispute reason is too long (max 500 characters)")]
    DisputeReasonTooLong,
    #[msg("Cannot cancel request in current status")]
    CannotCancelRequest,
}