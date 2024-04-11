import { delay } from '../shared';
import { getNearestElementOfType } from '../shared';

function setValue(
  el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
  value: string,
) {
  // eslint-disable-next-line no-case-declarations
  const proto = Object.getPrototypeOf(el);
  // eslint-disable-next-line no-case-declarations
  const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;

  if (setter) {
    // workaround for react
    setter.call(el, value);
  } else {
    el.value = value;
  }
}

function focusInputElement(el: HTMLElement) {
  el.click();
  el.focus();

  // emit a focusin event so that the focus status can be correctly handled
  el.dispatchEvent(
    new Event('focusin', {
      bubbles: true,
    }),
  );
}

export async function syntheticClick(el: Element) {
  const bounding = el.getBoundingClientRect();
  const mouseEventInitial = {
    bubbles: true,
    which: 1,
    clientX: bounding.x + bounding.width / 2,
    clientY: bounding.y + bounding.height / 2,
  };

  el.dispatchEvent(new MouseEvent('mousedown', mouseEventInitial));
  el.dispatchEvent(new PointerEvent('pointerdown', mouseEventInitial));

  if (el instanceof HTMLElement) {
    el.click();
  } else {
    el.dispatchEvent(new MouseEvent('click', mouseEventInitial));
  }

  el.dispatchEvent(new MouseEvent('mouseup', mouseEventInitial));
  el.dispatchEvent(new PointerEvent('pointerup', mouseEventInitial));
}

export async function syntheticInput(
  el: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement,
  value: string,
) {
  setValue(el, value);

  focusInputElement(el);
  await delay(300);

  // NOTE: set value again to ensure the input is not cleared after being focused (occurs in some combobox components)
  setValue(el, value);

  el.dispatchEvent(
    new Event('input', {
      bubbles: true,
    }),
  );

  el.dispatchEvent(
    new Event('change', {
      bubbles: true,
    }),
  );

  // TODO: unnecessary to blur out?
  // if (el.role !== 'combobox') {
  //   el.blur();
  // }
}

export async function syntheticInputOnContenteditable(
  el: HTMLElement,
  value: string,
) {
  focusInputElement(el);
  await delay(300);

  // clear exiting content
  const selection = window.getSelection();
  selection?.removeAllRanges();

  const range = document.createRange();
  range.selectNodeContents(el);

  selection?.addRange(range);
  document.execCommand('delete');

  await delay(300);

  // insert new content
  document.execCommand('insertText', false, value);
}

export async function syntheticEnter(
  el: HTMLInputElement | HTMLTextAreaElement,
) {
  const form = getNearestElementOfType<HTMLFormElement>(
    el,
    el => el.tagName === 'FORM',
  );

  if (form) {
    if (form.requestSubmit) {
      form.requestSubmit();
    } else {
      form.submit();
    }
  }

  focusInputElement(el);
  await delay(300);

  const keyboardEventInitial = {
    key: 'Enter',
    code: 'Enter',
    keyCode: 13,
    charCode: 13,
    bubbles: true,
  };

  el.dispatchEvent(new KeyboardEvent('keydown', keyboardEventInitial));
  el.dispatchEvent(new KeyboardEvent('keyup', keyboardEventInitial));
  el.dispatchEvent(new KeyboardEvent('keypress', keyboardEventInitial));
}
