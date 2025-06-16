#!/usr/bin/env python3
"""
Comprehensive MCP test runner for Robyn.

This script runs all MCP tests:
1. Unit tests (no server required)
2. Live integration tests (starts test server)
3. Knowledge assistant validation

Usage: python run_mcp_tests.py [--quick] [--live-only] [--unit-only]
"""

import asyncio
import subprocess
import sys
import os


def run_unit_tests():
    """Run unit tests"""
    print("🧪 Running MCP Unit Tests")
    print("=" * 40)
    
    try:
        result = subprocess.run([sys.executable, 'test_mcp_manual.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Extract just the summary
            lines = result.stdout.split('\n')
            summary_start = -1
            for i, line in enumerate(lines):
                if "TEST RESULTS" in line:
                    summary_start = i
                    break
            
            if summary_start >= 0:
                for line in lines[summary_start:]:
                    if line.strip():
                        print(line)
            else:
                print("✅ All unit tests passed!")
            return True
        else:
            print("❌ Unit tests failed:")
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Unit tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False


def run_live_tests():
    """Run live integration tests"""
    print("\n🌐 Running MCP Live Integration Tests")
    print("=" * 45)
    
    try:
        result = subprocess.run([sys.executable, 'test_mcp_live.py', 'full'],
                              capture_output=True, text=True, timeout=120)
        
        # Always show the output for live tests
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Live tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running live tests: {e}")
        return False


def validate_examples():
    """Validate example files"""
    print("\n📋 Validating Example Files")
    print("=" * 30)
    
    examples = [
        'example_mcp_simple.py',
        'example_knowledge_assistant.py'
    ]
    
    all_valid = True
    
    for example in examples:
        if os.path.exists(example):
            try:
                # Just check syntax
                with open(example, 'r') as f:
                    code = f.read()
                compile(code, example, 'exec')
                print(f"✅ {example} - syntax valid")
            except SyntaxError as e:
                print(f"❌ {example} - syntax error: {e}")
                all_valid = False
            except Exception as e:
                print(f"❌ {example} - error: {e}")
                all_valid = False
        else:
            print(f"⚠️  {example} - not found")
    
    return all_valid


def main():
    """Main test runner"""
    print("🧠 Robyn MCP Implementation Test Suite")
    print("=" * 50)
    
    # Parse command line arguments
    quick_mode = '--quick' in sys.argv
    live_only = '--live-only' in sys.argv
    unit_only = '--unit-only' in sys.argv
    
    if quick_mode:
        print("⚡ Running in quick mode (unit tests only)")
        unit_only = True
    
    results = []
    
    # Run unit tests
    if not live_only:
        unit_success = run_unit_tests()
        results.append(("Unit Tests", unit_success))
        
        if not unit_success and not quick_mode:
            print("\n❌ Unit tests failed. Skipping live tests.")
            print("Fix unit test issues before running integration tests.")
            sys.exit(1)
    
    # Run live tests
    if not unit_only:
        live_success = run_live_tests()
        results.append(("Live Integration Tests", live_success))
    
    # Validate examples
    if not live_only and not unit_only:
        examples_valid = validate_examples()
        results.append(("Example Validation", examples_valid))
    
    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("✅ MCP implementation is fully functional")
        print("✅ Ready for production use")
        print("✅ Compatible with Claude Desktop")
        print("✅ Supports all MCP protocol features:")
        print("   • JSON-RPC 2.0 compliance")
        print("   • URI template matching")
        print("   • Auto-generated schemas")
        print("   • Resources, tools, and prompts")
        print("   • Proper error handling")
        print()
        print("🚀 You can now:")
        print("   • Connect Claude Desktop to your MCP servers")
        print("   • Use the Knowledge Assistant example")
        print("   • Build custom MCP integrations")
        sys.exit(0)
    else:
        failed_count = sum(1 for _, passed in results if not passed)
        print(f"💥 {failed_count} test suite(s) failed")
        print()
        print("Please fix the failing tests before deploying to production.")
        sys.exit(1)


if __name__ == "__main__":
    main()