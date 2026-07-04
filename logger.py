import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    設定系統全域的日誌配置 (Logging Configuration)。
    日誌會同時輸出至 Console (標準輸出) 以及本地檔案 'logs/event_scraper.log'。
    檔案日誌具備自動輪轉功能，避免硬碟空間爆滿。
    """
    # 建立 logs 資料夾
    os.makedirs("logs", exist_ok=True)
    
    # 取得 Root Logger
    root_logger = logging.getLogger()
    
    # 如果已經設定過 Handler，則不重複設定 (防呆)
    if root_logger.handlers:
        return
        
    root_logger.setLevel(logging.DEBUG)  # 收集 DEBUG 層級以上的所有日誌

    # 定義日誌的輸出格式
    # 包含：時間、日誌層級、模組檔案名稱與行號、日誌訊息內容
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. 建立檔案日誌輸出 (Rotating File Handler)
    # 限制每個檔案大小最多 5MB，若超出則自動輪替，最多保留 5 個歷史記錄檔
    log_file_path = os.path.join("logs", "event_scraper.log")
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)  # 寫入檔案的日誌層級為 INFO (包含 WARNING, ERROR 等)
    file_handler.setFormatter(formatter)

    # 2. 建立終端機輸出 (Stream Handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # 終端機顯示 DEBUG 層級，方便開發階段進行細部排錯
    console_handler.setFormatter(formatter)

    # 將 Handler 註冊至 Root Logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("--- 日誌系統初始化完成，開始記錄系統運行軌跡 ---")
