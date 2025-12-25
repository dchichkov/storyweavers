"""
gen5k05.py - Additional Kernel Pack #05

This module extends gen5.py with 100 additional kernel implementations.
Import this module after gen5 to register the new kernels.

=============================================================================
KERNELS IN THIS PACK (100 kernels from dataset sampling):
=============================================================================

## Social Interaction Kernels
- Gratitude: Expressing thanks to someone
- Request: Asking for something 
- Warning: Giving a warning about danger
- Hospitality: Hosting guests, providing comfort

## Cognitive/Perception Kernels  
- Insight: Gaining understanding or wisdom
- Observe: Watching/noticing something
- Reflection: Thinking deeply about something
- Decision: Making a choice
- Idea: Having a creative thought

## Action/Attempt Kernels
- Attempt: Trying to do something
- Acquire: Obtaining or getting something
- Transform: Changing from one state to another
- Contrast: Comparing differences

## Emotional/State Kernels
- Comfort: Being comforted or comforting others
- Acceptance: Accepting a situation or person
- Denial: Refusing or rejecting something
- Scared: Being frightened

## Structural/Process Kernels
- Cooperation: Working together
- Condition: A prerequisite or requirement
- Resolution: Concluding/resolving conflict

=============================================================================

Usage:
    from gen5 import generate_story, REGISTRY
    import gen5k05  # Registers additional kernels
    
    story = generate_story(kernel_string)
"""

# Import everything we need from gen5
from gen5 import (
    REGISTRY, 
    StoryContext, 
    StoryFragment, 
    Character,
    NLGUtils,
    _to_phrase,
    _state_to_phrase,
    _event_to_phrase,
    _action_to_phrase,
)


# =============================================================================
# SOCIAL INTERACTION KERNELS
# =============================================================================

@REGISTRY.kernel("Gratitude")
def kernel_gratitude(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character expresses gratitude/thanks.
    
    Patterns from dataset:
      - Gratitude(Lily, Mom)           -- Lily grateful to Mom
      - Gratitude(Sue, Tim)            -- Sue grateful to Tim
      - resolution=Gratitude(OldLady, Friend)  -- in resolution
    """
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', None)
    
    if isinstance(to, str) and to in ctx.characters:
        to = ctx.characters[to]
    
    if len(chars) >= 2:
        # Gratitude(char1, char2) - char1 grateful to char2
        giver = chars[0]
        receiver = chars[1]
        giver.Joy += 8
        giver.Love += 5
        return StoryFragment(f'{giver.name} was very grateful to {receiver.name}.')
    elif chars and to:
        # Gratitude(char, to=other)
        chars[0].Joy += 8
        chars[0].Love += 5
        recipient_name = to.name if isinstance(to, Character) else str(to)
        return StoryFragment(f'{chars[0].name} felt grateful to {recipient_name}.')
    elif chars:
        # Just Gratitude(char)
        chars[0].Joy += 8
        chars[0].Love += 5
        return StoryFragment(f'{chars[0].name} felt very grateful.')
    
    return StoryFragment("gratitude", kernel_name="Gratitude")


@REGISTRY.kernel("Request")
def kernel_request(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character makes a request or asks for something.
    
    Patterns from dataset:
      - Request(Amy, Bird, food)       -- Amy asks Bird for food
      - Request(Emily, Lily)           -- Emily makes request to Lily
      - Request(Tom, stop)             -- Tom requests stop
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        # Request(char1, char2, object) - char1 asks char2 for object
        requester = chars[0]
        recipient = chars[1]
        if objects:
            return StoryFragment(f'{requester.name} asked {recipient.name} for {objects[0]}.')
        return StoryFragment(f'{requester.name} made a request to {recipient.name}.')
    elif chars and objects:
        # Request(char, thing)
        return StoryFragment(f'{chars[0].name} asked for {objects[0]}.')
    elif chars:
        return StoryFragment(f'{chars[0].name} made a request.')
    elif objects:
        return StoryFragment(f"there was a request for {objects[0]}", kernel_name="Request")
    
    return StoryFragment("request", kernel_name="Request")


@REGISTRY.kernel("Warning")
def kernel_warning(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character gives a warning.
    
    Patterns from dataset:
      - Warning(Mom, Lily)             -- Mom warns Lily
      - Warning(Mom, Lily, Tom)        -- Mom warns both
      - lesson=Warning(Mom, Lily)      -- as part of lesson
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    about = kwargs.get('about', None)
    
    if len(chars) >= 2:
        # Warning(warner, warned)
        warner = chars[0]
        warned_names = NLGUtils.join_list([c.name for c in chars[1:]])
        if about:
            return StoryFragment(f'{warner.name} warned {warned_names} about {about}.')
        elif objects:
            return StoryFragment(f'{warner.name} warned {warned_names} about {objects[0]}.')
        return StoryFragment(f'{warner.name} issued a warning.')
    elif chars:
        return StoryFragment(f'{chars[0].name} gave a warning.')
    
    return StoryFragment("warning", kernel_name="Warning")


@REGISTRY.kernel("Hospitality")
def kernel_hospitality(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Providing hospitality to guests.
    
    Patterns from dataset:
      - Hospitality(Friend, couch)     -- Friend provides couch
      - Hospitality(host=Witch, guests=[Lucy, Cat, Dog], setting=house)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    host = kwargs.get('host', None)
    guests = kwargs.get('guests', [])
    setting = kwargs.get('setting', None)
    
    if isinstance(host, Character):
        if guests:
            guest_names = NLGUtils.join_list([g.name if isinstance(g, Character) else str(g) for g in guests])
            host.Joy += 5
            host.Love += 3
            return StoryFragment(f'{host.name} welcomed {guest_names} warmly.')
        host.Joy += 5
        return StoryFragment(f'{host.name} was a gracious host.')
    elif len(chars) >= 2:
        # Hospitality(host, guest)
        host_char = chars[0]
        guest_names = NLGUtils.join_list([c.name for c in chars[1:]])
        host_char.Joy += 5
        host_char.Love += 3
        if objects:
            return StoryFragment(f'{host_char.name} offered {guest_names} {objects[0]}.')
        return StoryFragment(f'{host_char.name} welcomed {guest_names}.')
    elif chars and objects:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} provided {objects[0]} for their guests.')
    
    return StoryFragment("hospitality", kernel_name="Hospitality")


@REGISTRY.kernel("Cooperation")
def kernel_cooperation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Characters cooperate together.
    
    Patterns from dataset:
      - Cooperation(Spot+Bird+Ben, process=Push(melon))
      - Insight = Cooperation
    """
    chars = [a for a in args if isinstance(a, Character)]
    process = kwargs.get('process', None)
    outcome = kwargs.get('outcome', None)
    
    if len(chars) >= 2:
        # Multiple characters cooperating
        char_names = NLGUtils.join_list([c.name for c in chars])
        for c in chars:
            c.Joy += 5
            c.Love += 3
        if process:
            return StoryFragment(f'{char_names} worked together.')
        return StoryFragment(f'{char_names} cooperated.')
    elif chars:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} cooperated.')
    
    return StoryFragment("cooperation", kernel_name="Cooperation")


# =============================================================================
# COGNITIVE/PERCEPTION KERNELS
# =============================================================================

@REGISTRY.kernel("Insight")
def kernel_insight(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Gaining insight or understanding.
    
    Patterns from dataset:
      - Insight = Love(Mommy, Lily) + Protection(Mommy, Lily)
      - Insight(Sharing + Kindness)
      - Insight = Cooperation
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 3
        if objects:
            insights = NLGUtils.join_list(objects)
            return StoryFragment(f'there was an insight about {insights}')
        return StoryFragment(f'{chars[0].name} gained an important insight.')
    elif objects:
        insights = NLGUtils.join_list(objects)
        return StoryFragment(f'there was an insight about {insights}')
    
    return StoryFragment("insight", kernel_name="Insight")


@REGISTRY.kernel("Observe")
def kernel_observe(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Observing or watching something.
    
    Patterns from dataset:
      - Observe(butterfly)             -- observing butterfly
      - Observe(Finn, shell)           -- Finn observes shell
      - Observe(Wealthy(bookcase))     -- observing wealthy bookcase
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars and objects:
        observer = chars[0]
        observed = objects[0] if objects else "something"
        return StoryFragment(f'{observer.name} watched the {observed} carefully.')
    elif chars:
        return StoryFragment(f'{chars[0].name} observed carefully.')
    elif objects:
        return StoryFragment(f'observation!', kernel_name="Observe")
    
    return StoryFragment("observe", kernel_name="Observe")


@REGISTRY.kernel("Reflection")
def kernel_reflection(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Reflecting or thinking deeply.
    
    Patterns from dataset:
      - Reflection(Lily, feeling=Contentment, statement=GreatDay)
      - Reflection(Man) + Cease(Shout) + Start(Nice, People)
      - Reflection(Gratitude)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    feeling = kwargs.get('feeling', None)
    statement = kwargs.get('statement', None)
    
    if chars:
        if feeling or statement or objects:
            topic = feeling or statement or (objects[0] if objects else "life")
            return StoryFragment(f'{chars[0].name} reflected on {_to_phrase(topic)}.')
        return StoryFragment(f'{chars[0].name} thought deeply.')
    elif objects:
        return StoryFragment(f'there was reflection with {objects[0]}')
    
    return StoryFragment("reflection", kernel_name="Reflection")


@REGISTRY.kernel("Decision")
def kernel_decision(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Making a decision or choice.
    
    Patterns from dataset:
      - Decision(Lily, Agree)          -- Lily decides to agree
      - Decision(both)                 -- decision to take both
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    choice = kwargs.get('choice', None)
    
    if chars:
        char = chars[0]
        if objects:
            return StoryFragment(f'{char.name} decided to {objects[0]}.')
        elif choice:
            return StoryFragment(f'{char.name} decided on {choice}.')
        return StoryFragment(f'{char.name} made a decision.')
    elif objects:
        return StoryFragment(f'the decision was {objects[0]}')
    
    return StoryFragment("decision", kernel_name="Decision")


@REGISTRY.kernel("Idea")
def kernel_idea(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Having an idea or creative thought.
    
    Patterns from dataset:
      - Idea(Use(matches))             -- idea to use matches
      - Idea(Spot, plan=CooperateAll)  -- Spot has idea with plan
      - catalyst=Idea
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    plan = kwargs.get('plan', None)
    
    if chars:
        char = chars[0]
        char.Joy += 3
        if plan:
            return StoryFragment(f'{char.name} had a clever idea.')
        elif objects:
            return StoryFragment(f'{char.name} thought of an idea.')
        return StoryFragment(f'{char.name} had an idea!')
    
    return StoryFragment("there was an idea", kernel_name="Idea")


# =============================================================================
# ACTION/ATTEMPT KERNELS
# =============================================================================

@REGISTRY.kernel("Attempt")
def kernel_attempt(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Trying to do something.
    
    Patterns from dataset:
      - Attempt(Try(Bobo, get(Jar)) + Failure)
      - Attempt(Lily, action=Place(Ratty, shoebox))
      - Attempt(Mommy, Fix(car))
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    action = kwargs.get('action', None)
    
    if chars:
        char = chars[0]
        if action:
            return StoryFragment(f'{char.name} tried to {_action_to_phrase(action)}.')
        elif objects:
            return StoryFragment(f'{char.name} attempted to {objects[0]}.')
        return StoryFragment(f'{char.name} made an attempt.')
    
    return StoryFragment("there was an attempt to", kernel_name="Attempt")


@REGISTRY.kernel("Acquire")
def kernel_acquire(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Acquiring or obtaining something.
    
    Patterns from dataset:
      - Acquire(Skip, shell)           -- Skip acquires shell
      - Acquire(Puppy)                 -- acquiring puppy
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars and objects:
        char = chars[0]
        obj = objects[0]
        char.Joy += 5
        return StoryFragment(f'{char.name} acquired {obj}.')
    elif chars:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} obtained what they wanted.')
    elif objects:
        return StoryFragment(f'acquired {objects[0]}')
    
    return StoryFragment("acquire", kernel_name="Acquire")


@REGISTRY.kernel("Transform")
def kernel_transform(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Transforming from one state to another.
    
    Patterns from dataset:
      - Transform(Lazy, Active)        -- transform from lazy to active
      - Transform(Rock, Fairy)         -- rock transforms into fairy
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(objects) >= 2:
        # Transform(from, to)
        from_state = objects[0]
        to_state = objects[1]
        if chars:
            chars[0].Joy += 5
            return StoryFragment(f'The {from_state} transformed into a {to_state}.')
        return StoryFragment(f'The {from_state} transformed into a {to_state}.')
    elif chars:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} transformed.')
    
    return StoryFragment("Everything was transformed.", kernel_name="Transform")


@REGISTRY.kernel("Contrast")
def kernel_contrast(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Contrasting or comparing differences.
    
    Patterns from dataset:
      - Contrast(room, park)           -- contrast room and park
      - Contrast(Small(bookcase), Large(bookcase))
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(objects) >= 2:
        first = objects[0]
        second = objects[1]
        if chars:
            return StoryFragment(f'{chars[0].name} noticed the contrast between {first} and {second}.')
        return StoryFragment(f'There was a contrast: a {first} and a {second}.')
    elif chars:
        return StoryFragment(f'{chars[0].name} saw the difference.')
    
    return StoryFragment("contrast", kernel_name="Contrast")


# =============================================================================
# EMOTIONAL/STATE KERNELS
# =============================================================================

@REGISTRY.kernel("Comfort")
def kernel_comfort(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being comforted or comforting someone.
    
    Patterns from dataset:
      - Comfort(Lily, Hug(teddy)+Bed)  -- Lily comforted with teddy and bed
      - Comfort(Grace, Mum)            -- Mum comforts Grace
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        # Comfort(comforted, comforter)
        comforted = chars[0]
        comforter = chars[1]
        comforted.Joy += 8
        comforted.Sadness -= 5
        comforter.Love += 5
        return StoryFragment(f'{comforter.name} comforted {comforted.name}.')
    elif chars:
        chars[0].Joy += 8
        chars[0].Sadness -= 5
        return StoryFragment(f'{chars[0].name} was comforted.')
    
    return StoryFragment("comfort", kernel_name="Comfort")


@REGISTRY.kernel("Acceptance")
def kernel_acceptance(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Accepting a situation or person.
    
    Patterns from dataset:
      - Acceptance(Lily, waiting)      -- Lily accepts waiting
      - RequestPlay(Lily, Boy) + Acceptance
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars and objects:
        char = chars[0]
        thing = objects[0]
        char.Joy += 3
        char.Sadness -= 3
        return StoryFragment(f'{char.name} accepted {thing}.')
    elif chars:
        chars[0].Joy += 3
        chars[0].Sadness -= 3
        return StoryFragment(f'{chars[0].name} accepted the situation.')
    
    return StoryFragment("acceptance", kernel_name="Acceptance")


@REGISTRY.kernel("Denial")
def kernel_denial(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Denying or refusing something.
    
    Patterns from dataset:
      - Denial(Daddy, rule=Age)        -- Daddy denies due to age rule
      - Denial(Neighbor, flower)       -- Neighbor denies flower
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    rule = kwargs.get('rule', None)
    
    if chars and objects:
        denier = chars[0]
        denied_thing = objects[0]
        return StoryFragment(f'{denier.name} said no to {denied_thing}.')
    elif chars:
        return StoryFragment(f'{chars[0].name} refused.')
    elif objects:
        return StoryFragment(f'denial of {objects[0]}')
    
    return StoryFragment("denial", kernel_name="Denial")


@REGISTRY.kernel("Scared")
def kernel_scared(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being scared or frightened.
    
    Patterns from dataset:
      - Scared                         -- general fear state
      - process = Climb(rock) + Scared + Reassure(Billy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        for char in chars:
            char.Fear += 10
            char.Joy -= 5
        char_names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f'{char_names} felt scared.')
    elif ctx.current_focus:
        ctx.current_focus.Fear += 10
        ctx.current_focus.Joy -= 5
        return StoryFragment(f'{ctx.current_focus.name} was scared.')
    
    return StoryFragment("fear and anxiety", kernel_name="Scared")


# =============================================================================
# STRUCTURAL/PROCESS KERNELS
# =============================================================================

@REGISTRY.kernel("Condition")
def kernel_condition(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A condition or prerequisite.
    
    Patterns from dataset:
      - Condition(Talk) + Talk(Amy, Bird)
      - Condition(Prayer) + Ritual(Prayer)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if objects:
        condition = objects[0]
        return StoryFragment(f'there was a condition: {condition}')
    elif chars:
        return StoryFragment(f'{chars[0].name} set a condition.')
    
    return StoryFragment("condition", kernel_name="Condition")


# =============================================================================
# TRAIT/CHARACTER ATTRIBUTE KERNELS
# =============================================================================

@REGISTRY.kernel("Loyal")
def kernel_loyal(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Loyal character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Love += 5
    return StoryFragment("loyal", kernel_name="Loyal")


@REGISTRY.kernel("Impulsive")
def kernel_impulsive(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Impulsive character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 3
    return StoryFragment("impulsive", kernel_name="Impulsive")


@REGISTRY.kernel("Adventurous")
def kernel_adventurous(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Adventurous character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 5
    return StoryFragment("adventurous", kernel_name="Adventurous")


@REGISTRY.kernel("Joyful")
def kernel_joyful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Joyful character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 8
    return StoryFragment("joyful", kernel_name="Joyful")


@REGISTRY.kernel("Authority")
def kernel_authority(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Authority character trait."""
    return StoryFragment("authority", kernel_name="Authority")


@REGISTRY.kernel("Loneliness")
def kernel_loneliness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Loneliness emotion."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Sadness += 8
        chars[0].Joy -= 5
        return StoryFragment(f'{chars[0].name} felt lonely.')
    return StoryFragment("loneliness", kernel_name="Loneliness")


@REGISTRY.kernel("Family")
def kernel_family(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Family concept or group."""
    return StoryFragment("family", kernel_name="Family")


@REGISTRY.kernel("Home")
def kernel_home(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Home location/concept."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f'{chars[0].name} went home.')
    return StoryFragment("home", kernel_name="Home")


@REGISTRY.kernel("Sensitive")
def kernel_sensitive(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sensitive character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Love += 3
    return StoryFragment("sensitive", kernel_name="Sensitive")


@REGISTRY.kernel("Sharing")
def kernel_sharing(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Sharing concept or action.
    
    Patterns from dataset:
      - Insight(Sharing + Kindness)
      - Sharing(Share(Bobo, Toto, honey) + Joy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        for char in chars:
            char.Joy += 5
            char.Love += 5
    return StoryFragment("sharing", kernel_name="Sharing")


@REGISTRY.kernel("Nice")
def kernel_nice(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Nice character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Love += 5
    return StoryFragment("nice", kernel_name="Nice")


@REGISTRY.kernel("Musical")
def kernel_musical(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Musical character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 3
    return StoryFragment("musical", kernel_name="Musical")


@REGISTRY.kernel("Harmony")
def kernel_harmony(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Harmony state or concept."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        for char in chars:
            char.Joy += 5
            char.Love += 3
    return StoryFragment("harmony", kernel_name="Harmony")


@REGISTRY.kernel("Generous")
def kernel_generous(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Generous character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 5
        chars[0].Love += 5
    return StoryFragment("generous", kernel_name="Generous")


@REGISTRY.kernel("Cold")
def kernel_cold(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Cold weather/temperature."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy -= 3
    return StoryFragment("it was cold", kernel_name="Cold")


@REGISTRY.kernel("Exploration")
def kernel_exploration(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Exploration activity."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} explored.')
    return StoryFragment("exploration", kernel_name="Exploration")


@REGISTRY.kernel("Responsible")
def kernel_responsible(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Responsible character trait."""
    return StoryFragment("responsible", kernel_name="Responsible")


@REGISTRY.kernel("Determined")
def kernel_determined(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Determined character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 3
    return StoryFragment("determined", kernel_name="Determined")


# =============================================================================
# ACTION KERNELS (Continued)
# =============================================================================

@REGISTRY.kernel("Quarrel")
def kernel_quarrel(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Quarreling or arguing.
    
    Patterns from dataset:
      - process=Quarrel + Shout
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        for char in chars:
            char.Anger += 5
            char.Joy -= 3
        char_names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f'{char_names} quarreled.')
    elif chars:
        chars[0].Anger += 5
        return StoryFragment(f'{chars[0].name} was quarrelsome.')
    
    return StoryFragment("quarrel", kernel_name="Quarrel")


@REGISTRY.kernel("Vanish")
def kernel_vanish(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something vanishes or disappears.
    
    Patterns from dataset:
      - Vanish(eraser) + Loss(Lily, eraser)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if objects:
        obj = objects[0]
        return StoryFragment(f'the {obj} vanished.')
    elif chars:
        chars[0].Fear += 5
        return StoryFragment(f'{chars[0].name} vanished!')
    
    return StoryFragment("vanish", kernel_name="Vanish")


@REGISTRY.kernel("Split")
def kernel_split(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something splits or divides.
    
    Patterns from dataset:
      - Split(rock)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if objects:
        obj = objects[0]
        return StoryFragment(f'the {obj} split apart.')
    
    return StoryFragment("split", kernel_name="Split")


@REGISTRY.kernel("Dark")
def kernel_dark(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Darkness or dark condition.
    
    Patterns from dataset:
      - Dark(sky)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        for char in chars:
            char.Fear += 3
    
    if objects:
        return StoryFragment(f'the {objects[0]} was dark.')
    
    return StoryFragment("it was dark", kernel_name="Dark")


@REGISTRY.kernel("Goodbye")
def kernel_goodbye(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Saying goodbye.
    
    Patterns from dataset:
      - Goodbye(Lily, friends)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        first = chars[0]
        others = NLGUtils.join_list([c.name for c in chars[1:]])
        first.Sadness += 3
        return StoryFragment(f'{first.name} said goodbye to {others}.')
    elif chars and objects:
        chars[0].Sadness += 3
        return StoryFragment(f'{chars[0].name} said goodbye to {objects[0]}.')
    elif chars:
        chars[0].Sadness += 3
        return StoryFragment(f'{chars[0].name} waved goodbye.')
    
    return StoryFragment("goodbye", kernel_name="Goodbye")


@REGISTRY.kernel("Tell")
def kernel_tell(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Telling someone something.
    
    Patterns from dataset:
      - Tell(Lily, Billy, Split(rock))
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        teller = chars[0]
        listener = chars[1]
        if objects:
            return StoryFragment(f'{teller.name} told {listener.name} about {objects[0]}.')
        return StoryFragment(f'{teller.name} told {listener.name} a story.')
    elif chars:
        return StoryFragment(f'{chars[0].name} told a story.')
    
    return StoryFragment("tell", kernel_name="Tell")


@REGISTRY.kernel("Wow")
def kernel_wow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Expression of amazement.
    
    Patterns from dataset:
      - Wow(Billy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 8
        return StoryFragment(f'{chars[0].name} said "Wow!"')
    
    return StoryFragment('"Wow!"', kernel_name="Wow")


@REGISTRY.kernel("Tired")
def kernel_tired(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being tired or exhausted.
    
    Patterns from dataset:
      - Tired + Sleep
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy -= 3
        return StoryFragment(f'{chars[0].name} felt tired.')
    elif ctx.current_focus:
        ctx.current_focus.Joy -= 3
        return StoryFragment(f'{ctx.current_focus.name} was tired.')
    
    return StoryFragment("tired", kernel_name="Tired")


@REGISTRY.kernel("Skip")
def kernel_skip(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Skipping (movement or action).
    
    Patterns from dataset:
      - Skip
      - Joy(Skip)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} skipped happily.')
    elif ctx.current_focus:
        ctx.current_focus.Joy += 5
        return StoryFragment(f'{ctx.current_focus.name} skipped along.')
    
    return StoryFragment("skipping", kernel_name="Skip")


@REGISTRY.kernel("Nap")
def kernel_nap(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Taking a nap.
    
    Patterns from dataset:
      - Hug(Grace, Mum) + Nap
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f'{chars[0].name} took a nap.')
    
    return StoryFragment("nap", kernel_name="Nap")


@REGISTRY.kernel("Attachment")
def kernel_attachment(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Emotional attachment to something.
    
    Patterns from dataset:
      - Attachment(cloth) + Joy(cloth)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars and objects:
        chars[0].Love += 5
        return StoryFragment(f'{chars[0].name} was attached to {objects[0]}.')
    elif objects:
        return StoryFragment(f'there was attachment with {objects[0]}')
    
    return StoryFragment("attachment", kernel_name="Attachment")


@REGISTRY.kernel("Feeling")
def kernel_feeling(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Having a feeling or emotion.
    
    Patterns from dataset:
      - Feeling(Ignored)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars and objects:
        return StoryFragment(f'{chars[0].name} felt {objects[0]}.')
    elif objects:
        return StoryFragment(f'there was a feeling of {objects[0]}')
    
    return StoryFragment("feeling", kernel_name="Feeling")


@REGISTRY.kernel("Ignored")
def kernel_ignored(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being ignored.
    """
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Sadness += 8
        chars[0].Anger += 3
    return StoryFragment("ignored", kernel_name="Ignored")


@REGISTRY.kernel("Loving")
def kernel_loving(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Loving character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Love += 8
    return StoryFragment("loving", kernel_name="Loving")


@REGISTRY.kernel("Lazy")
def kernel_lazy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Lazy character trait."""
    return StoryFragment("lazy", kernel_name="Lazy")


@REGISTRY.kernel("Sleepy")
def kernel_sleepy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sleepy state."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy -= 2
    return StoryFragment("sleepy", kernel_name="Sleepy")


@REGISTRY.kernel("Gain")
def kernel_gain(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Gaining something.
    
    Patterns from dataset:
      - Gain(Power)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars and objects:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} gained {objects[0]}.')
    elif objects:
        return StoryFragment(f'there was a gain of {objects[0]}')
    
    return StoryFragment("gain", kernel_name="Gain")


@REGISTRY.kernel("Power")
def kernel_power(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Power concept."""
    return StoryFragment("power", kernel_name="Power")


@REGISTRY.kernel("Active")
def kernel_active(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Active state or trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 5
    return StoryFragment("active", kernel_name="Active")


@REGISTRY.kernel("LovedBy")
def kernel_lovedby(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being loved by someone or something.
    
    Patterns from dataset:
      - LovedBy(Community)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars and objects:
        chars[0].Joy += 8
        chars[0].Love += 8
        return StoryFragment(f'{chars[0].name} was loved by {objects[0]}.')
    elif objects:
        return StoryFragment(f'there was love from {objects[0]}')
    
    return StoryFragment("loved by", kernel_name="LovedBy")


@REGISTRY.kernel("Pocket")
def kernel_pocket(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Putting something in pocket.
    
    Patterns from dataset:
      - Pocket(rock)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars and objects:
        return StoryFragment(f'{chars[0].name} put {objects[0]} in their pocket.')
    elif objects:
        return StoryFragment(f'there was a pocket with {objects[0]}')
    
    return StoryFragment("pocket", kernel_name="Pocket")


@REGISTRY.kernel("Collector")
def kernel_collector(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Collector character trait."""
    return StoryFragment("collector", kernel_name="Collector")


@REGISTRY.kernel("Shine")
def kernel_shine(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something shining.
    
    Patterns from dataset:
      - Shine(garden)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if objects:
        return StoryFragment(f'the {objects[0]} was shining.')
    
    return StoryFragment("shine", kernel_name="Shine")


@REGISTRY.kernel("Reluctant")
def kernel_reluctant(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Reluctant character trait."""
    return StoryFragment("reluctant", kernel_name="Reluctant")


@REGISTRY.kernel("Cooperative")
def kernel_cooperative(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Cooperative character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Love += 5
    return StoryFragment("cooperative", kernel_name="Cooperative")


@REGISTRY.kernel("Bossy")
def kernel_bossy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Bossy character trait."""
    return StoryFragment("bossy", kernel_name="Bossy")


@REGISTRY.kernel("Not")
def kernel_not(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Negation operator.
    
    Patterns from dataset:
      - Not(Bossy)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if objects:
        return StoryFragment(f'there was not {objects[0]}')
    
    return StoryFragment("not", kernel_name="Not")


@REGISTRY.kernel("SnackLover")
def kernel_snacklover(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """SnackLover character trait."""
    return StoryFragment("snack lover", kernel_name="SnackLover")


@REGISTRY.kernel("SweetTooth")
def kernel_sweettooth(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """SweetTooth character trait."""
    return StoryFragment("sweet tooth", kernel_name="SweetTooth")


@REGISTRY.kernel("Jar")
def kernel_jar(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Jar object."""
    return StoryFragment("jar", kernel_name="Jar")


@REGISTRY.kernel("Clumsy")
def kernel_clumsy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Clumsy character trait."""
    return StoryFragment("clumsy", kernel_name="Clumsy")


@REGISTRY.kernel("Comfortable")
def kernel_comfortable(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Comfortable state."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 5
    return StoryFragment("comfortable", kernel_name="Comfortable")


@REGISTRY.kernel("Compassionate")
def kernel_compassionate(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Compassionate character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Love += 8
    return StoryFragment("compassionate", kernel_name="Compassionate")


@REGISTRY.kernel("Dependent")
def kernel_dependent(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Dependent character trait."""
    return StoryFragment("dependent", kernel_name="Dependent")


@REGISTRY.kernel("Unskilled")
def kernel_unskilled(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Unskilled character trait."""
    return StoryFragment("unskilled", kernel_name="Unskilled")


@REGISTRY.kernel("Grief")
def kernel_grief(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Grief emotion.
    
    Patterns from dataset:
      - Grief(Lily)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 15
        chars[0].Joy -= 10
        return StoryFragment(f'{chars[0].name} felt deep grief.')
    
    return StoryFragment("grief", kernel_name="Grief")


@REGISTRY.kernel("Grieving")
def kernel_grieving(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Grieving character trait/state."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Sadness += 10
    return StoryFragment("grieving", kernel_name="Grieving")


@REGISTRY.kernel("Death")
def kernel_death(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Death event.
    
    Patterns from dataset:
      - Death(Ratty)
      - Illness + Death
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} passed away.')
    elif objects:
        return StoryFragment(f'{objects[0]} died.')
    
    return StoryFragment("death", kernel_name="Death")


@REGISTRY.kernel("Illness")
def kernel_illness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Illness state.
    
    Patterns from dataset:
      - Illness(Ratty)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Sadness += 8
        chars[0].Joy -= 5
        return StoryFragment(f'{chars[0].name} became ill.')
    elif objects:
        return StoryFragment(f'{objects[0]} was sick.')
    
    return StoryFragment("illness", kernel_name="Illness")


@REGISTRY.kernel("Place")
def kernel_place(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Placing something somewhere.
    
    Patterns from dataset:
      - Place(Ratty, shoebox)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 1 and len(objects) >= 1:
        char = chars[0]
        location = objects[0]
        return StoryFragment(f'{char.name} was placed in {location}.')
    elif len(objects) >= 2:
        thing = objects[0]
        location = objects[1]
        return StoryFragment(f'{thing} was placed in {location}.')
    
    return StoryFragment("place", kernel_name="Place")


@REGISTRY.kernel("Step")
def kernel_step(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Stepping on something.
    
    Patterns from dataset:
      - Step(cage)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars and objects:
        return StoryFragment(f'{chars[0].name} stepped on {objects[0]}.')
    elif objects:
        return StoryFragment(f'there was a step on {objects[0]}')
    
    return StoryFragment("step", kernel_name="Step")


@REGISTRY.kernel("Add")
def kernel_add(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Adding something.
    
    Patterns from dataset:
      - Add(blankets)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars and objects:
        return StoryFragment(f'{chars[0].name} added {objects[0]}.')
    elif objects:
        return StoryFragment(f'added {objects[0]}')
    
    return StoryFragment("add", kernel_name="Add")


@REGISTRY.kernel("Broken")
def kernel_broken(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something broken.
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if objects:
        return StoryFragment(f'the {objects[0]} was broken.')
    
    return StoryFragment("broken", kernel_name="Broken")


@REGISTRY.kernel("Exam")
def kernel_exam(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    An exam or test.
    
    Patterns from dataset:
      - Exam(Nervous)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 5
        return StoryFragment(f'{chars[0].name} took an exam.')
    elif objects:
        return StoryFragment(f'there was an exam with {objects[0]}')
    
    return StoryFragment("exam", kernel_name="Exam")


@REGISTRY.kernel("SurpriseTest")
def kernel_surprisetest(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A surprise test.
    
    Patterns from dataset:
      - SurpriseTest(toy)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if objects:
        return StoryFragment(f'there was a surprise test with {objects[0]}')
    
    return StoryFragment("surprise test", kernel_name="SurpriseTest")


@REGISTRY.kernel("Working")
def kernel_working(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something working/functioning.
    
    Patterns from dataset:
      - state=Working(car)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if objects:
        return StoryFragment(f'the {objects[0]} was working.')
    
    return StoryFragment("working", kernel_name="Working")


@REGISTRY.kernel("Competitive")
def kernel_competitive(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Competitive character trait."""
    return StoryFragment("competitive", kernel_name="Competitive")


@REGISTRY.kernel("Race")
def kernel_race(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Having a race.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        char_names = NLGUtils.join_list([c.name for c in chars])
        for char in chars:
            char.Joy += 5
        return StoryFragment(f'{char_names} had a race.')
    elif chars:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} raced.')
    
    return StoryFragment("race", kernel_name="Race")


@REGISTRY.kernel("Ready")
def kernel_ready(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being ready.
    
    Patterns from dataset:
      - Ready(floor)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was ready.')
    elif objects:
        return StoryFragment(f'ready at {objects[0]}')
    
    return StoryFragment("ready", kernel_name="Ready")


@REGISTRY.kernel("NextRace")
def kernel_nextrace(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Next race concept."""
    return StoryFragment("the next race", kernel_name="NextRace")


@REGISTRY.kernel("Anticipatory")
def kernel_anticipatory(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Anticipatory character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 5
    return StoryFragment("anticipatory", kernel_name="Anticipatory")


@REGISTRY.kernel("Birthday")
def kernel_birthday(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Birthday event.
    
    Patterns from dataset:
      - Birthday(Lily, state=..., process=..., event=Party)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 10
        return StoryFragment(f'It was {chars[0].name}\'s birthday!')
    
    return StoryFragment("birthday", kernel_name="Birthday")


@REGISTRY.kernel("Creation")
def kernel_creation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Creation concept."""
    return StoryFragment("creation", kernel_name="Creation")


@REGISTRY.kernel("CreativePlay")
def kernel_creativeplay(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Creative play activity.
    
    Patterns from dataset:
      - CreativePlay(artsupplies, Friends)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        for char in chars:
            char.Joy += 8
        if objects:
            return StoryFragment(f'creative play with {objects[0]}')
    
    return StoryFragment("creative play", kernel_name="CreativePlay")


@REGISTRY.kernel("Party")
def kernel_party(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Party event.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        for char in chars:
            char.Joy += 10
        return StoryFragment('There was a party!')
    
    return StoryFragment("party", kernel_name="Party")


@REGISTRY.kernel("Surprising")
def kernel_surprising(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Surprising character trait."""
    return StoryFragment("surprising", kernel_name="Surprising")


@REGISTRY.kernel("Persistence")
def kernel_persistence(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Persistence quality or action.
    
    Patterns from dataset:
      - Persistence(Lily, care=Water(flower))
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} showed persistence.')
    
    return StoryFragment("persistence", kernel_name="Persistence")


@REGISTRY.kernel("Persistent")
def kernel_persistent(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Persistent character trait."""
    return StoryFragment("persistent", kernel_name="Persistent")


@REGISTRY.kernel("Resilient")
def kernel_resilient(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Resilient character trait."""
    chars = [a for a in args if isinstance(a, Character)]
    if chars:
        chars[0].Joy += 3
    return StoryFragment("resilient", kernel_name="Resilient")


@REGISTRY.kernel("SelfReliance")
def kernel_selfreliance(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Self-reliance concept."""
    return StoryFragment("self reliance", kernel_name="SelfReliance")


@REGISTRY.kernel("Guarded")
def kernel_guarded(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Guarded character trait - being cautious or protective."""
    return StoryFragment("guarded", kernel_name="Guarded")


@REGISTRY.kernel("Impermanence")
def kernel_impermanence(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Impermanence concept - understanding that things don't last forever.
    
    Patterns from dataset:
      - Lesson(Lily, Impermanence)
    """
    return StoryFragment("impermanence", kernel_name="Impermanence")


@REGISTRY.kernel("Nurture")
def kernel_nurture(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Nurturing or caring for something.
    
    Patterns from dataset:
      - Nurture(flower)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars and objects:
        chars[0].Love += 5
        chars[0].Joy += 3
        return StoryFragment(f'{chars[0].name} nurtured {objects[0]}.')
    elif chars:
        chars[0].Love += 5
        return StoryFragment(f'{chars[0].name} gave nurturing care.')
    elif objects:
        return StoryFragment(f'nurtured {objects[0]}')
    
    return StoryFragment("nurture", kernel_name="Nurture")


# =============================================================================
# TEST WHEN RUN DIRECTLY
# =============================================================================

if __name__ == '__main__':
    print("gen5k05.py - Additional Kernel Pack #05")
    print("=" * 70)
    print(f"Registered {len(REGISTRY.kernels)} total kernels")
    
    # Count kernels defined in this file
    import sys
    this_module = sys.modules[__name__]
    kernel_count = 0
    kernel_names = []
    for name in dir(this_module):
        obj = getattr(this_module, name)
        if callable(obj) and name.startswith('kernel_'):
            kernel_count += 1
            # Extract kernel name from function name
            kernel_name = name.replace('kernel_', '').replace('_', ' ').title()
            kernel_names.append(kernel_name)
    
    print(f"Kernels in this pack: {kernel_count}")
    print()
    print("Sample kernels from this pack:")
    for i, name in enumerate(sorted(kernel_names)[:20], 1):
        print(f"  {i:2}. {name}")
    if len(kernel_names) > 20:
        print(f"  ... and {len(kernel_names) - 20} more")
    print()
    print("✓ All kernels registered successfully!")

