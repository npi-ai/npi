import json
import os
import asyncio
from npiai import Context
from npiai.tools.outlook import Outlook
from npiai.tools.email_organizer import EmailOrganizer
from azure.identity import InteractiveBrowserCredential


async def main():
    creds = InteractiveBrowserCredential(
        client_id=os.environ.get("AZURE_CLIENT_ID", None),
        # tenant_id=os.environ.get("AZURE_TENANT_ID", None),
        tenant_id="common",
    )

    async with EmailOrganizer(provider=Outlook(creds)) as tool:
        email_list = [email async for email in tool.list_inbox_stream(limit=10)]

        for email in email_list:
            print(await tool._to_compact_email_with_pdf_attachments(email))

        print("Raw email list:", json.dumps(email_list, indent=4, ensure_ascii=False))

        filtered_emails = []

        async for result in tool.filter_stream(
            ctx=Context(),
            email_or_id_list=email_list,
            criteria="The email should include invoice-like content in the body or attachments",
            concurrency=4,
        ):
            if result["matched"]:
                filtered_emails.append(result["email"])

            print(
                f'Subject: {result["email"]["subject"]}, Matched: {result["matched"]}'
            )

        async for item in tool.summarize_stream(
            ctx=Context(),
            email_or_id_list=filtered_emails,
            concurrency=4,
            with_pdf_attachments=True,
            output_columns=[
                {
                    "name": "Invoice Number",
                    "type": "text",
                    "description": "The invoice number",
                },
                {
                    "name": "Issuer",
                    "type": "text",
                    "description": "The issuer of the invoice",
                },
                {
                    "name": "Recipient",
                    "type": "text",
                    "description": "The recipient of the invoice",
                },
                {
                    "name": "Amount",
                    "type": "number",
                    "description": "The total amount in the invoice",
                },
                {
                    "name": "Date",
                    "type": "text",
                    "description": "The date of the invoice",
                },
            ],
        ):
            print(json.dumps(item, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
