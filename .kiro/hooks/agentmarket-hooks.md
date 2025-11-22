# AgentMarket - Recommended Hooks for Development

## Overview

This document outlines the recommended Kiro IDE hooks specifically configured for AgentMarket development. These hooks automate common tasks and ensure code quality throughout the development process.

## Essential Hooks for AgentMarket

### 1. Code Quality Hooks

#### Format on Save
**Purpose:** Automatically format code to maintain consistent style
**Trigger:** On file save
**Files:** All TypeScript/React files

```json
{
  "id": "format-on-save",
  "enabled": true,
  "trigger": "onSave",
  "filePattern": "**/*.{ts,tsx,js,jsx}"
}
```

**Why it's important:**
- Maintains consistent code style across the team
- Reduces code review friction
- Follows AgentMarket coding standards

#### Lint on Save
**Purpose:** Catch errors and enforce best practices
**Trigger:** On file save
**Files:** Source files only

```json
{
  "id": "lint-on-save",
  "enabled": true,
  "trigger": "onSave",
  "filePattern": "src/**/*.{ts,tsx}"
}
```

**Why it's important:**
- Catches common errors early
- Enforces TypeScript best practices
- Prevents bugs before they reach production

### 2. Smart Contract Hooks

#### Build Contracts
**Purpose:** Compile Anchor smart contracts
**Trigger:** Manual
**Command:** `anchor build`

```json
{
  "id": "build-contracts",
  "enabled": true,
  "trigger": "manual"
}
```

**When to use:**
- After modifying Rust contract code
- Before running tests
- Before deployment

#### Test Contracts
**Purpose:** Run Anchor test suite
**Trigger:** Manual
**Command:** `anchor test`

```json
{
  "id": "test-contracts",
  "enabled": true,
  "trigger": "manual"
}
```

**When to use:**
- After implementing new contract instructions
- Before committing contract changes
- During development to verify functionality

#### Deploy to Devnet
**Purpose:** Deploy contracts to Solana devnet
**Trigger:** Manual (with confirmation)
**Command:** `anchor deploy --provider.cluster devnet`

```json
{
  "id": "deploy-devnet",
  "enabled": true,
  "trigger": "manual",
  "confirmBefore": true
}
```

**When to use:**
- After successful local testing
- To test integration with frontend
- Before mainnet deployment

### 3. Security Hooks

#### Security Scan
**Purpose:** Scan code for security vulnerabilities
**Trigger:** Manual or pre-commit
**Script:** `.kiro/hooks/scripts/security-check.js`

```json
{
  "id": "security-scan",
  "enabled": true,
  "trigger": "manual"
}
```

**What it checks:**
- Exposed API keys and secrets
- Hardcoded credentials
- Vulnerable dependencies
- Smart contract security issues

**When to use:**
- Before committing sensitive code
- After adding new dependencies
- Before deployment

### 4. Testing Hooks

#### Run Tests on Save
**Purpose:** Run relevant tests when test files change
**Trigger:** On save (test files only)
**Files:** `**/*.test.{ts,tsx}`

```json
{
  "id": "test-on-save",
  "enabled": false,
  "trigger": "onSave",
  "filePattern": "**/*.test.{ts,tsx}"
}
```

**Note:** Disabled by default to avoid slowing down development. Enable when working on specific features.

#### Type Check
**Purpose:** Run TypeScript compiler to check types
**Trigger:** Manual
**Command:** `npm run type-check`

```json
{
  "id": "type-check",
  "enabled": true,
  "trigger": "manual"
}
```

**When to use:**
- Before committing
- After major refactoring
- When TypeScript errors appear

### 5. Documentation Hooks

#### Update API Docs
**Purpose:** Generate API documentation from code
**Trigger:** Manual
**Command:** `npm run docs:generate`

```json
{
  "id": "update-api-docs",
  "enabled": true,
  "trigger": "manual"
}
```

**When to use:**
- After adding new API endpoints
- Before creating pull requests
- When updating public interfaces

#### Update Spec Progress
**Purpose:** Track task completion in spec files
**Trigger:** Manual
**Script:** `.kiro/hooks/scripts/update-specs.js`

```json
{
  "id": "update-specs",
  "enabled": true,
  "trigger": "manual"
}
```

**When to use:**
- After completing tasks
- To check overall progress
- For hackathon submission preparation

### 6. Performance Hooks

#### Bundle Analysis
**Purpose:** Analyze bundle size and performance
**Trigger:** Manual
**Command:** `npm run analyze`

```json
{
  "id": "bundle-analysis",
  "enabled": true,
  "trigger": "manual"
}
```

**When to use:**
- After adding new dependencies
- When optimizing performance
- Before production deployment

#### Accessibility Audit
**Purpose:** Check for accessibility issues
**Trigger:** Manual
**Command:** `npm run a11y-check`

```json
{
  "id": "accessibility-audit",
  "enabled": true,
  "trigger": "manual"
}
```

**When to use:**
- After creating new UI components
- Before major releases
- To ensure WCAG compliance

### 7. Development Workflow Hooks

#### Generate Component
**Purpose:** Create new React component with boilerplate
**Trigger:** Manual
**Script:** `.kiro/hooks/scripts/generate-component.js`

```json
{
  "id": "generate-component",
  "enabled": true,
  "trigger": "manual"
}
```

**When to use:**
- When creating new UI components
- To maintain consistent component structure
- To speed up development

## Recommended Hook Workflow

### Daily Development
1. **Enable:** `format-on-save`, `lint-on-save`
2. **Use manually:** `type-check` before commits
3. **Run occasionally:** `security-scan`

### Smart Contract Development
1. **After code changes:** `build-contracts`
2. **Before committing:** `test-contracts`
3. **For integration testing:** `deploy-devnet`

### Before Committing
1. Run `type-check`
2. Run `security-scan`
3. Ensure all tests pass
4. Update spec progress if completing tasks

### Before Pull Request
1. Run `bundle-analysis`
2. Run `accessibility-audit`
3. Update API documentation
4. Verify all hooks pass

### Before Deployment
1. Run full test suite
2. Run security scan
3. Build and test contracts
4. Deploy to devnet first
5. Verify all functionality

## Hook Configuration Tips

### Performance Optimization
```json
{
  "showNotification": false,  // Disable for frequent hooks
  "timeout": 30000,           // 30 second timeout
  "runInBackground": true     // Don't block IDE
}
```

### Debugging Hooks
```json
{
  "verbose": true,
  "logFile": ".kiro/hooks/logs/debug.log"
}
```

### Conditional Execution
```json
{
  "filePattern": "src/**/*.{ts,tsx}",
  "excludePattern": "**/*.test.{ts,tsx}",
  "condition": "git diff --cached --name-only"
}
```

## Custom Hooks for AgentMarket

### SecurityGuard AI Test Hook
Test SecurityGuard AI transaction scanning:

```json
{
  "id": "test-security-guard",
  "name": "Test SecurityGuard AI",
  "description": "Run SecurityGuard AI tests",
  "trigger": "manual",
  "command": "npm test -- security-guard",
  "enabled": true
}
```

### Solana RPC Health Check
Verify Solana RPC connection:

```json
{
  "id": "check-rpc",
  "name": "Check Solana RPC",
  "description": "Verify RPC connection and cluster",
  "trigger": "manual",
  "command": "solana cluster-version",
  "enabled": true
}
```

### Agent Registry Sync
Sync agent data from blockchain:

```json
{
  "id": "sync-agents",
  "name": "Sync Agent Registry",
  "description": "Fetch latest agent data from blockchain",
  "trigger": "manual",
  "command": "node scripts/sync-agents.js",
  "enabled": true
}
```

## Troubleshooting

### Hook Not Running
1. Check if hook is enabled in config
2. Verify file pattern matches
3. Check hook logs: `.kiro/hooks/logs/`
4. Test script manually: `node .kiro/hooks/scripts/[script].js`

### Hook Failing
1. Check error message in notification
2. Review hook logs
3. Verify dependencies are installed
4. Test command in terminal

### Hook Too Slow
1. Reduce scope with file patterns
2. Enable background execution
3. Disable notifications
4. Optimize script logic

## Best Practices

1. **Start with essential hooks only** - Add more as needed
2. **Test hooks manually first** - Before enabling auto-trigger
3. **Monitor hook performance** - Disable slow hooks
4. **Keep scripts simple** - Complex logic slows down IDE
5. **Use file patterns wisely** - Avoid scanning unnecessary files
6. **Provide clear feedback** - Use emojis and clear messages
7. **Log important events** - For debugging and auditing
8. **Document custom hooks** - Help team understand purpose

## For Hackathon Judges

These hooks demonstrate:
- **Automation:** Streamlined development workflow
- **Quality:** Automated code quality checks
- **Security:** Built-in security scanning
- **Efficiency:** Reduced manual tasks
- **Best Practices:** Following industry standards

The hooks are configured to support the spec-driven development workflow and ensure high-quality code throughout the AgentMarket project.
