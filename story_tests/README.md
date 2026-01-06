# Story Generation Test Suite

Regression testing for story generation using diff-based comparison with story IDs.

## Story IDs

Stories are identified by `dataset:line_number` (e.g., `data00:100`, `data01:523`).

- **dataset**: Which data file (data00, data01, etc.)
- **line_number**: 0-based line number in the `.kernels.jsonl` file

This ID format matches the existing pattern used in `cluster.py` and is stable - it always refers to the same story.

## Usage

### Pin a Story as a Test

First, find a story you want to test:

```bash
# Sample stories and note the STORY ID that's printed
python sample.py -k SomeKernel -n 5

# Or generate a specific story if you know its ID
python sample.py --story-id data00:100
```

Then pin it:

```bash
python story_tests.py --pin data00:100 --description "What this tests"
```

This will:
- Run `python sample.py --story-id data00:100`
- Save the complete output to `story_tests/data00_100.txt`
- Add the test to the index

**Important:** Commit the generated `.txt` file to version control!

### Run All Tests

```bash
python story_tests.py --run
```

Runs all pinned tests and compares current output against pinned output. Shows diffs for any failures.

### List Tests

```bash
python story_tests.py --list
```

### Show a Test

```bash
python story_tests.py --show data00_100
```

### Remove a Test

```bash
python story_tests.py --remove data00_100
```

## Workflow

### When Improving a Kernel

1. **Find a problematic story:**
   ```bash
   python sample.py -k SomeKernel -n 10
   # Look for issues, note the STORY ID printed
   ```

2. **Improve the kernel** in `gen5.py` or `gen5kXX.py`

3. **Verify the improvement:**
   ```bash
   python sample.py --story-id data00:12345
   ```

4. **Pin it if it's good:**
   ```bash
   python story_tests.py --pin data00:12345 --description "Fixed XYZ issue"
   ```

5. **Commit the test:**
   ```bash
   git add story_tests/data00_12345.txt story_tests/index.json
   git commit -m "Add test for SomeKernel improvements"
   ```

### Before Making Changes

Run tests to establish baseline:
```bash
python story_tests.py --run
```

### After Making Changes

Run tests again to catch regressions:
```bash
python story_tests.py --run
```

If tests fail, you'll see a unified diff showing exactly what changed.

## Why Story IDs Instead of Seeds?

**Seeds are fragile:**
- Depend on random sampling logic
- Break if dataset order changes  
- Break if sampling algorithm changes

**Story IDs are stable:**
- `data00:100` always refers to line 100 in data00.kernels.jsonl
- Doesn't depend on any runtime logic
- Matches existing ID format used in cluster.py
- Easy to find and reference specific stories

## Test Index

The `index.json` file tracks all tests:
- `story_id`: Which story (format: data00:123)
- `dataset`: Dataset name
- `line_num`: Line number
- `description`: What this test validates
- `pinned_date`: When the test was created
- `file`: Name of the pinned output file
- `summary`: Story summary for reference

## Integration with CI/CD

Add to your CI pipeline:

```yaml
- name: Run story generation tests
  run: python story_tests.py --run
```

Tests exit with code 0 on success, non-zero on failure.

## Notes

- Tests are deterministic (fixed story ID)
- Full output comparison (not just phrases)
- Easy to review what's "good" (just read the `.txt` files)
- Diffs show exactly what changed
- Generation is fast and free, so test liberally!
- Story IDs are stable and won't break when code changes
