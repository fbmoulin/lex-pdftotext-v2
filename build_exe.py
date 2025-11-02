#!/usr/bin/env python3
"""
Script de Build para PDF Legal Extractor

Gera executável Windows (.exe) usando PyInstaller com tratamento
robusto de erros e limpeza automática de arquivos bloqueados.
"""

import sys
import os
from pathlib import Path
import subprocess

# Import build utilities
try:
    from build_utils import pre_build_cleanup, verify_build_result
    HAS_BUILD_UTILS = True
except ImportError:
    HAS_BUILD_UTILS = False
    print("⚠️  build_utils.py não encontrado - usando limpeza básica")


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

    # Separador de path (Windows usa ; Linux/macOS usa :)
    separator = ';' if sys.platform == 'win32' else ':'

    # Comando PyInstaller
    cmd = [
        'pyinstaller',
        '--onefile',              # Gerar único executável
        '--windowed',             # Sem console (GUI apenas)
        '--name=PDF2MD',          # Nome do executável
        f'--add-data=assets{separator}assets',  # Incluir assets
        f'--add-data=src{separator}src',        # Incluir src
        '--clean',                # Limpar cache antes do build
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
        print(f"\n❌ Erro ao construir executável (código {e.returncode})")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return False


def create_portable_package():
    """Cria pacote portável (opcional)."""
    import shutil

    print("\n📦 Criando pacote portável...")

    dist_dir = Path('dist')
    package_dir = dist_dir / 'PDF2MD_Portable'

    # Determinar nome do executável
    exe_name = 'PDF2MD.exe' if sys.platform == 'win32' else 'PDF2MD'
    exe_path = dist_dir / exe_name

    if not exe_path.exists():
        print("   ⚠️  Executável não encontrado - pulando criação de pacote")
        return False

    try:
        # Remover pacote antigo se existir
        if package_dir.exists():
            shutil.rmtree(package_dir)

        package_dir.mkdir(parents=True)

        # Copiar executável
        shutil.copy(exe_path, package_dir)
        print(f"   ✓ Copiado: {exe_name}")

        # Copiar README
        if Path('README.md').exists():
            shutil.copy('README.md', package_dir)
            print("   ✓ Copiado: README.md")

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

FUNCIONALIDADES:
- Extrair texto de PDFs judiciais brasileiros
- Processamento em lote de múltiplos PDFs
- Mesclar documentos do mesmo processo
- Exportar resultados para diferentes locais

SUPORTE:
Para questões ou problemas, abra uma issue no GitHub:
https://github.com/fbmoulin/pdftotext

Versão: 1.0
Criado por: Lex Intelligentia
""", encoding='utf-8')
        print("   ✓ Criado: LEIA-ME.txt")

        # Criar arquivo zip
        print(f"   Criando PDF2MD_Portable.zip...")
        shutil.make_archive(
            str(dist_dir / 'PDF2MD_Portable'),
            'zip',
            package_dir
        )

        print(f"✅ Pacote portável criado: dist/PDF2MD_Portable.zip")
        return True

    except Exception as e:
        print(f"⚠️  Erro ao criar pacote portável: {e}")
        print("   (Isso não afeta o executável principal)")
        return False


def print_next_steps():
    """Imprime instruções de próximos passos."""
    print("\n" + "=" * 60)
    print("🎉 Build concluído!")
    print("=" * 60)
    print("\nPRÓXIMOS PASSOS:")
    print("\n1. Teste o executável:")
    if sys.platform == 'win32':
        print("   > .\\dist\\PDF2MD.exe")
    else:
        print("   > ./dist/PDF2MD")

    print("\n2. Para criar instalador Windows:")
    print("   > Abra installer.iss no Inno Setup Compiler")
    print("   > Clique em 'Compile' (F9)")

    print("\n3. Distribua:")
    print("   - Executável: dist/PDF2MD.exe (stand-alone)")
    print("   - Portável: dist/PDF2MD_Portable.zip")
    print("   - Instalador: Output/PDF2MD_Setup.exe (após Inno Setup)")
    print("\n" + "=" * 60)


def main():
    """Função principal do script de build."""
    print("=" * 60)
    print("PDF Legal Extractor - Build Script")
    print("=" * 60)

    # Verificar requisitos
    if not check_requirements():
        sys.exit(1)

    # Limpeza pré-build (usando build_utils se disponível)
    if HAS_BUILD_UTILS:
        cleanup_ok = pre_build_cleanup()
        if not cleanup_ok:
            print("⚠️  A limpeza não foi completamente bem-sucedida")
            print("   Continuando mesmo assim...\n")
    else:
        print("\n🧹 Pulando limpeza avançada (build_utils indisponível)\n")

    # Construir executável
    if not build_executable():
        print("\n" + "=" * 60)
        print("❌ Build falhou!")
        print("=" * 60)
        print("\nDICAS DE TROUBLESHOOTING:")
        print("1. Feche qualquer instância de PDF2MD.exe rodando")
        print("2. Feche todas as janelas do Explorer visualizando dist/")
        print("3. Execute: taskkill /F /IM PDF2MD.exe")
        print("4. Execute: Remove-Item dist -Recurse -Force")
        print("5. Tente novamente")
        print("=" * 60)
        sys.exit(1)

    # Verificar build (usando build_utils se disponível)
    if HAS_BUILD_UTILS:
        if not verify_build_result():
            sys.exit(1)

    # Criar pacote portável (opcional)
    try:
        create_portable_package()
    except Exception as e:
        print(f"⚠️  Erro ao criar pacote portável: {e}")
        print("   (Isso não afeta o executável principal)")

    # Instruções finais
    print_next_steps()


if __name__ == '__main__':
    main()
