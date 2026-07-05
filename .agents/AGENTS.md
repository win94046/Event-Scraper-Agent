# 專案特定規則 (Project-Scoped Rules)

- **Python 執行規範**: 在此專案中執行任何 Python 指令時，必須一律以 `venv\Scripts\python` 作為開頭，以確保使用正確的虛擬環境。

- **環境變數與金鑰安全規範**:
  - 本專案實作環境變數隔離。`.env` 實體檔案中只會存放佔位符（如 `YOUR_GEMINI_API_KEY_HERE`），絕對不能寫入真實金鑰。
  - 當需要執行與測試專案（例如需要呼叫 API 或發送郵件）時，請優先以 PowerShell 命令注入環境變數，範例如下：
    ```powershell
    $env:GEMINI_API_KEY="您的真實金鑰"
    $env:SENDER_PASSWORD="您的應用程式密碼"
    venv\Scripts\python main.py
    ```