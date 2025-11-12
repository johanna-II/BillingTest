/**
 * MCP Server for Cypress Control
 * Allows AI agents to control and generate Cypress tests
 *
 * Model Context Protocol (MCP) by Anthropic
 * Enables Claude and other AI models to interact with Cypress
 *
 * Installation:
 * cd cypress/mcp-server && npm install
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js'
import { spawn } from 'node:child_process'
import { promises as fs } from 'node:fs'
import path from 'node:path'

// Type for MCP request
interface MCPRequest {
  params: {
    name: string
    arguments?: Record<string, unknown>
  }
}

// ============================================================================
// MCP Server Setup
// ============================================================================

const server = new Server(
  {
    name: 'cypress-controller',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
)

// ============================================================================
// Available Tools
// ============================================================================

const tools: Tool[] = [
  {
    name: 'run_cypress_tests',
    description: 'Run Cypress E2E tests headlessly and return results',
    inputSchema: {
      type: 'object',
      properties: {
        spec: {
          type: 'string',
          description: 'Specific test file to run (optional, runs all if not specified)',
        },
      },
    },
  },
  {
    name: 'generate_test',
    description: 'Generate a new Cypress test file based on description',
    inputSchema: {
      type: 'object',
      properties: {
        testName: {
          type: 'string',
          description: 'Name of the test file (without .cy.ts)',
        },
        description: {
          type: 'string',
          description: 'Description of what the test should cover',
        },
        scenarios: {
          type: 'array',
          items: { type: 'string' },
          description: 'List of test scenarios to include',
        },
      },
      required: ['testName', 'description', 'scenarios'],
    },
  },
  {
    name: 'read_test_results',
    description: 'Read the latest Cypress test results',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'list_tests',
    description: 'List all available Cypress test files',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
]

// ============================================================================
// Tool Handlers
// ============================================================================

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools }
})

server.setRequestHandler(CallToolRequestSchema, async (request: MCPRequest) => {
  const { name, arguments: args } = request.params

  try {
    switch (name) {
      case 'run_cypress_tests':
        return await handleRunCypressTests(args ?? {})
      case 'generate_test':
        return await handleGenerateTest(args ?? {})
      case 'read_test_results':
        return await handleReadTestResults()
      case 'list_tests':
        return await handleListTests()
      default:
        throw new Error(`Unknown tool: ${name}`)
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    }
  }
})

// ============================================================================
// Tool Handler Functions
// ============================================================================

/**
 * Handle running Cypress tests
 */
async function handleRunCypressTests(args: Record<string, unknown>) {
  const spec = (args as { spec?: string }).spec

  // Validate spec path to prevent command injection
  if (spec) {
    // Check for path traversal attempts
    if (spec.includes('..') || spec.startsWith('/')) {
      throw new Error('Invalid spec path: path traversal not allowed')
    }

    // Check for command injection characters
    const dangerousChars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
    if (dangerousChars.some(char => spec.includes(char))) {
      throw new Error('Invalid spec path: contains forbidden characters')
    }

    // Validate file extension
    if (!spec.endsWith('.cy.ts') && !spec.endsWith('.cy.js')) {
      throw new Error('Invalid spec path: must be a .cy.ts or .cy.js file')
    }
  }

  // Build command args array directly (safer than string concatenation)
  const commandArgs = spec
    ? ['cypress', 'run', '--spec', `cypress/e2e/${spec}`]
    : ['cypress', 'run']

  const result = await runCommandWithArgs('npx', commandArgs)
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(result, null, 2),
      },
    ],
  }
}

/**
 * Handle generating a new test file
 */
async function handleGenerateTest(args: Record<string, unknown>) {
  const { testName, description, scenarios } = args as {
    testName: string
    description: string
    scenarios: string[]
  }

  // Validate testName to prevent path traversal attacks
  if (!testName || typeof testName !== 'string') {
    throw new Error('Invalid testName: must be a non-empty string')
  }

  // Check for path traversal attempts
  if (testName.includes('..') || testName.startsWith('/') || testName.startsWith('\\')) {
    throw new Error('Invalid testName: path traversal not allowed')
  }

  // Check for directory separators (prevent nested paths)
  if (testName.includes('/') || testName.includes('\\')) {
    throw new Error('Invalid testName: directory separators not allowed')
  }

  // Validate filename format (alphanumeric, hyphens, underscores only)
  if (!/^[a-zA-Z0-9_-]+$/.test(testName)) {
    throw new Error('Invalid testName: only alphanumeric characters, hyphens, and underscores allowed')
  }

  // Validate length (prevent extremely long filenames)
  if (testName.length > 100) {
    throw new Error('Invalid testName: maximum length is 100 characters')
  }

  // Validate description to prevent template injection
  if (!description || typeof description !== 'string') {
    throw new Error('Invalid description: must be a non-empty string')
  }

  if (description.length > 500) {
    throw new Error('Invalid description: maximum length is 500 characters')
  }

  // Validate scenarios to prevent template injection
  if (!Array.isArray(scenarios) || scenarios.length === 0) {
    throw new Error('Invalid scenarios: must be a non-empty array')
  }

  if (scenarios.some(s => typeof s !== 'string' || !s.trim())) {
    throw new Error('Invalid scenarios: all items must be non-empty strings')
  }

  if (scenarios.length > 50) {
    throw new Error('Invalid scenarios: maximum 50 scenarios allowed')
  }

  if (scenarios.some(s => s.length > 200)) {
    throw new Error('Invalid scenarios: each scenario maximum length is 200 characters')
  }

  const testContent = generateTestContent(testName, description, scenarios)
  const filePath = path.join(
    process.cwd(),
    'cypress',
    'e2e',
    'generated',
    `${testName}.cy.ts`
  )

  // Ensure directory exists
  await fs.mkdir(path.dirname(filePath), { recursive: true })

  // Write test file
  await fs.writeFile(filePath, testContent, 'utf-8')

  return {
    content: [
      {
        type: 'text',
        text: `✅ Generated test file: ${filePath}\n\n${testContent}`,
      },
    ],
  }
}

/**
 * Handle reading test results
 */
async function handleReadTestResults() {
  const resultsPath = path.join(
    process.cwd(),
    'cypress',
    'results',
    'results.json'
  )

  try {
    const results = await fs.readFile(resultsPath, 'utf-8')
    return {
      content: [
        {
          type: 'text',
          text: results,
        },
      ],
    }
  } catch {
    // Gracefully handle missing file - this is expected when tests haven't run yet
    return {
      content: [
        {
          type: 'text',
          text: `No test results found. Run tests first.\n\nExpected location: ${resultsPath}`,
        },
      ],
    }
  }
}

/**
 * Handle listing all test files
 */
async function handleListTests() {
  const testsDir = path.join(process.cwd(), 'cypress', 'e2e')
  const files = await listCypressFiles(testsDir)

  return {
    content: [
      {
        type: 'text',
        text: `Available Cypress tests:\n${files.join('\n')}`,
      },
    ],
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Run command with arguments array (secure, no shell injection risk)
 * This is the preferred method for executing commands
 *
 * @param executable - The executable to run (e.g., 'npx', 'npm', 'node')
 * @param args - Array of arguments to pass to the executable
 * @returns Promise with stdout and stderr
 */
async function runCommandWithArgs(
  executable: string,
  args: string[]
): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    // Security: Only allow specific whitelisted commands
    const allowedCommands = ['npx', 'npm', 'node']
    if (!allowedCommands.includes(executable)) {
      reject(new Error(`Command not allowed: ${executable}`))
      return
    }

    // Execute without shell for security (prevents command injection)
    const child = spawn(executable, args, {
      cwd: process.cwd(),
      shell: false, // Security: Prevent shell injection
    })

    let stdout = ''
    let stderr = ''

    child.stdout?.on('data', (data) => {
      stdout += data.toString()
    })

    child.stderr?.on('data', (data) => {
      stderr += data.toString()
    })

    child.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr })
      } else {
        reject(new Error(`Command failed with code ${code}: ${stderr}`))
      }
    })
  })
}

async function listCypressFiles(dir: string): Promise<string[]> {
  const files: string[] = []

  async function walk(currentPath: string) {
    const entries = await fs.readdir(currentPath, { withFileTypes: true })

    for (const entry of entries) {
      const fullPath = path.join(currentPath, entry.name)

      if (entry.isDirectory()) {
        await walk(fullPath)
      } else if (entry.name.endsWith('.cy.ts') || entry.name.endsWith('.cy.js')) {
        files.push(path.relative(dir, fullPath))
      }
    }
  }

  await walk(dir)
  return files
}

/**
 * Escape string for safe use in JavaScript/TypeScript string literals
 * Prevents template injection by escaping quotes and special characters
 */
function escapeForTemplate(str: string): string {
  const backslash = '\\'
  const escapedBackslash = backslash + backslash

  return str
    .replaceAll(backslash, escapedBackslash)    // Backslash
    .replaceAll("'", backslash + "'")           // Single quote
    .replaceAll('"', backslash + '"')           // Double quote
    .replaceAll('`', backslash + '`')           // Backtick
    .replaceAll('\n', backslash + 'n')          // Newline
    .replaceAll('\r', backslash + 'r')          // Carriage return
    .replaceAll('\t', backslash + 't')          // Tab
}

function generateTestContent(
  testName: string,
  description: string,
  scenarios: string[]
): string {
  // Escape all user-provided content to prevent template injection
  const safeDescription = escapeForTemplate(description)
  const safeTestName = escapeForTemplate(testName)

  const scenarioTests = scenarios
    .map((scenario) => {
      const safeScenario = escapeForTemplate(scenario)
      return `
  it('${safeScenario}', () => {
    // TODO: Implement test for: ${safeScenario}
    cy.log('Testing: ${safeScenario}')
  })`
    })
    .join('\n')

  return `/**
 * Auto-generated E2E Test
 * ${safeDescription}
 *
 * Generated by: MCP Cypress Server
 * Date: ${new Date().toISOString()}
 */

describe('${safeTestName}', () => {
  beforeEach(() => {
    cy.visit('/')
  })
${scenarioTests}
})
`
}

// ============================================================================
// Server Startup
// ============================================================================

const transport = new StdioServerTransport()
await server.connect(transport)

// Note: console.error writes to stderr, which is the correct channel for
// MCP server diagnostics (stdout is reserved for MCP protocol messages)
console.error('🚀 Cypress MCP Server running on stdio')
