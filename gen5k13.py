#!/usr/bin/env python3
"""
gen5k13.py - Additional Kernel Pack #13

This pack implements missing kernels to improve story generation quality,
particularly for common emotional patterns and family interactions.

KERNELS IMPLEMENTED:
- Sorry: Apologizing and expressing regret
- HeadHang: Physical gesture of shame/guilt
- Comforted: Being comforted and feeling better
- FamilySupport: Family members supporting each other
- Restless: Unable to stay still, feeling restless
- Basket: Container object used in stories
- Belonging: Sense of belonging and finding one's place
- StayForever: Committing to stay permanently
- Toys: Playthings and toy objects
- Kids/Lady: Additional character types

All kernels follow the standard pattern with appropriate emotional state updates.
"""

from gen5 import (
    REGISTRY,
    StoryContext,
    StoryFragment,
    Character,
    NLGUtils,
    _to_phrase,
    _event_to_phrase,
    _get_default_actor,
)


# =============================================================================
# EMOTIONAL EXPRESSIONS & GESTURES
# =============================================================================

@REGISTRY.kernel("Sorry")
def kernel_sorry(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character apologizes or says sorry.
    
    Patterns from dataset:
      - Sorry(Kitty)             -- Kitty says sorry
      - Sorry(boy)               -- boy apologizes
      - reaction=Sorry(Tim) + Embarrassment
    
    Usage: Often follows mistakes or accidents in cautionary tales.
    """
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', None)
    
    if chars:
        char = chars[0]
        char.Sadness += 3
        char.Fear += 2
        
        if isinstance(to, Character):
            return StoryFragment(f'{char.name} said "I\'m sorry" to {to.name}.')
        elif to:
            return StoryFragment(f'{char.name} said "I\'m sorry" to {to}.')
        else:
            return StoryFragment(f'{char.name} mumbled "Sorry," with sad eyes.')
    
    return StoryFragment("sorry", kernel_name="Sorry")


@REGISTRY.kernel("HeadHang")
def kernel_headhang(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Head hanging down in shame or guilt - physical gesture.
    
    Patterns from dataset:
      - consequence=HeadHang + Guilt  -- as emotional state
      - Her head hung from the stair  -- physical hanging
    
    Usage: Represents shame, guilt, or physical hanging posture.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Sadness += 5
        return StoryFragment(f"{char.name}'s head hung low in shame.")
    
    # As a state descriptor
    return StoryFragment("head hang", kernel_name="HeadHang")


@REGISTRY.kernel("Comforted")
def kernel_comforted(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character is comforted and feels better.
    
    Patterns from dataset:
      - Transformation(Benny, Comforted + Connected)
      - result=Comforted(Tim) + Friendship
      - Transformation(Kitty, Comforted + Confidence)
    
    Usage: Result of receiving support, comfort, or care from others.
    """
    chars = [a for a in args if isinstance(a, Character)]
    by = kwargs.get('by', None)
    
    if chars:
        char = chars[0]
        char.Joy += 8
        char.Sadness -= 5
        char.Fear -= 5
        
        if isinstance(by, Character):
            return StoryFragment(f'{char.name} felt comforted by {by.name}.')
        elif by:
            return StoryFragment(f'{char.name} felt comforted by {by}.')
        else:
            return StoryFragment(f'{char.name} felt comforted and safe.')
    
    return StoryFragment("comforted", kernel_name="Comforted")


# =============================================================================
# FAMILY & SOCIAL PATTERNS
# =============================================================================

@REGISTRY.kernel("FamilySupport")
def kernel_family_support(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Family members providing support to each other.
    
    Patterns from dataset:
      - FamilySupport(Kitty, agents=[Mommy, Daddy], action=Hug + Reassure, effect=Warmth + Acceptance)
      - FamilySupport(Lily, state=Routine, disruption=Absence, catalyst=Offer, process=Visit + Read)
      - FamilySupport(RequestHelp + Reluctance + Agreement + Clean + Success + Hug)
    
    Usage: Complex pattern representing family dynamics and mutual support.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    # Extract keyword arguments
    agents = kwargs.get('agents', [])
    action = kwargs.get('action', None)
    effect = kwargs.get('effect', None)
    state = kwargs.get('state', None)
    process = kwargs.get('process', None)
    outcome = kwargs.get('outcome', None)
    
    parts = []
    
    # Main character receiving support
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Joy += 10
        char.Love += 10
        char.Fear -= 5
    
    # State/background
    if state:
        state_text = _to_phrase(state)
        if char and state_text:
            parts.append(f"{char.name} was going through {state_text}.")
    
    # Agents providing support
    if agents:
        agent_names = []
        for agent in agents:
            if isinstance(agent, Character):
                agent.Love += 5
                agent_names.append(agent.name)
            else:
                agent_names.append(str(agent))
        
        if agent_names and char:
            agents_str = NLGUtils.join_list(agent_names)
            parts.append(f"{agents_str} came to support {char.name}.")
    
    # Action taken
    if action:
        action_text = _event_to_phrase(action)
        if action_text:
            parts.append(f"{action_text}.")
    
    # Process/what happened
    if process:
        process_text = _event_to_phrase(process)
        if process_text:
            parts.append(f"Together, they {process_text}.")
    
    # Effect/result
    if effect:
        effect_text = _event_to_phrase(effect)
        if effect_text:
            # Check if it's already a complete sentence (contains verb like "felt")
            if 'felt' in effect_text or char.name.lower() in effect_text.lower():
                parts.append(f"{effect_text}.")
            elif char:
                parts.append(f"{char.name} felt {effect_text}.")
            else:
                parts.append(f"{effect_text}.")
    
    # Outcome
    if outcome:
        outcome_text = _event_to_phrase(outcome)
        if outcome_text:
            parts.append(f"{outcome_text}.")
    
    if parts:
        return StoryFragment(' '.join(parts), kernel_name="FamilySupport")
    
    # Fallback for simple usage
    if char:
        return StoryFragment(f"{char.name} received support from family.")
    
    return StoryFragment("family support", kernel_name="FamilySupport")


# =============================================================================
# CHARACTER STATES & TRAITS
# =============================================================================

@REGISTRY.kernel("Restless")
def kernel_restless(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character is restless, unable to stay still.
    
    Patterns from dataset:
      - Timmy(Character, boy, Restless + Curious)
      - Kitty(Character, cat, Restless + Curious)
      - state=Restless + Longing(Adventure)
    
    Usage: Character trait indicating inability to settle down.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Fear += 2
        return StoryFragment(f"{char.name} was very restless.")
    
    # As a state descriptor, return just the adjective
    return StoryFragment("restless", kernel_name="Restless")


@REGISTRY.kernel("Belonging")
def kernel_belonging(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Sense of belonging and finding one's place.
    
    Patterns from dataset:
      - Belonging(catalyst=Lost, process=Invitation + Acceptance, outcome=Community + Joy)
      - transformation=Belonging + HappyEverAfter
      - transformation=Belonging(Kids) + StayForever  -- belonging with Kids
    
    Usage: About finding community, home, or where one fits in.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    catalyst = kwargs.get('catalyst', None)
    process = kwargs.get('process', None)
    outcome = kwargs.get('outcome', None)
    
    parts = []
    
    # Determine the subject - could be explicitly passed or from context
    # If an object/group is passed as arg (like "Kids"), that's WHERE they belong, not WHO
    char = chars[0] if chars else ctx.current_focus
    place_or_group = objects[0] if objects else (chars[0].name if chars and not ctx.current_focus else None)
    
    # If we got a character arg but current_focus exists, the arg is where they belong
    if chars and ctx.current_focus and ctx.current_focus != chars[0]:
        place_or_group = chars[0].name
        char = ctx.current_focus
    
    if char:
        char.Joy += 12
        char.Love += 8
        char.Sadness -= 5
    
    # Catalyst - what started the journey
    if catalyst:
        catalyst_text = _event_to_phrase(catalyst)
        if catalyst_text:
            parts.append(f"{catalyst_text}.")
    
    # Process - how belonging was found
    if process:
        process_text = _event_to_phrase(process)
        if process_text:
            parts.append(f"{process_text}.")
    
    # Outcome - result of finding belonging
    if outcome:
        outcome_text = _event_to_phrase(outcome)
        if outcome_text:
            parts.append(f"{outcome_text}.")
    
    if parts:
        return StoryFragment(' '.join(parts), kernel_name="Belonging")
    
    # Simple usage
    if char and place_or_group:
        return StoryFragment(f"{char.name} found a sense of belonging with {place_or_group}.")
    elif char:
        return StoryFragment(f"{char.name} finally felt like they belonged.")
    
    return StoryFragment("belonging", kernel_name="Belonging")


@REGISTRY.kernel("StayForever")
def kernel_stay_forever(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Staying somewhere or with someone forever.
    
    Patterns from dataset:
      - transformation=Belonging(Kids) + StayForever  -- staying with Kids
      - Wish(StayForever)                -- wishing to stay
      - consequence=StayForever + Friendship
    
    Usage: Represents commitment, permanence, or being unable to leave.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # Determine subject - prefer current_focus over explicit char arg
    # because in transformation contexts, the char arg is often WHERE they stay
    char = ctx.current_focus if ctx.current_focus else (chars[0] if chars else None)
    place_or_who = objects[0] if objects else (chars[0].name if chars and ctx.current_focus else None)
    
    if char:
        char.Love += 5
        
        if place_or_who:
            return StoryFragment(f"{char.name} decided to stay with {place_or_who} forever.")
        else:
            return StoryFragment(f"{char.name} stayed forever in that wonderful place.")
    
    return StoryFragment("stay forever", kernel_name="StayForever")


# =============================================================================
# OBJECTS & THINGS
# =============================================================================

@REGISTRY.kernel("Basket")
def kernel_basket(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A basket object - container for carrying things.
    
    Patterns from dataset:
      - catalyst=Basket                    -- basket as trigger
      - Escape(Basket)                     -- escaping from basket
      - Collect(flowers, basket=Basket(tight))
      - Loss(Handle(basket))
    
    Usage: Object in stories, often for carrying items or hiding in.
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # Check for attributes
    size = None
    if 'tight' in kwargs or (objects and 'tight' in objects):
        size = 'tight'
    elif 'big' in kwargs or (objects and 'big' in objects):
        size = 'big'
    
    # Set as current object for context
    if size:
        ctx.current_object = f"{size} basket"
        return StoryFragment(f"a {size} basket", kernel_name="Basket")
    
    ctx.current_object = "basket"
    return StoryFragment("a basket", kernel_name="Basket")


@REGISTRY.kernel("Toys")
def kernel_toys(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Toys - playthings for children.
    
    Patterns from dataset:
      - Surprise(Toys) + Play(Kids)
      - process=Escape(Basket) + Surprise(Toys)
    
    Usage: Objects in stories about play and discovery.
    """
    ctx.current_object = "toys"
    return StoryFragment("toys", kernel_name="Toys")


# =============================================================================
# ADDITIONAL CHARACTER TYPES
# =============================================================================

# =============================================================================
# TEST RUNNER
# =============================================================================

if __name__ == "__main__":
    """Test the kernels in this pack."""
    print(f"\n{'='*70}")
    print(f"Testing gen5k13.py - Kernel Pack #13")
    print(f"{'='*70}\n")
    
    from gen5registry import REGISTRY as REG
    
    # Count kernels from this file
    this_file_kernels = [
        'Sorry', 'HeadHang', 'Comforted', 'FamilySupport',
        'Restless', 'Belonging', 'StayForever',
        'Basket', 'Toys', 'Kids', 'Lady'
    ]
    
    implemented = [k for k in this_file_kernels if k in REG.kernels]
    
    print(f"✅ Kernels in this pack: {len(this_file_kernels)}")
    print(f"✅ Successfully registered: {len(implemented)}")
    print(f"✅ Total kernels in registry: {len(REG.kernels)}")
    
    if len(implemented) < len(this_file_kernels):
        missing = [k for k in this_file_kernels if k not in REG.kernels]
        print(f"\n⚠️  Not registered: {missing}")
    else:
        print(f"\n🎉 All kernels from this pack successfully registered!")
    
    print(f"\n{'='*70}")
    print(f"Test a specific kernel with:")
    print(f"  python sample.py -k Sorry -n 3 --seed 42")
    print(f"  python sample.py -k FamilySupport -n 3 --seed 42")
    print(f"{'='*70}\n")

