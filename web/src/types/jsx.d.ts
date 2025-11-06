/**
 * Global JSX namespace declaration for React 19
 * This resolves the "Cannot find namespace 'JSX'" error
 */

import type * as React from 'react'

declare global {
  namespace JSX {
    // Extend React.JSX types directly to avoid 'any' usage
    interface Element extends React.ReactElement {}
    interface ElementClass extends React.Component {
      render(): React.ReactNode
    }
    interface ElementAttributesProperty {
      props: Record<string, unknown>
    }
    interface ElementChildrenAttribute {
      children: React.ReactNode
    }
    type LibraryManagedAttributes<C, P> = React.JSX.LibraryManagedAttributes<C, P>
    interface IntrinsicAttributes extends React.JSX.IntrinsicAttributes {}
    interface IntrinsicClassAttributes<T> extends React.JSX.IntrinsicClassAttributes<T> {}
    interface IntrinsicElements extends React.JSX.IntrinsicElements {}
  }
}
