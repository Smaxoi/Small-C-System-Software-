#!/usr/bin/env python3
"""
test_runner.py — Small-C 直譯器自動化測試
執行方式: python test_runner.py
"""
import sys
import io
import os

# 強制 UTF-8 輸出（Windows cp950 不支援 emoji）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 把上層目錄加入 path，以便找到 interpreter.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interpreter import Interpreter

# ── 顏色輸出 ──────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ── 統計 ──────────────────────────────────────────────────────────────────────
_pass = 0
_fail = 0


# ── 執行器 ────────────────────────────────────────────────────────────────────

def _capture(fn):
    """Run fn() with stdout redirected; return captured text."""
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        fn()
    finally:
        sys.stdout = old
    return buf.getvalue()


def run_interactive(code: str) -> str:
    """Run code via exec_interactive on a fresh interpreter."""
    interp = Interpreter()
    return _capture(lambda: interp.exec_interactive(code)).strip()


def run_program(source: str) -> str:
    """Run a full program; strip the 'Program exited' trailer."""
    interp = Interpreter()
    raw = _capture(lambda: interp.run_program(source))
    lines = [l for l in raw.splitlines()
             if not l.startswith("Program exited")]
    return '\n'.join(lines).strip()


def run_program_raw(source: str) -> str:
    """Run a full program; keep all output including exit line."""
    interp = Interpreter()
    return _capture(lambda: interp.run_program(source)).strip()


# ── 斷言輔助 ──────────────────────────────────────────────────────────────────

def check(name: str, got: str, expected: str):
    global _pass, _fail
    got_s = got.strip()
    exp_s = expected.strip()
    if got_s == exp_s:
        print(f"  {GREEN}✅ PASS{RESET}  {name}")
        _pass += 1
    else:
        print(f"  {RED}❌ FAIL{RESET}  {name}")
        exp_lines = exp_s.splitlines()
        got_lines = got_s.splitlines()
        max_w = max((len(l) for l in exp_lines), default=0)
        print(f"       {'期望':^{max(max_w,8)}}   {'得到'}")
        for i in range(max(len(exp_lines), len(got_lines))):
            e = exp_lines[i] if i < len(exp_lines) else "(缺行)"
            g = got_lines[i] if i < len(got_lines) else "(缺行)"
            mark = " " if e == g else f"{RED}≠{RESET}"
            print(f"       {mark} {repr(e):<40}  {repr(g)}")
        _fail += 1


def section(title: str):
    print(f"\n{BOLD}{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*55}{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
#  測試組
# ══════════════════════════════════════════════════════════════════════════════

def test_arithmetic():
    section("【算術運算】")
    check("加法",        run_interactive('printf("%d\\n", 3 + 4);'),          "7")
    check("減法",        run_interactive('printf("%d\\n", 10 - 3);'),         "7")
    check("乘法",        run_interactive('printf("%d\\n", 6 * 7);'),          "42")
    check("乘法優先級",   run_interactive('printf("%d\\n", 3 + 4 * 5);'),     "23")
    check("括號優先",    run_interactive('printf("%d\\n", (3 + 4) * 5);'),    "35")
    check("整數除法",    run_interactive('printf("%d\\n", 17 / 5);'),          "3")
    check("取餘數",      run_interactive('printf("%d\\n", 17 % 5);'),          "2")
    check("負數除法",    run_interactive('printf("%d\\n", -15 / 4);'),         "-3")
    check("複合算術",    run_interactive('printf("%d\\n", 3 + 4 * 5 - 2);'),  "21")
    check("一元負號",    run_interactive('printf("%d\\n", -(3 + 4));'),        "-7")


def test_relational_logical():
    section("【關係 / 邏輯 / 位元運算】")
    check("大於(真)",    run_interactive('printf("%d\\n", 10 > 5);'),   "1")
    check("大於(假)",    run_interactive('printf("%d\\n", 5 > 10);'),   "0")
    check("等於",        run_interactive('printf("%d\\n", 7 == 7);'),   "1")
    check("不等於",      run_interactive('printf("%d\\n", 7 != 8);'),   "1")
    check("邏輯AND(假)", run_interactive('printf("%d\\n", 10 > 5 && 3 < 1);'), "0")
    check("邏輯OR(真)",  run_interactive('printf("%d\\n", 10 > 5 || 3 < 1);'), "1")
    check("邏輯NOT",     run_interactive('printf("%d\\n", !0);'),        "1")
    check("位元AND",     run_interactive('printf("%d\\n", 0xAB & 0x0F);'), "11")
    check("位元OR",      run_interactive('printf("%d\\n", 0xF0 | 0x0D);'), "253")
    check("位元XOR",     run_interactive('printf("%d\\n", 0xFF ^ 0x0F);'), "240")
    check("左移",        run_interactive('printf("%d\\n", 1 << 10);'),    "1024")
    check("右移",        run_interactive('printf("%d\\n", 1024 >> 2);'),  "256")
    check("位元NOT",     run_interactive('printf("%d\\n", ~0 & 0xFF);'),  "255")


def test_variables():
    section("【變數宣告與賦值】")
    check("int宣告",
          run_interactive('int x = 42; printf("%d\\n", x);'),
          "42")
    check("char宣告",
          run_interactive("char c = 'A'; printf(\"%c %d\\n\", c, c);"),
          "A 65")
    check("+=運算子",
          run_interactive('int x = 10; x += 5; printf("%d\\n", x);'),
          "15")
    check("-=運算子",
          run_interactive('int x = 10; x -= 3; printf("%d\\n", x);'),
          "7")
    check("*=運算子",
          run_interactive('int x = 4; x *= 3; printf("%d\\n", x);'),
          "12")
    check("前置++",
          run_interactive('int x = 5; printf("%d\\n", ++x);'),
          "6")
    check("後置++",
          run_interactive('int x = 5; printf("%d %d\\n", x++, x);'),
          "5 6")
    check("前置--",
          run_interactive('int x = 5; printf("%d\\n", --x);'),
          "4")
    check("多重宣告",
          run_interactive('int a = 1; int b = 2; int c = a + b; printf("%d\\n", c);'),
          "3")


def test_math_builtins():
    section("【數學內建函式】")
    check("abs正數",    run_interactive('printf("%d\\n", abs(42));'),       "42")
    check("abs負數",    run_interactive('printf("%d\\n", abs(-99));'),      "99")
    check("max",        run_interactive('printf("%d\\n", max(10, 20));'),   "20")
    check("min",        run_interactive('printf("%d\\n", min(10, 20));'),   "10")
    check("pow",        run_interactive('printf("%d\\n", pow(2, 10));'),    "1024")
    check("sqrt",       run_interactive('printf("%d\\n", sqrt(144));'),     "12")
    check("pow(3,3)",   run_interactive('printf("%d\\n", pow(3, 3));'),     "27")


def test_string_builtins():
    section("【字串內建函式】")
    check("strlen",
          run_interactive('printf("%d\\n", strlen("Hello"));'), "5")
    check("strcpy+strcmp",
          run_interactive(
              'char buf[20]; strcpy(buf, "abc"); '
              'printf("%d\\n", strcmp(buf, "abc"));'),
          "0")
    check("strcat",
          run_interactive(
              'char s[30]; strcpy(s, "Hello"); strcat(s, " World");'
              'printf("%s\\n", s);'),
          "Hello World")
    check("atoi",
          run_interactive('printf("%d\\n", atoi("2026"));'), "2026")
    check("itoa",
          run_interactive(
              'char buf[20]; itoa(99, buf); printf("%s\\n", buf);'),
          "99")
    check("substr",
          run_interactive(
              'char dst[10]; substr(dst, "Hello World", 6, 5);'
              'printf("%s\\n", dst);'),
          "World")
    check("strcmp大於",
          run_interactive('printf("%d\\n", strcmp("b","a") > 0);'), "1")
    check("strlen空字串",
          run_interactive('printf("%d\\n", strlen(""));'), "0")


def test_control_flow():
    section("【控制流程】")

    # if/else
    check("if-true",
          run_interactive('int x = 10; if (x > 5) printf("yes\\n"); else printf("no\\n");'),
          "yes")
    check("if-false",
          run_interactive('int x = 3; if (x > 5) printf("yes\\n"); else printf("no\\n");'),
          "no")

    # while
    check("while迴圈",
          run_interactive(
              'int i = 0; int s = 0;'
              'while (i < 5) { s += i; i++; }'
              'printf("%d\\n", s);'),
          "10")

    # for
    check("for迴圈",
          run_interactive(
              'int s = 0; int i;'
              'for (i = 1; i <= 10; i++) s += i;'
              'printf("%d\\n", s);'),
          "55")

    # do-while
    check("do-while",
          run_interactive(
              'int n = 1; int s = 0;'
              'do { s += n; n++; } while (n <= 5);'
              'printf("%d\\n", s);'),
          "15")

    # break
    check("break",
          run_interactive(
              'int i;'
              'for (i = 0; i < 10; i++) { if (i == 5) break; }'
              'printf("%d\\n", i);'),
          "5")

    # continue
    check("continue(跳過偶數)",
          run_interactive(
              'int i; int s = 0;'
              'for (i = 1; i <= 10; i++) {'
              '  if (i % 2 == 0) continue; s += i;'
              '}'
              'printf("%d\\n", s);'),
          "25")

    # nested if
    check("巢狀if",
          run_interactive(
              'int x = 7;'
              'if (x > 5) { if (x > 10) printf("big\\n"); '
              '             else printf("mid\\n"); }'
              'else printf("small\\n");'),
          "mid")


def test_arrays():
    section("【陣列】")
    check("陣列讀寫",
          run_interactive(
              'int arr[5]; arr[0]=10; arr[4]=99;'
              'printf("%d %d\\n", arr[0], arr[4]);'),
          "10 99")
    check("陣列迴圈加總",
          run_interactive(
              'int a[5]; int i; int s = 0;'
              'a[0]=1; a[1]=2; a[2]=3; a[3]=4; a[4]=5;'
              'for (i=0;i<5;i++) s += a[i];'
              'printf("%d\\n", s);'),
          "15")
    check("char陣列",
          run_interactive(
              'char name[6]; strcpy(name, "Alice");'
              'printf("%s\\n", name);'),
          "Alice")
    check("#define陣列大小",
          run_interactive(
              '#define N 4\n'
              'int arr[N]; int i;'
              'for(i=0;i<N;i++) arr[i]=i*i;'
              'printf("%d %d %d %d\\n", arr[0],arr[1],arr[2],arr[3]);'),
          "0 1 4 9")


def test_functions():
    section("【函式 / 遞迴】")

    check("簡單函式",
          run_program(
              'int add(int a, int b) { return a + b; }\n'
              'int main() { printf("%d\\n", add(3, 4)); return 0; }'),
          "7")

    check("void函式",
          run_program(
              'void greet(int n) { printf("Hi %d\\n", n); }\n'
              'int main() { greet(42); return 0; }'),
          "Hi 42")

    check("遞迴階乘",
          run_program(
              'int fact(int n) {\n'
              '  if (n <= 1) return 1;\n'
              '  return n * fact(n - 1);\n'
              '}\n'
              'int main() { printf("%d\\n", fact(6)); return 0; }'),
          "720")

    check("遞迴Fibonacci",
          run_program(
              'int fib(int n) {\n'
              '  if (n <= 1) return n;\n'
              '  return fib(n-1) + fib(n-2);\n'
              '}\n'
              'int main() { printf("%d\\n", fib(10)); return 0; }'),
          "55")

    check("GCD(遞迴)",
          run_program(
              'int gcd(int a, int b) {\n'
              '  if (b == 0) return a;\n'
              '  return gcd(b, a % b);\n'
              '}\n'
              'int main() { printf("%d\\n", gcd(48, 18)); return 0; }'),
          "6")

    check("多個函式互呼叫",
          run_program(
              'int square(int x) { return x * x; }\n'
              'int sum_sq(int a, int b) { return square(a) + square(b); }\n'
              'int main() { printf("%d\\n", sum_sq(3, 4)); return 0; }'),
          "25")


def test_pointers():
    section("【指標】")

    check("指標基本讀寫",
          run_program(
              'void set(int *p, int v) { *p = v; }\n'
              'int main() {\n'
              '  int x = 0; set(&x, 99);\n'
              '  printf("%d\\n", x);\n'
              '  return 0;\n'
              '}'),
          "99")

    check("swap函式",
          run_program(
              'void swap(int *a, int *b) {\n'
              '  int t = *a; *a = *b; *b = t;\n'
              '}\n'
              'int main() {\n'
              '  int x = 10; int y = 20;\n'
              '  swap(&x, &y);\n'
              '  printf("%d %d\\n", x, y);\n'
              '  return 0;\n'
              '}'),
          "20 10")

    check("陣列傳指標",
          run_program(
              'int sum(int *arr, int n) {\n'
              '  int i; int s = 0;\n'
              '  for (i=0; i<n; i++) s += arr[i];\n'
              '  return s;\n'
              '}\n'
              'int main() {\n'
              '  int a[4];\n'
              '  a[0]=1; a[1]=2; a[2]=3; a[3]=4;\n'
              '  printf("%d\\n", sum(a, 4));\n'
              '  return 0;\n'
              '}'),
          "10")


def test_printf_formats():
    section("【printf 格式化】")
    check("%d",  run_interactive('printf("%d\\n", 42);'),          "42")
    check("%c",  run_interactive("printf(\"%c\\n\", 'A');"),        "A")
    check("%s",  run_interactive('printf("%s\\n", "hello");'),      "hello")
    check("%x",  run_interactive('printf("%x\\n", 255);'),          "ff")
    check("%o",  run_interactive('printf("%o\\n", 8);'),            "10")
    check("多參數", run_interactive('printf("%d + %d = %d\\n", 3, 4, 7);'), "3 + 4 = 7")
    check("寬度%5d",   run_interactive('printf("%5d\\n", 42);'),       "   42")
    check("%-5d左對齊", run_interactive('printf("%-5d|\\n", 42);'),  "42   |")


def test_error_handling():
    global _pass, _fail
    section("【錯誤處理（錯了要報錯，不能崩潰）】")

    def run_and_check_error(name, code, keyword):
        """確認輸出中含有 keyword（錯誤訊息的關鍵字）。"""
        global _pass, _fail  # noqa: PLW0603
        got = run_interactive(code)
        if keyword.lower() in got.lower():
            print(f"  {GREEN}✅ PASS{RESET}  {name}  ({YELLOW}報錯:{RESET} ...{keyword}...)")
            _pass += 1
        else:
            print(f"  {RED}❌ FAIL{RESET}  {name}")
            print(f"       期望包含: {repr(keyword)}")
            print(f"       得到:     {repr(got)}")
            _fail += 1

    run_and_check_error("除以零",        'printf("%d\\n", 10 / 0);',           "Division by zero")
    run_and_check_error("對零取餘",       'printf("%d\\n", 10 % 0);',           "zero")
    run_and_check_error("sqrt負數",      'printf("%d\\n", sqrt(-1));',          "non-negative")
    run_and_check_error("陣列越界",
                        'int a[3]; a[5] = 0;',                                "out of bounds")
    run_and_check_error("語法錯誤-缺分號",  'int x = ;',                        "error")
    run_and_check_error("語法錯誤-缺閉括號", 'printf("%d\\n", (1 + 2;',         "error")

    # 確認錯誤後直譯器仍可繼續使用
    interp = Interpreter()
    buf = io.StringIO()
    old = sys.stdout; sys.stdout = buf
    interp.exec_interactive('printf("%d\\n", 1 / 0);')
    interp.exec_interactive('printf("alive\\n");')
    sys.stdout = old
    out = buf.getvalue()
    if "alive" in out:
        print(f"  {GREEN}✅ PASS{RESET}  錯誤後繼續執行")
        _pass += 1
    else:
        print(f"  {RED}❌ FAIL{RESET}  錯誤後繼續執行（直譯器崩潰了）")
        _fail += 1


def test_define():
    section("【#define 常數】")
    check("#define整數",
          run_interactive('#define SIZE 5\nprintf("%d\\n", SIZE);'),
          "5")
    check("#define用於陣列",
          run_interactive(
              '#define N 3\nint a[N];\n'
              'a[0]=10; a[1]=20; a[2]=30;\n'
              'printf("%d\\n", a[N-1]);'),
          "30")
    check("#define用於條件",
          run_interactive(
              '#define LIMIT 10\n'
              'int i; int s=0;\n'
              'for(i=1;i<=LIMIT;i++) s+=i;\n'
              'printf("%d\\n",s);'),
          "55")


def test_char_operations():
    section("【char 字元操作】")
    check("char加法",
          run_interactive("char c = 'A'; printf(\"%c\\n\", c + 1);"), "B")
    check("toupper",
          run_interactive("printf(\"%c\\n\", toupper('a'));"), "A")
    check("tolower",
          run_interactive("printf(\"%c\\n\", tolower('Z'));"), "z")
    check("isalpha",
          run_interactive("printf(\"%d %d\\n\", isalpha('a'), isalpha('1'));"), "1 0")
    check("isdigit",
          run_interactive("printf(\"%d %d\\n\", isdigit('5'), isdigit('x'));"), "1 0")


def test_selection_sort():
    section("【完整程式：Selection Sort】")
    prog = '''\
#define SIZE 5

void swap(int *a, int *b) {
    int t;
    t = *a; *a = *b; *b = t;
}

void sort(int *arr, int n) {
    int i; int j; int m;
    for (i = 0; i < n - 1; i = i + 1) {
        m = i;
        for (j = i + 1; j < n; j = j + 1)
            if (arr[j] < arr[m]) m = j;
        if (m != i) swap(&arr[i], &arr[m]);
    }
}

int main() {
    int a[SIZE];
    int i;
    a[0]=5; a[1]=3; a[2]=8; a[3]=1; a[4]=4;
    sort(a, SIZE);
    for (i = 0; i < SIZE; i = i + 1)
        printf("%d ", a[i]);
    printf("\\n");
    return 0;
}
'''
    check("排序結果", run_program(prog), "1 3 4 5 8")


# ══════════════════════════════════════════════════════════════════════════════
#  主程式
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print(f"\n{BOLD}Small-C 直譯器自動測試{RESET}")
    print(f"{'='*55}")

    test_arithmetic()
    test_relational_logical()
    test_variables()
    test_math_builtins()
    test_string_builtins()
    test_control_flow()
    test_arrays()
    test_functions()
    test_pointers()
    test_printf_formats()
    test_error_handling()
    test_define()
    test_char_operations()
    test_selection_sort()

    total = _pass + _fail
    pct   = int(_pass / total * 100) if total else 0

    print(f"\n{BOLD}{'='*55}{RESET}")
    print(f"{BOLD}測試結果：{_pass}/{total} 通過（{pct}%）{RESET}")
    if _fail == 0:
        print(f"{GREEN}{BOLD}🎉 全部通過！{RESET}")
    else:
        print(f"{RED}{BOLD}⚠️  {_fail} 個測試失敗，請查看上方的錯誤訊息。{RESET}")
    print()

    sys.exit(0 if _fail == 0 else 1)
