from transform5 import transform_ast

def test_registry_transforms():
    print("Testing Registry-based AST Transformations (transform5.py)...\n")
    
    test_cases = [
        {
            "name": "Brave after Fear",
            "input": "Fear(Lily)\nBrave(Lily)",
            "expected": ["_after='fear'", "_use_pronoun=True", "_transition='Then, '"]
        },
        {
            "name": "Happy after Sadness",
            "input": "Sadness(Lily)\nHappy(Lily)",
            "expected": ["_after='sadness'", "_use_pronoun=True", "_transition='In the end, '"]
        }
    ]
    
    for case in test_cases:
        print(f"Scenario: {case['name']}")
        output = transform_ast(case['input'])
        print(f"Output:\n{output.strip()}")
        
        success = True
        for e in case['expected']:
            if e not in output:
                print(f"❌ FAILED: Missing '{e}'")
                success = False
        
        if success:
            print("✅ PASSED")
        print("-" * 40)

if __name__ == "__main__":
    test_registry_transforms()
