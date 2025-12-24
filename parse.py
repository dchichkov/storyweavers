import json
import ast
from pathlib import Path
from collections import Counter


def extract_kernels(tree):
    """Extract all kernel names (capitalized identifiers) from kernel code."""
    kernels = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id[0].isupper():
            kernels.add(node.id)
    
    return sorted(kernels)


def extract_multi_param_kernels(tree):  
    """Extract kernels that are called with 2+ parameters."""
   
    multi_param = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check if it's a capitalized name (kernel)
            if isinstance(node.func, ast.Name) and node.func.id[0].isupper():
                # Count args + kwargs
                total_params = len(node.args) + len(node.keywords)
                if total_params >= 2:
                    multi_param.add(node.func.id)
    
    return sorted(multi_param)




def analyze_kernels(jsonl_file="kernels.jsonl"):
    total = parsed = failed = 0
    parse_errors = Counter()
    failed_examples = []
    all_kernels = Counter()

    
    with open(jsonl_file, 'r') as f:
        for line in f:
            total += 1
            record = json.loads(line)
            kernel = record.get("kernel", "")
            if not kernel:
                failed += 1
                parse_errors["empty_kernel"] += 1
                if len(failed_examples) < 5:
                    failed_examples.append({
                        "kernel": "<empty>",
                        "error": "empty_kernel"
                    })
                continue
            #print(f"\n--- Kernel {total} ---\n{kernel}\n")
            
            try:
                tree = ast.parse(kernel)
                parsed += 1

                #kernels = extract_kernels(tree)
                kernels = extract_multi_param_kernels(tree)
                all_kernels.update(kernels)

            except SyntaxError as e:
                failed += 1
                error_type = e.msg
                parse_errors[error_type] += 1
                if len(failed_examples) < 5:  # Keep first 5 failures
                    failed_examples.append({
                        "kernel": kernel[:100],
                        "error": error_type
                    })


    
    print(f"\n{'='*60}")
    print(f"KERNEL PARSING STATS")
    print(f"{'='*60}")
    print(f"Total records:     {total}")
    print(f"✓ Parsed:          {parsed} ({100*parsed/total:.1f}%)")
    print(f"✗ Failed:          {failed} ({100*failed/total:.1f}%)")
    
    if parse_errors:
        print(f"\n{'='*60}")
        print("ERROR BREAKDOWN:")
        for error, count in parse_errors.most_common():
            print(f"  {error}: {count}")
    
    if failed_examples:
        print(f"\n{'='*60}")
        print("EXAMPLE FAILURES:")
        for i, ex in enumerate(failed_examples, 1):
            print(f"\n{i}. {ex['error']}")
            print(f"   {ex['kernel']}")

    if all_kernels:
        print(f"\n{'='*60}")
        print("MOST COMMON KERNELS:")
        for i, (kernel, count) in enumerate(all_kernels.most_common(2000)):
            # count uppercase letters
            if count < 5:
                break
            #uppercase_count = sum(1 for c in kernel if c.isupper())
            #if uppercase_count > 1:
            #    continue

            print(f"#{i}  {kernel}: {count}")

if __name__ == "__main__":
    analyze_kernels("data00.kernels.jsonl")