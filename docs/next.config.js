const { remarkCodeHike } = require("@code-hike/mdx")

const withNextra = require('nextra')({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
  defaultShowCopyCode: true,
  mdxOptions: {
    remarkPlugins: [
      [
        remarkCodeHike,
        {
          theme: 'one-dark-pro'
        },
      ]
    ],
  },
});

module.exports = withNextra({
  basePath: '/docs',
  async redirects() {
    return [
      {
        source: '/:match((?!docs).*)',
        destination: '/docs/:match*',
        permanent: true,
        basePath: false
      }
    ]
  }
});
