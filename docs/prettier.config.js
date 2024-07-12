module.exports = {
  plugins: [
    '@ianvs/prettier-plugin-sort-imports',
    'prettier-plugin-packagejson',
    'prettier-plugin-tailwindcss',
    'prettier-plugin-classnames',
    'prettier-plugin-merge'
  ],
  endingPosition: 'absolute-with-indent',
  tailwindConfig: './tailwind.config.js',
  tailwindFunctions: ['cva', 'cn'],
  customAttributes: ['cn', 'clsx'],
  customFunctions: ['cn', 'clsx'],
  singleQuote: true,
  semi: false,
  trailingComma: 'all',
}
