/* Test 09: 字串函式與工具函式 */
int main() {
    char buf[64];
    char numstr[20];

    strcpy(buf, "Hello");
    printf("len=%d\n", strlen(buf));

    strcat(buf, ", World");
    printf("%s\n", buf);
    printf("len=%d\n", strlen(buf));

    printf("cmp=%d\n", strcmp("apple", "apple"));
    printf("cmp=%d\n", strcmp("abc", "abd"));
    printf("cmp=%d\n", strcmp("z", "a"));

    printf("atoi=%d\n", atoi("12345"));
    printf("atoi=%d\n", atoi("-99"));

    itoa(42, numstr);
    printf("itoa=%s\n", numstr);
    itoa(-7, numstr);
    printf("itoa=%s\n", numstr);

    printf("abs=%d\n", abs(-42));
    printf("max=%d\n", max(10, 25));
    printf("min=%d\n", min(10, 25));
    printf("pow=%d\n", pow(2, 8));
    printf("sqrt=%d\n", sqrt(81));

    return 0;
}
