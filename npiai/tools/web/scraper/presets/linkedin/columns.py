from textwrap import dedent
from npiai.tools.web.scraper.types import Column


POST_COLUMNS: list[Column] = [
    {
        "name": "Original Poster",
        "type": "text",
        "description": "Name of the person who originally posted the content.",
        "prompt": dedent(
            """
            **Description**: Extracts the name of the individual who originally posted the post.
            
            **Identification**: 
            1. If the post is a repost, locate text that typically follows the phrase 'reposted this' or initial text that provides a name.
            2. Otherwise, identify the name of the poster, often found at the top or bottom of the post.
            
            **Extraction**:
            1. Identify if the post is a repost by locating the phrase 'reposted this'.
            2. If it is a repost, extract the name of the original poster, often found after the phrase 'reposted this'.
            3. If not a repost, extract the name of the poster, often found at the top or bottom of the post.
        """
        ),
    },
    {
        "name": "Date",
        "type": "text",
        "description": "The date and time the post was shared.",
        "prompt": dedent(
            """
            **Description**: Extracts the date and time the post was shared.
            
            **Identification**: Locate the date and time stamp often found at the top or bottom of the post.
            
            **Extraction**:
            1. Identify the date and time stamp often found below the name and bio of the poster.
            2. Extract the date and time the post was shared.
            
            **Note**: Ensure to extract the date and time the post was shared, not the current date and time.
            """
        ),
    },
    {
        "name": "Content",
        "type": "text",
        "description": "The main content or message shared within the post.",
        "prompt": dedent(
            """
            **Description**: Provides the main textual content or message body of the post, outlining significant information or messages shared by the poster.
            
            **Identification**: Locate paragraphs or text blocks following initial headings and profile information, often set apart by paragraphs.
            
            **Extraction**:
            1. Identify blocks of text immediately following any initial header or introductory linking text.
            2. Extract all text content up to the closing of the first logical paragraph or section.
            3. Combine text if it spans multiple segments or lists.
            
            **Note**: Ensure to omit links or multimedia descriptions unless integral to the message.
            """
        ),
    },
    {
        "name": "Media Links",
        "type": "link",
        "description": "Links to the media content shared within the post.",
        "prompt": dedent(
            """
            **Description**: Extracts links to media content shared within the post.
            
            **Identification**: Look for links to external media content or embedded media within the post.
            
            **Extraction**:
            1. Identify links to external media content or embedded media within the post.
            2. Extract the URL links to the media content.
            
            **Note**: Ensure to include links to images, videos, or other multimedia content shared within the post.
            """
        ),
    },
    {
        "name": "Likes",
        "type": "text",
        "description": "The number of likes the post has received.",
        "prompt": dedent(
            """
            **Description**: Quantifies the number of likes the post has received.
            
            **Identification**: Seek specific numerical indicators directly following icon indicators or text alignments related to 'likes'.
            
            **Extraction**:
            1. Identify and numerically extract counts following icon or engagement activity markers like 'like'.
            2. Ensure to classify and include counts each for likes.
            
            **Note**: If the post has no likes, specify '0' as the count.
            """
        ),
    },
    {
        "name": "Comments",
        "type": "text",
        "description": "The number of comments the post has received.",
        "prompt": dedent(
            """
            **Description**: Quantifies the number of comments the post has received.
            
            **Identification**: Seek specific numerical indicators directly following icon indicators or text alignments related to 'comments'.
            
            **Extraction**:
            1. Identify and numerically extract counts following icon or engagement activity markers like 'comment'.
            2. Ensure to classify and include counts each for comments.
            
            **Note**: If the post has no comments, specify '0' as the count.
            """
        ),
    },
    {
        "name": "Reposts",
        "type": "text",
        "description": "The number of reposts the post has received.",
        "prompt": dedent(
            """
            **Description**: Quantifies the number of reposts the post has received.
            
            **Identification**: Seek specific numerical indicators directly following icon indicators or text alignments related to 'reposts'.
            
            **Extraction**:
            1. Identify and numerically extract counts following icon or engagement activity markers like 'repost'.
            2. Ensure to classify and include counts each for reposts.
            
            **Note**: If the post has no reposts, specify '0' as the count.
            """
        ),
    },
]
