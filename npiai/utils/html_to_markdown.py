from markdownify import MarkdownConverter


class CompactMarkdownConverter(MarkdownConverter):
    def convert_img(self, el, text, convert_as_inline):
        src = el.attrs.get("src", "")

        if not src:
            return ""

        if src.startswith("data:image"):
            el.attrs["src"] = "<base64_image>"

        return super().convert_img(el, text, convert_as_inline)

    def convert_noscript(self, el, text, convert_as_inline):
        return ""

    def convert_div(self, el, text, convert_as_inline):
        aria_label = el.attrs.get("aria-label", "")

        if aria_label and aria_label not in text:
            # print(f"{aria_label=} {text=} {el=}\n\n")
            return f"\n{text.rstrip()} (aria-label: {aria_label})"

        return text.rstrip() + " " if text else ""

        #
        # if text:
        #     text = text.strip("\n")
        #
        # if convert_as_inline or not text:
        #     return text
        #
        # return f"{text}\n"


def html_to_markdown(html: str, **options) -> str:
    return CompactMarkdownConverter(**options).convert(html).strip()
