import json
import os
import asyncio
from npiai import Context
from npiai.tools.outlook import Outlook
from npiai.tools.email_organizer import EmailOrganizer
from azure.identity import (
    InteractiveBrowserCredential,
    TokenCachePersistenceOptions,
    AuthenticationRecord,
)

token_cache = ".cache/outlook_token_cache.json"


async def main():
    # authenticate
    authentication_record = None

    if os.path.exists(token_cache):
        with open(token_cache, "r") as f:
            authentication_record = AuthenticationRecord.deserialize(f.read())

    creds = InteractiveBrowserCredential(
        client_id=os.environ.get("AZURE_CLIENT_ID", None),
        # tenant_id=os.environ.get("AZURE_TENANT_ID", None),
        tenant_id="common",
        cache_persistence_options=TokenCachePersistenceOptions(),
        authentication_record=authentication_record,
    )

    record = creds.authenticate(scopes=["Mail.Read", "Mail.Send"])

    os.makedirs(os.path.dirname(token_cache), exist_ok=True)

    with open(token_cache, "w") as f:
        f.write(record.serialize())

    async with EmailOrganizer(provider=Outlook(creds)) as tool:
        # list emails
        email_list = [email async for email in tool.list_inbox_stream(limit=10)]

        print("Raw email list:", json.dumps(email_list, indent=4, ensure_ascii=False))

        # filter invoice-like emails
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

        columns = await tool.infer_columns(
            ctx=Context(),
            email_or_id_list=filtered_emails[:3],
            with_pdf_attachments=True,
            goal="Extract invoice-related information from the emails.",
        )

        print("Inferred columns:", json.dumps(columns, indent=4, ensure_ascii=False))

        # summarize invoice-like emails
        async for item in tool.summarize_stream(
            ctx=Context(),
            email_or_id_list=filtered_emails,
            concurrency=4,
            with_pdf_attachments=True,
            output_columns=columns,
        ):
            print(json.dumps(item, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
