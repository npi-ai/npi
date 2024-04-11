export class Defer<V = unknown> {
  promise: Promise<V>;

  resolve!: (value?: V) => void;

  reject!: (error?: unknown) => void;

  constructor() {
    this.promise = new Promise((resolve, reject) => {
      this.resolve = resolve as typeof this.resolve;
      this.reject = reject;
    });
  }
}
