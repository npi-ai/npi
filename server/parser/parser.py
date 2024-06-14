import os
import ast
from string import Template
import yaml
from typing import List
import pydantic
import shutil
import secrets
import string
import boto3
import subprocess


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


def validate_tool(source_code, main_class: str, filename='main.py'):
    node = ast.parse(source_code)
    parser = ToolParser()
    parser.visit(node)

    if 'npiai.App' not in parser.imports:
        raise ValueError('No import statement found for npiai.App')
    if main_class not in parser.app_class['App'] or len(parser.app_class['App']) == 0:
        raise ValueError('No class extends npiai.App found in the file')

    if 'npiai.function' not in parser.imports:
        raise ValueError(f'No import statement found for npiai.function')
    module = parser.imports['npiai.function']
    if module not in parser.functions or len(parser.functions[module]) == 0:
        raise ValueError('No function that decorated with npiai.function found')

    print(f'Found {len(parser.functions[module])} functions decorated with npiai.function')


pyproject_template = Template(
    """[tool.poetry]
$POETRY_METADATA

[tool.poetry.dependencies]
$POETRY_DEPENDENCIES

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[virtualenvs]
create = true
in-project = true
""")

dockerfile_template = Template(
    """FROM npiai/python:3.11
COPY . /npiai/tools

RUN source /npiai/tools/.venv/bin/activate

ENTRYPOINT ["python", "/npiai/tools/main.py"]
""")


class ToolMetadata(pydantic.BaseModel):
    id: str
    name: str
    version: str
    description: str
    author: List[str]


entrypoint_template = Template(
    """import os
import sys
import importlib
import tokenize
import asyncio
import time

async def main():
    # Add the directory containing the file to sys.path
    module_dir, module_name = os.path.split('$MAIN_FILE')
    module_name = os.path.splitext(module_name)[0]  # Remove the .py extension

    if module_dir not in sys.path:
        sys.path.append(module_dir)

    # Now you can import the module using its name
    module = importlib.import_module(module_name)
    # Create an instance of the class
    tool_class = getattr(module, '$MAIN_CLASS')
    instance = tool_class()

    async with instance as i:
        # await i.wait() TODO add this method to BaseApp class
        time.sleep(1000)


if __name__ == '__main__':
    asyncio.run(main())
""")


def generate_secure_random_string(length):
    """
    Generate a secure random string of specified length.

    Args:
    length (int): Length of the secure random string to generate.

    Returns:
    str: The generated secure random string.
    """
    # Define the characters to choose from
    characters = string.ascii_letters + string.digits
    # Create a secure random string
    secure_random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return secure_random_string


tmp_dir = '/Users/wenfeng/tmp/build'

# Create an S3 client, credentials are stored in the environment
s3_client = boto3.client('s3')


def build(bucket: str, md: ToolMetadata):
    # 0. download source zip from S3
    root_dir = f'{tmp_dir}/{generate_secure_random_string(16)}'
    os.makedirs(root_dir, exist_ok=False)
    target_zip = f'{root_dir}/source.zip'

    s3_client.download_file(bucket, f'{md.id}/source.zip', target_zip)
    workdir = f'{root_dir}/source'
    shutil.unpack_archive(target_zip, workdir)

    # 1. check tool.yml
    with open('/'.join([workdir, 'npi.yml']), 'r') as f:
        tool = yaml.safe_load(f)

    if 'main' not in tool:
        raise ValueError('No main field specified in npi.yml')
    if 'class' not in tool:
        raise ValueError('No class field specified in npi.yml')

    # 2. check source code
    with open('/'.join([workdir, tool.get('main')]), 'r') as f:
        validate_tool(f.read(), tool.get('class'))

    # 3. generate pyproject.yml
    metadata = {
        'name': md.name,
        'version': md.version,
        'description': "NPi Tools created by NPi Cloud",
    }
    metadata_str = '\n'.join([f'{k} = "{v}"' for k, v in metadata.items()])
    authors = [f'"{a}"' for a in md.author]
    metadata_str = f'{metadata_str}\nauthors = [{", ".join(authors)}]'

    dependencies = {}
    for dep in tool['dependencies']:
        dependencies[dep['name']] = dep['version']
    message = pyproject_template.substitute(
        POETRY_METADATA=metadata_str,
        POETRY_DEPENDENCIES='\n'.join([f'{k} = "{v}"' for k, v in dependencies.items()])
    )
    with open('/'.join([workdir, 'pyproject.toml']), 'w') as f:
        f.write(message)

    # install dependencies to same directory
    result = subprocess.run('poetry install', cwd=workdir, shell=True, text=True, capture_output=True)

    if result:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return Code:", result.returncode)

    # 4. generate Dockerfile
    zip_file = f'{md.id}-{md.version}.zip'
    message = dockerfile_template.substitute(
        ZIP_FILE=zip_file,
        MAIN_FILE=f'/npiai/tools/{tool.get("main")}',
        MAIN_CLASS=tool.get('class'),
    )
    with open('/'.join([workdir, 'Dockerfile']), 'w') as f:
        f.write(message)

    # 5. generate entrypoint
    message = entrypoint_template.substitute(
        MAIN_FILE=f'/npiai/tools/{tool.get("main")}',
        MAIN_CLASS=tool.get('class'),
    )
    with open('/'.join([workdir, 'main.py']), 'w') as f:
        f.write(message)

    # 5. zip and upload to s3
    new_file = '/'.join([workdir, f'{md.id}-{md.version}'])
    shutil.make_archive(new_file, 'gztar', workdir)

    s3_client.upload_file(f'{new_file}.tar.gz', bucket, f'{md.id}/{md.version}/target.tar.gz')
    # build image here?

    # 6. TODO generate function.yml, need make export to be a static method

    # 7. clean up
    # shutil.rmtree(root_dir)


if __name__ == '__main__':
    # shutil.make_archive("source", 'zip', '/Users/wenfeng/workspace/npi-ai/npi/npiai/app/github')
    build(
        bucket='npiai-tools-build-test',
        md=ToolMetadata(
            id='github',
            name='github',
            version='0.1.0',
            description='GitHub Tool',
            author=['Wenfeng Wang'],
        ),
    )
