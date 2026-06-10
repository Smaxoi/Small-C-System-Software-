/* Test 07: 一維陣列操作 */
int sum_array(int *arr, int n) {
    int i;
    int total = 0;
    for (i = 0; i < n; i = i + 1) {
        total += arr[i];
    }
    return total;
}

void reverse(int *arr, int n) {
    int i;
    int tmp;
    for (i = 0; i < n / 2; i = i + 1) {
        tmp = arr[i];
        arr[i] = arr[n - 1 - i];
        arr[n - 1 - i] = tmp;
    }
}

int main() {
    int data[8];
    int i;

    for (i = 0; i < 8; i = i + 1) {
        data[i] = (i + 1) * 10;
    }

    for (i = 0; i < 8; i = i + 1) {
        printf("%d ", data[i]);
    }
    printf("\n");

    printf("sum=%d\n", sum_array(data, 8));

    reverse(data, 8);
    for (i = 0; i < 8; i = i + 1) {
        printf("%d ", data[i]);
    }
    printf("\n");

    return 0;
}
