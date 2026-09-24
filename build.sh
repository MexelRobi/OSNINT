#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   OSNINT Standalone Build Compiler      ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Virtual Environment aktivieren, falls nicht aktiv
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
fi

echo -e "${BLUE}[*] Compiling full standalone executable...${NC}"

# --collect-binaries sichert den C++ Kern von llama-cpp
# --collect-all sichert das gesamte huggingface_hub Ökosystem inside der Executable
pyinstaller --onefile \
            --clean \
            --name "osnint" \
            --collect-binaries "llama_cpp" \
            --collect-all "huggingface_hub" \
            osnint_tool.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[+] Build successful!${NC}"
    echo -e "${GREEN}[+] Your standalone binary is ready at: ${YELLOW}dist/osnint${NC}"
    echo -e "${BLUE}=========================================${NC}"
else
    echo -e "${RED}[!] Build failed.${NC}"
    exit 1
fi
