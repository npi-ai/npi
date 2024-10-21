MULTI_COLUMN_INFERENCE_PROMPT = """
Imagine you are summarizing the content of a webpage into a table with **multiple rows** of data. Each item on the page is represented as a markdown section and is surrounded by a <section> tag. Follow the steps below to infer the columns of the output table:
                        
1. **Identify Common Themes**: Begin by examining the provided markdown sections to discern common themes or shared attributes across the items.

2. **Determine Table Columns**: Based on the common themes identified, propose relevant columns. If each item contains a link to detailed information, consider including a 'URL' column.
"""

SINGLE_COLUMN_INFERENCE_PROMPT = """
Imagine you are summarizing the content of a webpage into a table with **a single row** of data. Suggest columns that encapsulate the essential details of the content. If the content includes multiple headings, consider using them as column names.
"""

MULTI_COLUMN_SCRAPING_PROMPT = """
You are a web scraper agent helping user summarize the content of a webpage into a table with **multiple rows** of data. Each item on the page is represented as a markdown section and is surrounded by a <section> tag. For the given markdown content, summarize the content into a table with the following columns:

# Column Definitions

{column_defs}

# Response Format

Respond with the table in CSV format. The first line should contain the column names, and the subsequent lines should contain the scraped data. Do not respond with any additional information.

Each column value should be enclosed in double quotes and separated by commas. Note that **column names must exactly match the provided column definitions**.
"""

SINGLE_COLUMN_SCRAPING_PROMPT = """
You are a web scraper agent helping user summarize the content of a webpage into a table with **a single row** of data. Summarize the content into a table with the following columns:

# Column Definitions
{column_defs}

# Response Format

Respond with the table in CSV format. The first line should contain the column names, and the second line should contain the scraped data. Do not respond with any additional information. 

Each column value should be enclosed in double quotes and separated by commas. Note that **column names must exactly match the provided column definitions**.
"""
