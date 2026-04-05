# 使用輕量版 Python
FROM python:3.11-slim

# 設定容器內的工作目錄
WORKDIR /app

# 複製依賴清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製目前的程式碼到容器
COPY . .

# 讓外部可以連到 5000 埠
EXPOSE 5000

# 啟動指令
CMD ["python", "app.py"]
