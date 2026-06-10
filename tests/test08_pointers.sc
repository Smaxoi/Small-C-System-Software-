/* Test 08: 指標操作 — 取址、取值、透過指標修改 */
void swap(int *a, int *b) {
    int tmp;
    tmp = *a;
    *a = *b;
    *b = tmp;
}

void increment(int *p) {
    *p = *p + 1;
}

int main() {
    int x = 10;
    int y = 20;
    int *p;

    p = &x;
    printf("x=%d, *p=%d\n", x, *p);

    *p = 99;
    printf("x=%d after *p=99\n", x);

    p = &y;
    increment(p);
    printf("y=%d after increment\n", y);

    int a = 3;
    int b = 7;
    printf("before: a=%d b=%d\n", a, b);
    swap(&a, &b);
    printf("after:  a=%d b=%d\n", a, b);

    return 0;
}
