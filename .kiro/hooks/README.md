# AgentMarket - Kiro Hooks

## Overview

This directory contains Kiro IDE agent hooks that automate development workflows. Hooks trigger automatically based on events (file saves, git commits) or manually via buttons in the IDE.

## Available Hooks

### Development Hooks
- **format-on-save**: Auto-format code on file save
- **lint-on-save**: Run linter on TypeScript/React files
- **test-on-save**: Run relevant tests when test files are saved
- **type-check**: Run TypeScript type checking

### Smart Contract Hooks
- **build-contracts**: Build Anchor smart contracts
- **test-contracts**: Run Anchor test suite
- **deploy-devnet**: Deploy contracts to Solana devnet

### Documentation Hooks
- **update-api-docs**: Generate API documentation from code
- **sync-readme**: Update README with latest project info
- **generate-changelog**: Create changelog from git commits

### Quality Assurance Hooks
- **security-scan**: Run security checks on code changes
- **performance-check**: Analyze bundle size and performance
- **accessibility-audit**: Check for accessibility issues

## Hook Configuration

Hooks are configured in `.kiro/hooks/config.json` with the following structure:

```json
{
  "hooks": [
    {
      "id": "format-on-save",
      "name": "Format Code on Save",
      "trigger": "onSave",
      "filePattern": "**/*.{ts,tsx,js,jsx}",
      "enabled": true,
      "command": "npm run format"
    }
  ]
}
```

## Creating Custom Hooks

To create a new hook:

1. Define hook in `config.json`
2. Create hook script in `.kiro/hooks/scripts/`
3. Test hook manually
4. Enable automatic triggering

## Usage

### Automatic Triggers
Hooks with `trigger: "onSave"` or `trigger: "onCommit"` run automatically.

### Manual Triggers
1. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Search for "Run Kiro Hook"
3. Select hook to execute

### Via Explorer
1. Open "Agent Hooks" section in Explorer
2. Click play button next to hook name

## Best Practices

- Keep hooks fast (<5 seconds)
- Use file patterns to limit scope
- Provide clear success/failure messages
- Log hook execution for debugging
- Test hooks before enabling auto-trigger
