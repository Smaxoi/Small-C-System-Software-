/* Test 10: #define 常數替換 + 位元運算 + switch/case */
#define MASK_LOW  0x0F
#define MASK_HIGH 0xF0
#define BITS      8

int main() {
    int val = 0xAB;

    printf("val=0x%x\n", val);
    printf("low nibble=%d\n",  val & MASK_LOW);
    printf("high nibble=%d\n", (val & MASK_HIGH) >> 4);
    printf("1<<%d=%d\n", BITS, 1 << BITS);
    printf("xor=0x%x\n", 0xFF ^ MASK_LOW);
    printf("not low=%d\n", ~MASK_LOW & 0xFF);

    /* switch/case */
    int i;
    for (i = 1; i <= 4; i = i + 1) {
        switch (i) {
            case 1: printf("one\n");   break;
            case 2: printf("two\n");   break;
            case 3: printf("three\n"); break;
            default: printf("other\n");
        }
    }

    return 0;
}
