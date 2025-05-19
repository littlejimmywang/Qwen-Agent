FROM --platform=linux/amd64 python:3.10-slim-bullseye

# Set environment variables to prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the entire project
COPY . .

# Install Python dependencies
# Install setuptools and wheel first for setup.py
RUN pip install --no-cache-dir setuptools wheel

# Install the package with extras for code_interpreter, mcp, rag, and python_executor
# This will also install dependencies from install_requires
# GUI dependencies removed as the target environment has no GUI
RUN pip install --no-cache-dir .[code_interpreter,mcp,rag,python_executor]

# EXPOSE 7860 # Removed as GUI is not used

# Command to run the application
# CMD ["python", "examples/assistant_psd.py"] # Removed, no default command 