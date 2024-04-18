import {
  getRole,
  computeAccessibleName,
  computeAccessibleDescription,
} from 'dom-accessibility-api';

import {
  defaultSelector,
  markerAttr,
  attrsToKeepRegex,
  getInteractiveElements,
  markElement,
  addBboxes,
  clearBboxes,
  getPageBrightness,
  isFormComponent,
  scrollPageDown,
  isContenteditable,
  isScrollablePage,
} from './grounding';

import {
  Observer,
  syntheticClick,
  syntheticEnter,
  syntheticInput,
  syntheticInputOnContenteditable,
} from './execution';

export type ElementJSON = {
  id: string;
  tag: string;
  role: string | null;
  accessibleName: string;
  accessibleDescription: string;
  attributes: Record<string, string>;
  options?: string[];
};

export class BrowserUtils {
  #prevElements: Element[] = [];
  #observer: Observer | null = null;

  constructor(readonly selector: string = defaultSelector) {}

  getElement(id: string): HTMLElement {
    const el = this.#prevElements.at(Number(id));

    if (el?.isConnected) {
      return el as HTMLElement;
    }

    return document.querySelector(`[data-marker-id="${id}"]`) as HTMLElement;
  }

  async addBboxes() {
    const interactiveElements = await getInteractiveElements(this.selector);
    addBboxes(interactiveElements);
  }

  clearBboxes() {
    clearBboxes();
  }

  elementToJSON(el: Element) {
    const elemJSON: ElementJSON = {
      id: el.getAttribute(markerAttr) || '',
      tag: el.tagName.toLowerCase(),
      role: getRole(el),
      accessibleName: computeAccessibleName(el),
      accessibleDescription: computeAccessibleDescription(el),
      attributes: {},
    };

    if (el.tagName === 'SELECT') {
      elemJSON.options = [...el.querySelectorAll('option')].map(
        opt => (opt as HTMLOptionElement).value,
      );
    }

    for (const attr of [...el.attributes]) {
      if (attrsToKeepRegex.test(attr.name)) {
        elemJSON.attributes[attr.name] = attr.value;
      }
    }

    if (isFormComponent(el)) {
      const value = el.value;

      if (value && el.getAttribute('type') !== 'password') {
        elemJSON.attributes.value = value;
      }
    }

    // shorten url
    const href = el.getAttribute('href');

    if (href) {
      if (!elemJSON.accessibleName && !elemJSON.accessibleDescription) {
        elemJSON.attributes.href = href.slice(0, 100);
      } else {
        delete elemJSON.attributes.href;
      }
    }

    return elemJSON;
  }

  async snapshot(screenshot?: string) {
    this.clearBboxes();

    const addedIDs = new Set<string>();
    const prevElemSet = new Set(this.#prevElements);

    const interactiveElements = await getInteractiveElements(this.selector);
    const pageBrightness = await getPageBrightness(screenshot);

    const elementsAsJSON: ElementJSON[] = interactiveElements.map((el, i) => {
      markElement(el, i, pageBrightness);

      const markerId = el.getAttribute(markerAttr);

      if (markerId === null) {
        throw new Error(`Unable to find markerId for element: ${el.outerHTML}`);
      }

      if (!prevElemSet.has(el)) {
        addedIDs.add(markerId);
      }

      return this.elementToJSON(el);
    });

    this.#prevElements = interactiveElements;

    return {
      interactiveElements,
      elementsAsJSON,
      addedIDs: [...addedIDs],
    };
  }

  initObserver(maxTimeout?: number) {
    this.#observer = new Observer(maxTimeout);
  }

  isScrollable() {
    return isScrollablePage();
  }

  async stable() {
    await this.#observer?.domStable();
  }

  async scrollPageDown() {
    return scrollPageDown();
  }

  async click(el: HTMLElement) {
    return syntheticClick(el);
  }

  async fill(el: HTMLElement, value: string) {
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      return syntheticInput(el, value);
    }

    if (isContenteditable(el)) {
      return syntheticInputOnContenteditable(el, value);
    }

    throw new Error('Unable to fill in a non-form element');
  }

  async select(el: HTMLElement, value: string) {
    if (!(el instanceof HTMLSelectElement)) {
      throw new Error('Unable to select a non-select element');
    }

    return syntheticInput(el, value);
  }

  async enter(el: HTMLElement) {
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      return syntheticEnter(el);
    }

    throw new Error('Unable to press enter on a non-form element');
  }
}
