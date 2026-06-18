#!/usr/bin/env python3
"""Test tree-sitter installation."""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Python version:", sys.version)

import tree_sitter
print("tree-sitter version:", tree_sitter.__version__)

try:
    import tree_sitter_cpp
    print("tree-sitter-cpp installed")
    cpp_lang = tree_sitter_cpp.language()
    print("Got cpp language object:", cpp_lang)
    
    try:
        lang1 = tree_sitter.Language(cpp_lang)
        print("tree_sitter.Language(cpp_lang) worked")
    except Exception as e1:
        print("tree_sitter.Language(cpp_lang) failed:", type(e1), e1)
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print("tree-sitter-cpp failed:", type(e), e)

try:
    import tree_sitter_java
    print("\ntree-sitter-java installed")
except Exception as e:
    print("tree-sitter-java failed:", type(e), e)

print("\nDone")
