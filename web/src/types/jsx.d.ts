/**
 * Global JSX namespace declaration for React
 * Extends React's built-in JSX types
 */

import type React from 'react'

declare global {
  namespace JSX {
    // Use React's JSX types directly
    interface Element extends React.JSX.Element {}
    interface ElementClass extends React.JSX.ElementClass {}
    interface ElementAttributesProperty extends React.JSX.ElementAttributesProperty {}
    interface ElementChildrenAttribute extends React.JSX.ElementChildrenAttribute {}
    interface IntrinsicElements extends React.JSX.IntrinsicElements {}
    interface IntrinsicAttributes extends React.JSX.IntrinsicAttributes {}
    interface IntrinsicClassAttributes<T> extends React.JSX.IntrinsicClassAttributes<T> {}
    type LibraryManagedAttributes<C, P> = React.JSX.LibraryManagedAttributes<C, P>
  }
}
