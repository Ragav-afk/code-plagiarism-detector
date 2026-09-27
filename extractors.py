"""
Block extraction: split a file into functions/methods so they can be compared block by block.
Python uses the built-in ast module; Java, C, C++ and JavaScript use tree-sitter parsers.
Nested functions stay inside their parent's block (no double counting).
"""
import ast
import os

# ---------- Python (ast) ----------

def _extract_python(code_text):
    try:
        tree = ast.parse(code_text)
    except SyntaxError:
        return []
    func_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    out = []

    def visit_body(body, prefix):
        for node in body:
            if isinstance(node, func_types):
                out.append((prefix + node.name, ast.unparse(node)))
            elif isinstance(node, ast.ClassDef):
                visit_body(node.body, prefix + node.name + ".")
            elif isinstance(node, ast.If):           # e.g. functions inside if __name__ == "__main__":
                visit_body(node.body, prefix)
                visit_body(node.orelse, prefix)

    visit_body(tree.body, "")
    return out


# ---------- Java / C / C++ / JavaScript (tree-sitter) ----------

_TS = {}          # extension -> (parser, function node types, class node types)
_TS_ERROR = None  # set if tree-sitter is not installed

try:
    from tree_sitter import Language, Parser
    import tree_sitter_java, tree_sitter_c, tree_sitter_cpp, tree_sitter_javascript

    def _mk(mod):
        return Parser(Language(mod.language()))

    _java = (_mk(tree_sitter_java), {'method_declaration', 'constructor_declaration'},
             {'class_declaration', 'interface_declaration', 'enum_declaration', 'record_declaration'})
    _c = (_mk(tree_sitter_c), {'function_definition'}, set())
    _cpp = (_mk(tree_sitter_cpp), {'function_definition'}, {'class_specifier', 'struct_specifier'})
    _js = (_mk(tree_sitter_javascript), {'function_declaration', 'method_definition'}, {'class_declaration'})
    _TS = {'.java': _java, '.c': _c, '.h': _c, '.cpp': _cpp, '.cc': _cpp, '.hpp': _cpp, '.js': _js}
except Exception as e:  # tree-sitter missing: file-level comparison still works
    _TS_ERROR = str(e)

_NAME_TYPES = {'identifier', 'field_identifier', 'qualified_identifier', 'operator_name',
               'destructor_name', 'property_identifier', 'type_identifier'}


def _node_name(node):
    name = node.child_by_field_name('name')
    if name is not None:
        return name.text.decode('utf-8', 'replace')
    # C/C++: the name is buried in declarator -> declarator -> ... -> identifier
    d = node.child_by_field_name('declarator')
    while d is not None and d.type not in _NAME_TYPES:
        nxt = d.child_by_field_name('declarator')
        if nxt is None:
            nxt = next((c for c in d.named_children
                        if c.type in _NAME_TYPES or c.type.endswith('declarator')), None)
        d = nxt
    return d.text.decode('utf-8', 'replace') if d is not None else '<anonymous>'


def _extract_tree_sitter(code_text, ext):
    parser, func_types, class_types = _TS[ext]
    src = code_text.encode('utf-8', 'replace')
    tree = parser.parse(src)
    out = []

    def walk(node, prefix):
        for child in node.named_children:
            if child.type in func_types:
                out.append((prefix + _node_name(child),
                            src[child.start_byte:child.end_byte].decode('utf-8', 'replace')))
                # do not descend: nested/local functions stay in the parent block
            elif child.type in class_types:
                walk(child, prefix + _node_name(child) + ".")
            else:
                walk(child, prefix)

    walk(tree.root_node, "")
    return out


def extract_functions(code_text, filename="x.py"):
    """Return list of (block_name, source) for one file. [] if unsupported or unparseable."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.py':
        return _extract_python(code_text)
    if ext in _TS:
        try:
            return _extract_tree_sitter(code_text, ext)
        except Exception:
            return []
    return []
