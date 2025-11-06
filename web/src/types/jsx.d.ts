/**
 * Global JSX namespace declaration for React
 * Required for TypeScript to understand JSX syntax
 */

import 'react'

declare global {
  namespace JSX {
    // Extend React's JSX namespace
    interface IntrinsicElements extends React.JSX.IntrinsicElements {}
  }
}
