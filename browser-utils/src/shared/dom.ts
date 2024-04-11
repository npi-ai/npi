export function getNearestElementOfType<T extends Element>(
  el: Element | null,
  assertFn: (el: Element) => boolean,
): T | null {
  while (el && el !== document.body) {
    if (assertFn(el)) {
      return el as T;
    }

    el = el.parentElement;
  }

  return null;
}

export function getInnerMostElements(
  elements: Iterable<Element>,
): Set<Element> {
  const result = new Set(elements);

  // only keep inner-most elements to reduce noise
  for (const outer of result) {
    for (const inner of result) {
      if (outer !== inner && outer.contains(inner)) {
        result.delete(outer);
      }
    }
  }

  return result;
}

export function getOuterMostElements(
  elements: Iterable<Element>,
): Set<Element> {
  const result = new Set(elements);

  // only keep inner-most elements to grab more details
  for (const outer of result) {
    for (const inner of result) {
      if (outer !== inner && outer.contains(inner)) {
        result.delete(inner);
      }
    }
  }

  return result;
}
