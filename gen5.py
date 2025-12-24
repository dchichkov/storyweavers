"""
Storyweavers Generation Engine (gen5.py)

A classical NLG system that converts story kernels to natural language text.
No LLMs at generation time - only templates, NLTK, and compositional execution.

DESIGN PRINCIPLES
=================
- Kernels ARE valid Python ASTs (function calls with args/kwargs)
- Generation happens by executing kernels against a registry
- NLTK provides linguistic variation (synonyms, inflection, articles)
- Templates with slots provide sentence structure
- Composition operators (+, /, newlines) handled by the interpreter

ARCHITECTURE
============
    Kernel String → ast.parse() → KernelExecutor
                                        ↓
                                  _eval_node() for each statement
                                        ↓
                                  Lookup kernel in REGISTRY
                                        ↓
                                  Execute kernel function
                                        ↓
                                  Returns StoryFragment
                                        ↓
                                  StoryContext.render() → Final Story

ADDING NEW KERNELS (Coding Agent Workflow)
==========================================
The recommended approach for expanding kernel coverage is interactive development
with a coding agent (like Claude, Cursor, etc.) rather than automated LLM synthesis.

Why this works better:
1. Context-aware: The agent sees the full codebase and existing patterns
2. Iterative refinement: Can test, debug, and improve in real-time
3. Consistent style: Follows established conventions
4. Better error handling: Handles edge cases discovered during testing

To add a new kernel, use this pattern:

    @REGISTRY.kernel("KernelName")
    def kernel_name(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
        '''Docstring describing the kernel.'''
        
        # 1. Parse arguments
        chars = [a for a in args if isinstance(a, Character)]
        objects = [str(a) for a in args if isinstance(a, str)]
        
        # 2. Update character state (optional)
        if chars:
            chars[0].Joy += 10  # or Fear, Love, Sadness, etc.
        
        # 3. Generate text based on arguments
        if len(chars) >= 2:
            return StoryFragment(f"{chars[0].name} verbed {chars[1].name}.")
        elif chars:
            return StoryFragment(f"{chars[0].name} verbed.")
        
        # 4. Handle concept/state usage (no character = nested in parent kernel)
        return StoryFragment("verbed", kernel_name="KernelName")

USAGE
=====
    from gen5 import generate_story
    
    kernel = '''
    Tim(Character, boy, Brave)
    Encounter(Tim, wolf)
    Fear(Tim)
    Brave(Tim)
    Run(wolf)
    Joy(Tim)
    '''
    
    story = generate_story(kernel)
    print(story)
    # "Once upon a time, there was a brave boy named Tim. Tim came across a wolf.
    #  Tim was scared. Tim was very brave. The wolf ran away. Tim felt very happy."
"""

import ast
import random
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional, Union, Tuple
from collections import defaultdict
import re

# Try to import NLTK, gracefully degrade if unavailable
try:
    import nltk
    from nltk.corpus import wordnet
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
    # Download required data silently
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('punkt', quiet=True)
except ImportError:
    NLTK_AVAILABLE = False
    print("Warning: NLTK not available. Using fallback text generation.")


# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class Character:
    """A story character with mutable emotional state."""
    name: str
    char_type: str = "character"
    traits: List[str] = field(default_factory=list)
    
    # Emotional state (0-100 scale)
    Joy: float = 50.0
    Fear: float = 0.0
    Love: float = 50.0
    Anger: float = 0.0
    Sadness: float = 0.0
    
    # For pronoun resolution
    pronouns: Tuple[str, str, str] = ("they", "them", "their")
    
    def __repr__(self):
        return self.name
    
    def __str__(self):
        return self.name
    
    def set_pronouns(self, subj: str, obj: str, poss: str):
        self.pronouns = (subj, obj, poss)
    
    @property
    def he(self): return self.pronouns[0]
    @property
    def him(self): return self.pronouns[1]  
    @property
    def his(self): return self.pronouns[2]


@dataclass 
class StoryFragment:
    """A piece of generated text with metadata."""
    text: str
    weight: float = 1.0  # Attention weight (reduced by / operator)
    kernel_name: str = ""
    
    def __str__(self):
        return self.text
    
    def __add__(self, other):
        """Composition: combine two fragments."""
        if isinstance(other, StoryFragment):
            return StoryFragment(
                text=f"{self.text} {other.text}".strip(),
                weight=(self.weight + other.weight) / 2
            )
        return StoryFragment(text=f"{self.text} {other}".strip(), weight=self.weight)
    
    def __truediv__(self, divisor):
        """Attention dilution: reduce weight."""
        return StoryFragment(self.text, self.weight / divisor, self.kernel_name)


@dataclass
class StoryContext:
    """Execution context for story generation."""
    characters: Dict[str, Character] = field(default_factory=dict)
    fragments: List[StoryFragment] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    current_focus: Optional[Character] = None
    
    def add_character(self, name: str, char_type: str, traits: List[str]) -> Character:
        char = Character(name, char_type, traits)
        # Infer pronouns from type
        if char_type in ('girl', 'woman', 'queen', 'princess', 'mother', 'grandma'):
            char.set_pronouns('she', 'her', 'her')
        elif char_type in ('boy', 'man', 'king', 'prince', 'father', 'grandpa'):
            char.set_pronouns('he', 'him', 'his')
        self.characters[name] = char
        return char
    
    def emit(self, text: str, weight: float = 1.0, kernel: str = ""):
        """Add a text fragment to the story."""
        if text and weight > 0.1:  # Skip very low weight fragments
            self.fragments.append(StoryFragment(text, weight, kernel))
    
    def render(self) -> str:
        """Render all fragments into final story text."""
        # Filter by weight and join
        texts = []
        for frag in self.fragments:
            if frag.weight > 0.3:  # Threshold for inclusion
                texts.append(frag.text)
        
        story = ' '.join(texts)
        # Clean up spacing and punctuation
        story = re.sub(r'\s+', ' ', story)
        story = re.sub(r'\s+([.,!?])', r'\1', story)
        # Fix double periods
        story = re.sub(r'\.\.+', '.', story)
        story = re.sub(r'\.!', '!', story)
        story = re.sub(r'\.\?', '?', story)
        # Capitalize after sentence-ending punctuation
        story = re.sub(r'([.!?])\s+([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), story)
        return story.strip()


# =============================================================================
# NATURAL LANGUAGE UTILITIES
# =============================================================================

class NLGUtils:
    """Natural language generation utilities using NLTK."""
    
    # Verb inflection patterns (past tense)
    IRREGULAR_PAST = {
        'run': 'ran', 'eat': 'ate', 'see': 'saw', 'find': 'found', 'feed': 'fed',
        'give': 'gave', 'take': 'took', 'make': 'made', 'come': 'came',
        'go': 'went', 'get': 'got', 'have': 'had', 'be': 'was',
        'say': 'said', 'tell': 'told', 'think': 'thought', 'feel': 'felt',
        'know': 'knew', 'hear': 'heard', 'begin': 'began', 'fall': 'fell',
        'fly': 'flew', 'grow': 'grew', 'hide': 'hid', 'hold': 'held',
        'lose': 'lost', 'meet': 'met', 'read': 'read', 'sing': 'sang',
        'sit': 'sat', 'sleep': 'slept', 'swim': 'swam', 'teach': 'taught',
        'throw': 'threw', 'understand': 'understood', 'wake': 'woke',
        'win': 'won', 'write': 'wrote', 'bring': 'brought', 'buy': 'bought',
        'catch': 'caught', 'choose': 'chose', 'draw': 'drew', 'drink': 'drank',
        'drive': 'drove', 'forget': 'forgot', 'freeze': 'froze', 'hurt': 'hurt',
        'keep': 'kept', 'lead': 'led', 'leave': 'left', 'let': 'let',
        'put': 'put', 'ride': 'rode', 'rise': 'rose', 'seek': 'sought',
        'send': 'sent', 'shake': 'shook', 'shine': 'shone', 'show': 'showed',
        'shut': 'shut', 'speak': 'spoke', 'spend': 'spent', 'stand': 'stood',
        'steal': 'stole', 'stick': 'stuck', 'strike': 'struck', 'sweep': 'swept',
        'wear': 'wore', 'weep': 'wept',
    }
    
    @staticmethod
    def past_tense(verb: str) -> str:
        """Convert verb to past tense."""
        verb = verb.lower()
        if verb in NLGUtils.IRREGULAR_PAST:
            return NLGUtils.IRREGULAR_PAST[verb]
        # Regular rules
        if verb.endswith('e'):
            return verb + 'd'
        if verb.endswith('y') and len(verb) > 1 and verb[-2] not in 'aeiou':
            return verb[:-1] + 'ied'
        if len(verb) > 2 and verb[-1] not in 'aeiouwxy' and verb[-2] in 'aeiou' and verb[-3] not in 'aeiou':
            return verb + verb[-1] + 'ed'  # Double consonant
        return verb + 'ed'
    
    @staticmethod
    def present_participle(verb: str) -> str:
        """Convert verb to -ing form."""
        verb = verb.lower()
        if verb.endswith('ie'):
            return verb[:-2] + 'ying'
        if verb.endswith('e') and not verb.endswith('ee'):
            return verb[:-1] + 'ing'
        if len(verb) > 2 and verb[-1] not in 'aeiouwxy' and verb[-2] in 'aeiou' and verb[-3] not in 'aeiou':
            return verb + verb[-1] + 'ing'
        return verb + 'ing'
    
    @staticmethod
    def article(word: str) -> str:
        """Get appropriate article (a/an)."""
        if not word:
            return "a"
        word = word.lower().strip()
        if word[0] in 'aeiou':
            return "an"
        return "a"
    
    @staticmethod
    def pluralize(word: str) -> str:
        """Simple pluralization."""
        if word.endswith('s') or word.endswith('x') or word.endswith('sh') or word.endswith('ch'):
            return word + 'es'
        if word.endswith('y') and len(word) > 1 and word[-2] not in 'aeiou':
            return word[:-1] + 'ies'
        return word + 's'
    
    @staticmethod
    def synonym(word: str) -> str:
        """Get a synonym using WordNet (if available)."""
        if not NLTK_AVAILABLE:
            return word
        try:
            synsets = wordnet.synsets(word)
            if synsets:
                lemmas = synsets[0].lemmas()
                candidates = [l.name().replace('_', ' ') for l in lemmas if l.name() != word]
                if candidates:
                    return random.choice(candidates)
        except:
            pass
        return word
    
    @staticmethod
    def join_list(items: List[str], conjunction: str = "and") -> str:
        """Join list items with proper grammar."""
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} {conjunction} {items[1]}"
        return ", ".join(items[:-1]) + f", {conjunction} " + items[-1]


# =============================================================================
# TEMPLATE SYSTEM
# =============================================================================

class TemplateEngine:
    """Sentence template system with slot filling."""
    
    def __init__(self):
        self.templates: Dict[str, List[str]] = defaultdict(list)
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load built-in sentence templates."""
        
        # Character introduction - weighted by position
        self.add('intro_first', "Once upon a time, there was {article} {adj} {type} named {name}.")
        self.add('intro_first', "There once was {article} {adj} {type} named {name}.")
        self.add('intro', "There was also {article} {type} named {name}.")
        self.add('intro', "{name} was {article} {adj} {type}.")
        self.add('intro', "{name}, {article} {adj} {type}, lived nearby.")
        
        # Lived/setting
        self.add('lived', "{name} lived in {article} {adj} {place}.")
        self.add('lived', "{name} lived with {others} in {article} {place}.")
        
        # Wanted/desire
        self.add('wanted', "{name} wanted to {goal}.")
        self.add('wanted', "{name} really wanted {object}.")
        self.add('wanted', "More than anything, {name} wanted to {goal}.")
        
        # Actions
        self.add('find', "{name} found {article} {object}.")
        self.add('find', "One day, {name} found {article} {adj} {object}.")
        
        self.add('play', "{name} played with {object}.")
        self.add('play', "{name} and {other} played together.")
        self.add('play', "{name} had fun playing.")
        
        self.add('see', "{name} saw {article} {object}.")
        self.add('see', "{name} noticed {article} {adj} {object}.")
        
        self.add('run', "{name} ran {direction}.")
        self.add('run', "{name} ran as fast as {he} could.")
        
        self.add('walk', "{name} walked {direction}.")
        self.add('walk', "{name} went for a walk.")
        
        # Emotions
        self.add('joy', "{name} felt very happy.")
        self.add('joy', "{name} was filled with joy.")
        self.add('joy', "{name} smiled happily.")
        
        self.add('sad', "{name} felt sad.")
        self.add('sad', "{name} was unhappy.")
        
        self.add('fear', "{name} was scared.")
        self.add('fear', "{name} felt afraid.")
        
        self.add('surprise', "{name} was surprised!")
        self.add('surprise', "What a surprise!")
        
        # Transitions
        self.add('then', "Then, {event}.")
        self.add('but', "But then, {event}.")
        self.add('suddenly', "Suddenly, {event}!")
        self.add('oneday', "One day, {event}.")
        
        # Friendship
        self.add('friendship', "{name} and {other} became friends.")
        self.add('friendship', "{name} and {other} were best friends.")
        
        # Learning/insight
        self.add('learn', "{name} learned that {lesson}.")
        self.add('learn', "{name} realized that {lesson}.")
        
        # Endings
        self.add('happy_end', "And they lived happily ever after.")
        self.add('happy_end', "Everyone was happy.")
        self.add('happy_end', "{name} was happy in the end.")
        
        # Journey structure
        self.add('journey_state', "{name} was {state}.")
        self.add('journey_catalyst', "But then, something {adj} happened.")
        self.add('journey_process', "{name} {action}.")
        self.add('journey_insight', "{name} learned {lesson}.")
        self.add('journey_transform', "After that, {name} was {state}.")
    
    def add(self, category: str, template: str):
        """Add a template to a category."""
        self.templates[category].append(template)
    
    def generate(self, category: str, **slots) -> str:
        """Generate text from a template with slot filling."""
        templates = self.templates.get(category, [])
        if not templates:
            return ""
        
        template = random.choice(templates)
        
        # Auto-generate article if needed
        if '{article}' in template and 'article' not in slots:
            # Find the word after {article}
            for key in ['adj', 'type', 'object', 'place']:
                if key in slots and slots[key]:
                    slots['article'] = NLGUtils.article(str(slots[key]))
                    break
            else:
                slots['article'] = 'a'
        
        # Fill slots
        try:
            return template.format(**slots)
        except KeyError as e:
            # Missing slot - try to fill with placeholder
            slots[str(e).strip("'")] = "something"
            try:
                return template.format(**slots)
            except:
                return ""


# =============================================================================
# KERNEL REGISTRY & DECORATORS  
# =============================================================================

class KernelRegistry:
    """Registry of story kernel implementations."""
    
    def __init__(self):
        self.kernels: Dict[str, Callable] = {}
        self.metadata: Dict[str, Dict] = {}
        self.templates = TemplateEngine()
    
    def kernel(self, name: str = None, verb: str = None, templates: List[str] = None):
        """Decorator to register a kernel function."""
        def decorator(func):
            kernel_name = name or func.__name__
            self.kernels[kernel_name] = func
            self.metadata[kernel_name] = {
                'verb': verb or kernel_name.lower(),
                'doc': func.__doc__,
            }
            # Add custom templates
            if templates:
                for t in templates:
                    self.templates.add(kernel_name.lower(), t)
            return func
        return decorator
    
    def get(self, name: str) -> Optional[Callable]:
        return self.kernels.get(name)
    
    def __contains__(self, name: str) -> bool:
        return name in self.kernels


# Global registry
REGISTRY = KernelRegistry()


# =============================================================================
# KERNEL IMPLEMENTATIONS
# =============================================================================

# --- Character Definition ---
@REGISTRY.kernel("Character")
def kernel_character(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Define a character - handled specially by executor."""
    # This is a marker, actual handling in executor
    return StoryFragment("")


# --- Meta-patterns (Story Structures) ---
@REGISTRY.kernel("Journey", templates=[
    "{name} went on a journey.",
    "{name}'s life was about to change."
])
def kernel_journey(ctx: StoryContext, character: Character = None, **kwargs) -> StoryFragment:
    """The Journey pattern - character transformation through experience."""
    parts = []
    
    # Handle case where character might not be passed
    if character is None:
        character = ctx.current_focus
    if character is None:
        character = Character("someone", "person")
    
    # State (initial situation)
    if 'state' in kwargs:
        state = kwargs['state']
        state_text = _state_to_phrase(state)
        if state_text:
            parts.append(f"{character.name} was {state_text}.")
    
    # Catalyst/Crisis (inciting incident)
    for key in ['catalyst', 'crisis']:
        if key in kwargs:
            event = kwargs[key]
            event_text = _event_to_phrase(event)
            if event_text:
                parts.append(f"But then, {event_text}!")
    
    # Process (the journey itself)
    if 'process' in kwargs:
        process = kwargs['process']
        process_text = _action_to_phrase(process)
        if process_text:
            parts.append(f"{character.name} {process_text}.")
    
    # Insight (what they learned)
    if 'insight' in kwargs:
        insight = kwargs['insight']
        character.Joy += 15
        insight_text = _to_phrase(insight)
        if insight_text:
            parts.append(f"{character.name} learned something important.")
    
    # Transformation (how they changed)
    if 'transformation' in kwargs:
        transform = kwargs['transformation']
        character.Joy += 10
        transform_text = _state_to_phrase(transform)
        if transform_text:
            parts.append(f"After that, {character.name} felt {transform_text}.")
    
    return StoryFragment(' '.join(parts), kernel_name="Journey")


@REGISTRY.kernel("Cautionary", templates=[
    "This is a story about being careful.",
])
def kernel_cautionary(ctx: StoryContext, character: Character = None, **kwargs) -> StoryFragment:
    """Cautionary tale pattern - character learns from mistake."""
    parts = []
    
    # Handle case where character might not be passed
    if character is None:
        character = ctx.current_focus
    if character is None:
        character = Character("someone", "person")
    
    if 'state' in kwargs:
        state_text = _state_to_phrase(kwargs['state'])
        if state_text:
            parts.append(f"{character.name} was {state_text}.")
    
    if 'event' in kwargs or 'trigger' in kwargs:
        event = kwargs.get('event') or kwargs.get('trigger')
        event_text = _event_to_phrase(event)
        if event_text:
            parts.append(f"One day, {event_text}.")
    
    if 'consequence' in kwargs:
        character.Fear += 10
        character.Joy -= 10
        cons_text = _state_to_phrase(kwargs['consequence'])
        if cons_text:
            parts.append(f"Because of that, {character.name} felt {cons_text}.")
    
    if 'lesson' in kwargs:
        lesson_text = _to_phrase(kwargs['lesson'])
        if lesson_text:
            parts.append(f"{character.name} learned to be more {lesson_text}.")
    
    return StoryFragment(' '.join(parts), kernel_name="Cautionary")


@REGISTRY.kernel("Friendship", templates=[
    "{name} and {other} became good friends.",
])
def kernel_friendship(ctx: StoryContext, char1: Character, char2: Character = None, **kwargs) -> StoryFragment:
    """Friendship pattern - two characters form a bond."""
    parts = []
    
    other_name = char2.name if char2 else "a new friend"
    
    if char1:
        char1.Love += 15
    if char2:
        char2.Love += 15
    
    if 'state' in kwargs:
        parts.append(f"{char1.name} was {_to_phrase(kwargs['state'])}.")
    
    if 'catalyst' in kwargs:
        parts.append(f"Then, {_to_phrase(kwargs['catalyst'])}.")
    
    if 'process' in kwargs:
        parts.append(_to_phrase(kwargs['process']))
    
    parts.append(f"{char1.name} and {other_name} became good friends.")
    
    if 'transformation' in kwargs:
        parts.append(f"They were {_to_phrase(kwargs['transformation'])} together.")
    
    return StoryFragment(' '.join(parts), kernel_name="Friendship")


# --- Action Kernels ---
@REGISTRY.kernel("Play", verb="play", templates=[
    "{name} played happily.",
    "{name} and {other} played together.",
])
def kernel_play(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters play."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str) and a != 'Character']
    
    for c in chars:
        c.Joy += 10
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} played together and had fun.")
    elif len(chars) == 1:
        if objects:
            return StoryFragment(f"{chars[0].name} played with the {NLGUtils.join_list(objects)}.")
        return StoryFragment(f"{chars[0].name} played happily.")
    
    # No characters - this is probably being used as a state/concept
    if objects:
        return StoryFragment(f"playing with the {NLGUtils.join_list(objects)}", kernel_name="Play")
    return StoryFragment("playing", kernel_name="Play")


@REGISTRY.kernel("Find", verb="find", templates=[
    "{name} found {article} {object}.",
])
def kernel_find(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character finds something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = chars[0] if chars else ctx.current_focus
    obj = objects[0] if objects else kwargs.get('object', 'something')
    
    if char:
        char.Joy += 5
        return StoryFragment(f"{char.name} found {NLGUtils.article(str(obj))} {obj}.")
    return StoryFragment(f"Someone found {NLGUtils.article(str(obj))} {obj}.")


@REGISTRY.kernel("See", verb="see")
def kernel_see(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character sees something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = chars[0] if chars else ctx.current_focus
    obj = objects[0] if objects else "something"
    
    if char:
        return StoryFragment(f"{char.name} saw {NLGUtils.article(str(obj))} {obj}.")
    return StoryFragment(f"They saw {NLGUtils.article(str(obj))} {obj}.")


@REGISTRY.kernel("Walk", verb="walk")
def kernel_walk(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character walks."""
    chars = [a for a in args if isinstance(a, Character)]
    char = chars[0] if chars else ctx.current_focus
    destination = kwargs.get('to') or kwargs.get('destination', '')
    
    if char:
        if destination:
            return StoryFragment(f"{char.name} walked to the {destination}.")
        return StoryFragment(f"{char.name} went for a walk.")
    return StoryFragment("They went for a walk.")


@REGISTRY.kernel("Run", verb="run")
def kernel_run(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character runs."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else None
    
    if char:
        char.Fear += 5  # Running often implies urgency
        return StoryFragment(f"{char.name} ran as fast as {char.he} could.")
    
    # If first arg is a string (like "wolf"), use that as subject
    if objects:
        subject = objects[0]
        return StoryFragment(f"The {subject} ran away.")
    
    return StoryFragment("They ran quickly.")


@REGISTRY.kernel("Laugh", verb="laugh")
def kernel_laugh(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters laugh."""
    chars = [a for a in args if isinstance(a, Character)]
    
    for c in chars:
        c.Joy += 8
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} laughed together.")
    elif chars:
        return StoryFragment(f"{chars[0].name} laughed happily.")
    return StoryFragment("Everyone laughed.")


@REGISTRY.kernel("Cry", verb="cry")
def kernel_cry(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character cries."""
    chars = [a for a in args if isinstance(a, Character)]
    char = chars[0] if chars else None
    
    if char:
        char.Sadness += 15
        char.Joy -= 10
        return StoryFragment(f"{char.name} started to cry.")
    # No character - used as concept
    return StoryFragment("cried", kernel_name="Cry")


@REGISTRY.kernel("Help", verb="help")
def kernel_help(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character helps another."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        helper, helpee = chars[0], chars[1]
        helper.Love += 10
        helpee.Love += 5
        helpee.Joy += 5
        return StoryFragment(f"{helper.name} helped {helpee.name}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} helped out.")
    return StoryFragment("Someone helped.")


@REGISTRY.kernel("Share", verb="share")
def kernel_share(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character shares something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = chars[0] if chars else ctx.current_focus
    obj = objects[0] if objects else "things"
    
    if char:
        char.Love += 8
        return StoryFragment(f"{char.name} shared {char.his} {obj}.")
    return StoryFragment(f"They shared the {obj}.")


@REGISTRY.kernel("Give", verb="give")
def kernel_give(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character gives something to another."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    if len(chars) >= 2:
        giver, receiver = chars[0], chars[1]
        obj = objects[0] if objects else "a gift"
        giver.Love += 5
        receiver.Joy += 10
        return StoryFragment(f"{giver.name} gave {receiver.name} {NLGUtils.article(obj)} {obj}.")
    elif chars and objects:
        return StoryFragment(f"{chars[0].name} gave away the {objects[0]}.")
    return StoryFragment("A gift was given.")


# --- Emotion Kernels ---
@REGISTRY.kernel("Joy", templates=["{name} felt very happy."])
def kernel_joy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Express joy."""
    chars = [a for a in args if isinstance(a, Character)]
    intensity = kwargs.get('intensity', 'very')
    
    for c in chars:
        c.Joy += 20
    
    if chars:
        return StoryFragment(f"{chars[0].name} felt {intensity} happy.")
    # No character - used as concept/state
    return StoryFragment("felt joyful", kernel_name="Joy")


@REGISTRY.kernel("Sadness", templates=["{name} felt sad."])
def kernel_sadness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Express sadness."""
    chars = [a for a in args if isinstance(a, Character)]
    
    for c in chars:
        c.Sadness += 15
        c.Joy -= 10
    
    if chars:
        return StoryFragment(f"{chars[0].name} felt sad.")
    # No character - used as concept/state
    return StoryFragment("sad", kernel_name="Sadness")


@REGISTRY.kernel("Fear", templates=["{name} was scared."])
def kernel_fear(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Express fear."""
    chars = [a for a in args if isinstance(a, Character)]
    
    for c in chars:
        c.Fear += 20
    
    if chars:
        return StoryFragment(f"{chars[0].name} was scared.")
    return StoryFragment("Fear filled the air.")


@REGISTRY.kernel("Surprise", templates=["What a surprise!"])
def kernel_surprise(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Express surprise."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was very surprised!")
    return StoryFragment("What a surprise!")


@REGISTRY.kernel("Happy")
def kernel_happy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters are happy."""
    chars = [a for a in args if isinstance(a, Character)]
    for c in chars:
        c.Joy += 15
    
    if chars:
        return StoryFragment(f"{chars[0].name} was happy.")
    return StoryFragment("Everyone was happy.")


# --- Transition/Routine Kernels ---
@REGISTRY.kernel("Routine")
def kernel_routine(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Establish routine/normal state."""
    chars = [a for a in args if isinstance(a, Character)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    activity = kwargs.get('activity') or kwargs.get('process', '')
    
    char = chars[0] if chars else ctx.current_focus
    
    # Check if there's an activity in the args
    if fragments:
        activity = _to_phrase(fragments[0])
    
    if char and activity:
        return StoryFragment(f"Every day, {char.name} would {activity}.")
    elif char:
        return StoryFragment(f"{char.name} was going about {char.his} day as usual.")
    return StoryFragment("It was a normal day.")


@REGISTRY.kernel("Encounter")
def kernel_encounter(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters encounter something/someone."""
    chars = [a for a in args if isinstance(a, Character)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    objects = [str(a) for a in args if not isinstance(a, (Character, StoryFragment)) and a is not None]
    location = kwargs.get('at') or kwargs.get('location', '')
    
    char = chars[0] if chars else ctx.current_focus
    
    # Determine what was encountered
    if len(chars) > 1:
        obj = chars[1].name
    elif fragments:
        obj = _to_phrase(fragments[0])
    elif objects:
        obj = objects[0].lower()
    else:
        obj = "something"
    
    if char:
        if location:
            return StoryFragment(f"{char.name} went to the {location} and found {NLGUtils.article(obj)} {obj}.")
        return StoryFragment(f"{char.name} came across {NLGUtils.article(obj)} {obj}.")
    return StoryFragment(f"There was an encounter with {obj}.")


@REGISTRY.kernel("Discovery")
def kernel_discovery(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character discovers something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = chars[0] if chars else ctx.current_focus
    obj = objects[0] if objects else "something wonderful"
    
    if char:
        char.Joy += 12
        return StoryFragment(f"{char.name} discovered {NLGUtils.article(str(obj))} {obj}!")
    return StoryFragment(f"Someone discovered {NLGUtils.article(str(obj))} {obj}!")


@REGISTRY.kernel("Lesson")
def kernel_lesson(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """A lesson is learned."""
    chars = [a for a in args if isinstance(a, Character)]
    lesson_content = args[0] if args and not isinstance(args[0], Character) else kwargs.get('content', 'something important')
    
    if chars:
        return StoryFragment(f"{chars[0].name} learned about {_to_phrase(lesson_content)}.")
    return StoryFragment(f"The lesson was about {_to_phrase(lesson_content)}.")


# --- Setting/Context Kernels ---
@REGISTRY.kernel("Lived")
def kernel_lived(ctx: StoryContext, character: Character, *args, **kwargs) -> StoryFragment:
    """Establish where character lives."""
    place = kwargs.get('location') or kwargs.get('place', 'a nice home')
    adj = kwargs.get('adj', '')
    others = kwargs.get('with', '')
    
    place_phrase = f"{adj} {place}".strip() if adj else place
    with_phrase = f" with {others}" if others else ""
    
    return StoryFragment(f"{character.name} lived in {NLGUtils.article(place_phrase)} {place_phrase}{with_phrase}.")


# --- Resolution Kernels ---
@REGISTRY.kernel("HappyEnd", templates=["And they lived happily ever after."])
def kernel_happy_end(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Happy ending."""
    return StoryFragment("And they all lived happily ever after.")


@REGISTRY.kernel("HappilyEverAfter")
def kernel_happily_ever_after(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Happy ending variant."""
    return StoryFragment("And they all lived happily ever after.")


# --- Additional Common Kernels ---
@REGISTRY.kernel("Accident")
def kernel_accident(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """An accident happens."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    process = kwargs.get('process', '')
    
    char = chars[0] if chars else None
    thing = objects[0] if objects else ''
    
    if char:
        char.Fear += 10
        if process:
            return StoryFragment(f"Oh no! {char.name} had an accident - {_to_phrase(process)}.")
        if thing:
            return StoryFragment(f"Oh no! {char.name} {NLGUtils.past_tense(thing)}.")
        return StoryFragment(f"Oh no! {char.name} had an accident.")
    
    # No character - used as concept/event
    if thing:
        # thing is probably a verb like "fall" -> "someone fell"
        return StoryFragment(f"someone {NLGUtils.past_tense(thing)}", kernel_name="Accident")
    return StoryFragment("an accident happened", kernel_name="Accident")


@REGISTRY.kernel("Wonder")
def kernel_wonder(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character wonders about something."""
    chars = [a for a in args if isinstance(a, Character)]
    char = chars[0] if chars else None
    
    if char:
        char.Joy += 5
        return StoryFragment(f"{char.name} was filled with wonder.")
    # No character - used as state/process
    return StoryFragment("wondered at it all", kernel_name="Wonder")


@REGISTRY.kernel("Desire")
def kernel_desire(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character wants something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    obj = kwargs.get('object') or (objects[0] if objects else 'something')
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        return StoryFragment(f"{char.name} really wanted {_to_phrase(obj)}.")
    return StoryFragment(f"Someone wanted {_to_phrase(obj)}.")


@REGISTRY.kernel("Longing")
def kernel_longing(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character longs for something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = chars[0] if chars else ctx.current_focus
    obj = objects[0] if objects else "something more"
    
    if char:
        char.Sadness += 5
        return StoryFragment(f"{char.name} longed for {_to_phrase(obj)}.")
    return StoryFragment(f"There was a longing for {_to_phrase(obj)}.")


@REGISTRY.kernel("Hug")
def kernel_hug(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters hug."""
    chars = [a for a in args if isinstance(a, Character)]
    
    for c in chars:
        c.Love += 10
        c.Joy += 5
    
    if len(chars) >= 2:
        return StoryFragment(f"{chars[0].name} gave {chars[1].name} a big hug.")
    elif chars:
        return StoryFragment(f"{chars[0].name} got a warm hug.")
    return StoryFragment("There were hugs all around.")


@REGISTRY.kernel("Thank")
def kernel_thank(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character thanks another."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        chars[1].Love += 5
        return StoryFragment(f"{chars[0].name} thanked {chars[1].name}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} said thank you.")
    return StoryFragment("Everyone was grateful.")


@REGISTRY.kernel("Comfort")
def kernel_comfort(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character comforts another."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        chars[1].Sadness -= 10
        chars[1].Joy += 5
        return StoryFragment(f"{chars[0].name} comforted {chars[1].name}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} was comforted.")
    return StoryFragment("There was comfort.")


@REGISTRY.kernel("Proud")
def kernel_proud(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character feels proud."""
    chars = [a for a in args if isinstance(a, Character)]
    
    for c in chars:
        c.Joy += 10
    
    if chars:
        return StoryFragment(f"{chars[0].name} felt very proud.")
    return StoryFragment("There was a feeling of pride.")


@REGISTRY.kernel("Pride")
def kernel_pride(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character feels pride."""
    return kernel_proud(ctx, *args, **kwargs)


@REGISTRY.kernel("Brave")
def kernel_brave(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is brave."""
    chars = [a for a in args if isinstance(a, Character)]
    
    for c in chars:
        c.Fear -= 10
        c.Joy += 5
    
    if chars:
        return StoryFragment(f"{chars[0].name} was very brave.")
    return StoryFragment("Someone was very brave.")


@REGISTRY.kernel("Careful")
def kernel_careful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is careful."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was careful.")
    return StoryFragment("Everyone was careful.")


@REGISTRY.kernel("Rescue")
def kernel_rescue(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Someone is rescued."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        chars[1].Fear -= 15
        chars[1].Joy += 10
        return StoryFragment(f"{chars[0].name} rescued {chars[1].name}!")
    elif chars:
        return StoryFragment(f"{chars[0].name} was rescued!")
    
    catalyst = kwargs.get('catalyst', '')
    process = kwargs.get('process', '')
    outcome = kwargs.get('outcome', '')
    
    parts = []
    if catalyst:
        parts.append(_to_phrase(catalyst))
    if process:
        parts.append(_to_phrase(process))
    if outcome:
        parts.append(_to_phrase(outcome))
    
    if parts:
        return StoryFragment("Someone came to the rescue! " + " ".join(parts))
    return StoryFragment("Someone came to the rescue!")


@REGISTRY.kernel("Conflict")
def kernel_conflict(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Conflict between characters - disagreement, fight, or struggle."""
    chars = [a for a in args if isinstance(a, Character)]
    cause = kwargs.get('cause', '')
    
    # Update emotional states
    for c in chars:
        c.Anger += 10
        c.Joy -= 5
    
    if len(chars) >= 2:
        if cause:
            cause_text = _to_phrase(cause)
            return StoryFragment(f"{chars[0].name} and {chars[1].name} had a conflict over the {cause_text}.")
        return StoryFragment(f"{chars[0].name} and {chars[1].name} got into a fight.")
    elif chars:
        if cause:
            return StoryFragment(f"{chars[0].name} had trouble because of {_to_phrase(cause)}.")
        return StoryFragment(f"There was trouble for {chars[0].name}.")
    
    # No character - check for keyword args describing the conflict
    chase = kwargs.get('chase', '')
    refusal = kwargs.get('refusal', '')
    demand = kwargs.get('demand', '')
    
    parts = []
    if chase:
        parts.append(_to_phrase(chase))
    if refusal:
        parts.append(_to_phrase(refusal))
    if demand:
        parts.append(_to_phrase(demand))
    
    if parts:
        return StoryFragment("There was conflict: " + " and ".join(parts) + ".")
    
    return StoryFragment("there was conflict", kernel_name="Conflict")


@REGISTRY.kernel("Warn")
def kernel_warn(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character warns about danger."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = chars[0] if chars else ctx.current_focus
    danger = objects[0] if objects else "danger"
    
    if char:
        return StoryFragment(f"{char.name} warned everyone about the {danger}!")
    return StoryFragment(f"There was a warning about {danger}!")


@REGISTRY.kernel("Hide")
def kernel_hide(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters hide."""
    chars = [a for a in args if isinstance(a, Character)]
    
    for c in chars:
        c.Fear += 5
    
    if chars:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} hid.")
    return StoryFragment("Everyone hid.")


@REGISTRY.kernel("Wait")
def kernel_wait(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character waits."""
    chars = [a for a in args if isinstance(a, Character)]
    until = kwargs.get('until', '')
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        if until:
            return StoryFragment(f"{char.name} waited patiently until {_to_phrase(until)}.")
        return StoryFragment(f"{char.name} waited patiently.")
    return StoryFragment("They waited.")


@REGISTRY.kernel("Return")
def kernel_return(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character returns somewhere."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    location = kwargs.get('location') or kwargs.get('to', '')
    
    char = chars[0] if chars else ctx.current_focus
    dest = location or (objects[0] if objects else 'home')
    
    if char:
        return StoryFragment(f"{char.name} went back to {dest}.")
    return StoryFragment(f"They returned to {dest}.")


@REGISTRY.kernel("Pick")
def kernel_pick(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character picks something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    obj = objects[0] if objects else 'something'
    
    if char:
        return StoryFragment(f"{char.name} picked some {obj}.")
    return StoryFragment(f"They picked some {obj}.")


@REGISTRY.kernel("Chase")
def kernel_chase(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character chases another."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    chaser = chars[0] if chars else ctx.current_focus
    target = chars[1] if len(chars) > 1 else (objects[0] if objects else 'something')
    
    if chaser:
        return StoryFragment(f"{chaser.name} chased the {target}.")
    return StoryFragment(f"They chased the {target}.")


@REGISTRY.kernel("Whistle")
def kernel_whistle(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character whistles."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    modifier = objects[0] if objects else ''
    
    if char:
        mod_text = f" very {modifier}" if modifier else ""
        return StoryFragment(f"{char.name} whistled{mod_text}.")
    return StoryFragment("Someone whistled.")


@REGISTRY.kernel("Feed")
def kernel_feed(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character feeds another."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        return StoryFragment(f"{chars[0].name} fed {chars[1].name}.")
    elif chars and objects:
        return StoryFragment(f"{chars[0].name} fed the {objects[0]}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} fed it.")
    # No character - used as concept
    return StoryFragment("fed", kernel_name="Feed")


@REGISTRY.kernel("Love")
def kernel_love(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character loves something/someone."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else None
    target = chars[1].name if len(chars) > 1 else (objects[0] if objects else 'it')
    
    if char:
        char.Love += 15
        return StoryFragment(f"{char.name} loved {target}.")
    # No character - used as concept
    if objects:
        return StoryFragment(f"loved {objects[0]}", kernel_name="Love")
    return StoryFragment("loved", kernel_name="Love")


@REGISTRY.kernel("Reassure")
def kernel_reassure(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character reassures another."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        chars[1].Fear -= 10
        return StoryFragment(f"{chars[0].name} reassured {chars[1].name} that everything would be okay.")
    elif chars:
        return StoryFragment(f"{chars[0].name} was reassured.")
    # No character - used as event
    return StoryFragment("someone was reassured", kernel_name="Reassure")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _to_phrase(value) -> str:
    """Convert various types to natural language phrase."""
    if isinstance(value, StoryFragment):
        text = value.text
        # Remove trailing period for embedding in sentences
        return text.rstrip('.!?')
    if isinstance(value, Character):
        return value.name
    if isinstance(value, str):
        # Handle kernel-like strings (CamelCase -> words)
        phrase = re.sub(r'([a-z])([A-Z])', r'\1 \2', value)
        # Handle snake_case
        phrase = phrase.replace('_', ' ')
        return phrase.lower()
    if isinstance(value, (list, tuple)):
        return NLGUtils.join_list([_to_phrase(v) for v in value])
    if value is None:
        return ""
    return str(value).lower()


# Mapping of kernel names to state descriptions
STATE_MAPPINGS = {
    'routine': 'going about the day',
    'happy': 'happy',
    'sad': 'sad',
    'scared': 'scared',
    'curious': 'curious',
    'lonely': 'lonely',
    'excited': 'excited',
    'tired': 'tired',
    'hungry': 'hungry',
    'playful': 'feeling playful',
    'joy': 'joyful',
    'fear': 'afraid',
    'longing': 'longing for something',
}


# Mapping of kernel names to action descriptions
ACTION_MAPPINGS = {
    'play': 'played',
    'run': 'ran',
    'walk': 'walked',
    'find': 'found something',
    'see': 'saw something',
    'discover': 'discovered something',
    'help': 'helped',
    'share': 'shared',
    'laugh': 'laughed',
    'cry': 'cried',
    'wait': 'waited patiently',
    'wonder': 'wondered',
    'joy': 'felt joyful',
    'fear': 'felt scared',
}


def _state_to_phrase(value) -> str:
    """Convert a state value to a descriptive phrase."""
    if isinstance(value, StoryFragment):
        text = value.text.rstrip('.!?').lower()
        # Check if it's a kernel-generated sentence, extract the state
        if ' was ' in text:
            return text.split(' was ')[-1]
        # Check for composed phrases like "going about and playing"
        words = text.split()
        if words:
            # Remove character name if present at start
            if words[0][0].isupper() if words[0] else False:
                words = words[1:]
            return ' '.join(words)
        return text
    
    if isinstance(value, str):
        key = value.lower().replace('_', ' ')
        key = re.sub(r'([a-z])([A-Z])', r'\1 \2', key).lower()
        # Handle composed values like "routine and play"
        parts = key.split(' and ')
        mapped_parts = []
        for part in parts:
            part = part.strip()
            if part in STATE_MAPPINGS:
                mapped_parts.append(STATE_MAPPINGS[part])
            elif part in ACTION_MAPPINGS:
                mapped_parts.append(ACTION_MAPPINGS[part].replace('ed', 'ing'))  # playing instead of played
            else:
                mapped_parts.append(part)
        return ' and '.join(mapped_parts)
    
    return _to_phrase(value)


def _event_to_phrase(value) -> str:
    """Convert an event/catalyst to a phrase."""
    if isinstance(value, StoryFragment):
        text = value.text.rstrip('.!?')
        # Make it flow as an event
        if text.startswith('There was '):
            text = text[10:]  # Remove "There was "
        return text
    
    if isinstance(value, str):
        phrase = re.sub(r'([a-z])([A-Z])', r'\1 \2', value).lower()
        return f"something {phrase} happened"
    
    return _to_phrase(value)


def _action_to_phrase(value) -> str:
    """Convert an action/process to a verb phrase."""
    if isinstance(value, StoryFragment):
        text = value.text.rstrip('.!?')
        # Extract action from sentences like "X did Y"
        words = text.split()
        if len(words) >= 2:
            # If it starts with a name, get the rest
            if words[0] and words[0][0].isupper():
                return ' '.join(words[1:])
            return text
        return text
    
    if isinstance(value, str):
        key = value.lower()
        key = re.sub(r'([a-z])([A-Z])', r'\1 \2', key).lower()
        
        # Handle composed values like "wonder and joy"
        parts = key.split(' and ')
        result_parts = []
        for part in parts:
            part = part.strip()
            if part in ACTION_MAPPINGS:
                result_parts.append(ACTION_MAPPINGS[part])
            else:
                # Convert to past tense
                words = part.split()
                if words:
                    result_parts.append(NLGUtils.past_tense(words[0]) + (' ' + ' '.join(words[1:]) if len(words) > 1 else ''))
        return ' and '.join(result_parts) if result_parts else key
    
    return _to_phrase(value)


# =============================================================================
# AST EXECUTOR
# =============================================================================

class KernelExecutor:
    """Execute story kernels by interpreting Python AST."""
    
    def __init__(self, registry: KernelRegistry = None):
        self.registry = registry or REGISTRY
        self.ctx = StoryContext()
    
    def execute(self, kernel_str: str) -> str:
        """Execute a kernel string and return generated story."""
        # Reset context
        self.ctx = StoryContext()
        
        # Parse AST
        try:
            tree = ast.parse(kernel_str)
        except SyntaxError as e:
            return f"[Parse error: {e}]"
        
        # Execute each statement
        for stmt in tree.body:
            if isinstance(stmt, ast.Expr):
                result = self._eval_node(stmt.value)
                if result and isinstance(result, StoryFragment) and result.text:
                    self.ctx.emit(result.text, result.weight, result.kernel_name)
        
        return self.ctx.render()
    
    def _eval_node(self, node: ast.AST) -> Any:
        """Evaluate an AST node."""
        
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            
            if isinstance(node.op, ast.Add):
                # Composition: combine fragments
                return self._compose(left, right)
            elif isinstance(node.op, ast.Div):
                # Attention dilution
                if isinstance(left, StoryFragment) and isinstance(right, (int, float)):
                    return StoryFragment(left.text, left.weight / right)
                return left
        
        elif isinstance(node, ast.Name):
            # Variable reference - could be character or concept
            name = node.id
            if name in self.ctx.characters:
                return self.ctx.characters[name]
            # Return as concept string
            return name
        
        elif isinstance(node, ast.Constant):
            return node.value
        
        elif isinstance(node, ast.List):
            return [self._eval_node(el) for el in node.elts]
        
        elif isinstance(node, ast.Subscript):
            # Handle indexing (e.g., items[0])
            value = self._eval_node(node.value)
            if isinstance(value, list):
                idx = self._eval_node(node.slice)
                if isinstance(idx, int) and 0 <= idx < len(value):
                    return value[idx]
            return value
        
        return None
    
    def _eval_call(self, node: ast.Call) -> Any:
        """Evaluate a function call."""
        if not isinstance(node.func, ast.Name):
            return None
        
        func_name = node.func.id
        
        # Evaluate arguments
        args = [self._eval_node(arg) for arg in node.args]
        kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}
        
        # Check for Character definition: Name(Character, type, traits)
        if args and args[0] == 'Character':
            # Parse type and traits - could be 1 or 2 additional args
            char_type = "character"
            traits = []
            
            if len(args) > 1:
                # Check if second arg looks like a type (lowercase common nouns) or traits
                second = str(args[1])
                common_types = {'girl', 'boy', 'man', 'woman', 'dog', 'cat', 'bird', 'fish',
                               'rabbit', 'bunny', 'bear', 'lion', 'mouse', 'frog', 'duck',
                               'mother', 'father', 'mom', 'dad', 'grandma', 'grandpa',
                               'friend', 'teacher', 'farmer', 'king', 'queen', 'princess', 'prince'}
                
                if '+' in second:
                    # It's traits, no type specified
                    traits = self._parse_traits(second)
                elif second.lower() in common_types:
                    char_type = second.lower()
                    if len(args) > 2:
                        traits = self._parse_traits(args[2])
                else:
                    # Treat as a single trait/descriptor, use it as adjective
                    traits = [second.lower()]
                    if len(args) > 2:
                        traits.extend(self._parse_traits(args[2]))
            
            # Use different intro template for first vs subsequent characters
            is_first = len(self.ctx.characters) == 0
            
            char = self.ctx.add_character(func_name, str(char_type), traits)
            self.ctx.current_focus = char
            
            # Generate intro
            adj = NLGUtils.join_list(traits[:2]) if traits else ""
            
            template_category = 'intro_first' if is_first else 'intro'
            intro = self.registry.templates.generate(template_category,
                name=func_name,
                type=char_type,
                adj=adj,
                article=NLGUtils.article(adj.split()[0] if adj else str(char_type))
            )
            return StoryFragment(intro, kernel_name="Character")
        
        # Lookup and execute kernel
        if func_name in self.registry:
            kernel_func = self.registry.get(func_name)
            try:
                result = kernel_func(self.ctx, *args, **kwargs)
                if isinstance(result, StoryFragment):
                    return result
                elif isinstance(result, str):
                    return StoryFragment(result, kernel_name=func_name)
            except Exception as e:
                # Fallback: generate generic text
                return self._fallback_kernel(func_name, args, kwargs)
        else:
            # Unknown kernel - generate fallback
            return self._fallback_kernel(func_name, args, kwargs)
    
    def _fallback_kernel(self, name: str, args: list, kwargs: dict) -> StoryFragment:
        """Generate fallback text for unknown kernels."""
        # Convert CamelCase to sentence
        phrase = re.sub(r'([a-z])([A-Z])', r'\1 \2', name).lower()
        
        # Find character in args
        chars = [a for a in args if isinstance(a, Character)]
        fragments = [a for a in args if isinstance(a, StoryFragment)]
        objects = [str(a) for a in args if not isinstance(a, (Character, StoryFragment)) and a is not None]
        
        if chars:
            char = chars[0]
            verb = NLGUtils.past_tense(phrase.split()[0])
            rest = ' '.join(phrase.split()[1:])
            
            # Add objects if present
            if objects:
                obj_text = NLGUtils.join_list(objects)
                return StoryFragment(f"{char.name} {verb} {rest} {obj_text}".strip() + ".", kernel_name=name)
            if rest:
                return StoryFragment(f"{char.name} {verb} {rest}.", kernel_name=name)
            return StoryFragment(f"{char.name} {verb}.", kernel_name=name)
        
        # Handle fragments from nested calls
        if fragments:
            frag_texts = [_to_phrase(f) for f in fragments]
            return StoryFragment(f"There was {phrase}: " + NLGUtils.join_list(frag_texts) + ".", kernel_name=name)
        
        # Handle objects without character
        if objects:
            return StoryFragment(f"There was {phrase} with {NLGUtils.join_list(objects)}.", kernel_name=name)
        
        # No character - passive/general statement
        return StoryFragment(f"There was {phrase}.", kernel_name=name)
    
    def _compose(self, left: Any, right: Any) -> StoryFragment:
        """Compose two values with + operator."""
        left_text = _to_phrase(left) if left else ""
        right_text = _to_phrase(right) if right else ""
        
        # Combine intelligently
        if left_text and right_text:
            # For concepts/states, use "and"
            combined = f"{left_text} and {right_text}"
            return StoryFragment(combined)
        
        return StoryFragment(left_text or right_text)
    
    def _parse_traits(self, traits_value) -> List[str]:
        """Parse traits from various formats."""
        if isinstance(traits_value, str):
            # Handle "Curious+Hopeful" format
            return [t.strip().lower() for t in traits_value.replace('+', ',').split(',')]
        elif isinstance(traits_value, list):
            return [str(t).lower() for t in traits_value]
        return []


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def generate_story(kernel: str) -> str:
    """Generate a story from a kernel string."""
    executor = KernelExecutor(REGISTRY)
    return executor.execute(kernel)


# =============================================================================
# TEST & EXAMPLES
# =============================================================================

if __name__ == "__main__":
    # Test kernels from the clustering results
    
    test_kernels = [
        # Simple character intro
        '''
Lily(Character, girl, Curious+Hopeful)
''',
        
        # Journey pattern
        '''
Lily(Character, girl, Curious+Hopeful)
Journey(Lily,
    state=Routine,
    catalyst=Discovery(rainbow),
    process=Wonder+Joy,
    insight=Unexpected(beauty),
    transformation=Happy)
''',
        
        # Friendship pattern
        '''
Tim(Character, boy, Playful)
Sam(Character, dog, Loyal)
Friendship(Tim, Sam,
    state=Routine+Play,
    catalyst=Encounter(park),
    transformation=Happy)
''',

        # From cluster 65
        '''
Lily(Character, girl, Friendly+Playful)
Mittens(Character, cat, Furry)
Timmy(Character, boy, Polite)
Play(Lily, Mittens, Timmy)
Joy(Lily)
Friendship(Lily, Timmy)
''',

        # Cautionary tale
        '''
Tim(Character, boy, Curious)
Mom(Character, mother, Caring)
Cautionary(Tim,
    state=Play(ball),
    event=Accident(fall),
    consequence=Sadness+Cry,
    lesson=Careful)
''',

        # More complex - from cluster representatives
        '''
Sally(Character, girl, Patient+Curious)
Mommy(Character, mother, Caring)
Routine(Sally)
Discovery(Sally, box)
Joy(Sally)
Happy(Sally)
''',
    ]
    
    # Real kernels from clustering results (1.5m.md)
    real_kernels = [
        # From Cluster 65
        '''
Lily(Character, girl, Friendly+Playful)
Mittens(Character, cat, Furry)
Timmy(Character, boy, Polite)
Play(Lily, Mittens, Timmy)
Joy(Lily)
Friendship(Lily, Timmy)
''',
        
        # From Cluster 80
        '''
Timmy(Character, boy, Curious+Fearful)
Farmer(Character, Reassuring)
Bull(Character, big+Friendly)
Journey(Timmy,
    state=Routine+Fear(Bull),
    catalyst=Reassure,
    process=Feed(Timmy, Bull)+Joy(Timmy)+Joy(Bull),
    transformation=Friendship(Timmy, Bull)+Love(Timmy, farm))
''',

        # From Cluster 139
        '''
Lily(Character, Curious+Helpful)
Neighbor(Character, Grateful)
Pick(flowers)
See(truck)
Run(cat)
Chase(Lily, cat)
Return(cat, neighbor)
Joy(neighbor)
''',

        # From Cluster 223
        '''
Lily(Character, girl, Resourceful)
Encounter(Lily, wolf, forest)
Fear(Lily)
Run(Lily)
Whistle(Lily, loud)
Run(wolf)
''',
    ]
    
    print("=" * 70)
    print("STORYWEAVERS GENERATION ENGINE - TEST RUN")
    print("=" * 70)
    
    for i, kernel in enumerate(test_kernels, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}")
        print(f"{'='*70}")
        print("KERNEL:")
        print(kernel.strip())
        print("\nGENERATED STORY:")
        story = generate_story(kernel)
        print(story)
        print()
    
    print("\n" + "=" * 70)
    print("TESTING WITH REAL KERNELS FROM DATASET")
    print("=" * 70)
    
    for i, kernel in enumerate(real_kernels, 1):
        print(f"\n{'='*70}")
        print(f"REAL KERNEL {i}")
        print(f"{'='*70}")
        print("KERNEL:")
        print(kernel.strip())
        print("\nGENERATED STORY:")
        story = generate_story(kernel)
        print(story)
        print()

