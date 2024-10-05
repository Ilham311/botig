# Gunakan image Python resmi sebagai base image
FROM python:3.10-slim

# Menetapkan direktori kerja di dalam container
WORKDIR /app

# Menyalin file requirements.txt ke dalam container
COPY requirements.txt .

# Install dependencies dari requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Menyalin semua file dari direktori saat ini ke dalam container
COPY . .

# Menetapkan perintah default yang akan dijalankan ketika container dimulai
CMD ["python", "run.py"]
