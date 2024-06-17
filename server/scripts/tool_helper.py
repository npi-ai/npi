import ast
import argparse


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


def _validate_tool(code, main_class: str):
    node = ast.parse(code)
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


if __name__ == '__main__':
    argP = argparse.ArgumentParser(description="Validate NPi Tool source code")

    argP.add_argument('--source', type=str, help="tool source code file")
    argP.add_argument('--class_name', type=str, help="main class to NPi Tool")

    args = argP.parse_args()
    with open(args.source, 'r') as f:
        source_code = f.read()
    _validate_tool(source_code, args.class_name)
    print('Validation passed')
