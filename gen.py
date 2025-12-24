import ast
import random

class KernelToText:
    def __init__(self):
        self.characters = {}
        
    def generate(self, kernel_str):
        tree = ast.parse(kernel_str)
        
        # Extract characters first
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if (isinstance(call.func, ast.Name) and 
                    len(call.args) > 0 and 
                    isinstance(call.args[0], ast.Name) and
                    call.args[0].id == 'Character'):
                    self._extract_character(stmt.value)
        
        # Generate story from patterns
        story = []
        for stmt in tree.body:
            text = self._statement_to_text(stmt)
            if text:
                story.append(text)
        
        return ' '.join(story)
    
    def _extract_character(self, call_node):
        """Extract: Lily(Character, girl, Curious+Hopeful)"""
        if not isinstance(call_node.func, ast.Name):
            return
        
        name = call_node.func.id
        char_type = self._node_to_value(call_node.args[1]) if len(call_node.args) > 1 else "character"
        traits = self._node_to_value(call_node.args[2]) if len(call_node.args) > 2 else ""
        
        self.characters[name] = {'type': char_type, 'traits': traits}
    
    def _statement_to_text(self, stmt):
        if not isinstance(stmt, ast.Expr):
            return ""
        
        node = stmt.value
        
        # Character definition
        if isinstance(node, ast.Call) and len(node.args) > 0:
            if isinstance(node.args[0], ast.Name) and node.args[0].id == 'Character':
                return self._character_intro(node)
            
            # Story patterns
            if isinstance(node.func, ast.Name):
                if node.func.id == 'Journey':
                    return self._journey_to_text(node)
                elif node.func.id == 'Cautionary':
                    return self._cautionary_to_text(node)
        
        return ""
    
    def _character_intro(self, call_node):
        name = call_node.func.id
        info = self.characters.get(name, {})
        
        templates = [
            f"{name} was a {info.get('type', 'character')}.",
            f"There was a {info.get('type', 'character')} named {name}.",
            f"Once upon a time, {name} was a {info.get('type', 'character')}."
        ]
        
        traits = info.get('traits', '')
        if traits:
            templates[0] += f" {name} was {traits.lower().replace('+', ' and ')}."
        
        return random.choice(templates)
    
    def _journey_to_text(self, call_node):
        """Convert Journey(...) to narrative"""
        # Extract character (first arg)
        char = self._node_to_value(call_node.args[0]) if call_node.args else "someone"
        
        # Extract keywords
        parts = {}
        for kw in call_node.keywords:
            parts[kw.arg] = self._node_to_value(kw.value)
        
        story = []
        
        # State/setup
        if 'state' in parts:
            story.append(f"{char} was doing {self._phrase(parts['state'])}.")
        
        # Crisis/catalyst
        if 'crisis' in parts:
            story.append(f"But then, {self._phrase(parts['crisis'])}.")
        elif 'catalyst' in parts:
            story.append(f"Suddenly, {self._phrase(parts['catalyst'])}.")
        
        # Process
        if 'process' in parts:
            story.append(f"{char} {self._phrase(parts['process'])}.")
        
        # Insight
        if 'insight' in parts:
            story.append(f"{char} learned {self._phrase(parts['insight'])}.")
        
        # Transformation
        if 'transformation' in parts:
            story.append(f"In the end, {self._phrase(parts['transformation'])}.")
        
        return ' '.join(story)
    
    def _cautionary_to_text(self, call_node):
        """Convert Cautionary tale"""
        return self._journey_to_text(call_node)  # Similar structure
    
    def _phrase(self, text):
        """Convert kernel syntax to natural language phrase"""
        # Handle common patterns
        text = text.replace('+', ' and ')
        text = text.replace('(', ' with ')
        text = text.replace(')', '')
        text = text.replace(',', ' and')
        
        # Lowercase kernel names
        words = text.split()
        words = [w.lower() if w[0].isupper() and w not in self.characters else w for w in words]
        
        return ' '.join(words)
    
    def _node_to_value(self, node):
        """Extract value from AST node as string"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.BinOp):
            left = self._node_to_value(node.left)
            right = self._node_to_value(node.right)
            op = '+' if isinstance(node.op, ast.Add) else '/'
            return f"{left}{op}{right}"
        elif isinstance(node, ast.Call):
            func = self._node_to_value(node.func)
            args = ','.join(self._node_to_value(arg) for arg in node.args)
            return f"{func}({args})"
        return ""


# Usage
if __name__ == "__main__":
    kernel = """
Lily(Character, girl, Curious+Hopeful)
Journey(Lily,
    state=Routine+Travel(car),
    crisis=Stalled(car),
    process=Wait+Discovery(rainbow),
    insight=Joy(Unexpected))
"""
    
    gen = KernelToText()
    print(gen.generate(kernel))
