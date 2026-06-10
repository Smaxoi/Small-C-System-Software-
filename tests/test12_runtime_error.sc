/* Test 12: 執行期錯誤偵測 — 本程式故意引發錯誤驗證解譯器不崩潰 */
int main() {
    int x = 10 / 0;
    return 0;
}
