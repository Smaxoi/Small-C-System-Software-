/* Test 03: if/else 條件分支、關係與邏輯運算 */
int classify(int n) {
    if (n > 0) {
        return 1;
    } else if (n < 0) {
        return -1;
    } else {
        return 0;
    }
}

int main() {
    int i;
    int scores[5];
    scores[0] = 95;
    scores[1] = 82;
    scores[2] = 70;
    scores[3] = 55;
    scores[4] = 40;

    for (i = 0; i < 5; i = i + 1) {
        int s;
        s = scores[i];
        if (s >= 90) {
            printf("%d: A\n", s);
        } else if (s >= 80) {
            printf("%d: B\n", s);
        } else if (s >= 70) {
            printf("%d: C\n", s);
        } else {
            printf("%d: F\n", s);
        }
    }

    printf("%d %d %d\n", classify(5), classify(0), classify(-3));
    printf("%d\n", 5 >= 3 && 2 < 10);
    printf("%d\n", 5 > 10 || 3 < 4);
    printf("%d\n", !(5 == 5));
    return 0;
}
