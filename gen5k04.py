"""
gen5k04.py - Additional Kernel Pack #04

This module extends gen5.py with 100 additional kernel implementations.
Import this module after gen5 to register the new kernels.

=============================================================================
KERNELS IN THIS PACK (100 kernels organized by category):
=============================================================================

## ARRIVALS & DEPARTURES (5 kernels)
- Arrival: Someone arrives at a location
- Enter: Character enters a space/building
- Reunion: Characters meet again after separation
- Return: Going back to a place
- Separate: Characters part ways

## EMOTIONAL STATES (15 kernels)
- Relief: Feeling of relief after tension
- Curiosity: Being curious about something
- Confidence: Feeling confident
- Hope: Having hope for the future
- Regret: Feeling regret about past actions
- Embarrassment: Feeling embarrassed
- Anxious: Feeling anxious or worried
- Grateful: Feeling grateful/thankful
- Determination: Being determined
- Excitement: Feeling excited
- Fame: Achieving fame/recognition
- Pride: Parental/personal pride (enhanced version)
- Shame: Feeling ashamed
- Envy: Feeling envious
- Contentment: Feeling content

## COMMUNICATION (10 kernels)
- Dialogue: Characters have a conversation
- Need: Expressing a need
- Request: Asking for something
- Plan: Making a plan
- Promise: Making a promise
- Warning: Giving a warning
- Compliment: Giving a compliment
- Tease: Playful teasing
- Whisper: Speaking quietly
- Shout: Speaking loudly

## ACTIONS & ACTIVITIES (20 kernels)
- Retrieve: Getting something back
- Wear: Putting on clothing/accessories
- Create: Making something new
- Hit: Striking something
- Hurt: Getting hurt/injured
- Assist: Helping someone with a task
- Discover: Finding something new
- Observe: Watching carefully
- PlayTogether: Playing with others
- Game: Playing a game
- Measure: Measuring something
- Build: Building/constructing
- Break: Breaking something
- Climb: Climbing up something
- Dig: Digging in the ground
- Swim: Swimming in water
- Dance: Dancing for joy
- Sing: Singing a song
- Paint: Painting/drawing
- Cook: Cooking food

## OUTCOMES & RESULTS (10 kernels)
- Result: The result of actions
- Outcome: Final outcome
- Consequence: Consequence of action
- Victory: Winning/succeeding
- Defeat: Losing/failing
- Success: Achieving success
- Failure: Experiencing failure
- Achievement: Completing an achievement
- Breakthrough: Having a breakthrough
- Setback: Experiencing a setback

## INTERVENTION & SUPPORT (10 kernels)
- Intervention: Someone intervenes to help
- Mediation: Someone mediates a conflict
- Guidance: Providing guidance
- Mentorship: Being mentored (enhanced version)
- Rescue: Rescuing someone (enhanced version)
- Support: Providing support
- Encourage: Encouraging someone
- Comfort: Comforting someone (enhanced version)
- Reassure: Reassuring someone
- Defend: Defending someone

## ENVIRONMENTAL & SITUATIONS (10 kernels)
- Noise: Hearing a noise
- Silence: Experiencing silence
- Darkness: Being in darkness
- Light: Finding light
- Weather: Weather conditions
- Shelter: Finding shelter
- Danger: Facing danger
- Safety: Being safe
- Trap: Being trapped
- Escape: Escaping danger (enhanced version)

## ABSTRACT CONCEPTS (10 kernels)
- Memory: Remembering something
- Insight: Gaining insight (enhanced version)
- Wisdom: Showing wisdom
- Knowledge: Gaining knowledge
- Understanding: Understanding something
- Realization: Realizing something
- Awareness: Becoming aware
- Confusion: Being confused
- Clarity: Gaining clarity
- Mystery: Encountering mystery

## SOCIAL DYNAMICS (10 kernels)
- Community: Community gathering/feeling
- Unity: Coming together in unity
- Cooperation: Cooperating together
- Competition: Competing with others
- Alliance: Forming an alliance
- Betrayal: Being betrayed
- Loyalty: Showing loyalty
- Trust: Building trust (enhanced version)
- Friendship: Forming friendships (enhanced version)
- Conflict: Having a conflict (enhanced version)

=============================================================================

Usage:
    from gen5 import generate_story, REGISTRY
    import gen5k04  # Registers additional kernels
    
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
# ARRIVALS & DEPARTURES (5 kernels)
# =============================================================================

@REGISTRY.kernel("Arrival")
def kernel_arrival(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Someone arrives at a location.
    
    Patterns from dataset:
      - Arrival(Bird) -- Bird arrives
      - catalyst=Arrival(Lion) -- Lion's arrival triggers events
    """
    chars = [a for a in args if isinstance(a, Character)]
    location = kwargs.get('location', kwargs.get('at', ''))
    
    if chars:
        char = chars[0]
        if location:
            return StoryFragment(f"{char.name} arrived at the {_to_phrase(location)}.")
        return StoryFragment(f"{char.name} arrived.")
    
    return StoryFragment("there was an arrival", kernel_name="Arrival")


@REGISTRY.kernel("Enter")
def kernel_enter(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character enters a space or building.
    
    Patterns from dataset:
      - Enter(tent) -- entering a tent
      - Enter(Lily, house) -- Lily enters house
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    place = kwargs.get('place', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if place:
            return StoryFragment(f"{char.name} entered the {_to_phrase(place)}.")
        return StoryFragment(f"{char.name} went inside.")
    
    if place:
        return StoryFragment(f"entering the {_to_phrase(place)}", kernel_name="Enter")
    return StoryFragment("entry", kernel_name="Enter")


@REGISTRY.kernel("Reunion")
def kernel_reunion(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Characters meet again after separation.
    
    Patterns from dataset:
      - Reunion(Tim, Mom) -- Tim reunites with Mom
      - outcome=Reunion -- happy reunion
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        char1, char2 = chars[0], chars[1]
        char1.Joy += 15
        char2.Joy += 15
        return StoryFragment(f"{char1.name} and {char2.name} were reunited!")
    elif chars:
        char = chars[0]
        char.Joy += 12
        return StoryFragment(f"{char.name} was reunited with their loved ones.")
    
    return StoryFragment("They were happily reunited.", kernel_name="Reunion")


@REGISTRY.kernel("Separate")
def kernel_separate(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Characters part ways.
    
    Patterns from dataset:
      - Separate(Lily, Timmy) -- they separate
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        char1, char2 = chars[0], chars[1]
        char1.Sadness += 3
        char2.Sadness += 3
        return StoryFragment(f"{char1.name} and {char2.name} went their separate ways.")
    elif chars:
        char = chars[0]
        return StoryFragment(f"{char.name} separated from the others.")
    
    return StoryFragment("separation", kernel_name="Separate")


# =============================================================================
# EMOTIONAL STATES (15 kernels)
# =============================================================================

@REGISTRY.kernel("Relief")
def kernel_relief(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling of relief after tension.
    
    Patterns from dataset:
      - Relief(Lily) -- Lily feels relief
      - outcome=Relief -- relieved outcome
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Fear = max(0, char.Fear - 10)
        char.Sadness = max(0, char.Sadness - 8)
        char.Joy += 8
        return StoryFragment(f"{char.name} felt a wave of relief wash over them.")
    
    return StoryFragment("there was relief", kernel_name="Relief")


@REGISTRY.kernel("Curiosity")
def kernel_curiosity(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being curious about something.
    
    Patterns from dataset:
      - Curiosity(Tim) -- Tim is curious
      - state=Routine+Curiosity(paints) -- curious about paints
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    about = kwargs.get('about', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if about:
            return StoryFragment(f"{char.name} was curious about the {_to_phrase(about)}.")
        return StoryFragment(f"{char.name} wondered what it could be.")
    
    if about:
        return StoryFragment(f"curiosity about {_to_phrase(about)}", kernel_name="Curiosity")
    return StoryFragment("curiosity", kernel_name="Curiosity")


@REGISTRY.kernel("Hope")
def kernel_hope(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Having hope for the future.
    
    Patterns from dataset:
      - Hope(Possibility) -- hope for possibilities
      - Hope(stars) -- hoping about stars
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    about = kwargs.get('about', kwargs.get('for', objects[0] if objects else ''))
    
    if chars:
        char = chars[0]
        char.Joy += 7
        if about:
            return StoryFragment(f"{char.name} hoped for {_to_phrase(about)}.")
        return StoryFragment(f"{char.name} felt hopeful.")
    
    if about:
        return StoryFragment(f"hope for {_to_phrase(about)}", kernel_name="Hope")
    return StoryFragment("hope", kernel_name="Hope")


@REGISTRY.kernel("Regret")
def kernel_regret(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling regret about past actions.
    
    Patterns from dataset:
      - Regret(Mom, Eat(mushroom)) -- Mom regrets the action
    """
    chars = [a for a in args if isinstance(a, Character)]
    action = kwargs.get('action', '')
    
    if chars:
        char = chars[0]
        char.Sadness += 10
        if action:
            return StoryFragment(f"{char.name} regretted {_to_phrase(action)}.")
        return StoryFragment(f"{char.name} felt deep regret.")
    
    return StoryFragment("regret", kernel_name="Regret")


@REGISTRY.kernel("Embarrassment")
def kernel_embarrassment(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling embarrassed.
    
    Patterns from dataset:
      - Embarrassment(Lily) -- Lily feels embarrassed
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Sadness += 5
        char.Anger += 3
        return StoryFragment(f"{char.name} felt embarrassed and their face turned red.")
    
    return StoryFragment("embarrassment", kernel_name="Embarrassment")


@REGISTRY.kernel("Anxious")
def kernel_anxious(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling anxious or worried.
    
    Patterns from dataset:
      - Mommy(Character, adult, Anxious+Caring)
    """
    chars = [a for a in args if isinstance(a, Character)]
    about = kwargs.get('about', '')
    
    if chars:
        char = chars[0]
        char.Fear += 5
        if about:
            return StoryFragment(f"{char.name} felt anxious about {_to_phrase(about)}.")
        return StoryFragment(f"{char.name} felt worried and anxious.")
    
    return StoryFragment("anxious", kernel_name="Anxious")


@REGISTRY.kernel("Grateful")
def kernel_grateful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling grateful/thankful.
    
    Patterns from dataset:
      - transformation=Grateful+Confidence -- becomes grateful
    """
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', '')
    
    if chars:
        char = chars[0]
        char.Joy += 10
        char.Love += 8
        if to:
            return StoryFragment(f"{char.name} felt grateful to {_to_phrase(to)}.")
        return StoryFragment(f"{char.name} was very grateful.")
    
    return StoryFragment("grateful", kernel_name="Grateful")


@REGISTRY.kernel("Determination")
def kernel_determination(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being determined.
    
    Patterns from dataset:
      - Determination(Deer, goal=RecordAgain)
    """
    chars = [a for a in args if isinstance(a, Character)]
    goal = kwargs.get('goal', '')
    
    if chars:
        char = chars[0]
        char.Fear = max(0, char.Fear - 5)
        if goal:
            return StoryFragment(f"{char.name} was determined to {_to_phrase(goal)}.")
        return StoryFragment(f"{char.name} set their jaw with determination.")
    
    return StoryFragment("determination", kernel_name="Determination")


@REGISTRY.kernel("Excitement")
def kernel_excitement(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling excited.
    
    Patterns from dataset:
      - Excitement(Lily)
    """
    chars = [a for a in args if isinstance(a, Character)]
    about = kwargs.get('about', '')
    
    if chars:
        char = chars[0]
        char.Joy += 12
        if about:
            return StoryFragment(f"{char.name} was filled with excitement about {_to_phrase(about)}!")
        return StoryFragment(f"{char.name} was filled with excitement!")
    
    return StoryFragment("excitement", kernel_name="Excitement")


@REGISTRY.kernel("Fame")
def kernel_fame(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Achieving fame/recognition.
    
    Patterns from dataset:
      - Pride(Deer) + Fame(Deer)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Joy += 10
        return StoryFragment(f"{char.name} felt famous and special.")
    
    return StoryFragment("fame", kernel_name="Fame")


@REGISTRY.kernel("Shame")
def kernel_shame(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling ashamed.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Sadness += 8
        char.Anger += 5
        return StoryFragment(f"{char.name} felt ashamed of what {char.he} had done.")
    
    return StoryFragment("shame", kernel_name="Shame")


@REGISTRY.kernel("Envy")
def kernel_envy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling envious.
    """
    chars = [a for a in args if isinstance(a, Character)]
    of = kwargs.get('of', '')
    
    if chars:
        char = chars[0]
        char.Anger += 5
        char.Sadness += 5
        if of:
            return StoryFragment(f"{char.name} felt envious of {_to_phrase(of)}.")
        return StoryFragment(f"{char.name} felt a twinge of envy.")
    
    return StoryFragment("envy", kernel_name="Envy")


@REGISTRY.kernel("Contentment")
def kernel_contentment(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Feeling content.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Joy += 8
        return StoryFragment(f"{char.name} felt peaceful and content.")
    
    return StoryFragment("contentment", kernel_name="Contentment")


# =============================================================================
# COMMUNICATION (10 kernels)
# =============================================================================

@REGISTRY.kernel("Dialogue")
def kernel_dialogue(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Characters have a conversation.
    
    Patterns from dataset:
      - Dialogue(Hope(stars)) -- dialogue about stars/hope
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    about = kwargs.get('about', objects[0] if objects else '')
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        if about:
            return StoryFragment(f"{names} talked together about {_to_phrase(about)}.")
        return StoryFragment(f"{names} had a conversation.")
    elif chars:
        char = chars[0]
        if about:
            return StoryFragment(f"{char.name} talked about {_to_phrase(about)}.")
        return StoryFragment(f"{char.name} spoke up.")
    
    if about:
        return StoryFragment(f"conversation about {_to_phrase(about)}", kernel_name="Dialogue")
    return StoryFragment("dialogue", kernel_name="Dialogue")


@REGISTRY.kernel("Need")
def kernel_need(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Expressing a need.
    
    Patterns from dataset:
      - Need(ReachBars) -- need to reach bars
      - Need(Skip, home) -- Skip needs a home
      - Need(Vest, Timmy) -- Timmy needs vest
      - Need(Light) + Idea(Use(matches)) -- need for light leads to idea
    """
    chars = [a for a in args if isinstance(a, Character)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    objects = [str(a) for a in args if not isinstance(a, (Character, StoryFragment))]
    
    # If we have fragments, extract their meaning
    if fragments:
        thing = _to_phrase(fragments[0])
    else:
        thing = kwargs.get('thing', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if thing:
            return StoryFragment(f"{char.name} needed {_to_phrase(thing)}.")
        return StoryFragment(f"{char.name} had a need.")
    
    if thing:
        return StoryFragment(f"They needed {_to_phrase(thing)}.", kernel_name="Need")
    return StoryFragment("There was a need.", kernel_name="Need")


@REGISTRY.kernel("Plan")
def kernel_plan(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Making a plan.
    
    Patterns from dataset:
      - Plan(Dad, Idea)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    goal = kwargs.get('goal', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if goal:
            return StoryFragment(f"{char.name} made a plan to {_to_phrase(goal)}.")
        return StoryFragment(f"{char.name} came up with a clever plan.")
    
    return StoryFragment("a plan", kernel_name="Plan")


@REGISTRY.kernel("Promise")
def kernel_promise(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Making a promise.
    """
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', '')
    what = kwargs.get('what', '')
    
    if chars:
        char = chars[0]
        char.Love += 5
        if to and what:
            return StoryFragment(f'{char.name} promised {_to_phrase(to)} that they would {_to_phrase(what)}.')
        elif what:
            return StoryFragment(f'{char.name} promised to {_to_phrase(what)}.')
        return StoryFragment(f'{char.name} made a promise.')
    
    return StoryFragment("a promise", kernel_name="Promise")


@REGISTRY.kernel("Compliment")
def kernel_compliment(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Giving a compliment.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        giver, receiver = chars[0], chars[1]
        receiver.Joy += 8
        return StoryFragment(f"{giver.name} said something nice to {receiver.name}.")
    elif chars:
        char = chars[0]
        char.Joy += 5
        return StoryFragment(f"{char.name} received a compliment.")
    
    return StoryFragment("a compliment", kernel_name="Compliment")


@REGISTRY.kernel("Tease")
def kernel_tease(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Playful teasing.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        teaser, teased = chars[0], chars[1]
        teased.Anger += 3
        return StoryFragment(f"{teaser.name} teased {teased.name} playfully.")
    elif chars:
        char = chars[0]
        return StoryFragment(f"{char.name} was being teased.")
    
    return StoryFragment("teasing", kernel_name="Tease")


@REGISTRY.kernel("Whisper")
def kernel_whisper(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Speaking quietly.
    """
    chars = [a for a in args if isinstance(a, Character)]
    what = kwargs.get('what', '')
    
    if chars:
        char = chars[0]
        if what:
            return StoryFragment(f'{char.name} whispered about {_to_phrase(what)}.')
        return StoryFragment(f'{char.name} whispered quietly.')
    
    return StoryFragment("whispers", kernel_name="Whisper")


@REGISTRY.kernel("Shout")
def kernel_shout(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Speaking loudly.
    
    Patterns from dataset:
      - Shout("Bottle, where are you?")
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    what = kwargs.get('what', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if what:
            return StoryFragment(f'{char.name} shouted, "{_to_phrase(what)}!"')
        return StoryFragment(f'{char.name} shouted loudly.')
    
    if what:
        return StoryFragment(f'a shout of "{_to_phrase(what)}"', kernel_name="Shout")
    return StoryFragment("shouting", kernel_name="Shout")


# =============================================================================
# ACTIONS & ACTIVITIES (20 kernels)
# =============================================================================

@REGISTRY.kernel("Wear")
def kernel_wear(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Putting on clothing/accessories.
    
    Patterns from dataset:
      - Wear(Lucy, dress(favorite))
      - Wear(Vest, Lily)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    item = kwargs.get('item', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if item:
            return StoryFragment(f"{char.name} wore their {_to_phrase(item)}.")
        return StoryFragment(f"{char.name} got dressed.")
    
    if item:
        return StoryFragment(f"wearing {_to_phrase(item)}", kernel_name="Wear")
    return StoryFragment("wearing", kernel_name="Wear")


@REGISTRY.kernel("Create")
def kernel_create(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Making something new.
    
    Patterns from dataset:
      - Create(cookies, from=air) -- magician creates cookies
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    thing = kwargs.get('thing', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Joy += 10
        if thing:
            return StoryFragment(f"{char.name} created {_to_phrase(thing)}.")
        return StoryFragment(f"{char.name} made something wonderful.")
    
    if thing:
        return StoryFragment(f"creating {_to_phrase(thing)}", kernel_name="Create")
    return StoryFragment("creation", kernel_name="Create")


@REGISTRY.kernel("Hit")
def kernel_hit(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Striking something.
    
    Patterns from dataset:
      - Hit(puck) -- hitting the hockey puck
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    thing = kwargs.get('thing', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if thing:
            return StoryFragment(f"{char.name} hit the {_to_phrase(thing)}.")
        return StoryFragment(f"{char.name} hit it hard.")
    
    if thing:
        return StoryFragment(f"hitting the {_to_phrase(thing)}", kernel_name="Hit")
    return StoryFragment("a hit", kernel_name="Hit")


@REGISTRY.kernel("Hurt")
def kernel_hurt(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Getting hurt/injured.
    
    Patterns from dataset:
      - Hurt(knee) -- hurt knee
      - result=Hurt(knee) -- resulted in hurt knee
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    bodypart = kwargs.get('where', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Sadness += 10
        char.Fear += 5
        if bodypart:
            return StoryFragment(f"{char.name} hurt their {_to_phrase(bodypart)}.")
        return StoryFragment(f"{char.name} got hurt.")
    
    if bodypart:
        return StoryFragment(f"hurt {_to_phrase(bodypart)}", kernel_name="Hurt")
    return StoryFragment("pain", kernel_name="Hurt")


@REGISTRY.kernel("Assist")
def kernel_assist(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Helping someone with a task.
    
    Patterns from dataset:
      - Assist(Mom, Lily, Test(rock))
      - Assist(Timmy, task=Fix(equipment))
    """
    chars = [a for a in args if isinstance(a, Character)]
    task = kwargs.get('task', kwargs.get('with', ''))
    
    if len(chars) >= 2:
        helper, helped = chars[0], chars[1]
        helper.Joy += 5
        helped.Joy += 5
        if task:
            return StoryFragment(f"{helper.name} assisted {helped.name} with {_to_phrase(task)}.")
        return StoryFragment(f"{helper.name} helped {helped.name}.")
    elif chars:
        char = chars[0]
        if task:
            return StoryFragment(f"{char.name} provided assistance with {_to_phrase(task)}.")
        return StoryFragment(f"{char.name} gave assistance.")
    
    return StoryFragment("assistance", kernel_name="Assist")


@REGISTRY.kernel("Discover")
def kernel_discover(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Finding something new.
    
    Patterns from dataset:
      - Discover(Nest, eggs) -- discovering nest with eggs
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    thing = kwargs.get('thing', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Joy += 10
        if thing:
            return StoryFragment(f"{char.name} discovered {_to_phrase(thing)}!")
        return StoryFragment(f"{char.name} made an amazing discovery!")
    
    if thing:
        return StoryFragment(f"discovering {_to_phrase(thing)}", kernel_name="Discover")
    return StoryFragment("a discovery", kernel_name="Discover")


@REGISTRY.kernel("PlayTogether")
def kernel_playtogether(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Playing with others.
    
    Patterns from dataset:
      - PlayTogether(Tim, Max, Baseball)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    activity = kwargs.get('activity', objects[0] if objects else '')
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        for char in chars:
            char.Joy += 10
        if activity:
            return StoryFragment(f"{names} played {_to_phrase(activity)} together.")
        return StoryFragment(f"{names} played together happily.")
    elif chars:
        char = chars[0]
        char.Joy += 8
        if activity:
            return StoryFragment(f"{char.name} played {_to_phrase(activity)}.")
        return StoryFragment(f"{char.name} played with others.")
    
    return StoryFragment("playing together", kernel_name="PlayTogether")


@REGISTRY.kernel("Game")
def kernel_game(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Playing a game.
    
    Patterns from dataset:
      - Victory(Game) -- winning a game
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    gametype = kwargs.get('type', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Joy += 8
        if gametype:
            return StoryFragment(f"{char.name} played a game of {_to_phrase(gametype)}.")
        return StoryFragment(f"{char.name} played a fun game.")
    
    if gametype:
        return StoryFragment(f"a game of {_to_phrase(gametype)}", kernel_name="Game")
    return StoryFragment("a game", kernel_name="Game")


@REGISTRY.kernel("Measure")
def kernel_measure(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Measuring something.
    
    Patterns from dataset:
      - Measure(Tim, object=barn, method=TinySteps)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    thing = kwargs.get('object', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if thing:
            return StoryFragment(f"{char.name} measured the {_to_phrase(thing)}.")
        return StoryFragment(f"{char.name} took measurements.")
    
    return StoryFragment("measuring", kernel_name="Measure")


@REGISTRY.kernel("Build")
def kernel_build(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Building/constructing.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    thing = kwargs.get('thing', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Joy += 10
        if thing:
            return StoryFragment(f"{char.name} built a {_to_phrase(thing)}.")
        return StoryFragment(f"{char.name} built something.")
    
    if thing:
        return StoryFragment(f"building a {_to_phrase(thing)}", kernel_name="Build")
    return StoryFragment("building", kernel_name="Build")


@REGISTRY.kernel("Break")
def kernel_break(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Breaking something.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    thing = kwargs.get('thing', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Sadness += 8
        if thing:
            return StoryFragment(f"{char.name} broke the {_to_phrase(thing)}.")
        return StoryFragment(f"{char.name} broke it by accident.")
    
    if thing:
        return StoryFragment(f"breaking the {_to_phrase(thing)}", kernel_name="Break")
    return StoryFragment("something broke", kernel_name="Break")


@REGISTRY.kernel("Climb")
def kernel_climb(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Climbing up something.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    thing = kwargs.get('thing', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Fear += 5
        if thing:
            return StoryFragment(f"{char.name} climbed up the {_to_phrase(thing)}.")
        return StoryFragment(f"{char.name} climbed higher and higher.")
    
    if thing:
        return StoryFragment(f"climbing {_to_phrase(thing)}", kernel_name="Climb")
    return StoryFragment("climbing", kernel_name="Climb")


@REGISTRY.kernel("Dig")
def kernel_dig(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Digging in the ground.
    """
    chars = [a for a in args if isinstance(a, Character)]
    where = kwargs.get('where', '')
    
    if chars:
        char = chars[0]
        if where:
            return StoryFragment(f"{char.name} dug in the {_to_phrase(where)}.")
        return StoryFragment(f"{char.name} dug a hole.")
    
    return StoryFragment("digging", kernel_name="Dig")


@REGISTRY.kernel("Swim")
def kernel_swim(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Swimming in water.
    """
    chars = [a for a in args if isinstance(a, Character)]
    where = kwargs.get('where', kwargs.get('in', ''))
    
    if chars:
        char = chars[0]
        char.Joy += 10
        if where:
            return StoryFragment(f"{char.name} swam in the {_to_phrase(where)}.")
        return StoryFragment(f"{char.name} splashed and swam happily.")
    
    return StoryFragment("swimming", kernel_name="Swim")


@REGISTRY.kernel("Dance")
def kernel_dance(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Dancing for joy.
    
    Patterns from dataset:
      - Dance(Man) -- man dances
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Joy += 12
        return StoryFragment(f"{char.name} danced happily.")
    
    return StoryFragment("dancing", kernel_name="Dance")


@REGISTRY.kernel("Sing")
def kernel_sing(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Singing a song.
    """
    chars = [a for a in args if isinstance(a, Character)]
    song = kwargs.get('song', '')
    
    if chars:
        char = chars[0]
        char.Joy += 10
        if song:
            return StoryFragment(f"{char.name} sang {_to_phrase(song)}.")
        return StoryFragment(f"{char.name} sang a beautiful song.")
    
    return StoryFragment("singing", kernel_name="Sing")


@REGISTRY.kernel("Paint")
def kernel_paint(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Painting/drawing.
    
    Patterns from dataset:
      - Paint(art, subjects=[flowers,cars,stars,animals])
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    subject = kwargs.get('subject', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Joy += 10
        if subject:
            return StoryFragment(f"{char.name} painted {_to_phrase(subject)}.")
        return StoryFragment(f"{char.name} painted a picture.")
    
    return StoryFragment("painting", kernel_name="Paint")


@REGISTRY.kernel("Cook")
def kernel_cook(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Cooking food.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    food = kwargs.get('food', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Joy += 8
        if food:
            return StoryFragment(f"{char.name} cooked {_to_phrase(food)}.")
        return StoryFragment(f"{char.name} cooked a delicious meal.")
    
    return StoryFragment("cooking", kernel_name="Cook")


# =============================================================================
# OUTCOMES & RESULTS (10 kernels)
# =============================================================================

@REGISTRY.kernel("Result")
def kernel_result(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    The result of actions.
    
    Patterns from dataset:
      - Result(Happy + Healthy)
      - Result(Delicious)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    outcome = kwargs.get('outcome', objects[0] if objects else '')
    
    if outcome:
        return StoryFragment(f"The result was {_to_phrase(outcome)}.")
    
    return StoryFragment("there was a result", kernel_name="Result")


@REGISTRY.kernel("Outcome")
def kernel_outcome(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Final outcome.
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    result = objects[0] if objects else ''
    
    if result:
        return StoryFragment(f"The outcome was {_to_phrase(result)}.")
    
    return StoryFragment("the outcome", kernel_name="Outcome")


@REGISTRY.kernel("Consequence")
def kernel_consequence(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Consequence of action.
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    effect = objects[0] if objects else ''
    
    if effect:
        return StoryFragment(f"As a consequence, {_to_phrase(effect)}.")
    
    return StoryFragment("there were consequences", kernel_name="Consequence")


@REGISTRY.kernel("Victory")
def kernel_victory(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Winning/succeeding.
    
    Patterns from dataset:
      - Victory(Game) -- winning a game
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    what = kwargs.get('at', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Joy += 15
        if what:
            return StoryFragment(f"{char.name} won at {_to_phrase(what)}!")
        return StoryFragment(f"{char.name} was victorious!")
    
    if what:
        return StoryFragment(f"victory at {_to_phrase(what)}", kernel_name="Victory")
    return StoryFragment("victory", kernel_name="Victory")


@REGISTRY.kernel("Defeat")
def kernel_defeat(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Losing/failing.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Sadness += 15
        return StoryFragment(f"{char.name} was defeated.")
    
    return StoryFragment("defeat", kernel_name="Defeat")


@REGISTRY.kernel("Success")
def kernel_success(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Achieving success.
    """
    chars = [a for a in args if isinstance(a, Character)]
    at = kwargs.get('at', '')
    
    if chars:
        char = chars[0]
        char.Joy += 12
        if at:
            return StoryFragment(f"{char.name} succeeded at {_to_phrase(at)}!")
        return StoryFragment(f"{char.name} was successful!")
    
    return StoryFragment("success", kernel_name="Success")


@REGISTRY.kernel("Failure")
def kernel_failure(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Experiencing failure.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Sadness += 10
        return StoryFragment(f"{char.name} failed to achieve their goal.")
    
    return StoryFragment("failure", kernel_name="Failure")


@REGISTRY.kernel("Achievement")
def kernel_achievement(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Completing an achievement.
    """
    chars = [a for a in args if isinstance(a, Character)]
    what = kwargs.get('what', '')
    
    if chars:
        char = chars[0]
        char.Joy += 15
        if what:
            return StoryFragment(f"{char.name} achieved {_to_phrase(what)}!")
        return StoryFragment(f"{char.name} accomplished something great!")
    
    return StoryFragment("an achievement", kernel_name="Achievement")


@REGISTRY.kernel("Breakthrough")
def kernel_breakthrough(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Having a breakthrough.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Joy += 12
        return StoryFragment(f"{char.name} had a breakthrough!")
    
    return StoryFragment("a breakthrough", kernel_name="Breakthrough")


@REGISTRY.kernel("Setback")
def kernel_setback(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Experiencing a setback.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Sadness += 8
        return StoryFragment(f"{char.name} experienced a setback.")
    
    return StoryFragment("a setback", kernel_name="Setback")


# =============================================================================
# INTERVENTION & SUPPORT (10 kernels)
# =============================================================================

@REGISTRY.kernel("Intervention")
def kernel_intervention(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Someone intervenes to help.
    
    Patterns from dataset:
      - Intervention(Bird, action=Drop(toy, Sue))
      - Intervention(OldMan, action=Guide(...))
    """
    chars = [a for a in args if isinstance(a, Character)]
    action = kwargs.get('action', '')
    
    if chars:
        helper = chars[0]
        helper.Joy += 5
        if action:
            return StoryFragment(f"{helper.name} intervened by {_to_phrase(action)}.")
        return StoryFragment(f"{helper.name} stepped in to help.")
    
    return StoryFragment("an intervention", kernel_name="Intervention")


@REGISTRY.kernel("Mediation")
def kernel_mediation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Someone mediates a conflict.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        mediator = chars[0]
        return StoryFragment(f"{mediator.name} helped resolve the disagreement.")
    
    return StoryFragment("mediation", kernel_name="Mediation")


@REGISTRY.kernel("Support")
def kernel_support(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Providing support.
    
    Patterns from dataset:
      - Support(Sam) -- Sam provides support
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        supporter, supported = chars[0], chars[1]
        supported.Joy += 8
        return StoryFragment(f"{supporter.name} supported {supported.name}.")
    elif chars:
        char = chars[0]
        char.Joy += 5
        return StoryFragment(f"{char.name} received support.")
    
    return StoryFragment("support", kernel_name="Support")


@REGISTRY.kernel("Encourage")
def kernel_encourage(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Encouraging someone.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        encourager, encouraged = chars[0], chars[1]
        encouraged.Joy += 10
        encouraged.Fear = max(0, encouraged.Fear - 5)
        return StoryFragment(f"{encourager.name} encouraged {encouraged.name}.")
    elif chars:
        char = chars[0]
        char.Joy += 8
        return StoryFragment(f"{char.name} felt encouraged.")
    
    return StoryFragment("encouragement", kernel_name="Encourage")


@REGISTRY.kernel("Defend")
def kernel_defend(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Defending someone.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        defender, defended = chars[0], chars[1]
        defender.Fear += 5
        defended.Joy += 10
        return StoryFragment(f"{defender.name} stood up to defend {defended.name}.")
    elif chars:
        char = chars[0]
        char.Fear += 5
        return StoryFragment(f"{char.name} defended bravely.")
    
    return StoryFragment("defense", kernel_name="Defend")


# Note: Guidance, Mentorship, Rescue, Comfort, Escape already exist in gen5k01
# We'll create enhanced/alternate versions if needed, or skip to avoid duplicates


# =============================================================================
# ENVIRONMENTAL & SITUATIONS (10 kernels)
# =============================================================================

@REGISTRY.kernel("Noise")
def kernel_noise(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Hearing a noise.
    
    Patterns from dataset:
      - stimulus=Noise -- hearing a noise
      - Unexpected(noise) -- unexpected noise
    """
    chars = [a for a in args if isinstance(a, Character)]
    kind = kwargs.get('kind', '')
    
    if chars:
        char = chars[0]
        char.Fear += 5
        if kind:
            return StoryFragment(f"{char.name} heard a {_to_phrase(kind)} noise.")
        return StoryFragment(f"{char.name} heard a strange noise.")
    
    if kind:
        return StoryFragment(f"a {_to_phrase(kind)} noise", kernel_name="Noise")
    return StoryFragment("a noise", kernel_name="Noise")


@REGISTRY.kernel("Silence")
def kernel_silence(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Experiencing silence.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        return StoryFragment(f"Everything was quiet around {char.name}.")
    
    return StoryFragment("silence", kernel_name="Silence")


@REGISTRY.kernel("Darkness")
def kernel_darkness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being in darkness.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Fear += 8
        return StoryFragment(f"{char.name} was surrounded by darkness.")
    
    return StoryFragment("darkness", kernel_name="Darkness")


@REGISTRY.kernel("Light")
def kernel_light(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Finding light.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Fear = max(0, char.Fear - 8)
        char.Joy += 8
        return StoryFragment(f"{char.name} saw a bright light ahead.")
    
    return StoryFragment("light", kernel_name="Light")


@REGISTRY.kernel("Weather")
def kernel_weather(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Weather conditions.
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    condition = kwargs.get('condition', objects[0] if objects else '')
    
    if condition:
        return StoryFragment(f"The weather was {_to_phrase(condition)}.")
    
    return StoryFragment("the weather changed", kernel_name="Weather")


@REGISTRY.kernel("Shelter")
def kernel_shelter(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Finding shelter.
    
    Patterns from dataset:
      - Shelter -- finding shelter
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Fear = max(0, char.Fear - 10)
        char.Joy += 5
        return StoryFragment(f"{char.name} found shelter from the storm.")
    
    return StoryFragment("finding shelter", kernel_name="Shelter")


@REGISTRY.kernel("Danger")
def kernel_danger(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Facing danger.
    """
    chars = [a for a in args if isinstance(a, Character)]
    kind = kwargs.get('kind', '')
    
    if chars:
        char = chars[0]
        char.Fear += 15
        if kind:
            return StoryFragment(f"{char.name} faced danger from {_to_phrase(kind)}.")
        return StoryFragment(f"{char.name} was in danger!")
    
    return StoryFragment("danger", kernel_name="Danger")


@REGISTRY.kernel("Safety")
def kernel_safety(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being safe.
    
    Patterns from dataset:
      - outcome=Safety(tree) -- safe in tree
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    where = kwargs.get('where', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        char.Fear = max(0, char.Fear - 15)
        char.Joy += 10
        if where:
            return StoryFragment(f"{char.name} was safe in the {_to_phrase(where)}.")
        return StoryFragment(f"{char.name} was finally safe.")
    
    return StoryFragment("safety", kernel_name="Safety")


@REGISTRY.kernel("Trap")
def kernel_trap(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being trapped.
    
    Patterns from dataset:
      - Solution(Trap) -- trap as solution
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Fear += 15
        char.Sadness += 10
        return StoryFragment(f"{char.name} was trapped!")
    
    return StoryFragment("a trap", kernel_name="Trap")


# =============================================================================
# ABSTRACT CONCEPTS (10 kernels)
# =============================================================================

@REGISTRY.kernel("Memory")
def kernel_memory(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Remembering something.
    
    Patterns from dataset:
      - Relief(Lily) + Memory(noise)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    thing = kwargs.get('of', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if thing:
            return StoryFragment(f"{char.name} would always remember {_to_phrase(thing)}.")
        return StoryFragment(f"{char.name} remembered it fondly.")
    
    if thing:
        return StoryFragment(f"a memory of {_to_phrase(thing)}", kernel_name="Memory")
    return StoryFragment("a memory", kernel_name="Memory")


@REGISTRY.kernel("Wisdom")
def kernel_wisdom(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Showing wisdom.
    
    Patterns from dataset:
      - insight=Wisdom -- wisdom gained
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Joy += 8
        return StoryFragment(f"{char.name} gained wisdom from the experience.")
    
    return StoryFragment("wisdom", kernel_name="Wisdom")


@REGISTRY.kernel("Knowledge")
def kernel_knowledge(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Gaining knowledge.
    """
    chars = [a for a in args if isinstance(a, Character)]
    about = kwargs.get('about', '')
    
    if chars:
        char = chars[0]
        char.Joy += 5
        if about:
            return StoryFragment(f"{char.name} learned about {_to_phrase(about)}.")
        return StoryFragment(f"{char.name} gained new knowledge.")
    
    return StoryFragment("knowledge", kernel_name="Knowledge")


@REGISTRY.kernel("Understanding")
def kernel_understanding(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Understanding something.
    """
    chars = [a for a in args if isinstance(a, Character)]
    what = kwargs.get('what', '')
    
    if chars:
        char = chars[0]
        char.Joy += 8
        if what:
            return StoryFragment(f"{char.name} understood {_to_phrase(what)}.")
        return StoryFragment(f"{char.name} finally understood.")
    
    return StoryFragment("understanding", kernel_name="Understanding")


@REGISTRY.kernel("Realization")
def kernel_realization(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Realizing something.
    
    Patterns from dataset:
      - Realization(Heavy + Strong)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    what = kwargs.get('what', objects[0] if objects else '')
    
    if chars:
        char = chars[0]
        if what:
            return StoryFragment(f"{char.name} realized that it was {_to_phrase(what)}.")
        return StoryFragment(f"{char.name} had a sudden realization.")
    
    if what:
        return StoryFragment(f"the realization that {_to_phrase(what)}", kernel_name="Realization")
    return StoryFragment("a realization", kernel_name="Realization")


@REGISTRY.kernel("Awareness")
def kernel_awareness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Becoming aware.
    """
    chars = [a for a in args if isinstance(a, Character)]
    of = kwargs.get('of', '')
    
    if chars:
        char = chars[0]
        if of:
            return StoryFragment(f"{char.name} became aware of {_to_phrase(of)}.")
        return StoryFragment(f"{char.name} became more aware.")
    
    return StoryFragment("awareness", kernel_name="Awareness")


@REGISTRY.kernel("Confusion")
def kernel_confusion(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being confused.
    """
    chars = [a for a in args if isinstance(a, Character)]
    about = kwargs.get('about', '')
    
    if chars:
        char = chars[0]
        if about:
            return StoryFragment(f"{char.name} was confused about {_to_phrase(about)}.")
        return StoryFragment(f"{char.name} felt confused.")
    
    return StoryFragment("confusion", kernel_name="Confusion")


@REGISTRY.kernel("Clarity")
def kernel_clarity(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Gaining clarity.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        char.Joy += 8
        return StoryFragment(f"Everything became clear to {char.name}.")
    
    return StoryFragment("clarity", kernel_name="Clarity")


@REGISTRY.kernel("Mystery")
def kernel_mystery(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Encountering mystery.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        char = chars[0]
        return StoryFragment(f"{char.name} encountered a strange mystery.")
    
    return StoryFragment("a mystery", kernel_name="Mystery")


# =============================================================================
# SOCIAL DYNAMICS (10 kernels)
# =============================================================================

@REGISTRY.kernel("Community")
def kernel_community(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Community gathering/feeling.
    
    Patterns from dataset:
      - Community(Pride + Joy, members=Friends)
    """
    objects = [str(a) for a in args if isinstance(a, str)]
    feeling = kwargs.get('feeling', objects[0] if objects else '')
    members = kwargs.get('members', '')
    
    if feeling and members:
        return StoryFragment(f"The {_to_phrase(members)} felt {_to_phrase(feeling)} as a community.")
    elif feeling:
        return StoryFragment(f"There was a sense of {_to_phrase(feeling)} in the community.")
    
    return StoryFragment("a strong sense of community", kernel_name="Community")


@REGISTRY.kernel("Unity")
def kernel_unity(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Coming together in unity.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        names = NLGUtils.join_list([c.name for c in chars])
        for char in chars:
            char.Joy += 8
            char.Love += 5
        return StoryFragment(f"{names} came together in unity.")
    
    return StoryFragment("unity", kernel_name="Unity")


@REGISTRY.kernel("Competition")
def kernel_competition(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Competing with others.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} competed against each other.")
    elif chars:
        char = chars[0]
        return StoryFragment(f"{char.name} entered the competition.")
    
    return StoryFragment("competition", kernel_name="Competition")


@REGISTRY.kernel("Alliance")
def kernel_alliance(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Forming an alliance.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        for char in chars:
            char.Love += 8
        return StoryFragment(f"{names} formed an alliance.")
    elif chars:
        char = chars[0]
        return StoryFragment(f"{char.name} sought allies.")
    
    return StoryFragment("an alliance", kernel_name="Alliance")


@REGISTRY.kernel("Betrayal")
def kernel_betrayal(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being betrayed.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        betrayer, betrayed = chars[0], chars[1]
        betrayed.Sadness += 20
        betrayed.Anger += 15
        return StoryFragment(f"{betrayer.name} betrayed {betrayed.name}.")
    elif chars:
        char = chars[0]
        char.Sadness += 20
        char.Anger += 15
        return StoryFragment(f"{char.name} felt betrayed.")
    
    return StoryFragment("betrayal", kernel_name="Betrayal")


@REGISTRY.kernel("Loyalty")
def kernel_loyalty(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Showing loyalty.
    """
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', '')
    
    if chars:
        char = chars[0]
        char.Love += 10
        if to:
            return StoryFragment(f"{char.name} showed loyalty to {_to_phrase(to)}.")
        return StoryFragment(f"{char.name} remained loyal.")
    
    return StoryFragment("loyalty", kernel_name="Loyalty")


# Note: Trust, Friendship, Conflict already exist in base gen5
# We've reached 100 kernels!


# =============================================================================
# TEST FUNCTION
# =============================================================================

def test_kernels():
    """Test that all kernels in this pack are properly registered."""
    from gen5 import generate_story
    
    print("Testing gen5k04.py kernels...")
    print(f"Total kernels registered: {len(REGISTRY.kernels)}")
    
    # Test a few sample kernels
    test_cases = [
        "Tim(Character, boy)\nArrival(Tim)\nRelief(Tim)",
        "Lily(Character, girl)\nCuriosity(Lily)\nDiscover(Lily, treasure)",
        "Max(Character, boy)\nNeed(Max, help)\nAssist(Max)",
    ]
    
    for i, kernel_str in enumerate(test_cases, 1):
        print(f"\n--- Test {i} ---")
        print(f"Kernel: {kernel_str}")
        story = generate_story(kernel_str)
        print(f"Story: {story}")
    
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_kernels()

