#!/usr/bin/env python3
# gen5k08.py - Additional Kernel Pack #08
"""
High-priority missing kernels implementation.

This pack implements the top missing kernels based on usage frequency
in the TinyStories dataset.

Kernels implemented:
- Anger (978 usages): Character feeling/expressing anger
- Seek (956 usages): Looking/searching for something
- Buy (909 usages): Purchasing items
- Continue (896 usages): Continuing an action
- Healing (888 usages): Recovery/healing process
- Explanation (848 usages): Explaining something
- Drink (836 usages): Drinking beverages/liquids
- Look (821 usages): Looking at something/someone
"""

from gen5 import (
    REGISTRY,
    StoryContext,
    StoryFragment,
    Character,
    NLGUtils,
    _to_phrase,
)


@REGISTRY.kernel("Anger")
def kernel_anger(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character feeling or expressing anger.
    
    Patterns from sampling:
      - Anger                      -- general anger state/emotion
      - Anger(Mom)                 -- Mom feels angry
      - Anger(Tom) + Anger(Amy)    -- multiple characters angry
      - reaction=Anger             -- as a reaction emotion
    
    Usage contexts:
      - As emotional reaction to conflict/mistake
      - As a state in arguments
      - As response to misbehavior
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        # Multiple characters feeling angry
        if len(chars) > 1:
            for char in chars:
                char.Anger += 15
                char.Joy -= 10
            names = NLGUtils.join_list([c.name for c in chars])
            return StoryFragment(f"{names} became angry.")
        
        # Single character feeling angry
        char = chars[0]
        char.Anger += 15
        char.Joy -= 10
        
        # Check for what they're angry about
        about = kwargs.get('about', kwargs.get('at', None))
        if about:
            return StoryFragment(f"{char.name} was very angry about {_to_phrase(about)}.")
        
        return StoryFragment(f"{char.name} felt angry.")
    
    # No character - used as emotion/state concept
    return StoryFragment("anger", kernel_name="Anger")


@REGISTRY.kernel("Seek")
def kernel_seek(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Looking for or searching for something.
    
    Patterns from sampling:
      - Seek(eyes)                 -- looking for eyes (for snowman)
      - Seek(safePlace)            -- seeking a safe place
      - Seek(Tim, toy)             -- Tim seeking his toy
      - Search(place) + Seek(item) -- part of search process
    
    Similar to Search but often more specific/goal-oriented.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    if chars and objects:
        char = chars[0]
        target = _to_phrase(objects[0])
        char.Focus = target
        return StoryFragment(f"{char.name} looked around for {target}.")
    
    if chars:
        char = chars[0]
        target = kwargs.get('target', kwargs.get('for', 'something'))
        char.Focus = target
        return StoryFragment(f"{char.name} searched for {_to_phrase(target)}.")
    
    if objects:
        target = _to_phrase(objects[0])
        return StoryFragment(f"seeking {target}", kernel_name="Seek")
    
    # Generic seeking
    return StoryFragment("seeking", kernel_name="Seek")


@REGISTRY.kernel("Buy")
def kernel_buy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Purchasing or acquiring items from a shop/store.
    
    Patterns from sampling:
      - Buy(aeroplane)              -- buying an aeroplane
      - Buy(Lucy, Icecream(cone))   -- Lucy buying ice cream cone
      - action=Buy(aeroplane)       -- as part of quest/activity
      - Buy(item, payment=coin)     -- buying with payment
    
    Often involves going to shop, choosing item, purchasing.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    payment = kwargs.get('payment', kwargs.get('with', None))
    location = kwargs.get('at', kwargs.get('from', 'the shop'))
    
    if chars and objects:
        char = chars[0]
        item = _to_phrase(objects[0])
        char.Joy += 5
        
        if payment:
            return StoryFragment(
                f"{char.name} bought {item} at {_to_phrase(location)} with {_to_phrase(payment)}."
            )
        
        return StoryFragment(f"{char.name} bought {item} at {_to_phrase(location)}.")
    
    if chars:
        char = chars[0]
        item = kwargs.get('item', kwargs.get('thing', 'something'))
        char.Joy += 5
        
        if payment:
            return StoryFragment(
                f"{char.name} bought {_to_phrase(item)} with {_to_phrase(payment)}."
            )
        
        return StoryFragment(f"{char.name} went shopping and bought {_to_phrase(item)}.")
    
    if objects:
        item = _to_phrase(objects[0])
        if payment:
            return StoryFragment(f"buying {item} with {_to_phrase(payment)}", kernel_name="Buy")
        return StoryFragment(f"buying {item}", kernel_name="Buy")
    
    # Generic buying
    return StoryFragment("buying something", kernel_name="Buy")


@REGISTRY.kernel("Continue")
def kernel_continue(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Continuing an action or activity.
    
    Patterns from sampling:
      - Continue                      -- general continuation
      - Continue(DrumPlay)            -- continuing to play drum
      - Decline(Duck, Continue)       -- declining to continue
      - resolution=Continue(activity) -- as part of resolution
    
    Often used when someone persists with an activity despite
    interruption or after a break.
    """
    chars = [a for a in args if isinstance(a, Character)]
    activities = [str(a) for a in args if not isinstance(a, Character)]
    
    activity = kwargs.get('activity', kwargs.get('doing', None))
    if not activity and activities:
        activity = activities[0]
    
    if chars:
        char = chars[0]
        
        if activity:
            return StoryFragment(f"{char.name} continued {_to_phrase(activity)}.")
        
        # Continue with current focus
        if hasattr(char, 'Focus') and char.Focus:
            return StoryFragment(f"{char.name} continued with {char.Focus}.")
        
        return StoryFragment(f"{char.name} kept going.")
    
    if activity:
        return StoryFragment(f"continuing {_to_phrase(activity)}", kernel_name="Continue")
    
    # Generic continuation
    return StoryFragment("continuing", kernel_name="Continue")


@REGISTRY.kernel("Healing")
def kernel_healing(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Recovery or healing process.
    
    Patterns from sampling:
      - Healing                    -- general healing
      - Healing(wound)             -- healing a wound
      - Healing(Timmy)             -- Timmy recovering
      - process=Healing + Care     -- as part of recovery process
    
    Often involves recovery from injury, illness, or emotional hurt.
    Related to Recovery, Care, Medicine.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if not isinstance(a, Character)]
    
    agent = kwargs.get('by', kwargs.get('agent', None))
    method = kwargs.get('method', kwargs.get('with', None))
    
    if chars:
        char = chars[0]
        
        # Reduce negative emotions during healing
        char.Sadness = max(0, char.Sadness - 10)
        char.Fear = max(0, char.Fear - 5)
        char.Joy += 5
        
        if objects:
            # Healing specific thing
            what = _to_phrase(objects[0])
            if agent:
                return StoryFragment(
                    f"{char.name}'s {what} was healing with help from {_to_phrase(agent)}."
                )
            return StoryFragment(f"{char.name}'s {what} was healing.")
        
        # General healing
        if method:
            return StoryFragment(
                f"{char.name} was healing with {_to_phrase(method)}."
            )
        
        if agent:
            return StoryFragment(
                f"{char.name} was getting better with {_to_phrase(agent)}'s help."
            )
        
        return StoryFragment(f"{char.name} was healing and feeling better.")
    
    if objects:
        what = _to_phrase(objects[0])
        return StoryFragment(f"healing {what}", kernel_name="Healing")
    
    # Generic healing
    return StoryFragment("healing", kernel_name="Healing")


@REGISTRY.kernel("Explanation")
def kernel_explanation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Explaining something to someone.
    
    Patterns from sampling:
      - Explanation(Mom, message=Patience)  -- Mom explaining patience
      - Explanation(teacher, about=science) -- teacher explaining science
      - Explanation + Guidance              -- as part of teaching
    
    Often involves teaching a lesson, clarifying something, or
    providing information/reasoning.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    message = kwargs.get('message', kwargs.get('about', kwargs.get('topic', None)))
    to = kwargs.get('to', kwargs.get('recipient', None))
    
    if chars:
        explainer = chars[0]
        
        if len(chars) > 1:
            # Multiple characters involved - first explains to second
            listener = chars[1]
            
            if message:
                return StoryFragment(
                    f"{explainer.name} explained to {listener.name} about {_to_phrase(message)}."
                )
            
            return StoryFragment(
                f"{explainer.name} explained everything to {listener.name}."
            )
        
        # Single explainer
        if to and message:
            return StoryFragment(
                f"{explainer.name} explained to {_to_phrase(to)} about {_to_phrase(message)}."
            )
        
        if message:
            return StoryFragment(
                f"{explainer.name} gave an explanation about {_to_phrase(message)}."
            )
        
        if to:
            return StoryFragment(
                f"{explainer.name} explained things to {_to_phrase(to)}."
            )
        
        return StoryFragment(f"{explainer.name} explained carefully.")
    
    # No character - concept
    if message:
        return StoryFragment(f"an explanation about {_to_phrase(message)}", kernel_name="Explanation")
    
    return StoryFragment("an explanation", kernel_name="Explanation")


@REGISTRY.kernel("Drink")
def kernel_drink(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Drinking beverages or liquids.
    
    Patterns from sampling:
      - Drink(water)              -- drinking water
      - Drink(Lily, milk)         -- Lily drinking milk
      - Drink(juice, from=cup)    -- drinking juice from cup
      - action=Drink + Eat        -- as part of meal/snack
    
    Common beverages: water, milk, juice, tea, coffee.
    """
    chars = [a for a in args if isinstance(a, Character)]
    beverages = [str(a) for a in args if not isinstance(a, Character)]
    
    container = kwargs.get('from', kwargs.get('container', None))
    
    if chars:
        char = chars[0]
        char.Joy += 3
        
        if beverages:
            beverage = _to_phrase(beverages[0])
            
            if container:
                return StoryFragment(
                    f"{char.name} drank {beverage} from {_to_phrase(container)}."
                )
            
            return StoryFragment(f"{char.name} drank some {beverage}.")
        
        # No specific beverage mentioned
        if container:
            return StoryFragment(
                f"{char.name} drank from {_to_phrase(container)}."
            )
        
        return StoryFragment(f"{char.name} had something to drink.")
    
    if beverages:
        beverage = _to_phrase(beverages[0])
        if container:
            return StoryFragment(f"drinking {beverage} from {_to_phrase(container)}", kernel_name="Drink")
        return StoryFragment(f"drinking {beverage}", kernel_name="Drink")
    
    # Generic drinking
    return StoryFragment("drinking", kernel_name="Drink")


@REGISTRY.kernel("Look")
def kernel_look(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Looking at something or someone.
    
    Patterns from sampling:
      - Look(tree)                -- looking at tree
      - Look(Lily, at=mirror)     -- Lily looking at mirror
      - Look(around)              -- looking around
      - action=Look + See         -- as part of observation
    
    Different from Observe (more detailed) or Seek (goal-oriented).
    Look is more casual/general gazing or glancing.
    """
    chars = [a for a in args if isinstance(a, Character)]
    targets = [str(a) for a in args if not isinstance(a, Character)]
    
    at = kwargs.get('at', kwargs.get('target', None))
    direction = kwargs.get('direction', None)
    
    if chars:
        char = chars[0]
        
        # Looking at specific target
        if targets:
            target = _to_phrase(targets[0])
            char.Focus = target
            return StoryFragment(f"{char.name} looked at {target}.")
        
        if at:
            target = _to_phrase(at)
            char.Focus = target
            return StoryFragment(f"{char.name} looked at {target}.")
        
        if direction:
            return StoryFragment(f"{char.name} looked {_to_phrase(direction)}.")
        
        # General looking around
        return StoryFragment(f"{char.name} looked around.")
    
    # No character - as concept or direction
    if targets:
        target = _to_phrase(targets[0])
        return StoryFragment(f"looking at {target}", kernel_name="Look")
    
    if at:
        return StoryFragment(f"looking at {_to_phrase(at)}", kernel_name="Look")
    
    # Generic looking
    return StoryFragment("looking", kernel_name="Look")


# =============================================================================
# TEST THE KERNELS
# =============================================================================

if __name__ == "__main__":
    print("Testing gen5k08 kernels...")
    print(f"Registered kernels: {len(REGISTRY.kernels)}")
    
    # Test each kernel
    from gen5 import Character, StoryContext
    
    ctx = StoryContext()
    lily = Character("Lily", "girl")
    mom = Character("Mom", "mother")
    
    print("\n" + "="*70)
    print("Testing Anger:")
    print(f"  - Anger(): {kernel_anger(ctx)}")
    print(f"  - Anger(Lily): {kernel_anger(ctx, lily)}")
    print(f"  - Anger(Lily, Mom): {kernel_anger(ctx, lily, mom)}")
    
    print("\n" + "="*70)
    print("Testing Seek:")
    print(f"  - Seek(toy): {kernel_seek(ctx, 'toy')}")
    print(f"  - Seek(Lily, ball): {kernel_seek(ctx, lily, 'ball')}")
    
    print("\n" + "="*70)
    print("Testing Buy:")
    print(f"  - Buy(icecream): {kernel_buy(ctx, 'icecream')}")
    print(f"  - Buy(Lily, toy): {kernel_buy(ctx, lily, 'toy')}")
    
    print("\n" + "="*70)
    print("Testing Continue:")
    print(f"  - Continue(): {kernel_continue(ctx)}")
    print(f"  - Continue(playing): {kernel_continue(ctx, 'playing')}")
    print(f"  - Continue(Lily, dancing): {kernel_continue(ctx, lily, 'dancing')}")
    
    print("\n" + "="*70)
    print("Testing Healing:")
    print(f"  - Healing(): {kernel_healing(ctx)}")
    print(f"  - Healing(Lily): {kernel_healing(ctx, lily)}")
    print(f"  - Healing(wound): {kernel_healing(ctx, 'wound')}")
    
    print("\n" + "="*70)
    print("Testing Explanation:")
    print(f"  - Explanation(Mom): {kernel_explanation(ctx, mom)}")
    print(f"  - Explanation(Mom, Lily): {kernel_explanation(ctx, mom, lily)}")
    print(f"  - Explanation(Mom, message='patience'): {kernel_explanation(ctx, mom, message='patience')}")
    
    print("\n" + "="*70)
    print("Testing Drink:")
    print(f"  - Drink(water): {kernel_drink(ctx, 'water')}")
    print(f"  - Drink(Lily, milk): {kernel_drink(ctx, lily, 'milk')}")
    
    print("\n" + "="*70)
    print("Testing Look:")
    print(f"  - Look(tree): {kernel_look(ctx, 'tree')}")
    print(f"  - Look(Lily, at='mirror'): {kernel_look(ctx, lily, at='mirror')}")
    
    print("\n" + "="*70)
    print("✓ All tests completed!")
    print(f"Total kernels now: {len(REGISTRY.kernels)}")

