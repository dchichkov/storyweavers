import difflib
from dataclasses import dataclass
from typing import List, Tuple
import ast
import os
from openai import OpenAI
import ast
from dataclasses import dataclass, field
from typing import Callable, Dict, Any

# Decorator and registry
class KernelRegistry:
    def __init__(self):
        self.kernels: Dict[str, Callable] = {}
        self.metadata: Dict[str, Dict] = {}
    
    def register(self, summary="", verb="", past=""):
        def decorator(func):
            name = func.__name__
            self.kernels[name] = func
            self.metadata[name] = {
                'summary': summary,
                'verb': verb,
                'past': past or verb + 'ed',
                'doc': func.__doc__
            }
            return func
        return decorator

@dataclass
class KernelConcept:
    """Represents a kernel as a concept/pattern before execution."""
    name: str
    args: tuple = ()
    
    def execute(self, context=None):
        """Execute this concept with given context."""
        if self.name in KERNELS.kernels:
            return KERNELS.kernels[self.name](*self.args)
        return self.name.lower()
    
    def __str__(self):
        return self.name.lower()

KERNELS = KernelRegistry()


@dataclass
class ExecutionResult:
    kernel_code: str
    story_text: str
    error: str = None
    
    @property
    def success(self):
        return self.error is None

class TestDrivenKernelSynthesis:
    def __init__(self, registry, kernel_dataset):
        self.registry = registry
        self.dataset = kernel_dataset
        self.kernel_versions = {}  # Track version history
        
    def find_stories_using(self, kernel_name: str, limit=20) -> List[dict]:
        """Find stories that use a specific kernel."""
        import re
        
        matches = []
        for story in self.dataset:
            kernel_str = story.get('kernel', '')
            # Look for kernel name as function call or reference
            if re.search(rf'\b{kernel_name}\b', kernel_str):
                matches.append(story)
                if len(matches) >= limit:
                    break
        
        return matches
    
    def execute_stories(self, stories: List[dict]) -> List[ExecutionResult]:
        """Execute multiple stories and capture results."""
        results = []
        
        for story in stories:
            try:
                executor = KernelExecutor(self.registry)
                text = executor.execute(story['kernel'])
                results.append(ExecutionResult(
                    kernel_code=story['kernel'],
                    story_text=text
                ))
            except Exception as e:
                results.append(ExecutionResult(
                    kernel_code=story['kernel'],
                    story_text="",
                    error=str(e)
                ))
        
        return results
    
    def synthesize_or_update(self, kernel_name: str):
        """Synthesize new kernel or update existing one."""
        
        # 1. Find usage examples
        examples = self.find_stories_using(kernel_name, limit=20)
        
        if not examples:
            print(f"No examples found for {kernel_name}")
            return False
        
        print(f"\n{'='*60}")
        print(f"SYNTHESIZING: {kernel_name}")
        print(f"Found {len(examples)} usage examples")
        
        # 2. Execute BEFORE (baseline)
        print("\n--- Executing BEFORE ---")
        before_results = self.execute_stories(examples)
        
        before_success = sum(1 for r in before_results if r.success)
        print(f"Success: {before_success}/{len(before_results)}")
        
        # 3. Synthesize new implementation
        print("\n--- Synthesizing new implementation ---")
        new_code = self._llm_synthesize(kernel_name, examples, before_results)
        
        if not new_code:
            print("Synthesis failed")
            return False
        
        print(f"Generated code:\n{new_code[:200]}...")
        
        # 4. Apply new implementation
        old_impl = self.registry.kernels.get(kernel_name)
        try:
            exec(new_code, globals())
        except Exception as e:
            print(f"✗ Code execution failed: {e}")
            return False
        
        # 5. Execute AFTER
        print("\n--- Executing AFTER ---")
        after_results = self.execute_stories(examples)
        
        after_success = sum(1 for r in after_results if r.success)
        print(f"Success: {after_success}/{len(after_results)}")
        
        # 6. Generate diffs
        diffs = self._generate_diffs(before_results, after_results)
        
        # 7. LLM evaluation
        print("\n--- Evaluating changes ---")
        verdict = self._llm_evaluate(kernel_name, diffs, before_success, after_success)
        
        print(f"\nVerdict: {verdict['decision']} ({verdict['score']}/10)")
        print(f"Reasoning: {verdict['reasoning']}")
        
        # 8. Accept or rollback
        if verdict['decision'] == 'ACCEPT':
            print("✓ Accepted changes")
            self.kernel_versions[kernel_name] = {
                'before': old_impl,
                'after': self.registry.kernels[kernel_name],
                'verdict': verdict
            }
            return True
        else:
            print("✗ Rejected changes, rolling back")
            if old_impl:
                self.registry.kernels[kernel_name] = old_impl
            return False
    
    def _generate_diffs(self, before: List[ExecutionResult], 
                       after: List[ExecutionResult]) -> List[dict]:
        """Generate story-by-story diffs."""
        diffs = []
        
        for b, a in zip(before, after):
            diff_lines = list(difflib.unified_diff(
                b.story_text.split('\n'),
                a.story_text.split('\n'),
                lineterm=''
            ))
            
            diffs.append({
                'kernel': b.kernel_code[:100],
                'before_text': b.story_text,
                'after_text': a.story_text,
                'before_error': b.error,
                'after_error': a.error,
                'diff': '\n'.join(diff_lines) if diff_lines else 'No change'
            })
        
        return diffs
    
    def _llm_synthesize(self, kernel_name: str, examples: List[dict], 
                       baseline_results: List[ExecutionResult]) -> str:
        """Use LLM to synthesize kernel implementation."""
        
        # Format examples
        example_text = "\n\n".join([
            f"Example {i+1}:\n{ex['kernel'][:200]}"
            for i, ex in enumerate(examples[:10])
        ])
        
        # Show current failures
        failures = [r for r in baseline_results if not r.success]
        failure_text = "\n".join([
            f"- {f.error[:100]}"
            for f in failures[:5]
        ])
        
        samples = """@Stories
def Accident(story, character, process, consequence):
    "Character has an accident."
    character.Fear += 10
    return f"{character.name} {process}. Then, {consequence}."


@Stories
def Laugh(story, character, *args, **kvargs):
    "they laugh."
    character.Joy += 1

    reason = f"because {kvargs['reason']}." if 'reason' in kvargs else ""
    others = " and " + " and ".join(args) if args else ""
    for other in args:
        other.Joy += 1
        other.Love += character / 100       # increases other.Love to the character, small amount
        character.Love += other / 100       # increases character.Love to the other

    return f"{character.name}{others} laughed{reason}"
"""


        prompt = f"""
Synthesize a Python function for the kernel `{kernel_name}`.

USAGE EXAMPLES:
{example_text}

CURRENT FAILURES:
{failure_text}

REQUIREMENTS:
1. Handle multiple argument patterns (0, 1, 2+ args)
2. Accept Story objects or strings
3. Mutate story state when appropriate (Joy, Fear, Love, etc)
4. Return natural language text
5. Be polymorphic - work as action, concept, or composition

SAMPLE KERNELS:
{samples}        


Return ONLY the kernel Python code, no explanations, import statements, or comments.
"""
        
        # Call LLM (placeholder - use your LLM client)
        print(f"\nLLM Prompt:\n{prompt}...\n")
        response = call_llm(prompt)
        return response
    
    def _llm_evaluate(self, kernel_name: str, diffs: List[dict], 
                     before_success: int, after_success: int) -> dict:
        """Use LLM to evaluate if changes are improvements."""
        
        # Format diffs for LLM
        diff_text = "\n\n".join([
            f"Story {i+1}:\n"
            f"BEFORE: {d['before_text'][:150] if d['before_text'] else d['before_error']}\n"
            f"AFTER:  {d['after_text'][:150] if d['after_text'] else d['after_error']}\n"
            f"DIFF: {d['diff'][:200]}"
            for i, d in enumerate(diffs[:10])
        ])
        
        prompt = f"""
Evaluate if the kernel `{kernel_name}` changes are an improvement.

METRICS:
- Success rate: {before_success}/{len(diffs)} → {after_success}/{len(diffs)}

STORY CHANGES:
{diff_text}

EVALUATION CRITERIA:
1. More stories execute successfully (+)
2. Generated text is more natural (+)
3. Text is grammatically correct (+)
4. Character state mutations make sense (+)
5. Stories that worked before still work (no regressions) (+)
6. Handles edge cases better (+)

RESPOND IN JSON:
{{
    "decision": "ACCEPT" or "REJECT",
    "score": 1-10,
    "reasoning": "Brief explanation",
    "regressions": ["list", "of", "specific", "regressions"],
    "improvements": ["list", "of", "improvements"]
}}
"""
        
        # Call LLM
        response = call_llm(prompt)
        
        # Parse JSON (with error handling)
        try:
            import json
            return json.loads(response)
        except:
            # Fallback heuristic
            return {
                'decision': 'ACCEPT' if after_success >= before_success else 'REJECT',
                'score': 7 if after_success > before_success else 4,
                'reasoning': 'Heuristic: success rate comparison'
            }


def call_llm(prompt: str) -> str:
    """Placeholder - replace with actual LLM call."""
    # Use your AsyncOpenAI client here
    localhost_base_url = os.environ.get("LOCALHOST_BASE_URL", "http://localhost:8001/v1")
    localhost_api_key = os.environ.get("LOCALHOST_API_KEY", "dummy-key")
    
    client = OpenAI(api_key=localhost_api_key, base_url=localhost_base_url)
    
    response = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    
    return response.choices[0].message.content

def load_jsonl(file_path: str) -> List[dict]:
    import json
    records = []
    with open(file_path, 'r') as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except:
                continue
    return records


# Usage
if __name__ == "__main__":
    # Load your dataset
    stories = load_jsonl("kernels_output.jsonl")
    
    synthesis = TestDrivenKernelSynthesis(KERNELS, stories)
    
    # Synthesize specific kernel
    synthesis.synthesize_or_update("Play")
    
    # Or batch process missing kernels
    missing_kernels = find_undefined_kernels(stories)
    for kernel in missing_kernels[:10]:
        synthesis.synthesize_or_update(kernel)