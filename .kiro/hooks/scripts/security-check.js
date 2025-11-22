#!/usr/bin/env node

/**
 * Security Check Hook
 * 
 * Scans code for common security issues:
 * - Exposed API keys and secrets
 * - Hardcoded credentials
 * - Unsafe dependencies
 * - Common vulnerabilities
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const SECURITY_PATTERNS = [
  { pattern: /sk-[a-zA-Z0-9]{32,}/, message: 'Anthropic API key detected' },
  { pattern: /AKIA[0-9A-Z]{16}/, message: 'AWS Access Key detected' },
  { pattern: /ghp_[a-zA-Z0-9]{36}/, message: 'GitHub Personal Access Token detected' },
  { pattern: /xoxb-[0-9]{11}-[0-9]{11}-[a-zA-Z0-9]{24}/, message: 'Slack Bot Token detected' },
  { pattern: /AIza[0-9A-Za-z\\-_]{35}/, message: 'Google API Key detected' },
  { pattern: /password\s*=\s*["'][^"']+["']/, message: 'Hardcoded password detected' },
  { pattern: /private_key\s*=\s*["'][^"']+["']/, message: 'Private key detected' },
];

function scanFile(filePath) {
  const issues = [];
  
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    lines.forEach((line, index) => {
      SECURITY_PATTERNS.forEach(({ pattern, message }) => {
        if (pattern.test(line)) {
          issues.push({
            file: filePath,
            line: index + 1,
            message,
            content: line.trim()
          });
        }
      });
    });
  } catch (error) {
    console.error(`⚠️  Could not scan ${filePath}: ${error.message}`);
  }
  
  return issues;
}

function scanDirectory(dir, excludePatterns = []) {
  let allIssues = [];
  
  const files = fs.readdirSync(dir, { withFileTypes: true });
  
  files.forEach(file => {
    const filePath = path.join(dir, file.name);
    
    // Skip excluded patterns
    if (excludePatterns.some(pattern => filePath.includes(pattern))) {
      return;
    }
    
    if (file.isDirectory()) {
      allIssues = allIssues.concat(scanDirectory(filePath, excludePatterns));
    } else if (file.name.match(/\.(ts|tsx|js|jsx|json|env)$/)) {
      allIssues = allIssues.concat(scanFile(filePath));
    }
  });
  
  return allIssues;
}

function runSecurityCheck() {
  console.log('🔒 Running security checks...\n');
  
  const excludePatterns = [
    'node_modules',
    '.next',
    'dist',
    'build',
    '.git',
    '.kiro/hooks/examples'
  ];
  
  // 1. Scan for secrets in code
  console.log('1️⃣  Scanning for exposed secrets...');
  const issues = scanDirectory('src', excludePatterns);
  
  if (issues.length > 0) {
    console.log(`\n❌ Found ${issues.length} potential security issue(s):\n`);
    issues.forEach(issue => {
      console.log(`   ${issue.file}:${issue.line}`);
      console.log(`   ⚠️  ${issue.message}`);
      console.log(`   📝 ${issue.content.substring(0, 80)}...`);
      console.log('');
    });
    return false;
  }
  console.log('   ✅ No secrets detected\n');
  
  // 2. Check environment files
  console.log('2️⃣  Checking environment files...');
  const envFiles = ['.env', '.env.local', '.env.production'];
  let envIssues = false;
  
  envFiles.forEach(file => {
    if (fs.existsSync(file)) {
      try {
        const gitIgnore = fs.readFileSync('.gitignore', 'utf8');
        if (!gitIgnore.includes(file)) {
          console.log(`   ⚠️  ${file} is not in .gitignore`);
          envIssues = true;
        }
      } catch (error) {
        // .gitignore doesn't exist
      }
    }
  });
  
  if (!envIssues) {
    console.log('   ✅ Environment files properly configured\n');
  } else {
    console.log('');
  }
  
  // 3. Check for vulnerable dependencies
  console.log('3️⃣  Checking for vulnerable dependencies...');
  try {
    execSync('npm audit --audit-level=high', { stdio: 'inherit' });
    console.log('   ✅ No high-severity vulnerabilities\n');
  } catch (error) {
    console.log('   ⚠️  Vulnerabilities detected (see above)\n');
    return false;
  }
  
  // 4. Check for common security issues in smart contracts
  if (fs.existsSync('programs')) {
    console.log('4️⃣  Checking smart contracts...');
    const contractIssues = [];
    
    // Check for common Solana/Anchor issues
    const checkContract = (filePath) => {
      const content = fs.readFileSync(filePath, 'utf8');
      
      // Check for missing input validation
      if (content.includes('pub fn') && !content.includes('require!')) {
        contractIssues.push({
          file: filePath,
          message: 'Missing input validation (require! macro)'
        });
      }
      
      // Check for unchecked arithmetic
      if (content.match(/\+|\-|\*|\//) && !content.includes('checked_')) {
        contractIssues.push({
          file: filePath,
          message: 'Potential integer overflow (use checked arithmetic)'
        });
      }
    };
    
    const scanContracts = (dir) => {
      const files = fs.readdirSync(dir, { withFileTypes: true });
      files.forEach(file => {
        const filePath = path.join(dir, file.name);
        if (file.isDirectory()) {
          scanContracts(filePath);
        } else if (file.name.endsWith('.rs')) {
          checkContract(filePath);
        }
      });
    };
    
    scanContracts('programs');
    
    if (contractIssues.length > 0) {
      console.log(`   ⚠️  Found ${contractIssues.length} potential issue(s) in contracts:`);
      contractIssues.forEach(issue => {
        console.log(`      ${issue.file}: ${issue.message}`);
      });
      console.log('');
    } else {
      console.log('   ✅ No obvious security issues in contracts\n');
    }
  }
  
  return issues.length === 0;
}

// Run the security check
const passed = runSecurityCheck();

if (passed) {
  console.log('✅ All security checks passed!\n');
  process.exit(0);
} else {
  console.log('❌ Security checks failed. Please fix the issues above.\n');
  process.exit(1);
}
