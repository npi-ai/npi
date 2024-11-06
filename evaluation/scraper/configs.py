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
                "description": "The apps involved in the playbook, separated by commas",
            },
            {
                "name": "Description",
                "type": "text",
                "description": "The description of the playbook",
            },
            {
                "name": "Time Saved",
                "type": "text",
                "description": "The time saved by using the playbook in short format. Instead of '3 minutes' or '3 mins', use '3 min'.",
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
                "description": "Title or description of the ifttt applet. Skip any item that does not link to an applet. Remove 'by xxx' part as it is not needed.",
            },
            {
                "name": "Apps Involved",
                "type": "text",
                "description": "Apps involved in the ifttt applet, usually shown as icons and appear before the title/description",
            },
            {
                "name": "User Count",
                "type": "text",
                "description": "Number of users using the ifttt applet. Fill in '0' if not available.",
            },
            {
                "name": "URL",
                "type": "link",
                "description": "The URL of the ifttt applet",
            },
        ],
    },
    "zapier": {
        "url": "https://zapier.com/templates",
        "scraping_type": "list-like",
        # [All Templates] section
        "ancestor_selector": ".PublicTemplateGrid_wrapper__F3U2T:nth-child(4) > .PublicTemplateGrid_templatesWrapper__8K3kH",
        "items_selector": ".PublicTemplateGrid_wrapper__F3U2T:nth-child(4) > .PublicTemplateGrid_templatesWrapper__8K3kH > .TemplateCard_wrapper__GzoyG",
        "limit": 100,
        "output_columns": [
            {
                "name": "Template Name",
                "type": "text",
                "description": "The name of the template which indicates the main function or purpose of the item.",
            },
            {
                "name": "Thumbnail",
                "type": "image",
                "description": "The URL of the thumbnail image that visually represents each template.",
            },
            {
                "name": "Description",
                "type": "text",
                "description": "A brief description of what the template does or the main function it serves.",
            },
            {
                "name": "URL",
                "type": "link",
                "description": "The URL linking to the detailed page or further information about the template.",
            },
        ],
    },
}
