import ast
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any, Callable, Tuple

@dataclass
class TransformContext:
    """
    Narrative state tracked during the AST transformation pass.
    """
    seen_kernels: List[str] = field(default_factory=list)
    last_subject: Optional[str] = None
    current_phase: str = "setup"
    
    # Generic storage for custom state tracking between transforms
    data: Dict[str, Any] = field(default_factory=dict)

# Narrative Heuristics (Externalized from Context)
PHASE_MAP = {
    'Fear': 'rising', 'Danger': 'rising', 'Scared': 'rising', 'Trapped': 'rising', 
    'Sadness': 'rising', 'Sad': 'rising', 'Conflict': 'rising',
    'Brave': 'climax', 'Victory': 'climax', 'Rescue': 'climax', 'Escape': 'climax',
    'Happy': 'resolution', 'Moral': 'resolution', 'HappyEnd': 'resolution', 'Lesson': 'resolution'
}

TRANSITIONS = {
    ('setup', 'rising'): "But one day, ",
    ('rising', 'climax'): "Then, ",
    ('rising', 'resolution'): "In the end, ",
    ('climax', 'resolution'): "In the end, ",
}

class TransformRegistry:
    """Registry for kernel-specific AST transformation functions."""
    
    def __init__(self):
        self.transforms: Dict[str, Callable] = {}
        
    def transform(self, name: str):
        """Decorator to register a transform function for a specific kernel."""
        def decorator(func):
            self.transforms[name] = func
            return func
        return decorator
    
    def get(self, name: str) -> Optional[Callable]:
        return self.transforms.get(name)

# Global registry for transforms
TRANSFORMS = TransformRegistry()

# --- Transformation Utilities ---

def inject_kwarg(node: ast.Call, key: str, value: Any) -> None:
    """Inject a keyword argument into a Call node."""
    if any(kw.arg == key for kw in node.keywords):
        return
    node.keywords.append(ast.keyword(arg=key, value=ast.Constant(value=value)))

def apply_pronouns(ctx: TransformContext, node: ast.Call, char_name: Optional[str]):
    """Standard pronoun resolution logic."""
    if char_name and char_name == ctx.last_subject:
        inject_kwarg(node, '_use_pronoun', True)

def apply_phase(ctx: TransformContext, node: ast.Call, new_phase: str):
    """Handle phase transitions and inject transition strings."""
    if new_phase != ctx.current_phase:
        transition = TRANSITIONS.get((ctx.current_phase, new_phase))
        if transition:
            inject_kwarg(node, '_transition', transition)
        ctx.current_phase = new_phase

class StoryASTTransformer(ast.NodeTransformer):
    """
    Walks the Story AST and applies registered transforms per kernel.
    """
    def __init__(self, registry: TransformRegistry):
        self.registry = registry
        self.ctx = TransformContext()
        
    def visit_Call(self, node: ast.Call) -> ast.Call:
        # 1. Generic visit children first (depth-first)
        self.generic_visit(node)
        
        if not isinstance(node.func, ast.Name):
            return node
            
        kernel_name = node.func.id
        if kernel_name == "Character":
            return node
            
        # 2. Extract character name if present
        char_name = None
        if node.args and isinstance(node.args[0], ast.Name):
            name = node.args[0].id
            if name[0].isupper():
                char_name = name

        # 3. Look up and apply kernel-specific transform
        transform_func = self.registry.get(kernel_name)
        if transform_func:
            transform_func(self.ctx, node, char_name)
        else:
            # Fallback to general heuristics if no specific transform is registered
            self._default_transform(node, char_name)
            
        # 4. Final state update
        self.ctx.seen_kernels.append(kernel_name)
        if char_name:
            self.ctx.last_subject = char_name
            
        return node

    def _default_transform(self, node: ast.Call, char_name: Optional[str]):
        """General heuristics applied to unregistered kernels."""
        kernel_name = node.func.id
        
        # Apply standard pronoun logic
        apply_pronouns(self.ctx, node, char_name)
            
        # Apply standard phase mapping
        if kernel_name in PHASE_MAP:
            apply_phase(self.ctx, node, PHASE_MAP[kernel_name])

# --- Sample Registered Transforms ---

@TRANSFORMS.transform("Fear")
def transform_fear(ctx: TransformContext, node: ast.Call, char_name: Optional[str]):
    """Fear transform: establishes rising action."""
    apply_phase(ctx, node, "rising")
    apply_pronouns(ctx, node, char_name)

@TRANSFORMS.transform("Brave")
def transform_brave(ctx: TransformContext, node: ast.Call, char_name: Optional[str]):
    """Brave transform: climax of the story, requires preceding fear."""
    apply_phase(ctx, node, "climax")
    apply_pronouns(ctx, node, char_name)
    
    # Custom kernel-specific logic: check for preceding fear
    recent = ctx.seen_kernels[-3:]
    if 'Fear' in recent or 'Scared' in recent or 'Danger' in recent:
        inject_kwarg(node, '_after', 'fear')

@TRANSFORMS.transform("Happy")
def transform_happy(ctx: TransformContext, node: ast.Call, char_name: Optional[str]):
    """Happy transform: resolution of the story."""
    apply_phase(ctx, node, "resolution")
    apply_pronouns(ctx, node, char_name)
    
    # Custom logic: distinguish "Happy" from "Happy again"
    if any(k in ctx.seen_kernels for k in ['Sadness', 'Sad', 'Loss', 'Fear']):
        inject_kwarg(node, '_after', 'sadness')

def transform_ast(source: str) -> str:
    """Entry point to transform a story kernel string."""
    try:
        tree = ast.parse(source)
        transformer = StoryASTTransformer(TRANSFORMS)
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)
    except Exception as e:
        print(f"Error during AST transformation: {e}")
        return source

if __name__ == "__main__":
    # Test the transformation
    test_source = """
Lily(Character, girl)
Fear(Lily, dog)
Brave(Lily)
Happy(Lily)
"""
    print("--- Transformed Source ---")
    print(transform_ast(test_source))
