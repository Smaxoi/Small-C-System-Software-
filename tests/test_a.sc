/* Selection Sort with Statistics */
#define SIZE 8

// Swap two integers via pointers
void swap(int *a, int *b) {
    int temp;
    temp = *a;
    *a = *b;
    *b = temp;
}

void selection_sort(int *arr, int n) {
    int i;
    int j;
    int min_idx;
    for (i = 0; i < n - 1; i = i + 1) {
        min_idx = i;
        for (j = i + 1; j < n; j = j + 1) {
            if (arr[j] < arr[min_idx]) {
                min_idx = j;
            }
        }
        if (min_idx != i) {
            swap(&arr[i], &arr[min_idx]);
        }
    }
}

int compute_sum(int *arr, int n) {
    int i;
    int total = 0;
    for (i = 0; i < n; i = i + 1) {
        total += arr[i];
    }
    return total;
}

int find_max(int *arr, int n) {
    int i;
    int m = arr[0];
    for (i = 1; i < n; i = i + 1) {
        m = max(m, arr[i]);
    }
    return m;
}

int find_min(int *arr, int n) {
    int i;
    int m = arr[0];
    for (i = 1; i < n; i = i + 1) {
        m = min(m, arr[i]);
    }
    return m;
}

int main() {
    int data[SIZE];
    int i;
    int total;

    data[0] = 64; data[1] = 25; data[2] = 12; data[3] = 22;
    data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 33;

    printf("Original: ");
    for (i = 0; i < SIZE; i = i + 1) {
        printf("%d ", data[i]);
    }
    printf("\n");

    printf("Max = %d\n", find_max(data, SIZE));
    printf("Min = %d\n", find_min(data, SIZE));

    total = compute_sum(data, SIZE);
    printf("Sum = %d\n", total);
    printf("Avg = %d\n", total / SIZE);

    selection_sort(data, SIZE);

    printf("Sorted:   ");
    for (i = 0; i < SIZE; i = i + 1) {
        printf("%d ", data[i]);
    }
    printf("\n");

    return 0;
}
