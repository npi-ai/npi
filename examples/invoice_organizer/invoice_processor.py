import json
import os.path

from npiai import FunctionTool, Context, function

from constants import StorageKeys


class InvoiceProcessor(FunctionTool):
    name = "invoice_processor"

    description = """
    Process the invoice data and save them into files.
    """

    @function
    async def process_invoice(
        self,
        ctx: Context,
        invoice_number: str | None = None,
        invoice_date: str | None = None,
        due_date: str | None = None,
        assigner: str | None = None,
        subject: str | None = None,
        total_amount: str | None = None,
        email_subject: str | None = None,
    ):
        """
        Process the invoice data and save them into files.

        Args:
            ctx: NPi Context
            invoice_number: Invoice number
            invoice_date: Invoice date in YYYY-MM-DD format
            due_date: Invoice due date in YYYY-MM-DD format
            assigner: The entity sending the invoice
            subject: The subject of the invoice
            total_amount: The total amount or price of the invoice, including currency code
            email_subject: The subject of the email containing the invoice
        """
        data = {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "assigner": assigner,
            "subject": subject,
            "total_amount": total_amount,
            "email_subject": email_subject,
        }

        # TODO: save invoice data

        print(
            f"Saving into {await ctx.kv.get(StorageKeys.OUTPUT_FILENAME)} (format: {await ctx.kv.get(StorageKeys.OUTPUT_FORMAT)})"
        )

        print(json.dumps(data, indent=2, ensure_ascii=False))

        output_file = await ctx.kv.get(StorageKeys.OUTPUT_FILENAME)
        current_data = []

        try:
            if os.path.exists(output_file):
                with open(output_file, "r") as f:
                    current_data = json.load(f)
        except Exception:
            pass

        with open(output_file, "w") as f:
            current_data.append(data)
            f.write(json.dumps(current_data, indent=2, ensure_ascii=False))

        return "Invoice processed"
