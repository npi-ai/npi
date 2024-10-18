from markdownify import MarkdownConverter


class CompactConverter(MarkdownConverter):
    def convert_img(self, el, text, convert_as_inline):
        src = el.attrs.get("src", "")

        if not src:
            return ""

        if src.startswith("data:image"):
            el.attrs["src"] = "<base64_image>"

        return super().convert_img(el, text, convert_as_inline)

    def convert_noscript(self, _el, _text, _convert_as_inline):
        return ""

    # def convert_div(self, el, text, convert_as_inline):
    #     if text:
    #         text = text.strip("\n")
    #
    #     if convert_as_inline or not text:
    #         return text
    #
    #     return f"{text}\n"


def html_to_markdown(html: str, **options) -> str:
    return CompactConverter(**options).convert(html).strip()
