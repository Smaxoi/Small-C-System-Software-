/* Test 04: while / for / do-while / break / continue */
int main() {
    int i;
    int sum = 0;

    /* while 迴圈：1+2+...+10 */
    i = 1;
    while (i <= 10) {
        sum += i;
        i = i + 1;
    }
    printf("sum1to10=%d\n", sum);

    /* for 迴圈：印偶數 2-10 */
    for (i = 1; i <= 10; i = i + 1) {
        if (i % 2 != 0) continue;
        printf("%d ", i);
    }
    printf("\n");

    /* for 迴圈：break 在 7 前停止 */
    for (i = 1; i <= 20; i = i + 1) {
        if (i > 6) break;
        printf("%d ", i);
    }
    printf("\n");

    /* do-while */
    i = 1;
    sum = 0;
    do {
        sum += i;
        i = i + 1;
    } while (i <= 5);
    printf("dowhile=%d\n", sum);

    return 0;
}
