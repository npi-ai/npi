import React from 'react';
import { DocsThemeConfig } from 'nextra-theme-docs';

const config: DocsThemeConfig = {
  logo: <span>NPi AI</span>,
  project: {
    link: 'https://github.com/npi-ai/npi',
  },
  chat: {
    link: 'https://discord.com',
  },
  docsRepositoryBase: 'https://github.com/npi-ai/npi',
  footer: {
    text: `NPI AI @ ${new Date().getFullYear()}`,
  },
};

export default config;
