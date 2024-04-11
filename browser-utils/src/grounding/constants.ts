export const attrsToKeepRegex =
  /value|type|href|title|alt|aria-(?!label|labelledby|description|describedby)|placeholder|disabled/;

export const a11yAttrs = [
  'aria-label',
  'aria-description',
  'alt',
  'title',
  'value',
  'placeholder',
];

export const a11ySelectors = a11yAttrs.map(attr => `[${attr}]`).join(',');

export const markerAttr = 'data-marker-id';

export const bboxClassName = 'lc-marker';

// @see: https://github.com/philc/vimium/blob/master/content_scripts/link_hints.js#L1118
export const defaultSelector =
  'a, button, input, textarea, summary, select, [role="button"], [role="tab"], [role="link"], [role="checkbox"], [role="menuitem"], [role="menuitemcheckbox"], [role="menuitemradio"], [role="radio"], [role="combobox"], [role="option"], [role="searchbox"], [role="textbox"], [contenteditable]';
