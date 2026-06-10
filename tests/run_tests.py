#python3
"""
Small-C 解譯器 自動測試腳本
用法：python run_tests.py [tests_dir]
預設在目前目錄的 tests/ 資料夾尋找 .sc 與 .expected 檔案
"""
import sys
import os
import subprocess
import glob

def run_test(sc_path, expected_path, python_cmd='python'):
    """執行一個 .sc 測試並與 .expected 比較"""
    # 執行解譯器
    result = subprocess.run(
        [python_cmd, 'main.py', sc_path],
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    actual = result.stdout

    # 讀取預期輸出
    with open(expected_path, 'r', encoding='utf-8') as f:
        expected = f.read()

    passed = actual == expected
    return passed, actual, expected


def main():
    tests_dir = sys.argv[1] if len(sys.argv) > 1 else 'tests'

    # 偵測 python 指令（Windows 用 python，Linux/Mac 用 python3）
    python_cmd = 'python' if sys.platform == 'win32' else 'python3'

    # 找出所有測試
    sc_files = sorted(glob.glob(os.path.join(tests_dir, '*.sc')))
    if not sc_files:
        print(f'[錯誤] 在 {tests_dir}/ 找不到任何 .sc 檔案')
        sys.exit(1)

    print(f'Small-C 解譯器測試報告')
    print(f'測試目錄: {tests_dir}/  共 {len(sc_files)} 個測試')
    print('=' * 60)

    passed_count = 0
    failed_tests = []

    for sc_path in sc_files:
        name = os.path.basename(sc_path)
        expected_path = sc_path.replace('.sc', '.expected')

        if not os.path.exists(expected_path):
            print(f'  [SKIP] {name} (找不到對應的 .expected)')
            continue

        passed, actual, expected = run_test(sc_path, expected_path, python_cmd)

        if passed:
            passed_count += 1
            print(f'  [PASS] {name}')
        else:
            failed_tests.append(name)
            print(f'  [FAIL] {name}')
            # 顯示差異（前 5 行）
            act_lines = actual.splitlines()
            exp_lines = expected.splitlines()
            for i, (a, e) in enumerate(zip(act_lines, exp_lines)):
                if a != e:
                    print(f'         第 {i+1} 行差異:')
                    print(f'         期望: {repr(e)}')
                    print(f'         實際: {repr(a)}')
                    break
            if len(act_lines) != len(exp_lines):
                print(f'         行數不同: 期望 {len(exp_lines)} 行，實際 {len(act_lines)} 行')

    total = len(sc_files)
    print('=' * 60)
    print(f'結果: {passed_count}/{total} 通過', end='')
    if failed_tests:
        print(f'  (失敗: {", ".join(failed_tests)})')
    else:
        print('  ✅ 全部通過')


if __name__ == '__main__':
    main()
