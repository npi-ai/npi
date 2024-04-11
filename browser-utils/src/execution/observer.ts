export class Observer {
  #stablePromise: Promise<void>;
  #hasChange: boolean = false;
  #observer!: MutationObserver;
  #overallTimer!: number;

  constructor(maxTimeout: number = 5_000) {
    this.#stablePromise = new Promise(resolve => {
      let timer: number;

      const done = () => {
        resolve();
        clearTimeout(timer);
        clearTimeout(this.#overallTimer);
        observer.disconnect();
        window.removeEventListener('scroll', resolveDelayed);
      };

      const resolveDelayed = () => {
        clearTimeout(timer);
        timer = window.setTimeout(() => {
          done();
        }, 3_000);
      };

      // listen to scroll event
      window.addEventListener('scroll', resolveDelayed);

      // overall timeout
      this.#overallTimer = window.setTimeout(() => {
        done();
      }, maxTimeout);

      const observer = new MutationObserver(mutations => {
        for (const m of mutations) {
          if (m.target !== document.body) {
            this.#hasChange = true;
            break;
          }
        }

        if (this.#hasChange) {
          resolveDelayed();
        }
      });

      observer.observe(document.body, {
        subtree: true,
        childList: true,
      });

      this.#observer = observer;
    });
  }

  async domStable() {
    await this.#stablePromise;
  }

  domChanged() {
    return this.#hasChange;
  }

  disconnect() {
    this.#observer.disconnect();
    clearTimeout(this.#overallTimer);
  }
}
