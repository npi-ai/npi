export async function getPageBrightness(screenshot?: string): Promise<number> {
  if (!screenshot) {
    return 100;
  }

  const img = document.createElement('img');

  return new Promise((resolve, reject) => {
    img.onload = () => {
      const width = img.naturalWidth;
      const height = img.naturalHeight;
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d')!;

      canvas.width = width;
      canvas.height = height;

      ctx.drawImage(img, 0, 0, width, height);

      const pixels = ctx.getImageData(0, 0, width, height);
      const count = pixels.data.length;
      let brightnessTotal = 0;

      for (let offset = 0; offset < count; offset += 4) {
        const r = pixels.data[offset];
        const g = pixels.data[offset + 1];
        const b = pixels.data[offset + 2];
        const br = 0.3 * r + 0.59 * g + 0.11 * b;

        brightnessTotal += (br / 255) * 100;
      }

      resolve(Math.floor(brightnessTotal / width / height));
    };

    img.onerror = reject;
    img.src = screenshot;
  });
}

export function isDark(brightness: number) {
  return brightness < 45;
}

export function randomBrightness(pageBrightness: number) {
  let lower: number;
  let upper: number;

  if (isDark(pageBrightness)) {
    lower = 100 - pageBrightness * 2;
    upper = 100;
  } else {
    lower = 0;
    upper = 100 - pageBrightness / 2;
  }

  return Math.trunc(Math.random() * (upper - lower) + lower);
}
