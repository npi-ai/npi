configs = {
    "bardeen": {
        "url": "https://www.bardeen.ai/playbooks",
        "scraping_type": "list-like",
        "ancestor_selector": ".playbook_list",
        "items_selector": ".playbook_list .playbook_item-link",
        "limit": 200,
        "output_columns": [
            {
                "name": "Apps Involved",
                "type": "text",
                "description": "The apps involved in the playbook",
            },
            {
                "name": "Description",
                "type": "text",
                "description": "The description of the playbook",
            },
            {
                "name": "Time Saved",
                "type": "text",
                "description": "The time saved by using the playbook in format like '1 min'",
            },
            {
                "name": "URL",
                "type": "link",
                "description": "The URL of the playbook",
            },
        ],
    },
    "retool": {
        "url": "https://retool.com/templates",
        "scraping_type": "list-like",
        "ancestor_selector": ".sc-e51951af-3",
        "items_selector": ".sc-e51951af-3 > a",
        "limit": 100,
        "output_columns": [
            {
                "name": "Template Name",
                "type": "text",
                "description": "Name of the retool template",
            },
            {
                "name": "Description",
                "type": "text",
                "description": "Description of the retool template",
            },
            {
                "name": "Snapshot",
                "type": "image",
                "description": "Snapshot image of the retool template",
            },
            {
                "name": "URL",
                "type": "link",
                "description": "The URL of the retool template",
            },
        ],
    },
    "ifttt": {
        "url": "https://ifttt.com/explore",
        "scraping_type": "list-like",
        "ancestor_selector": ".get-more-results > .get-more",
        "items_selector": ".get-more-results > .get-more > .explore-tile",
        "limit": 100,
        "output_columns": [
            {
                "name": "Title/Description",
                "type": "text",
                "description": "Title or description of the ifttt applet",
            },
            {
                "name": "Apps Involved",
                "type": "text",
                "description": "Apps involved in the ifttt applet, usually shown as icons",
            },
            {
                "name": "User Count",
                "type": "text",
                "description": "Number of users using the ifttt applet",
            },
            {
                "name": "URL",
                "type": "link",
                "description": "The URL of the ifttt applet",
            },
        ],
    },
}
