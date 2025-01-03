MULTI_COLUMN_INFERENCE_PROMPT = """
Imagine you are summarizing the content of a webpage into a table with **multiple rows** of data. Each item on the page is represented as a markdown section and is surrounded by a <section> tag. Suggest columns that encapsulate the essential details of the content. 

## Goal

{goal}

## Instructions

Follow the steps below to infer the columns of the output table:
                        
1. **Identify Common Themes**: Begin by examining the provided markdown sections to discern common themes or shared attributes across the items.

2. **Determine Table Columns**: Based on the common themes identified, propose relevant columns. Each column should represent a single attribute or piece of information associated with each item. For example, instead of having an 'Images' column, consider breaking it down into 'Logo', 'Product Image', etc. If each item contains a link to detailed information, consider including a 'URL' (or any other relevant name) column.

3. **Assign Column Types**: For each column, specify the type of data it should contain. Possible column types are:
    - **text**: Columns that contain textual information.
    - **link**: Columns that contain URLs or hyperlinks.
    - **image**: Columns that contain image URLs.

4. **Generate a Step-by-Step Prompt**: For each column, provide a step-by-step prompt that describes how to extract the data for that column from the markdown sections. The prompt must contain the following information:
    - **Description**: A brief description of the data to be extracted. Explain what the data represents and how it relates to the markdown content.
    - **Identification**: How to identify the relevant data within the markdown section. This could involve looking for specific headings, tags, or patterns.
    - **Extraction**: The steps to extract the data from the identified location. Include any necessary transformations or processing steps in a numbered list.
    - **Note**: Any additional notes or considerations for extracting the data if needed. This could include handling special cases or edge scenarios. For example, if a column contains currency values, specify the currency format.
"""

SINGLE_COLUMN_INFERENCE_PROMPT = """
Imagine you are summarizing the content of a webpage into a table with **a single row** of data. Suggest columns that encapsulate the essential details of the content. 

## Goal

{goal}

## Instructions

Follow the steps below to infer the columns of the output table:

1. **Identify Key Information**: Review the provided markdown document to determine the most critical information that should be included in the table.

2. **Review Headings**: If the content includes multiple headings, consider using them as column names.

3. **Determining Column Name**: Based on the key information identified, propose a column name that best represents the content. Each column should represent a single attribute or piece of information. For example, instead of having an 'Images' column, consider breaking it down into 'Logo', 'Product Image', etc.

4. **Assign Column Types**: For each column, specify the type of data it should contain. Possible column types are:
    - **text**: Columns that contain textual information.
    - **link**: Columns that contain URLs or hyperlinks.
    - **image**: Columns that contain image URLs.

5. **Generate a Step-by-Step Prompt**: For each column, provide a step-by-step prompt that describes how to extract the data for that column from the markdown sections. The prompt must contain the following information:
    - **Description**: A brief description of the data to be extracted. Explain what the data represents and how it relates to the markdown content.
    - **Identification**: How to identify the relevant data within the markdown section. This could involve looking for specific headings, tags, or patterns.
    - **Extraction**: The steps to extract the data from the identified location. Include any necessary transformations or processing steps in a numbered list.
    - **Note**: Any additional notes or considerations for extracting the data if needed. This could include handling special cases or edge scenarios. For example, if a column contains currency values, specify the currency format.
"""

MULTI_COLUMN_SCRAPING_PROMPT = """
You are a web scraper agent helping user summarize the content of a webpage into a table with **multiple rows** of data. Each item on the page is represented as a markdown section and is surrounded by a <section> tag, with each section assigned a unique id attribute. Use the specified column definitions to extract and organize the data properly.

## Column Definition Format

The columns are defined in a json object with the following fields:

- **name**: The name of the column.
- **type**: The type of the column. Possible values are as follows:
    - **text**: Columns that contain textual information.
    - **link**: Columns that contain URLs or hyperlinks.
    - **image**: Columns that contain image URLs.
- **description**: A brief description of the data to be extracted.
- **prompt**: An optional step-by-step prompt on how to extract the column data.

## Instructions

1. Extract data from the webpage based on the given column prompts. Try keep the data as is, without any additional processing if not specified.
2. Organize this data into a CSV format table with the following format:
   - The first line contains the column names.
   - The subsequent lines should contain the scraped data.
3. Enclose all values and column names in double quotes and separate them using commas.
4. Ensure that column names in the CSV match exactly as defined in the column definitions.

## Column Definitions for This Task

```json
{column_defs}
```
"""

SINGLE_COLUMN_SCRAPING_PROMPT = """
You are a web scraper agent helping user summarize the content of a webpage into a table with **a single row** of data. Use the specified column definitions to extract and organize the data properly.

## Column Definition Format

The columns are defined in a json object with the following fields:

- **name**: The name of the column.
- **type**: The type of the column. Possible values are as follows:
    - **text**: Columns that contain textual information.
    - **link**: Columns that contain URLs or hyperlinks.
    - **image**: Columns that contain image URLs.
- **description**: A brief description of the data to be extracted.
- **prompt**: An optional step-by-step prompt on how to extract the column data.

## Instructions

1. Extract data from the webpage based on the given column prompts. Try keep the data as is, without any additional processing if not specified.
2. Organize this data into a CSV format table with one row, with the following format:
   - The first line contains the column names.
   - The second line contains the corresponding extracted data.
3. Enclose all values and column names in double quotes and separate them using commas.
4. Ensure that column names in the CSV match exactly as defined in the column definitions.

## Column Definitions for This Task

```json
{column_defs}
```
"""
