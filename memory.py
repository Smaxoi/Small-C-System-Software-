# memory.py - Memory model and scope management for Small-C interpreter

class MemError(Exception):
    pass

class Memory:
    """Flat address space. Each cell holds one integer value."""

    BASE_ADDR = 0x1000

    def __init__(self):
        self.cells = {}
        self.next_addr = Memory.BASE_ADDR

    def alloc(self, count=1, fill=0):
        """Allocate `count` cells, return base address."""
        addr = self.next_addr
        for i in range(count):
            self.cells[addr + i] = fill
        self.next_addr += count
        return addr

    def valid(self, addr):
        return addr in self.cells

    def read(self, addr):
        if addr not in self.cells:
            raise MemError(f"Invalid memory read at 0x{addr:X}")
        return self.cells[addr]

    def write(self, addr, value):
        if addr not in self.cells:
            raise MemError(f"Invalid memory write at 0x{addr:X}")
        # Clamp to 32-bit signed
        value = int(value)
        if value > 2147483647:
            value = value - (1 << 32)
        elif value < -2147483648:
            value = value + (1 << 32)
        self.cells[addr] = value

    def read_string(self, addr):
        """Read null-terminated char array from memory."""
        chars = []
        while self.cells.get(addr, 0) != 0:
            chars.append(chr(self.cells[addr] & 0xFF))
            addr += 1
            if len(chars) > 65536:
                break
        return ''.join(chars)

    def write_string(self, addr, s):
        """Write null-terminated string into memory starting at addr."""
        for i, c in enumerate(s):
            if addr + i not in self.cells:
                raise MemError(f"String write out of bounds at 0x{addr+i:X}")
            self.cells[addr + i] = ord(c) & 0xFF
        null_addr = addr + len(s)
        if null_addr in self.cells:
            self.cells[null_addr] = 0

    def alloc_string_literal(self, s):
        """Allocate and write a string literal, return base address."""
        addr = self.alloc(len(s) + 1)
        for i, c in enumerate(s):
            self.cells[addr + i] = ord(c) & 0xFF
        self.cells[addr + len(s)] = 0
        return addr

    def reset(self):
        self.cells.clear()
        self.next_addr = Memory.BASE_ADDR


# ── Variable info ──────────────────────────────────────────────────────────

class VarInfo:
    def __init__(self, type_, addr, size=1, is_array=False, is_pointer=False):
        self.type_ = type_           # 'int' | 'char' | 'int*' | 'char*' | 'void'
        self.addr = addr             # memory address of variable (or base of array)
        self.size = size             # 1 for scalar, N for array
        self.is_array = is_array
        self.is_pointer = is_pointer

    def __repr__(self):
        return (f"VarInfo({self.type_!r}, addr=0x{self.addr:X}, "
                f"size={self.size}, arr={self.is_array}, ptr={self.is_pointer})")


# ── Scope ──────────────────────────────────────────────────────────────────

class Scope:
    def __init__(self, parent=None, func_name=None):
        self.vars = {}           # name -> VarInfo
        self.parent = parent
        self.func_name = func_name  # name of enclosing function (for TRACE/debug)

    def define(self, name, info: VarInfo):
        self.vars[name] = info

    def lookup(self, name) -> VarInfo:
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name) -> VarInfo:
        return self.vars.get(name)

    def all_vars(self):
        """Return all variables visible in this scope (for VARS command)."""
        result = {}
        scope = self
        while scope is not None:
            for name, info in scope.vars.items():
                if name not in result:
                    result[name] = info
            scope = scope.parent
        return result
