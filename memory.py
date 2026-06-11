# memory.py - Small-C 直譯器的「記憶體模型」與「作用域管理」
#
# 這個檔案做兩件事：
#   1. Memory  ── 模擬 C 的記憶體（一格一格的位址空間）
#   2. Scope   ── 管理變數作用域（哪個變數在哪個範圍看得到）

class MemError(Exception):
    pass


class Memory:
    """平坦位址空間：把記憶體想成一排格子，每格存一個整數。"""

    # 【核心】位址從 0x1000 開始，把 0 留給 NULL 指標（避免和真實位址 0 混淆）
    BASE_ADDR = 0x1000

    def __init__(self):
        self.cells = {}                  # 核心資料：{ 位址 -> 數值 }，整個記憶體就是這個字典
        self.next_addr = Memory.BASE_ADDR  # 下一塊可配置的空位址

    def alloc(self, count=1, fill=0):
        """【配置記憶體】要 count 個連續格子，回傳起始位址（像 malloc）。"""
        addr = self.next_addr
        for i in range(count):
            self.cells[addr + i] = fill   # 把這幾格先填 0
        self.next_addr += count           # 指標往後移，下次從新位置配置
        return addr

    def valid(self, addr):
        return addr in self.cells          # 這個位址有沒有被配置過

    def read(self, addr):
        """【讀記憶體】讀某個位址的值；沒配置過就報錯。"""
        if addr not in self.cells:
            raise MemError(f"Invalid memory read at 0x{addr:X}")
        return self.cells[addr]

    def write(self, addr, value):
        """【寫記憶體】把值寫進某位址，並模擬 C 的 32 位元整數溢位。"""
        if addr not in self.cells:
            raise MemError(f"Invalid memory write at 0x{addr:X}")
        # 【核心】32-bit 有號數環繞：超過範圍就回繞，模擬真實 int 溢位行為
        value = int(value)
        if value > 2147483647:
            value = value - (1 << 32)
        elif value < -2147483648:
            value = value + (1 << 32)
        self.cells[addr] = value

    def read_string(self, addr):
        """【讀字串】從 addr 開始一格一格讀，遇到 0（'\\0'）就停 —— 這就是 C 字串。"""
        chars = []
        while self.cells.get(addr, 0) != 0:   # 核心：以 null 結尾判斷字串結束
            chars.append(chr(self.cells[addr] & 0xFF))
            addr += 1
            if len(chars) > 65536:             # 保險：避免沒結尾時無限迴圈
                break
        return ''.join(chars)

    def write_string(self, addr, s):
        """【寫字串】把字串逐字寫入記憶體，最後補一個 0 當結尾。"""
        for i, c in enumerate(s):
            if addr + i not in self.cells:
                raise MemError(f"String write out of bounds at 0x{addr+i:X}")
            self.cells[addr + i] = ord(c) & 0xFF
        null_addr = addr + len(s)
        if null_addr in self.cells:
            self.cells[null_addr] = 0          # 核心：補 '\0' 結尾

    def alloc_string_literal(self, s):
        """【配置字串常數】給 "..." 字面值配一塊記憶體並寫入，回傳起始位址。"""
        addr = self.alloc(len(s) + 1)          # +1 是給結尾的 '\0'
        for i, c in enumerate(s):
            self.cells[addr + i] = ord(c) & 0xFF
        self.cells[addr + len(s)] = 0
        return addr

    def reset(self):
        """清空整個記憶體（每次重新 RUN 程式時呼叫）。"""
        self.cells.clear()
        self.next_addr = Memory.BASE_ADDR


# ── 變數資訊 ────────────────────────────────────────────────────────────────

class VarInfo:
    """【一個變數的完整身分證】記錄它的型別、位址、大小、是不是陣列/指標。"""

    def __init__(self, type_, addr, size=1, is_array=False, is_pointer=False):
        self.type_ = type_           # 型別：'int' | 'char' | 'int*' | 'char*' | 'void'
        self.addr = addr             # 它在記憶體的位址（陣列的話是起始位址）
        self.size = size             # 純量=1，陣列=N
        self.is_array = is_array     # 是不是陣列
        self.is_pointer = is_pointer # 是不是指標

    def __repr__(self):
        return (f"VarInfo({self.type_!r}, addr=0x{self.addr:X}, "
                f"size={self.size}, arr={self.is_array}, ptr={self.is_pointer})")


# ── 作用域 ──────────────────────────────────────────────────────────────────

class Scope:
    """【作用域】一層變數表，串成鏈狀（自己找不到就往外層 parent 找）。"""

    def __init__(self, parent=None, func_name=None):
        self.vars = {}              # 核心資料：{ 變數名 -> VarInfo }
        self.parent = parent        # 外層作用域（全域是最外層，parent=None）
        self.func_name = func_name  # 所屬函式名（給 TRACE/除錯用）

    def define(self, name, info: VarInfo):
        """在「目前這層」宣告一個變數。"""
        self.vars[name] = info

    def lookup(self, name) -> VarInfo:
        """【變數查找鏈】先找自己這層，找不到就往外層一路找上去。"""
        if name in self.vars:
            return self.vars[name]            # 核心：本層找到直接回傳
        if self.parent is not None:
            return self.parent.lookup(name)   # 核心：往外層遞迴找
        return None                           # 全找不到 → 未定義變數

    def lookup_local(self, name) -> VarInfo:
        """只找「目前這層」，不往外找（判斷是否重複宣告時用）。"""
        return self.vars.get(name)

    def all_vars(self):
        """蒐集所有看得到的變數（VARS 指令用）；內層遮蔽外層的同名變數。"""
        result = {}
        scope = self
        while scope is not None:
            for name, info in scope.vars.items():
                if name not in result:        # 先遇到的（內層）優先，外層同名被遮蔽
                    result[name] = info
            scope = scope.parent
        return result
