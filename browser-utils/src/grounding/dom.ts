import {
  isDisabled,
  isInaccessible,
  computeAccessibleName,
  computeAccessibleDescription,
} from 'dom-accessibility-api';
import { getScrollableParent } from './scroll';
import { markerAttr, defaultSelector } from './constants';
import { getNearestElementOfType, getInnerMostElements } from '../shared';

export function isContenteditable(el: Element) {
  const editable = el.getAttribute('contenteditable');

  return (
    editable === '' || editable === 'true' || editable === 'plaintext-only'
  );
}

export function hasA11yInfo(el: Element) {
  return !!(computeAccessibleName(el) || computeAccessibleDescription(el));
}

export async function getClickableElements(): Promise<Set<Element>> {
  const result = new Set<Element>();

  const elements = document.querySelectorAll('*');

  for (const el of elements) {
    if (result.has(el)) {
      continue;
    }

    const styles = getComputedStyle(el);

    if (
      // el instanceof HTMLElement &&
      styles.cursor === 'pointer' &&
      styles.pointerEvents !== 'none' &&
      hasA11yInfo(el)
    ) {
      result.add(
        el instanceof SVGElement
          ? getNearestElementOfType<SVGElement>(
              el,
              el => el.tagName === 'svg',
            ) || el
          : el,
      );
    }
  }

  return result;
}

export function isFormComponent(
  el: Element,
): el is
  | HTMLInputElement
  | HTMLTextAreaElement
  | HTMLSelectElement
  | HTMLOptionElement {
  const { tagName } = el;

  return (
    tagName === 'INPUT' ||
    tagName === 'TEXTAREA' ||
    tagName === 'SELECT' ||
    tagName === 'OPTION'
  );
}

// check if the element is visible for user
// i.e., not fully overlapped by other elements
export function isVisibleForUser(el: Element) {
  const rects = el.getClientRects();
  const slices = 4;

  for (const rect of rects) {
    // select 5 points ([0, 0.25, 0.5, 0.75, 1]) along the diagonal line to
    // check if the point is covered by other element
    for (let i = 0; i <= slices; i++) {
      const x = rect.left + (rect.width * i) / slices;
      const y = rect.top + (rect.height * i) / slices;
      const topEl = document.elementFromPoint(x, y);

      if (el.contains(topEl)) {
        return true;
      }
    }
  }

  return false;
}

export async function getInteractiveElements(selector = defaultSelector) {
  const { innerWidth, innerHeight } = window;

  // use inner-most elements to reduce noise
  const clickableElements = getInnerMostElements(await getClickableElements());
  // TODO: not necessary to get inner-most elements for selector matches?
  const baseElements = new Set(
    [...document.querySelectorAll(selector)].filter(el => {
      // preserve <summary />
      if (el.tagName === 'SUMMARY') {
        return true;
      }

      // remove elements inside a closed <details />
      const detailsEl = getNearestElementOfType<HTMLDetailsElement>(
        el,
        el => el.tagName === 'DETAILS',
      );
      return !detailsEl || detailsEl.open;
    }),
  );

  // use inner-most elements if they are the only children of their parents
  for (const el of baseElements) {
    if (el.children.length === 1 && baseElements.has(el.firstElementChild!)) {
      baseElements.delete(el);
    }
  }

  // remove the clickable element if it is a parent or a child of a base element to reduce noise
  for (const el of baseElements) {
    for (const clickable of clickableElements) {
      if (clickable.contains(el) || el.contains(clickable)) {
        clickableElements.delete(clickable);
      }
    }
  }

  const targets = [...new Set([...baseElements, ...clickableElements])]
    .filter(el => !isDisabled(el) && !isInaccessible(el))
    .filter(el => {
      // TODO: configurable rules
      // preserve monaco editor's textarea
      if (el.matches('textarea.monaco-mouse-cursor-text')) {
        return true;
      }

      // visibility check
      const bounding = el.getBoundingClientRect();

      if (bounding.width === 0 || bounding.height === 0) {
        return false;
      }

      const scrollableParent = getScrollableParent(el);

      // keep elements inside a scrollable container except the documentElement
      if (
        scrollableParent &&
        scrollableParent !== document.documentElement &&
        scrollableParent !== document.body
      ) {
        return true;
      }

      // keep viewport-visible elements only
      const isInsideViewport =
        bounding.top < innerHeight &&
        bounding.bottom > 0 &&
        bounding.left < innerWidth &&
        bounding.right > 0;

      if (!isInsideViewport) {
        return false;
      }

      return isVisibleForUser(el);
    })
    .map((el, i) => {
      el.setAttribute(markerAttr, i.toString());
      return el;
    });

  return targets;
}
