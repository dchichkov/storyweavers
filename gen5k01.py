"""
gen5k01.py - Additional Kernel Pack #01

This module extends gen5.py with additional kernel implementations.
Import this module after gen5 to register the new kernels.

=============================================================================
KERNELS IN THIS PACK (with usage patterns from sampling):
=============================================================================

## Apology
Usage patterns:
  - Apology(Anna, Ben, Lily)  -- multiple chars apologizing
  - Apology(Tim)              -- single char apologizing
  - Apology(Tim, to=Ann)      -- char apologizing to specific person
  - resolution=Apology(Tim)+Forgiveness(Mom)  -- part of resolution

## Forgiveness  
Usage patterns:
  - Forgiveness(Max)          -- one char forgiving
  - Forgiveness(Mom)          -- parent/authority forgiving
  - Often paired with Apology

## Quest
Usage patterns:
  - Quest(Bunny, state=..., obstacle=..., catalyst=..., process=..., result=...)
  - Quest(Max, Lucy, clue=..., setting=..., outcome=...)
  - Has goal, obstacles, process, and outcome

## Loss
Usage patterns:
  - Loss(Apple)               -- losing an object
  - Loss(Mommy, Sick)         -- temporary loss of companion  
  - Loss(salad)               -- losing something desired

## Resolution
Usage patterns:
  - Resolution(Hug(Tom,Lily)+Share(BigNut)+Happy)  -- wrapping up story
  - Resolution(share(chair, Tim, Sam))              -- resolving conflict
  - Resolution(MutualWin + FunTogether)             -- happy ending summary
=============================================================================

Usage:
    from gen5 import generate_story, REGISTRY
    import gen5k01  # Registers additional kernels
    
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
    _get_default_actor,
)


# =============================================================================
# SOCIAL INTERACTION KERNELS
# =============================================================================

@REGISTRY.kernel("Apology")
def kernel_apology(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character apologizes to another.
    
    Patterns from dataset:
      - Apology(Anna, Ben, Lily)  -- Anna+Ben apologize to Lily
      - Apology(Tim)              -- Tim apologizes
      - Apology(Tim, to=Ann)      -- Tim apologizes to Ann
    """
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', None)
    
    # Resolve 'to' if it's a string that might be a character name
    if isinstance(to, str) and to in ctx.characters:
        to = ctx.characters[to]
    
    if len(chars) >= 2:
        # Multiple chars apologizing to last one: Apology(Anna, Ben, Lily)
        apologizers = chars[:-1]
        recipient = chars[-1]
        apologizer_names = NLGUtils.join_list([c.name for c in apologizers])
        for c in apologizers:
            c.Love += 5
        return StoryFragment(f'{apologizer_names} said "sorry" to {recipient.name}.')
    elif chars:
        apologizer = chars[0]
        apologizer.Love += 5
        if to:
            recipient_name = to.name if isinstance(to, Character) else str(to)
            return StoryFragment(f'{apologizer.name} said "I\'m sorry" to {recipient_name}.')
        return StoryFragment(f'{apologizer.name} said "I\'m sorry."')
    
    return StoryFragment("an apology was made", kernel_name="Apology")


@REGISTRY.kernel("Forgiveness")
def kernel_forgiveness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character forgives another.
    
    Patterns from dataset:
      - Forgiveness(Max)     -- Max forgives
      - Forgiveness(Mom)     -- authority figure forgives
      - Often paired with preceding Apology
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        forgiver = chars[0]
        forgiver.Anger = max(0, forgiver.Anger - 15)
        forgiver.Joy += 5
        
        if len(chars) >= 2:
            forgiven = chars[1]
            return StoryFragment(f"{forgiver.name} forgave {forgiven.name}.")
        return StoryFragment(f"{forgiver.name} forgave them.")
    
    return StoryFragment("forgiveness was given", kernel_name="Forgiveness")


# =============================================================================
# NARRATIVE PATTERN KERNELS
# =============================================================================

@REGISTRY.kernel("Quest")
def kernel_quest(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character goes on a quest or mission.
    
    Patterns from dataset:
      - Quest(Bunny, state=..., obstacle=..., catalyst=..., process=..., result=...)
      - Quest(Max, Lucy, clue=..., setting=..., outcome=...)
      - Quest(Tim, Goal(...), Process(...), Consequence(...), Resolution(...))
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    # Extract various kwargs
    goal = kwargs.get('goal', kwargs.get('Goal', kwargs.get('longing', '')))
    process = kwargs.get('process', kwargs.get('Process', kwargs.get('steps', '')))
    outcome = kwargs.get('outcome', kwargs.get('result', kwargs.get('Outcome', '')))
    obstacle = kwargs.get('obstacle', kwargs.get('Obstacle', ''))
    setting = kwargs.get('setting', '')
    clue = kwargs.get('clue', '')
    
    parts = []
    
    if chars:
        hero = chars[0]
        hero.Fear += 3  # Adventure involves some fear
        
        # Opening
        if goal:
            parts.append(f"{hero.name} set out to {_to_phrase(goal)}.")
        elif clue:
            parts.append(f"{hero.name} followed the clue of {_to_phrase(clue)}.")
        else:
            parts.append(f"{hero.name} went on an adventure.")
        
        # Setting
        if setting:
            parts.append(f"The journey took them to the {_to_phrase(setting)}.")
        
        # Obstacle
        if obstacle:
            parts.append(f"But there was {_to_phrase(obstacle)} in the way.")
        
        # Process
        if process:
            parts.append(f"{hero.name} {_action_to_phrase(process)}.")
        
        # Outcome
        if outcome:
            hero.Joy += 10
            hero.Fear -= 5
            parts.append(f"In the end, {_to_phrase(outcome)}!")
    else:
        parts.append("There was a great quest.")
        if goal:
            parts.append(f"The goal was to {_to_phrase(goal)}.")
    
    return StoryFragment(' '.join(parts), kernel_name="Quest")


@REGISTRY.kernel("Loss")
def kernel_loss(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character or thing is lost.
    
    Patterns from dataset:
      - Loss(Apple)           -- an object is lost
      - Loss(Mommy, Sick)     -- companion temporarily unavailable
      - Loss(ball)            -- toy is lost
      - Consequence(Loss(salad)+Sad(Rabbit))  -- as part of consequence
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # Check for modifier like Sick
    modifier = None
    for arg in args:
        if isinstance(arg, StoryFragment):
            modifier = arg.kernel_name or str(arg)
    
    if chars and not objects:
        # Loss(Character) - character is lost or unavailable
        lost_one = chars[0]
        if modifier:
            return StoryFragment(f"{lost_one.name} was {_to_phrase(modifier).lower()} and could not come.")
        return StoryFragment(f"{lost_one.name} was gone.")
    
    if objects:
        # Loss(object) - an object is lost
        lost_thing = objects[0]
        if ctx.current_focus:
            ctx.current_focus.Sadness += 10
            ctx.current_focus.Joy -= 5
            return StoryFragment(f"The {lost_thing} was lost. {ctx.current_focus.name} was very sad.")
        return StoryFragment(f"The {lost_thing} was lost.")
    
    return StoryFragment("something was lost", kernel_name="Loss")


@REGISTRY.kernel("Resolution")
def kernel_resolution(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Story resolution - how things are wrapped up.
    
    Patterns from dataset:
      - Resolution(Hug(Tom,Lily)+Share(BigNut)+Happy)  -- compound resolution
      - Resolution(share(chair, Tim, Sam))              -- specific action
      - Resolution(MutualWin + FunTogether)             -- abstract concepts
    """
    # Get any embedded actions/states
    parts = []
    
    for arg in args:
        if isinstance(arg, StoryFragment):
            if arg.text:
                parts.append(arg.text)
        elif isinstance(arg, Character):
            parts.append(f"{arg.name} was happy")
        elif isinstance(arg, str):
            parts.append(_to_phrase(arg))
    
    # Check kwargs for common resolution patterns
    if 'promise' in kwargs:
        parts.insert(0, f"With a promise to {_to_phrase(kwargs['promise'])},")
    
    if parts:
        text = ' and '.join(parts)
        # Ensure proper capitalization and punctuation
        text = text.strip()
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        if not text.endswith('.') and not text.endswith('!'):
            text += '.'
        
        # Update character states - resolution is usually positive
        for char in ctx.characters.values():
            char.Joy += 5
            char.Fear -= 3
        
        return StoryFragment(text, kernel_name="Resolution")
    
    return StoryFragment("Everything worked out in the end.", kernel_name="Resolution")


# =============================================================================
# SUPPORTING KERNELS (commonly paired with the main ones above)
# =============================================================================

@REGISTRY.kernel("RuleFollow")
def kernel_rule_follow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters agree to follow rules."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} agreed to follow the rules from now on.")
    elif chars:
        return StoryFragment(f"{chars[0].name} promised to follow the rules.")
    
    return StoryFragment("Everyone agreed to follow the rules.", kernel_name="RuleFollow")


@REGISTRY.kernel("Fall")
def kernel_fall(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character or thing falls."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    # If there are characters, they are the subject
    if chars:
        actor = chars[0]
        actor.Fear += 5
        actor.Sadness += 3
        if objects:
            # Fall(Lily, ground) -> "Lily fell to the ground"
            return StoryFragment(f"{actor.name} fell to the {_to_phrase(objects[0])}.")
        return StoryFragment(f"{actor.name} fell down.")
    
    # No explicit character - check if it's describing where something fell
    # Fall(ground) is likely describing where something else (implicit) fell
    if objects:
        place = _to_phrase(objects[0])
        # Check if there's a subject from context
        actor = _get_default_actor(ctx, [])
        if actor and place in ['ground', 'floor', 'down']:
            # Implicit subject fell to a place
            return StoryFragment(f"it fell to the {place}", kernel_name="Fall")
        return StoryFragment(f"fell to the {place}", kernel_name="Fall")
    
    return StoryFragment("there was a fall", kernel_name="Fall")


@REGISTRY.kernel("Slip")
def kernel_slip(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character slips on something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    slipper = chars[0] if chars else ctx.current_focus
    cause = objects[0] if objects else ''
    
    if slipper:
        slipper.Fear += 3
        if cause:
            return StoryFragment(f"{slipper.name} slipped on the {cause}.")
        return StoryFragment(f"{slipper.name} slipped.")
    
    return StoryFragment("someone slipped", kernel_name="Slip")


@REGISTRY.kernel("Injury")
def kernel_injury(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character gets injured."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    injured = chars[0] if chars else ctx.current_focus
    body_part = objects[0] if objects else ''
    
    if injured:
        injured.Sadness += 10
        injured.Joy -= 5
        if body_part:
            return StoryFragment(f"{injured.name} hurt their {body_part}.")
        return StoryFragment(f"{injured.name} got hurt.")
    
    if body_part:
        return StoryFragment(f"the {body_part} was hurt", kernel_name="Injury")
    return StoryFragment("someone got hurt", kernel_name="Injury")


@REGISTRY.kernel("Trip")
def kernel_trip(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character trips."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 2
        return StoryFragment(f"{chars[0].name} tripped.")
    
    return StoryFragment("there was a trip", kernel_name="Trip")


# =============================================================================
# EMOTION KERNELS
# =============================================================================

@REGISTRY.kernel("Sad")
def kernel_sad(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character is sad.
    
    Patterns:
      - Sad(Tim)           -- Tim is sad
      - Sad(boy)           -- the boy is sad
      - state=Sad          -- as part of problem description
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 15
        chars[0].Joy -= 10
        return StoryFragment(f"{chars[0].name} felt very sad.")
    
    return StoryFragment("there was sadness", kernel_name="Sad")


@REGISTRY.kernel("Angry")
def kernel_angry(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is angry."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Anger += 15
        return StoryFragment(f"{chars[0].name} was angry.")
    
    return StoryFragment("there was anger", kernel_name="Angry")


@REGISTRY.kernel("Calm")
def kernel_calm(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character becomes calm."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear -= 10
        chars[0].Anger -= 10
        return StoryFragment(f"{chars[0].name} felt calm.")
    
    return StoryFragment("everything became calm", kernel_name="Calm")


# =============================================================================
# ACTION KERNELS
# =============================================================================

@REGISTRY.kernel("Search")
def kernel_search(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character searches for something.
    
    Patterns:
      - Search(parents)                    -- looking for parents
      - process=Search + Heed(Voice)       -- as part of quest
      - Search(under(trees)+behind(bushes))-- searching locations
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    searcher = chars[0] if chars else ctx.current_focus
    target = objects[0] if objects else ''
    
    if searcher:
        if target:
            return StoryFragment(f"{searcher.name} searched for {_to_phrase(target)}.")
        return StoryFragment(f"{searcher.name} searched everywhere.")
    
    if target:
        return StoryFragment(f"there was a search for {_to_phrase(target)}", kernel_name="Search")
    return StoryFragment("there was a search", kernel_name="Search")


@REGISTRY.kernel("Clean")
def kernel_clean(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character cleans something.
    
    Patterns:
      - Clean(toys)              -- clean up toys
      - Clean(car, tool=cloth)   -- clean with tool
      - Clean(room)              -- clean a room
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    tool = kwargs.get('tool', '')
    
    cleaner = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'up'
    
    if cleaner:
        if tool:
            return StoryFragment(f"{cleaner.name} cleaned the {thing} with a {tool}.")
        return StoryFragment(f"{cleaner.name} cleaned the {thing}.")
    
    return StoryFragment(f"the {thing} was cleaned", kernel_name="Clean")


@REGISTRY.kernel("Jump")
def kernel_jump(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character jumps."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    jumper = chars[0] if chars else ctx.current_focus
    over = objects[0] if objects else ''
    
    if jumper:
        if over:
            return StoryFragment(f"{jumper.name} jumped over the {over}.")
        return StoryFragment(f"{jumper.name} jumped up high.")
    
    return StoryFragment("there was jumping", kernel_name="Jump")


@REGISTRY.kernel("Fly")
def kernel_fly(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character flies."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 10
        return StoryFragment(f"{chars[0].name} flew through the air.")
    
    return StoryFragment("there was flying", kernel_name="Fly")


# =============================================================================
# NARRATIVE PATTERN KERNELS
# =============================================================================

@REGISTRY.kernel("Transformation")
def kernel_transformation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character or situation transforms.
    
    Patterns:
      - Transformation(Village, Kindness)   -- village becomes kinder
      - Transformation(Tim, Brave)          -- character becomes brave
      - transformation=Skill(Build)+Teach   -- at end of growth arc
      - Transformation(Play(Pirates) + SafeLight([flashlight, lantern])) -- ongoing activity transforms
    """
    chars = [a for a in args if isinstance(a, Character)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    objects = [str(a) for a in args if not isinstance(a, (Character, StoryFragment))]
    
    # Handle transformation content from fragments
    if fragments:
        # Combine multiple fragments into a coherent transformation
        transformation_parts = []
        has_verb = False
        for frag in fragments:
            text = _to_phrase(frag)
            # Skip empty or very short fragments
            if not text or len(text.strip()) < 2:
                continue
            # Clean up verb forms - make sure they're in proper tense for past narrative
            if text.startswith('playing'):
                text = 'continued playing'
                has_verb = True
            elif text.startswith('pretending'):
                text = 'continued ' + text  # "continued pretending to be..."
                has_verb = True
            elif text.startswith('using'):
                text = 'used' + text[5:]  # "using X" -> "used X"
                has_verb = True
            transformation_parts.append(text)
        
        if transformation_parts:
            transformation_text = ' and '.join(transformation_parts)
            if chars:
                char = chars[0]
                char.Joy += 10
                # If parts are states/feelings (not verbs), use "felt"
                if not has_verb and any(word in transformation_text for word in ['comforted', 'happy', 'sad', 'confident', 'brave', 'safe', 'warm', 'loved']):
                    return StoryFragment(f"After that, {char.name} felt {transformation_text}.")
                return StoryFragment(f"After that, {char.name} {transformation_text}.")
            return StoryFragment(f"From then on, they {transformation_text}.", kernel_name="Transformation")
    
    # Simple transformation with trait
    if chars:
        char = chars[0]
        trait = objects[0] if objects else 'different'
        char.Joy += 10
        return StoryFragment(f"{char.name} was transformed and became {_to_phrase(trait)}.")
    
    if len(objects) >= 2:
        return StoryFragment(f"The {objects[0]} was filled with {_to_phrase(objects[1])}.")
    elif objects:
        return StoryFragment(f"Everything changed to {_to_phrase(objects[0])}.")
    
    return StoryFragment("Everything was transformed.", kernel_name="Transformation")


@REGISTRY.kernel("Praise")
def kernel_praise(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Someone praises another/something.
    
    Patterns:
      - Praise(Villagers, newCloth)         -- villagers praise something
      - Validation(Mom, reaction=Hug+Praise)-- mom praises
      - Praise(Mom, Tim)                    -- mom praises Tim
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        praiser = chars[0]
        praised = chars[1]
        praised.Joy += 10
        praised.Love += 5
        return StoryFragment(f"{praiser.name} praised {praised.name} for doing a great job.")
    elif chars:
        praiser = chars[0]
        if objects:
            return StoryFragment(f"{praiser.name} praised the wonderful {objects[0]}.")
        return StoryFragment(f"{praiser.name} gave praise.")
    
    if objects:
        return StoryFragment(f"Everyone praised the {objects[0]}.")
    return StoryFragment("There was much praise.", kernel_name="Praise")


@REGISTRY.kernel("Celebrate")
def kernel_celebrate(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters celebrate."""
    chars = [a for a in args if isinstance(a, Character)]
    
    for c in chars:
        c.Joy += 15
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} celebrated together!")
    elif chars:
        return StoryFragment(f"{chars[0].name} celebrated!")
    
    return StoryFragment("Everyone celebrated!", kernel_name="Celebrate")


@REGISTRY.kernel("Teach")
def kernel_teach(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character teaches another.
    
    Patterns:
      - Teach(Mom, Lily, skill=Build(tower))
      - Teach(Lily, Brother, skill=Build)
    """
    chars = [a for a in args if isinstance(a, Character)]
    skill = kwargs.get('skill', '')
    
    if len(chars) >= 2:
        teacher = chars[0]
        student = chars[1]
        student.Joy += 5
        if skill:
            return StoryFragment(f"{teacher.name} taught {student.name} how to {_to_phrase(skill)}.")
        return StoryFragment(f"{teacher.name} taught {student.name} something new.")
    elif chars:
        if skill:
            return StoryFragment(f"{chars[0].name} learned to {_to_phrase(skill)}.")
        return StoryFragment(f"{chars[0].name} learned something new.")
    
    return StoryFragment("There was teaching and learning.", kernel_name="Teach")


@REGISTRY.kernel("Cooperate")
def kernel_cooperate(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters work together."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    task = objects[0] if objects else ''
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        for c in chars:
            c.Joy += 5
            c.Love += 3
        if task:
            return StoryFragment(f"{names} worked together to {_to_phrase(task)}.")
        return StoryFragment(f"{names} worked together as a team.")
    elif chars:
        if task:
            return StoryFragment(f"{chars[0].name} helped with {_to_phrase(task)}.")
        return StoryFragment(f"{chars[0].name} cooperated.")
    
    return StoryFragment("Everyone worked together.", kernel_name="Cooperate")


# =============================================================================
# DAILY ACTIVITY KERNELS
# =============================================================================

@REGISTRY.kernel("Sleep")
def kernel_sleep(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character sleeps.
    
    Patterns:
      - Sleep(Lily)                  -- Lily goes to sleep
      - Sleep(Lily, state=Dream(...))-- sleeping and dreaming
    """
    chars = [a for a in args if isinstance(a, Character)]
    state = kwargs.get('state', '')
    
    if chars:
        if state:
            return StoryFragment(f"{chars[0].name} went to sleep and {_to_phrase(state)}.")
        return StoryFragment(f"{chars[0].name} went to sleep.")
    
    return StoryFragment("everyone went to sleep", kernel_name="Sleep")


@REGISTRY.kernel("Wake")
def kernel_wake(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character wakes up."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} woke up.")
    
    return StoryFragment("everyone woke up", kernel_name="Wake")


@REGISTRY.kernel("Dream")
def kernel_dream(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character dreams.
    
    Patterns:
      - Dream(Lily, bird)      -- Lily dreams of bird
      - Dream(Flight)          -- a dream of flight
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f"{chars[0].name} dreamed about {_to_phrase(objects[0])}.")
        return StoryFragment(f"{chars[0].name} had a wonderful dream.")
    
    if objects:
        return StoryFragment(f"there was a dream of {_to_phrase(objects[0])}", kernel_name="Dream")
    return StoryFragment("there were dreams", kernel_name="Dream")


@REGISTRY.kernel("Eat")
def kernel_eat(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character eats something.
    
    Patterns:
      - Eat(spaghetti)       -- eating food
      - Eat(apples)          -- eating item
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    eater = chars[0] if chars else ctx.current_focus
    food = objects[0] if objects else 'food'
    
    if eater:
        eater.Joy += 3
        return StoryFragment(f"{eater.name} ate the {food}.")
    
    return StoryFragment(f"the {food} was eaten", kernel_name="Eat")


@REGISTRY.kernel("Rest")
def kernel_rest(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character rests."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    location = objects[0] if objects else ''
    
    if chars:
        chars[0].Fear -= 5
        if location:
            return StoryFragment(f"{chars[0].name} rested by the {location}.")
        return StoryFragment(f"{chars[0].name} took a rest.")
    
    return StoryFragment("everyone took a rest", kernel_name="Rest")


@REGISTRY.kernel("Sit")
def kernel_sit(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character sits down."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    where = objects[0] if objects else ''
    
    if chars:
        if where:
            return StoryFragment(f"{chars[0].name} sat down on the {where}.")
        return StoryFragment(f"{chars[0].name} sat down.")
    
    return StoryFragment("everyone sat down", kernel_name="Sit")


# =============================================================================
# COMMUNICATION KERNELS  
# =============================================================================

@REGISTRY.kernel("Ask")
def kernel_ask(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character asks for something.
    
    Patterns:
      - Ask(Bird, help)              -- asking for help
      - Ask(Lily, Dad, Fix(teddy))   -- asking someone to do something
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        asker = chars[0]
        askee = chars[1]
        what = objects[0] if objects else 'for help'
        return StoryFragment(f"{asker.name} asked {askee.name} {_to_phrase(what)}.")
    elif chars:
        what = objects[0] if objects else 'for help'
        return StoryFragment(f"{chars[0].name} asked {_to_phrase(what)}.")
    
    return StoryFragment("someone asked for help", kernel_name="Ask")


@REGISTRY.kernel("Talk")
def kernel_talk(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters talk."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} talked together.")
    elif chars:
        return StoryFragment(f"{chars[0].name} talked.")
    
    return StoryFragment("they talked", kernel_name="Talk")


@REGISTRY.kernel("Listen")
def kernel_listen(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character listens."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        return StoryFragment(f"{chars[0].name} listened to {chars[1].name}.")
    elif chars:
        if objects:
            return StoryFragment(f"{chars[0].name} listened to the {objects[0]}.")
        return StoryFragment(f"{chars[0].name} listened carefully.")
    
    return StoryFragment("someone listened", kernel_name="Listen")


@REGISTRY.kernel("Call")
def kernel_call(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character calls out."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        return StoryFragment(f"{chars[0].name} called out to {chars[1].name}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} called out.")
    
    return StoryFragment("someone called out", kernel_name="Call")


# =============================================================================
# OBJECT MANIPULATION KERNELS
# =============================================================================

@REGISTRY.kernel("Fix")
def kernel_fix(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character fixes something.
    
    Patterns:
      - Fix(teddy)           -- fix a toy
      - Fix(car)             -- fix an object
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    fixer = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if fixer:
        fixer.Joy += 5
        return StoryFragment(f"{fixer.name} fixed the {thing}.")
    
    return StoryFragment(f"the {thing} was fixed", kernel_name="Fix")


@REGISTRY.kernel("Show")
def kernel_show(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character shows something to another.
    
    Patterns:
      - Show(Max, Buddy, cube)      -- Max shows cube to Buddy
      - Show(Timmy, to=Mom, object=car)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    to = kwargs.get('to', None)
    obj = kwargs.get('object', '')
    
    thing = obj if obj else (objects[0] if objects else 'it')
    
    if len(chars) >= 2:
        return StoryFragment(f"{chars[0].name} showed the {thing} to {chars[1].name}.")
    elif chars:
        if to:
            to_name = to.name if isinstance(to, Character) else str(to)
            return StoryFragment(f"{chars[0].name} showed the {thing} to {to_name}.")
        return StoryFragment(f"{chars[0].name} showed off the {thing}.")
    
    return StoryFragment(f"the {thing} was shown", kernel_name="Show")


@REGISTRY.kernel("Push")
def kernel_push(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character pushes something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    pusher = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if pusher:
        return StoryFragment(f"{pusher.name} pushed the {thing}.")
    
    return StoryFragment(f"the {thing} was pushed", kernel_name="Push")


@REGISTRY.kernel("Pull")
def kernel_pull(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character pulls something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    puller = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if puller:
        return StoryFragment(f"{puller.name} pulled the {thing}.")
    
    return StoryFragment(f"the {thing} was pulled", kernel_name="Pull")


@REGISTRY.kernel("Open")
def kernel_open(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character opens something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    opener = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if opener:
        return StoryFragment(f"{opener.name} opened the {thing}.")
    
    return StoryFragment(f"the {thing} was opened", kernel_name="Open")


@REGISTRY.kernel("Close")
def kernel_close(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character closes something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    closer = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if closer:
        return StoryFragment(f"{closer.name} closed the {thing}.")
    
    return StoryFragment(f"the {thing} was closed", kernel_name="Close")


@REGISTRY.kernel("Touch")
def kernel_touch(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character touches something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    toucher = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if toucher:
        return StoryFragment(f"{toucher.name} touched the {thing}.")
    
    return StoryFragment(f"the {thing} was touched", kernel_name="Touch")


@REGISTRY.kernel("Hold")
def kernel_hold(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character holds something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    holder = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if holder:
        return StoryFragment(f"{holder.name} held the {thing}.")
    
    return StoryFragment(f"the {thing} was held", kernel_name="Hold")


@REGISTRY.kernel("Lift")
def kernel_lift(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character lifts something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    lifter = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if lifter:
        return StoryFragment(f"{lifter.name} lifted the {thing}.")
    
    return StoryFragment(f"the {thing} was lifted", kernel_name="Lift")


@REGISTRY.kernel("Shake")
def kernel_shake(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character shakes something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    shaker = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if shaker:
        return StoryFragment(f"{shaker.name} shook the {thing}.")
    
    return StoryFragment(f"the {thing} shook", kernel_name="Shake")


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    from gen5 import generate_story
    
    print("=" * 70)
    print("TESTING gen5k01 KERNELS")
    print("=" * 70)
    
    test_kernels = [
        # Test 1: Apology and Forgiveness (from dataset patterns)
        '''
Tim(Character, boy, Naughty + Curious)
Mom(Character, adult, Caring)

Conflict(Tim, Mom)
Apology(Tim, to=Mom)
Forgiveness(Mom)
Happy(Tim)
''',
        
        # Test 2: Quest pattern (from dataset)
        '''
Bunny(Character, rabbit, Happy + Playful)

Quest(Bunny,
    goal=Find(cake),
    obstacle=Height,
    process=Jump + Reach,
    outcome=Satisfaction + Joy)
''',
        
        # Test 3: Loss and Resolution
        '''
Lily(Character, girl, Curious)
Tim(Character, boy, Friend)

Play(Lily, Tim, toy=ball)
Loss(ball)
Sadness(Lily)
Resolution(Find(ball) + Happy)
''',

        # Test 4: Full cautionary with apology (dataset pattern)
        '''
Lily(Character, child, Brave)
Max(Character, child, Cautious + Caring)

Cautionary(
    event=Accident(Lily, process=Climb + Slip + Fall),
    consequence=Injury(Lily)
)
Help(Max, Lily)
Apology(Lily)
Forgiveness(Max)
RuleFollow(Lily, Max)
''',
    ]
    
    for i, kernel in enumerate(test_kernels, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}")
        print(f"{'='*70}")
        print("KERNEL:")
        print(kernel.strip())
        print("\nGENERATED:")
        print(generate_story(kernel))
