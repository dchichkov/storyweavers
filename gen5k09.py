#!/usr/bin/env python3
"""
gen5k09.py - Additional Kernel Pack #09

Implements high-frequency missing kernels from data01.kernels.jsonl:
- Follow (832 usages): Following a character/object
- Stuck (811 usages): Being stuck or trapped
- Change (787 usages): Transformation or change
- Thanks (781 usages): Expressing gratitude  
- Spill (778 usages): Spilling liquids/objects
- Recovery (771 usages): Recovering from illness/setback
- Pretend (761 usages): Pretend play
- Reach (737 usages): Reaching for something

Plus additional missing kernels from data00/data01.
"""

from gen5 import (
    REGISTRY,
    StoryContext,
    StoryFragment,
    Character,
    NLGUtils,
    _to_phrase,
    _get_default_actor,
)


@REGISTRY.kernel("Follow")
def kernel_follow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character follows someone or something.
    
    Patterns from sampling:
      - Follow(butterfly)                  -- following an object
      - Follow(Goat, target=butterfly)     -- character follows target
      - Follow(butterfly) + Cross(structure) -- following as part of journey
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    target = kwargs.get('target', '')
    
    follower = chars[0] if chars else ctx.current_focus
    thing = target or (objects[0] if objects else '')
    
    if follower:
        if thing:
            follower.Joy += 3  # Following something is slightly positive/engaging
            return StoryFragment(f"{follower.name} followed the {_to_phrase(thing)}.")
        return StoryFragment(f"{follower.name} followed along.")
    
    if thing:
        return StoryFragment(f"followed the {_to_phrase(thing)}", kernel_name="Follow")
    
    return StoryFragment("followed", kernel_name="Follow")


@REGISTRY.kernel("Stuck")
def kernel_stuck(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character or object is stuck.
    
    Common patterns:
      - Stuck(car)            -- object is stuck
      - Stuck(Tim, in=mud)    -- character stuck in something
      - Stuck(ball, where=tree) -- object stuck somewhere
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    location = kwargs.get('in', kwargs.get('where', ''))
    
    if chars:
        char = chars[0]
        char.Sadness += 8
        char.Fear += 5
        if location:
            return StoryFragment(f"{char.name} was stuck in the {_to_phrase(location)}.")
        return StoryFragment(f"{char.name} was stuck.")
    
    thing = objects[0] if objects else 'something'
    if location:
        return StoryFragment(f"the {thing} was stuck in the {_to_phrase(location)}", kernel_name="Stuck")
    return StoryFragment(f"the {thing} was stuck", kernel_name="Stuck")


@REGISTRY.kernel("Change")
def kernel_change(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something changes or transforms.
    
    Patterns:
      - Change(weather)           -- thing changes
      - Change(Tim, state=happy)  -- character changes state
      - Change(color, to=blue)    -- explicit transformation
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    state = kwargs.get('state', kwargs.get('to', ''))
    
    if chars:
        char = chars[0]
        if state:
            return StoryFragment(f"{char.name} changed and became {_to_phrase(state)}.")
        return StoryFragment(f"{char.name} changed.")
    
    thing = objects[0] if objects else 'things'
    if state:
        return StoryFragment(f"the {thing} changed to {_to_phrase(state)}", kernel_name="Change")
    return StoryFragment(f"the {thing} changed", kernel_name="Change")


@REGISTRY.kernel("Thanks")
def kernel_thanks(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character expresses thanks/gratitude.
    
    Patterns:
      - Thanks(Tim)           -- Tim says thanks
      - Thanks(Tim, to=Mom)   -- Tim thanks Mom
      - Thanks(Mom, for=help) -- thanks for something
    """
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', None)
    for_what = kwargs.get('for', '')
    
    if chars:
        char = chars[0]
        char.Joy += 8
        char.Love += 5
        
        if to and for_what:
            return StoryFragment(f"{char.name} thanked {_to_phrase(to)} for the {_to_phrase(for_what)}.")
        elif to:
            return StoryFragment(f"{char.name} said thank you to {_to_phrase(to)}.")
        elif for_what:
            return StoryFragment(f"{char.name} was thankful for the {_to_phrase(for_what)}.")
        return StoryFragment(f"{char.name} said thank you.")
    
    return StoryFragment("there was gratitude", kernel_name="Thanks")


@REGISTRY.kernel("Spill")
def kernel_spill(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Spilling a liquid or objects.
    
    Patterns:
      - Spill(juice)              -- spilling something
      - Spill(Tim, object=milk)   -- character spills something
      - Spill(water, on=floor)    -- spill on location
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    obj = kwargs.get('object', '')
    location = kwargs.get('on', kwargs.get('onto', ''))
    
    if chars:
        char = chars[0]
        char.Sadness += 5
        thing = obj or (objects[0] if objects else 'something')
        
        if location:
            return StoryFragment(f"{char.name} spilled the {thing} on the {_to_phrase(location)}.")
        return StoryFragment(f"{char.name} spilled the {thing}.")
    
    thing = obj or (objects[0] if objects else 'something')
    if location:
        return StoryFragment(f"the {thing} spilled on the {_to_phrase(location)}", kernel_name="Spill")
    return StoryFragment(f"the {thing} spilled", kernel_name="Spill")


@REGISTRY.kernel("Recovery")
def kernel_recovery(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Recovering from illness, injury, or setback.
    
    Patterns:
      - Recovery(Tim)                 -- character recovers
      - Recovery(Tim, from=illness)   -- recovery from specific condition
      - Recovery(process=rest)        -- recovery process
    """
    chars = [a for a in args if isinstance(a, Character)]
    from_what = kwargs.get('from', '')
    process = kwargs.get('process', '')
    
    if chars:
        char = chars[0]
        char.Joy += 10
        char.Sadness -= 10
        
        if from_what and process:
            return StoryFragment(f"{char.name} recovered from the {_to_phrase(from_what)} by {_to_phrase(process)}.")
        elif from_what:
            return StoryFragment(f"{char.name} recovered from the {_to_phrase(from_what)}.")
        elif process:
            return StoryFragment(f"{char.name} recovered by {_to_phrase(process)}.")
        return StoryFragment(f"{char.name} got better.")
    
    return StoryFragment("recovery", kernel_name="Recovery")


@REGISTRY.kernel("Pretend")
def kernel_pretend(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Pretend play or imagination.
    
    Patterns:
      - Pretend(pirate)              -- pretending to be something
      - Pretend(Tim, role=doctor)    -- character pretends to be role
      - Pretend(Tim, action=fly)     -- character pretends to do action
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    role = kwargs.get('role', kwargs.get('as', ''))
    action = kwargs.get('action', '')
    
    if chars:
        char = chars[0]
        char.Joy += 10  # Pretend play is fun!
        
        if role:
            return StoryFragment(f"{char.name} pretended to be {NLGUtils.article(_to_phrase(role))} {_to_phrase(role)}.")
        elif action:
            return StoryFragment(f"{char.name} pretended to {_to_phrase(action)}.")
        elif objects:
            return StoryFragment(f"{char.name} pretended to be {NLGUtils.article(objects[0])} {objects[0]}.")
        return StoryFragment(f"{char.name} was pretending.")
    
    if objects:
        return StoryFragment(f"pretended to be {NLGUtils.article(objects[0])} {objects[0]}", kernel_name="Pretend")
    return StoryFragment("pretend play", kernel_name="Pretend")


@REGISTRY.kernel("Reach")
def kernel_reach(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Reaching for or toward something.
    
    Patterns:
      - Reach(toy)                -- reaching for object
      - Reach(Tim, target=shelf)  -- character reaches for target
      - Reach(high)               -- reaching high/far
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    target = kwargs.get('target', kwargs.get('for', ''))
    
    reacher = chars[0] if chars else ctx.current_focus
    thing = target or (objects[0] if objects else 'something')
    
    if reacher:
        return StoryFragment(f"{reacher.name} reached for the {_to_phrase(thing)}.")
    
    return StoryFragment(f"reached for the {_to_phrase(thing)}", kernel_name="Reach")


# Additional missing kernels from data00/data01

@REGISTRY.kernel("Mess")
def kernel_mess(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Making or encountering a mess.
    
    Patterns:
      - Mess(dirt)           -- mess of something
      - Mess(Tim, made=toys) -- character makes mess
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    made = kwargs.get('made', '')
    
    if chars:
        char = chars[0]
        char.Sadness += 5
        thing = made or (objects[0] if objects else 'things')
        return StoryFragment(f"{char.name} made a mess with the {_to_phrase(thing)}.")
    
    thing = made or (objects[0] if objects else 'things')
    return StoryFragment(f"there was a mess of {_to_phrase(thing)}", kernel_name="Mess")


@REGISTRY.kernel("Cleanup")
def kernel_cleanup(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Cleaning up a mess.
    
    Patterns from sampling:
      - Cleanup(Tim, tool=shovel, process=scoop(dirt) + replace(earth))
      - Cleanup(Tim + Sam, result=Sadness + Unhappy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    tool = kwargs.get('tool', '')
    process = kwargs.get('process', '')
    
    if len(chars) > 1:
        # Multiple characters cleaning up together
        names = NLGUtils.join_list([c.name for c in chars])
        for c in chars:
            c.Joy -= 3  # Cleanup is not that fun
        if tool:
            return StoryFragment(f"{names} cleaned up with {NLGUtils.article(tool)} {tool}.")
        return StoryFragment(f"{names} cleaned up the mess.")
    elif chars:
        char = chars[0]
        char.Joy -= 3  # Cleanup is tedious
        if tool and process:
            return StoryFragment(f"{char.name} cleaned up using {NLGUtils.article(tool)} {tool} to {_to_phrase(process)}.")
        elif tool:
            return StoryFragment(f"{char.name} got {NLGUtils.article(tool)} {tool} and cleaned up.")
        return StoryFragment(f"{char.name} cleaned everything up.")
    
    return StoryFragment("cleanup", kernel_name="Cleanup")


@REGISTRY.kernel("Boredom")
def kernel_boredom(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    State of boredom.
    
    Patterns:
      - Boredom(Tim, cause=Old(toys) + Bored)
    """
    chars = [a for a in args if isinstance(a, Character)]
    cause = kwargs.get('cause', '')
    
    if chars:
        char = chars[0]
        char.Joy -= 10
        char.Sadness += 5
        if cause:
            return StoryFragment(f"{char.name} was bored because of {_to_phrase(cause)}.")
        return StoryFragment(f"{char.name} felt so bored.")
    
    return StoryFragment("boredom", kernel_name="Boredom")


@REGISTRY.kernel("Unhappy")
def kernel_unhappy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is unhappy."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 10
        chars[0].Joy -= 10
        return StoryFragment(f"{chars[0].name} was unhappy.")
    
    return StoryFragment("unhappy", kernel_name="Unhappy")


@REGISTRY.kernel("Guilt")
def kernel_guilt(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling guilt or remorse.
    
    Patterns:
      - Guilt(Tim)              -- feeling guilty
      - Guilt(Tim, about=lie)   -- guilt about something
    """
    chars = [a for a in args if isinstance(a, Character)]
    about = kwargs.get('about', kwargs.get('for', ''))
    
    if chars:
        char = chars[0]
        char.Sadness += 10
        if about:
            return StoryFragment(f"{char.name} felt guilty about {_to_phrase(about)}.")
        return StoryFragment(f"{char.name} felt guilty.")
    
    return StoryFragment("guilt", kernel_name="Guilt")


@REGISTRY.kernel("Empathy")
def kernel_empathy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Showing empathy or understanding.
    
    Patterns:
      - Empathy(Mom, for=Tim)     -- empathy toward someone
      - Empathy(Tim)              -- character shows empathy
    """
    chars = [a for a in args if isinstance(a, Character)]
    for_who = kwargs.get('for', kwargs.get('toward', ''))
    
    if chars:
        char = chars[0]
        char.Love += 8
        char.Joy += 5
        if for_who:
            return StoryFragment(f"{char.name} felt empathy for {_to_phrase(for_who)}.")
        return StoryFragment(f"{char.name} showed understanding and kindness.")
    
    return StoryFragment("empathy", kernel_name="Empathy")


@REGISTRY.kernel("Unexpected")
def kernel_unexpected(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something unexpected happens.
    
    Patterns:
      - Unexpected(event)           -- unexpected thing
      - Unexpected(storm)           -- unexpected event
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    event = objects[0] if objects else 'something'
    
    return StoryFragment(f"unexpectedly, {_to_phrase(event)} happened", kernel_name="Unexpected")


@REGISTRY.kernel("Slide")
def kernel_slide(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Sliding down or across something.
    
    Patterns:
      - Slide(Tim)             -- character slides
      - Slide(Tim, down=hill)  -- slide down something
    """
    chars = [a for a in args if isinstance(a, Character)]
    down = kwargs.get('down', kwargs.get('on', ''))
    
    if chars:
        char = chars[0]
        char.Joy += 8
        if down:
            return StoryFragment(f"{char.name} slid down the {_to_phrase(down)}.")
        return StoryFragment(f"{char.name} went down the slide.")
    
    return StoryFragment("sliding", kernel_name="Slide")


@REGISTRY.kernel("Sweet")
def kernel_sweet(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sweet taste or personality."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} was sweet")
    
    if objects:
        return StoryFragment(f"the {objects[0]} was sweet", kernel_name="Sweet")
    
    return StoryFragment("sweet", kernel_name="Sweet")


@REGISTRY.kernel("Shared")
def kernel_shared(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Sharing something.
    
    Patterns:
      - Shared(toy)              -- sharing an object
      - Shared(Tim, toy, with=Sue) -- character shares with someone
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    with_who = kwargs.get('with', '')
    
    if chars:
        char = chars[0]
        char.Joy += 8
        char.Love += 5
        thing = objects[0] if objects else 'something'
        if with_who:
            return StoryFragment(f"{char.name} shared the {thing} with {_to_phrase(with_who)}.")
        return StoryFragment(f"{char.name} shared the {thing}.")
    
    thing = objects[0] if objects else 'something'
    return StoryFragment(f"sharing the {thing}", kernel_name="Shared")


@REGISTRY.kernel("Scary")
def kernel_scary(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Something is scary."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Fear += 12
        return StoryFragment(f"{chars[0].name} was scared")
    
    if objects:
        return StoryFragment(f"the {objects[0]} was scary", kernel_name="Scary")
    
    return StoryFragment("scary", kernel_name="Scary")


@REGISTRY.kernel("Social")
def kernel_social(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Social interaction or being social."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 6
        return StoryFragment(f"{chars[0].name} enjoyed being social")
    
    return StoryFragment("social", kernel_name="Social")


@REGISTRY.kernel("Warmth")
def kernel_warmth(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Feeling or experiencing warmth."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 8
        return StoryFragment(f"{chars[0].name} felt the warmth")
    
    return StoryFragment("warmth", kernel_name="Warmth")


@REGISTRY.kernel("Bad")
def kernel_bad(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Something bad or negative."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Sadness += 8
        return StoryFragment(f"{chars[0].name} felt bad")
    
    if objects:
        return StoryFragment(f"the {objects[0]} was bad", kernel_name="Bad")
    
    return StoryFragment("bad", kernel_name="Bad")


@REGISTRY.kernel("Reassurance")
def kernel_reassurance(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Providing reassurance or comfort.
    
    Patterns:
      - Reassurance(Mom, to=Tim)   -- someone reassures another
      - Reassurance(Tim)           -- character receives reassurance
    """
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', '')
    
    if len(chars) >= 2:
        giver = chars[0]
        receiver = chars[1]
        receiver.Fear -= 10
        receiver.Joy += 8
        return StoryFragment(f"{giver.name} reassured {receiver.name} that everything would be okay.")
    elif chars:
        char = chars[0]
        char.Fear -= 10
        char.Joy += 8
        if to:
            return StoryFragment(f"{char.name} reassured {_to_phrase(to)} that everything would be okay.")
        return StoryFragment(f"{char.name} received reassurance.")
    
    return StoryFragment("reassurance", kernel_name="Reassurance")


@REGISTRY.kernel("Scream")
def kernel_scream(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character screams."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 15
        return StoryFragment(f"{chars[0].name} screamed!")
    
    return StoryFragment("a scream", kernel_name="Scream")


@REGISTRY.kernel("Group")
def kernel_group(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """A group or gathering."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        for c in chars:
            c.Joy += 5
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} formed a group")
    
    return StoryFragment("a group gathered", kernel_name="Group")


@REGISTRY.kernel("Pretty")
def kernel_pretty(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Something is pretty or beautiful."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} was pretty")
    
    if objects:
        return StoryFragment(f"the {objects[0]} was pretty", kernel_name="Pretty")
    
    return StoryFragment("pretty", kernel_name="Pretty")


@REGISTRY.kernel("Helpless")
def kernel_helpless(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Feeling helpless."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 12
        chars[0].Fear += 8
        return StoryFragment(f"{chars[0].name} felt helpless")
    
    return StoryFragment("helpless", kernel_name="Helpless")


@REGISTRY.kernel("Meal")
def kernel_meal(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Eating a meal."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} ate a meal")
    
    return StoryFragment("a meal", kernel_name="Meal")


@REGISTRY.kernel("Greeting")
def kernel_greeting(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Greeting someone."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        chars[0].Joy += 3
        chars[1].Joy += 3
        return StoryFragment(f"{chars[0].name} greeted {chars[1].name}")
    elif chars:
        chars[0].Joy += 3
        return StoryFragment(f"{chars[0].name} said hello")
    
    return StoryFragment("greetings", kernel_name="Greeting")


@REGISTRY.kernel("Imagination")
def kernel_imagination(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Using imagination."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 10
        return StoryFragment(f"{chars[0].name} used {chars[0].his} imagination")
    
    return StoryFragment("imagination", kernel_name="Imagination")


@REGISTRY.kernel("Naive")
def kernel_naive(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Naive or innocent character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was naive")
    
    return StoryFragment("naive", kernel_name="Naive")


# Test the module when run directly
if __name__ == "__main__":
    print(f"✅ gen5k09.py loaded successfully!")
    print(f"📦 Total kernels in registry: {len(REGISTRY.kernels)}")
    print(f"\n🔧 Kernels added in this pack:")
    
    # List kernels added in this file
    kernels_in_this_file = [
        "Follow", "Stuck", "Change", "Thanks", "Spill", "Recovery", "Pretend", "Reach",
        "Mess", "Cleanup", "Boredom", "Unhappy", "Guilt", "Empathy", "Unexpected",
        "Slide", "Sweet", "Shared", "Scary", "Social", "Warmth", "Bad", "Reassurance",
        "Scream", "Group", "Pretty", "Helpless", "Meal", "Greeting", "Imagination", "Naive"
    ]
    
    for kernel in kernels_in_this_file:
        if kernel in REGISTRY.kernels:
            print(f"   ✓ {kernel}")
        else:
            print(f"   ✗ {kernel} - NOT FOUND!")
    
    print(f"\n🎯 Total new kernels: {len(kernels_in_this_file)}")

