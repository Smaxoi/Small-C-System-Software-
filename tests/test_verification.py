#!/usr/bin/env python3
"""
test_verification.py — 對應評分標準 Test A 的自動化驗收測試
對應文件: 期末專題-Small-C 互動式解譯器評分標準-學生版.md
執行方式: python test_verification.py
"""
import sys
import io
import os
from itertools import zip_longest

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 把上層目錄加入 path，以便找到 interpreter.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interpreter import Interpreter

HERE   = os.path.dirname(os.path.abspath(__file__))
GREEN  = "\033[92m"; RED    = "\033[91m"; YELLOW = "\033[93m"
CYAN   = "\033[96m"; RESET  = "\033[0m";  BOLD   = "\033[1m"; DIM = "\033[90m"

_pass = _fail = 0


# ── 輔助工具 ──────────────────────────────────────────────────────────────────

def _capture(fn):
    buf = io.StringIO()
    old, sys.stdout = sys.stdout, buf
    try:
        fn()
    finally:
        sys.stdout = old
    return buf.getvalue()


def normalize(s):
    """每行去除尾端空白，整體去除前後空行。"""
    return '\n'.join(ln.rstrip() for ln in s.splitlines()).strip()


def run_interactive(code: str) -> str:
    interp = Interpreter()
    return normalize(_capture(lambda: interp.exec_interactive(code)))


def run_program(src: str) -> str:
    """執行完整程式，移除 'Program exited' 那行。"""
    interp = Interpreter()
    raw = _capture(lambda: interp.run_program(src))
    lines = [l for l in raw.splitlines() if not l.startswith("Program exited")]
    return normalize('\n'.join(lines))


def load_c(filename: str) -> str:
    path = os.path.join(HERE, filename)
    return open(path, encoding='utf-8').read()


def check(name: str, got: str, expected: str):
    global _pass, _fail
    g, e = normalize(got), normalize(expected)
    if g == e:
        print(f"  {GREEN}✅ PASS{RESET}  {name}")
        _pass += 1
    else:
        print(f"  {RED}❌ FAIL{RESET}  {name}")
        e_lines = e.splitlines()
        g_lines = g.splitlines()
        for el, gl in zip_longest(e_lines, g_lines, fillvalue="(缺行)"):
            mark = " " if el == gl else f"{RED}≠{RESET}"
            print(f"         {mark} 期望: {repr(el)}")
            if el != gl:
                print(f"           得到: {repr(gl)}")
        _fail += 1


def check_contains(name: str, got: str, keyword: str):
    global _pass, _fail
    if keyword.lower() in got.lower():
        print(f"  {GREEN}✅ PASS{RESET}  {name}  {DIM}(含 '{keyword}'){RESET}")
        _pass += 1
    else:
        print(f"  {RED}❌ FAIL{RESET}  {name}  {DIM}(未含 '{keyword}'，得到: {repr(got[:80])}){RESET}")
        _fail += 1


def section(title: str):
    print(f"\n{BOLD}{CYAN}{'─'*62}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*62}{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
#  步驟 2：算術運算與優先順序
# ══════════════════════════════════════════════════════════════════════════════
def test_step2():
    section("步驟 2：算術運算與優先順序")
    check("3+4*5-2 = 21",
          run_interactive('printf("%d\\n", 3 + 4 * 5 - 2);'), "21")
    check("(3+4)*(5-2) = 21",
          run_interactive('printf("%d\\n", (3 + 4) * (5 - 2));'), "21")
    check("100/7 = 14",
          run_interactive('printf("%d\\n", 100 / 7);'), "14")
    check("100%7 = 2",
          run_interactive('printf("%d\\n", 100 % 7);'), "2")
    check("-15/4 = -3  (C 截斷行為，非 Python floor)",
          run_interactive('printf("%d\\n", -15 / 4);'), "-3")


# ══════════════════════════════════════════════════════════════════════════════
#  步驟 3：關係、邏輯與位元運算
# ══════════════════════════════════════════════════════════════════════════════
def test_step3():
    section("步驟 3：關係 / 邏輯 / 位元運算")
    check("10>5=1, 10<5=0, 10==10=1",
          run_interactive('printf("%d %d %d\\n", 10 > 5, 10 < 5, 10 == 10);'),
          "1 0 1")
    check("AND=0, OR=1",
          run_interactive('printf("%d %d\\n", 10 > 5 && 3 < 1, 10 > 5 || 3 < 1);'),
          "0 1")
    check("0xAB & 0x0F = 11",
          run_interactive('printf("%d\\n", 0xAB & 0x0F);'), "11")
    check("1 << 10 = 1024",
          run_interactive('printf("%d\\n", 1 << 10);'), "1024")
    check("0xF0 | 0x0D = 0xfd  (%x 格式)",
          run_interactive('printf("0x%x\\n", 0xF0 | 0x0D);'), "0xfd")


# ══════════════════════════════════════════════════════════════════════════════
#  步驟 4：變數、char 與數學函式
# ══════════════════════════════════════════════════════════════════════════════
def test_step4():
    section("步驟 4：變數 / char / 數學函式")
    check("abs(-18) = 18",
          run_interactive('int x=25; int y=-18; printf("abs(%d) = %d\\n", y, abs(y));'),
          "abs(-18) = 18")
    check("max(25,30)=30, min(25,30)=25",
          run_interactive('int x=25; printf("max=%d, min=%d\\n", max(x,30), min(x,30));'),
          "max=30, min=25")
    check("pow(2,16) = 65536",
          run_interactive('printf("pow(2,16) = %d\\n", pow(2,16));'),
          "pow(2,16) = 65536")
    check("sqrt(625) = 25",
          run_interactive('printf("sqrt(625) = %d\\n", sqrt(625));'),
          "sqrt(625) = 25")
    check("char 'Z': code=90, next='['  (ASCII 91)",
          run_interactive("char ch='Z'; printf(\"ch=%c, code=%d, next=%c\\n\", ch, ch, ch+1);"),
          "ch=Z, code=90, next=[")


# ══════════════════════════════════════════════════════════════════════════════
#  步驟 5：字串函式與工具函式
# ══════════════════════════════════════════════════════════════════════════════
def test_step5():
    section("步驟 5：字串函式")
    check('strcpy + strcat + strlen → "System Software", len=15',
          run_interactive(
              'char buf[50]; strcpy(buf,"System"); strcat(buf," Software");'
              'printf("buf=\\"%s\\", len=%d\\n", buf, strlen(buf));'),
          'buf="System Software", len=15')
    check('strcmp("apple","banana") → 負數(-1)',
          run_interactive('printf("cmp=%d\\n", strcmp("apple","banana"));'),
          "cmp=-1")
    check('atoi("2026") = 2026',
          run_interactive('printf("atoi=%d\\n", atoi("2026"));'),
          "atoi=2026")
    check('itoa(12345) → "12345"',
          run_interactive('char n[20]; itoa(12345,n); printf("itoa result: %s\\n",n);'),
          "itoa result: 12345")


# ══════════════════════════════════════════════════════════════════════════════
#  步驟 8：CHECK + RUN 選擇排序
# ══════════════════════════════════════════════════════════════════════════════
def test_step8():
    section("步驟 8：RUN 選擇排序（test_selection_sort.c）")
    src = load_c("test_selection_sort.c")
    expected = """\
Original: 64 25 12 22 11 90 45 33
Max = 90
Min = 11
Sum = 302
Avg = 37
Sorted:   11 12 22 25 33 45 64 90"""
    check("完整輸出（含統計 + 排序結果）", run_program(src), expected)


# ══════════════════════════════════════════════════════════════════════════════
#  步驟 10：EDIT 後重新 RUN（程式修改驗證）
# ══════════════════════════════════════════════════════════════════════════════
def test_step10_edited():
    section("步驟 10：EDIT 第 62 行後重新 RUN（data[7]=77）")
    src = load_c("test_selection_sort.c").replace(
        "data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 33;",
        "data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 77;"
    )
    expected = """\
Original: 64 25 12 22 11 90 45 77
Max = 90
Min = 11
Sum = 346
Avg = 43
Sorted:   11 12 22 25 45 64 77 90"""
    check("data[7]=77 → Sum=346, Avg=43", run_program(src), expected)


# ══════════════════════════════════════════════════════════════════════════════
#  步驟 12：GCD 遞迴
# ══════════════════════════════════════════════════════════════════════════════
def test_step12():
    section("步驟 12：GCD 遞迴（test_gcd.c）")
    src = load_c("test_gcd.c")
    check("GCD(48,18) = 6", run_program(src), "GCD(48,18) = 6")


# ══════════════════════════════════════════════════════════════════════════════
#  步驟 13：do/while + continue + break
# ══════════════════════════════════════════════════════════════════════════════
def test_step13():
    section("步驟 13：do/while + continue + break")
    src = """\
int main() {
    int n = 1;
    do {
        if (n % 3 == 0) {
            n = n + 1;
            continue;
        }
        if (n > 12) break;
        printf("%d ", n);
        n = n + 1;
    } while (n <= 20);
    printf("\\n");
    return 0;
}"""
    # 跳過 3 的倍數，遇到 n>12 停止 → 1 2 4 5 7 8 10 11
    check("輸出: 1 2 4 5 7 8 10 11", run_program(src), "1 2 4 5 7 8 10 11")


# ══════════════════════════════════════════════════════════════════════════════
#  步驟 14：錯誤處理（不 crash，顯示錯誤訊息後回到提示符）
# ══════════════════════════════════════════════════════════════════════════════
def test_step14():
    section("步驟 14：錯誤處理")

    i1 = Interpreter()
    o1 = _capture(lambda: i1.exec_interactive('printf("%d\\n", 10 / 0);'))
    check_contains("除以零 → 含 'zero' 的錯誤訊息", o1, "zero")

    i2 = Interpreter()
    o2 = _capture(lambda: i2.exec_interactive('printf("%d\\n", sqrt(-4));'))
    check_contains("sqrt(-4) → 含 'sqrt' 的錯誤訊息", o2, "sqrt")

    i3 = Interpreter()
    o3 = _capture(lambda: i3.exec_interactive('int bad = ;'))
    check_contains("語法錯誤 → 含 'error' 的訊息", o3, "error")

    i4 = Interpreter()
    o4 = _capture(lambda: i4.exec_interactive('int arr[3]; arr[5] = 10;'))
    check_contains("陣列越界 → 含 'bounds' 的錯誤訊息", o4, "bounds")


# ══════════════════════════════════════════════════════════════════════════════
#  手動測試清單（需在 python main.py 裡操作）
# ══════════════════════════════════════════════════════════════════════════════
def print_manual_checklist():
    section("☐  需手動在  python main.py  測試的互動指令")
    items = [
        ("步驟 1",  "ABOUT  → 確認顯示：版本號、作者、課程名稱、學期"),
        ("步驟 1",  "HELP   → 確認列出所有指令（LOAD/SAVE/LIST/EDIT/DELETE/INSERT/APPEND/NEW/RUN/CHECK/TRACE/VARS/FUNCS…）"),
        ("步驟 6",  "NEW 後 APPEND → 逐行輸入 test_selection_sort.c（87行），以 . 結束"),
        ("步驟 7",  "LIST 1-5  → 確認顯示 #define SIZE 8 等前 5 行"),
        ("步驟 7",  "LIST 56   → 確認顯示 int main() {"),
        ("步驟 9",  "FUNCS → 確認列出 swap / selection_sort / compute_sum / find_max / find_min / main 及所有 built-in"),
        ("步驟 10", "SAVE test_a.sc → 確認顯示 87 lines saved"),
        ("步驟 10", "EDIT 62 → 把 data[7]=33 改為 77 → RUN → 確認 Sum=346, Avg=43, Sorted: ...77..."),
        ("步驟 11", "DELETE 3（空白行）→ LIST 1-5 確認第 3 行變為原第 4 行"),
        ("步驟 11", "INSERT 3 → 輸入空白行（直接按 Enter）→ . 結束 → LIST 1-5 確認恢復"),
        ("步驟 12", "TRACE ON → APPEND 輸入 test_gcd.c → RUN → 確認 [line N] 追蹤輸出出現"),
        ("步驟 13", "NEW → int n=1; → do{...}while(n<=20); → printf(\"\\n\"); → 確認輸出 1 2 4 5 7 8 10 11"),
        ("步驟 15", "NEW → LOAD test_a.sc → RUN → 確認輸出 Sum=302（SAVE 當時的原始版本）"),
        ("步驟 16", "CLEAR → 確認畫面清空；QUIT → 確認顯示 Goodbye 並正常退出"),
    ]
    for step, desc in items:
        print(f"  {YELLOW}☐  [{step}]{RESET}  {desc}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  主程式
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print(f"{BOLD}{CYAN}")
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║   Small-C 驗收測試腳本 A  自動化驗證              ║")
    print("  ║   對應: 評分標準-學生版.md  Test A (公開版)        ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print(f"{RESET}")

    test_step2()
    test_step3()
    test_step4()
    test_step5()
    test_step8()
    test_step10_edited()
    test_step12()
    test_step13()
    test_step14()

    print_manual_checklist()

    total = _pass + _fail
    print(f"{BOLD}{'─'*62}{RESET}")
    print(f"{BOLD}自動化測試結果：{GREEN}{_pass} 通過{RESET}  /  {RED}{_fail} 失敗{RESET}  /  共 {total} 項{RESET}")
    print(f"{BOLD}{'─'*62}{RESET}")
    if _fail == 0:
        print(f"\n{GREEN}{BOLD}  ✅ 全部通過！自動化項目已驗收，請完成上方手動清單後即可應試。{RESET}\n")
    else:
        print(f"\n{RED}{BOLD}  ❌ 有 {_fail} 項失敗，請修正後再試。{RESET}\n")
    sys.exit(0 if _fail == 0 else 1)
