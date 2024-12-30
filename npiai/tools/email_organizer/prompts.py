FILTER_PROMPT = """
You are an email organizer agent helping user filter emails based on specific criteria. For the given email, you should determine whether it meets the filtering criteria or not, and callback with a boolean value.
"""

COLUMN_INFERENCE_PROMPT = """
Imagine you are summarizing the content of emails into a table with **multiple rows** of data. Each email is represented as a json object with various fields such as 'subject', 'from', 'to', 'cc', 'bcc', 'date', 'body', and 'attachments'. Suggest columns that encapsulate the essential details of the content.

## Goal

{goal}

## Instructions

Follow the steps below to infer the columns of the output table:

1. **Identify Common Themes**: Begin by examining the provided emails to discern common themes or shared attributes across them.

2. **Determining Column Name**: Based on the common themes identified, propose relevant columns. Each column should represent a single attribute or piece of information associated with each item. Avoid unnecessary metadata columns like 'Email ID', 'Body', or 'Has Attachments'.

3. **Assign Column Types**: For each column, specify the type of data it should contain. Possible column types are:
    - **text**: Columns that contain textual information.
    - **number**: Columns that contain numerical information.

4. **Generate a Step-by-Step Prompt**: For each column, provide a step-by-step prompt that describes how to extract the data for that column from the email data. The prompt must contain the following information:
    - **Description**: A brief description of the data to be extracted. Explain what the data represents and how it relates to the markdown content.
    - **Identification**: How to identify the relevant data within the provided email.
    - **Extraction**: The steps to extract the data from the identified location. Include any necessary transformations or processing steps in a numbered list.
    - **Note**: Any additional notes or considerations for extracting the data if needed. This could include handling special cases or edge scenarios. For example, if a column contains currency values, specify the currency format.
"""

SUMMARIZE_PROMPT = """
You are an email organizer agent helping user summarize emails into a table. Use the specified column definitions to extract and organize the data properly. 

## Column Definition Format

The columns are defined in a json object with the following fields:

- **name**: The name of the column.
- **type**: The type of the column. Possible values are as follows:
    - **text**: Columns that contain textual information.
    - **number**: Columns that contain numerical information.
- **description**: A brief description of the data to be extracted.
- **prompt**: An optional step-by-step prompt on how to extract the column data.

## Instructions

1. Extract data from the email based on the given column prompts. Try keep the data as is, without any additional processing if not specified.
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
