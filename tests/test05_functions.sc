/* Test 05: 函式定義與呼叫、參數傳遞 */
int add(int a, int b) {
    return a + b;
}

int multiply(int a, int b) {
    return a * b;
}

int max3(int a, int b, int c) {
    int m;
    m = a;
    if (b > m) m = b;
    if (c > m) m = c;
    return m;
}

void print_line(int n) {
    int i;
    for (i = 0; i < n; i = i + 1) {
        printf("-");
    }
    printf("\n");
}

int main() {
    printf("%d\n", add(3, 4));
    printf("%d\n", multiply(6, 7));
    printf("%d\n", max3(10, 25, 18));
    printf("%d\n", add(multiply(2, 3), multiply(4, 5)));
    print_line(8);
    return 0;
}
