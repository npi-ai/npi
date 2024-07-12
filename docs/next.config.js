const withNextra = require('nextra')({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
  defaultShowCopyCode: true,
})

module.exports = withNextra({
  async redirects() {
    return [
      {
        source: '/docs/examples',
        destination: '/examples',
        permanent: true,
      },
    ]
  },
})
