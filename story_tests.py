#!/usr/bin/env python3
"""
Story Generation Test Suite
============================

Diff-based regression testing for story generation using story IDs.

Pin a good story output:
    python story_tests.py --pin data00:12345 "Tests Play kernel improvements"

Run all tests:
    python story_tests.py --run

List all tests:
    python story_tests.py --list
"""

import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import json
import difflib

TESTS_DIR = Path(__file__).parent / "story_tests"
TESTS_INDEX = TESTS_DIR / "index.json"


class TestSuite:
    """Manage story generation tests."""
    
    def __init__(self):
        self.tests_dir = TESTS_DIR
        self.tests_dir.mkdir(exist_ok=True)
        self.index = self._load_index()
    
    def _load_index(self):
        """Load test index."""
        if TESTS_INDEX.exists():
            with open(TESTS_INDEX) as f:
                return json.load(f)
        return {}
    
    def _save_index(self):
        """Save test index."""
        with open(TESTS_INDEX, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _parse_story_id(self, story_id: str):
        """Parse story_id like 'data00:12345' into (dataset, line_num)."""
        if ':' not in story_id:
            raise ValueError(f"Story ID must be in format 'dataXX:line_num', got: {story_id}")
        
        dataset, line_str = story_id.split(':', 1)
        try:
            line_num = int(line_str)
        except ValueError:
            raise ValueError(f"Line number must be integer, got: {line_str}")
        
        return dataset, line_num
    
    def _get_story(self, story_id: str):
        """Get a story by ID (dataset:line_num)."""
        dataset, line_num = self._parse_story_id(story_id)
        
        # Read the specific line from the dataset
        dataset_file = Path(__file__).parent / "TinyStories_kernels" / f"{dataset}.kernels.jsonl"
        
        if not dataset_file.exists():
            raise FileNotFoundError(f"Dataset file not found: {dataset_file}")
        
        with open(dataset_file) as f:
            for i, line in enumerate(f):
                if i == line_num:
                    return json.loads(line)
        
        raise ValueError(f"Line {line_num} not found in {dataset}")
    
    def pin(self, story_id: str, description: str = ""):
        """Pin a story generation as a test case."""
        # Validate story_id
        try:
            dataset, line_num = self._parse_story_id(story_id)
            story_data = self._get_story(story_id)
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
        
        test_name = story_id.replace(':', '_')
        test_file = self.tests_dir / f"{test_name}.txt"
        
        print(f"Generating story for {story_id}...")
        print(f"  Dataset: {dataset}")
        print(f"  Line: {line_num}")
        print(f"  Summary: {story_data.get('summary', 'N/A')[:60]}...")
        
        # Generate the story using sample.py with the story ID
        cmd = ["python", "sample.py", "--story-id", story_id]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            print(f"✗ Error running sample.py: {result.stderr}")
            return False
        
        # Save output to file
        with open(test_file, 'w') as f:
            f.write(result.stdout)
        
        # Update index
        self.index[test_name] = {
            'story_id': story_id,
            'dataset': dataset,
            'line_num': line_num,
            'description': description,
            'pinned_date': datetime.now().isoformat(),
            'file': str(test_file.name),
            'summary': story_data.get('summary', '')[:100],
        }
        self._save_index()
        
        print(f"✓ Pinned test: {test_name}")
        print(f"  File: {test_file}")
        print(f"  Commit this file to version control!")
        return True
    
    def run_test(self, test_name: str):
        """Run a single test."""
        if test_name not in self.index:
            print(f"✗ Test not found: {test_name}")
            return None
        
        test_info = self.index[test_name]
        story_id = test_info['story_id']
        pinned_file = self.tests_dir / test_info['file']
        
        if not pinned_file.exists():
            print(f"✗ Pinned file not found: {pinned_file}")
            return None
        
        # Run sample.py with story ID
        cmd = ["python", "sample.py", "--story-id", story_id]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode != 0:
            return {
                'test': test_name,
                'status': 'ERROR',
                'error': result.stderr,
            }
        
        # Compare with pinned output
        with open(pinned_file) as f:
            expected = f.read()
        
        actual = result.stdout
        
        if expected == actual:
            return {
                'test': test_name,
                'status': 'PASS',
                'story_id': story_id,
            }
        else:
            # Generate diff
            diff = list(difflib.unified_diff(
                expected.splitlines(keepends=True),
                actual.splitlines(keepends=True),
                fromfile=f'expected ({test_name})',
                tofile='actual',
                lineterm=''
            ))
            
            return {
                'test': test_name,
                'status': 'FAIL',
                'story_id': story_id,
                'diff': ''.join(diff),
            }
    
    def run_all(self):
        """Run all tests."""
        if not self.index:
            print("No tests in suite. Use --pin to add tests.")
            return []
        
        results = []
        for test_name in sorted(self.index.keys()):
            print(f"Running {test_name}...", end=' ', flush=True)
            result = self.run_test(test_name)
            if result:
                print(result['status'])
                results.append(result)
        
        return results
    
    def list_tests(self):
        """List all tests."""
        if not self.index:
            print("\nNo tests in suite. Use --pin to add tests.\n")
            return
        
        print(f"\n{'='*70}")
        print(f"STORY TEST SUITE - {len(self.index)} tests")
        print(f"{'='*70}\n")
        
        for test_name, info in sorted(self.index.items()):
            print(f"📌 {test_name}")
            print(f"   Story ID: {info['story_id']}")
            if info.get('summary'):
                print(f"   Summary: {info['summary']}")
            if info.get('description'):
                print(f"   Description: {info['description']}")
            print(f"   Pinned: {info['pinned_date'][:10]}")
            print(f"   File: {info['file']}")
            print()
    
    def show(self, test_name: str):
        """Show the pinned output for a test."""
        if test_name not in self.index:
            print(f"✗ Test not found: {test_name}")
            return
        
        test_info = self.index[test_name]
        pinned_file = self.tests_dir / test_info['file']
        
        if not pinned_file.exists():
            print(f"✗ Pinned file not found: {pinned_file}")
            return
        
        print(f"\n{'='*70}")
        print(f"TEST: {test_name}")
        print(f"Story ID: {test_info['story_id']}")
        print(f"{'='*70}\n")
        
        with open(pinned_file) as f:
            print(f.read())
    
    def remove(self, test_name: str):
        """Remove a test."""
        if test_name not in self.index:
            print(f"✗ Test not found: {test_name}")
            return
        
        test_info = self.index[test_name]
        pinned_file = self.tests_dir / test_info['file']
        
        if pinned_file.exists():
            pinned_file.unlink()
        
        del self.index[test_name]
        self._save_index()
        
        print(f"✓ Removed test: {test_name}")


def main():
    parser = argparse.ArgumentParser(
        description='Story Generation Test Suite - Diff-based regression testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pin a story as a test (find story ID with sample.py first)
  python story_tests.py --pin data00:12345 --description "Play kernel improvements"
  
  # Run all tests
  python story_tests.py --run
  
  # List all tests
  python story_tests.py --list
  
  # Show a specific test
  python story_tests.py --show data00_12345
  
  # Remove a test
  python story_tests.py --remove data00_12345
  
Story ID format: dataXX:line_num (e.g., data00:12345, data01:999)
        """
    )
    
    parser.add_argument('--pin', metavar='STORY_ID',
                       help='Pin a story as a test (format: dataXX:line_num)')
    parser.add_argument('--description', type=str, default='',
                       help='Description of what this test validates')
    parser.add_argument('--run', action='store_true',
                       help='Run all tests')
    parser.add_argument('--list', action='store_true',
                       help='List all tests')
    parser.add_argument('--show', metavar='TEST_NAME',
                       help='Show pinned output for a test')
    parser.add_argument('--remove', metavar='TEST_NAME',
                       help='Remove a test')
    
    args = parser.parse_args()
    
    suite = TestSuite()
    
    if args.pin:
        suite.pin(args.pin, args.description)
    
    elif args.run:
        results = suite.run_all()
        
        if not results:
            return
        
        # Print summary
        print(f"\n{'='*70}")
        print("TEST RESULTS")
        print(f"{'='*70}\n")
        
        passed = sum(1 for r in results if r['status'] == 'PASS')
        failed = sum(1 for r in results if r['status'] == 'FAIL')
        errors = sum(1 for r in results if r['status'] == 'ERROR')
        
        print(f"✓ Passed: {passed}")
        print(f"✗ Failed: {failed}")
        print(f"⚠ Errors: {errors}")
        
        # Show diffs for failures
        if failed > 0:
            print(f"\n{'='*70}")
            print("DIFFS:")
            print(f"{'='*70}\n")
            
            for r in results:
                if r['status'] == 'FAIL':
                    print(f"\n✗ {r['test']} (story_id={r['story_id']})")
                    print(r['diff'])
        
        # Show errors
        if errors > 0:
            print(f"\n{'='*70}")
            print("ERRORS:")
            print(f"{'='*70}\n")
            
            for r in results:
                if r['status'] == 'ERROR':
                    print(f"\n⚠ {r['test']}")
                    print(r['error'])
        
        # Exit with error code if any tests failed
        sys.exit(0 if (failed == 0 and errors == 0) else 1)
    
    elif args.list:
        suite.list_tests()
    
    elif args.show:
        suite.show(args.show)
    
    elif args.remove:
        suite.remove(args.remove)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
