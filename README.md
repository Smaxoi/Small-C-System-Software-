# Small-C 互動式解譯器

> 系統軟體課程期末專題 ── Spring 2026

以 Python 3 實作的 Small-C 子集樹狀走訪直譯器（Tree-walking Interpreter）。
支援互動式 REPL、語法高亮、記憶體視覺化、TRACE 逐行追蹤、COLOR 主題切換，以及 switch/case 加分功能。

---

## 目錄

1. [環境需求](#環境需求)
2. [快速啟動](#快速啟動)
3. [互動式 Shell 指令](#互動式-shell-指令)
4. [Small-C 語言規格](#small-c-語言規格)
5. [內建函式總覽](#內建函式總覽)
6. [專案架構](#專案架構)
7. [系統設計說明](#系統設計說明)
8. [測試](#測試)
9. [操作範例](#操作範例)
10. [額外功能說明](#額外功能說明)

---

## 環境需求

- **Python 3.8 以上**（建議 3.10 / 3.11 / 3.12）
- 不需要安裝任何第三方套件，僅使用 Python 標準函式庫

```bash
python --version   # 確認版本 >= 3.8
```

---

## 快速啟動

### 啟動互動式 REPL

```bash
python main.py
```

### 啟動時直接載入程式

```bash
python main.py myprogram.c
```

### 啟動後的畫面

```
  ██████╗ ███╗   ███╗ █████╗ ██╗     ██╗
  ╚════██╗████╗ ████║██╔══██╗██║     ██║
   █████╔╝██╔████╔██║███████║██║     ██║
  ██╔═══╝ ██║╚██╔╝██║██╔══██║██║     ██║
  ███████╗██║ ╚═╝ ██║██║  ██║███████╗███████╗
  ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝

  ╔══════════════════════════════════════════════════╗
  ║    Small-C Interactive Interpreter  v1.0         ║
  ║          System Software  -  Spring 2026         ║
  ╚══════════════════════════════════════════════════╝

  快速開始
  APPEND              →  輸入程式碼（. 結束）
  RUN                 →  執行程式
  ...

sc>
```

---

## 互動式 Shell 指令

### 程式管理

| 指令 | 說明 |
|------|------|
| `APPEND` | 進入多行輸入模式，以單獨一行 `.` 結束。支援自動縮排（`{` 後自動縮排，`}` 自動退格）。 |
| `LIST` | 列出全部程式碼（含語法高亮） |
| `LIST n` | 列出第 n 行 |
| `LIST n1-n2` | 列出第 n1 到 n2 行 |
| `EDIT n` | 編輯第 n 行（顯示原內容，輸入新內容取代） |
| `DELETE n` | 刪除第 n 行 |
| `DELETE n1-n2` | 刪除第 n1 到 n2 行 |
| `INSERT n` | 在第 n 行之前插入新行（同樣以 `.` 結束） |
| `NEW` | 清除目前程式（若有未儲存修改會提示確認） |
| `SAVE filename` | 將程式儲存為檔案 |
| `LOAD filename` | 從檔案載入程式 |

### 執行與除錯

| 指令 | 說明 |
|------|------|
| `RUN` | 執行目前程式 |
| `CHECK` | 僅做語法檢查，不執行 |
| `TRACE ON` | 開啟逐行追蹤模式（每行執行前顯示 `[line N] 內容`） |
| `TRACE OFF` | 關閉追蹤模式 |
| `VARS` | 顯示目前所有變數（名稱、型別、位址、值） |
| `FUNCS` | 列出所有使用者定義函式與內建函式 |
| `MEMSHOW` | 顯示記憶體配置圖（變數位址 + 字串常數） |

### 系統指令

| 指令 | 說明 |
|------|------|
| `COLOR` | 顯示目前主題及所有可用主題預覽 |
| `COLOR default` | 切換為預設主題（藍/綠/黃） |
| `COLOR matrix` | 切換為 Matrix 主題（全綠） |
| `COLOR warm` | 切換為暖色主題（紅/橘） |
| `COLOR ocean` | 切換為海洋主題（青/藍） |
| `COLOR off` | 關閉語法高亮 |
| `CLEAR` | 清除終端機畫面 |
| `HELP` | 顯示所有指令說明 |
| `ABOUT` | 顯示直譯器版本資訊 |
| `QUIT` / `EXIT` | 離開直譯器（若有未儲存修改會提示確認） |

> **提示：**
> - 在任何提示符下按 `Ctrl+C` 可取消目前輸入，回到 `sc>`
> - 直接輸入 Small-C 程式碼即可立即執行（不須 APPEND + RUN）
> - 輸入未完成的程式碼（例如只輸入 `{` 後按 Enter）會進入 `  > ` 連續輸入模式

---

## Small-C 語言規格

### 資料型別

| 型別 | 說明 | 範圍 |
|------|------|------|
| `int` | 32 位元有號整數 | −2,147,483,648 ～ 2,147,483,647 |
| `char` | 8 位元字元 | 0 ～ 127 |
| `void` | 僅用於函式回傳型別 | — |

```c
int x = 42;
char c = 'A';
int arr[10];          // 一維陣列
int *p;  p = &x;      // 指標與取址
```

### 運算子（優先順序由高到低）

| 優先順序 | 運算子 | 說明 |
|---------|-------|------|
| 1（最高）| `[]`  `()`  `++`  `--` | 陣列下標、函式呼叫、後置遞增/遞減 |
| 2 | `++`  `--`  `-`  `!`  `~`  `*`  `&` | 前置遞增/遞減、一元負號、邏輯非、位元非、取值、取址 |
| 3 | `*`  `/`  `%` | 乘、除（截斷至零）、取餘 |
| 4 | `+`  `-` | 加、減 |
| 5 | `<<`  `>>` | 左移、右移 |
| 6 | `<`  `<=`  `>`  `>=` | 關係運算 |
| 7 | `==`  `!=` | 等於、不等於 |
| 8 | `&` | 位元 AND |
| 9 | `^` | 位元 XOR |
| 10 | `\|` | 位元 OR |
| 11 | `&&` | 邏輯 AND（短路求值） |
| 12 | `\|\|` | 邏輯 OR（短路求值） |
| 13（最低）| `=`  `+=`  `-=`  `*=`  `/=`  `%=` | 指定、複合指定 |

> 整數除法採用 **C 語言截斷至零**行為：`-15 / 4 = -3`（非 Python 的向下取整 `-4`）

### 控制流程

```c
// if / else
if (x > 0) {
    printf("positive\n");
} else {
    printf("non-positive\n");
}

// while
while (i < 10) {
    i = i + 1;
}

// for
for (i = 0; i < n; i = i + 1) {
    printf("%d\n", arr[i]);
}

// do/while
do {
    n = n + 1;
} while (n < 100);

// switch/case（含 fall-through 與 default）
switch (x) {
    case 1: printf("one\n");   break;
    case 2: printf("two\n");   break;
    default: printf("other\n"); break;
}

// break / continue / return
break;
continue;
return value;
```

### 前置處理器

```c
#define SIZE 100
#define MAX_VAL 255
```

`#define` 常數可用於陣列大小、運算式及函式引數。

### 函式定義與呼叫

```c
// 定義
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);   // 支援遞迴
}

// 呼叫
int result = factorial(10);
```

支援：
- 回傳值型別：`int`、`char`、`void`
- 參數：值傳遞（by value）、指標傳遞（by pointer）
- 遞迴呼叫

### 跳脫字元

| 序列 | 意義 |
|------|------|
| `\n` | 換行 |
| `\t` | 定位字元 |
| `\r` | 歸位字元 |
| `\\` | 反斜線 |
| `\'` | 單引號 |
| `\"` | 雙引號 |
| `\0` | 空字元（字串結尾） |

### 數值常數

```c
int a = 255;      // 十進位
int b = 0xFF;     // 十六進位
int c = 0377;     // 八進位
char d = 'A';     // 字元常數（值為 65）
```

---

## 內建函式總覽

### I/O 函式

| 函式 | 說明 |
|------|------|
| `printf(fmt, ...)` | 格式化輸出。支援 `%d` `%c` `%s` `%x` `%X` `%o` `%%`，以及寬度旗標 `%-5d` `%05d` |
| `scanf(fmt, ...)` | 格式化輸入（`%d` `%c` `%s`） |
| `putchar(c)` | 輸出單一字元 |
| `getchar()` | 讀取單一字元，回傳 ASCII 值 |
| `puts(s)` | 輸出字串並自動換行 |

### 字串函式

| 函式 | 說明 |
|------|------|
| `strlen(s)` | 回傳字串長度（不含 `\0`） |
| `strcpy(dst, src)` | 複製字串 |
| `strcat(dst, src)` | 字串串接（附加到 dst 後面） |
| `strcmp(s1, s2)` | 字串比較，回傳 `−1` / `0` / `1` |
| `strncpy(dst, src, n)` | 最多複製 n 個字元 |
| `substr(dst, src, pos, len)` | 擷取子字串 |
| `strrev(dst, src)` | 將 src 反轉後存入 dst |
| `strtok(str, delim)` | C 風格字串分詞（傳入 0 繼續上次） |
| `atoi(s)` | 字串轉整數 |
| `itoa(n, buf)` | 整數轉字串 |

### 數學函式

| 函式 | 說明 |
|------|------|
| `abs(x)` | 絕對值 |
| `max(a, b)` | 兩數最大值 |
| `min(a, b)` | 兩數最小值 |
| `pow(base, exp)` | 次方（exp 需 ≥ 0） |
| `sqrt(x)` | 整數平方根（向下取整） |
| `rand()` | 回傳 0～32767 的亂數 |
| `srand(seed)` | 設定亂數種子 |

### 字元函式

| 函式 | 說明 |
|------|------|
| `isalpha(c)` | 是否為字母 |
| `isdigit(c)` | 是否為數字 |
| `isspace(c)` | 是否為空白字元 |
| `isupper(c)` | 是否為大寫 |
| `islower(c)` | 是否為小寫 |
| `toupper(c)` | 轉大寫 |
| `tolower(c)` | 轉小寫 |

### 記憶體 / 其他

| 函式 | 說明 |
|------|------|
| `memset(ptr, val, n)` | 將 n 個 byte 設為 val |
| `exit(code)` | 結束程式，回傳 code |

---

## 專案架構

```
small-C專題/
├── main.py          # 互動式 Shell、語法高亮、COLOR 主題、MEMSHOW
├── interpreter.py   # 樹狀走訪直譯器、內建函式實作
├── parser.py        # 遞迴下降語法分析器
├── lexer.py         # 詞法分析器（Tokenizer）
├── nodes.py         # AST 節點定義
├── memory.py        # 平坦記憶體模型、Scope 鏈、VarInfo
├── ascii_art.txt    # 啟動畫面 ASCII 藝術
├── requirements.txt # 相依套件（僅標準函式庫）
└── tests/
    ├── test_runner.py          # 92 項基本功能自動化測試
    ├── test_verification.py    # 27 項對應評分標準 Test A 的驗收測試
    ├── test_selection_sort.c   # 選擇排序 + 統計（驗收步驟 6）
    ├── test_gcd.c              # GCD 遞迴（驗收步驟 12）
    ├── test_bubble.c           # 氣泡排序
    ├── test_isprime.c          # 質數判斷
    └── test_switch.c           # switch/case 測試
```

---

## 系統設計說明

### 三層式處理架構

```
原始碼（字串）
      │
      ▼
  [ Lexer ]  ────────────────────────────────  詞法分析
  lexer.py                                     字元 → Token 串列
      │
      ▼
  [ Parser ]  ───────────────────────────────  語法分析
  parser.py                                    Token → AST（抽象語法樹）
      │
      ▼
  [ Interpreter ]  ──────────────────────────  直譯執行
  interpreter.py                               走訪 AST 節點，逐一執行
      │
      ├── Memory（平坦位址空間，BASE = 0x1000）
      └── Scope（變數查找鏈，支援巢狀作用域）
```

### Lexer（詞法分析器）

- 手動字元掃描，不依賴 `re` 模組
- 支援：關鍵字、識別符、整數（十進位 / 十六進位 / 八進位）、字串、字元、運算子、`#define`
- 自動跳過 `//` 單行與 `/* */` 區塊註解
- 跳脫字元處理（`\n` `\t` `\0` 等）
- 非 ASCII 字元（中文、emoji）自動跳過，不 crash

### Parser（語法分析器）

- **遞迴下降**（Recursive Descent）策略
- 透過函式呼叫層次表達運算子優先順序：
  `parse_expr()` → `parse_or()` → `parse_and()` → ... → `parse_unary()` → `parse_primary()`
- 支援 top-level 語句直接執行（不強制要求 `main()`）

### Interpreter（樹狀走訪直譯器）

- **Tree-walking**：直接走訪 AST，每種節點對應一個 Python 方法
- 控制流程訊號（`break` / `continue` / `return`）以 Python Exception 實作
- 函式呼叫建立獨立的 `func_scope`，引數在呼叫端 scope 求值（by value）
- 內建函式透過 `_get_builtin()` 查表分派

### Memory（記憶體模型）

```
Memory.cells = {
    0x1000: 42,    ← int x = 42
    0x1001: 65,    ← char c = 'A'
    0x1002: 10,    ← arr[0]
    0x1003: 20,    ← arr[1]
    ...
}
```

- `cells` 為 Python `dict`，以整數位址為 key
- 從 `0x1000` 開始，保留 `0` 作為 NULL 指標
- `alloc(n)` 配置 n 個連續 cell，回傳起始位址
- 整數寫入做 32-bit 截斷（模擬 C 的 int 溢位）

### Scope（作用域鏈）

```
global_scope
    └── func_scope（函式呼叫時建立）
            └── block_scope（{} 區塊時建立）
```

- `lookup(name)` 先找自己，找不到往 parent 查，實現巢狀作用域
- 每個變數以 `VarInfo(type_, addr, size, is_array, is_pointer)` 記錄

### switch/case 實作（加分項目）

以 `matched` 旗標實現 C 語言的 fall-through 行為：

```python
matched = False
for case_val_node, stmts in node.cases:
    if not matched:
        if val == eval(case_val_node):
            matched = True       # 一旦命中，後續 case 全部執行
    if matched:
        exec(stmts)              # 直到 break（BreakSignal）跳出
```

---

## 測試

### 執行自動化測試

```bash
cd tests

# 92 項基本功能測試（算術、邏輯、陣列、指標、遞迴、字串、排序…）
python test_runner.py

# 27 項對應評分標準 Test A 的驗收測試
python test_verification.py
```

### 測試涵蓋範圍

| 類別 | 測試項目 |
|------|---------|
| 算術運算 | 四則運算、優先順序、負數除法（截斷）、取餘 |
| 關係 / 邏輯 | `>` `<` `==` `!=` `&&` `\|\|` `!`、短路求值 |
| 位元運算 | `&` `\|` `^` `~` `<<` `>>` |
| 變數 | `int` / `char` 宣告、複合指定（`+=` `-=` 等）、`++` `--` |
| 控制流程 | `if/else`、`while`、`for`、`do/while`、`break`、`continue` |
| 陣列 / 指標 | 宣告、讀寫、越界偵測、指標傳遞 |
| 函式 | 定義、呼叫、遞迴、`void` / `int` 回傳 |
| 內建函式 | I/O、字串（含 strrev / strtok）、數學、字元 |
| printf 格式 | `%d` `%c` `%s` `%x` `%o`、寬度旗標 `%-5d` `%05d` |
| #define | 常數定義與展開（含陣列大小） |
| switch/case | 單一命中、fall-through、default |
| 錯誤處理 | 除以零、sqrt 負數、陣列越界、語法錯誤 |
| 完整程式 | 選擇排序、氣泡排序、質數、GCD |

---

## 操作範例

### 範例一：直接在提示符執行運算式

```
sc> printf("%d\n", 3 + 4 * 5);
23
sc> int x = 10; x += 5; printf("%d\n", x);
15
sc> printf("0x%x\n", 0xF0 | 0x0D);
0xfd
```

### 範例二：APPEND 輸入遞迴函式

```
sc> APPEND
(Enter lines; type '.' alone to finish. Auto-indent ON.)
   1│  int fact(int n) {
   2│+4 if (n <= 1) return 1;
   3│+4 return n * fact(n - 1);
   4│+4 }
   5│  int main() {
   6│+4 printf("%d\n", fact(10));
   7│+4 return 0;
   8│+4 }
   9│  .
sc> RUN
3628800
Program exited with return value 0.
```

### 範例三：TRACE 逐行追蹤

```
sc> TRACE ON
Trace mode enabled.
sc> RUN
[line 1] int fact(int n) {
[line 2] if (n <= 1) return 1;
[line 3] return n * fact(n - 1);
...
3628800
Program exited with return value 0.
sc> TRACE OFF
```

### 範例四：MEMSHOW 記憶體檢視

```
sc> int x = 42; char c = 'A'; int arr[3];
sc> arr[0] = 10; arr[1] = 20; arr[2] = 30;
sc> MEMSHOW
  0x1000  int    x        =  42
  0x1001  char   c        =  65  'A'
  0x1002  int    arr[3]   =  {10, 20, 30}
```

### 範例五：EDIT 修改程式

```
sc> LIST 5
   5:     data[7] = 33;
sc> EDIT 5
   5:     data[7] = 33;
   5> data[7] = 77;
sc> RUN
...已反映修改...
```

### 範例六：COLOR 主題切換

```
sc> COLOR
目前主題：default
可用主題：
  COLOR default    keyword  "string"  42  // comment  ◀ 目前
  COLOR matrix     keyword  "string"  42  // comment
  COLOR warm       keyword  "string"  42  // comment
  COLOR ocean      keyword  "string"  42  // comment
  COLOR off        keyword  "string"  42  // comment
sc> COLOR matrix
主題已切換為：matrix
```

### 範例七：switch/case（加分功能）

```
sc> APPEND
   1│  int main() {
   2│+4 int x = 2;
   3│+4 switch (x) {
   4│+8     case 1: printf("one\n");   break;
   5│+8     case 2: printf("two\n");   break;
   6│+8     case 3: printf("three\n"); break;
   7│+8     default: printf("other\n"); break;
   8│+4 }
   9│+4 return 0;
  10│+4 }
   .
sc> RUN
two
Program exited with return value 0.
```

---

## 錯誤處理

直譯器對以下錯誤均會顯示明確訊息，**不會 crash**，執行後回到 `sc>` 提示符：

| 錯誤類型 | 範例 | 訊息 |
|---------|------|------|
| 語法錯誤 | `int bad = ;` | `Syntax error: ...` |
| 除以零 | `printf("%d", 10 / 0);` | `Runtime error: Division by zero` |
| 陣列越界 | `int a[3]; a[5] = 1;` | `Runtime error: Array index out of bounds` |
| sqrt 負數 | `sqrt(-1)` | `Runtime error: sqrt: argument must be non-negative` |
| 未定義變數 | `printf("%d", z);` | `Runtime error: Undefined variable 'z'` |
| 未定義函式 | `foo();` | `Runtime error: Undefined function 'foo'` |

---

## 額外功能說明

以下功能均為**超出作業基本要求**、自行設計實作的項目。

### 總覽

| 功能 | 類別 | 說明 |
|------|------|------|
| switch / case | 加分項目（+5 分） | 含 fall-through、default |
| COLOR 主題切換 | Shell 指令 | 4 種語法高亮主題 |
| LIST 語法高亮 | Shell 指令 | 彩色顯示程式碼 |
| APPEND 自動縮排 | Shell 指令 | 自動計算縮排深度 |
| MEMSHOW 記憶體視覺化 | Shell 指令 | 顯示變數位址與值 |
| Ctrl+C 優雅處理 | 系統穩定性 | 任何時機按 Ctrl+C 都不會卡住 |
| strrev | 內建函式 | 字串反轉 |
| strtok | 內建函式 | C 風格字串分詞 |
| Script Mode | 語言支援 | 無需 main() 也能直接執行 |

---

### 1. switch / case（加分 +5 分）

作業說明中列為選擇性加分項目。實作完整的 C 語言 `switch` 語意，包含：

- **fall-through**：命中某個 `case` 後，若無 `break`，會繼續執行下一個 `case`
- **default**：所有 `case` 都不符合時執行
- **break**：跳出整個 `switch`

```c
int x = 2;
switch (x) {
    case 1: printf("one\n");   break;
    case 2: printf("two\n");   break;   // 命中此處
    case 3: printf("three\n"); break;
    default: printf("other\n"); break;
}
// 輸出: two
```

**實作方式：** 使用 `matched` 布林旗標。一旦某個 `case` 值相等，`matched` 設為 `True`，後續所有 `case` 的語句均執行，直到 `break`（拋出 `BreakSignal`）跳出。

---

### 2. COLOR 指令（語法高亮主題切換）

作業只要求 `LIST` 能顯示程式碼，未要求彩色。我們額外設計了 5 種主題，可在執行期間隨時切換：

```
sc> COLOR             ← 顯示所有主題預覽
sc> COLOR default     ← 藍/綠/黃（預設）
sc> COLOR matrix      ← 全綠，仿終端機風格
sc> COLOR warm        ← 紅/橘暖色調
sc> COLOR ocean       ← 青/藍冷色調
sc> COLOR off         ← 關閉所有顏色
```

每種主題對不同語法元素（關鍵字、字串、數字、函式名稱、註解）套用不同顏色，使用 ANSI escape code 實作，無需任何第三方套件。

---

### 3. LIST 語法高亮

`LIST` 指令輸出的程式碼具有語法高亮，自行以字元掃描方式實作（不使用 regex），分辨以下元素：

| 元素 | 顏色（預設主題） |
|------|----------------|
| 關鍵字（`int` `if` `for` 等） | 藍色 |
| 字串常數（`"..."`) | 綠色 |
| 字元常數（`'...'`） | 青色 |
| 數字（十進位 / 十六進位） | 黃色 |
| 函式名稱（`name(` 形式） | 青色 |
| `#define` | 紫色 |
| 註解（`//` 和 `/* */`） | 灰色 |

---

### 4. APPEND 自動縮排

作業只要求 `APPEND` 能夠多行輸入，未要求縮排輔助。我們額外加入自動縮排深度提示：

```
sc> APPEND
   1│  int main() {        ← 輸入 {，下一行自動提示 +4
   2│+4 int i = 0;
   3│+4 for (i = 0; i < 5; i = i + 1) {
   4│+8     printf("%d\n", i);
   5│+8 }                  ← 輸入 }，自動退一層縮排儲存
   6│+4 return 0;
   7│+4 }
   8│  .
```

**設計細節：**
- `{` 使縮排深度 +1，`}` 使深度 -1
- 深度提示（`+4` `+8`）僅作視覺顯示，不佔輸入位置，使用者可自由退格到最左
- 儲存時自動套用對應的空格縮排

---

### 5. MEMSHOW 記憶體視覺化

作業未要求，自行設計的除錯工具，顯示所有變數在記憶體中的配置：

```
sc> int x = 42; char c = 'A'; int arr[3];
sc> arr[0] = 10; arr[1] = 20; arr[2] = 30;
sc> MEMSHOW
  0x1000  int    x        =  42
  0x1001  char   c        =  65  'A'
  0x1002  int    arr[3]   =  {10, 20, 30}
```

可直接觀察：變數的記憶體位址（十六進位）、型別、陣列完整內容。

---

### 6. Ctrl+C 優雅處理

原本若在多行輸入中途按 Ctrl+C，會卡在 `  > ` 提示符無法退出。我們以 `_CTRL_C` sentinel 物件解決此問題：

```python
_CTRL_C = object()   # 獨立 sentinel，有別於 '' 或 None

def read_line(self, prompt=''):
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("  ^C")
        return _CTRL_C   # 回傳 sentinel 而非空字串
```

現在在任何提示符（包括 `  > ` 連續輸入模式）下按 Ctrl+C，都能正確取消輸入並回到 `sc>`：

```
sc> int main() {
  >     printf("hello\n");
  > ^C
(input cancelled)
sc>
```

---

### 7. strrev（字串反轉）

作業的字串函式清單未包含 `strrev`，自行補充實作：

```c
char dst[20];
strrev(dst, "Hello");
printf("%s\n", dst);   // 輸出: olleH
```

實作：從記憶體讀出字串 → Python 切片 `s[::-1]` 反轉 → 寫回目標位址。

---

### 8. strtok（字串分詞）

作業的字串函式清單未包含 `strtok`，自行補充實作，完整模擬 C 語言 `strtok` 的行為，包含**跨呼叫的靜態狀態**：

```c
char str[50];
strcpy(str, "apple,banana,cherry");
char *token = strtok(str, ",");
while (token != 0) {
    printf("%s\n", token);
    token = strtok(0, ",");   // 傳入 0 表示繼續上次
}
// 輸出:
// apple
// banana
// cherry
```

**實作細節：** 使用直譯器類別層級的 `_strtok_str` 與 `_strtok_pos` 兩個變數模擬 C 語言的 `static` 內部狀態，實現跨呼叫的連續分詞。

---

### 9. Script Mode（無需 main() 的腳本模式）

標準 C 程式必須有 `main()` 才能執行，但我們額外支援直接在頂層撰寫語句（適合互動式除錯）：

```
sc> int x = 10;
sc> for (x = 0; x < 5; x = x + 1) {
  >     printf("%d\n", x);
  > }
0
1
2
3
4
```

**實作方式：** `run_program()` 先嘗試尋找 `main()`；若不存在，則收集所有頂層可執行語句，在 `global_scope` 下直接執行。
