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

  async snapshot(screenshot?: string) {
    clearBboxes();

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

      const elemJSON: ElementJSON = {
        id: markerId,
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
        }
      }

      if (!prevElemSet.has(el)) {
        addedIDs.add(markerId);
      }

      return elemJSON;
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

  async click(id: string) {
    const el = this.getElement(id);
    return syntheticClick(el);
  }

  async fill(id: string, value: string) {
    const el = this.getElement(id);

    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      return syntheticInput(el, value);
    }

    if (isContenteditable(el)) {
      return syntheticInputOnContenteditable(el, value);
    }

    throw new Error('Unable to fill in a non-form element');
  }

  async select(id: string, value: string) {
    const el = this.getElement(id);

    if (!(el instanceof HTMLSelectElement)) {
      throw new Error('Unable to select a non-select element');
    }

    return syntheticInput(el, value);
  }

  async enter(id: string) {
    const el = this.getElement(id);

    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      return syntheticEnter(el);
    }

    throw new Error('Unable to press enter on a non-form element');
  }
}
