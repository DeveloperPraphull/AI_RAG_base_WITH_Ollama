#!/bin/bash

# Start Ollama in the background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
for i in {1..60}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    echo "Attempt $i: Waiting for Ollama..."
    sleep 1
done

# Pull the model
echo "Pulling llama3.2 model..."
ollama pull llama3.2

echo "Model ready. Ollama is running."
wait $OLLAMA_PID
