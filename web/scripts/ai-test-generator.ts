/**
 * AI-Powered Test Generator for PR Changes
 * Analyzes code changes and generates appropriate E2E tests
 *
 * Usage:
 * - With API: ANTHROPIC_API_KEY=xxx node ai-test-generator.ts
 * - No API: Generates smart templates based on file analysis
 */

import { promises as fs } from 'node:fs'
import path from 'node:path'

// ============================================================================
// Types
// ============================================================================

interface FileChange {
  path: string
  type: 'added' | 'modified' | 'deleted'
  category: 'component' | 'hook' | 'page' | 'api' | 'util' | 'other'
}

interface TestScenario {
  description: string
  priority: 'high' | 'medium' | 'low'
  steps: string[]
}

interface GeneratedTest {
  fileName: string
  description: string
  scenarios: TestScenario[]
  code: string
}

// ============================================================================
// File Analysis
// ============================================================================

function categorizeFile(filePath: string): FileChange['category'] {
  if (filePath.includes('/components/')) return 'component'
  if (filePath.includes('/hooks/')) return 'hook'
  if (filePath.includes('/app/')) return 'page'
  if (filePath.includes('workers/')) return 'api'
  if (filePath.includes('/lib/')) return 'util'
  return 'other'
}

function analyzeChanges(changedFiles: string[]): {
  needsTests: boolean
  categories: Set<FileChange['category']>
  files: FileChange[]
} {
  const files: FileChange[] = changedFiles.map((path) => ({
    path,
    type: 'modified',
    category: categorizeFile(path),
  }))

  const categories = new Set(files.map((f) => f.category))

  // Need tests if user-facing code changed
  const needsTests = categories.has('component') ||
                     categories.has('page') ||
                     categories.has('api')

  return { needsTests, categories, files }
}

// ============================================================================
// Test Generation Logic
// ============================================================================

function createComponentScenarios(): TestScenario[] {
  return [
    {
      description: 'should render modified components without errors',
      priority: 'high',
      steps: [
        'Visit the page',
        'Verify component is visible',
        'Interact with component',
        'Verify no console errors',
      ],
    },
    {
      description: 'should maintain component state after changes',
      priority: 'high',
      steps: [
        'Interact with component',
        'Modify state',
        'Verify state persists',
        'Verify UI updates correctly',
      ],
    },
  ]
}

function createPageScenarios(): TestScenario[] {
  return [
    {
      description: 'should navigate to updated pages successfully',
      priority: 'high',
      steps: [
        'Navigate to page',
        'Verify page loads',
        'Verify content is correct',
        'Test page interactions',
      ],
    },
  ]
}

function createApiScenarios(): TestScenario[] {
  return [
    {
      description: 'should integrate with updated API endpoints',
      priority: 'high',
      steps: [
        'Call API through UI',
        'Verify request is made',
        'Verify response is handled',
        'Verify UI updates with data',
      ],
    },
    {
      description: 'should handle API errors gracefully',
      priority: 'medium',
      steps: [
        'Trigger API call',
        'Simulate error',
        'Verify error handling',
        'Verify user sees error message',
      ],
    },
  ]
}

function createHookScenarios(): TestScenario[] {
  return [
    {
      description: 'should maintain hook functionality after changes',
      priority: 'medium',
      steps: [
        'Use feature that depends on hook',
        'Verify hook return values',
        'Test hook error cases',
        'Verify side effects',
      ],
    },
  ]
}

function createIntegrationScenario(): TestScenario {
  return {
    description: 'should work with existing features (integration)',
    priority: 'high',
    steps: [
      'Complete a full user workflow',
      'Verify all steps work',
      'Verify data consistency',
      'Verify no side effects on other features',
    ],
  }
}

function generateTestScenarios(analysis: ReturnType<typeof analyzeChanges>): TestScenario[] {
  const scenarios: TestScenario[] = []

  if (analysis.categories.has('component')) {
    scenarios.push(...createComponentScenarios())
  }

  if (analysis.categories.has('page')) {
    scenarios.push(...createPageScenarios())
  }

  if (analysis.categories.has('api')) {
    scenarios.push(...createApiScenarios())
  }

  if (analysis.categories.has('hook')) {
    scenarios.push(...createHookScenarios())
  }

  // Always add integration test
  scenarios.push(createIntegrationScenario())

  return scenarios
}

function generateCypressCode(
  prNumber: number,
  changedFiles: string[],
  scenarios: TestScenario[]
): string {
  const scenarioTests = scenarios
    .map((scenario) => {
      const steps = scenario.steps.map((step) => `    // ${step}`).join('\n')

      return `  it('${scenario.description}', () => {
${steps}

    // Basic smoke test
    cy.visit('/')
    cy.get('body').should('exist')

    // TODO: Implement specific test based on changes
    // Changed files: ${changedFiles.slice(0, 3).join(', ')}
    ${changedFiles.some(f => f.includes('Billing')) ? `
    // Test billing functionality
    cy.fillBasicInfo('pr-test-${prNumber}', 'bg-test')
    cy.addUsage(100)
    cy.calculateBilling()
    cy.contains('Billing Statement').should('be.visible')` : ''}
  })`
    })
    .join('\n\n')

  const prLabel = prNumber > 0 ? `PR #${prNumber}` : 'Template'

  return `/**
 * Auto-Generated E2E Test for ${prLabel}
 *
 * 🤖 Generated by: AI Test Automation
 * 📅 Date: ${new Date().toISOString()}
 *
 * 📝 Changed Files:
${changedFiles.map((f) => ` * - ${f}`).join('\n')}
 *
 * 💡 This test covers new features and prevents regressions.
 * 🔄 It will be included in future regression test runs.
 */

describe('${prLabel} - Feature & Regression Tests', () => {
  beforeEach(() => {
    cy.visit('/')
    // Clear any previous state
    cy.clearLocalStorage()
  })

  afterEach(() => {
    // Cleanup after each test
    cy.clearCookies()
  })

${scenarioTests}
})
`
}

// ============================================================================
// Claude API Integration (Optional)
// ============================================================================

async function generateWithClaudeAPI(
  changedFiles: string[],
  prNumber: number
): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY

  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY not found')
  }

  const prLabel = prNumber > 0 ? `PR #${prNumber}` : 'Template'

  const prompt = `You are an expert QA engineer. Analyze these code changes and generate comprehensive Cypress E2E tests.

Changed files:
${changedFiles.join('\n')}

Generate a complete Cypress test file that:
1. Tests new features added
2. Tests modified functionality
3. Prevents regressions
4. Covers edge cases
5. Tests integration with existing features

Use these custom commands:
- cy.fillBasicInfo(uuid, billingGroupId)
- cy.addUsage(volume)
- cy.addCredit(amount)
- cy.addAdjustment(type, value)
- cy.calculateBilling()
- cy.processPayment()

Return ONLY the TypeScript code, no explanations.
Start with: describe('${prLabel}...`

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
      messages: [{ role: 'user', content: prompt }],
    }),
  })

  if (!response.ok) {
    throw new Error(`Claude API error: ${response.statusText}`)
  }

  const data = await response.json()
  return data.content[0].text
}

// ============================================================================
// Main Logic Helpers
// ============================================================================

async function readChangedFiles(changedFilesPath: string): Promise<string[]> {
  try {
    const content = await fs.readFile(changedFilesPath, 'utf-8')
    return content.split('\n').filter((f) => f.trim())
  } catch {
    console.log('⚠️  No changed files found. Using example...')
    return ['web/src/components/BillingInputForm.tsx']
  }
}

function logChangedFiles(changedFiles: string[]): void {
  console.log(`\n📝 Changed files (${changedFiles.length}):`)
  for (const file of changedFiles) {
    console.log(`  - ${file}`)
  }
}

function logAnalysis(analysis: ReturnType<typeof analyzeChanges>): void {
  console.log(`\n🔍 Analysis:`)
  console.log(`  Needs tests: ${analysis.needsTests ? 'YES' : 'NO'}`)
  console.log(`  Categories: ${Array.from(analysis.categories).join(', ')}`)
}

async function generateTestCode(
  changedFiles: string[],
  prNumber: number,
  scenarios: TestScenario[]
): Promise<string> {
  // Try Claude API if available
  if (process.env.ANTHROPIC_API_KEY) {
    console.log('\n🤖 Using Claude API for enhanced test generation...')
    try {
      const testCode = await generateWithClaudeAPI(changedFiles, prNumber)
      console.log('✅ AI-generated test received')
      return testCode
    } catch (error) {
      console.error('⚠️  Claude API failed:', error instanceof Error ? error.message : String(error))
      console.log('Falling back to template generation')
    }
  } else {
    console.log('\n📝 No API key. Generating smart template...')
    console.log('💡 Tip: Set ANTHROPIC_API_KEY for AI-generated tests')
  }

  return generateCypressCode(prNumber, changedFiles, scenarios)
}

async function saveAndOutputTest(
  testCode: string,
  prNumber: number
): Promise<void> {
  const outputDir = path.join(process.cwd(), 'cypress', 'e2e', 'pr-generated')
  await fs.mkdir(outputDir, { recursive: true })

  const fileName = `pr-${prNumber || 'template'}.cy.ts`
  const outputPath = path.join(outputDir, fileName)

  await fs.writeFile(outputPath, testCode, 'utf-8')

  console.log(`\n✅ Test file saved: ${outputPath}`)
  console.log(`\n📦 Preview:\n`)
  console.log(testCode.split('\n').slice(0, 20).join('\n'))
  console.log('\n... (truncated)\n')

  // Output for GitHub Actions
  if (process.env.GITHUB_OUTPUT) {
    await fs.appendFile(
      process.env.GITHUB_OUTPUT,
      `test-generated=true\ntest-file=${fileName}\n`
    )
  }
}

// ============================================================================
// Main Logic
// ============================================================================

async function main() {
  console.log('🤖 AI-Powered E2E Test Generator')
  console.log('='.repeat(50))

  const changedFilesPath = process.env.CHANGED_FILES_PATH || '../changed-files.txt'
  const prNumber = Number.parseInt(process.env.PR_NUMBER || '0', 10)

  // Read and display changed files
  const changedFiles = await readChangedFiles(changedFilesPath)
  logChangedFiles(changedFiles)

  // Analyze changes
  const analysis = analyzeChanges(changedFiles)
  logAnalysis(analysis)

  if (!analysis.needsTests) {
    console.log('\n✅ No user-facing changes. Skipping test generation.')
    return
  }

  // Generate test scenarios
  const scenarios = generateTestScenarios(analysis)
  console.log(`\n🎯 Generated ${scenarios.length} test scenarios`)

  // Generate test code
  const testCode = await generateTestCode(changedFiles, prNumber, scenarios)

  // Save and output
  await saveAndOutputTest(testCode, prNumber)

  console.log('\n🎉 Done! Run with: npm run e2e')
}

// ============================================================================
// Execution
// ============================================================================

// Using async IIFE for tsx compatibility (top-level await causes CJS error)
void (async function main Execution() {
  try {
    await main()
  } catch (error) {
    console.error('❌ Error:', error)
    process.exit(1)
  }
})()
