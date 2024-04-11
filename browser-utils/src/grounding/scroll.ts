export function getScrollableParent(el: Element | null) {
  while (el) {
    if (isScrollable(el)) {
      return el;
    }

    el = el.parentElement;
  }

  return null;
}

export function getScrollTop() {
  const doc = document.documentElement;

  return (window.scrollY || doc.scrollTop) - (doc.clientTop || 0);
}

export function isScrollable(el: Element = document.documentElement) {
  const { overflowY } = getComputedStyle(el);

  const canScroll =
    el === document.documentElement ||
    overflowY === 'scroll' ||
    overflowY === 'auto';

  return canScroll && el.scrollTop + el.clientHeight < el.scrollHeight;
}

export function scrollPageDown() {
  const scrollTop = getScrollTop();

  window.scrollTo(window.scrollX, scrollTop + window.innerHeight);
}

export function isScrollablePage() {
  return (
    getScrollableParent(document.body) !== null &&
    Math.ceil(getScrollTop() + window.innerHeight) < getPageHeight()
  );
}

// see: https://stackoverflow.com/a/1147768/2369823
export function getPageHeight() {
  const body = document.body;
  const html = document.documentElement;

  return Math.max(
    body.scrollHeight,
    body.offsetHeight,
    html.clientHeight,
    html.scrollHeight,
    html.offsetHeight,
  );
}
