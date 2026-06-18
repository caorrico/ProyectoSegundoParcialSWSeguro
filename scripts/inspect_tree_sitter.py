#!/usr/bin/env python3
"""Inspect tree-sitter module contents."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import tree_sitter
print("Tree-sitter module contents:", dir(tree_sitter))

print("\nLooking for Language class:")
print(hasattr(tree_sitter, 'Language'))
if hasattr(tree_sitter, 'Language'):
    print("Language class found. Signature:", tree_sitter.Language.__init__.__annotations__)

import inspect
if hasattr(tree_sitter, 'Language'):
    print(inspect.signature(tree_sitter.Language.__init__))

import tree_sitter_cpp
print("\ntree_sitter_cpp language() returns type:", type(tree_sitter_cpp.language()))
print("tree_sitter_cpp.language():", tree_sitter_cpp.language())

print("\nTrying to create Parser and just use set_language:")
try:
    parser = tree_sitter.Parser()
    cpp_lang = tree_sitter_cpp.language()
    parser.set_language(cpp_lang)
    print("SUCCESS: parser.set_language(cpp_lang) worked!")
    
    test_code = b"int main() { return 0; }"
    tree = parser.parse(test_code)
    print("SUCCESS: Parsed test code! Root node:", tree.root_node)
except Exception as e:
    print("ERROR:", type(e), str(e))
    import traceback
    traceback.print_exc()
