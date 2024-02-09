FROM python:3.9-slim

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install torch==2.0.1+cpu torchvision==0.15.2+cpu torchaudio==2.0.2 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

RUN gdown https://drive.google.com/uc?id=1I-Rv676N45aUgY7tcsazQE7fLzzb2LFr

# Download the image features from a Google Drive link
RUN gdown https://drive.google.com/uc?id=103LTvXhmbjPOVjDVbhwjjzHrsQLpskWt

# Move data.csv, image_features.npz to a directory named /data
RUN mkdir --parents /app/data && mv data.csv /app/data && mv image_features.npz /app/data

COPY . /app/

RUN chmod +x ./entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]