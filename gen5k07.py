"""
gen5k07.py - Additional Kernel Pack #07

This module extends gen5.py with additional kernel implementations.
Import this module after gen5 to register the new kernels.

=============================================================================
KERNELS IN THIS PACK:
=============================================================================

## Trait/Character Attribute Kernels (5)
- Obedient: Being obedient and following rules
- Cheerful: Having a cheerful, happy disposition
- Innocent: Pure, naive, without guile
- Disobedient: Not following rules/commands
- Muddy: State of being covered with mud

## Location/Setting Kernels (2)
- Park: A park location/setting
- Jungle: Jungle location/setting

## Action/Process Kernels (8)
- Wash: Washing/cleaning action
- Learning: Process of learning
- Teaching: Process of teaching/instructing
- Release: Releasing or letting go
- Song: Singing or a song
- Appreciation: Showing appreciation
- Responsibility: Taking responsibility
- Disobey: Act of disobeying

## Concept/Abstract Kernels (2)
- CharacterGroup: A group of characters
- Flight: Flying or flight

=============================================================================
USAGE PATTERNS FROM SAMPLING:
=============================================================================

Obedient:
  - Obedient(Spot) - as character trait transformation
  - Used in Cautionary tales as transformation outcome
  - Often paired with learning to follow rules

Park:
  - Park - as location/setting
  - Used in Routine(), Journey() as location parameter
  - Common setting for encounters and play

Wash:
  - Wash(hands) - washing specific things
  - Wash(Anna, Ben, with=soap) - characters washing
  - Often follows messy activities (mud, dirt)
  - Can be part of hygiene routines

Learning:
  - Learning(BigThings=Fun) - learning a concept
  - Learning(Friends+Timmy) - characters learning
  - Often appears as insight in Journey/Cautionary
  - Paired with Teaching kernel

Teaching:
  - Teaching(Mom, Tim, lesson=Careful) - teaching a lesson
  - Teaching(Mom, Acceptance) - parent teaching
  - Often involves wisdom transmission
  - Usually precedes or enables Learning

Cheerful:
  - Cheerful - as character trait
  - Bird1(Character, bird, Cheerful)
  - Often paired with Helpful, Friendly

Appreciation:
  - Appreciation(Mom, Sara) - someone appreciating
  - Appreciation(writing) - appreciating something
  - Often appears as insight/transformation
  - Increases Joy and Love

Responsibility:
  - Responsibility(Fix) - taking responsibility
  - Often appears in lessons
  - Paired with Calmness, Acceptance
  - Growth-oriented kernel

Release:
  - Release(loop) - releasing an object
  - Release(bear) - releasing a character
  - Release(balloon) - letting go unintentionally
  - Can be liberation or loss

Song:
  - Song(Bird, Lily) - character singing to another
  - Song(song) - singing action
  - Often brings joy, connection
  - Can have magical effects in stories

"""

from gen5 import (
    REGISTRY,
    StoryContext,
    StoryFragment,
    Character,
    NLGUtils,
    _to_phrase,
)


# =============================================================================
# TRAIT/CHARACTER ATTRIBUTE KERNELS
# =============================================================================

@REGISTRY.kernel("Obedient")
def kernel_obedient(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being obedient and following rules.
    
    Patterns:
      - Obedient(Spot) - character becomes obedient
      - Used as transformation in Cautionary tales
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Joy += 5
        return StoryFragment(f"{char.name} was obedient.")
    
    return StoryFragment("obedient", kernel_name="Obedient")


@REGISTRY.kernel("Cheerful")
def kernel_cheerful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Having a cheerful, happy disposition.
    
    Patterns:
      - Cheerful - as character trait
      - Often paired with Helpful, Friendly
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Joy += 8
        return StoryFragment(f"{char.name} was cheerful.")
    
    return StoryFragment("cheerful", kernel_name="Cheerful")


@REGISTRY.kernel("Innocent")
def kernel_innocent(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Pure, naive, without guile.
    
    Patterns:
      - Innocent - as character trait
      - Often used for children or victims
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        return StoryFragment(f"{char.name} was innocent.")
    
    return StoryFragment("innocent", kernel_name="Innocent")


@REGISTRY.kernel("Disobedient")
def kernel_disobedient(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Not following rules or commands.
    
    Patterns:
      - Disobedient - as negative character trait
      - Often precedes negative consequences
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Sadness += 3
        return StoryFragment(f"{char.name} was disobedient.")
    
    return StoryFragment("disobedient", kernel_name="Disobedient")


@REGISTRY.kernel("Muddy")
def kernel_muddy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    State of being covered with mud.
    
    Patterns:
      - Muddy - as character state
      - Spot(Character, dog, Playful + Muddy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        return StoryFragment(f"{char.name} was muddy.")
    
    return StoryFragment("muddy", kernel_name="Muddy")


# =============================================================================
# LOCATION/SETTING KERNELS
# =============================================================================

@REGISTRY.kernel("Park")
def kernel_park(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A park location/setting.
    
    Patterns:
      - Park - as location
      - Routine(Lily, Mommy, Park)
      - setting=Park
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{NLGUtils.join_list([c.name for c in chars])} went to the park.")
    
    return StoryFragment("the park", kernel_name="Park")


@REGISTRY.kernel("Jungle")
def kernel_jungle(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Jungle location/setting.
    
    Patterns:
      - Jungle - as exotic location
      - Adventure(Jungle, ...)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{NLGUtils.join_list([c.name for c in chars])} went to the jungle.")
    
    return StoryFragment("the jungle", kernel_name="Jungle")


# =============================================================================
# ACTION/PROCESS KERNELS
# =============================================================================

@REGISTRY.kernel("Wash")
def kernel_wash(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Washing/cleaning action.
    
    Patterns:
      - Wash(hands) - washing specific things
      - Wash(Anna, Ben, with=soap) - characters washing
      - Wash(beans) - washing objects
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    with_what = kwargs.get('with', None)
    target = kwargs.get('target', None)
    
    # If target specified (like Wash(rain, target=Fur))
    if target:
        target_str = _to_phrase(target)
        agent = chars[0].name if chars else objects[0] if objects else "something"
        return StoryFragment(f"{agent} washed {target_str}.")
    
    # Characters washing themselves
    if chars:
        char_names = NLGUtils.join_list([c.name for c in chars])
        if with_what:
            return StoryFragment(f"{char_names} washed with {with_what}.")
        return StoryFragment(f"{char_names} washed up.")
    
    # Washing objects
    if objects:
        obj = objects[0]
        return StoryFragment(f"The {obj} was washed.")
    
    return StoryFragment("washing", kernel_name="Wash")


@REGISTRY.kernel("Learning")
def kernel_learning(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Process of learning.
    
    Patterns:
      - Learning(BigThings=Fun) - learning a concept
      - Learning(Friends+Timmy) - characters learning
      - Often appears as insight
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # Learning a concept (from kwargs)
    if kwargs:
        concept = list(kwargs.keys())[0]
        value = kwargs[concept]
        return StoryFragment(f"learning that {concept} is {_to_phrase(value)}.")
    
    # Characters learning
    if chars:
        char_names = NLGUtils.join_list([c.name for c in chars])
        for char in chars:
            char.Joy += 3
        return StoryFragment(f"{char_names} learned something important.")
    
    # Abstract learning
    if objects:
        return StoryFragment(f"learning about {objects[0]}.")
    
    return StoryFragment("learning", kernel_name="Learning")


@REGISTRY.kernel("Teaching")
def kernel_teaching(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Process of teaching/instructing.
    
    Patterns:
      - Teaching(Mom, Tim, lesson=Careful) - teaching a lesson
      - Teaching(Mom, Acceptance) - teaching a concept
      - Teaching(CircleOfLife) - teaching about concept
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    lesson = kwargs.get('lesson', None)
    method = kwargs.get('method', None)
    
    # Teacher teaching student a lesson
    if len(chars) >= 2:
        teacher = chars[0]
        student = chars[1]
        if lesson:
            lesson_str = _to_phrase(lesson)
            return StoryFragment(f"{teacher.name} taught {student.name} about {lesson_str}.")
        return StoryFragment(f"{teacher.name} taught {student.name}.")
    
    # Single character teaching
    if chars:
        teacher = chars[0]
        if lesson:
            lesson_str = _to_phrase(lesson)
            return StoryFragment(f"{teacher.name} taught about {lesson_str}.")
        return StoryFragment(f"{teacher.name} taught a lesson.")
    
    # Teaching a concept
    if objects:
        return StoryFragment(f"teaching about {objects[0]}.")
    
    return StoryFragment("teaching", kernel_name="Teaching")


@REGISTRY.kernel("Release")
def kernel_release(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Releasing or letting go.
    
    Patterns:
      - Release(loop) - releasing an object
      - Release(bear) - releasing a character
      - Release(balloon) - letting go unintentionally
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # Releasing a character
    if chars:
        char = chars[0]
        char.Joy += 10
        return StoryFragment(f"{char.name} was released and set free.")
    
    # Releasing an object
    if objects:
        obj = objects[0]
        return StoryFragment(f"The {obj} was released.")
    
    return StoryFragment("released", kernel_name="Release")


@REGISTRY.kernel("Song")
def kernel_song(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Singing or a song.
    
    Patterns:
      - Song(Bird, Lily) - character singing to another
      - Song(song) - singing action
      - Often brings joy
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # Character singing to another
    if len(chars) >= 2:
        singer = chars[0]
        listener = chars[1]
        singer.Joy += 5
        listener.Joy += 5
        return StoryFragment(f"{singer.name} sang a beautiful song for {listener.name}.")
    
    # Single character singing
    if chars:
        char = chars[0]
        char.Joy += 5
        return StoryFragment(f"{char.name} sang a happy song.")
    
    # Song as object/concept
    if objects:
        return StoryFragment(f"singing the {objects[0]}.")
    
    return StoryFragment("a song", kernel_name="Song")


@REGISTRY.kernel("Appreciation")
def kernel_appreciation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Showing appreciation.
    
    Patterns:
      - Appreciation(Mom, Sara) - someone appreciating another
      - Appreciation(writing) - appreciating something
      - Often appears as insight/transformation
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # One character appreciating another
    if len(chars) >= 2:
        appreciator = chars[0]
        appreciated = chars[1]
        appreciator.Joy += 5
        appreciator.Love += 5
        appreciated.Joy += 8
        return StoryFragment(f"{appreciator.name} showed appreciation for {appreciated.name}.")
    
    # Character appreciating something
    if chars:
        char = chars[0]
        char.Joy += 5
        if objects:
            return StoryFragment(f"{char.name} appreciated {objects[0]}.")
        return StoryFragment(f"{char.name} felt appreciation.")
    
    # Appreciating a concept
    if objects:
        return StoryFragment(f"appreciation for {objects[0]}.")
    
    return StoryFragment("appreciation", kernel_name="Appreciation")


@REGISTRY.kernel("Responsibility")
def kernel_responsibility(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Taking responsibility.
    
    Patterns:
      - Responsibility(Fix) - responsibility to fix
      - Responsibility - as lesson or transformation
      - Growth-oriented kernel
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # Character taking responsibility
    if chars:
        char = chars[0]
        char.Joy += 3
        if objects:
            return StoryFragment(f"{char.name} took responsibility for {objects[0]}.")
        return StoryFragment(f"{char.name} learned to take responsibility.")
    
    # Responsibility for something
    if objects:
        return StoryFragment(f"responsibility for {objects[0]}.")
    
    return StoryFragment("responsibility", kernel_name="Responsibility")


@REGISTRY.kernel("Disobey")
def kernel_disobey(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Act of disobeying.
    
    Patterns:
      - Disobey - as negative action in Cautionary tales
      - Usually leads to negative consequences
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Sadness += 5
        char.Fear += 3
        return StoryFragment(f"{char.name} disobeyed.")
    
    return StoryFragment("disobeying", kernel_name="Disobey")


# =============================================================================
# CONCEPT/ABSTRACT KERNELS
# =============================================================================

@REGISTRY.kernel("CharacterGroup")
def kernel_character_group(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A group of characters.
    
    Patterns:
      - CharacterGroup - representing multiple characters as a unit
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        char_names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{char_names} formed a group.")
    
    if objects:
        return StoryFragment(f"a group of {objects[0]}.")
    
    return StoryFragment("a group", kernel_name="CharacterGroup")


@REGISTRY.kernel("Flight")
def kernel_flight(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Flying or flight.
    
    Patterns:
      - Flight - flying action
      - Often used with birds or magical creatures
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Joy += 8
        return StoryFragment(f"{char.name} took flight and soared through the air.")
    
    return StoryFragment("flight", kernel_name="Flight")


# =============================================================================
# TEST BLOCK - Run when this file is executed directly
# =============================================================================

if __name__ == "__main__":
    print("gen5k07.py - Additional Kernel Pack #07")
    print("=" * 50)
    print(f"Total kernels in registry: {len(REGISTRY.kernels)}")
    
    # List kernels from this pack
    pack_kernels = [
        "Obedient", "Cheerful", "Innocent", "Disobedient", "Muddy",
        "Park", "Jungle",
        "Wash", "Learning", "Teaching", "Release", "Song", 
        "Appreciation", "Responsibility", "Disobey",
        "CharacterGroup", "Flight"
    ]
    
    implemented = sum(1 for k in pack_kernels if k in REGISTRY.kernels)
    print(f"Kernels defined in this pack: {len(pack_kernels)}")
    print(f"Successfully registered: {implemented}")
    
    # Show sample kernels
    print("\nSample kernels from this pack:")
    for kernel_name in ["Obedient", "Park", "Wash", "Learning", "Song", "Appreciation"][:6]:
        if kernel_name in REGISTRY.kernels:
            print(f"  ✓ {kernel_name}")
    
    print("\n" + "=" * 50)
    print("✅ Kernel pack loaded successfully!")
    print("=" * 50)

