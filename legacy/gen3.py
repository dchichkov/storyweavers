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

# Character state
@dataclass
class Character:
    name: str
    type: str
    traits: list = field(default_factory=list)
    Love: float = 100.0
    Joy: float = 100.0
    Fear: float = 0.0
    
    def __repr__(self):
        return self.name

# Define kernels
@KERNELS.register(summary="loss", verb="lose", past="lost")
def Loss(character, obj):
    """Character loses something valued."""
    character.Love -= 10
    return f"{character.name} lost {obj}"

@KERNELS.register(summary="discovery", verb="discover", past="discovered")
def Discovery(character, obj):
    """Character discovers something."""
    character.Joy += 15
    return f"{character.name} discovered a {obj}"

@KERNELS.register(summary="wait", verb="wait", past="waited")
def Wait(character):
    """Character waits."""
    character.Joy -= 5
    return f"{character.name} waited"

#@KERNELS.register(summary="stumble", verb="stumble", past="stumbled")
#def Stumble(character, obstacle):
#    """Character stumbles on something."""
#    character.Fear += 10
#    return f"{character.name} stumbled on a {obstacle}"


@KERNELS.register(summary="stumble", verb="stumble", past="stumbled")
def Stumble(*args, **kwargs):
    """Character stumbles, optionally on something."""
    # Handle different argument patterns
    if len(args) == 0:
        return "stumbled"
    
    # Unpack based on types
    character = None
    obstacle = None
    
    for arg in args:
        if isinstance(arg, Character):
            character = arg
        elif isinstance(arg, str):
            obstacle = arg
        elif isinstance(arg, KernelConcept):
            obstacle = str(arg)
    
    # Build text and mutate state
    if character and obstacle:
        character.Fear += 10
        return f"{character.name} stumbled on a {obstacle}"
    elif character:
        character.Fear += 10
        return f"{character.name} stumbled"
    elif obstacle:
        return f"stumbled on a {obstacle}"
    
    return "stumbled"

@KERNELS.register(summary="help", verb="help", past="helped")
def Help(helper, helpee):
    """One character helps another."""
    helper.Love += 5
    helpee.Love += 10
    return f"{helper.name} helped {helpee.name}"

@KERNELS.register(summary="journey", verb="journey", past="journeyed")
def Journey(character, **kwargs):
    """Character goes on journey."""
    parts = []
    
    if 'state' in kwargs:
        parts.append(f"{character.name} was in a routine.")
    
    if 'crisis' in kwargs or 'catalyst' in kwargs:
        crisis_text = kwargs.get('crisis') or kwargs.get('catalyst')
        parts.append(f"But then, {crisis_text}.")
    
    if 'process' in kwargs:
        parts.append(kwargs['process'])
    
    if 'insight' in kwargs:
        parts.append(f"{character.name} learned that {kwargs['insight']}.")
        character.Joy += 20
    
    return ' '.join(parts)


# AST Executor
class KernelExecutor:
    def __init__(self, registry: KernelRegistry):
        self.registry = registry
        self.characters: Dict[str, Character] = {}
        self.story_parts = []
    
    def execute(self, kernel_str: str) -> str:
        tree = ast.parse(kernel_str)
        
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr):
                result = self._eval_node(stmt.value)
                if result:
                    self.story_parts.append(result)
        
        return ' '.join(self.story_parts)
    
    def _eval_node(self, node):
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            # Handle + composition
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return f"{left} and {right}"
        elif isinstance(node, ast.Name):
            return node.id.lower()
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return None
    
    def _eval_call(self, call_node):
        if not isinstance(call_node.func, ast.Name):
            return None
        
        func_name = call_node.func.id
        
        # Character definition
        if (call_node.args and isinstance(call_node.args[0], ast.Name) and 
            call_node.args[0].id == 'Character'):
            char_name = func_name
            char_type = self._eval_node(call_node.args[1]) if len(call_node.args) > 1 else "character"
            traits = self._eval_node(call_node.args[2]) if len(call_node.args) > 2 else []
            
            self.characters[char_name] = Character(char_name, char_type, traits)
            return f"There was a {char_type} named {char_name}."
        
        # Kernel execution
        if func_name in self.registry.kernels:
            kernel_func = self.registry.kernels[func_name]
            
            # Evaluate arguments
            args = []
            for arg in call_node.args:
                if isinstance(arg, ast.Name) and arg.id in self.characters:
                    args.append(self.characters[arg.id])
                else:
                    args.append(self._eval_node(arg))
            
            # Evaluate keyword arguments
            kwargs = {}
            for kw in call_node.keywords:
                kwargs[kw.arg] = self._eval_node(kw.value)
            
            # Execute kernel
            return kernel_func(*args, **kwargs)
        
        return None


# Example usage
if __name__ == "__main__":
    kernel = """
Lily(Character, girl, Curious+Hopeful)
Journey(Lily,
    state=Routine,
    crisis=Stumble(Lily, rock),
    process=Wait(Lily) + Discovery(Lily, rainbow),
    insight="unexpected things bring joy")
"""
    
    executor = KernelExecutor(KERNELS)
    story = executor.execute(kernel)
    
    print("STORY:")
    print(story)
    
    print("\n\nCHARACTER STATE:")
    for char in executor.characters.values():
        print(f"{char.name}: Joy={char.Joy:.1f}, Love={char.Love:.1f}, Fear={char.Fear:.1f}")
