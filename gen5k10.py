"""
gen5k10.py - Additional Kernel Pack #10

This module extends gen5.py with additional kernel implementations
focused on high-usage missing kernels from coverage analysis.

=============================================================================
KERNELS IN THIS PACK (with usage patterns from sampling):
=============================================================================

## Action Kernels
- Mix(ingredients)                 -- mixing ingredients (baking, cooking)
- Avoid(char, thing)               -- avoiding something/someone
- Purchase(char, item)             -- buying/purchasing items
- Capture(char, target)            -- catching or capturing something
- Drive(char, vehicle)             -- driving a vehicle
- Check(char, thing)               -- checking or examining something
- Put(char, object, location)      -- putting/placing objects

## Emotion/Response Kernels
- Reaction(char, stimulus)         -- reacting to something

## State/Status Kernels
- Missing(object)                  -- something is missing/lost
- Caution(char, about=thing)       -- warning someone to be careful

"""

from gen5 import (
    REGISTRY,
    StoryContext,
    StoryFragment,
    Character,
    NLGUtils,
    _to_phrase,
    _action_to_phrase,
    _get_default_actor,
)

# =============================================================================
# ACTION KERNELS
# =============================================================================

@REGISTRY.kernel("Mix")
def kernel_mix(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Mixing ingredients or things together.
    
    Patterns from sampling:
      - Mix(bowl)                    -- mixing in a bowl
      - Mix(flour, sugar, eggs)      -- mixing ingredients
      - Mix(clay, clay)              -- combining materials
      - Mix(mixer, batter)           -- using a mixer
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        if objects:
            if len(objects) == 1:
                return StoryFragment(f"{char.name} mixed {_to_phrase(objects[0])}.")
            else:
                items = NLGUtils.join_list([_to_phrase(obj) for obj in objects])
                return StoryFragment(f"{char.name} mixed {items} together.")
        return StoryFragment(f"{char.name} mixed the ingredients.")
    
    # No character - used as concept/process
    if objects:
        if len(objects) == 1:
            return StoryFragment(f"mixing {_to_phrase(objects[0])}", kernel_name="Mix")
        items = NLGUtils.join_list([_to_phrase(obj) for obj in objects])
        return StoryFragment(f"mixing {items}", kernel_name="Mix")
    
    return StoryFragment("mixing", kernel_name="Mix")


@REGISTRY.kernel("Avoid")
def kernel_avoid(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Avoiding something or someone.
    
    Patterns from sampling:
      - Avoid(Vet, SharpTest)        -- avoiding future situations
      - Avoid(BigWave)               -- staying away from danger
      - Avoid(Circus)                -- avoiding places after bad experience
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        char.Fear += 3
        if objects:
            thing = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} learned to avoid {thing}.")
        return StoryFragment(f"{char.name} stayed away.")
    
    # No character - used as concept
    if objects:
        thing = _to_phrase(objects[0])
        return StoryFragment(f"avoiding {thing}", kernel_name="Avoid")
    
    return StoryFragment("avoiding", kernel_name="Avoid")


@REGISTRY.kernel("Purchase")
def kernel_purchase(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Purchasing or buying something.
    
    Patterns from sampling:
      - Purchase(Chair, blue + Toys) -- buying a new item
      - Purchase(FireworkToy)        -- buying a toy
      - Purchase(toy)                -- buying after saving money
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        char.Joy += 5
        if objects:
            item = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} bought a {item}.")
        return StoryFragment(f"{char.name} made a purchase.")
    
    # No character - used as concept
    if objects:
        item = _to_phrase(objects[0])
        return StoryFragment(f"purchasing a {item}", kernel_name="Purchase")
    
    return StoryFragment("purchasing", kernel_name="Purchase")


@REGISTRY.kernel("Capture")
def kernel_capture(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Capturing or catching something/someone.
    
    Patterns from sampling:
      - Capture(Fluffy)              -- capturing a character
      - Capture(Zookeeper)           -- someone being captured by another
      - Capture                      -- being caught
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    by = kwargs.get('by', None)
    
    if chars:
        target = chars[0]
        target.Fear += 8
        target.Sadness += 5
        
        if by:
            capturer = by if isinstance(by, Character) else _to_phrase(by)
            capturer_name = capturer.name if isinstance(by, Character) else capturer
            return StoryFragment(f"{target.name} was captured by {capturer_name}.")
        
        return StoryFragment(f"{target.name} was captured.")
    
    # No character
    if objects:
        thing = _to_phrase(objects[0])
        return StoryFragment(f"capturing {thing}", kernel_name="Capture")
    
    return StoryFragment("capture", kernel_name="Capture")


@REGISTRY.kernel("Drive")
def kernel_drive(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Driving a vehicle.
    
    Patterns from sampling:
      - Drive(truck)                 -- dreaming of driving
      - Drive(car)                   -- driving to a place
      - Try(Drive(car))              -- attempting to drive
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        if objects:
            vehicle = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} drove the {vehicle}.")
        return StoryFragment(f"{char.name} drove.")
    
    # No character - used as concept
    if objects:
        vehicle = _to_phrase(objects[0])
        return StoryFragment(f"driving the {vehicle}", kernel_name="Drive")
    
    return StoryFragment("driving", kernel_name="Drive")


@REGISTRY.kernel("Check")
def kernel_check(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Checking or examining something.
    
    Patterns from sampling:
      - Check(heartbeat)             -- checking heartbeat (playing doctor)
      - Check(mouth)                 -- checking for injury
      - Check(closet)                -- looking in a place
      - Check(Mommy)                 -- someone checking on a person
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        if objects:
            thing = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} checked the {thing}.")
        elif len(chars) > 1:
            # Checking on another character
            target = chars[1]
            return StoryFragment(f"{char.name} checked on {target.name}.")
        return StoryFragment(f"{char.name} checked.")
    
    # No character - used as concept
    if objects:
        thing = _to_phrase(objects[0])
        return StoryFragment(f"checking the {thing}", kernel_name="Check")
    
    return StoryFragment("checking", kernel_name="Check")


@REGISTRY.kernel("Put")
def kernel_put(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Putting or placing something somewhere.
    
    Common patterns:
      - Put(object, location)        -- placing object in location
      - Put(char, object)            -- character putting something
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    location = kwargs.get('location', kwargs.get('in', kwargs.get('on', None)))
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        if objects:
            item = _to_phrase(objects[0])
            if location:
                loc = _to_phrase(location)
                return StoryFragment(f"{char.name} put the {item} in the {loc}.")
            return StoryFragment(f"{char.name} put the {item} down.")
        return StoryFragment(f"{char.name} put it away.")
    
    # No character - used as concept
    if objects:
        item = _to_phrase(objects[0])
        if location:
            loc = _to_phrase(location)
            return StoryFragment(f"putting the {item} in the {loc}", kernel_name="Put")
        return StoryFragment(f"putting the {item}", kernel_name="Put")
    
    return StoryFragment("putting", kernel_name="Put")


# =============================================================================
# EMOTION/RESPONSE KERNELS
# =============================================================================

@REGISTRY.kernel("Reaction")
def kernel_reaction(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Reacting to something.
    
    Patterns from sampling:
      - Reaction(Mom, see=[ink, paper, hands], emotion=Surprised + Proud)
      - Reaction(Timmy, folder, Disgust)
      - Reaction(Lily, frown)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    emotion = kwargs.get('emotion', None)
    see = kwargs.get('see', None)
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        if emotion:
            # Has specific emotion
            emotion_phrase = _to_phrase(emotion)
            return StoryFragment(f"{char.name} reacted with {emotion_phrase}.")
        elif objects:
            # Reacting to something
            thing = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} reacted to the {thing}.")
        return StoryFragment(f"{char.name} reacted.")
    
    # No character - used as concept
    return StoryFragment("a reaction", kernel_name="Reaction")


# =============================================================================
# STATE/STATUS KERNELS
# =============================================================================

@REGISTRY.kernel("Missing")
def kernel_missing(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something is missing or lost.
    
    Patterns from sampling:
      - Missing(phone)               -- phone is missing
      - Missing(ornament)            -- ornament is missing (after lie)
      - Missing(necklace)            -- lost necklace
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    # Missing typically applies to objects
    if objects:
        item = _to_phrase(objects[0])
        if char:
            char.Sadness += 8
            char.Fear += 5
            return StoryFragment(f"{char.name} realized the {item} was missing.")
        return StoryFragment(f"the {item} was missing", kernel_name="Missing")
    
    # Generic missing
    if char:
        char.Sadness += 8
        return StoryFragment(f"{char.name} felt something was missing.")
    
    return StoryFragment("missing", kernel_name="Missing")


@REGISTRY.kernel("Caution")
def kernel_caution(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Warning someone to be careful.
    
    Patterns from sampling:
      - Caution(Mommy, about=toyairplane) -- warning about something
      - Caution(Mommy, Daddy, Lily)      -- parents warning child
      - Lesson(Caution)                  -- learning to be cautious
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    about = kwargs.get('about', None)
    
    if len(chars) >= 2:
        # One character warning another
        warner = chars[0]
        warned = chars[-1]  # Last character is the one being warned
        if about:
            thing = _to_phrase(about)
            return StoryFragment(f'{warner.name} warned {warned.name} to be careful with {thing}.')
        return StoryFragment(f'{warner.name} told {warned.name} to be careful.')
    elif chars:
        # Single character being cautious or warning
        char = chars[0]
        if about:
            thing = _to_phrase(about)
            return StoryFragment(f'{char.name} was cautious about {thing}.')
        if objects:
            thing = _to_phrase(objects[0])
            return StoryFragment(f'{char.name} warned about {thing}.')
        return StoryFragment(f'{char.name} was cautious.')
    
    # No character - used as concept
    if about:
        thing = _to_phrase(about)
        return StoryFragment(f"caution about {thing}", kernel_name="Caution")
    if objects:
        thing = _to_phrase(objects[0])
        return StoryFragment(f"caution about {thing}", kernel_name="Caution")
    
    return StoryFragment("caution", kernel_name="Caution")


# =============================================================================
# TEST HARNESS
# =============================================================================

def test_kernels():
    """Test the kernels in this pack."""
    from gen5 import Character
    
    print(f"\n{'='*70}")
    print("TESTING gen5k10.py KERNELS")
    print(f"{'='*70}\n")
    
    # Create test context
    ctx = StoryContext()
    
    # Test characters
    lily = Character("Lily", "girl")
    mom = Character("Mom", "mother")
    
    # Test Mix
    print("Mix:")
    print(f"  {kernel_mix(ctx, lily, 'flour', 'sugar')}")
    print(f"  {kernel_mix(ctx, 'bowl')}")
    
    # Test Avoid
    print("\nAvoid:")
    print(f"  {kernel_avoid(ctx, lily, 'dog')}")
    print(f"  {kernel_avoid(ctx, 'danger')}")
    
    # Test Purchase
    print("\nPurchase:")
    print(f"  {kernel_purchase(ctx, mom, 'toy')}")
    print(f"  {kernel_purchase(ctx, 'dress')}")
    
    # Test Capture
    print("\nCapture:")
    print(f"  {kernel_capture(ctx, lily)}")
    print(f"  {kernel_capture(ctx, lily, by=mom)}")
    
    # Test Drive
    print("\nDrive:")
    print(f"  {kernel_drive(ctx, mom, 'car')}")
    print(f"  {kernel_drive(ctx, 'truck')}")
    
    # Test Check
    print("\nCheck:")
    print(f"  {kernel_check(ctx, mom, 'closet')}")
    print(f"  {kernel_check(ctx, mom, lily)}")
    
    # Test Put
    print("\nPut:")
    print(f"  {kernel_put(ctx, lily, 'toy', location='box')}")
    print(f"  {kernel_put(ctx, 'book')}")
    
    # Test Reaction
    print("\nReaction:")
    print(f"  {kernel_reaction(ctx, mom, emotion='surprised')}")
    print(f"  {kernel_reaction(ctx, lily, 'noise')}")
    
    # Test Missing
    print("\nMissing:")
    print(f"  {kernel_missing(ctx, mom, 'phone')}")
    print(f"  {kernel_missing(ctx, 'necklace')}")
    
    # Test Caution
    print("\nCaution:")
    print(f"  {kernel_caution(ctx, mom, lily, about='jellyfish')}")
    print(f"  {kernel_caution(ctx, mom, 'danger')}")
    
    print(f"\n{'='*70}")
    print(f"REGISTERED KERNELS: {len(REGISTRY.kernels)}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    test_kernels()

