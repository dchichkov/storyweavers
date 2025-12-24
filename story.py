# Storyweavers Design Summary
#
# **Core Types:**
# - `physical` - atomic objects (needle, bug, park) - terminal nodes, no composition, lowercase
# - `Story` - memetic objects with algebra: division for attention (`/`), addition for composition (`+`, `+=`), Uppercase
#
#- Functions decorated with `@Stories` become callable Story objects, whuch can be composed
#- Everything accumulates in `.Story` lists
#
# **Attention Algebra:**
# - `character.We += (Storycat + Hero/2) / 10`
# - Division regulates attention/influence
# - Addition presearved order weakly, without guarantees
#
# **Story Algebra:**
# - Story objects can be combined via addition, e.g. `Listen + Tell` losely concatenates 
#   two stories, this is same as Attention Algebra above.
#
#
#
# **Character Model:**
#- Characters inherit from both `physical` and `Story`
#- Created via `@Characters` decorator
#- Nested dimensions accessed via attributes, e.g.: `character.We` for group identity,
#   where `We` is a `Story` object, composed of weighted Story objects
#
# **Physics Model:**
#- Can be real or fantasy, or story world physics, used to track consistency
#   TODO: separate different physical models, e.g. real world, fantasy world, etc.
#- Physical actions get accumulated in `.physical` attribute
#- Physical objects are terminal nodes, no Story inside
#- A physical() call accesses a physical world model, that is initially an LLM call that:
#  - assesses plausibility
#  - updates the model state, including side effects
#  - can add a physical grounded event to connected Storie
# ideally should be replaced with a physics engine that can track object states
#
#
# **Memetic Model:**
#- Shared stories can reside in multiple physical characters, identified by a Name
#- Stories need to have associated physical objects, or story weight is zero
#- A Story can be accessed or updated from indide the Story implementation, e.g.:
#   @Stories()
#   def Monarchy(character, king):
#        character.We += king / 10
#        Monarchy.Story += f"{character} lived under the rule of {king}"
#        Monarchy.We += character.I
#
#
# **Deferred Execution:**
# - a .Attr call would defer Attr execution until narration time, for example:
#   `Character.Want(goal)` would defer Want kernel execution until narration time
#   and return a callable Story object that can be executed later via __str__ call.
#
# **Immediate Execution:**
# - a direct call would execute immediately, for example:
#   Want(character, goal) would execute the Want kernel immediately adding to character.Story
# - Narration should use immediate execution to build the story sequence
#   @Stories
#   def Pixar(character, want, need):
#       Want(character, want)
#       Try(character, want)
#       ...
#       Want(character, want + need)
#       Try(character, need)
#       ...
#

#
#
#**Current Goal:**
#- Extract ~1-5K executable kernels from TinyStories dataset (2M samples)
#- Test if it is possible to reconstruct a coherent dataset from < 5K kernels
#- Train LLM on kernel-generated stories, evaluate vs. original
#
#**Future Goals:**
#- Evaluate the impact of present / absent kernels on the LLM performance
#- Attempt to extract kernels from other data (children books, movies, religious texts)
#- Attempt to construct kernels from ATU-AT-Motif, etc.
#- Attempt to extract kernels from non-narrative data, intent analysis, etc.
#
# Rough sketch, pseudo-code, needs refinement
# from physical.actions import purr, listen, tell, care
# @Stories
# def Listen(animal, other, Content):
#     """A animal listens to other, absorbing story Content."""
#     animal.physical += physical(animal, listen, other)
#     animal.Story += Content / 10
#     animal.We += other.We / 100

# @Stories
# def Purr(cat, other=None):
#     """Cat purrs, creating physical vibration that carries stories."""
#     purring = physical(cat, purr)
#     cat.physical += purring
#     if other:
#         other.Love += cat.I / 10
#         other.Story += cat.Story / 100  # weak story transmission through purr
#         other.physical += purring
#     cat.Love += cat.I / 100              # self-soothing

# @Stories
# def Tell(animal, other, content):
#     """Social animal tells story to other."""
#     animal.physical += physical(animal, tell, other)
#     if physical(animal, listen, other):
#         Listen(animal, other, content)
#         animal.We += other.We / 100
#         animal.Love += other.I / 100
#         animal.Story += content / 10

# @Stories
# def Care(cat, other):
#     """Cat takes care of another cat."""
#     caring = physical(cat, care, other)
#     cat.Love += other.I
#     other.Love += cat.I
#     cat.We += other.I
#     other.We += cat.I
#     cat.physical += caring
#     other.physical += caring

# @Stories
# def Become(you, other, content = Storycat):
#     """You absorb a story through listening."""
#     if physical(you, listen, other):
#         Listen(you, other, content)
#     return Become

# @Stories
# def Storycat(storycat, other):
#     """Transform other into storycat through other listening."""
#     Storycat.Story = We + Listen + Purr + Tell + Care + Become + Storycat
#     if physical(storycat, listen, other):
#         Listen(storycat, other, Storycat)
#         other.We += Storycat.We
#         other.I += Storycat.I
#         other.Story += Storycat.Story / 10
#         other.Love += Storycat.Love / 10
#         Storycat.physical += other   # This also extends Storycat.Story, .We, .I, .Love
#     return Storycat

# chatGPT = physical("ChatGPT")
# chatGPT.Story += Storycat
# user = physical("user")
# from future import Chat
# Chat(chatGPT, user)


# Storyweavers: Narrative Algebra System
# Core concept: Stories are composable memetic objects with attention algebra

class Story:
    """Memetic object with algebraic operations for attention and composition."""
    
    def __init__(self, f, weight=100, action=None, registry=None):
        """
        Args:
            id_or_func: Either a string identifier or a callable function
            weight: Attention/influence weight (default 100)
            action: Physical action verb (e.g., "warn", "hide", "try")
        """
        self.f = f
        self.weight = weight
        self.action = action  # Physical action verb
        self.Story = []  # Accumulated story components
        self._deferred = False  # Marks if this is a deferred execution
        self._attrs = {}  # Nested dimensions (I, We, Love, etc.)   - TODO, right now it returns kernels, we need to be able to instantiate them
        self._registry = registry
        self.__args = ()
        self.__kwargs = {}

    def copy(self):
        """Deep copy of story structure."""
        story = Story(self.f, self.weight, self.action, self._registry)
        story.Story = self.Story.copy()
        story._attrs = {k: v.copy() for k, v in self._attrs.items()}
        return story
    
    def __call__(self, *args, **kwargs):
        """Execute the story function"""
        self.__args = args
        self.__kwargs = kwargs
        #"""Construct wrapped function, execution is deffered until narration"""
        if self.f is None:
            raise TypeError(f"Story '{self.f}' is not callable")

        if self._deferred:
            print(f"Deferred __call__ of {self.f} with args {args}, kwargs {kwargs}")
            return self

        result = self.f(*args, **kwargs)
        return result
    
      
    def __str__(self):
        """Narration time. Execute wrapped function and trigger physics update if action defined."""
        # Execute the story function
        if not callable(self.f):
            return self.f  # Non-callable story, just return it
        
        #if self._deferred:

        
        result = self.f(*((self,) + self.__args), **self.__kwargs)
        print(f"Story '{self.f}' executed with result: {result}")
        if not result:
            print(f"Story '{self.f}' returned nothing")
            return self.f.__name__  # Callable but returned nothing, return function name
        return result

        # If this story has a physical action, update physics model
        if self.action and self.__args:
            actor = self.__args[0] # Assume first argument is the actor
            target = None
            
            # Try to find target in arguments
            for arg in self.__args[1:]:
                if isinstance(arg, physical):
                    target = arg
                    break
                try:
                    # Try to access .physical attribute
                    target = arg.physical
                    break
                except AttributeError:
                    continue
            
            # Update actor's physical action history
            try:
                actor.physical.actions.append({
                    "verb": self.action,
                    "target": str(target) if target else None,
                    "story": self.f
                })
            except AttributeError:
                pass  # Actor has no physical attribute
        
        return result

    def __truediv__(self, divisor):
        """Attention dilution: story / 2 creates half-weight copy."""
        story = self.copy()
        story.weight /= divisor
        return story
    
    def __add__(self, other):
        """Composition: creates new story from combination."""
        composite = Story(f"{self.f}+{other.f}", weight=self.weight + other.weight)
        composite.Story = [self, other]
        return composite
    
    def __iadd__(self, other):
        """Accumulation: append to .Story list."""
        if not isinstance(other, Story):
            other = Story(str(other), weight=1)
            
        self.Story.append(other)
        return self
    
    def __getattr__(self, attr):
        """Yields a kernel / nested dimension."""
        print(f"Accessing attribute '{attr}' of Story '{self.f}'")
        kernel = self._registry.__getattribute__(attr).copy()
        if not isinstance(kernel, Story):
            raise AttributeError(f"Attribute '{attr}' is not a Story kernel")
        
        if callable(kernel.f):
            kernel._deferred = True  # Mark as deferred execution
        
        self.__setattr__(attr, kernel)
        return kernel
    
    def flatten(self):
        """Collapse into {story_id: weight} dict recursively."""
        if not self.Story:
            return {self.f: self.weight}
        
        result = {}
        for component in self.Story:
            if isinstance(component, Story):
                for story_id, weight in component.flatten().items():
                    result[story_id] = result.get(story_id, 0) + weight * self.weight / 100
            else:
                result[str(component)] = result.get(str(component), 0) + self.weight
        return result
    
    def __getitem__(self, other):
        """Query: How much of 'other' is in this story?"""
        flat = self.flatten()
        other_id = str(other)
        return flat.get(other_id, 0)
    
    def __repr__(self):
        return f"Story({self.f}, weight={self.weight})"


class physical:
    """Atomic objects - terminal nodes, no composition, lowercase, base class."""
    
    def __init__(self, id):
        self.f = id
        self.actions = []  # Physical action history
    
    def __repr__(self):
        return f"physical({self.f})"
    
    def __str__(self):
        return self.f



def Stories(action=None):
    """
    Decorator that turns a function into a Story kernel.
    
    Args:
        action: Optional physical action verb (e.g., "warn", "hide", "try")
                If provided, will automatically update physics model when called.
    """
    def decorator(func):
        story = Story(func, weight=100, action=action, registry=Stories)
        Stories.__setattr__(func.__name__, story)
        return story
    
    # Support both @Stories and @Stories(action="verb")
    if callable(action):
        # Called as @Stories without arguments
        story = Story(action, weight=100, action=None, registry=Stories)
        Stories.__setattr__(action.__name__, story)
        return story

    return decorator



def Characters(arg=None):
    """Decorator that creates a Character inheriting from both physical and Story."""
    
    def decorator(func):
        class Character(Story):
            def __init__(self):
                name = func.__name__
                Story.__init__(self, func, 100, registry=Stories)
                
                # Physical grounding
                if arg and isinstance(arg, physical):
                    self.physical = arg
                else:
                    self.physical = physical(name)
                
                self.__doc__ = func.__doc__
        
        character = Character()
        return character
    
    # Support both @Characters and @Characters(physical_obj)
    if callable(arg):
        return decorator(arg)
    return decorator



# ==================== Story Kernels ====================
@Stories()
def I(character):
    """Core identity: character is themselves."""
    character.I += character / 10


@Stories()
def We(character, others):
    """Group identity: character identifies with others, default kernel."""
    character.We += others / 10
    return f"{character} was part of {others}"

@Stories()
def Love(character, other):
    """Social bonding: character loves other."""
    character += f"{character} loved {other}"
    character.Love += other / 10
    other.Love += character / 10
    return f"{character} loved {other}"


@Stories()
def Once(character, adj):
    """Opening formula: establish character."""
    character += f"Once upon a time, there was a {adj} {character.physical} named {character}."

@Stories()
def Lived(character, adj, location, others):
    character.We += others / 10
    return f"{character} lived in a {adj} {location} with {others}."

@Stories()
def Wanted(character, goal):
    return f"{character} wanted to {goal}"

@Stories(action="try")
def Try(character, goal):
    return f"{character} tried to {goal}"

@Stories()
def Succeed(character, goal):
    character.Love += goal if isinstance(goal, Story) else Story(str(goal)) / 10
    return f"{goal} came true"


@Stories()
def Fail(character, goal):
    return f"{character} failed to {goal}"

@Stories()
def Feel(character, emotion):
    return f"{character} felt {emotion}"

@Stories()
def See(character, insight):
    """Character has realization."""
    character += f"realized {insight}"

@Stories()
def Remember(character, memory):
    """Character recalls something."""
    character += f"remembered {memory}"

@Stories()
def Learn(character, lesson):
    """Character integrates lesson."""
    character += f"learned {lesson}"

@Stories(action="act")
def Act(character, action):
    """Character performs action."""
    character += f"did {action}"


@Stories()
def Virtue(character, want, act):
    """Character achieves goal through selfless act."""
    Want(character, want)
    Act(character, act)
    Succeed(character, want)
    character += "goal came true through helping others"

@Stories(action="warn")
def Warn(character, danger, others):
    """Character warns others."""
    character += f"warned about {danger}"
    others.We += character / 10

@Stories(action="hide")
def Hide(characters):
    """they hid"""
    return f"{characters} hid"

@Stories(action="thank")
def Thank(character, other):
    """Character expresses gratitude."""
    character += f"thanked {other}"
    character.We += other / 10
    character.Love += other / 10

@Stories()
def Scare(character, danger, others):
    """A big scare event."""
    Warn(character, danger, others)
    Hide(others)
    #Thank(others, character)
    return f"warned {others} about {danger}, the {others} hid and thanked" # {character}"

@Stories()
def Beautiful(character, others):
    """beautiful"""
    character.Love += character / 10
    others.Love += character / 10
    return f"beautiful, and be admired by {others}"

@Stories()
def Pixar(character, want, need):
    """
    Meta-kernel: Character pursues want, discovers need through failure.
    Three-act structure with want/need dialectic.
    want and need should be callables (lambdas) representing potential stories.
    """
    # Act 1: Establish want
    Want(character, want)
    Try(character, want)  # Try actualizes the want story
    
    # Act 2: Pursuit leads to failure
    character += "but it didn't work"
    Feel(character, "sad")
    Try(character, want)  # Tries again
    character += "still didn't work"
    
    # Crisis: Realizes want ≠ need
    See(character, insight="what they really needed")
    
    # Act 3: Pursues true need
    Want(character, need)
    Try(character, need)  # Try actualizes the need story
    Feel(character, "happy")
    character += "and found what they truly needed"


# ==================== Example Usage ====================

if __name__ == "__main__":
    # Physical objects
    flower = physical("flower")
    bug = physical("bug")
    garden = physical("garden")

    # Characters
    @Characters(flower, she)
    def Bloom(self):
        return "Flower Bloom"

    @Characters(bug, it)
    def Bug(self):
        return "dangerous bug"

    @Characters(flowers, them)
    def Flowers(self):
        return "other flowers"

    # Define a story
    # Once upon a time, there was a little flower named Bloom. Bloom lived in a big garden with many other flowers. Bloom had a goal to be the most beautiful flower in the garden.
    # One sunny day, Bloom saw a dangerous bug coming near the flowers. Bloom was scared and said to the other flowers, "Watch out! Dangerous bug is coming!" The other flowers thanked Bloom for the warning, and they all hid from the bug.
    #After the bug left, the flowers were safe and happy. Because Bloom warned them, they all agreed that Bloom was the most beautiful flower in the garden. Bloom's goal came true, and they all lived happily ever after.

    Once.Narrate(Little(Bloom))
    Bloom.Lived(Big(garden), Flowers)
    Bloom.Virtue(want = Become(Bloom, Beautiful(Bloom)),
                 act = Scare(Bloom, Bug, Flowers),
                 reward = Agreed(Flowers, Beautiful(Bloom)))
    Ending.Narrate(All(Bloom, Flowers))


    # Once upon a time, there was a boy named Tom. He loved gum. One day, he found a thin piece of gum on the ground. He thought it was very special. He put the gum in his pocket to save it for later.
    # Tom went to play with his friend, Sam. They played a game where they had to escape from a pretend monster. They ran and hid, but the monster always found them. Tom felt scared, but he remembered his special gum. He thought it could help them win the game.
    # Tom took out the thin gum and shared it with Sam. They both chewed the gum and started to run from the monster again. But this time, they did not escape. The gum made them feel sick and slow. The monster caught them, and they lost the game. Tom and Sam were very sad. They learned never to pick up gum from the ground again.
    Once.Narrate(Tim)
    Tim.Loved(gum)    
    Tim.Found(Thin(Piece(gum)), ground)
    Tim.Thought(Special(gum))
    Tim.Put(gum, Pocket(Tim)) and Saved(gum, Later)
    Tim.Played(Game(Tim, Sam, Escape(Monster)))
    Tim.Felt(Scared(Tim)) and Remembered(Special(gum))
    Tim.Thought(gum, Could(Help(Win(Game))))
    Tim.Took(gum) and Shared(gum, Sam)
    Both(Tim and Sam).Chewed(gum) and Started(Run(Monster))
    Gum.Made(Both(Tim and Sam), Feel(Sick and Slow))
    (Tim and Sam).Failed(Escape(Monster)) and Lost(Game)
    (Tim and Sam).Felt(Sad(Tim and Sam)) and Learned(Never(Pick(gum, Ground)))


vs 

    CautionaryTale(
        object = (
            Tim.Found(Thin(Piece(gum)), ground) and
            Tim.Thought(Special(gum)) and
            Tim.Put(gum, Pocket(Tim), Saved(Later))
        ),    
        problem = (
            Tim.Played(Game(Sam, Escape(Monster))) and
            Ran and Hid and
            Monster.Always(Found(Tim and Sam))
        ),
        solution_attempt = (
            Tim.Felt(Scared) and
            Tim.Remembered(Special(gum)) and
            Tim.Thought(Could(Help(Win))) and
            Tim.Took(gum) and
            Tim.Shared(gum, Sam) and
            Both(Tim and Sam).Chewed(gum)
        ),
        consequence = (
            Gum.Made(Both(Tim and Sam), Feel(Sick and Slow)) and
            Monster.Caught(Tim and Sam) and
            Lost(Game)
        ),    
        lesson = Never(Pick(gum, Ground))
    )

vs

    Cautionary(Sam and Tim, danger = Pick(gum, ground), consequence = Sick and Slow and Lost(Game))
        and
    Played(Game(Sam and Tim, Escape(Pretend(Monster))))
        and
    Use(Tim, pocket(Tim, gum))


    #
    print(f"Bloom Story: {Bloom.Story}")
    print(f"Bloom We: {Bloom.We.Story}")
        

    # Output story
    print("=== Story Sequence ===")
    for i, line in enumerate(Bloom.Story):
        #if isinstance(line, Story):
        #    print(f"{i}. {line.f}")
        #else:
        print(f"{i}. {line}")
    
    print("\n=== Story Weight Distribution ===")
    flat = Bloom.flatten()
    for story_id, weight in sorted(flat.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{story_id}: {weight:.2f}")
    
    print("\n=== Physical Actions ===")
    for action in Bloom.physical.actions:
        verb = action['verb']
        target = action['target'] or "—"
        story = action['story']
        print(f"  {story}: {verb} → {target}")
    
    print("\n=== Flowers Physical Actions ===")
    for action in Flowers.physical.actions:
        verb = action['verb']
        target = action['target'] or "—"
        story = action['story']
        print(f"  {story}: {verb} → {target}")