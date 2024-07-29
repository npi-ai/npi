from simplegmail import Gmail
from simplegmail.message import Message
from simplegmail.label import Label
from simplegmail.attachment import Attachment
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError
import re
import base64
import html
import dateutil.parser as parser
from typing import Optional, List


class GmailClientWrapper(Gmail):
    def _create_message(
        self,
        sender: str,
        to: str,
        subject: str = "",
        msg_html: str = None,
        msg_plain: str = None,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[str] = None,
        signature: bool = False,
        user_id: str = "me",
        reply_to: Optional[str] = None,
    ) -> dict:
        """
        Creates the raw email message to be sent.

        Args:
            sender: The email address the message is being sent from.
            to: The email address the message is being sent to.
            subject: The subject line of the email.
            msg_html: The HTML message of the email.
            msg_plain: The plain text alternate message of the email (for slow
                or old browsers).
            cc: The list of email addresses to be Cc'd.
            bcc: The list of email addresses to be Bcc'd
            attachments: A list of attachment file paths.
            signature: Whether the account signature should be added to the
                message. Will add the signature to your HTML message only, or a
                create a HTML message if none exists.
            reply_to: The id of the message that this email replies to.

        Returns:
            The message dict.

        """

        msg = MIMEMultipart("mixed" if attachments else "alternative")
        msg["To"] = to
        msg["From"] = sender
        msg["Subject"] = subject

        if cc:
            msg["Cc"] = ", ".join(cc)

        if bcc:
            msg["Bcc"] = ", ".join(bcc)

        if signature:
            m = re.match(r".+\s<(?P<addr>.+@.+\..+)>", sender)
            address = m.group("addr") if m else sender
            account_sig = self._get_alias_info(address, user_id)["signature"]

            if msg_html is None:
                msg_html = ""

            msg_html += "<br /><br />" + account_sig

        if reply_to:
            msg_id = reply_to.headers.get("Message-ID") or reply_to.id
            msg["In-Reply-To"] = msg_id
            msg["References"] = msg_id

        attach_plain = MIMEMultipart("alternative") if attachments else msg
        attach_html = MIMEMultipart("related") if attachments else msg

        if msg_plain:
            attach_plain.attach(MIMEText(msg_plain, "plain"))

        if msg_html:
            attach_html.attach(MIMEText(msg_html, "html"))

        if attachments:
            attach_plain.attach(attach_html)
            msg.attach(attach_plain)

            self._ready_message_with_attachments(msg, attachments)

        res = {"raw": base64.urlsafe_b64encode(msg.as_string().encode()).decode()}

        if reply_to:
            res["threadId"] = reply_to.thread_id

        return res

    def _build_message_from_ref(
        self,
        user_id: str,
        message_ref: dict,
        attachments: str = "reference",
        is_draft: bool = False,
    ) -> Message:
        """
        Creates a Message object from a reference.

        Args:
            user_id: The username of the account the message belongs to.
            message_ref: The message reference object returned from the Gmail
                API.
            attachments: Accepted values are 'ignore' which completely ignores
                all attachments, 'reference' which includes attachment
                information but does not download the data, and 'download' which
                downloads the attachment data to store locally. Default
                'reference'.
            is_draft: Whether the message is a draft or not.

        Returns:
            The Message object.

        Raises:
            googleapiclient.errors.HttpError: There was an error executing the
                HTTP request.

        """

        try:
            # Get message JSON
            if is_draft:
                message = (
                    self.service.users()
                    .drafts()
                    .get(userId=user_id, id=message_ref["id"])
                    .execute()["message"]
                )
            else:
                message = (
                    self.service.users()
                    .messages()
                    .get(userId=user_id, id=message_ref["id"])
                    .execute()
                )

        except HttpError as error:
            # Pass along the error
            raise error

        else:
            msg_id = message["id"]
            thread_id = message["threadId"]
            label_ids = []
            if "labelIds" in message:
                user_labels = {x.id: x for x in self.list_labels(user_id=user_id)}
                label_ids = [user_labels[x] for x in message["labelIds"]]
            snippet = html.unescape(message["snippet"])

            payload = message["payload"]
            headers = payload["headers"]

            # Get header fields (date, from, to, subject)
            date = ""
            sender = ""
            recipient = ""
            subject = ""
            msg_hdrs = {}
            cc = []
            bcc = []
            for hdr in headers:
                if hdr["name"].lower() == "date":
                    try:
                        date = str(parser.parse(hdr["value"]).astimezone())
                    except Exception:
                        date = hdr["value"]
                elif hdr["name"].lower() == "from":
                    sender = hdr["value"]
                elif hdr["name"].lower() == "to":
                    recipient = hdr["value"]
                elif hdr["name"].lower() == "subject":
                    subject = hdr["value"]
                elif hdr["name"].lower() == "cc":
                    cc = hdr["value"].split(", ")
                elif hdr["name"].lower() == "bcc":
                    bcc = hdr["value"].split(", ")

                msg_hdrs[hdr["name"]] = hdr["value"]

            parts = self._evaluate_message_payload(
                payload, user_id, message_ref["id"], attachments
            )

            plain_msg = None
            html_msg = None
            attms = []
            for part in parts:
                if part["part_type"] == "plain":
                    if plain_msg is None:
                        plain_msg = part["body"]
                    else:
                        plain_msg += "\n" + part["body"]
                elif part["part_type"] == "html":
                    if html_msg is None:
                        html_msg = part["body"]
                    else:
                        html_msg += "<br/>" + part["body"]
                elif part["part_type"] == "attachment":
                    attm = Attachment(
                        self.service,
                        user_id,
                        msg_id,
                        part["attachment_id"],
                        part["filename"],
                        part["filetype"],
                        part["data"],
                    )
                    attms.append(attm)

            return Message(
                self.service,
                self.creds,
                user_id,
                msg_id,
                thread_id,
                recipient,
                sender,
                subject,
                date,
                snippet,
                plain_msg,
                html_msg,
                label_ids,
                attms,
                msg_hdrs,
                cc,
                bcc,
            )

    def create_draft(
        self,
        sender: str,
        to: str,
        subject: str = "",
        msg_html: Optional[str] = None,
        msg_plain: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        signature: bool = False,
        user_id: str = "me",
        reply_to: Optional[str] = None,
    ) -> Message:
        """
        Create and insert a draft email.

        Args:
            sender: The email address the message is being sent from.
            to: The email address the message is being sent to.
            subject: The subject line of the email.
            msg_html: The HTML message of the email.
            msg_plain: The plain text alternate message of the email. This is
                often displayed on slow or old browsers, or if the HTML message
                is not provided.
            cc: The list of email addresses to be cc'd.
            bcc: The list of email addresses to be bcc'd.
            attachments: The list of attachment file names.
            signature: Whether the account signature should be added to the
                message.
            user_id: The address of the sending account. 'me' for the
                default address associated with the account.
            reply_to: The id of the message that this draft replies to.

        Returns:
            The Message object representing the draft message.

        Raises:
            googleapiclient.errors.HttpError: There was an error executing the
                HTTP request.

        """

        msg = self._create_message(
            sender,
            to,
            subject,
            msg_html,
            msg_plain,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            signature=signature,
            user_id=user_id,
            reply_to=reply_to,
        )

        try:
            req = (
                self.service.users().drafts().create(userId="me", body={"message": msg})
            )
            res = req.execute()
            return self._build_message_from_ref(
                user_id, res, "reference", is_draft=True
            )

        except HttpError as error:
            # Pass along the error
            raise error

    def send_message(
        self,
        sender: str,
        to: str,
        subject: str = "",
        msg_html: Optional[str] = None,
        msg_plain: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[str]] = None,
        signature: bool = False,
        user_id: str = "me",
        reply_to: Optional[str] = None,
    ) -> Message:
        """
        Sends an email.

        Args:
            sender: The email address the message is being sent from.
            to: The email address the message is being sent to.
            subject: The subject line of the email.
            msg_html: The HTML message of the email.
            msg_plain: The plain text alternate message of the email. This is
                often displayed on slow or old browsers, or if the HTML message
                is not provided.
            cc: The list of email addresses to be cc'd.
            bcc: The list of email addresses to be bcc'd.
            attachments: The list of attachment file names.
            signature: Whether the account signature should be added to the
                message.
            user_id: The address of the sending account. 'me' for the
                default address associated with the account.
            reply_to: The id of the message that this email replies to.

        Returns:
            The Message object representing the sent message.

        Raises:
            googleapiclient.errors.HttpError: There was an error executing the
                HTTP request.

        """

        msg = self._create_message(
            sender,
            to,
            subject,
            msg_html,
            msg_plain,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            signature=signature,
            user_id=user_id,
            reply_to=reply_to,
        )

        try:
            req = self.service.users().messages().send(userId="me", body=msg)
            res = req.execute()
            return self._build_message_from_ref(user_id, res, "reference")

        except HttpError as error:
            # Pass along the error
            raise error

    def get_messages(
        self,
        user_id: str = "me",
        labels: Optional[List[Label]] = None,
        query: str = "",
        max_results: int = 100,
        attachments: str = "reference",
        include_spam_trash: bool = False,
    ) -> List[Message]:
        """
        Gets messages from your account.

        Args:
            user_id: the user's email address. Default 'me', the authenticated
                user.
            labels: label IDs messages must match.
            query: a Gmail query to match.
            max_results: Maximum number of messages to return. This field defaults to 100.
            attachments: accepted values are 'ignore' which completely
                ignores all attachments, 'reference' which includes attachment
                information but does not download the data, and 'download' which
                downloads the attachment data to store locally. Default
                'reference'.
            include_spam_trash: whether to include messages from spam or trash.

        Returns:
            A list of message objects.

        Raises:
            googleapiclient.errors.HttpError: There was an error executing the
                HTTP request.

        """

        if labels is None:
            labels = []

        labels_ids = [lbl.id if isinstance(lbl, Label) else lbl for lbl in labels]

        try:
            page_token = None
            remaining = max_results
            message_refs = []

            while remaining > 0:
                retrieve_count = min(500, remaining)

                response = (
                    self.service.users()
                    .messages()
                    .list(
                        userId=user_id,
                        q=query,
                        labelIds=labels_ids,
                        maxResults=retrieve_count,
                        includeSpamTrash=include_spam_trash,
                        pageToken=page_token,
                    )
                    .execute()
                )

                if "messages" in response:  # ensure request was successful
                    message_refs.extend(response["messages"])

                page_token = response.get("nextPageToken")
                remaining -= retrieve_count

                if not page_token:
                    break

            return self._get_messages_from_refs(
                user_id,
                message_refs,
                attachments,
            )

        except HttpError as error:
            # Pass along the error
            raise error

    def add_labels(self, message: Message, labels: List[Label]):
        """
        Add labels to a message's context

        Args:
            message: The message to add labels to
            labels: A list of labels to add

        Raises:
            googleapiclient.errors.HttpError: There was an error executing the
                HTTP request.
        """
        try:
            self.service.users().threads().modify(
                userId="me",
                id=message.thread_id,
                body={"addLabelIds": [lbl.id for lbl in labels]},
            ).execute()
        except HttpError as error:
            # Pass along the error
            raise error

    def remove_labels(self, message: Message, labels: List[Label]):
        """
        Remove labels from a message's context

        Args:
            message: The message to remove labels from
            labels: A list of labels to remove

        Raises:
            googleapiclient.errors.HttpError: There was an error executing the
                HTTP request.
        """
        try:
            self.service.users().threads().modify(
                userId="me",
                id=message.thread_id,
                body={"removeLabelIds": [lbl.id for lbl in labels]},
            ).execute()
        except HttpError as error:
            # Pass along the error
            raise error

    def get_message_by_id(self, message_id: str):
        """
        Get an email message using the given id

        Args:
            message_id: message id

        Returns:
            The Message object

        Raises:
            googleapiclient.errors.HttpError: There was an error executing the
                HTTP request.
        """

        try:
            res = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id)
                .execute()
            )
            return self._build_message_from_ref(
                user_id="me", message_ref=res, attachments="reference"
            )
        except HttpError as error:
            # Pass along the error
            raise error
