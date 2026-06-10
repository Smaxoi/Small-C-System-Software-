/* Test 11: 語法錯誤偵測
   這個程式故意含有語法錯誤，用來驗證 CHECK 指令能正確回報。
   第 4 行 int x = 10 缺少分號。*/
int main() {
    int x = 10
    return 0;
}
