#!/usr/bin/env python3
"""
Build Utilities - Helper functions for Windows build process
Handles file locking, process management, and cleanup
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path


def kill_process_by_name(process_name):
    """
    Kill all processes matching the given name (Windows).

    Args:
        process_name: Name of process to kill (e.g., 'PDF2MD.exe')

    Returns:
        bool: True if successful or no process found
    """
    if sys.platform != 'win32':
        return True

    try:
        # Use taskkill on Windows
        result = subprocess.run(
            ['taskkill', '/F', '/IM', process_name],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"   ✓ Processo {process_name} encerrado")
            return True
        elif 'not found' in result.stderr.lower() or 'não encontrado' in result.stderr.lower():
            # Process not running - that's fine
            return True
        else:
            print(f"   ⚠️  Aviso ao encerrar {process_name}: {result.stderr.strip()}")
            return True
    except Exception as e:
        print(f"   ⚠️  Erro ao encerrar processo: {e}")
        return False


def wait_for_file_release(file_path, max_attempts=5, delay=1):
    """
    Wait for a file to be released (not locked).

    Args:
        file_path: Path to file
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds

    Returns:
        bool: True if file is accessible or doesn't exist
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return True

    for attempt in range(max_attempts):
        try:
            # Try to open file exclusively
            with open(file_path, 'a'):
                pass
            return True
        except PermissionError:
            if attempt < max_attempts - 1:
                print(f"   ⏳ Aguardando liberação de {file_path.name}... ({attempt + 1}/{max_attempts})")
                time.sleep(delay)
            else:
                return False
        except Exception:
            return True

    return False


def safe_remove_tree(path, max_attempts=5):
    """
    Safely remove a directory tree with retry logic.

    Args:
        path: Path to directory
        max_attempts: Maximum number of attempts

    Returns:
        bool: True if successful
    """
    path = Path(path)

    if not path.exists():
        return True

    for attempt in range(max_attempts):
        try:
            shutil.rmtree(path)
            return True
        except PermissionError as e:
            if attempt < max_attempts - 1:
                print(f"   ⏳ Tentando remover {path}... ({attempt + 1}/{max_attempts})")
                time.sleep(1)

                # Try to change permissions
                try:
                    for root, dirs, files in os.walk(path):
                        for d in dirs:
                            os.chmod(os.path.join(root, d), 0o777)
                        for f in files:
                            os.chmod(os.path.join(root, f), 0o777)
                except Exception:
                    pass
            else:
                print(f"   ⚠️  Não foi possível remover {path}: {e}")
                return False
        except Exception as e:
            print(f"   ⚠️  Erro ao remover {path}: {e}")
            return False

    return False


def pre_build_cleanup():
    """
    Comprehensive pre-build cleanup for Windows.
    Kills processes, waits for file release, removes directories.

    Returns:
        bool: True if cleanup successful
    """
    print("\n🧹 Limpeza pré-build...")

    success = True

    # 1. Kill any running PDF2MD processes
    print("   [1/3] Encerrando processos...")
    kill_process_by_name('PDF2MD.exe')
    time.sleep(1)

    # 2. Wait for files to be released
    print("   [2/3] Aguardando liberação de arquivos...")
    dist_exe = Path('dist/PDF2MD.exe')
    if dist_exe.exists():
        if not wait_for_file_release(dist_exe, max_attempts=3):
            print("   ⚠️  Arquivo ainda bloqueado - continuando mesmo assim...")
            success = False

    # 3. Remove build directories
    print("   [3/3] Removendo diretórios de build...")

    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"      Removendo {dir_name}/")
            if not safe_remove_tree(dir_name, max_attempts=3):
                success = False

    # Remove spec files
    for spec_file in Path('.').glob('*.spec'):
        try:
            spec_file.unlink()
            print(f"      Removendo {spec_file}")
        except Exception as e:
            print(f"      ⚠️  Não foi possível remover {spec_file}: {e}")

    if success:
        print("   ✓ Limpeza concluída\n")
    else:
        print("   ⚠️  Limpeza parcial - alguns arquivos podem estar em uso\n")
        print("   💡 Dica: Feche todas as janelas do Explorer e tente novamente\n")

    return success


def verify_build_result():
    """
    Verify that build was successful and display results.

    Returns:
        bool: True if build successful
    """
    exe_name = 'PDF2MD.exe' if sys.platform == 'win32' else 'PDF2MD'
    exe_path = Path('dist') / exe_name

    if not exe_path.exists():
        print(f"\n❌ Executável não encontrado: {exe_path}")
        return False

    # Check file size
    size_mb = exe_path.stat().st_size / (1024 * 1024)

    print(f"\n✅ Build concluído com sucesso!")
    print(f"   📍 Local: {exe_path}")
    print(f"   📦 Tamanho: {size_mb:.2f} MB")

    # Check for portable package
    portable_zip = Path('dist/PDF2MD_Portable.zip')
    if portable_zip.exists():
        zip_size = portable_zip.stat().st_size / (1024 * 1024)
        print(f"   📦 Pacote portável: {portable_zip} ({zip_size:.2f} MB)")

    return True


if __name__ == '__main__':
    print("Build Utils - Test Mode")
    print("=" * 50)
    pre_build_cleanup()
