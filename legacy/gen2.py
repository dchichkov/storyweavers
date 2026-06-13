import ast
import random
from typing import Dict, Any

class KernelToText:
    def __init__(self):
        self.characters = {}
        self.verb_map = {
            'Wait': 'waited',
            'Discovery': 'discovered',
            'Travel': 'traveled',
            'Stalled': 'got stuck',
            'Find': 'found',
            'Help': 'helped',
            'Fall': 'fell',
            'Stumble': 'stumbled',
            'Observe': 'observed',
            'Wonder': 'wondered about',
            'Rescue': 'was rescued by',
        }
        
    def generate(self, kernel_str):
        tree = ast.parse(kernel_str)
        
        # Extract characters
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                self._maybe_extract_character(stmt.value)
        
        # Generate story
        parts = []
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Name):
                    if call.func.id == 'Journey':
                        parts.append(self._journey_to_text(call))
        
        return ' '.join(parts)
    
    def _maybe_extract_character(self, call_node):
        if not isinstance(call_node.func, ast.Name):
            return
        
        # Check if Character(...) pattern
        if (call_node.args and isinstance(call_node.args[0], ast.Name) and 
            call_node.args[0].id == 'Character'):
            name = call_node.func.id
            char_type = self._get_arg(call_node, 1, 'character')
            traits = self._get_arg(call_node, 2, '')
            self.characters[name] = {'type': char_type, 'traits': traits}
    
    def _journey_to_text(self, call_node):
        char = self._get_arg(call_node, 0, 'someone')
        kw = {kw.arg: kw.value for kw in call_node.keywords}
        
        sentences = []
        
        # Setup
        char_info = self.characters.get(char, {})
        if char_info:
            trait_text = self._traits_to_text(char_info.get('traits', ''))
            sentences.append(f"Once upon a time, there was a {trait_text} {char_info['type']} named {char}.")
        
        # State
        if 'state' in kw:
            state_text = self._state_to_text(char, kw['state'])
            sentences.append(state_text)
        
        # Crisis/Catalyst
        if 'crisis' in kw:
            sentences.append(self._crisis_to_text(kw['crisis']))
        elif 'catalyst' in kw:
            sentences.append(self._catalyst_to_text(kw['catalyst']))
        
        # Process
        if 'process' in kw:
            sentences.append(self._process_to_text(char, kw['process']))
        
        # Insight
        if 'insight' in kw:
            sentences.append(self._insight_to_text(char, kw['insight']))
        
        return ' '.join(sentences)
    
    def _traits_to_text(self, traits_node):
        if isinstance(traits_node, str):
            return traits_node.lower().replace('+', ' and ')
        text = self._node_to_text(traits_node)
        return text.lower().replace('+', ' and ')
    
    def _state_to_text(self, char, state_node):
        """Convert state description to opening sentence"""
        components = self._split_by_plus(state_node)
        
        actions = []
        for comp in components:
            if isinstance(comp, ast.Call):
                func_name = comp.func.id if isinstance(comp.func, ast.Name) else ''
                if func_name == 'Travel':
                    vehicle = self._get_arg(comp, 0, 'somewhere')
                    actions.append(f"traveling by {vehicle}")
                elif func_name == 'Routine':
                    continue  # Skip, implied
                else:
                    actions.append(func_name.lower())
            elif isinstance(comp, ast.Name):
                if comp.id != 'Routine':
                    actions.append(comp.id.lower())
        
        if actions:
            return f"{char} was {' and '.join(actions)} with her family."
        return f"{char} was going about her day."
    
    def _crisis_to_text(self, crisis_node):
        if isinstance(crisis_node, ast.Call):
            func = crisis_node.func.id if isinstance(crisis_node.func, ast.Name) else ''
            if func == 'Stalled':
                what = self._get_arg(crisis_node, 0, 'something')
                return f"But then, the {what} got stuck!"
        
        text = self._node_to_text(crisis_node)
        return f"But then, {text}!"
    
    def _catalyst_to_text(self, catalyst_node):
        components = self._split_by_plus(catalyst_node)
        events = []
        
        for comp in components:
            if isinstance(comp, ast.Call):
                func = comp.func.id if isinstance(comp.func, ast.Name) else ''
                verb = self.verb_map.get(func, func.lower())
                arg = self._get_arg(comp, 0, '')
                events.append(f"{verb} on a {arg}" if arg else verb)
            elif isinstance(comp, ast.Name):
                verb = self.verb_map.get(comp.id, comp.id.lower())
                events.append(verb)
        
        return f"Suddenly, she {' and '.join(events)}!"
    
    def _process_to_text(self, char, process_node):
        components = self._split_by_plus(process_node)
        actions = []
        
        for comp in components:
            if isinstance(comp, ast.Call):
                func = comp.func.id if isinstance(comp.func, ast.Name) else ''
                verb = self.verb_map.get(func, func.lower())
                
                arg = self._get_arg(comp, 0, '')
                if isinstance(comp.args[0], ast.List) if comp.args else False:
                    items = [self._node_to_text(el) for el in comp.args[0].elts]
                    arg = ', '.join(items[:-1]) + f' and {items[-1]}'
                
                actions.append(f"{verb} a {arg}" if arg and func == 'Discovery' else 
                              f"{verb} {arg}" if arg else verb)
            elif isinstance(comp, ast.Name):
                verb = self.verb_map.get(comp.id, comp.id.lower() + 'ed')
                actions.append(verb)
        
        if actions:
            return f"{char} {', '.join(actions[:-1])} and {actions[-1]}." if len(actions) > 1 else f"{char} {actions[0]}."
        return ""
    
    def _insight_to_text(self, char, insight_node):
        if isinstance(insight_node, ast.Call):
            func = insight_node.func.id if isinstance(insight_node.func, ast.Name) else ''
            if func == 'Joy':
                what = self._get_arg(insight_node, 0, 'something')
                return f"Even though things didn't go as planned, {char} found joy in the unexpected {what.lower()}."
            elif func == 'Lesson':
                return f"{char} learned an important lesson."
        
        return f"{char} felt different after that."
    
    def _split_by_plus(self, node):
        """Split node by + operators"""
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._split_by_plus(node.left) + self._split_by_plus(node.right)
        return [node]
    
    def _get_arg(self, call_node, idx, default):
        if isinstance(call_node, ast.Call) and len(call_node.args) > idx:
            return self._node_to_text(call_node.args[idx])
        return default
    
    def _node_to_text(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Call):
            return node.func.id if isinstance(node.func, ast.Name) else ''
        return ''


# Test
kernel = """
Lily(Character, girl, Curious+Hopeful)
Journey(Lily,
    state=Routine+Travel(car),
    crisis=Stalled(car),
    process=Wait+Discovery(rainbow),
    insight=Joy(Discovery))
"""

gen = KernelToText()
print(gen.generate(kernel))
