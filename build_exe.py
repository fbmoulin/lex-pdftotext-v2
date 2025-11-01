#!/usr/bin/env python3
"""
Script de Build para PDF Legal Extractor

Gera executável Windows (.exe) usando PyInstaller.
"""

import sys
import os
import shutil
from pathlib import Path
import subprocess


def check_requirements():
    """Verifica se PyInstaller está instalado."""
    try:
        import PyInstaller
        print("✅ PyInstaller encontrado")
        return True
    except ImportError:
        print("❌ PyInstaller não encontrado")
        print("   Instale com: pip install pyinstaller")
        return False


def clean_build_dirs():
    """Limpa diretórios de build anteriores."""
    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['*.spec']

    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"🗑️  Removendo {dir_name}/")
            shutil.rmtree(dir_name)

    for pattern in files_to_clean:
        for file in Path('.').glob(pattern):
            print(f"🗑️  Removendo {file}")
            file.unlink()


def build_executable():
    """Constrói o executável com PyInstaller."""
    print("\n🔨 Construindo executável...\n")

    # Verificar se ícone existe
    icon_path = Path('assets/logo.ico')
    icon_arg = f'--icon={icon_path}' if icon_path.exists() else ''

    if not icon_path.exists():
        print("⚠️  Ícone não encontrado em assets/logo.ico")
        print("   O executável será criado sem ícone personalizado")
        print("   Veja assets/ICON_CREATION.md para criar um ícone\n")

    # Comando PyInstaller
    cmd = [
        'pyinstaller',
        '--onefile',              # Gerar único executável
        '--windowed',             # Sem console (GUI apenas)
        '--name=PDF2MD',          # Nome do executável
        '--add-data=assets;assets',  # Incluir assets
        '--add-data=src;src',        # Incluir src
    ]

    if icon_arg:
        cmd.append(icon_arg)

    # Hidden imports (dependências que PyInstaller pode não detectar)
    hidden_imports = [
        'fitz',
        'PyMuPDF',
        'webview',
        'click',
        'tqdm',
    ]

    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')

    # Entry point
    cmd.append('app_ui.py')

    # Executar PyInstaller
    print(f"Comando: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao construir executável: {e}")
        return False


def verify_build():
    """Verifica se o build foi bem-sucedido."""
    exe_path = Path('dist/PDF2MD.exe')

    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n✅ Executável criado com sucesso!")
        print(f"   📍 Localização: {exe_path}")
        print(f"   📦 Tamanho: {size_mb:.2f} MB")
        return True
    else:
        print(f"\n❌ Executável não encontrado em: {exe_path}")
        return False


def create_portable_package():
    """Cria pacote portável (opcional)."""
    print("\n📦 Criando pacote portável...")

    dist_dir = Path('dist')
    package_dir = dist_dir / 'PDF2MD_Portable'

    if package_dir.exists():
        shutil.rmtree(package_dir)

    package_dir.mkdir(parents=True)

    # Copiar executável
    shutil.copy(dist_dir / 'PDF2MD.exe', package_dir)

    # Copiar README
    if Path('README.md').exists():
        shutil.copy('README.md', package_dir)

    # Criar README de instalação
    install_readme = package_dir / 'LEIA-ME.txt'
    install_readme.write_text("""
PDF Legal Extractor - Versão Portável
====================================

INSTALAÇÃO:
1. Extraia todos os arquivos para uma pasta no seu computador
2. Execute PDF2MD.exe
3. Crie um atalho no desktop se desejar

REQUISITOS:
- Windows 10 ou superior
- Nenhuma instalação adicional necessária

SEGURANÇA:
Se o Windows Defender bloquear o executável:
1. Clique em "Mais informações"
2. Clique em "Executar assim mesmo"

(Isso acontece porque o executável não tem assinatura digital)

SUPORTE:
Para questões ou problemas, contate o desenvolvedor.

Versão: 1.0
""", encoding='utf-8')

    # Criar arquivo zip
    print(f"   Criando PDF2MD_Portable.zip...")
    shutil.make_archive(
        str(dist_dir / 'PDF2MD_Portable'),
        'zip',
        package_dir
    )

    print(f"✅ Pacote portável criado: dist/PDF2MD_Portable.zip")


def main():
    """Função principal do script de build."""
    print("=" * 60)
    print("PDF Legal Extractor - Build Script")
    print("=" * 60)

    # Verificar requisitos
    if not check_requirements():
        sys.exit(1)

    # Limpar builds anteriores
    print("\n🧹 Limpando builds anteriores...")
    clean_build_dirs()

    # Construir executável
    if not build_executable():
        sys.exit(1)

    # Verificar build
    if not verify_build():
        sys.exit(1)

    # Criar pacote portável (opcional)
    try:
        create_portable_package()
    except Exception as e:
        print(f"⚠️  Erro ao criar pacote portável: {e}")
        print("   (Isso não afeta o executável principal)")

    # Instruções finais
    print("\n" + "=" * 60)
    print("🎉 Build concluído com sucesso!")
    print("=" * 60)
    print("\nPRÓXIMOS PASSOS:")
    print("\n1. Teste o executável:")
    print("   > dist\\PDF2MD.exe")
    print("\n2. Para criar instalador Windows:")
    print("   > Abra installer.iss no Inno Setup Compiler")
    print("   > Clique em 'Compile'")
    print("\n3. Distribua:")
    print("   - Executável: dist/PDF2MD.exe (stand-alone)")
    print("   - Portável: dist/PDF2MD_Portable.zip")
    print("   - Instalador: Output/PDF2MD_Setup.exe (após Inno Setup)")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
