void swap(int *x, int *y) {
    int temp;
    temp = *x; *x = *y; *y = temp;
}

void bubble_sort(int *arr, int n) {
    int i; int j;
    for (i = 0; i < n - 1; i = i + 1)
        for (j = 0; j < n - 1 - i; j = j + 1)
            if (arr[j] > arr[j+1])
                swap(&arr[j], &arr[j+1]);
}

void print_array(int *arr, int n) {
    int i;
    for (i = 0; i < n; i = i + 1)
        printf("%d ", arr[i]);
    printf("\n");
}

int main() {
    int data[7];
    data[0] = 64; data[1] = 34; data[2] = 25;
    data[3] = 12; data[4] = 22; data[5] = 11; data[6] = 90;
    printf("Before sorting: ");
    print_array(data, 7);
    bubble_sort(data, 7);
    printf("After sorting:  ");
    print_array(data, 7);
    return 0;
}
