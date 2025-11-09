/**
 * AI-Powered Cypress Test Generator
 * Automatically generates E2E test scenarios using Claude API
 *
 * Usage:
 * - With Claude API: ANTHROPIC_API_KEY=xxx npm run generate:tests
 * - With Cursor: Just ask Cursor to generate tests (free!)
 */

import { promises as fs } from 'node:fs'
import path from 'node:path'

// ============================================================================
// Configuration
// ============================================================================

interface TestScenario {
  name: string
  description: string
  steps: string[]
  assertions: string[]
}

interface TestSuite {
  suiteName: string
  description: string
  scenarios: TestScenario[]
}

// ============================================================================
// Claude API Integration (Optional - requires API key)
// ============================================================================

async function generateWithClaude(prompt: string): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY

  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY not set. Use Cursor instead for free!')
  }

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 4096,
      messages: [
        {
          role: 'user',
          content: prompt,
        },
      ],
    }),
  })

  if (!response.ok) {
    throw new Error(`Claude API error: ${response.statusText}`)
  }

  const data = await response.json()
  return data.content[0].text
}

// ============================================================================
// Test Suite Templates
// ============================================================================

const BILLING_APP_CONTEXT = `
# Billing Calculator Application

## Features:
1. Basic Info Input (UUID, Billing Group ID, Date, Unpaid Amount)
2. Usage Management (Add/Remove usage entries with volume and instance types)
3. Credit Management (Add/Remove credits with different types: FREE, PAID, PROMOTIONAL)
4. Adjustment Management (Add/Remove discounts/surcharges at different levels)
5. Billing Calculation (Calculate statement with all inputs)
6. Payment Processing (Process payment for calculated statement)
7. History Management (Save and load previous calculations)
8. PDF Export (Download billing statement as PDF)

## Tech Stack:
- Next.js 14 (App Router)
- React 19
- TypeScript
- Cloudflare Workers (Backend API)
- React Query (Data fetching)
- Zustand (State management)

## Test Requirements:
- Cover happy paths and edge cases
- Test validation and error handling
- Test integration between components
- Test state persistence (history)
- Test PDF generation
`

function generatePrompt(focus: string): string {
  return `${BILLING_APP_CONTEXT}

Generate Cypress E2E test scenarios for: ${focus}

Return ONLY valid TypeScript code in this exact format:

\`\`\`typescript
describe('Test Suite Name', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('test scenario 1', () => {
    // Test implementation
  })

  it('test scenario 2', () => {
    // Test implementation
  })
})
\`\`\`

Focus on realistic user workflows and edge cases.
Use custom commands: cy.fillBasicInfo(), cy.addUsage(), cy.addCredit(), cy.addAdjustment(), cy.calculateBilling(), cy.processPayment()
`
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Extract TypeScript code from markdown code blocks
 * Uses RegExp.exec() for better performance (SonarQube S6594)
 */
function extractTypeScriptCode(text: string): string | null {
  const regex = /```typescript\n([\s\S]+?)\n```/
  const match = regex.exec(text)
  return match ? match[1] : null
}

// ============================================================================
// Test Generation Functions
// ============================================================================

async function generateTestSuite(
  suiteName: string,
  focus: string
): Promise<string> {
  console.log(`🤖 Generating test suite: ${suiteName}`)
  console.log(`📝 Focus: ${focus}`)

  const prompt = generatePrompt(focus)

  // Try Claude API if available, otherwise provide template
  if (!process.env.ANTHROPIC_API_KEY) {
    console.log('ℹ️  No API key found. Generating template...')
    console.log('💡 Tip: Ask Cursor to fill in the test implementation!')
    return generateTemplate(suiteName, focus)
  }

  console.log('🔑 Using Claude API...')
  try {
    const generated = await generateWithClaude(prompt)
    return extractTypeScriptCode(generated) || generated
  } catch (error) {
    console.error('⚠️  Claude API failed:', error instanceof Error ? error.message : String(error))
    console.log('Falling back to template generation')
    return generateTemplate(suiteName, focus)
  }
}

function generateTemplate(suiteName: string, focus: string): string {
  return `/**
 * Auto-generated E2E Test Template
 * Focus: ${focus}
 *
 * 🤖 Generated by: AI Test Generator
 * 📅 Date: ${new Date().toISOString()}
 *
 * 💡 TODO: Ask Cursor/Claude to implement these tests!
 * Example prompt: "Implement these Cypress tests for ${focus}"
 */

describe('${suiteName}', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('should handle basic ${focus.toLowerCase()} flow', () => {
    // TODO: Implement test
    cy.fillBasicInfo('test-001', 'bg-kr-test')
    cy.addUsage(100)
    cy.calculateBilling()
  })

  it('should validate ${focus.toLowerCase()} inputs', () => {
    // TODO: Implement validation test
  })

  it('should handle ${focus.toLowerCase()} edge cases', () => {
    // TODO: Implement edge case test
  })

  it('should integrate ${focus.toLowerCase()} with other features', () => {
    // TODO: Implement integration test
  })
})
`
}

async function saveTestFile(fileName: string, content: string): Promise<void> {
  const outputDir = path.join(process.cwd(), 'cypress', 'e2e', 'generated')
  await fs.mkdir(outputDir, { recursive: true })

  const filePath = path.join(outputDir, `${fileName}.cy.ts`)
  await fs.writeFile(filePath, content, 'utf-8')

  console.log(`✅ Test file saved: ${filePath}`)
}

// ============================================================================
// Predefined Test Suites
// ============================================================================

const TEST_SUITES: Array<{ name: string; focus: string }> = [
  { name: 'usage-management', focus: 'Usage Entry Management' },
  { name: 'credit-handling', focus: 'Credit Application and Validation' },
  { name: 'adjustment-scenarios', focus: 'Discount and Surcharge Adjustments' },
  { name: 'payment-flow', focus: 'Complete Payment Processing' },
  { name: 'history-persistence', focus: 'History Save and Load' },
  { name: 'error-handling', focus: 'Error Scenarios and Validation' },
  { name: 'integration-full', focus: 'Complete End-to-End Integration' },
]

// ============================================================================
// Main Execution Helpers
// ============================================================================

async function generateAllSuites(): Promise<void> {
  console.log('📦 Generating all test suites...\n')

  for (const suite of TEST_SUITES) {
    try {
      const content = await generateTestSuite(suite.name, suite.focus)
      await saveTestFile(suite.name, content)
      console.log('')
    } catch (error) {
      console.error(`❌ Failed to generate ${suite.name}:`,
        error instanceof Error ? error.message : String(error))
    }
  }
}

async function generateSingleSuite(suiteName: string): Promise<void> {
  const suite = TEST_SUITES.find((s) => s.name === suiteName)
  if (!suite) {
    console.error(`❌ Unknown suite: ${suiteName}`)
    return
  }

  const content = await generateTestSuite(suite.name, suite.focus)
  await saveTestFile(suite.name, content)
}

function showUsage(): void {
  console.log('Usage:')
  console.log('  npm run generate:tests -- --all           # Generate all suites')
  console.log('  npm run generate:tests -- suite-name      # Generate specific suite')
  console.log('\nAvailable suites:')
  for (const suite of TEST_SUITES) {
    console.log(`  - ${suite.name}: ${suite.focus}`)
  }
}

// ============================================================================
// Main Execution
// ============================================================================

async function main() {
  console.log('🎯 AI-Powered Cypress Test Generator')
  console.log('=====================================\n')

  const args = process.argv.slice(2)
  const generateAll = args.includes('--all')

  if (generateAll) {
    await generateAllSuites()
  } else {
    const suiteName = args[0]
    if (!suiteName) {
      showUsage()
      return
    }
    await generateSingleSuite(suiteName)
  }

  console.log('\n✨ Done! Run tests with: npm run e2e')
}

try {
  await main()
} catch (error) {
  console.error('❌ Fatal error:', error)
  process.exit(1)
}
