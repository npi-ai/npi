import { BrowserUtils } from './browser-utils';

// expose BrowserUtils to window
declare global {
  interface Window {
    BrowserUtils: typeof BrowserUtils;
  }
}

window.BrowserUtils = BrowserUtils;
