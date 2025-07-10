#!/usr/bin/env python3
"""
Render Deployment Helper Script
Switches between different dependency configurations based on deployment success
"""

import os
import shutil
import sys
from pathlib import Path

def backup_file(file_path: str) -> str:
    """Create a backup of a file"""
    backup_path = f"{file_path}.backup"
    if os.path.exists(file_path):
        shutil.copy2(file_path, backup_path)
        print(f"✅ Backed up {file_path} to {backup_path}")
    return backup_path

def restore_file(file_path: str) -> bool:
    """Restore a file from backup"""
    backup_path = f"{file_path}.backup"
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, file_path)
        print(f"✅ Restored {file_path} from backup")
        return True
    return False

def switch_to_no_rust_mode():
    """Switch to no-rust dependencies mode"""
    print("🔄 Switching to no-rust deployment mode...")
    
    backend_dir = Path("backend")
    
    # Backup original files
    backup_file(str(backend_dir / "requirements.txt"))
    backup_file(str(backend_dir / "app" / "core" / "auth.py"))
    
    # Switch to no-rust requirements
    no_rust_req = backend_dir / "requirements-no-rust.txt"
    main_req = backend_dir / "requirements.txt"
    
    if no_rust_req.exists():
        shutil.copy2(str(no_rust_req), str(main_req))
        print("✅ Switched to no-rust requirements.txt")
    
    # Switch to Argon2 auth
    argon2_auth = backend_dir / "app" / "core" / "auth_argon2.py"
    main_auth = backend_dir / "app" / "core" / "auth.py"
    
    if argon2_auth.exists():
        shutil.copy2(str(argon2_auth), str(main_auth))
        print("✅ Switched to Argon2 authentication")
    
    print("🚀 Ready for no-rust deployment!")
    print("📝 Commit and push these changes to trigger Render deployment")

def switch_to_binary_wheel_mode():
    """Switch to binary wheel mode (recommended)"""
    print("🔄 Switching to binary wheel deployment mode...")
    
    # This mode uses the current setup with PyJWT and specific cryptography version
    print("✅ Already configured for binary wheel mode")
    print("📋 Current configuration:")
    print("   - PyJWT instead of python-jose")
    print("   - cryptography==41.0.7 (has binary wheels)")
    print("   - bcrypt==4.1.2 (has binary wheels)")
    print("   - pip install with --only-binary=all flag")
    
    print("🚀 Ready for binary wheel deployment!")
    print("📝 Commit and push these changes to trigger Render deployment")

def restore_original_mode():
    """Restore original configuration"""
    print("🔄 Restoring original configuration...")
    
    backend_dir = Path("backend")
    
    # Restore from backups
    restored_req = restore_file(str(backend_dir / "requirements.txt"))
    restored_auth = restore_file(str(backend_dir / "app" / "core" / "auth.py"))
    
    if restored_req or restored_auth:
        print("✅ Original configuration restored")
    else:
        print("⚠️  No backups found to restore")

def main():
    if len(sys.argv) < 2:
        print("🚀 Render Deployment Helper")
        print("=" * 40)
        print("Usage: python deploy_render.py [mode]")
        print()
        print("Available modes:")
        print("  binary-wheel  - Use binary wheels (recommended)")
        print("  no-rust      - Avoid all Rust dependencies")
        print("  restore      - Restore original configuration")
        print()
        print("Current status:")
        print("  ✅ Binary wheel mode is already configured")
        print("  📝 Just commit and push to deploy")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == "binary-wheel":
        switch_to_binary_wheel_mode()
    elif mode == "no-rust":
        switch_to_no_rust_mode()
    elif mode == "restore":
        restore_original_mode()
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: binary-wheel, no-rust, restore")
        sys.exit(1)

if __name__ == "__main__":
    main()
