import ast
from string import Template

class ToolParser(ast.NodeVisitor):
    def __init__(self):
        self.imports = {}
        self.app_class = {}
        self.functions = {}
        self.module = ''

    def visit_Import(self, node):
        for alias in node.names:
            self.imports[alias.name] = alias.asname or alias.name
        # Continue visiting other nodes
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module
        for alias in node.names:
            if module == '__future__':
                continue
            imported_name = f"{module}.{alias.name}"
            self.imports[imported_name] = alias.asname or alias.name
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        print(f'Class: {node.name}')
        if node.bases:
            base_names = [self.get_name(base) for base in node.bases]
            for name in base_names:
                if name not in self.app_class:
                    self.app_class[name] = []
                self.app_class[name].append(node.name)
        # Continue visiting child nodes like methods inside the class
        self.generic_visit(node)

    def get_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self.get_name(node.func) + f'({", ".join(self.get_name(arg) for arg in node.args)})'
        return '<unknown>'

    def visit_FunctionDef(self, node):
        if node.decorator_list:
            for decorator in node.decorator_list:
                decorator_name = self.get_name(decorator)
                if decorator_name not in self.functions:
                    self.functions[decorator_name] = []
                self.functions[decorator_name].append(node.name)
        self.generic_visit(node)

def validate_tool(source_code):
    node = ast.parse(source_code)
    parser = ToolParser()
    parser.visit(node)

    if 'npiai.App' not in parser.imports:
        raise ValueError('No import statement found for npiai.App')

    module = parser.imports['npiai.App']
    if parser.app_class.get('App') is None or len(parser.app_class['App']) == 0:
        raise ValueError('No class extends npiai.App found in the file')

    main_class = 'GitHub'
    classes = parser.app_class['App']
    if main_class not in parser.app_class['App']:
        raise ValueError(f'No class named {main_class} found in {filename}')

    npi_functions = []

    if 'npiai.function' not in parser.imports:
        raise ValueError(f'No import statement found for npiai.function')

    module = parser.imports['npiai.function']
    if module not in parser.functions or len(parser.functions[module]) == 0:
        raise ValueError('No function that decorated with npiai.function found')

    print(f'Found {len(parser.functions[module])} functions decorated with npiai.function')


pyproject_template = Template(
"""
[tool.poetry]
$POETRY_METADATA

[tool.poetry.dependencies]
$POETRY_DEPENDENCIES

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
""")


dockerfile_template = Template(
"""
FROM npiai/python:3.11
COPY . /npiai/app

WORKDIR /npiai/app
unzip $ZIP_FILE
poetry install

ENV MAIN_FILE=/npiai/app/$MAIN_FILE
ENV MAIN_CLASS=$MAIN_CLASS

ENTRYPOINT ["python", "/npiai/app/main.py"]
""")

def main():
    # 1. check tool.yml

    # 2. check source code
    file = '/Users/wenfeng/workspace/npi-ai/npi/npiai/app/github/app.py'
    with open(file, 'r') as f:
        validate_tool(f.read())


    # 3. generate pyproject.yml
    metadata = {
        'name': 'npiai',
        'version': '0.1.0',
        'description': 'NPI AI Tool',
        'authors': ['NPI AI'],
    }
    dependencies = {
        'npiai': '0.1.0',
    }
    message = pyproject_template.substitute(
        POETRY_METADATA='\n'.join([f'{k} = "{v}"' for k, v in metadata.items()]),
        POETRY_DEPENDENCIES='\n'.join([f'{k} = "{v}"' for k, v in dependencies.items()])
    )

    print(message)

    # 4. generate Dockerfile

    message = dockerfile_template.substitute(
        ZIP_FILE='app.zip',
        MAIN_FILE='app.py',
        MAIN_CLASS='GitHub'
    )

    print(message)

    # 5. zip and upload to s3

    # 6. update db status



if __name__ == '__main__':
    main()