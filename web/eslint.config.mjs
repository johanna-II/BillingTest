import nextPlugin from 'eslint-config-next'

const config = [
  {
    ignores: [
      '.next/**',
      'node_modules/**',
      'out/**',
      '.turbo/**',
    ],
  },
  ...nextPlugin,
  {
    rules: {
      'react-hooks/exhaustive-deps': 'warn',
      'react/no-unescaped-entities': 'off',
    },
  },
]

export default config
