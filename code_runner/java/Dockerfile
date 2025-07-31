FROM openjdk:17-slim

# Set working directory
WORKDIR /app

# Copy everything into /app
COPY . .

# Download gson.jar for JSON output
RUN apt-get update && apt-get install -y curl && \
    curl -L -o gson.jar https://repo1.maven.org/maven2/com/google/code/gson/gson/2.10.1/gson-2.10.1.jar && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Compile run.java with gson support
RUN javac -cp gson.jar run.java

# Run with gson on the classpath
CMD ["java", "-cp", ".:gson.jar", "run"]
