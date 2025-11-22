#!/usr/bin/env node

/**
 * Component Generator Hook
 * 
 * Generates React component boilerplate with:
 * - TypeScript interface
 * - Proper imports
 * - Component structure
 * - Optional test file
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function toPascalCase(str) {
  return str
    .split(/[-_\s]/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join('');
}

function toKebabCase(str) {
  return str
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .toLowerCase();
}

function generateComponent(name, type, includeTest) {
  const pascalName = toPascalCase(name);
  const kebabName = toKebabCase(name);
  
  const componentDir = path.join('src', 'components', type);
  const componentPath = path.join(componentDir, `${kebabName}.tsx`);
  const testPath = path.join(componentDir, `${kebabName}.test.tsx`);

  // Check if component already exists
  if (fs.existsSync(componentPath)) {
    console.log(`\n❌ Component already exists: ${componentPath}`);
    return false;
  }

  // Determine if it should be a client component
  const isClientComponent = ['agents', 'security', 'wallet'].includes(type);

  // Generate component template
  const componentTemplate = `${isClientComponent ? "'use client';\n\n" : ''}import { FC } from 'react';
${type === 'ui' ? "import { cn } from '@/lib/utils';\n" : ''}
interface ${pascalName}Props {
  className?: string;
  // Add additional props here
}

export const ${pascalName}: FC<${pascalName}Props> = ({ 
  className,
  ...props 
}) => {
  return (
    <div${type === 'ui' ? ' className={cn("", className)}' : ''}>
      {/* ${pascalName} content */}
    </div>
  );
};
`;

  // Generate test template
  const testTemplate = `import { render, screen } from '@testing-library/react';
import { ${pascalName} } from './${kebabName}';

describe('${pascalName}', () => {
  it('renders without crashing', () => {
    render(<${pascalName} />);
    expect(screen.getByRole('generic')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<${pascalName} className="custom-class" />);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});
`;

  // Create directory if it doesn't exist
  fs.mkdirSync(componentDir, { recursive: true });

  // Write component file
  fs.writeFileSync(componentPath, componentTemplate);
  console.log(`\n✅ Component created: ${componentPath}`);

  // Write test file if requested
  if (includeTest) {
    fs.writeFileSync(testPath, testTemplate);
    console.log(`✅ Test file created: ${testPath}`);
  }

  // Update index file if it exists
  const indexPath = path.join(componentDir, 'index.ts');
  if (fs.existsSync(indexPath)) {
    const exportLine = `export { ${pascalName} } from './${kebabName}';\n`;
    fs.appendFileSync(indexPath, exportLine);
    console.log(`✅ Export added to ${indexPath}`);
  } else {
    // Create index file
    const exportLine = `export { ${pascalName} } from './${kebabName}';\n`;
    fs.writeFileSync(indexPath, exportLine);
    console.log(`✅ Index file created: ${indexPath}`);
  }

  console.log('\n📝 Next steps:');
  console.log(`   1. Open ${componentPath}`);
  console.log(`   2. Add your component logic`);
  console.log(`   3. Import: import { ${pascalName} } from '@/components/${type}';`);
  console.log('');

  return true;
}

// Interactive prompts
console.log('🎨 React Component Generator\n');

rl.question('Component name (e.g., AgentCard, WalletButton): ', (name) => {
  if (!name || name.trim() === '') {
    console.log('❌ Component name is required');
    rl.close();
    return;
  }

  rl.question('Component type (ui/agents/security/wallet): ', (type) => {
    const validTypes = ['ui', 'agents', 'security', 'wallet'];
    
    if (!validTypes.includes(type)) {
      console.log(`❌ Invalid type. Choose from: ${validTypes.join(', ')}`);
      rl.close();
      return;
    }

    rl.question('Include test file? (y/n): ', (includeTestAnswer) => {
      const includeTest = includeTestAnswer.toLowerCase() === 'y';
      
      generateComponent(name.trim(), type, includeTest);
      rl.close();
    });
  });
});
