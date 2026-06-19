# Python'ning eng so'nggi yengil versiyasi
FROM python:3.11-slim

# Loyiha papkasini yaratish va unga kirish
WORKDIR /app

# Kutubxonalar ro'yxatini ko'chirib o'tish
COPY requirements.txt .

# Kutubxonalarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Asosiy kodni ko'chirib o'tish
COPY bot.py .

# Botni ishga tushirish
CMD ["python", "bot.py"]