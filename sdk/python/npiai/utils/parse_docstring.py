from docstring_parser.google import GoogleParser, DEFAULT_SECTIONS, Section, SectionType

NPI_SECTIONS = [
    *DEFAULT_SECTIONS,
    Section('Few Shots', 'few_shots', SectionType.SINGULAR),
    Section('Few shots', 'few_shots', SectionType.SINGULAR),
    Section('few shots', 'few_shots', SectionType.SINGULAR),
    Section('Few Shot', 'few_shots', SectionType.SINGULAR),
    Section('Few shot', 'few_shots', SectionType.SINGULAR),
    Section('few shot', 'few_shots', SectionType.SINGULAR),
]


def parse_docstring(docstring: str):
    return GoogleParser(sections=NPI_SECTIONS).parse(docstring)
