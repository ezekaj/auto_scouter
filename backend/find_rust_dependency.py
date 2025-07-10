#!/usr/bin/env python3
"""
Script to identify which dependency is causing Rust compilation issues
Tests each dependency individually to isolate the problematic one
"""

import subprocess
import sys
import tempfile
import os

def test_dependency(dep_line):
    """Test if a single dependency requires Rust compilation"""
    print(f"Testing: {dep_line}")
    
    # Create a temporary requirements file with just this dependency
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(dep_line + '\n')
        temp_req_file = f.name
    
    try:
        # Try to install just this dependency
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--dry-run', '--no-deps', '-r', temp_req_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"  ✅ {dep_line} - OK")
            return True
        else:
            if 'maturin' in result.stderr or 'cargo' in result.stderr.lower() or 'rust' in result.stderr.lower():
                print(f"  ❌ {dep_line} - REQUIRES RUST COMPILATION")
                print(f"     Error: {result.stderr[:200]}...")
                return False
            else:
                print(f"  ⚠️  {dep_line} - Other error: {result.stderr[:100]}...")
                return True
    except subprocess.TimeoutExpired:
        print(f"  ⏰ {dep_line} - Timeout")
        return True
    except Exception as e:
        print(f"  ❓ {dep_line} - Exception: {e}")
        return True
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_req_file)
        except:
            pass

def main():
    print("🔍 Rust Dependency Detective")
    print("=" * 50)
    
    # Read requirements.txt
    with open('requirements.txt', 'r') as f:
        lines = f.readlines()
    
    # Filter out comments and empty lines
    dependencies = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            dependencies.append(line)
    
    print(f"Found {len(dependencies)} dependencies to test\n")
    
    problematic_deps = []
    safe_deps = []
    
    for dep in dependencies:
        if test_dependency(dep):
            safe_deps.append(dep)
        else:
            problematic_deps.append(dep)
    
    print("\n" + "=" * 50)
    print("📊 RESULTS")
    print("=" * 50)
    
    print(f"\n✅ SAFE DEPENDENCIES ({len(safe_deps)}):")
    for dep in safe_deps:
        print(f"  {dep}")
    
    if problematic_deps:
        print(f"\n❌ PROBLEMATIC DEPENDENCIES ({len(problematic_deps)}):")
        for dep in problematic_deps:
            print(f"  {dep}")
        
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print("1. Replace or remove the problematic dependencies")
        print("2. Find pure Python alternatives")
        print("3. Use pre-compiled binary wheels if available")
    else:
        print(f"\n🎉 ALL DEPENDENCIES ARE SAFE!")
        print("The Rust compilation issue might be from transitive dependencies.")
        print("Try using --only-binary=all flag in pip install.")

if __name__ == "__main__":
    main()
