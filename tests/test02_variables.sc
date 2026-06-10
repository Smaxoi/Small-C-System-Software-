/* Test 02: 變數宣告、複合指定、字元 */
int main() {
    int x = 10;
    int y = 20;
    int z;
    z = x + y;
    printf("x=%d, y=%d, z=%d\n", x, y, z);
    x += 5;
    y -= 3;
    printf("x=%d, y=%d\n", x, y);
    x *= 2;
    y /= 2;
    z %= 7;
    printf("x=%d, y=%d, z=%d\n", x, y, z);
    char ch = 'A';
    printf("ch=%c, code=%d\n", ch, ch);
    ch = ch + 1;
    printf("ch=%c, code=%d\n", ch, ch);
    return 0;
}
