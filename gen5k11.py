"""
gen5k11.py - Additional Kernel Pack #11

This module extends gen5.py with additional kernel implementations
focused on high-usage missing kernels from coverage analysis (batch 2).

=============================================================================
KERNELS IN THIS PACK (with usage patterns from sampling):
=============================================================================

## Action Kernels
- Hear(char, sound)                -- hearing something
- Stop(action)                     -- stopping an action
- Choose(char, choice)             -- choosing/selecting something
- Recall(char, memory)             -- remembering something
- Disregard(char, warning)         -- ignoring/disregarding advice

## Emotion/Experience Kernels
- Enjoy(char, activity)            -- enjoying something
- Continuation(activity)           -- continuing an activity

## Story/Play Kernels
- Pirates                          -- pretend play as pirates
- Explorers                        -- pretend play as explorers

## Safety/Warning Kernels
- MatchesDanger                    -- danger of matches lesson
- SafeLight(flashlight/lantern)    -- safe lighting alternatives

## Object Kernels
- Water(bucket)                    -- water for putting out fires

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

@REGISTRY.kernel("Hear")
def kernel_hear(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Hearing something.
    
    Patterns from sampling:
      - Hear(wind)                   -- hearing wind
      - Hear(leaves)                 -- hearing leaves
      - Hear(song)                   -- hearing a song
      - Hear(house, Sing(Lily))      -- place hearing something
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        if objects:
            sound = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} heard {sound}.")
        return StoryFragment(f"{char.name} heard something.")
    
    # No character - used as concept
    if objects:
        sound = _to_phrase(objects[0])
        return StoryFragment(f"hearing {sound}", kernel_name="Hear")
    
    return StoryFragment("hearing", kernel_name="Hear")


@REGISTRY.kernel("Stop")
def kernel_stop(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Stopping an action or activity.
    
    Patterns from sampling:
      - Stop(Play(drum))             -- stopping playing
      - Stop(watch)                  -- stopping watching
      - Stop(bug)                    -- stopping a bug (making it stop)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    action = kwargs.get('action', None)
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        if action:
            action_phrase = _action_to_phrase(action)
            return StoryFragment(f"{char.name} stopped {action_phrase}.")
        elif objects:
            thing = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} stopped {thing}.")
        return StoryFragment(f"{char.name} stopped.")
    
    # No character - stopping something
    if objects:
        thing = _to_phrase(objects[0])
        return StoryFragment(f"stopping {thing}", kernel_name="Stop")
    
    return StoryFragment("stopped", kernel_name="Stop")


@REGISTRY.kernel("Choose")
def kernel_choose(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Choosing or selecting something.
    
    Patterns from sampling:
      - Choose(candle, scent=flower) -- choosing a specific item
      - Choose(cheap)                -- choosing the cheap option
      - Choose(Lily, Wash(dishes))   -- character choosing an action
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        char.Joy += 3  # Small positive for making a decision
        if objects:
            choice = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} chose {choice}.")
        return StoryFragment(f"{char.name} made a choice.")
    
    # No character - used as concept
    if objects:
        choice = _to_phrase(objects[0])
        return StoryFragment(f"choosing {choice}", kernel_name="Choose")
    
    return StoryFragment("a choice", kernel_name="Choose")


@REGISTRY.kernel("Recall")
def kernel_recall(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Remembering or recalling something.
    
    Patterns from sampling:
      - Recall(Mom, advice=If(Caught, Wiggle)) -- recalling advice
      - Recall(Lily, past=Noise(library))      -- remembering past event
      - Recall(Abracadabra)                    -- remembering a word
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    advice = kwargs.get('advice', None)
    past = kwargs.get('past', None)
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        if advice:
            advice_phrase = _to_phrase(advice)
            return StoryFragment(f"{char.name} remembered the advice: {advice_phrase}.")
        elif past:
            past_phrase = _to_phrase(past)
            return StoryFragment(f"{char.name} recalled {past_phrase}.")
        elif objects:
            thing = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} remembered {thing}.")
        return StoryFragment(f"{char.name} remembered.")
    
    # No character - used as concept
    if objects:
        thing = _to_phrase(objects[0])
        return StoryFragment(f"recalling {thing}", kernel_name="Recall")
    
    return StoryFragment("remembering", kernel_name="Recall")


@REGISTRY.kernel("Disregard")
def kernel_disregard(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Ignoring or disregarding advice/warnings.
    
    Patterns from sampling:
      - Disregard(Tom)               -- Tom disregards warning
      - Conflict(Nervous(Lily) + Disregard(Tom))  -- tension from disregarding
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        char.Anger += 3  # Slight increase in impulsiveness/defiance
        if objects:
            thing = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} disregarded {thing}.")
        return StoryFragment(f"{char.name} ignored the warning.")
    
    # No character - used as concept
    if objects:
        thing = _to_phrase(objects[0])
        return StoryFragment(f"disregarding {thing}", kernel_name="Disregard")
    
    return StoryFragment("disregard", kernel_name="Disregard")


# =============================================================================
# EMOTION/EXPERIENCE KERNELS
# =============================================================================

@REGISTRY.kernel("Enjoy")
def kernel_enjoy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Enjoying something.
    
    Patterns from sampling:
      - Enjoy(peach)                 -- enjoying eating something
      - Enjoy(Lily, Lemonade)        -- character enjoying something
      - Enjoy + Safe                 -- enjoying the park (safe to enjoy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        char.Joy += 8
        if objects:
            thing = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} enjoyed {thing}.")
        return StoryFragment(f"{char.name} enjoyed it.")
    
    # No character - used as concept
    if objects:
        thing = _to_phrase(objects[0])
        return StoryFragment(f"enjoying {thing}", kernel_name="Enjoy")
    
    return StoryFragment("enjoyment", kernel_name="Enjoy")


@REGISTRY.kernel("Continuation")
def kernel_continuation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Continuing an activity or action.
    
    Patterns from sampling:
      - Continuation(Walk, Lily, teddy, Happy)    -- continuing to walk
      - Continuation(Sue, action=Add(drawing))    -- continuing an action
      - Continuation(Reading(anotherBook))        -- continuing reading
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    action = kwargs.get('action', None)
    state = kwargs.get('state', None)
    
    char = _get_default_actor(ctx, chars)
    
    if char:
        if action:
            action_phrase = _action_to_phrase(action)
            return StoryFragment(f"{char.name} continued {action_phrase}.")
        elif objects:
            activity = _to_phrase(objects[0])
            return StoryFragment(f"{char.name} continued {activity}.")
        return StoryFragment(f"{char.name} continued on.")
    
    # No character - used as concept
    if objects:
        activity = _to_phrase(objects[0])
        return StoryFragment(f"continuing {activity}", kernel_name="Continuation")
    
    return StoryFragment("continuing", kernel_name="Continuation")


# =============================================================================
# STORY/PLAY KERNELS
# =============================================================================

@REGISTRY.kernel("Pirates")
def kernel_pirates(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Pretend play as pirates.
    
    Patterns from sampling:
      - Play(Pirates, Explorers, Lily, Tom)    -- playing pirates
      - Transformation(Play(Pirates) + SafeLight)  -- continuing pirate play
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        for char in chars:
            char.Joy += 10
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} pretended to be pirates.")
    
    return StoryFragment("playing pirates", kernel_name="Pirates")


@REGISTRY.kernel("Explorers")
def kernel_explorers(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Pretend play as explorers.
    
    Patterns from sampling:
      - Play(Pirates, Explorers, Lily, Tom)    -- playing explorers
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        for char in chars:
            char.Joy += 10
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} pretended to be explorers.")
    
    return StoryFragment("playing explorers", kernel_name="Explorers")


# =============================================================================
# SAFETY/WARNING KERNELS
# =============================================================================

@REGISTRY.kernel("MatchesDanger")
def kernel_matches_danger(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Lesson about the danger of matches.
    
    Patterns from sampling:
      - Lesson(MatchesDanger)    -- learning about match danger
    """
    return StoryFragment("the danger of playing with matches", kernel_name="MatchesDanger")


@REGISTRY.kernel("SafeLight")
def kernel_safe_light(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Safe lighting alternatives (flashlight, lantern, etc).
    
    Patterns from sampling:
      - Transformation(Play(Pirates) + SafeLight([flashlight, lantern]))
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    lights = objects if objects else ['flashlight']
    light_list = NLGUtils.join_list(lights)
    
    if chars:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} used a safe {light_list} instead.")
    
    return StoryFragment(f"using a safe {light_list}", kernel_name="SafeLight")


# =============================================================================
# OBJECT KERNELS
# =============================================================================

@REGISTRY.kernel("Water")
def kernel_water(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Water (for drinking, washing, putting out fires, etc).
    
    Patterns from sampling:
      - Rescue(Mom, method=Water(bucket))    -- using water to rescue
      - Water(bucket)                         -- water in a bucket
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    container = objects[0] if objects else None
    
    if chars:
        char = chars[0]
        if container:
            return StoryFragment(f"{char.name} got some water in a {container}.")
        return StoryFragment(f"{char.name} got some water.")
    
    if container:
        return StoryFragment(f"water in a {container}", kernel_name="Water")
    
    return StoryFragment("water", kernel_name="Water")


# =============================================================================
# TEST HARNESS
# =============================================================================

def test_kernels():
    """Test the kernels in this pack."""
    from gen5 import Character
    
    print(f"\n{'='*70}")
    print("TESTING gen5k11.py KERNELS")
    print(f"{'='*70}\n")
    
    # Create test context
    ctx = StoryContext()
    
    # Test characters
    lily = Character("Lily", "girl")
    mom = Character("Mom", "mother")
    
    # Test Hear
    print("Hear:")
    print(f"  {kernel_hear(ctx, lily, 'song')}")
    print(f"  {kernel_hear(ctx, 'wind')}")
    
    # Test Stop
    print("\nStop:")
    print(f"  {kernel_stop(ctx, lily, 'playing')}")
    print(f"  {kernel_stop(ctx, 'noise')}")
    
    # Test Choose
    print("\nChoose:")
    print(f"  {kernel_choose(ctx, lily, 'candle')}")
    print(f"  {kernel_choose(ctx, 'cheap')}")
    
    # Test Recall
    print("\nRecall:")
    print(f"  {kernel_recall(ctx, lily, advice='be careful')}")
    print(f"  {kernel_recall(ctx, 'password')}")
    
    # Test Enjoy
    print("\nEnjoy:")
    print(f"  {kernel_enjoy(ctx, lily, 'cake')}")
    print(f"  {kernel_enjoy(ctx, 'sunshine')}")
    
    # Test Continuation
    print("\nContinuation:")
    print(f"  {kernel_continuation(ctx, lily, 'walking')}")
    print(f"  {kernel_continuation(ctx, 'playing')}")
    
    print(f"\n{'='*70}")
    print(f"REGISTERED KERNELS: {len(REGISTRY.kernels)}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    test_kernels()

