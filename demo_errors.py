from interpreter import Interpreter

i = Interpreter()

print("=== 範例1：Runtime 錯誤（除以零）===")
i.exec_interactive('int x = 10;\nint y = 0;\nprintf("%d\\n", x / y);')

print()
print("=== 範例2：語法錯誤（缺少表達式）===")
i.exec_interactive('int bad = ;')

print()
print("=== 範例3：陣列越界 ===")
i.exec_interactive('int arr[3];\narr[0] = 1;\narr[5] = 99;')

print()
print("=== 範例4：程式中的 ParseError ===")
src = """\
int main() {
    int x = 10;
    printf("%d\\n", x +++ );
    return 0;
}"""
i.run_program(src, src.split('\n'))
