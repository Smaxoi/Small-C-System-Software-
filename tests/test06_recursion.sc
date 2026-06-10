/* Test 06: 遞迴呼叫 — 階乘與 GCD */
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int gcd(int a, int b) {
    if (b == 0) return a;
    return gcd(b, a % b);
}

int power(int base, int exp) {
    if (exp == 0) return 1;
    return base * power(base, exp - 1);
}

int main() {
    int i;
    for (i = 0; i <= 7; i = i + 1) {
        printf("%d! = %d\n", i, factorial(i));
    }
    printf("gcd(48,18) = %d\n", gcd(48, 18));
    printf("gcd(100,75) = %d\n", gcd(100, 75));
    printf("2^10 = %d\n", power(2, 10));
    return 0;
}
