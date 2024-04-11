import { getPageBrightness, isDark, randomBrightness } from './screenshot';
import { getScrollTop } from './scroll';
import { bboxClassName, markerAttr } from './constants';

function getZindex(el: Element | null) {
  let zIndex = -Infinity;

  while (el && el !== document.body) {
    const z = parseInt(window.getComputedStyle(el).zIndex, 10);

    if (z > zIndex) {
      zIndex = z;
    }

    el = el.parentElement;
  }

  return isFinite(zIndex) ? zIndex.toString() : 'auto';
}

export function markElement(el: Element, id: number, pageBrightness: number) {
  const scrollTop = getScrollTop();
  const rects = el.getClientRects();

  const brightness = randomBrightness(pageBrightness);
  const bgColor = `hsl(${(Math.random() * 360) | 0}, ${
    (Math.random() * 100) | 0
  }%, ${brightness}%)`;
  const textColor = isDark(pageBrightness) ? '#000' : '#fff';
  // const bgColor = 'red';
  // const textColor = '#fff';
  const zIndex = getZindex(el);

  for (const rect of rects) {
    if (rect.width === 0 || rect.height === 0) {
      continue;
    }

    const marker = document.createElement('div');
    marker.className = bboxClassName;
    marker.style.top = scrollTop + rect.top + 'px';
    marker.style.left = rect.left + 'px';
    marker.style.width = rect.width + 'px';
    marker.style.height = rect.height + 'px';
    marker.style.zIndex = zIndex;
    marker.setAttribute(markerAttr, id.toString());

    marker.style.setProperty('--bg-color', bgColor);
    marker.style.setProperty('--text-color', textColor);

    document.body.appendChild(marker);
  }
}

export function addMask(elements: Element[]) {
  const canvas = document.createElement('canvas');
  canvas.id = 'lc-mask';
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const ctx = canvas.getContext('2d')!;

  ctx.fillRect(0, 0, canvas.width, canvas.height);

  elements.forEach(el => {
    const rects = el.getClientRects();

    for (const rect of rects) {
      ctx.clearRect(rect.x, rect.y, rect.width, rect.height);
    }
  });

  document.body.appendChild(canvas);
}

export async function addBboxes(elements: Element[], screenshot?: string) {
  const pageBrightness = await getPageBrightness(screenshot);

  elements.forEach((el, i) => {
    markElement(el, i, pageBrightness);
  });

  return elements;
}

export function clearBboxes() {
  document.querySelector('#lc-mask')?.remove();

  [...document.querySelectorAll(`.${bboxClassName}`)].forEach(el =>
    el.remove(),
  );

  [...document.querySelectorAll(`[${markerAttr}]`)].forEach(el => {
    el.removeAttribute(markerAttr);
  });
}
