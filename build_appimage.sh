#!/usr/bin/env bash
# Script para compilar o AppImage do OpenValora
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# Extrai a versão oficial do projeto
VERSION=$(python3 -c "
for line in open('app/main.py'):
    if line.startswith('__version__'):
        print(line.split('=')[1].strip(' \"\'\n'))
        break
")
VERSION=${VERSION:-0.1.0}

echo "=========================================================="
echo "  Construindo AppImage do OpenValora v${VERSION} (NBR 14653)"
echo "=========================================================="

# 0. Limpa completamente builds e arquivos anteriores para garantir que apenas a versão mais recente fique salva
echo "Limpando compilações anteriores em dist/ e build/..."
rm -rf build/OpenValora.AppDir build/ValoraOpen.AppDir dist/*
mkdir -p dist build

# 1. Compila executável atualizado com PyInstaller
echo "Compilando executável com PyInstaller..."
SPEC_FILE="openvalora.spec"
if [ ! -f "${SPEC_FILE}" ]; then
    SPEC_FILE="valoraopen.spec"
fi

if [ -d ".venv" ]; then
    .venv/bin/python -m PyInstaller --clean --noconfirm "${SPEC_FILE}"
else
    python3 -m PyInstaller --clean --noconfirm "${SPEC_FILE}"
fi

# Cria alias para compatibilidade com ambos os nomes
if [ -f "dist/openvalora" ] && [ ! -f "dist/valoraopen" ]; then
    cp dist/openvalora dist/valoraopen
elif [ -f "dist/valoraopen" ] && [ ! -f "dist/openvalora" ]; then
    cp dist/valoraopen dist/openvalora
fi

# 2. Cria a estrutura do AppDir
APPDIR="build/OpenValora.AppDir"
rm -rf "${APPDIR}"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/512x512/apps"
mkdir -p "${APPDIR}/usr/share/pixmaps"

echo "Montando estrutura AppDir..."
cp dist/openvalora "${APPDIR}/usr/bin/openvalora"
chmod +x "${APPDIR}/usr/bin/openvalora"
cp dist/openvalora "${APPDIR}/usr/bin/valoraopen" 2>/dev/null || true

cp packaging/AppRun "${APPDIR}/AppRun"
chmod +x "${APPDIR}/AppRun"

cp packaging/openvalora.desktop "${APPDIR}/openvalora.desktop"
cp packaging/openvalora.desktop "${APPDIR}/OpenValora.desktop"
cp packaging/openvalora.desktop "${APPDIR}/valoraopen.desktop"
cp packaging/openvalora.desktop "${APPDIR}/usr/share/applications/openvalora.desktop"
cp packaging/openvalora.desktop "${APPDIR}/usr/share/applications/OpenValora.desktop"
cp packaging/openvalora.desktop "${APPDIR}/usr/share/applications/valoraopen.desktop"

# Ícones oficiais na raiz do AppDir e temas do sistema
ICON_SRC="OpenValora.png"
if [ ! -f "${ICON_SRC}" ]; then
    ICON_SRC="ValoraOpen.png"
fi
cp "${ICON_SRC}" "${APPDIR}/OpenValora.png"
cp "${ICON_SRC}" "${APPDIR}/openvalora.png"
cp "${ICON_SRC}" "${APPDIR}/ValoraOpen.png"
cp "${ICON_SRC}" "${APPDIR}/valoraopen.png"
cp "${ICON_SRC}" "${APPDIR}/.DirIcon"

cp packaging/openvalora.png "${APPDIR}/usr/share/icons/hicolor/256x256/apps/openvalora.png" 2>/dev/null || cp packaging/valoraopen.png "${APPDIR}/usr/share/icons/hicolor/256x256/apps/openvalora.png"
cp packaging/openvalora.png "${APPDIR}/usr/share/icons/hicolor/256x256/apps/OpenValora.png" 2>/dev/null || cp packaging/valoraopen.png "${APPDIR}/usr/share/icons/hicolor/256x256/apps/OpenValora.png"
cp packaging/openvalora-512.png "${APPDIR}/usr/share/icons/hicolor/512x512/apps/openvalora.png" 2>/dev/null || cp packaging/valoraopen-512.png "${APPDIR}/usr/share/icons/hicolor/512x512/apps/openvalora.png"
cp packaging/openvalora-512.png "${APPDIR}/usr/share/icons/hicolor/512x512/apps/OpenValora.png" 2>/dev/null || cp packaging/valoraopen-512.png "${APPDIR}/usr/share/icons/hicolor/512x512/apps/OpenValora.png"

cp packaging/openvalora.png "${APPDIR}/usr/share/pixmaps/openvalora.png" 2>/dev/null || cp packaging/valoraopen.png "${APPDIR}/usr/share/pixmaps/openvalora.png"
cp packaging/openvalora.png "${APPDIR}/usr/share/pixmaps/OpenValora.png" 2>/dev/null || cp packaging/valoraopen.png "${APPDIR}/usr/share/pixmaps/OpenValora.png"

# 3. Baixa appimagetool se não estiver no sistema
APPIMAGETOOL="$(which appimagetool 2>/dev/null || true)"
if [ -z "${APPIMAGETOOL}" ]; then
    if [ ! -f "build/appimagetool-x86_64.AppImage" ]; then
        echo "Baixando appimagetool..."
        mkdir -p build
        curl -sSL -o build/appimagetool-x86_64.AppImage \
            https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
        chmod +x build/appimagetool-x86_64.AppImage
    fi
    APPIMAGETOOL="${SCRIPT_DIR}/build/appimagetool-x86_64.AppImage"
fi

# 4. Executa o appimagetool
echo "Empacotando AppImage com versão ${VERSION}..."
export ARCH=x86_64
APPIMAGE_NAME="OpenValora-${VERSION}-Linux-x86_64.AppImage"

if [ -n "${APPIMAGE_EXTRACT_AND_RUN}" ] || [ ! -e /dev/fuse ]; then
    "${APPIMAGETOOL}" --appimage-extract-and-run "${APPDIR}" "dist/${APPIMAGE_NAME}"
else
    "${APPIMAGETOOL}" "${APPDIR}" "dist/${APPIMAGE_NAME}" || \
    "${APPIMAGETOOL}" --appimage-extract-and-run "${APPDIR}" "dist/${APPIMAGE_NAME}"
fi

# Mantém também cópias com nomes complementares para compatibilidade
cp -f "dist/${APPIMAGE_NAME}" dist/OpenValora-Linux-x86_64.AppImage
cp -f "dist/${APPIMAGE_NAME}" dist/ValoraOpen-Linux-x86_64.AppImage
chmod +x dist/*.AppImage

# 5. Remove diretório temporário AppDir para manter somente o AppImage final e o binário
rm -rf "${APPDIR}"

echo "=========================================================="
echo "  Sucesso! Somente a versão mais recente foi salva em dist/:"
ls -lh dist/
echo "=========================================================="
