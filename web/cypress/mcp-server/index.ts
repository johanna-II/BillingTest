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
      case 'run_cypress_tests': {
        const spec = (args as { spec?: string }).spec
        const command = spec
          ? `npx cypress run --spec "cypress/e2e/${spec}"`
          : 'npx cypress run'

        const result = await runCommand(command)
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        }
      }

      case 'generate_test': {
        const { testName, description, scenarios } = args as {
          testName: string
          description: string
          scenarios: string[]
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

      case 'read_test_results': {
        // Read latest test results from Cypress reports
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
        } catch (error) {
          // Log error for debugging
          console.error('Failed to read test results:', error instanceof Error ? error.message : String(error))

          return {
            content: [
              {
                type: 'text',
                text: 'No test results found. Run tests first.',
              },
            ],
          }
        }
      }

      case 'list_tests': {
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
// Helper Functions
// ============================================================================

async function runCommand(command: string): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    // Parse command safely - avoid shell injection
    const parts = command.split(' ')
    const executable = parts[0]
    const args = parts.slice(1)

    // Security: Only allow specific whitelisted commands
    const allowedCommands = ['npx', 'npm', 'node']
    if (!allowedCommands.includes(executable)) {
      reject(new Error(`Command not allowed: ${executable}`))
      return
    }

    // Execute without shell for security
    const child = spawn(executable, args, {
      cwd: process.cwd(),
      shell: false,  // Security: Prevent shell injection
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

function generateTestContent(
  testName: string,
  description: string,
  scenarios: string[]
): string {
  const scenarioTests = scenarios
    .map(
      (scenario) => `
  it('${scenario}', () => {
    // TODO: Implement test for: ${scenario}
    cy.log('Testing: ${scenario}')
  })`
    )
    .join('\n')

  return `/**
 * Auto-generated E2E Test
 * ${description}
 *
 * Generated by: MCP Cypress Server
 * Date: ${new Date().toISOString()}
 */

describe('${testName}', () => {
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
console.error('🚀 Cypress MCP Server running on stdio')
