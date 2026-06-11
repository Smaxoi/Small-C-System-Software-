#!/usr/bin/env python3
"""
Small-C 解譯器 對照式自動測試腳本
用法：python run_tests.py            （預設測 tests/ 自己這個資料夾）
      python run_tests.py <資料夾>

每個 .sc 測試檔搭配一個同名 .expected 預期輸出檔，
直接呼叫 interpreter 執行，比對實際輸出與預期輸出。
（不經由 main.py 的互動模式，避免卡住）
"""
import sys
import os
import io
import glob

# 把上層目錄加入 path，才能 import 到 interpreter.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interpreter import Interpreter

# Windows 終端機強制 UTF-8，才能正確顯示中文與符號
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def run_sc(sc_path):
    """執行一個 .sc 程式，回傳它印出的所有內容（含 'Program exited...' 那行）。"""
    interp = Interpreter()
    src = open(sc_path, 'r', encoding='utf-8').read()
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf            # 把程式輸出導向字串緩衝區以便比對
    try:
        interp.run_program(src)
    finally:
        sys.stdout = old        # 還原，避免影響後續報告輸出
    return buf.getvalue()


def main():
    # 預設測「腳本自己所在的資料夾」，也可由命令列指定
    here = os.path.dirname(os.path.abspath(__file__))
    tests_dir = sys.argv[1] if len(sys.argv) > 1 else here

    sc_files = sorted(glob.glob(os.path.join(tests_dir, '*.sc')))
    if not sc_files:
        print(f'[錯誤] 在 {tests_dir}/ 找不到任何 .sc 檔案')
        sys.exit(1)

    print('Small-C 解譯器對照測試報告')
    print(f'測試目錄: {tests_dir}  共 {len(sc_files)} 個測試')
    print('=' * 60)

    passed_count = 0
    failed_tests = []
    skipped = 0

    for sc_path in sc_files:
        name = os.path.basename(sc_path)
        expected_path = sc_path[:-3] + '.expected'   # 把 .sc 換成 .expected

        if not os.path.exists(expected_path):
            print(f'  [SKIP] {name} (找不到對應的 .expected)')
            skipped += 1
            continue

        actual   = run_sc(sc_path)
        expected = open(expected_path, 'r', encoding='utf-8').read()

        if actual == expected:
            passed_count += 1
            print(f'  [PASS] {name}')
        else:
            failed_tests.append(name)
            print(f'  [FAIL] {name}')
            # 顯示第一處差異，方便除錯
            act_lines = actual.splitlines()
            exp_lines = expected.splitlines()
            for i, (a, e) in enumerate(zip(act_lines, exp_lines)):
                if a != e:
                    print(f'         第 {i+1} 行差異:')
                    print(f'         期望: {e!r}')
                    print(f'         實際: {a!r}')
                    break
            if len(act_lines) != len(exp_lines):
                print(f'         行數不同: 期望 {len(exp_lines)} 行，實際 {len(act_lines)} 行')

    ran = passed_count + len(failed_tests)   # 實際有跑的（排除 skip）
    print('=' * 60)
    tail = f'（另有 {skipped} 個略過）' if skipped else ''
    if failed_tests:
        print(f'結果: {passed_count}/{ran} 通過  (失敗: {", ".join(failed_tests)}) {tail}')
    else:
        print(f'結果: {passed_count}/{ran} 通過  ✅ 全部通過 {tail}')

    sys.exit(0 if not failed_tests else 1)


if __name__ == '__main__':
    main()
