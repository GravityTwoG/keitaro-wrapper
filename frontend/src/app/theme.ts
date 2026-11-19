import { createTheme } from '@mantine/core';

export const theme = createTheme({
  fontFamily: '"Manrope Variable", "Manrope", system-ui, sans-serif',
  fontFamilyMonospace: '"JetBrains Mono Variable", "JetBrains Mono", monospace',
  primaryColor: 'forest',
  primaryShade: { light: 6, dark: 7 },
  defaultRadius: 'md',
  headings: {
    fontFamily: '"Manrope Variable", "Manrope", system-ui, sans-serif',
    fontWeight: '750',
    sizes: {
      h1: { fontSize: '2rem', lineHeight: '1.15' },
      h2: { fontSize: '1.35rem', lineHeight: '1.25' },
      h3: { fontSize: '1.1rem', lineHeight: '1.3' },
    },
  },
  colors: {
    forest: [
      '#eefbf3',
      '#d7f5e2',
      '#afeac5',
      '#83dda5',
      '#5fd18b',
      '#47c97a',
      '#3ac370',
      '#2cab5c',
      '#22984f',
      '#0f8340',
    ],
  },
  components: {
    Button: {
      defaultProps: { radius: 'md' },
    },
    Card: {
      defaultProps: { radius: 'lg' },
    },
    Paper: {
      defaultProps: { radius: 'lg' },
    },
    Badge: {
      defaultProps: { radius: 'sm' },
    },
    Table: {
      defaultProps: { verticalSpacing: 'sm', horizontalSpacing: 'md' },
    },
  },
});
