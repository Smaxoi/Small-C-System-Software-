"""Demo: MEMSHOW + colorized LIST"""
import sys, io, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from interpreter import Interpreter

print("=" * 60)
print("【MEMSHOW 測試】")
print("=" * 60)

interp = Interpreter()
interp.exec_interactive('#define SIZE 4')
interp.exec_interactive('int x = 42;')
interp.exec_interactive('int y = -7;')
interp.exec_interactive('char ch = 90;')         # 'Z'
interp.exec_interactive('int arr[SIZE];')
interp.exec_interactive('arr[0]=10; arr[1]=20; arr[2]=30; arr[3]=40;')
interp.exec_interactive('char buf[20];')
interp.exec_interactive('strcpy(buf, "Hello, World!");')
interp.exec_interactive('int *p;')
# point p at y
code = 'p = &y;'
interp.exec_interactive(code)
interp.show_memory(interp.global_scope)

print()
print("=" * 60)
print("【彩色 LIST 測試（raw ANSI 碼）】")
print("=" * 60)

# Test colorize directly
from main import _colorize
samples = [
    '#define SIZE 8',
    'void swap(int *a, int *b) {',
    '    int temp = *a;  // save a',
    '    *a = *b;',
    '    *b = temp;      /* restore */',
    '}',
    'int main() {',
    '    char buf[50];',
    '    strcpy(buf, "Hello World");',
    "    char c = 'Z';",
    '    int x = 0xFF;',
    '    printf("%d %s\\n", 42, buf);',
    '    return 0;',
    '}',
]

for i, line in enumerate(samples, 1):
    colored = _colorize(line)
    print(f"\033[90m{i:4d}:\033[0m {colored}")
