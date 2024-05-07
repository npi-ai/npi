import React from 'react';
import { DocsThemeConfig } from 'nextra-theme-docs';

const config: DocsThemeConfig = {
  logo: <span>NPi AI</span>,
  logoLink: 'https://www.npi.ai',
  project: {
    link: 'https://github.com/npi-ai/npi',
  },
  chat: {
    link: 'https://discord.gg/VvSnx7z26c',
  },
  docsRepositoryBase: 'https://github.com/npi-ai/npi',
  footer: {
    text: `NPi AI @ ${new Date().getFullYear()}`,
  },
  sidebar: {
    toggleButton: true
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
