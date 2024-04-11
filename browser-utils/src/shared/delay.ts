export async function delay(ms: number) {
  await new Promise(res => setTimeout(res, ms));
}
