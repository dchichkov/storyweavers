# Storyweavers Engine Improvements TODO

Engine improvements inspired by interactive fiction systems (Ink, ChoiceScript, Inform 7, Twine, TADS).

---

## Current Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Kernel String  │────▶│  KernelExecutor  │────▶│  StoryFragment  │
│  (Python AST)   │     │   _eval_node()   │     │  text + weight  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                         │
                    ┌──────────┼──────────┐              │
                    ▼          ▼          ▼              ▼
              ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐
              │ REGISTRY │ │ Context │ │ Template │ │ render()│
              │ kernels  │ │ chars   │ │ Engine   │ │ → text  │
              └──────────┘ └─────────┘ └──────────┘ └─────────┘
```

### Architectural Strengths (What's Working)

1. **Clean AST-based execution**: Kernels are valid Python, parsed once, executed compositionally
2. **Centralized state**: `StoryContext` holds all mutable state (characters, focus, objects)
3. **Separation of concerns**: Kernels produce `StoryFragment`, templates handle surface text
4. **Character emotions**: Already tracked (`Joy`, `Fear`, `Love`, `Anger`, `Sadness`)
5. **Extensible registry**: New kernels added via `@REGISTRY.kernel()` decorator

### Architectural Gaps (What's Missing)

| Gap | Current State | IF Systems Have |
|-----|---------------|-----------------|
| **Story Phase** | None | Ink weaves, Twine passages |
| **Location** | `current_object` only | Inform 7 rooms, TADS scope |
| **Transitions** | Hardcoded "But then," | Ink glue, smart connectors |
| **Pronoun tracking** | Names repeated | Inform 7 auto-pronouns |
| **Scene structure** | Single paragraph | Twine passages, breaks |
| **Template variety** | 1-2 per kernel | Should be 5+ |
| **Emotion → text** | Emotions tracked but unused | ChoiceScript state-modified text |

### Fundamental Problem: Direct Interpretation

The current architecture directly interprets the AST, which means each kernel must independently handle:
- Pronoun decisions (can't see other references)
- Transition insertion (can't see story structure)
- Prerequisite checking (can't see what came before)
- Coherence (logic scattered across 800+ kernels)

---

## Simplified Approach: AST → AST Transforms

**Before implementing full IR, try AST-to-AST rewriting.** This is simpler: walk the AST, add/modify nodes, then execute the transformed AST with the existing interpreter.

### Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐
│ Kernel AST  │───▶│ AST Passes  │───▶│ Transformed │───▶│ Execute  │
│ (raw input) │    │ (rewrite)   │    │    AST      │    │  → Text  │
└─────────────┘    └─────────────┘    └─────────────┘    └──────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         Pronouns   Transitions  Prerequisites
```

### How It Works

The AST is valid Python - we can walk it, analyze it, and **inject new keyword arguments** before execution.

**Original AST:**
```python
Story(
    protagonist=Tim(Character, Curious),
    conflict=Fear(Tim, dog),
    resolution=Brave(Tim)
)
```

**After AST transform:**
```python
Story(
    protagonist=Tim(Character, Curious),
    _transition="One day",           # INJECTED
    conflict=Fear(Tim, dog),
    _use_pronoun=Tim,                # INJECTED: next ref to Tim uses "he"
    _transition="But then",          # INJECTED  
    resolution=Brave(Tim, _despite="fear")  # INJECTED: context from Fear
)
```

### Implementation

```python
import ast

class StoryASTTransformer(ast.NodeTransformer):
    """Transform story AST before execution."""
    
    def __init__(self):
        self.seen_characters = {}      # name → Character info
        self.seen_kernels = []         # list of kernel names in order
        self.last_subject = None       # for pronoun decisions
        self.current_phase = "setup"
    
    def visit_Call(self, node: ast.Call) -> ast.Call:
        """Visit each kernel call, potentially adding kwargs."""
        kernel_name = node.func.id if isinstance(node.func, ast.Name) else None
        
        if kernel_name:
            # Track what we've seen
            self.seen_kernels.append(kernel_name)
            
            # Apply transforms
            node = self._add_pronoun_hint(node, kernel_name)
            node = self._add_transition(node, kernel_name)
            node = self._add_prerequisite_context(node, kernel_name)
        
        # Recurse into children
        self.generic_visit(node)
        return node
    
    def _add_pronoun_hint(self, node: ast.Call, kernel_name: str) -> ast.Call:
        """Add _use_pronoun=True if subject was just mentioned."""
        # Extract first arg if it's a character reference
        if node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Name):
                char_name = first_arg.id
                if char_name == self.last_subject:
                    # Same character → inject pronoun hint
                    node.keywords.append(
                        ast.keyword(arg='_use_pronoun', value=ast.Constant(True))
                    )
                self.last_subject = char_name
        return node
    
    def _add_transition(self, node: ast.Call, kernel_name: str) -> ast.Call:
        """Add _transition for phase changes."""
        phase_starters = {'Fear': 'rising', 'Danger': 'rising', 
                         'Brave': 'climax', 'Victory': 'climax',
                         'Resolution': 'resolution', 'Moral': 'resolution'}
        
        if kernel_name in phase_starters:
            new_phase = phase_starters[kernel_name]
            if new_phase != self.current_phase:
                transitions = {
                    ('setup', 'rising'): "But one day, ",
                    ('rising', 'climax'): "Then, ",
                    ('climax', 'resolution'): "After that, ",
                }
                key = (self.current_phase, new_phase)
                if key in transitions:
                    node.keywords.append(
                        ast.keyword(arg='_transition', 
                                   value=ast.Constant(transitions[key]))
                    )
                self.current_phase = new_phase
        return node
    
    def _add_prerequisite_context(self, node: ast.Call, kernel_name: str) -> ast.Call:
        """Add _context for prerequisite-aware generation."""
        prerequisites = {
            'Brave': ['Fear', 'Scared', 'Danger'],
            'Rescue': ['Danger', 'Fall', 'Accident'],
            'Forgiveness': ['Conflict', 'Anger', 'Apology'],
        }
        
        if kernel_name in prerequisites:
            prereqs = prerequisites[kernel_name]
            matched = [p for p in prereqs if p in self.seen_kernels]
            if matched:
                # Inject the prerequisite context
                node.keywords.append(
                    ast.keyword(arg='_despite', 
                               value=ast.Constant(matched[0].lower()))
                )
        return node


def transform_story_ast(source: str) -> str:
    """Transform story kernel source, return modified source."""
    tree = ast.parse(source, mode='eval')
    transformer = StoryASTTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    return ast.unparse(new_tree)
```

### Kernels Use Injected Kwargs

Kernels check for the injected `_` prefixed kwargs:

```python
@REGISTRY.kernel("Brave")
def kernel_brave(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    char = _get_character(args, ctx)
    
    # Check for injected hints
    use_pronoun = kwargs.get('_use_pronoun', False)
    transition = kwargs.get('_transition', '')
    despite = kwargs.get('_despite', '')
    
    # Use pronoun if hinted
    subject = char.he if use_pronoun else char.name
    
    # Build text with context
    if despite:
        text = f"Despite {char.pronoun_his} {despite}, {subject} was brave."
    else:
        text = f"{subject} was brave."
    
    if transition:
        text = transition + text
    
    return StoryFragment(text)
```

### Example Transform

**Input:**
```
Story(protagonist=Tim(Character, Curious), conflict=Fear(Tim, dog), resolution=Brave(Tim))
```

**After `StoryASTTransformer`:**
```
Story(protagonist=Tim(Character, Curious), conflict=Fear(Tim, dog, _transition='But one day, '), resolution=Brave(Tim, _use_pronoun=True, _transition='Then, ', _despite='fear'))
```

**Generated text:**
```
Tim was curious. But one day, Tim was scared of the dog. Then, despite his fear, he was brave.
```

vs. current output:
```
Tim was curious. Tim was scared of the dog. Tim was brave.
```

### Advantages Over Full IR

| Aspect | AST → AST | Full IR |
|--------|-----------|---------|
| **Implementation** | ~100 lines | ~500+ lines |
| **Testing** | Can print transformed AST | Need IR pretty-printer |
| **Compatibility** | Works with existing executor | Needs new executor |
| **Incremental** | Add one pass at a time | All-or-nothing |
| **Debugging** | `ast.unparse()` to see result | Custom tooling needed |

### Limitations

- Less structured than full IR (still just AST nodes)
- Passes can't easily share state (need to re-walk)
- Complex multi-kernel patterns harder to express
- No typed schema for annotations

### When to Graduate to Full IR

Upgrade to full IR when:
1. AST transforms get too complex (>5 passes)
2. Need rich inter-kernel relationships
3. Want to serialize/cache the IR
4. Need constraint validation before execution

### Implementation Path

1. **Create `StoryASTTransformer` class** (~50 lines)
2. **Add pronoun pass** - track subjects, inject `_use_pronoun`
3. **Add transition pass** - detect phases, inject `_transition`
4. **Add prerequisite pass** - track kernels, inject `_despite` etc.
5. **Update key kernels** - Check for `_` kwargs
6. **Test with sample.py** - Compare before/after

---

## MLIR-Style Compiler Pipeline (Full IR Approach)

Instead of direct interpretation, adopt a **compiler pipeline** with intermediate representation (IR) and optimization passes:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐
│ Kernel AST  │───▶│   StoryIR   │───▶│ Optimization│───▶│  Annotated  │───▶│  Execute │
│ (raw input) │    │ (structured)│    │   Passes    │    │     IR      │    │  → Text  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └──────────┘
                          │                  │
                   ┌──────┴──────┐    ┌──────┴──────┐
                   │ Flatten     │    │ Pronouns    │
                   │ Scope chars │    │ Transitions │
                   │ Track locs  │    │ Prerequisites│
                   └─────────────┘    │ Coherence   │
                                      └─────────────┘
```

### Why This Is Better

| Concern | Current (Interpreter) | Proposed (Compiler) |
|---------|----------------------|---------------------|
| **Pronouns** | Each kernel checks `ctx.fragments[-1]` | Pronoun pass sees ALL refs, decides globally |
| **Transitions** | Kernels hardcode "But then" | Transition pass sees structure, inserts smartly |
| **Prerequisites** | Nothing enforces Fear→Brave | Prerequisite pass annotates `Brave(despite=Fear)` |
| **Coherence** | Logic in 800 kernels | Centralized in optimization passes |

### Proposed IR: StoryIR

```python
@dataclass
class StoryIR:
    """Intermediate representation of a story, before text generation."""
    
    # Extracted from AST parsing
    characters: Dict[str, CharacterIR]    # All characters with traits, emotions
    scenes: List[SceneIR]                  # Story broken into scenes/beats
    locations: List[str]                   # Settings mentioned
    
    # Added by optimization passes
    pronoun_map: Dict[int, str]           # sentence_idx → "he"/"she"/"they"/name
    transitions: Dict[int, str]            # scene_idx → "But then,"
    prerequisites_satisfied: bool          # Constraint check passed
    
@dataclass
class SceneIR:
    """A scene/beat in the story."""
    phase: str                            # setup, rising, climax, falling, resolution
    kernels: List[KernelIR]               # Kernels in this scene
    location: Optional[str]
    mood: str = "neutral"
    
@dataclass
class KernelIR:
    """A single kernel call, annotated."""
    name: str                             # "Brave", "Fear", etc.
    args: List[Any]                       # Positional args
    kwargs: Dict[str, Any]                # Keyword args
    
    # Added by passes
    subject_ref: str = ""                 # "Tim" or "he" or "the boy"
    emotion_modifier: str = ""            # "nervously", "despite fear"
    transition_before: str = ""           # "But then, "
    prerequisite_context: List[str] = field(default_factory=list)  # ["Fear"] for Brave
```

### Optimization Passes

#### Pass 1: Lower AST → StoryIR

```python
def lower_to_ir(ast_node) -> StoryIR:
    """Convert raw Python AST to structured StoryIR."""
    ir = StoryIR()
    
    # Walk AST, extract:
    # - Character definitions → ir.characters
    # - Location kernels → ir.locations  
    # - Group by meta-pattern kwargs → ir.scenes
    # - Individual kernels → scene.kernels
    
    return ir
```

#### Pass 2: Prerequisite Check & Annotation

```python
PREREQUISITES = {
    'Brave': ['Fear', 'Danger', 'Scared'],
    'Rescue': ['Danger', 'Accident', 'Fall'],
    'Forgiveness': ['Conflict', 'Apology', 'Anger'],
    'Celebration': ['Victory', 'Achievement'],
}

def prerequisite_pass(ir: StoryIR) -> StoryIR:
    """Check prerequisites, annotate kernels with context."""
    seen_kernels = set()
    
    for scene in ir.scenes:
        for kernel in scene.kernels:
            if kernel.name in PREREQUISITES:
                prereqs = PREREQUISITES[kernel.name]
                matched = [p for p in prereqs if p in seen_kernels]
                if matched:
                    kernel.prerequisite_context = matched
                    # Brave after Fear → Brave(despite=Fear)
                    kernel.emotion_modifier = f"despite {matched[0].lower()}"
            seen_kernels.add(kernel.name)
    
    return ir
```

#### Pass 3: Pronoun Resolution

```python
def pronoun_pass(ir: StoryIR) -> StoryIR:
    """Globally resolve when to use names vs pronouns."""
    last_subject = None
    sentences_since_name = 0
    
    for scene in ir.scenes:
        for kernel in scene.kernels:
            char = kernel.args[0] if kernel.args else None
            
            if char and isinstance(char, CharacterIR):
                if (last_subject == char.name and 
                    sentences_since_name < 2):
                    # Same character, recently named → pronoun
                    kernel.subject_ref = char.pronoun  # "he"/"she"
                else:
                    # Different character or too long → use name
                    kernel.subject_ref = char.name
                    sentences_since_name = 0
                
                last_subject = char.name
                sentences_since_name += 1
        
        # Reset at scene boundary
        sentences_since_name = 0
    
    return ir
```

#### Pass 4: Transition Insertion

```python
PHASE_TRANSITIONS = {
    ('setup', 'rising'): ["One day, ", "But then, ", "Suddenly, "],
    ('rising', 'climax'): ["The moment came. ", "It was then that "],
    ('climax', 'resolution'): ["After that, ", "Finally, "],
}

def transition_pass(ir: StoryIR) -> StoryIR:
    """Insert transitions between scenes/phases."""
    prev_phase = None
    
    for scene in ir.scenes:
        if prev_phase and prev_phase != scene.phase:
            key = (prev_phase, scene.phase)
            if key in PHASE_TRANSITIONS:
                scene.kernels[0].transition_before = random.choice(
                    PHASE_TRANSITIONS[key]
                )
        prev_phase = scene.phase
    
    return ir
```

### Execution After Passes

After all passes, kernels have rich annotations:

```python
# Before passes:
KernelIR(name="Brave", args=[Tim])

# After passes:
KernelIR(
    name="Brave", 
    args=[Tim],
    subject_ref="he",                    # Pronoun pass decided
    emotion_modifier="despite his fear", # Prerequisite pass added
    transition_before="But then, ",      # Transition pass added
    prerequisite_context=["Fear"]        # Knows what came before
)
```

Kernel execution becomes simpler:

```python
@REGISTRY.kernel("Brave")
def kernel_brave(ctx, kernel_ir: KernelIR) -> StoryFragment:
    # Annotations already computed by passes!
    subject = kernel_ir.subject_ref  # "he" not "Tim"
    modifier = kernel_ir.emotion_modifier  # "despite his fear"
    transition = kernel_ir.transition_before  # "But then, "
    
    text = f"{transition}{subject.capitalize()} was brave"
    if modifier:
        text = f"{transition}{modifier.capitalize()}, {subject} was brave"
    
    return StoryFragment(text + ".")
```

### World Model Constraints

The IR can also enforce world-model constraints (Inform 7 style):

```python
CONSTRAINTS = {
    'Rescue': lambda ir, kernel: any(
        k.name in ('Danger', 'Fall', 'Accident') 
        for scene in ir.scenes for k in scene.kernels
    ),
    'Fly': lambda ir, kernel: (
        kernel.args[0].char_type in ('bird', 'butterfly', 'fairy')
        if kernel.args else True
    ),
}

def constraint_pass(ir: StoryIR) -> StoryIR:
    """Validate world model constraints, fix or warn."""
    for scene in ir.scenes:
        for kernel in scene.kernels:
            if kernel.name in CONSTRAINTS:
                if not CONSTRAINTS[kernel.name](ir, kernel):
                    # Option 1: Inject prerequisite
                    # Option 2: Make metaphorical
                    # Option 3: Warn in output
                    kernel.constraint_violation = True
    return ir
```

### Implementation Path

| Phase | Work | Impact |
|-------|------|--------|
| **1. Define StoryIR** | Dataclasses for IR | Foundation |
| **2. AST → IR lowering** | Parse existing AST into IR | No output change yet |
| **3. Pronoun pass** | First optimization | Immediate quality boost |
| **4. Transition pass** | Phase-aware connectors | Better flow |
| **5. Prerequisite pass** | Context annotations | Coherence |
| **6. Update kernels** | Use IR annotations | Simpler kernel code |

### Benefits

1. **Kernels become simpler** - just semantic → text, no context checking
2. **Coherence is centralized** - optimization passes, not 800 kernels
3. **Easy to add new passes** - pronoun improvements, style transforms
4. **Testable in isolation** - can unit test each pass
5. **Inspection** - can print IR to debug why output is wrong

### Analogy

| LLVM/MLIR | Storyweavers |
|-----------|--------------|
| Source code | Kernel AST |
| LLVM IR | StoryIR |
| Optimization passes | Pronoun, Transition, Prerequisite passes |
| Target codegen | Text generation via kernels |

---

## Architecture Improvement Roadmap

### Phase 1: StoryContext Enhancements (Foundation)

Add new fields to `StoryContext` (gen5.py line 151):

```python
@dataclass
class StoryContext:
    # Existing fields...
    characters: Dict[str, Character] = field(default_factory=dict)
    fragments: List[StoryFragment] = field(default_factory=list)
    current_focus: Optional[Character] = None
    current_object: Optional[str] = None
    
    # NEW: Phase 1 additions
    story_phase: str = "setup"                    # Priority 1
    previous_phase: str = ""                      # For transition detection
    current_location: str = ""                    # Priority 4
    location_established: bool = False
    
    # NEW: Phase 2 additions  
    last_subject: Optional[Character] = None      # Priority 5
    sentences_since_name: int = 0
    executed_kernels: Set[str] = field(default_factory=set)  # Priority 9
    
    # NEW: Phase 3 additions
    current_scene: str = ""                       # Priority 10
    scene_mood: str = "neutral"
```

### Phase 2: StoryFragment Enhancements

Add metadata to `StoryFragment` (gen5.py line 127):

```python
@dataclass 
class StoryFragment:
    text: str
    weight: float = 1.0
    kernel_name: str = ""
    
    # NEW: Text control
    glue_before: bool = False    # Priority 6: join without space
    glue_after: bool = False
    transition_type: str = "neutral"  # "cause", "contrast", "sequence", "conclusion"
    
    # NEW: Rendering hints
    starts_paragraph: bool = False    # Priority 10: scene breaks
    emotion_context: str = ""         # Priority 3: "fearful", "joyful"
```

### Phase 3: TemplateEngine Enhancements

Add phase-aware and emotion-aware templates (gen5.py line 400):

```python
class TemplateEngine:
    def __init__(self):
        self.templates: Dict[str, List[str]] = defaultdict(list)
        
        # NEW: Transition templates by phase change
        self.transitions: Dict[str, List[str]] = {
            "setup_to_rising": ["One day, ", "But then, ", "Suddenly, "],
            "rising_to_climax": ["The moment came. ", "It was then that "],
            "climax_to_resolution": ["After that, ", "Finally, ", "And so, "],
        }
        
        # NEW: Emotion-modified template categories
        # Instead of just 'joy', have 'joy_fear_high', 'joy_neutral', etc.
```

### Phase 4: KernelExecutor Enhancements

Add tracking and smart composition (gen5.py line 1991):

```python
class KernelExecutor:
    def __init__(self, registry):
        self.registry = registry
        self.ctx = StoryContext()
        
        # NEW: Tracking
        self._executed_kernels: List[str] = []
        self._phase_just_changed: bool = False
    
    def _compose(self, left, right):
        # NEW: Smart joining based on fragment types
        # Instead of always "and", use "while", "then", "but" contextually
```

### Phase 5: Helper Function Additions

Add to gen5.py after line 1793:

```python
def _emotion_adverb(char: Character) -> str:
    """Get adverb based on dominant emotion."""
    if char.Fear > 60: return "nervously"
    if char.Joy > 70: return "happily"
    if char.Sadness > 60: return "sadly"
    if char.Anger > 60: return "angrily"
    return ""

def _get_transition(old_phase: str, new_phase: str) -> str:
    """Get transition phrase for phase change."""
    key = f"{old_phase}_to_{new_phase}"
    transitions = REGISTRY.templates.transitions.get(key, [])
    return random.choice(transitions) if transitions else ""

def _smart_join(left: str, right: str, transition_type: str = "neutral") -> str:
    """Join two text fragments with appropriate connector."""
    connectors = {
        "cause": ["so ", "because of this, ", "as a result, "],
        "contrast": ["but ", "however, ", "yet "],
        "sequence": ["then ", "and then ", "next, "],
        "conclusion": ["finally, ", "in the end, ", "and so "],
        "neutral": [" ", " and ", ". "],
    }
    connector = random.choice(connectors.get(transition_type, connectors["neutral"]))
    return f"{left.rstrip('. ')}{connector}{right}"
```

---

## Feasibility Assessment

| Component | Effort | Risk | Dependencies |
|-----------|--------|------|--------------|
| `StoryContext` fields | Trivial | None | None |
| `StoryFragment` fields | Low | None | Update `_compose()` |
| `TemplateEngine` transitions | Low | None | Phase tracking |
| `KernelExecutor` tracking | Medium | Test carefully | None |
| Helper functions | Low | None | None |
| Update 800+ kernels | High (grunt work) | Low | All above |

### Recommended Implementation Order

1. **Add `StoryContext` fields** (10 min) - No breaking changes
2. **Add `_emotion_adverb()` helper** (5 min) - Immediately usable
3. **Update meta-patterns to set phase** (30 min) - `Journey`, `Cautionary`, `Quest`
4. **Add transition templates** (20 min) - Auto-insert on phase change
5. **Improve `_compose()`** (30 min) - Smarter joining logic
6. **Add template variety** (ongoing) - 5+ templates per kernel

---

## Priority 1: Story Phase Tracking
**Status:** Not started  
**Effort:** Low  
**Impact:** High  

Add phase awareness to `StoryContext` so templates and kernels know where we are in the narrative arc.

```python
@dataclass
class StoryContext:
    story_phase: str = "setup"  # setup, rising_action, climax, falling_action, resolution
    
    def advance_phase(self, new_phase: str):
        self.story_phase = new_phase
```

**Implementation notes:**
- Meta-patterns (`Journey`, `Cautionary`, `Quest`) should advance phases as they process kwargs
- Phase transitions: setup → rising_action (catalyst) → climax (conflict) → falling_action (resolution) → resolution (transformation)
- Templates can be phase-aware: "Once upon a time..." in setup vs "Finally..." in resolution

**Inspired by:** Ink's weave structure for managing narrative flow

---

## Priority 2: Transition Templates
**Status:** Not started  
**Effort:** Medium  
**Impact:** High  

Add transition phrases between story phases to fix choppy narrative flow.

```python
class TemplateEngine:
    def __init__(self):
        self.transitions = {
            "setup_to_rising": [
                "One day, ",
                "But then, ",
                "Suddenly, ",
                "It happened that ",
            ],
            "rising_to_climax": [
                "The moment had come. ",
                "It was then that ",
                "Just when things seemed okay, ",
            ],
            "climax_to_resolution": [
                "After that, ",
                "In the end, ",
                "Finally, ",
                "And so, ",
            ]
        }
```

**Implementation notes:**
- `StoryContext.emit()` could auto-insert transitions when phase changes
- Transition selection should be random for variety
- Could also have fragment-level transitions (cause, contrast, sequence, conclusion)

**Inspired by:** Twine's passage links and natural flow between story segments

---

## Priority 3: Emotion-Modified Templates
**Status:** Not started  
**Effort:** Low  
**Impact:** Medium  

Leverage existing character emotion state (Joy, Fear, Love, Anger, Sadness) to modify generated text.

```python
# In TemplateEngine
self.templates['action_joy_high'] = [
    "{name} happily {action}.",
    "{name} {action}, beaming with joy.",
]
self.templates['action_fear_high'] = [
    "{name} nervously {action}.",
    "{name} {action}, trembling slightly.",
]

# Usage in kernels:
def kernel_action(ctx, char, **kwargs):
    if char.Fear > 60:
        return ctx.templates.generate('action_fear_high', name=char.name, action="did it")
    elif char.Joy > 70:
        return ctx.templates.generate('action_joy_high', name=char.name, action="did it")
    return StoryFragment(f"{char.name} did it.")
```

**Implementation notes:**
- Define emotion thresholds (e.g., >60 = "high")
- Apply to common action kernels first (Run, Walk, See, Find)
- Could add adverb injection as simpler alternative: `"{name} {adverb} {action}."`

**Inspired by:** ChoiceScript's state-modified text output

---

## Priority 4: Location/Setting Persistence
**Status:** Not started  
**Effort:** Low  
**Impact:** Medium  

Track current location so action kernels can reference it naturally.

```python
@dataclass
class StoryContext:
    current_location: str = ""
    location_established: bool = False

# In location kernels:
@REGISTRY.kernel("Park")
def kernel_park(ctx, *args, **kwargs):
    ctx.current_location = "the park"
    ctx.location_established = True
    return StoryFragment("at the park", kernel_name="Park")

# In action kernels:
@REGISTRY.kernel("Play")
def kernel_play(ctx, *args, **kwargs):
    location_suffix = f" in {ctx.current_location}" if ctx.location_established else ""
    return StoryFragment(f"{char.name} played happily{location_suffix}.")
```

**Implementation notes:**
- Location should persist until explicitly changed
- Meta-patterns with `setting=` kwarg should set location
- Consider location-appropriate action variations (play in park vs play at home)

**Inspired by:** Inform 7's world model with automatic scope

---

## Priority 5: Pronoun Resolution
**Status:** Not started  
**Effort:** Medium  
**Impact:** Medium  

Reduce repetitive character name usage by tracking mentions and using pronouns.

```python
@dataclass
class StoryContext:
    last_subject: Optional[Character] = None
    last_object: Optional[str] = None
    mention_counts: Dict[str, int] = field(default_factory=dict)
    sentences_since_name: int = 0
    
    def subject_reference(self, char: Character) -> str:
        """Get appropriate reference (name or pronoun) for character."""
        self.sentences_since_name += 1
        
        # Use name if: first mention, or >2 sentences since last name, or different character
        if (char.name not in self.mention_counts or 
            self.sentences_since_name > 2 or 
            self.last_subject != char):
            self.mention_counts[char.name] = self.mention_counts.get(char.name, 0) + 1
            self.last_subject = char
            self.sentences_since_name = 0
            return char.name
        
        # Use pronoun
        return char.he  # "he", "she", "they"
```

**Implementation notes:**
- Need to be careful with multiple characters in same scene
- Reset pronoun tracking at scene/phase changes
- Consider object pronouns too (him/her/them, it)

**Inspired by:** Inform 7's automatic pronoun resolution

---

## Priority 6: Ink-style Glue & Text Control
**Status:** Not started  
**Effort:** Low  
**Impact:** Medium  

Ink uses "glue" (`<>`) to control how text fragments join. Currently fragments join with simple spaces, leading to awkward output like "Frog hop. Bird provided guidance."

```python
class StoryFragment:
    text: str
    weight: float = 1.0
    kernel_name: str = ""
    glue_before: bool = False   # NEW: join without space to previous
    glue_after: bool = False    # NEW: join without space to next
    suppress: bool = False      # NEW: generate but don't emit (side effects only)

# Usage in composition:
def _compose(self, left, right):
    if right.glue_before or left.glue_after:
        return StoryFragment(f"{left.text}{right.text}")  # No space
    # ... existing logic
```

**Current problem** (from `Journey` kernel):
- `process=hop + Guidance(Bird)` → "Frog hop. Bird provided guidance." 
- Should be: "Frog hopped along as Bird guided the way."

**Implementation notes:**
- Verbs used as concepts (`hop`) should auto-conjugate based on context
- Compound actions (`hop + Guidance`) need smarter joining: "X did A while Y did B"
- Add `StoryFragment.as_verb()` helper for present/past tense conversion

**Inspired by:** Ink's glue system (`<>`) for text control

---

## Priority 7: Conditional Text Variations (Ink Alternatives)
**Status:** Not started  
**Effort:** Medium  
**Impact:** Medium  

Ink supports inline alternatives: `{~once|twice|many times}` and conditionals `{flag: text if true}`. This could make kernels more dynamic without hardcoding.

```python
# New template syntax with alternatives
self.templates['discovery'] = [
    "{name} found {article} {object}.",
    "{name} discovered {article} {object}!",
    "{name} came across {article} {object}.",  
    "There, in front of {name}, was {article} {object}.",
]

# Conditional based on story state
self.templates['discovery_feared'] = [
    "{name} nervously approached the {object}.",
    "With trembling hands, {name} picked up the {object}.",
]

# In kernel:
def kernel_find(ctx, char, obj):
    if char.Fear > 50:
        return ctx.templates.generate('discovery_feared', name=char.name, object=obj)
    return ctx.templates.generate('discovery', name=char.name, object=obj)
```

**Current problem** (from `Basket`, `Escape` kernels):
- These kernels have smart pattern detection (methods vs threats)
- But text output is still single-template: `"{char.name} escaped from the {thing}!"`
- Missing: variations based on *how* they escaped, *how scared* they were

**Implementation notes:**
- Template selection could weight by emotion state
- Add "once only" templates for first-time events
- Consider cycling through templates to avoid repetition in longer stories

**Inspired by:** Ink's alternatives `{~a|b|c}` and sequences `{stopping: a|b|c}`

---

## Priority 8: ChoiceScript-style Fairmath for Emotions
**Status:** Not started  
**Effort:** Low  
**Impact:** Low  

ChoiceScript uses "fairmath" - bounded changes that are proportional to distance from limits. Currently emotions can overflow (Joy > 100) or underflow (Joy < 0).

```python
class Character:
    def _fairmath_adjust(self, current: float, delta: float) -> float:
        """Bounded adjustment - harder to reach extremes."""
        if delta > 0:
            # Positive change: percentage of remaining headroom
            return current + (100 - current) * (delta / 100)
        else:
            # Negative change: percentage of current value
            return current + current * (delta / 100)
    
    def adjust_joy(self, delta: float):
        self.Joy = max(0, min(100, self._fairmath_adjust(self.Joy, delta)))
```

**Current problem** (from `Happy`, `Contentment`, `Journey` kernels):
- Multiple joy boosts can stack: `char.Joy += 15` in Happy, `+8` in Contentment, `+15` in Journey insight
- A character going through a full Journey pattern ends up with Joy > 100
- No diminishing returns - 5th "happy" event feels same as 1st

**Implementation notes:**
- Keep simple `+=` syntax but clamp internally
- Consider opposing pairs: Joy vs Sadness should balance
- High emotion should decay slightly each phase (regression to mean)

**Inspired by:** ChoiceScript's fairmath system for balanced stat progression

---

## Priority 9: Inform 7-style Implicit Actions
**Status:** Not started  
**Effort:** Medium  
**Impact:** Medium  

Inform 7 automatically inserts implicit actions (opening a closed door before entering). This could help with narrative coherence.

```python
# Define action prerequisites
ACTION_PREREQUISITES = {
    'Escape': ['Fear', 'Danger', 'Trapped'],  # Should have fear/danger context
    'Rescue': ['Fear', 'Danger', 'Accident'],  # Someone must be in danger
    'Forgiveness': ['Conflict', 'Apology'],    # Must have conflict first
    'Celebration': ['Victory', 'Achievement', 'Resolution'],  # Must have won
}

# In executor, check prerequisites and inject if missing:
def _eval_call(self, node):
    # ... existing logic ...
    
    kernel_name = node.func.id
    if kernel_name in ACTION_PREREQUISITES:
        prereqs = ACTION_PREREQUISITES[kernel_name]
        if not any(p in self._executed_kernels for p in prereqs):
            # Auto-inject a minimal prerequisite
            self._inject_prerequisite(kernel_name, prereqs[0])
```

**Current problem** (from `Escape`, `Belonging` kernels):
- `Escape` is smart about methods vs threats, but doesn't ensure danger was established
- `Belonging` has catalyst/process/outcome but they're optional
- Story can have `Rescue(Mom, Lily)` without any `Danger` or `Fear` being established

**Implementation notes:**
- Track which kernels have been executed in context
- Soft prerequisites (warn but continue) vs hard (inject if missing)
- Could also suggest missing kernels in `sample.py` output

**Inspired by:** Inform 7's implicit action system and "before" rules

---

## Priority 10: Twine-style Passage/Scene Structure
**Status:** Not started  
**Effort:** Medium  
**Impact:** High  

Twine organizes stories into passages with links. This maps well to story "beats" or scenes that should have paragraph breaks and distinct moods.

```python
@dataclass
class StoryContext:
    current_scene: str = ""
    scene_fragments: List[StoryFragment] = field(default_factory=list)
    all_scenes: List[Tuple[str, List[StoryFragment]]] = field(default_factory=list)
    
    def start_scene(self, name: str, mood: str = "neutral"):
        """Begin a new scene/passage."""
        if self.scene_fragments:
            self.all_scenes.append((self.current_scene, self.scene_fragments))
        self.current_scene = name
        self.scene_fragments = []
        self.scene_mood = mood
    
    def render(self) -> str:
        """Render with paragraph breaks between scenes."""
        paragraphs = []
        for scene_name, frags in self.all_scenes:
            para = ' '.join(f.text for f in frags if f.weight > 0.3)
            paragraphs.append(para)
        # Add current scene
        if self.scene_fragments:
            paragraphs.append(' '.join(f.text for f in self.scene_fragments if f.weight > 0.3))
        return '\n\n'.join(paragraphs)
```

**Current problem:**
- All output is one continuous paragraph
- Original stories have natural paragraph breaks
- No way to mark "this is a new beat" in the narrative

**Implementation notes:**
- Meta-patterns (`Journey`, `Cautionary`) could auto-create scenes for each phase
- Scene transitions get different connectors: "Meanwhile...", "Later that day..."
- Scene mood affects template selection within that scene

**Inspired by:** Twine's passage structure and Bitsy's room-based organization

---

## Future Ideas (Lower Priority)

### Bitsy-style Minimal Evocative Output
Bitsy creates atmosphere with minimal text. Consider a "compact" mode:

```python
# Verbose (current):
"Once upon a time, there was a little boy named Tim. Tim was very curious. 
Tim found a ball. Tim was happy."

# Compact/evocative:
"Tim, curious. A ball, found. Joy."
```

Useful for: summaries, poetry mode, or dense narrative kernels.

### Kernel Preconditions & Effects Metadata
Tag kernels with preconditions and automatic state effects:

```python
@REGISTRY.kernel("Rescue", 
    requires={"target": {"Fear": ">30"}},
    effects={"target": {"Fear": -30, "Joy": +20}},
    transitions_from=["Danger", "Fall", "Accident"])
def kernel_rescue(ctx, *args, **kwargs):
    pass
```

### Fragment Transition Types
Add semantic transition hints to fragments:

```python
class StoryFragment:
    transition_type: str = "neutral"  # "cause", "contrast", "sequence", "conclusion"
```

### Scene/Beat Boundaries
Explicit scene markers for paragraph breaks and tonal shifts:

```python
ctx.start_scene("confrontation")
# ... generate conflict ...
ctx.end_scene()
ctx.start_scene("resolution")
```

### Dialogue Generation
Quoted speech for character interactions:

```python
@REGISTRY.kernel("Say")
def kernel_say(ctx, speaker, content, to=None):
    return StoryFragment(f'"{content}," said {speaker.name}.')
```

### TADS-style Action Verification
TADS verifies actions before execution. Could add narrative plausibility checks:

```python
@REGISTRY.kernel("Fly")
def kernel_fly(ctx, char, **kwargs):
    # Verify: can this character fly?
    if char.char_type not in ('bird', 'butterfly', 'fairy', 'dragon'):
        # Make it metaphorical or add context
        return StoryFragment(f"{char.name} felt like flying.")
    return StoryFragment(f"{char.name} flew through the air.")
```

### Ink-style Tunnels (Subroutine Calls)
Ink's tunnels let you call a sub-story and return. Could work for recurring patterns:

```python
# Define a reusable sub-pattern
@REGISTRY.tunnel("comfort_sequence")
def tunnel_comfort(ctx, comforter, comforted):
    """Reusable comfort pattern: approach → hug → reassure."""
    return [
        kernel_approach(ctx, comforter, comforted),
        kernel_hug(ctx, comforter, comforted),
        kernel_reassure(ctx, comforter, comforted),
    ]

# Use in kernels:
@REGISTRY.kernel("Comfort")
def kernel_comfort(ctx, *args):
    # Can either do simple version or call tunnel
    if ctx.detail_level > 2:
        return ctx.call_tunnel("comfort_sequence", *args)
    return StoryFragment(f"{args[0].name} comforted {args[1].name}.")
```

---

## Observations from Current Kernel Implementations

### What's Working Well

1. **Pattern detection in `Escape`**: Distinguishes methods (basket, window) from threats (cage, trap)
2. **Context tracking in `Basket`**: Sets `ctx.current_object` for later reference
3. **Structured patterns in `Belonging`**: catalyst/process/outcome mirrors IF story structure
4. **Character group factories in `Kids`**: `_make_character_kernel` reduces boilerplate

### What's Missing

1. **Verb conjugation**: `hop` as a process becomes "Frog hop" not "Frog hopped"
2. **Compound action joining**: `A + B` becomes "A. B." not "A while B" or "A and then B"
3. **Emotion-aware output**: High Fear doesn't affect how `Escape` is narrated
4. **Scene breaks**: No paragraph structure in output
5. **Prerequisite tracking**: Can `Rescue` without `Danger`, `Forgive` without `Conflict`
6. **Template variety**: Most kernels have 1-2 templates, should have 5+ for naturalness

---

## References

- **Ink**: https://www.inklestudios.com/ink/ - Weaves & threading for narrative flow
- **ChoiceScript**: https://www.choiceofgames.com/make-your-own-games/choicescript-intro/ - State-modified text
- **Inform 7**: http://inform7.com/ - World model, pronoun resolution, natural language
- **Twine**: https://twinery.org/ - Passage flow and transitions
- **TADS**: https://www.tads.org/ - Action preconditions and effects

---

## Implementation Order

### Phase 1: Core Narrative Flow (High Impact)
1. [ ] Story Phase Tracking (Priority 1) - Foundation for other improvements
2. [ ] Transition Templates (Priority 2) - Fix choppy narrative flow
3. [ ] Twine-style Scene Structure (Priority 10) - Paragraph breaks, mood tracking

### Phase 2: Text Quality (Medium Impact)
4. [ ] Ink-style Glue & Text Control (Priority 6) - Better fragment joining
5. [ ] Conditional Text Variations (Priority 7) - Template variety
6. [ ] Emotion-Modified Templates (Priority 3) - Use existing emotion state

### Phase 3: World Coherence (Polish)
7. [ ] Location Persistence (Priority 4) - Setting context
8. [ ] Pronoun Resolution (Priority 5) - Natural prose
9. [ ] Implicit Actions (Priority 9) - Narrative prerequisites

### Phase 4: Refinements
10. [ ] Fairmath Emotions (Priority 8) - Bounded stat changes

### Testing Each Change

```bash
# Before making changes, capture baseline
python sample.py -k Journey -n 5 --seed 42 -o > baseline_journey.txt

# After changes, compare
python sample.py -k Journey -n 5 --seed 42 -o > new_journey.txt
diff baseline_journey.txt new_journey.txt

# Pin good stories as tests
python story_tests.py --pin data00:41 --description "Journey with improved flow"
```

### Quick Wins (Can Do Now)

These require only kernel changes, no engine changes:

1. **Add template variety** - Each kernel should have 5+ templates
2. **Improve verb handling** - `_action_to_phrase()` should conjugate properly
3. **Better compound joining** - `_compose()` should use "and", "while", "then"
4. **Add emotion adverbs** - Helper function to get adverb from emotion state

```python
def _emotion_adverb(char: Character) -> str:
    """Get adverb based on dominant emotion."""
    if char.Fear > 60: return "nervously"
    if char.Joy > 70: return "happily"  
    if char.Sadness > 60: return "sadly"
    if char.Anger > 60: return "angrily"
    return ""  # neutral
```

---

## Context Helpers for Autonomous Kernel Optimization

**Key insight**: The language model gets compiled into kernel if-statements. At 10k kernels with sophisticated conditionals, coherence emerges from pattern-matching in kernel code, not engine smarts.

### The Agent Optimization Loop

```
1. python sample.py -k Brave -n 10 --show-source
2. See: "Tim was scared. Tim was brave." (incoherent)
3. Add if-statement to kernel_brave checking for recent Fear
4. Retest: "Tim was scared. Despite his fear, Tim was brave." (coherent)
5. Repeat
```

### StoryContext Helper Properties

Add computed properties to `StoryContext` that make pattern-matching easy for kernels:

```python
@dataclass
class StoryContext:
    # ... existing fields ...
    
    @property
    def recent_kernels(self) -> list[str]:
        """Last 5 kernel names for quick pattern matching."""
        return [f.kernel_name for f in self.fragments[-5:] if f.kernel_name]
    
    @property
    def recent_emotions(self) -> dict[str, int]:
        """Aggregate emotion changes from recent fragments."""
        # Track which emotions were affected recently
        ...
    
    @property  
    def mentioned_names(self) -> set[str]:
        """Character names mentioned recently - for pronoun decisions."""
        ...
    
    @property
    def last_action(self) -> Optional[str]:
        """Most recent action kernel name (Run, Walk, Find, etc.)."""
        action_kernels = {'Run', 'Walk', 'Find', 'See', 'Eat', 'Play', ...}
        for f in reversed(self.fragments[-5:]):
            if f.kernel_name in action_kernels:
                return f.kernel_name
        return None
```

### Pattern-Matching Helpers

Common patterns extracted as helper functions:

```python
def follows_kernel(ctx: StoryContext, kernel: str, within: int = 3) -> bool:
    """Check if this kernel follows a specific kernel recently."""
    return kernel in ctx.recent_kernels[:within]

def follows_emotion(ctx: StoryContext, emotion: str) -> bool:
    """Check if this follows an emotion kernel (Fear, Joy, Sadness, etc.)."""
    emotion_kernels = {'Fear', 'Joy', 'Sadness', 'Anger', 'Love', 'Happy', 'Scared'}
    return any(k in emotion_kernels and emotion.lower() in k.lower() 
               for k in ctx.recent_kernels)

def same_character_focus(ctx: StoryContext, char: Character) -> bool:
    """Is this the same character as the current focus?"""
    return ctx.current_focus and ctx.current_focus.name == char.name

def character_just_mentioned(ctx: StoryContext, char: Character) -> bool:
    """Was this character just mentioned? (use pronoun instead)"""
    if not ctx.fragments:
        return False
    return char.name in ctx.fragments[-1].text
```

### Example: Context-Aware Kernel

Before (incoherent):
```python
@REGISTRY.kernel("Brave")
def kernel_brave(ctx, *args, **kwargs):
    char = _get_character(args, ctx)
    return StoryFragment(f"{char.name} was brave.")
```

After (coherent):
```python
@REGISTRY.kernel("Brave")
def kernel_brave(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    char = _get_character(args, ctx)
    
    # Pattern: Brave after Fear → "Despite fear..."
    if follows_kernel(ctx, 'Fear'):
        return StoryFragment(f"Despite {char.pronoun_his} fear, {char.name} was brave.")
    
    # Pattern: Brave after Danger → "Facing danger..."
    if follows_kernel(ctx, 'Danger'):
        return StoryFragment(f"Facing the danger, {char.name} stayed brave.")
    
    # Pattern: same character → use pronoun
    if same_character_focus(ctx, char):
        return StoryFragment(f"{char.he.capitalize()} was very brave.")
    
    # Default
    return StoryFragment(f"{char.name} was brave.")
```

### Scaling to 10k Kernels

| Kernel Count | What Gets Encoded in If-Statements |
|--------------|-------------------------------------|
| 800 | Basic patterns: "Apology with recipient", "Fear of object" |
| 2k | Context awareness: "Brave after Fear", "Joy after Loss" |
| 5k | Narrative arcs: "Resolution references Conflict" |
| 10k | Style variations: "short sentence after long", pronoun decisions |

### Implementation Priority

1. **Add `recent_kernels` property** - Trivial, immediately useful
2. **Add `follows_kernel()` helper** - Simple function, enables pattern matching
3. **Update 10 key emotion kernels** - Brave, Happy, Sad, Scared to use patterns
4. **Document patterns in kernel docstrings** - Help agent know what to check
5. **Add `--incoherent` flag to sample.py** - Find stories where patterns break

### Why This Works

Infocom's coherence came from hand-written responses. Storyweavers' coherence comes from:

1. **LLM extracts patterns** at dataset creation time
2. **Agent encodes patterns** into if-statements during kernel development
3. **Runtime executes code** - no LLM needed

The more sophisticated the if-statements, the more coherent the output. The agent's job is to:
- Sample stories
- Identify incoherent sequences
- Add conditionals to handle them
- Test and iterate

**The kernels ARE the language model, just compiled into code.**

