#!/usr/bin/env node

/**
 * Update Spec Progress Hook
 * 
 * This script updates the task completion status in spec files
 * based on actual implementation progress.
 */

const fs = require('fs');
const path = require('path');

const SPECS_DIR = path.join(__dirname, '../../specs');

function updateSpecProgress() {
  console.log('🔄 Updating spec progress...\n');

  try {
    // Get all spec directories
    const specDirs = fs.readdirSync(SPECS_DIR, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);

    if (specDirs.length === 0) {
      console.log('ℹ️  No spec directories found.');
      return;
    }

    specDirs.forEach(specName => {
      const tasksFile = path.join(SPECS_DIR, specName, 'tasks.md');
      
      if (!fs.existsSync(tasksFile)) {
        console.log(`⚠️  No tasks.md found for ${specName}`);
        return;
      }

      const content = fs.readFileSync(tasksFile, 'utf8');
      const lines = content.split('\n');
      
      let completed = 0;
      let total = 0;
      
      lines.forEach(line => {
        if (line.trim().match(/^- \[(x| )\]/)) {
          total++;
          if (line.includes('[x]')) {
            completed++;
          }
        }
      });

      const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
      
      console.log(`📊 ${specName}:`);
      console.log(`   Completed: ${completed}/${total} tasks (${percentage}%)`);
      console.log('');
    });

    console.log('✅ Spec progress updated successfully!');
  } catch (error) {
    console.error('❌ Error updating spec progress:', error.message);
    process.exit(1);
  }
}

updateSpecProgress();
