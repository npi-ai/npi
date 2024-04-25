import React from 'react';
import { DocsThemeConfig } from 'nextra-theme-docs';

const config: DocsThemeConfig = {
  logo: <span>NPi AI</span>,
  project: {
    link: 'https://github.com/npi-ai/npi',
  },
  chat: {
    link: 'https://discord.gg/4tyWuHpu',
  },
  docsRepositoryBase: 'https://github.com/npi-ai/npi',
  footer: {
    text: `NPI AI @ ${new Date().getFullYear()}`,
  },
  editLink: {
    text: 'Edit this page on GitHub →',
  },
  toc: {
    backToTop: true,
  },
  useNextSeoProps() {
    return {
      titleTemplate: '%s – NPi',
    };
  },
};

export default config;
