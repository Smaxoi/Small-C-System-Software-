"""Generate test_input.txt for the full grading rubric test."""
lines = []

# ── Step 1: ABOUT / HELP ────────────────────────────────────────────────────
lines += ['ABOUT', 'HELP']

# ── Step 2: Arithmetic ──────────────────────────────────────────────────────
lines += [
    'printf("%d\\n", 3 + 4 * 5 - 2);',
    'printf("%d\\n", (3 + 4) * (5 - 2));',
    'printf("%d\\n", 100 / 7);',
    'printf("%d\\n", 100 % 7);',
    'printf("%d\\n", -15 / 4);',
]

# ── Step 3: Relational / logical / bitwise ──────────────────────────────────
lines += [
    'printf("%d %d %d\\n", 10 > 5, 10 < 5, 10 == 10);',
    'printf("%d %d\\n", 10 > 5 && 3 < 1, 10 > 5 || 3 < 1);',
    'printf("%d\\n", 0xAB & 0x0F);',
    'printf("%d\\n", 1 << 10);',
    'printf("0x%x\\n", 0xF0 | 0x0D);',
]

# ── Step 4: Variables / math / char ─────────────────────────────────────────
lines += [
    'int x = 25;',
    'int y = -18;',
    'printf("abs(%d) = %d\\n", y, abs(y));',
    'printf("max=%d, min=%d\\n", max(x, 30), min(x, 30));',
    'printf("pow(2,16) = %d\\n", pow(2, 16));',
    'printf("sqrt(625) = %d\\n", sqrt(625));',
    "char ch = 'Z';",
    'printf("ch=%c, code=%d, next=%c\\n", ch, ch, ch + 1);',
    'VARS',
]

# ── Step 5: String functions ─────────────────────────────────────────────────
lines += [
    'char buf[50];',
    'strcpy(buf, "System");',
    'strcat(buf, " Software");',
    'printf("buf=\\"%s\\", len=%d\\n", buf, strlen(buf));',
    'printf("cmp=%d\\n", strcmp("apple", "banana"));',
    'printf("atoi=%d\\n", atoi("2026"));',
    'char numstr[20];',
    'itoa(12345, numstr);',
    'printf("itoa result: %s\\n", numstr);',
]

# ── Step 6: NEW + APPEND selection sort ─────────────────────────────────────
lines += ['NEW']
lines += ['APPEND']
lines += [
    '/* Selection Sort with Statistics */',
    '#define SIZE 8',
    '',
    '// Swap two integers via pointers',
    'void swap(int *a, int *b) {',
    '    int temp;',
    '    temp = *a;',
    '    *a = *b;',
    '    *b = temp;',
    '}',
    '',
    'void selection_sort(int *arr, int n) {',
    '    int i;',
    '    int j;',
    '    int min_idx;',
    '    for (i = 0; i < n - 1; i = i + 1) {',
    '        min_idx = i;',
    '        for (j = i + 1; j < n; j = j + 1) {',
    '            if (arr[j] < arr[min_idx]) {',
    '                min_idx = j;',
    '            }',
    '        }',
    '        if (min_idx != i) {',
    '            swap(&arr[i], &arr[min_idx]);',
    '        }',
    '    }',
    '}',
    '',
    'int compute_sum(int *arr, int n) {',
    '    int i;',
    '    int total = 0;',
    '    for (i = 0; i < n; i = i + 1) {',
    '        total += arr[i];',
    '    }',
    '    return total;',
    '}',
    '',
    'int find_max(int *arr, int n) {',
    '    int i;',
    '    int m = arr[0];',
    '    for (i = 1; i < n; i = i + 1) {',
    '        m = max(m, arr[i]);',
    '    }',
    '    return m;',
    '}',
    '',
    'int find_min(int *arr, int n) {',
    '    int i;',
    '    int m = arr[0];',
    '    for (i = 1; i < n; i = i + 1) {',
    '        m = min(m, arr[i]);',
    '    }',
    '    return m;',
    '}',
    '',
    'int main() {',
    '    int data[SIZE];',
    '    int i;',
    '    int total;',
    '',
    '    data[0] = 64; data[1] = 25; data[2] = 12; data[3] = 22;',
    '    data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 33;',
    '',
    '    printf("Original: ");',
    '    for (i = 0; i < SIZE; i = i + 1) {',
    '        printf("%d ", data[i]);',
    '    }',
    '    printf("\\n");',
    '',
    '    printf("Max = %d\\n", find_max(data, SIZE));',
    '    printf("Min = %d\\n", find_min(data, SIZE));',
    '',
    '    total = compute_sum(data, SIZE);',
    '    printf("Sum = %d\\n", total);',
    '    printf("Avg = %d\\n", total / SIZE);',
    '',
    '    selection_sort(data, SIZE);',
    '',
    '    printf("Sorted:   ");',
    '    for (i = 0; i < SIZE; i = i + 1) {',
    '        printf("%d ", data[i]);',
    '    }',
    '    printf("\\n");',
    '',
    '    return 0;',
    '}',
    '.',   # end APPEND
]

# ── Step 7: LIST ─────────────────────────────────────────────────────────────
lines += ['LIST 1-5', 'LIST 56']

# ── Step 8: CHECK / RUN ──────────────────────────────────────────────────────
lines += ['CHECK', 'RUN']

# ── Step 9: FUNCS ────────────────────────────────────────────────────────────
lines += ['FUNCS']

# ── Step 10: SAVE + EDIT 62 ──────────────────────────────────────────────────
lines += [
    'SAVE test_a.sc',
    'EDIT 62',
    '    data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 77;',
    'LIST 61-63',
    'RUN',
]

# ── Step 11: DELETE + INSERT ─────────────────────────────────────────────────
lines += [
    'DELETE 3',
    'LIST 1-5',
    'INSERT 3',
    '',       # blank line to insert
    '.',      # end INSERT
    'LIST 1-5',
]

# ── Step 12: TRACE ───────────────────────────────────────────────────────────
lines += ['NEW', 'y']   # y = confirm clear (modified=True after APPEND)
lines += ['APPEND']
lines += [
    'int gcd(int a, int b) {',
    '    while (b != 0) {',
    '        int temp;',
    '        temp = b;',
    '        b = a % b;',
    '        a = temp;',
    '    }',
    '    return a;',
    '}',
    '',
    'int main() {',
    '    printf("GCD(48,18) = %d\\n", gcd(48, 18));',
    '    return 0;',
    '}',
    '.',
]
lines += ['TRACE ON', 'RUN', 'TRACE OFF']

# ── Step 13: do/while + break/continue ──────────────────────────────────────
lines += ['NEW', 'y']
lines += [
    'int n = 1;',
    'do {',
    '    if (n % 3 == 0) {',
    '        n = n + 1;',
    '        continue;',
    '    }',
    '    if (n > 12) break;',
    '    printf("%d ", n);',
    '    n = n + 1;',
    '} while (n <= 20);',
    'printf("\\n");',
]

# ── Step 14: Error handling ──────────────────────────────────────────────────
lines += [
    'printf("%d\\n", 10 / 0);',
    'printf("%d\\n", sqrt(-4));',
    'int bad = ;',
    'int arr[3];',
    'arr[5] = 10;',
]

# ── Step 15: LOAD + RUN original ─────────────────────────────────────────────
lines += ['NEW', 'LOAD test_a.sc', 'RUN']

# ── Step 16: CLEAR + QUIT ────────────────────────────────────────────────────
lines += ['CLEAR', 'QUIT']

with open('test_input.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print(f'Written {len(lines)} commands to test_input.txt')
