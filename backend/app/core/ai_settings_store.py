import json
import os
from pathlib import Path
from app.core.config import settings

# DATA_DIR: Đường dẫn tới thư mục lưu trữ dữ liệu cấu hình cục bộ của hệ thống
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
# SETTINGS_FILE: Đường dẫn file JSON lưu trữ cấu hình mô hình AI (Gemini) động
SETTINGS_FILE = DATA_DIR / "ai_settings.json"

def get_ai_settings():
    """
    Mục đích: Lấy ra cấu hình cài đặt AI hiện tại đang được áp dụng.
    Cơ chế hoạt động: Đọc tệp cấu hình từ đĩa `ai_settings.json` nếu có. Nếu không tồn tại hoặc lỗi, trả về cấu hình mặc định.
    """
    default_config = {
        "model": settings.GEMINI_MODEL,
        "api_key": settings.GEMINI_API_KEY or "",
        "system_version": "v4.2 Active",
        "performance_stats": {
            "accuracy": 98.4,
            "safety_overrides": 1.2,
            "latency": 850
        },
        "feature_modules": {
            "symptom_checker": True,
            "interaction_check": True,
            "gemini_integration": True
        },
        "disclaimers": [
            {
                "id": "desc_1",
                "title": "Emergency Prefix",
                "text": "\"If you are experiencing a medical emergency, please call 911 or visit the nearest emergency room immediately.\""
            },
            {
                "id": "desc_2",
                "title": "Standard Medical Disclaimer",
                "text": "\"I am an AI assistant, not a doctor. The information provided is for educational purposes and should not replace professional medical advice.\""
            }
        ]
    }
    
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "model": data.get("model", default_config["model"]),
                    "api_key": data.get("api_key", default_config["api_key"]) or "",
                    "system_version": data.get("system_version", default_config["system_version"]),
                    "performance_stats": data.get("performance_stats", default_config["performance_stats"]),
                    "feature_modules": data.get("feature_modules", default_config["feature_modules"]),
                    "disclaimers": data.get("disclaimers", default_config["disclaimers"])
                }
        except Exception:
            pass
            
    return default_config

def save_ai_settings(config_data: dict):
    """
    Mục đích: Lưu thông tin cấu hình AI mới (bao gồm tên mô hình, khóa API, modules...) vào tệp lưu trữ động.
    """
    # Lấy dữ liệu cũ để tránh ghi đè mất những field không truyền lên
    current_config = get_ai_settings()
    current_config.update(config_data)
    
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current_config, f, indent=2, ensure_ascii=False)
