from docstring_parser.google import GoogleParser, DEFAULT_SECTIONS, Section, SectionType

NPI_SECTIONS = [
    *DEFAULT_SECTIONS,
    Section("FewShots", "few_shots", SectionType.SINGULAR),
]


def parse_docstring(docstring: str):
    return GoogleParser(sections=NPI_SECTIONS).parse(docstring)
