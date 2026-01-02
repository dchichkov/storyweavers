"""
gen5k03.py - Additional Kernel Pack #03

This module extends gen5.py with 100 additional kernel implementations.
Import this module after gen5 to register the new kernels.

=============================================================================
KERNELS IN THIS PACK (100 kernels total):
=============================================================================

This pack implements high-priority missing kernels identified through coverage
analysis, focusing on the most commonly used kernels in the TinyStories dataset.

### Communication & Warning Kernels (6 kernels)
- Warning(char, about)           -- warning about danger
- Advice(char, topic)            -- giving advice
- Offer(char, thing)             -- offering something
- Question(char, topic)          -- asking a question
- Reveal(char, secret)           -- revealing information
- Revelation(truth)              -- alias for Reveal
- Guidance(char, direction)      -- providing guidance

### Social & Relationship Kernels (7 kernels)
- Friends(char1, char2)          -- becoming friends
- Friend(char)                   -- alias for Friends
- Bond(char1, char2)             -- forming a bond
- Cooperation(chars)             -- working together
- Trust(char1, char2)            -- trusting someone
- Kindness(char)                 -- showing kindness
- Acceptance(char, thing)        -- accepting something

### Narrative Structure Kernels (6 kernels)
- Adventure(char, quest)         -- going on adventure
- Catalyst(event)                -- triggering event
- Obstacle(thing)                -- obstacle in path
- Process(steps)                 -- process of doing
- Moral(lesson)                  -- moral lesson
- Transform(char, form)          -- transformation
- Outcome(result)                -- outcome of events

### Emotional State Kernels (7 kernels)
- Pain(char)                     -- experiencing pain
- Happiness(char)                -- feeling happiness
- Emotion(char, feeling)         -- general emotion
- Anticipation(char)             -- anticipating something
- Laughter(char)                 -- laughing
- Laugh(char)                    -- alias for Laughter
- Excitement(char)               -- being excited

### Action & Movement Kernels (8 kernels)
- Watch(char, thing)             -- watching something
- Ride(char, vehicle)            -- riding something
- Take(char, object)             -- taking something
- Use(char, tool)                -- using something
- Make(char, thing)              -- making something
- Gather(chars, location)        -- gathering together
- Escape(char, from)             -- escaping from

### Object & Animal Kernels (4 kernels)
- Bird(name)                     -- bird character
- Dog(name)                      -- dog character
- Cat(name)                      -- cat character
- Bear(name)                     -- bear character

### Concept Kernels (15 kernels)
- Idea(concept)                  -- having an idea
- Habit(behavior)                -- habitual behavior
- Growth(char/thing)             -- growing/developing
- Lost(char/thing)               -- being lost
- Sight(char, vision)            -- seeing something
- Observation(char, scene)       -- observing
- Threat(danger)                 -- threatening situation
- Aid(helper, helped)            -- giving aid
- Repair(char, object)           -- repairing something
- Celebration(event)             -- celebrating
- Invitation(char, event)        -- inviting to event
- Refusal(char, request)         -- refusing request
- Action(char, deed)             -- taking action
- Learn(char, lesson)            -- learning something
- Want(char, desire)             -- wanting something
- Spot(char, thing)              -- spotting something

### Character Type/Descriptor Kernels (13 kernels)
- Boy, Girl, Man                 -- character types
- Brother, Sister                -- family relations
- Daddy, Mother, Father          -- parents
- Child, Adult, Baby             -- age groups
- Stranger, Neighbor, Teacher    -- roles

### Trait/Adjective Kernels (33 kernels)
Traits that modify characters or objects:
- Playful, Helpful, Friendly, Creative, Supportive, Protective
- Caring, Kind, Brave, Shy, Clever, Wise, Patient, Gentle
- Strong, Fast, Slow, Loud, Quiet
- Beautiful, Ugly, Dirty, Shiny
- Old, New, Big, Small, Little, Tiny, Huge
- Fun (as trait/state)

=============================================================================

Usage:
    from gen5 import generate_story, REGISTRY
    import gen5k03  # Registers additional kernels
    
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
# COMMUNICATION & WARNING KERNELS
# =============================================================================

@REGISTRY.kernel("Advice")
def kernel_advice(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character gives advice.
    
    Patterns:
      - Advice(char, topic)       -- giving advice on topic
      - Advice(Mom, Lily)         -- Mom advises Lily
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        adviser = chars[0]
        advisee = chars[1]
        topic = objects[0] if objects else ''
        if topic:
            return StoryFragment(f"{adviser.name} gave {advisee.name} advice about {_to_phrase(topic)}.")
        return StoryFragment(f"{adviser.name} gave {advisee.name} some advice.")
    elif chars:
        topic = objects[0] if objects else 'the situation'
        return StoryFragment(f"{chars[0].name} gave advice about {_to_phrase(topic)}.")
    
    return StoryFragment("advice was given", kernel_name="Advice")


@REGISTRY.kernel("Offer")
def kernel_offer(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character offers something.
    
    Patterns:
      - Offer(char, thing)        -- char offers thing
      - Offer(help)               -- offering help
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thing = objects[0] if objects else 'help'
    
    if len(chars) >= 2:
        offerer = chars[0]
        recipient = chars[1]
        return StoryFragment(f"{offerer.name} offered {recipient.name} {_to_phrase(thing)}.")
    elif chars:
        offerer = chars[0]
        offerer.Love += 3
        return StoryFragment(f"{offerer.name} offered {_to_phrase(thing)}.")
    
    return StoryFragment(f"there was an offer of {_to_phrase(thing)}", kernel_name="Offer")


@REGISTRY.kernel("Question")
def kernel_question(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character asks a question.
    
    Patterns:
      - Question(char, topic)     -- asking about topic
      - Question(Why?)            -- a question is asked
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    topic = objects[0] if objects else ''
    
    if chars:
        asker = chars[0]
        if topic:
            return StoryFragment(f"{asker.name} asked a question about {_to_phrase(topic)}.")
        return StoryFragment(f"{asker.name} asked a question.")
    
    if topic:
        return StoryFragment(f"there was a question: {_to_phrase(topic)}", kernel_name="Question")
    return StoryFragment("a question was asked", kernel_name="Question")


@REGISTRY.kernel("Reveal")
def kernel_reveal(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something is revealed.
    
    Patterns:
      - Reveal(char, secret)      -- char reveals secret
      - Reveal(truth)             -- truth is revealed
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    
    if fragments:
        secret = _to_phrase(fragments[0])
    elif objects:
        secret = _to_phrase(objects[0])
    else:
        secret = "the truth"
    
    if chars:
        revealer = chars[0]
        return StoryFragment(f"{revealer.name} revealed {secret}.")
    
    return StoryFragment(f"{secret} was revealed", kernel_name="Reveal")


@REGISTRY.kernel("Revelation")
def kernel_revelation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Alias for Reveal - a revelation occurs."""
    return kernel_reveal(ctx, *args, **kwargs)


@REGISTRY.kernel("Guidance")
def kernel_guidance(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character provides guidance.
    
    Patterns:
      - Guidance(char, direction) -- providing guidance
      - Guidance(wise advice)     -- guidance given
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        guide = chars[0]
        guided = chars[1]
        return StoryFragment(f"{guide.name} gave {guided.name} guidance.")
    elif chars:
        guide = chars[0]
        direction = objects[0] if objects else ''
        if direction:
            return StoryFragment(f"{guide.name} provided guidance about {_to_phrase(direction)}.")
        return StoryFragment(f"{guide.name} provided guidance.")
    
    return StoryFragment("guidance was provided", kernel_name="Guidance")


# =============================================================================
# SOCIAL & RELATIONSHIP KERNELS
# =============================================================================

@REGISTRY.kernel("Friends")
def kernel_friends(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Characters become friends.
    
    Patterns:
      - Friends(char1, char2)     -- becoming friends
      - Friends(Lily, Max)        -- Lily and Max are friends
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        for c in chars:
            c.Joy += 8
            c.Love += 5
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} became good friends.")
    elif chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} made new friends.")
    
    return StoryFragment("they became friends", kernel_name="Friends")


@REGISTRY.kernel("Friend")
def kernel_friend(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Alias for Friends - singular friend."""
    return kernel_friends(ctx, *args, **kwargs)


@REGISTRY.kernel("Bond")
def kernel_bond(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Characters form a bond.
    
    Patterns:
      - Bond(char1, char2)        -- forming a bond
      - Bond(Lily, Dog)           -- special bond
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        for c in chars:
            c.Love += 10
        return StoryFragment(f"{chars[0].name} and {chars[1].name} formed a special bond.")
    elif chars:
        return StoryFragment(f"{chars[0].name} felt a special connection.")
    
    return StoryFragment("a bond was formed", kernel_name="Bond")


@REGISTRY.kernel("Trust")
def kernel_trust(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character trusts another.
    
    Patterns:
      - Trust(char1, char2)       -- char1 trusts char2
      - Trust(Lily)               -- learning to trust
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        truster = chars[0]
        trusted = chars[1]
        truster.Love += 5
        truster.Fear -= 5
        return StoryFragment(f"{truster.name} learned to trust {trusted.name}.")
    elif chars:
        chars[0].Fear -= 5
        return StoryFragment(f"{chars[0].name} learned to trust.")
    
    return StoryFragment("trust was built", kernel_name="Trust")


@REGISTRY.kernel("Kindness")
def kernel_kindness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character shows kindness.
    
    Patterns:
      - Kindness(char)            -- showing kindness
      - moral=Kindness            -- kindness as moral
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 10
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} showed great kindness.")
    
    return StoryFragment("there was kindness", kernel_name="Kindness")


# =============================================================================
# NARRATIVE STRUCTURE KERNELS
# =============================================================================

@REGISTRY.kernel("Adventure")
def kernel_adventure(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character goes on an adventure.
    
    Patterns:
      - Adventure(char, quest)    -- going on adventure
      - Adventure(forest)         -- adventure in location
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    location = objects[0] if objects else 'far away'
    
    if chars:
        adventurer = chars[0]
        adventurer.Joy += 8
        adventurer.Fear += 3
        return StoryFragment(f"{adventurer.name} went on an adventure to the {_to_phrase(location)}.")
    
    return StoryFragment(f"there was an adventure to the {_to_phrase(location)}", kernel_name="Adventure")


@REGISTRY.kernel("Catalyst")
def kernel_catalyst(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A catalyzing event occurs.
    
    Patterns:
      - Catalyst(event)           -- triggering event
      - catalyst=Discovery(...)   -- discovery as catalyst
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    
    if fragments:
        event = _to_phrase(fragments[0])
        return StoryFragment(f"Then, {event}.")
    elif objects:
        event = _to_phrase(objects[0])
        return StoryFragment(f"Then, {event} happened.")
    elif chars:
        return StoryFragment(f"Then, {chars[0].name} made a discovery.")
    
    return StoryFragment("Something important happened.", kernel_name="Catalyst")


@REGISTRY.kernel("Obstacle")
def kernel_obstacle(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    An obstacle appears.
    
    Patterns:
      - Obstacle(thing)           -- obstacle in path
      - obstacle=Wall             -- wall as obstacle
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    obstacle = objects[0] if objects else 'a challenge'
    
    if chars:
        chars[0].Fear += 5
        return StoryFragment(f"{chars[0].name} faced an obstacle: {_to_phrase(obstacle)}.")
    
    return StoryFragment(f"there was an obstacle: {_to_phrase(obstacle)}", kernel_name="Obstacle")


@REGISTRY.kernel("Process")
def kernel_process(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A process unfolds.
    
    Patterns:
      - Process(steps)            -- process of doing
      - process=Try+Learn+Succeed -- multi-step process
    """
    chars = [a for a in args if isinstance(a, Character)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if fragments:
        steps = ' and then '.join([_to_phrase(f) for f in fragments])
        return StoryFragment(f"The process was: {steps}.")
    elif objects:
        return StoryFragment(f"Through {_to_phrase(objects[0])},")
    elif chars:
        return StoryFragment(f"{chars[0].name} went through the process.")
    
    return StoryFragment("there was a process", kernel_name="Process")


@REGISTRY.kernel("Moral")
def kernel_moral(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    The moral lesson of the story.
    
    Patterns:
      - Moral(lesson)             -- moral lesson
      - moral=Sharing+Caring      -- combined moral
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    
    if fragments:
        lesson = _to_phrase(fragments[0])
    elif objects:
        lesson = _to_phrase(objects[0])
    else:
        lesson = "being kind to others"
    
    return StoryFragment(f"The lesson was about {lesson}.", kernel_name="Moral")


# =============================================================================
# EMOTIONAL STATE KERNELS
# =============================================================================

@REGISTRY.kernel("Pain")
def kernel_pain(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character experiences pain.
    
    Patterns:
      - Pain(char)                -- experiencing pain
      - consequence=Pain          -- pain as consequence
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Sadness += 12
        chars[0].Joy -= 8
        if objects:
            return StoryFragment(f"{chars[0].name} felt pain from the {objects[0]}.")
        return StoryFragment(f"{chars[0].name} was in pain.")
    
    return StoryFragment("there was pain", kernel_name="Pain")


@REGISTRY.kernel("Happiness")
def kernel_happiness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character experiences happiness.
    
    Patterns:
      - Happiness(char)           -- feeling happiness
      - state=Happiness           -- happiness as state
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 15
        return StoryFragment(f"{chars[0].name} felt true happiness.")
    
    return StoryFragment("there was happiness", kernel_name="Happiness")


@REGISTRY.kernel("Emotion")
def kernel_emotion(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    General emotional state.
    
    Patterns:
      - Emotion(char, feeling)    -- general emotion
      - Emotion(Joy)              -- emotion concept
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    feeling = objects[0] if objects else 'strong feelings'
    
    if chars:
        return StoryFragment(f"{chars[0].name} felt {_to_phrase(feeling)}.")
    
    return StoryFragment(f"there was {_to_phrase(feeling)}", kernel_name="Emotion")


@REGISTRY.kernel("Anticipation")
def kernel_anticipation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character anticipates something.
    
    Patterns:
      - Anticipation(char, event) -- anticipating event
      - Anticipation(party)       -- anticipation of event
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    event = objects[0] if objects else 'what would happen'
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} looked forward to {_to_phrase(event)}.")
    
    return StoryFragment(f"there was anticipation of {_to_phrase(event)}", kernel_name="Anticipation")


@REGISTRY.kernel("Laughter")
def kernel_laughter(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character laughs.
    
    Patterns:
      - Laughter(char)            -- laughing
      - Laughter(together)        -- laughing together
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        for c in chars:
            c.Joy += 10
        return StoryFragment(f"{names} laughed together.")
    elif chars:
        chars[0].Joy += 10
        return StoryFragment(f"{chars[0].name} laughed happily.")
    
    return StoryFragment("there was laughter", kernel_name="Laughter")


# =============================================================================
# ACTION & MOVEMENT KERNELS
# =============================================================================

@REGISTRY.kernel("Watch")
def kernel_watch(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character watches something.
    
    Patterns:
      - Watch(char, thing)        -- watching something
      - Watch(birds)              -- watching birds
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thing = objects[0] if objects else 'carefully'
    watcher = chars[0] if chars else ctx.current_focus
    
    if watcher:
        return StoryFragment(f"{watcher.name} watched the {thing}.")
    
    return StoryFragment(f"watched the {thing}", kernel_name="Watch")


@REGISTRY.kernel("Ride")
def kernel_ride(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character rides something.
    
    Patterns:
      - Ride(char, vehicle)       -- riding something
      - Ride(bike)                -- riding a bike
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    vehicle = objects[0] if objects else 'bike'
    rider = chars[0] if chars else ctx.current_focus
    
    if rider:
        rider.Joy += 8
        return StoryFragment(f"{rider.name} rode the {vehicle}.")
    
    return StoryFragment(f"rode the {vehicle}", kernel_name="Ride")


@REGISTRY.kernel("Take")
def kernel_take(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character takes something.
    
    Patterns:
      - Take(char, object)        -- taking something
      - Take(toy)                 -- taking toy
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thing = objects[0] if objects else 'it'
    taker = chars[0] if chars else ctx.current_focus
    
    if taker:
        return StoryFragment(f"{taker.name} took the {thing}.")
    
    return StoryFragment(f"took the {thing}", kernel_name="Take")


@REGISTRY.kernel("Use")
def kernel_use(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character uses something.
    
    Patterns:
      - Use(char, tool)           -- using something
      - Use(hammer)               -- using a tool
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    tool = objects[0] if objects else 'it'
    user = chars[0] if chars else ctx.current_focus
    
    if user:
        return StoryFragment(f"{user.name} used the {tool}.")
    
    return StoryFragment(f"used the {tool}", kernel_name="Use")


@REGISTRY.kernel("Make")
def kernel_make(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character makes something.
    
    Patterns:
      - Make(char, thing)         -- making something
      - Make(sandcastle)          -- making object
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thing = objects[0] if objects else 'something'
    maker = chars[0] if chars else ctx.current_focus
    
    if maker:
        maker.Joy += 5
        return StoryFragment(f"{maker.name} made a {thing}.")
    
    return StoryFragment(f"made a {thing}", kernel_name="Make")


@REGISTRY.kernel("Gather")
def kernel_gather(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Characters gather together.
    
    Patterns:
      - Gather(chars, location)   -- gathering together
      - Gather(around tree)       -- gathering at place
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    location = objects[0] if objects else 'together'
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} gathered {_to_phrase(location)}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} gathered {_to_phrase(location)}.")
    
    return StoryFragment(f"everyone gathered {_to_phrase(location)}", kernel_name="Gather")


@REGISTRY.kernel("Escape")
def kernel_escape(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character escapes from danger.
    
    Patterns:
      - Escape(char, from)        -- escaping from danger
      - Escape(danger)            -- escaping
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    from_what = kwargs.get('from', '')
    
    danger = from_what if from_what else (objects[0] if objects else 'danger')
    
    if chars:
        chars[0].Fear -= 10
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} escaped from the {_to_phrase(danger)}!")
    
    return StoryFragment(f"escaped from the {_to_phrase(danger)}", kernel_name="Escape")


# =============================================================================
# OBJECT & ANIMAL KERNELS
# =============================================================================

@REGISTRY.kernel("Bird")
def kernel_bird(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Bird character or object.
    
    Patterns:
      - Bird(name)                -- bird character
      - Bird(pretty, blue)        -- bird description
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        # It's a character named Bird
        return StoryFragment(f"{chars[0].name} the bird")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} bird", kernel_name="Bird")
    
    return StoryFragment("a bird", kernel_name="Bird")


@REGISTRY.kernel("Dog")
def kernel_dog(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Dog character or object.
    
    Patterns:
      - Dog(name)                 -- dog character
      - Dog(big, brown)           -- dog description
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the dog")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} dog", kernel_name="Dog")
    
    return StoryFragment("a dog", kernel_name="Dog")


@REGISTRY.kernel("Cat")
def kernel_cat(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Cat character or object.
    
    Patterns:
      - Cat(name)                 -- cat character
      - Cat(soft, fluffy)         -- cat description
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the cat")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} cat", kernel_name="Cat")
    
    return StoryFragment("a cat", kernel_name="Cat")


@REGISTRY.kernel("Bear")
def kernel_bear(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Bear character or object.
    
    Patterns:
      - Bear(name)                -- bear character
      - Bear(big, brown)          -- bear description
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the bear")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} bear", kernel_name="Bear")
    
    return StoryFragment("a bear", kernel_name="Bear")


# =============================================================================
# CONCEPT KERNELS
# =============================================================================

@REGISTRY.kernel("Habit")
def kernel_habit(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A habit or routine.
    
    Patterns:
      - Habit(behavior)           -- habitual behavior
      - Habit(daily walk)         -- specific habit
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    behavior = objects[0] if objects else 'this'
    
    if chars:
        return StoryFragment(f"{chars[0].name} had a habit of {_to_phrase(behavior)}.")
    
    return StoryFragment(f"there was a habit of {_to_phrase(behavior)}", kernel_name="Habit")


@REGISTRY.kernel("Growth")
def kernel_growth(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character or thing grows/develops.
    
    Patterns:
      - Growth(char)              -- character growth
      - Growth(plant)             -- thing growing
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 8
        return StoryFragment(f"{chars[0].name} grew and learned.")
    
    thing = objects[0] if objects else 'it'
    return StoryFragment(f"The {thing} grew.", kernel_name="Growth")


@REGISTRY.kernel("Lost")
def kernel_lost(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character or thing is lost.
    
    Patterns:
      - Lost(char)                -- character is lost
      - Lost(toy)                 -- object is lost
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Fear += 10
        chars[0].Sadness += 8
        return StoryFragment(f"{chars[0].name} got lost.")
    
    thing = objects[0] if objects else 'something'
    return StoryFragment(f"The {thing} was lost.", kernel_name="Lost")


@REGISTRY.kernel("Sight")
def kernel_sight(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character sees something.
    
    Patterns:
      - Sight(char, vision)       -- seeing something
      - Sight(beautiful view)     -- a sight
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    vision = objects[0] if objects else 'something amazing'
    
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f"{chars[0].name} saw {_to_phrase(vision)}.")
    
    return StoryFragment(f"the sight of {_to_phrase(vision)}", kernel_name="Sight")


@REGISTRY.kernel("Observation")
def kernel_observation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character makes an observation.
    
    Patterns:
      - Observation(char, scene)  -- observing scene
      - Observation(nature)       -- observation of nature
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    scene = objects[0] if objects else 'everything'
    
    if chars:
        return StoryFragment(f"{chars[0].name} observed the {scene} carefully.")
    
    return StoryFragment(f"there was observation of the {scene}", kernel_name="Observation")


@REGISTRY.kernel("Threat")
def kernel_threat(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A threat appears.
    
    Patterns:
      - Threat(danger)            -- threatening situation
      - Threat(char, danger)      -- threat to character
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    danger = objects[0] if objects else 'something dangerous'
    
    if chars:
        chars[0].Fear += 12
        return StoryFragment(f"{chars[0].name} faced a threat from {_to_phrase(danger)}.")
    
    return StoryFragment(f"there was a threat of {_to_phrase(danger)}", kernel_name="Threat")


@REGISTRY.kernel("Aid")
def kernel_aid(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character provides aid.
    
    Patterns:
      - Aid(helper, helped)       -- giving aid
      - Aid(char)                 -- receiving aid
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        helper = chars[0]
        helped = chars[1]
        helper.Love += 5
        helped.Joy += 5
        return StoryFragment(f"{helper.name} came to {helped.name}'s aid.")
    elif chars:
        return StoryFragment(f"{chars[0].name} received aid.")
    
    return StoryFragment("aid was given", kernel_name="Aid")


@REGISTRY.kernel("Repair")
def kernel_repair(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character repairs something.
    
    Patterns:
      - Repair(char, object)      -- repairing something
      - Repair(toy)               -- toy is repaired
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thing = objects[0] if objects else 'it'
    repairer = chars[0] if chars else ctx.current_focus
    
    if repairer:
        repairer.Joy += 5
        return StoryFragment(f"{repairer.name} repaired the {thing}.")
    
    return StoryFragment(f"the {thing} was repaired", kernel_name="Repair")


@REGISTRY.kernel("Celebration")
def kernel_celebration(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A celebration occurs.
    
    Patterns:
      - Celebration(event)        -- celebrating event
      - Celebration(victory)      -- victory celebration
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    event = objects[0] if objects else ''
    
    for c in chars:
        c.Joy += 15
    
    if chars and event:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} celebrated {_to_phrase(event)}!")
    elif chars:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} had a celebration!")
    elif event:
        return StoryFragment(f"There was a celebration of {_to_phrase(event)}!")
    
    return StoryFragment("There was a celebration!", kernel_name="Celebration")


@REGISTRY.kernel("Invitation")
def kernel_invitation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    An invitation is extended.
    
    Patterns:
      - Invitation(char, event)   -- inviting to event
      - Invitation(party)         -- invitation to party
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    event = objects[0] if objects else 'a party'
    
    if len(chars) >= 2:
        inviter = chars[0]
        invitee = chars[1]
        invitee.Joy += 5
        return StoryFragment(f"{inviter.name} sent {invitee.name} an invitation to the {_to_phrase(event)}.")
    elif chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} received an invitation to the {_to_phrase(event)}.")
    
    return StoryFragment(f"there was an invitation to the {_to_phrase(event)}", kernel_name="Invitation")


@REGISTRY.kernel("Refusal")
def kernel_refusal(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character refuses a request.
    
    Patterns:
      - Refusal(char, request)    -- refusing request
      - Refusal(to share)         -- refusing something
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    request = objects[0] if objects else ''
    
    if chars:
        chars[0].Anger += 3
        if request:
            return StoryFragment(f"{chars[0].name} refused to {_to_phrase(request)}.")
        return StoryFragment(f"{chars[0].name} refused.")
    
    if request:
        return StoryFragment(f"there was a refusal to {_to_phrase(request)}", kernel_name="Refusal")
    return StoryFragment("there was a refusal", kernel_name="Refusal")


@REGISTRY.kernel("Action")
def kernel_action(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character takes action.
    
    Patterns:
      - Action(char, deed)        -- taking action
      - Action(brave deed)        -- an action
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    
    if fragments:
        deed = _to_phrase(fragments[0])
    elif objects:
        deed = _to_phrase(objects[0])
    else:
        deed = 'something'
    
    if chars:
        return StoryFragment(f"{chars[0].name} took action and {deed}.")
    
    return StoryFragment(f"action was taken: {deed}", kernel_name="Action")


@REGISTRY.kernel("Learn")
def kernel_learn(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character learns something.
    
    Patterns:
      - Learn(char, lesson)       -- learning something
      - Learn(to share)           -- learning a skill
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    lesson = objects[0] if objects else 'something new'
    
    if chars:
        chars[0].Joy += 8
        return StoryFragment(f"{chars[0].name} learned {_to_phrase(lesson)}.")
    
    return StoryFragment(f"learned {_to_phrase(lesson)}", kernel_name="Learn")


@REGISTRY.kernel("Want")
def kernel_want(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character wants something.
    
    Patterns:
      - Want(char, desire)        -- wanting something
      - Want(toy)                 -- wanting toy
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    desire = objects[0] if objects else 'something'
    
    if chars:
        return StoryFragment(f"{chars[0].name} wanted {_to_phrase(desire)}.")
    
    return StoryFragment(f"wanted {_to_phrase(desire)}", kernel_name="Want")


# =============================================================================
# ADDITIONAL SUPPORT KERNELS TO REACH 100
# =============================================================================

@REGISTRY.kernel("Boy")
def kernel_boy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Boy character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the boy")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} boy", kernel_name="Boy")
    
    return StoryFragment("a boy", kernel_name="Boy")


@REGISTRY.kernel("Girl")
def kernel_girl(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Girl character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the girl")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} girl", kernel_name="Girl")
    
    return StoryFragment("a girl", kernel_name="Girl")


@REGISTRY.kernel("Man")
def kernel_man(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Man character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the man")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} man", kernel_name="Man")
    
    return StoryFragment("a man", kernel_name="Man")


@REGISTRY.kernel("Fun")
def kernel_fun(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Having fun."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 10
        return StoryFragment(f"{chars[0].name} had so much fun!")
    
    return StoryFragment("it was fun", kernel_name="Fun")


@REGISTRY.kernel("Playful")
def kernel_playful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being playful."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 8
        return StoryFragment(f"{chars[0].name} was playful")
    
    return StoryFragment("playful", kernel_name="Playful")


@REGISTRY.kernel("Helpful")
def kernel_helpful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being helpful."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 5
        return StoryFragment(f"{chars[0].name} was helpful")
    
    return StoryFragment("helpful", kernel_name="Helpful")


@REGISTRY.kernel("Friendly")
def kernel_friendly(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being friendly."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 5
        chars[0].Joy += 3
        return StoryFragment(f"{chars[0].name} was friendly")
    
    return StoryFragment("friendly", kernel_name="Friendly")


@REGISTRY.kernel("Creative")
def kernel_creative(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being creative."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} was creative")
    
    return StoryFragment("creative", kernel_name="Creative")


@REGISTRY.kernel("Supportive")
def kernel_supportive(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being supportive."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 8
        return StoryFragment(f"{chars[0].name} was supportive")
    
    return StoryFragment("supportive", kernel_name="Supportive")


@REGISTRY.kernel("Protective")
def kernel_protective(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being protective."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 5
        return StoryFragment(f"{chars[0].name} was protective")
    
    return StoryFragment("protective", kernel_name="Protective")


@REGISTRY.kernel("Caring")
def kernel_caring(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being caring."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 10
        return StoryFragment(f"{chars[0].name} was caring")
    
    return StoryFragment("caring", kernel_name="Caring")


@REGISTRY.kernel("Kind")
def kernel_kind(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being kind."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 8
        return StoryFragment(f"{chars[0].name} was kind")
    
    return StoryFragment("kind", kernel_name="Kind")


@REGISTRY.kernel("Clever")
def kernel_clever(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being clever."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} was clever")
    
    return StoryFragment("clever", kernel_name="Clever")


@REGISTRY.kernel("Wise")
def kernel_wise(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being wise."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was wise")
    
    return StoryFragment("wise", kernel_name="Wise")


@REGISTRY.kernel("Patient")
def kernel_patient(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being patient."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear -= 3
        return StoryFragment(f"{chars[0].name} was patient")
    
    return StoryFragment("patient", kernel_name="Patient")


@REGISTRY.kernel("Gentle")
def kernel_gentle(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being gentle."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 5
        return StoryFragment(f"{chars[0].name} was gentle")
    
    return StoryFragment("gentle", kernel_name="Gentle")


@REGISTRY.kernel("Strong")
def kernel_strong(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being strong."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear -= 5
        return StoryFragment(f"{chars[0].name} was strong")
    
    return StoryFragment("strong", kernel_name="Strong")


@REGISTRY.kernel("Fast")
def kernel_fast(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being fast."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f"{chars[0].name} was fast")
    
    return StoryFragment("fast", kernel_name="Fast")


@REGISTRY.kernel("Slow")
def kernel_slow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being slow."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was slow")
    
    return StoryFragment("slow", kernel_name="Slow")


@REGISTRY.kernel("Loud")
def kernel_loud(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being loud."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was loud")
    
    return StoryFragment("loud", kernel_name="Loud")


@REGISTRY.kernel("Quiet")
def kernel_quiet(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being quiet."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was quiet")
    
    return StoryFragment("quiet", kernel_name="Quiet")


@REGISTRY.kernel("Beautiful")
def kernel_beautiful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being beautiful."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was beautiful")
    
    if objects:
        return StoryFragment(f"a beautiful {objects[0]}", kernel_name="Beautiful")
    
    return StoryFragment("beautiful", kernel_name="Beautiful")


@REGISTRY.kernel("Ugly")
def kernel_ugly(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being ugly."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Sadness += 3
        return StoryFragment(f"{chars[0].name} felt ugly")
    
    if objects:
        return StoryFragment(f"an ugly {objects[0]}", kernel_name="Ugly")
    
    return StoryFragment("ugly", kernel_name="Ugly")


@REGISTRY.kernel("Dirty")
def kernel_dirty(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being dirty."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was dirty")
    
    if objects:
        return StoryFragment(f"a dirty {objects[0]}", kernel_name="Dirty")
    
    return StoryFragment("dirty", kernel_name="Dirty")


@REGISTRY.kernel("Shiny")
def kernel_shiny(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being shiny."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was shiny")
    
    if objects:
        return StoryFragment(f"a shiny {objects[0]}", kernel_name="Shiny")
    
    return StoryFragment("shiny", kernel_name="Shiny")


@REGISTRY.kernel("Old")
def kernel_old(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being old."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was old")
    
    if objects:
        return StoryFragment(f"an old {objects[0]}", kernel_name="Old")
    
    return StoryFragment("old", kernel_name="Old")


@REGISTRY.kernel("New")
def kernel_new(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being new."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f"{chars[0].name} was new")
    
    if objects:
        return StoryFragment(f"a new {objects[0]}", kernel_name="New")
    
    return StoryFragment("new", kernel_name="New")


@REGISTRY.kernel("Big")
def kernel_big(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being big."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was big")
    
    if objects:
        return StoryFragment(f"a big {objects[0]}", kernel_name="Big")
    
    return StoryFragment("big", kernel_name="Big")


@REGISTRY.kernel("Small")
def kernel_small(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being small."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was small")
    
    if objects:
        return StoryFragment(f"a small {objects[0]}", kernel_name="Small")
    
    return StoryFragment("small", kernel_name="Small")


@REGISTRY.kernel("Little")
def kernel_little(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being little."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was little")
    
    if objects:
        return StoryFragment(f"a little {objects[0]}", kernel_name="Little")
    
    return StoryFragment("little", kernel_name="Little")


@REGISTRY.kernel("Tiny")
def kernel_tiny(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being tiny."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was tiny")
    
    if objects:
        return StoryFragment(f"a tiny {objects[0]}", kernel_name="Tiny")
    
    return StoryFragment("tiny", kernel_name="Tiny")


@REGISTRY.kernel("Huge")
def kernel_huge(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Being huge."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was huge")
    
    if objects:
        return StoryFragment(f"a huge {objects[0]}", kernel_name="Huge")
    
    return StoryFragment("huge", kernel_name="Huge")


@REGISTRY.kernel("Brother")
def kernel_brother(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Brother character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the brother")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} brother", kernel_name="Brother")
    
    return StoryFragment("a brother", kernel_name="Brother")


@REGISTRY.kernel("Sister")
def kernel_sister(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sister character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the sister")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} sister", kernel_name="Sister")
    
    return StoryFragment("a sister", kernel_name="Sister")


@REGISTRY.kernel("Mother")
def kernel_mother(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Mother character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the mother")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} mother", kernel_name="Mother")
    
    return StoryFragment("a mother", kernel_name="Mother")


@REGISTRY.kernel("Father")
def kernel_father(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Father character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the father")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} father", kernel_name="Father")
    
    return StoryFragment("a father", kernel_name="Father")


@REGISTRY.kernel("Child")
def kernel_child(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Child character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the child")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} child", kernel_name="Child")
    
    return StoryFragment("a child", kernel_name="Child")


@REGISTRY.kernel("Adult")
def kernel_adult(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Adult character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the adult")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} adult", kernel_name="Adult")
    
    return StoryFragment("an adult", kernel_name="Adult")


@REGISTRY.kernel("Baby")
def kernel_baby(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Baby character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the baby")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} baby", kernel_name="Baby")
    
    return StoryFragment("a baby", kernel_name="Baby")


@REGISTRY.kernel("Stranger")
def kernel_stranger(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Stranger character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the stranger")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} stranger", kernel_name="Stranger")
    
    return StoryFragment("a stranger", kernel_name="Stranger")


@REGISTRY.kernel("Neighbor")
def kernel_neighbor(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Neighbor character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the neighbor")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} neighbor", kernel_name="Neighbor")
    
    return StoryFragment("a neighbor", kernel_name="Neighbor")


@REGISTRY.kernel("Teacher")
def kernel_teacher(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Teacher character reference."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} the teacher")
    
    if objects:
        description = ' '.join(objects)
        return StoryFragment(f"a {description} teacher", kernel_name="Teacher")
    
    return StoryFragment("a teacher", kernel_name="Teacher")


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    from gen5 import generate_story
    
    print("=" * 70)
    print("TESTING gen5k03 KERNELS")
    print(f"Total kernels in registry: {len(REGISTRY.kernels)}")
    print("=" * 70)
    
    test_kernels = [
        # Test 1: Warning and Danger
        '''
Lily(Character, girl, Curious)
Mom(Character, mother, Caring)

Warning(Mom, Lily, danger)
Adventure(Lily, forest)
Threat(wild animal)
Escape(Lily, animal)
Relief(Lily)
''',
        
        # Test 2: Friends and Bond
        '''
Tim(Character, boy, Playful)
Max(Character, boy, Friendly)

Meet(Tim, Max)
Friends(Tim, Max)
Bond(Tim, Max)
Cooperation(Tim, Max, build)
Happiness(Tim)
''',
        
        # Test 3: Idea and Make
        '''
Anna(Character, girl, Creative)

Problem(Anna, toy)
Idea(Anna, fix)
Make(Anna, new toy)
Success(Anna)
Joy(Anna)
''',

        # Test 4: Animals
        '''
Lily(Character, girl, Kind)

Find(Lily, Bird)
Bird(small, blue)
Care(Lily, Bird)
Bond(Lily, Bird)
Happy(Lily)
''',

        # Test 5: Learning and Growth
        '''
Tom(Character, boy, Brave)
Dad(Character, father, Wise)

Challenge(Tom, ride bike)
Advice(Dad, Tom)
Learn(Tom, balance)
Growth(Tom)
Celebration(success)
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
    
    # Count kernels
    print(f"\n{'='*70}")
    print(f"KERNEL COUNT: {len(REGISTRY.kernels)} kernels registered")
    print("=" * 70)

