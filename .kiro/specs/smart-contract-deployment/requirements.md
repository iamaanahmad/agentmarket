# Requirements Document

## Introduction

This document outlines the requirements for deploying and managing the AgentMarket smart contracts on the Solana blockchain. The deployment system must handle multiple Anchor programs across different environments (devnet, testnet, mainnet) with proper configuration management, verification, and monitoring.

## Glossary

- **Anchor Program**: A Solana smart contract built using the Anchor framework
- **Program ID**: A unique public key identifier for a deployed Solana program
- **IDL (Interface Definition Language)**: A JSON file describing the program's interface
- **Devnet**: Solana's development network for testing
- **Mainnet**: Solana's production network
- **PDA (Program Derived Address)**: A deterministic address derived from a program ID and seeds
- **Deployment System**: The automated tooling and scripts for deploying smart contracts
- **Program Authority**: The wallet with permission to upgrade a deployed program
- **Upgrade Authority**: The account that can modify a deployed program

## Requirements

### Requirement 1

**User Story:** As a smart contract developer, I want to build all Anchor programs with proper configuration, so that they are ready for deployment to any network.

#### Acceptance Criteria

1. WHEN the developer runs the build command, THE Deployment System SHALL compile all four Anchor programs (agent_registry, marketplace_escrow, reputation_system, royalty_splitter) successfully
2. WHEN a program is built, THE Deployment System SHALL generate the corresponding IDL file in JSON format
3. WHEN a build fails, THE Deployment System SHALL display clear error messages indicating which program failed and why
4. THE Deployment System SHALL validate that all program dependencies are correctly specified in Cargo.toml files
5. WHEN building for a specific network, THE Deployment System SHALL use the appropriate program IDs from the configuration

### Requirement 2

**User Story:** As a smart contract developer, I want to deploy programs to devnet for testing, so that I can validate functionality before mainnet deployment.

#### Acceptance Criteria

1. WHEN the developer initiates devnet deployment, THE Deployment System SHALL deploy all programs to Solana devnet within 60 seconds
2. WHEN a program is deployed, THE Deployment System SHALL verify the deployment by fetching the program account
3. WHEN deployment completes, THE Deployment System SHALL save the program IDs to a configuration file
4. THE Deployment System SHALL validate that the deploying wallet has sufficient SOL balance before attempting deployment
5. WHEN a program already exists at the target address, THE Deployment System SHALL perform an upgrade instead of initial deployment
6. WHEN deployment fails, THE Deployment System SHALL provide detailed error information and rollback instructions

### Requirement 3

**User Story:** As a smart contract developer, I want to initialize program state accounts after deployment, so that the programs are ready to accept user transactions.

#### Acceptance Criteria

1. WHEN programs are deployed, THE Deployment System SHALL create all required PDA accounts for each program
2. WHEN initializing the agent registry, THE Deployment System SHALL set the platform configuration with admin and treasury wallet addresses
3. WHEN initializing the escrow program, THE Deployment System SHALL configure the platform fee percentage (10%) and treasury allocation (5%)
4. THE Deployment System SHALL validate that all initialization transactions succeed before marking deployment as complete
5. WHEN initialization fails, THE Deployment System SHALL provide clear instructions for manual recovery

### Requirement 4

**User Story:** As a smart contract developer, I want to verify deployed programs match the source code, so that I can ensure deployment integrity.

#### Acceptance Criteria

1. WHEN deployment completes, THE Deployment System SHALL compute the hash of the deployed program bytecode
2. WHEN verification is requested, THE Deployment System SHALL compare the deployed bytecode hash with the locally built program hash
3. WHEN hashes match, THE Deployment System SHALL mark the deployment as verified
4. WHEN hashes do not match, THE Deployment System SHALL alert the developer and prevent further operations
5. THE Deployment System SHALL store verification results in a deployment log file

### Requirement 5

**User Story:** As a smart contract developer, I want to manage program upgrade authority, so that I can control who can modify deployed programs.

#### Acceptance Criteria

1. WHEN deploying to devnet, THE Deployment System SHALL set the upgrade authority to the deploying wallet
2. WHEN deploying to mainnet, THE Deployment System SHALL prompt for confirmation before setting upgrade authority
3. THE Deployment System SHALL support transferring upgrade authority to a multisig wallet address
4. THE Deployment System SHALL support revoking upgrade authority to make programs immutable
5. WHEN upgrade authority is changed, THE Deployment System SHALL verify the change by querying the program account

### Requirement 6

**User Story:** As a smart contract developer, I want to copy IDL files to the frontend project, so that the UI can interact with deployed contracts.

#### Acceptance Criteria

1. WHEN deployment completes successfully, THE Deployment System SHALL copy all IDL files to the src/lib/idl directory
2. WHEN copying IDL files, THE Deployment System SHALL update the program IDs in each IDL to match the deployed addresses
3. THE Deployment System SHALL validate that IDL files are valid JSON before copying
4. WHEN IDL files are updated, THE Deployment System SHALL trigger TypeScript type regeneration if configured
5. THE Deployment System SHALL maintain a backup of previous IDL files before overwriting

### Requirement 7

**User Story:** As a smart contract developer, I want to run integration tests against deployed programs, so that I can verify they work correctly on-chain.

#### Acceptance Criteria

1. WHEN deployment completes, THE Deployment System SHALL execute the Anchor test suite against the deployed programs
2. WHEN running tests, THE Deployment System SHALL use the correct RPC endpoint for the target network
3. THE Deployment System SHALL validate that all test accounts have sufficient SOL for test transactions
4. WHEN tests fail, THE Deployment System SHALL provide detailed logs showing which test failed and why
5. THE Deployment System SHALL support running individual test files for specific programs

### Requirement 8

**User Story:** As a smart contract developer, I want to monitor deployed program health, so that I can detect and respond to issues quickly.

#### Acceptance Criteria

1. WHEN programs are deployed, THE Deployment System SHALL record deployment metadata (timestamp, network, program IDs, deployer wallet)
2. THE Deployment System SHALL provide a command to check the status of all deployed programs
3. WHEN checking status, THE Deployment System SHALL verify each program account exists and is executable
4. THE Deployment System SHALL display the current upgrade authority for each program
5. THE Deployment System SHALL calculate and display the total rent-exempt balance required for all program accounts

### Requirement 9

**User Story:** As a smart contract developer, I want to deploy to mainnet with safety checks, so that I can minimize the risk of production issues.

#### Acceptance Criteria

1. WHEN initiating mainnet deployment, THE Deployment System SHALL require explicit confirmation with a typed phrase
2. WHEN deploying to mainnet, THE Deployment System SHALL verify all programs have passed devnet testing
3. THE Deployment System SHALL validate that the deploying wallet has sufficient SOL for deployment and rent
4. THE Deployment System SHALL perform a dry-run simulation before actual mainnet deployment
5. WHEN mainnet deployment completes, THE Deployment System SHALL send a notification to configured channels (email, Slack, Discord)
6. THE Deployment System SHALL create a deployment report with all program IDs, transaction signatures, and verification hashes

### Requirement 10

**User Story:** As a smart contract developer, I want to manage deployment configurations for different environments, so that I can easily switch between networks.

#### Acceptance Criteria

1. THE Deployment System SHALL maintain separate configuration files for devnet, testnet, and mainnet
2. WHEN switching environments, THE Deployment System SHALL load the appropriate RPC endpoint, program IDs, and wallet configuration
3. THE Deployment System SHALL validate configuration files on load and report any missing or invalid values
4. THE Deployment System SHALL support environment variables for sensitive values like private keys and API keys
5. WHEN configuration is updated, THE Deployment System SHALL validate the new values before saving
