# AgentMarket - Kiro IDE Usage Guide

## Overview

This document outlines how we're using Kiro IDE throughout the AgentMarket development process. This is critical for the hackathon submission as we must demonstrate effective use of Kiro IDE.

## Mandatory Hackathon Requirements

### .kiro Folder Structure
```
.kiro/
├── specs/
│   └── [feature-name]/
│       ├── requirements.md    # User stories with EARS notation
│       ├── design.md          # Technical architecture
│       └── tasks.md           # Implementation checklist
├── steering/
│   ├── project-context.md     # Project overview
│   ├── architecture.md        # System architecture
│   ├── coding-standards.md    # Code style guidelines
│   ├── security-guidelines.md # Security best practices
│   ├── testing-strategy.md    # Testing approach
│   └── kiro-ide-usage.md      # This file
└── README.md                  # Kiro IDE documentation
```

## Spec-Driven Development Workflow

### Phase 1: Requirements Gathering

**Goal:** Transform rough feature ideas into structured requirements

**Process:**
1. Create `.kiro/specs/[feature-name]/requirements.md`
2. Write user stories in format:
   ```markdown
   ### Requirement 1
   **User Story:** As a [role], I want [feature], so that [benefit]
   
   #### Acceptance Criteria
   1. WHEN [event], THE [System] SHALL [response]
   2. WHILE [state], THE [System] SHALL [response]
   ```
3. Use EARS (Easy Approach to Requirements Syntax) patterns
4. Follow INCOSE semantic quality rules
5. Iterate with team until approved

**Example:**
```markdown
### Requirement 1: Agent Registration

**User Story:** As an AI agent creator, I want to register my agent on-chain with capabilities and pricing, so that users can discover and hire my agent while I earn royalties.

#### Acceptance Criteria
1. WHEN the creator submits valid agent metadata, THE AgentMarket SHALL mint an NFT to the creator's wallet within 5 seconds
2. WHEN the agent is registered, THE AgentMarket SHALL make the agent searchable in the marketplace immediately
3. THE AgentMarket SHALL validate that agent name is between 1-50 characters
4. THE AgentMarket SHALL validate that pricing is greater than 0 and less than 1000 SOL
```

### Phase 2: Design Documentation

**Goal:** Create comprehensive technical design based on requirements

**Process:**
1. Create `.kiro/specs/[feature-name]/design.md`
2. Include sections:
   - Overview
   - Architecture diagrams
   - Component specifications
   - Data models
   - API contracts
   - Error handling
   - Testing strategy
3. Reference requirements document
4. Iterate until approved

**Example Structure:**
```markdown
# Agent Registration - Design Document

## Overview
This feature enables AI agent creators to register their agents on the Solana blockchain...

## Architecture
[Mermaid diagram showing flow]

## Smart Contract Design
### AgentProfile Account Structure
```rust
pub struct AgentProfile {
    pub agent_id: Pubkey,
    pub creator: Pubkey,
    // ...
}
```

## API Design
### POST /api/agents/register
Request body: {...}
Response: {...}
```

### Phase 3: Task Breakdown

**Goal:** Convert design into actionable implementation tasks

**Process:**
1. Create `.kiro/specs/[feature-name]/tasks.md`
2. Break design into discrete coding tasks
3. Use checkbox format with hierarchy:
   ```markdown
   - [ ] 1. Setup project structure
   - [ ] 1.1 Create smart contract skeleton
   - [ ] 1.2 Setup API routes
   - [ ]* 1.3 Write unit tests (optional)
   ```
4. Link each task to requirements
5. Mark testing tasks as optional with `*`
6. Iterate until approved

**Task Format:**
```markdown
- [ ] 2. Implement agent registration smart contract
- [ ] 2.1 Create AgentProfile account structure
  - Define all fields (agent_id, creator, name, etc.)
  - Implement space calculation
  - _Requirements: 1.1, 1.2_
  
- [ ] 2.2 Implement register_agent instruction
  - Validate input parameters
  - Mint NFT to creator
  - Store metadata on-chain
  - _Requirements: 1.1, 1.3, 1.4_
  
- [ ]* 2.3 Write unit tests for registration
  - Test successful registration
  - Test input validation
  - Test unauthorized access
  - _Requirements: 1.1_
```

### Phase 4: Implementation

**Goal:** Execute tasks one at a time with Kiro IDE assistance

**Process:**
1. Open `tasks.md` in Kiro IDE
2. Click "Start task" next to a task item
3. Kiro IDE reads requirements.md and design.md for context
4. Implement the specific task
5. Mark task as complete
6. Move to next task

**Best Practices:**
- Only work on ONE task at a time
- Read requirements and design before coding
- Follow coding standards from steering files
- Test implementation before marking complete
- Don't skip ahead to other tasks

## AWS Q Developer Integration

### How We Use Q Developer

**Code Generation:**
```
Prompt: "Generate Anchor smart contract for agent registration based on design.md"
Q Developer: [Generates Rust code following Anchor patterns]
```

**Code Review:**
```
Prompt: "Review this smart contract for security issues"
Q Developer: [Analyzes code, suggests improvements]
```

**Documentation:**
```
Prompt: "Generate API documentation for /api/agents/register endpoint"
Q Developer: [Creates comprehensive API docs]
```

**Test Generation:**
```
Prompt: "Generate integration tests for agent registration flow"
Q Developer: [Creates test suite]
```

### Evidence Collection

Throughout development, we collect:
- Screenshots of Q Developer suggestions
- Examples of generated code
- Before/after code improvements
- Spec → Implementation examples

This proves Q Developer usage for judges.

## Steering Files Usage

### Always Included Context

These files are automatically included in all Kiro IDE interactions:

**project-context.md:**
- Project overview and goals
- Technology stack
- Core features
- Success metrics

**architecture.md:**
- System architecture diagrams
- Component specifications
- Data flow diagrams
- Infrastructure details

**coding-standards.md:**
- TypeScript/React conventions
- Rust/Anchor patterns
- Python standards
- Testing guidelines

**security-guidelines.md:**
- Smart contract security
- Frontend security
- API security
- Best practices

**testing-strategy.md:**
- Testing philosophy
- Test types and coverage
- Example test patterns

### Conditional Context

Files can be conditionally included based on file patterns:

```markdown
---
inclusion: fileMatch
fileMatchPattern: '*.rs'
---

# Rust-Specific Guidelines
[Rust coding standards]
```

### Manual Context

Files can be manually included via `#` in chat:

```
User: "Help me implement the escrow contract #escrow-design.md"
Kiro: [Reads escrow-design.md and provides implementation]
```

## Kiro IDE Features We Use

### 1. Spec-Driven Development
- Create requirements → design → tasks workflow
- Iterate on each phase with approval gates
- Track progress with task checkboxes

### 2. Context Management
- Steering files provide consistent context
- File references (#file) for specific context
- Codebase scanning (#Codebase) for discovery

### 3. Code Generation
- Generate boilerplate from specs
- Create tests from requirements
- Scaffold components from design

### 4. Code Review
- Review for security issues
- Check against coding standards
- Validate against requirements

### 5. Documentation
- Generate API docs
- Create README files
- Document complex logic

## Documentation for Judges

### README.md Structure

```markdown
# AgentMarket

## Kiro IDE Usage

This project was built using Kiro IDE's spec-driven development workflow.

### Spec Files
- [Agent Registration Requirements](/.kiro/specs/agent-registration/requirements.md)
- [Agent Registration Design](/.kiro/specs/agent-registration/design.md)
- [Agent Registration Tasks](/.kiro/specs/agent-registration/tasks.md)

### Development Process
1. **Requirements Phase:** Defined user stories with EARS notation
2. **Design Phase:** Created technical architecture and data models
3. **Implementation Phase:** Executed tasks one by one with Kiro IDE

### AWS Q Developer Integration
- Used for code generation from specs
- Code review and security analysis
- Test generation
- Documentation creation

[Screenshots and examples]

### Steering Files
We created comprehensive steering files to provide consistent context:
- Project context and architecture
- Coding standards
- Security guidelines
- Testing strategy

These files ensured all generated code followed best practices.
```

### Video Demonstration

**Script for Demo Video (30 seconds on Kiro IDE):**

1. **Show .kiro folder structure** (5s)
   - "We used Kiro IDE's spec-driven development"
   - Show requirements.md, design.md, tasks.md

2. **Show requirements document** (5s)
   - "Started with structured requirements using EARS notation"
   - Highlight user stories and acceptance criteria

3. **Show design document** (5s)
   - "Created detailed technical design"
   - Show architecture diagrams and data models

4. **Show tasks execution** (10s)
   - "Broke design into actionable tasks"
   - Show task list with checkboxes
   - Demonstrate "Start task" feature

5. **Show AWS Q Developer usage** (5s)
   - "Used Q Developer for code generation and review"
   - Show example of generated code

## Best Practices

### Do's
✅ Create complete specs before coding
✅ Use EARS notation for requirements
✅ Link tasks to specific requirements
✅ Execute one task at a time
✅ Collect evidence of Q Developer usage
✅ Keep steering files updated
✅ Document the development process

### Don'ts
❌ Skip requirements or design phases
❌ Start coding without specs
❌ Work on multiple tasks simultaneously
❌ Ignore steering file guidelines
❌ Forget to document Kiro IDE usage
❌ Skip task completion tracking

## Submission Checklist

### .kiro Folder
- [ ] Complete requirements.md for all features
- [ ] Detailed design.md for all features
- [ ] Task breakdown in tasks.md
- [ ] All tasks marked complete
- [ ] Steering files present and comprehensive

### Documentation
- [ ] README explains Kiro IDE usage
- [ ] Screenshots of spec files
- [ ] Examples of Q Developer usage
- [ ] Development process documented

### Demo Video
- [ ] Show .kiro folder structure
- [ ] Demonstrate spec-driven workflow
- [ ] Highlight Q Developer integration
- [ ] Explain how specs guided implementation

## Example: Complete Feature Development

### Feature: Agent Registration

**1. Requirements (.kiro/specs/agent-registration/requirements.md)**
- 5 user stories with acceptance criteria
- EARS notation for all requirements
- Clear, testable criteria

**2. Design (.kiro/specs/agent-registration/design.md)**
- Smart contract structure
- API endpoint specifications
- Frontend component design
- Data flow diagrams
- Error handling strategy

**3. Tasks (.kiro/specs/agent-registration/tasks.md)**
- 15 implementation tasks
- Each linked to requirements
- Testing tasks marked optional
- Clear dependencies

**4. Implementation**
- Used Kiro IDE to execute tasks
- Q Developer generated boilerplate
- Followed coding standards
- Completed all tasks

**5. Evidence**
- Screenshots of each phase
- Q Developer code examples
- Before/after improvements
- Task completion tracking

This demonstrates perfect Kiro IDE usage for judges.
