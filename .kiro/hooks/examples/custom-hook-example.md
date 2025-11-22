# Custom Hook Examples

## Example 1: Auto-Update Tests Hook

This hook automatically updates test files when implementation files change.

### Hook Configuration
```json
{
  "id": "update-tests",
  "name": "Update Tests on Implementation Change",
  "description": "Suggest test updates when implementation changes",
  "trigger": "onSave",
  "filePattern": "src/**/*.{ts,tsx}",
  "excludePattern": "**/*.test.{ts,tsx}",
  "enabled": true,
  "command": "node .kiro/hooks/scripts/suggest-test-updates.js ${file}",
  "showNotification": true
}
```

### Script (suggest-test-updates.js)
```javascript
#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const filePath = process.argv[2];
const testPath = filePath.replace(/\.(ts|tsx)$/, '.test.$1');

if (fs.existsSync(testPath)) {
  console.log(`✅ Test file exists: ${testPath}`);
  console.log('💡 Consider updating tests for recent changes');
} else {
  console.log(`⚠️  No test file found for ${filePath}`);
  console.log(`💡 Consider creating: ${testPath}`);
}
```

## Example 2: Smart Contract Validation Hook

Validates Rust smart contract code before committing.

### Hook Configuration
```json
{
  "id": "validate-contracts",
  "name": "Validate Smart Contracts",
  "description": "Run clippy and format checks on Rust files",
  "trigger": "onSave",
  "filePattern": "programs/**/*.rs",
  "enabled": true,
  "command": "cargo clippy --manifest-path programs/Cargo.toml -- -D warnings",
  "showNotification": true
}
```

## Example 3: Documentation Sync Hook

Keeps README in sync with package.json and code changes.

### Hook Configuration
```json
{
  "id": "sync-docs",
  "name": "Sync Documentation",
  "description": "Update README with latest package info",
  "trigger": "onSave",
  "filePattern": "package.json",
  "enabled": true,
  "command": "node .kiro/hooks/scripts/sync-docs.js",
  "showNotification": true
}
```

### Script (sync-docs.js)
```javascript
#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const readmePath = 'README.md';

let readme = fs.readFileSync(readmePath, 'utf8');

// Update version
readme = readme.replace(
  /Version: \d+\.\d+\.\d+/,
  `Version: ${packageJson.version}`
);

// Update dependencies count
const depCount = Object.keys(packageJson.dependencies || {}).length;
readme = readme.replace(
  /Dependencies: \d+/,
  `Dependencies: ${depCount}`
);

fs.writeFileSync(readmePath, readme);
console.log('✅ README.md updated with latest package info');
```

## Example 4: Pre-Commit Security Check

Runs security checks before allowing commits.

### Hook Configuration
```json
{
  "id": "pre-commit-security",
  "name": "Pre-Commit Security Check",
  "description": "Scan for secrets and vulnerabilities before commit",
  "trigger": "onCommit",
  "enabled": true,
  "command": "node .kiro/hooks/scripts/security-check.js",
  "showNotification": true,
  "blockOnFailure": true
}
```

### Script (security-check.js)
```javascript
#!/usr/bin/env node

const { execSync } = require('child_process');

console.log('🔒 Running security checks...\n');

try {
  // Check for secrets
  console.log('1. Checking for exposed secrets...');
  execSync('git diff --cached --name-only | xargs grep -l "sk-" || true', {
    stdio: 'inherit'
  });

  // Check for TODO/FIXME in critical files
  console.log('\n2. Checking for unresolved TODOs in critical files...');
  const todos = execSync(
    'git diff --cached | grep -i "TODO\\|FIXME" || true',
    { encoding: 'utf8' }
  );
  
  if (todos.trim()) {
    console.log('⚠️  Found TODOs in staged changes:');
    console.log(todos);
  }

  // Run npm audit
  console.log('\n3. Running npm audit...');
  execSync('npm audit --audit-level=high', { stdio: 'inherit' });

  console.log('\n✅ Security checks passed!');
  process.exit(0);
} catch (error) {
  console.error('\n❌ Security checks failed!');
  process.exit(1);
}
```

## Example 5: Component Generator Hook

Generates boilerplate for new React components.

### Hook Configuration
```json
{
  "id": "generate-component",
  "name": "Generate React Component",
  "description": "Create new component with boilerplate",
  "trigger": "manual",
  "enabled": true,
  "command": "node .kiro/hooks/scripts/generate-component.js",
  "showNotification": true,
  "promptForInput": true
}
```

### Script (generate-component.js)
```javascript
#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

rl.question('Component name (PascalCase): ', (name) => {
  rl.question('Component type (ui/agents/security): ', (type) => {
    const componentDir = path.join('src', 'components', type);
    const componentPath = path.join(componentDir, `${name}.tsx`);

    if (fs.existsSync(componentPath)) {
      console.log(`❌ Component already exists: ${componentPath}`);
      rl.close();
      return;
    }

    const template = `'use client';

import { FC } from 'react';

interface ${name}Props {
  // Add props here
}

export const ${name}: FC<${name}Props> = (props) => {
  return (
    <div>
      {/* Component content */}
    </div>
  );
};
`;

    fs.mkdirSync(componentDir, { recursive: true });
    fs.writeFileSync(componentPath, template);

    console.log(`✅ Component created: ${componentPath}`);
    rl.close();
  });
});
```

## Example 6: Performance Monitor Hook

Monitors build performance and bundle size.

### Hook Configuration
```json
{
  "id": "monitor-performance",
  "name": "Monitor Build Performance",
  "description": "Track build time and bundle size",
  "trigger": "manual",
  "enabled": true,
  "command": "node .kiro/hooks/scripts/monitor-performance.js",
  "showNotification": true
}
```

### Script (monitor-performance.js)
```javascript
#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('📊 Monitoring build performance...\n');

const startTime = Date.now();

try {
  // Build the project
  console.log('Building project...');
  execSync('npm run build', { stdio: 'inherit' });

  const buildTime = ((Date.now() - startTime) / 1000).toFixed(2);
  console.log(`\n⏱️  Build time: ${buildTime}s`);

  // Check bundle size
  const buildDir = path.join('.next', 'static');
  if (fs.existsSync(buildDir)) {
    const getSize = (dir) => {
      let size = 0;
      const files = fs.readdirSync(dir, { withFileTypes: true });
      
      files.forEach(file => {
        const filePath = path.join(dir, file.name);
        if (file.isDirectory()) {
          size += getSize(filePath);
        } else {
          size += fs.statSync(filePath).size;
        }
      });
      
      return size;
    };

    const totalSize = getSize(buildDir);
    const sizeMB = (totalSize / 1024 / 1024).toFixed(2);
    
    console.log(`📦 Bundle size: ${sizeMB} MB`);

    // Save metrics
    const metrics = {
      timestamp: new Date().toISOString(),
      buildTime: parseFloat(buildTime),
      bundleSize: parseFloat(sizeMB)
    };

    const metricsFile = '.kiro/metrics.json';
    let allMetrics = [];
    
    if (fs.existsSync(metricsFile)) {
      allMetrics = JSON.parse(fs.readFileSync(metricsFile, 'utf8'));
    }
    
    allMetrics.push(metrics);
    fs.writeFileSync(metricsFile, JSON.stringify(allMetrics, null, 2));

    console.log('\n✅ Performance metrics saved!');
  }
} catch (error) {
  console.error('\n❌ Performance monitoring failed:', error.message);
  process.exit(1);
}
```

## Best Practices for Custom Hooks

### 1. Keep Scripts Fast
- Aim for <5 seconds execution time
- Use caching where possible
- Run expensive operations asynchronously

### 2. Provide Clear Feedback
```javascript
console.log('🔄 Starting process...');
console.log('✅ Success!');
console.log('⚠️  Warning: ...');
console.log('❌ Error: ...');
```

### 3. Handle Errors Gracefully
```javascript
try {
  // Hook logic
} catch (error) {
  console.error('❌ Hook failed:', error.message);
  process.exit(1); // Exit with error code
}
```

### 4. Use File Patterns Wisely
```json
{
  "filePattern": "src/**/*.{ts,tsx}",
  "excludePattern": "**/*.test.{ts,tsx}"
}
```

### 5. Add Confirmation for Destructive Actions
```json
{
  "confirmBefore": true,
  "confirmMessage": "This will deploy to production. Continue?"
}
```

### 6. Log Hook Execution
```javascript
const logFile = '.kiro/hooks/logs/hook-execution.log';
const timestamp = new Date().toISOString();
fs.appendFileSync(logFile, `[${timestamp}] Hook executed: ${hookId}\n`);
```

## Testing Custom Hooks

### Manual Testing
```bash
# Test hook script directly
node .kiro/hooks/scripts/your-hook.js

# Test with file argument
node .kiro/hooks/scripts/your-hook.js src/components/Button.tsx
```

### Automated Testing
```javascript
// test-hook.js
const { execSync } = require('child_process');

describe('Custom Hook', () => {
  it('should execute successfully', () => {
    const result = execSync('node .kiro/hooks/scripts/your-hook.js', {
      encoding: 'utf8'
    });
    
    expect(result).toContain('✅');
  });
});
```

## Debugging Hooks

### Enable Verbose Logging
```json
{
  "verbose": true,
  "logFile": ".kiro/hooks/logs/debug.log"
}
```

### Check Hook Execution
```bash
# View hook logs
cat .kiro/hooks/logs/hook-execution.log

# Test hook manually
npm run hook:test your-hook-id
```
