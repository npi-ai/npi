testdata = [
    {
        "url": "https://www.bardeen.ai/playbooks",
        "infinite_scroll": True,
        "pagination_button": None,
        "scraping_type": "list-like",
        "selectors": {
            "items": ".playbook_list > .playbook_item",
            "ancestor": ".playbook_list",
        },
    },
    {
        "url": "https://www.bardeen.ai/playbooks/get-data-from-the-currently-opened-imdb-com-title-page",
        "infinite_scroll": False,
        "pagination_button": None,
        "scraping_type": "single",
    },
    {
        "url": "https://ifttt.com/explore",
        "infinite_scroll": True,
        "pagination_button": None,
        "scraping_type": "list-like",
        "selectors": {
            "items": ".get-more-results > .get-more > .explore-tile",
            "ancestor": ".get-more-results > .get-more",
        },
    },
    {
        "url": "https://retool.com/templates",
        "infinite_scroll": False,
        "pagination_button": None,
        "scraping_type": "list-like",
        "selectors": {
            "items": ".sc-e51951af-3 > a",
            "ancestor": ".sc-e51951af-3",
        },
    },
    {
        "url": "https://www.google.com/search?q=test&hl=ja",
        "infinite_scroll": False,
        "pagination_button": "#pnnext",
        "scraping_type": "list-like",
        "selectors": {
            "items": "#rso > div:nth-child(4) > .MjjYud",
            "ancestor": "#rso > div:nth-child(4)",
        },
    },
    {
        "url": "https://www.amazon.com/s?k=test",
        "infinite_scroll": False,
        "pagination_button": ".s-pagination-next",
        "scraping_type": "list-like",
        "selectors": {
            "items": ".s-main-slot > .sg-col-20-of-24",
            "ancestor": ".s-main-slot",
        },
    },
    {
        "url": "https://www.amazon.com/product-reviews/B09KZ6TBNY/",
        "infinite_scroll": False,
        "pagination_button": ".a-last > a",
        "scraping_type": "list-like",
        "selectors": {
            "items": "#cm_cr-review_list > .a-section",
            "ancestor": "#cm_cr-review_list",
        },
    },
    # {
    #     "url": "https://x.com/home",
    #     "infinite_scroll": True,
    #     "pagination_button": None,
    #     "scraping_type": "list-like",
    #     "selectors": {
    #         "items": ".r-f8sm7e:nth-child(5) > .css-175oi2r > .css-175oi2r > div > .css-175oi2r",
    #         "ancestor": ".r-f8sm7e:nth-child(5) > .css-175oi2r > .css-175oi2r > div",
    #     },
    # },
]
