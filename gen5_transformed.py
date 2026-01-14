from gen5registry import REGISTRY, KernelExecutor, StoryContext, StoryFragment, Character
from transform5 import transform_ast
import ast

class EnhancedKernelExecutor(KernelExecutor):
    """
    An enhanced executor that transforms the story AST before execution
    using the registry-based transforms in transform5.py.
    """
    def execute(self, kernel_str: str) -> str:
        # 1. Transform the kernel string (AST -> AST)
        transformed_kernel = transform_ast(kernel_str)
        
        # 2. Execute as usual using the transformed string
        return super().execute(transformed_kernel)

# Redefine a few kernels to show off the transformation results
@REGISTRY.kernel("Brave")
def kernel_brave_enhanced(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Enhanced Brave kernel that uses injected hints."""
    chars = [a for a in args if isinstance(a, Character)]
    if not chars:
        return StoryFragment("Someone was brave.")
    
    char = chars[0]
    
    # Extract injected hints
    use_pronoun = kwargs.get('_use_pronoun', False)
    transition = kwargs.get('_transition', '')
    after = kwargs.get('_after', '')
    
    # Update state
    char.Fear -= 20
    char.Joy += 10
    
    # Choose subject
    subject = char.he if use_pronoun else char.name
    
    # Build core text based on context
    if after == 'fear':
        text = f"Despite {char.his} fear, {subject} was brave."
    elif after == 'danger':
        text = f"Facing the danger, {subject} stood brave."
    else:
        text = f"{subject} was very brave."
        
    # Prepend transition if present
    if transition:
        # Lowercase first letter of text if transition ends with comma and space
        if transition.endswith(', ') and text[0].isupper():
            text = transition + text[0].lower() + text[1:]
        else:
            text = transition + text
            
    return StoryFragment(text, kernel_name="Brave")

@REGISTRY.kernel("Happy")
def kernel_happy_enhanced(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Enhanced Happy kernel that uses injected hints."""
    chars = [a for a in args if isinstance(a, Character)]
    if not chars:
        return StoryFragment("Everyone was happy.")
    
    char = chars[0]
    
    # Extract injected hints
    use_pronoun = kwargs.get('_use_pronoun', False)
    transition = kwargs.get('_transition', '')
    after = kwargs.get('_after', '')
    
    # Update state
    char.Joy += 15
    
    # Choose subject
    subject = char.he if use_pronoun else char.name
    
    # Build core text based on context
    if after == 'sadness' or after == 'sad':
        text = f"{subject} finally felt happy again."
    elif after == 'fear':
        text = f"{subject} felt relieved and happy."
    else:
        text = f"{subject} was very happy."
        
    # Prepend transition if present
    if transition:
        if transition.endswith(', ') and text[0].isupper():
            text = transition + text[0].lower() + text[1:]
        else:
            text = transition + text
            
    return StoryFragment(text, kernel_name="Happy")

if __name__ == "__main__":
    test_kernel = """
Lily(Character, girl, Curious)
Fear(Lily, dog)
Brave(Lily)
Happy(Lily)
"""
    print("=" * 70)
    print("STORYWEAVERS 2.0 - AST TRANSFORM DEMO")
    print("=" * 70)
    print("\nKERNEL STRING:")
    print(test_kernel.strip())
    
    # Standard execution
    print("\n--- STANDARD EXECUTION ---")
    standard_executor = KernelExecutor(REGISTRY)
    print(standard_executor.execute(test_kernel))
    
    # Enhanced execution
    print("\n--- ENHANCED EXECUTION (with AST Transforms) ---")
    enhanced_executor = EnhancedKernelExecutor(REGISTRY)
    print(enhanced_executor.execute(test_kernel))
    print("\n" + "=" * 70)
