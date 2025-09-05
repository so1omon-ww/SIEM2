#!/usr/bin/env python3
"""
Главный скрипт для сборки всех офлайн репозиториев
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Сборка всех репозиториев"""
    print("Building all offline repositories...")
    
    # Создание директории для скриптов
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    try:
        # Сборка Windows репозитория
        print("\n=== Building Windows Repository ===")
        subprocess.run([sys.executable, "build_windows_repo.py"], 
                      cwd=scripts_dir, check=True)
        
        # Сборка Astra Linux репозитория
        print("\n=== Building Astra Linux Repository ===")
        subprocess.run([sys.executable, "build_astra_docker.py"], 
                      cwd=scripts_dir, check=True)
        
        print("\n=== All repositories built successfully! ===")
        print("Archives created:")
        print("- offline_repos/windows/siem-windows-agent-v2.0.0.zip")
        print("- offline_repos/astra/siem-astra-agent-v2.0.0.zip")
        
    except subprocess.CalledProcessError as e:
        print(f"Error building repositories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
