# nodes.py - Small-C 的「抽象語法樹 (AST)」節點定義
#
# 【這個檔案是什麼】
#   Parser 會把程式碼組成一棵「語法樹」，樹上每個節點就是這裡的一個 class。
#   例如  x = 1 + 2  會變成：
#         Assign(=)
#         ├─ target: Ident('x')
#         └─ value : BinaryOp(+)
#                    ├─ IntLit(1)
#                    └─ IntLit(2)
#   Interpreter 之後就「走訪」這棵樹來執行程式。
#   每個節點都存 line（行號），方便執行出錯時回報是哪一行。

class Node:
    """所有 AST 節點的共同基底（本身沒內容，只是個分類標籤）。"""
    pass

# ── 最上層結構 ───────────────────────────────────────────────────────────────

class Program(Node):
    """【整個程式】一支 .c 檔的根節點，底下掛著所有函式、全域變數、#define。"""
    def __init__(self, items):
        self.items = items  # 清單：FuncDef | VarDecl | Define

class FuncDef(Node):
    """【函式定義】對應  int add(int a, int b) { ... }"""
    def __init__(self, return_type, name, params, body, line=0):
        self.return_type = return_type   # 回傳型別 'int' | 'char' | 'void'
        self.name = name                 # 函式名
        self.params = params             # 參數清單（list of Param）
        self.body = body                 # 函式本體（Block）
        self.line = line

class Param(Node):
    """【函式參數】對應  int a、int *p、int arr[]"""
    def __init__(self, type_, name, is_pointer=False, is_array=False):
        self.type_ = type_
        self.name = name
        self.is_pointer = is_pointer
        self.is_array = is_array         # int arr[] 形式的參數

class Define(Node):
    """【前置處理常數】對應  #define SIZE 100"""
    def __init__(self, name, value, line=0):
        self.name = name
        self.value = value               # 整數或字串

# ── 陳述句 (Statements) ──────────────────────────────────────────────────────
# 「做一件事」的語法：宣告、迴圈、判斷、return…（不產生數值）

class Block(Node):
    """【區塊】對應一對大括號  { 一堆陳述句 }"""
    def __init__(self, stmts, line=0):
        self.stmts = stmts
        self.line = line

class VarDecl(Node):
    """【變數宣告】對應  int x = 5;  /  int arr[10];  /  int *p;"""
    def __init__(self, type_, name, init=None, is_array=False,
                 array_size=None, is_pointer=False, line=0):
        self.type_ = type_
        self.name = name
        self.init = init                 # 初始值運算式（可為 None）
        self.is_array = is_array
        self.array_size = array_size     # 陣列大小運算式或 None
        self.is_pointer = is_pointer
        self.line = line

class If(Node):
    """【條件判斷】對應  if (cond) {...} else {...}"""
    def __init__(self, cond, then_body, else_body=None, line=0):
        self.cond = cond                 # 條件
        self.then_body = then_body       # 條件成立做的事
        self.else_body = else_body       # else（可為 None）
        self.line = line

class While(Node):
    """【while 迴圈】對應  while (cond) {...}"""
    def __init__(self, cond, body, line=0):
        self.cond = cond
        self.body = body
        self.line = line

class For(Node):
    """【for 迴圈】對應  for (init; cond; incr) {...}"""
    def __init__(self, init, cond, incr, body, line=0):
        self.init = init    # 初始化（VarDecl | ExprStmt | None）
        self.cond = cond    # 每圈先檢查的條件
        self.incr = incr    # 每圈結束做的遞增
        self.body = body
        self.line = line

class DoWhile(Node):
    """【do/while 迴圈】對應  do {...} while (cond);  —— 至少先做一次"""
    def __init__(self, body, cond, line=0):
        self.body = body
        self.cond = cond
        self.line = line

class Break(Node):
    """【break】跳出迴圈或 switch"""
    def __init__(self, line=0):
        self.line = line

class Continue(Node):
    """【continue】跳過本圈剩下的，直接進入下一圈"""
    def __init__(self, line=0):
        self.line = line

class Return(Node):
    """【return】從函式回傳一個值（expr 可為 None 代表 return;）"""
    def __init__(self, expr=None, line=0):
        self.expr = expr
        self.line = line

class ExprStmt(Node):
    """【運算式陳述句】對應  printf(...);  或  x = 5;  這種「一行運算式 + 分號」"""
    def __init__(self, expr, line=0):
        self.expr = expr
        self.line = line

# ── 運算式 (Expressions) ─────────────────────────────────────────────────────
# 「算出一個值」的語法：加減乘除、變數、函式呼叫、字面值…

class Assign(Node):
    """【指定】對應  x = 5  /  x += 3（複合指定）"""
    def __init__(self, op, target, value, line=0):
        self.op = op         # '=' | '+=' | '-=' | '*=' | '/=' | '%='
        self.target = target # 被指定的左值（變數、陣列元素、*指標）
        self.value = value   # 右邊算出的值
        self.line = line

class BinaryOp(Node):
    """【二元運算】對應  a + b、a < b、a && b 等兩個運算元的運算"""
    def __init__(self, op, left, right, line=0):
        self.op = op
        self.left = left
        self.right = right
        self.line = line

class UnaryOp(Node):
    """【一元（前置）運算】對應  -x、!flag、~bits、++i、*p（取值）、&x（取址）"""
    def __init__(self, op, expr, line=0):
        self.op = op         # '-' | '!' | '~' | '++' | '--' | '*' | '&'
        self.expr = expr
        self.line = line

class PostfixOp(Node):
    """【後置運算】對應  i++  /  i--（先用值，再加減）"""
    def __init__(self, op, expr, line=0):
        self.op = op         # '++' | '--'
        self.expr = expr
        self.line = line

class FuncCall(Node):
    """【函式呼叫】對應  add(1, 2)  /  printf("%d", x)"""
    def __init__(self, name, args, line=0):
        self.name = name     # 函式名
        self.args = args     # 引數運算式清單
        self.line = line

class ArrayAccess(Node):
    """【陣列存取】對應  arr[i]  —— base 是陣列、index 是索引"""
    def __init__(self, base, index, line=0):
        self.base = base     # 陣列運算式（Ident 或指標運算式）
        self.index = index
        self.line = line

class Ident(Node):
    """【識別符】對應一個變數名，如  x、count"""
    def __init__(self, name, line=0):
        self.name = name
        self.line = line

class IntLit(Node):
    """【整數字面值】對應  42、0xFF"""
    def __init__(self, value, line=0):
        self.value = value
        self.line = line

class CharLit(Node):
    """【字元字面值】對應  'A'（存的是 ASCII 整數）"""
    def __init__(self, value, line=0):
        self.value = value   # 整數（ASCII 碼）
        self.line = line

class StrLit(Node):
    """【字串字面值】對應  "hello"（跳脫字元已解碼完成）"""
    def __init__(self, value, line=0):
        self.value = value   # Python 字串
        self.line = line

class SwitchStmt(Node):
    """【switch 多重分支｜加分功能】對應  switch (x) { case 1: ... break; default: ... }"""
    def __init__(self, expr, cases, default_stmts, line=0):
        self.expr          = expr           # 要比對的運算式
        self.cases         = cases          # 清單：每項是 (case 值, [該分支的陳述句...])
        self.default_stmts = default_stmts  # default 分支的陳述句，或 None
        self.line          = line
