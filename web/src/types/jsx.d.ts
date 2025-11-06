/**
 * Global JSX namespace declaration for React
 * Required for TypeScript to understand JSX syntax
 */

import type React from 'react'

declare global {
  namespace JSX {
    // Core JSX types from React
    interface Element extends React.ReactElement<unknown, unknown> {}
    interface ElementClass extends React.Component<unknown> {
      render(): React.ReactNode
    }
    interface ElementAttributesProperty {
      props: Record<string, unknown>
    }
    interface ElementChildrenAttribute {
      children: React.ReactNode
    }

    // Intrinsic elements (HTML tags)
    interface IntrinsicElements extends React.JSX.IntrinsicElements {}

    // Type utilities
    interface IntrinsicAttributes extends React.JSX.IntrinsicAttributes {}
    interface IntrinsicClassAttributes<T> extends React.JSX.IntrinsicClassAttributes<T> {}
    type LibraryManagedAttributes<C, P> = React.JSX.LibraryManagedAttributes<C, P>
  }
}
