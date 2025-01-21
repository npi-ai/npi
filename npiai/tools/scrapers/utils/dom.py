from npiai.core import PlaywrightContext


async def init_items_observer(
    playwright: PlaywrightContext,
    ancestor_selector: str | None = None,
    items_selector: str | None = None,
):
    # attach mutation observer to the ancestor element
    await playwright.page.evaluate(
        """
        ([ancestor_selector, items_selector]) => {
            const ancestor = document.querySelector(ancestor_selector);
            
            if (!ancestor) {
                return;
            }
            
            window.addedNodes = [];
            
            window.npiObserver = new MutationObserver((records) => {
                for (const record of records) {
                    for (const addedNode of record.addedNodes) {
                        if (addedNode.nodeType === Node.ELEMENT_NODE &&
                            (addedNode.matches(items_selector) || addedNode.querySelector(items_selector))
                        ) {
                            window.addedNodes.push(addedNode);
                        }
                    }
                }
            });
            
            window.npiObserver.observe(
                document.querySelector(ancestor_selector), 
                { childList: true, subtree: true }
            );
        }
        """,
        [ancestor_selector or "body", items_selector or "*"],
    )


async def has_items_added(playwright: PlaywrightContext, timeout: int = 3000) -> bool:
    return await playwright.page.evaluate(
        """
        (timeout) => {
            return new Promise(resolve => {
                let count = 0;
                const maxCount = Math.floor(timeout / 100);
                
                function check() {
                    if (!window.addedNodes) {
                        return resolve(false);
                    }
                    if (window.addedNodes.length > 0) {
                        return resolve(true);
                    }
                    if (count > maxCount) {
                        return resolve(false);
                    }
                    
                    count++;
                    setTimeout(check, 100);
                }
                
                check();
            });
        }
        """,
        timeout,
    )
