int is_prime(int n) {
    int i;
    if (n < 2) return 0;
    for (i = 2; i * i <= n; i = i + 1)
        if (n % i == 0) return 0;
    return 1;
}

int main() {
    int i;
    int count = 0;
    printf("Prime numbers from 2 to 100:\n");
    for (i = 2; i <= 100; i = i + 1) {
        if (is_prime(i)) {
            printf("%d ", i);
            count = count + 1;
        }
    }
    printf("\nTotal: %d primes\n", count);
    return 0;
}
