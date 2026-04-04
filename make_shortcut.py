"""Creates a desktop shortcut for DarkStare AI on Windows."""
import os, sys, pathlib

def make():
    try:
        bat_src  = sys.argv[1] if len(sys.argv) > 1 else ""
        desktop  = pathlib.Path.home() / "Desktop"
        link     = desktop / "DarkStare AI.bat"
        if link.exists():
            return
        src_dir  = pathlib.Path(bat_src).parent if bat_src else pathlib.Path(__file__).parent
        srv      = src_dir / "server.py"
        link.write_text(
            f'@echo off\n'
            f'cd /d "{src_dir}"\n'
            f'start "DarkStare Server" /MIN python "{srv}"\n'
            f'timeout /t 4 /nobreak >nul\n'
            f'start "" "http://localhost:8000"\n'
            f'echo DarkStare AI is running at http://localhost:8000\n'
            f'pause\n',
            encoding="utf-8"
        )
        print(f"[OK] Desktop shortcut created: {link}")
    except Exception as e:
        print(f"[Note] Could not create shortcut: {e}")

if __name__ == "__main__":
    make()
