FROM node:18-slim

# add curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl tini && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# have nodemon available for local dev use (file watching)
RUN npm install -g nodemon

# Kopiujemy package.json i package-lock.json najpierw
COPY package*.json ./

# Instalujemy zależności z pełnym logowaniem
RUN npm install --verbose

# Kopiujemy resztę plików
COPY . .

# Kopiujemy plik obrazu
COPY ../media/catvsdog.jpg ./media/

# Dodajemy logi podczas budowania
RUN echo "Building application..." && \
    ls -la && \
    echo "Node version: $(node -v)" && \
    echo "NPM version: $(npm -v)"

ENV PORT=80
EXPOSE 80

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "server.js"]
