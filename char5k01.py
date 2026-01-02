"""
Character Definitions Pack #01 (char5k01.py)

Common character names used in TinyStories dataset.
These provide default character types and traits, reducing verbosity.

Usage:
    # Use defaults (recommended for common cases):
    Lucy()  # Creates a friendly girl named Lucy (default traits)
    Tim()   # Creates a curious boy named Tim (default traits)
    Mom()   # Creates a caring mother named Mom
    
    # Full customization (when needed):
    Lucy(Character, woman, Wise+Patient)  # Creates a wise and patient woman named Lucy
    Tim(Character, man, Brave+Strong)     # Creates a brave and strong man named Tim
    
Design Philosophy:
- Provides sensible defaults for common character names
- Reduces boilerplate in kernels (Lucy() instead of Lucy(Character, girl, Friendly))
- Still allows full Character(name, type, traits) syntax when customization is needed
- First call creates the character, subsequent calls reference it

Default Traits by Character:
- Lucy: friendly girl
- Tim: curious boy  
- Mom: caring mother
- etc. (see individual kernel docstrings)
"""

from gen5 import (
    REGISTRY,
    StoryContext,
    StoryFragment,
    Character,
)


def _make_character_kernel(name: str, default_type: str = "character", default_traits: list = None):
    """
    Factory to create character name kernels with default types and optional traits.
    
    Handles two main patterns:
    1. Name()                           -> Use defaults
    2. Name(Character, type, traits)    -> Full customization (handled like regular Character kernel)
    """
    def kernel_func(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
        # Check if character already exists (reference to existing character)
        if name in ctx.characters:
            char = ctx.characters[name]
            ctx.current_focus = char
            return StoryFragment("")  # Character already introduced
        
        # Parse arguments  
        char_type = default_type
        traits = default_traits[:] if default_traits else []
        
        # Check if this is Character(name, type, traits) pattern
        # In this case, args[0] will be a StoryFragment marker from Character kernel
        if args and isinstance(args[0], StoryFragment) and args[0].text == '' and args[0].kernel_name == '':
            # Pattern: Name(Character, type, traits)
            # This matches the standard Character kernel behavior in gen5.py
            if len(args) > 1:
                char_type = str(args[1])
            if len(args) > 2:
                traits_arg = args[2]
                if isinstance(traits_arg, str):
                    traits = [t.strip() for t in traits_arg.split('+')]
                elif isinstance(traits_arg, list):
                    traits = traits_arg
        # else: Pattern 1 - Name() with no args, use defaults
        
        # Create the character
        char = ctx.add_character(name, char_type, traits)
        ctx.current_focus = char
        
        # Generate introduction text based on position
        is_first = len(ctx.characters) == 1
        
        if traits:
            adj_list = " and ".join(traits[:2]) if len(traits) <= 2 else ", ".join(traits[:2]) + ", and " + traits[2]
            adj = adj_list.lower()
            if is_first:
                return StoryFragment(f"Once upon a time, there was a {adj} {char_type} named {name}.")
            else:
                return StoryFragment(f"There was also a {adj} {char_type} named {name}.")
        else:
            if is_first:
                return StoryFragment(f"Once upon a time, there was a {char_type} named {name}.")
            else:
                return StoryFragment(f"There was also a {char_type} named {name}.")
    
    return kernel_func


# =============================================================================
# COMMON GIRL NAMES
# =============================================================================

@REGISTRY.kernel("Lucy")
def kernel_lucy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Lucy - A girl character. Common traits: Curious, Playful, Friendly, Kind."""
    return _make_character_kernel("Lucy", "girl", ["friendly"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Lily")
def kernel_lily(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Lily - A girl character. Common traits: Curious, Hopeful, Friendly, Playful."""
    return _make_character_kernel("Lily", "girl", ["curious"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Emma")
def kernel_emma(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Emma - A girl character. Common traits: Kind, Helpful, Caring."""
    return _make_character_kernel("Emma", "girl", ["kind"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Anna")
def kernel_anna(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Anna - A girl character. Common traits: Sweet, Gentle, Caring."""
    return _make_character_kernel("Anna", "girl", ["sweet"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Sue")
def kernel_sue(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sue - A girl character. Common traits: Kind, Helpful, Friendly."""
    return _make_character_kernel("Sue", "girl", ["helpful"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Amy")
def kernel_amy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Amy - A girl character. Common traits: Playful, Happy, Energetic."""
    return _make_character_kernel("Amy", "girl", ["playful"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Sara")
def kernel_sara(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sara - A girl character. Common traits: Smart, Curious, Thoughtful."""
    return _make_character_kernel("Sara", "girl", ["smart"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Mia")
def kernel_mia(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Mia - A girl character. Common traits: Brave, Adventurous, Bold."""
    return _make_character_kernel("Mia", "girl", ["brave"])(ctx, *args, **kwargs)


# =============================================================================
# COMMON BOY NAMES
# =============================================================================

@REGISTRY.kernel("Tim")
def kernel_tim(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Tim - A boy character. Common traits: Curious, Playful, Brave."""
    return _make_character_kernel("Tim", "boy", ["curious"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Tom")
def kernel_tom(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Tom - A boy character. Common traits: Friendly, Helpful, Kind."""
    return _make_character_kernel("Tom", "boy", ["friendly"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Max")
def kernel_max(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Max - A boy character. Common traits: Playful, Energetic, Fun."""
    return _make_character_kernel("Max", "boy", ["playful"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Ben")
def kernel_ben(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Ben - A boy character. Common traits: Brave, Strong, Confident."""
    return _make_character_kernel("Ben", "boy", ["brave"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Sam")
def kernel_sam(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sam - A child character. Common traits: Smart, Clever, Resourceful."""
    return _make_character_kernel("Sam", "child", ["smart"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Jack")
def kernel_jack(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Jack - A boy character. Common traits: Adventurous, Brave, Bold."""
    return _make_character_kernel("Jack", "boy", ["adventurous"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Timmy")
def kernel_timmy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Timmy - A boy character. Common traits: Curious, Playful, Friendly."""
    return _make_character_kernel("Timmy", "boy", ["curious"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Tommy")
def kernel_tommy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Tommy - A boy character. Common traits: Happy, Cheerful, Playful."""
    return _make_character_kernel("Tommy", "boy", ["happy"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Billy")
def kernel_billy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Billy - A boy character. Common traits: Silly, Fun, Playful."""
    return _make_character_kernel("Billy", "boy", ["silly"])(ctx, *args, **kwargs)


# =============================================================================
# COMMON ADULT/FAMILY NAMES
# =============================================================================

@REGISTRY.kernel("Mom")
def kernel_mom(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Mom - A mother character. Common traits: Caring, Loving, Protective."""
    return _make_character_kernel("Mom", "mother", ["caring"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Mommy")
def kernel_mommy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Mommy - A mother character. Common traits: Loving, Kind, Gentle."""
    return _make_character_kernel("Mommy", "mother", ["loving"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Dad")
def kernel_dad(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Dad - A father character. Common traits: Strong, Helpful, Wise."""
    return _make_character_kernel("Dad", "father", ["helpful"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Daddy")
def kernel_daddy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Daddy - A father character. Common traits: Fun, Playful, Loving."""
    return _make_character_kernel("Daddy", "father", ["fun"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Grandma")
def kernel_grandma(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Grandma - A grandmother character. Common traits: Wise, Kind, Gentle."""
    return _make_character_kernel("Grandma", "grandmother", ["wise"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Grandpa")
def kernel_grandpa(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Grandpa - A grandfather character. Common traits: Wise, Patient, Fun."""
    return _make_character_kernel("Grandpa", "grandfather", ["wise"])(ctx, *args, **kwargs)


# =============================================================================
# COMMON ANIMAL/PET NAMES
# =============================================================================

@REGISTRY.kernel("Spot")
def kernel_spot(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Spot - A dog character. Common traits: Loyal, Friendly, Playful."""
    return _make_character_kernel("Spot", "dog", ["loyal"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Fluffy")
def kernel_fluffy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Fluffy - A cat character. Common traits: Soft, Cuddly, Playful."""
    return _make_character_kernel("Fluffy", "cat", ["fluffy"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Whiskers")
def kernel_whiskers(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Whiskers - A cat character. Common traits: Curious, Clever, Independent."""
    return _make_character_kernel("Whiskers", "cat", ["curious"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Bobo")
def kernel_bobo(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Bobo - A monkey character. Common traits: Silly, Playful, Mischievous."""
    return _make_character_kernel("Bobo", "monkey", ["playful"])(ctx, *args, **kwargs)

@REGISTRY.kernel("Bella")
def kernel_bella(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Bella - A pet character (dog/cat). Common traits: Beautiful, Gentle, Loving."""
    return _make_character_kernel("Bella", "dog", ["beautiful"])(ctx, *args, **kwargs)


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    from gen5 import KernelExecutor
    
    print("=" * 70)
    print("CHARACTER DEFINITIONS PACK #01 - TEST RUN")
    print("=" * 70)
    print()
    
    executor = KernelExecutor()
    
    tests = [
        # Pattern 1: Use defaults
        ("Lucy()", "Should use default: friendly girl"),
        ("Tim()", "Should use default: curious boy"),
        ("Mom()", "Should use default: caring mother"),
        
        # Pattern 2: Full customization via Character marker
        ("Lucy(Character, woman, Wise+Patient)", "Should allow full customization"),
        ("Tim(Character, man, Brave+Strong)", "Should allow full customization"),
        
        # Multiple characters
        ("Lucy()\nTim()\nMom()", "Should introduce multiple characters"),
        
        # References (second mention)
        ("Lucy()\nLucy()", "Second mention should not re-introduce"),
        
        # Mix with actions
        ("Lucy()\nTim()\nFriendship(Lucy, Tim)", "Characters with kernels"),
    ]
    
    for i, (kernel_str, description) in enumerate(tests, 1):
        print(f"{'=' * 70}")
        print(f"TEST {i}: {description}")
        print(f"{'=' * 70}")
        print("KERNEL:")
        print(kernel_str)
        print()
        print("GENERATED:")
        story = executor.execute(kernel_str)
        print(story)
        print()
    
    print("=" * 70)
    print("✅ CHARACTER PACK LOADED")
    print(f"   Total kernels in registry: {len(REGISTRY.kernels)}")
    print("=" * 70)

