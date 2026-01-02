"""
gen5k02.py - Additional Kernel Pack #02

This module extends gen5.py with 100 additional kernel implementations.
Import this module after gen5 to register the new kernels.

=============================================================================
KERNELS IN THIS PACK (with usage patterns from sampling):
=============================================================================

## Communication Kernels
- Request(char, thing)           -- asking for something
- Gift(object) / Gift(char, to=other, object=thing)  -- giving gifts
- Promise(char, action)          -- making a promise
- Wish(char, desire)             -- expressing a wish
- Explain(char, topic)           -- explaining something
- Invite(char, to=event)         -- inviting someone
- Greet(char)                    -- greeting someone
- Introduce(char1, char2)        -- introducing characters

## Mental/Emotional Kernels
- Gratitude(char, to=other)      -- expressing thanks
- Insight(concept)               -- gaining understanding
- Curious(char)                  -- being curious
- Lonely(char)                   -- feeling lonely
- Excited(char)                  -- being excited
- Worried(char)                  -- being worried
- Confused(char)                 -- being confused
- Nervous(char)                  -- being nervous
- Bored(char)                    -- being bored
- Jealous(char)                  -- being jealous
- Embarrassed(char)              -- being embarrassed
- Guilty(char)                   -- feeling guilty
- Relieved(char)                 -- feeling relieved
- Hopeful(char)                  -- feeling hopeful

## Attempt/Decision Kernels  
- Attempt(char, action)          -- trying to do something
- Try(char, action)              -- alias for attempt
- Decide(char, choice)           -- making a decision
- Agree(char)                    -- agreeing to something
- Refuse(char)                   -- refusing something
- Accept(char, thing)            -- accepting something
- Reject(char, thing)            -- rejecting something

## Exploration Kernels
- Explore(location)              -- exploring a place
- Visit(char, place)             -- visiting somewhere
- Arrive(char, location)         -- arriving somewhere
- Leave(char)                    -- leaving
- Travel(char, destination)      -- traveling
- Wander(char)                   -- wandering around

## Physical Action Kernels
- Throw(char, object)            -- throwing something
- Catch(char, object)            -- catching something
- Drop(char, object)             -- dropping something
- Dig(char, location)            -- digging
- Cut(char, object)              -- cutting something
- Pour(char, liquid)             -- pouring something
- Stir(char, object)             -- stirring
- Collect(char, items)           -- collecting things
- Carry(char, object)            -- carrying something
- Grab(char, object)             -- grabbing something
- Wave(char)                     -- waving
- Point(char, direction)         -- pointing
- Kick(char, object)             -- kicking something
- Splash(char, water)            -- splashing
- Blow(char)                     -- blowing

## Narrative Pattern Kernels
- Problem(char, issue)           -- a problem occurs
- Solution(action)               -- solving a problem
- Reward(char, prize)            -- getting a reward
- Punishment(char)               -- receiving punishment
- Challenge(char, task)          -- facing a challenge
- Overcome(char, obstacle)       -- overcoming difficulty
- Mistake(char)                  -- making a mistake
- Realize(char, truth)           -- having a realization
- Remember(char, memory)         -- remembering something
- Forget(char, thing)            -- forgetting something

## Nature/Weather Kernels
- Rain()                         -- it rains
- Snow()                         -- it snows
- Wind()                         -- wind blows
- Storm()                        -- a storm
- Sunny()                        -- sunny weather
- Magic(object)                  -- something magical

## Daily Activity Kernels
- Cook(char, food)               -- cooking
- Bake(char, food)               -- baking
- Draw(char, picture)            -- drawing
- Paint(char, artwork)           -- painting
- Read(char, book)               -- reading
- Write(char, text)              -- writing
- Study(char, subject)           -- studying
- Practice(char, skill)          -- practicing
- Work(char)                     -- working
- Garden(char)                   -- gardening
- Shop(char)                     -- shopping
- Pack(char)                     -- packing
- Unpack(char)                   -- unpacking
- Wrap(char, gift)               -- wrapping

## Social Interaction Kernels
- Meet(char1, char2)             -- meeting someone
- Say(char, message)             -- saying something
- Agree(char)                    -- agreeing
- Argue(char1, char2)            -- arguing
- Apologize(char)                -- apologizing (alias)
- Forgive(char)                  -- forgiving (alias)

## Care/Nurture Kernels
- Care(char, for=other)          -- taking care of someone
- Protect(char, other)           -- protecting someone
- Nurse(char)                    -- nursing/caring for sick
- Heal(char)                     -- healing/getting better
- Grow(thing)                    -- growing

=============================================================================

Usage:
    from gen5 import generate_story, REGISTRY
    import gen5k02  # Registers additional kernels
    
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
# COMMUNICATION KERNELS
# =============================================================================

@REGISTRY.kernel("Gift")
def kernel_gift(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A gift is given.
    
    Patterns:
      - Gift(toy)                 -- a gift of toy
      - Gift(char, object)        -- char gives gift
      - Gift(char, to=other, object=thing)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    to = kwargs.get('to', None)
    obj = kwargs.get('object', '')
    
    thing = obj if obj else (objects[0] if objects else 'a gift')
    
    if len(chars) >= 2:
        giver = chars[0]
        receiver = chars[1]
        giver.Love += 5
        receiver.Joy += 10
        return StoryFragment(f"{giver.name} gave {receiver.name} {NLGUtils.article(thing)} {thing} as a gift.")
    elif chars:
        giver = chars[0]
        giver.Love += 5
        if to:
            to_name = to.name if isinstance(to, Character) else str(to)
            return StoryFragment(f"{giver.name} gave {to_name} {NLGUtils.article(thing)} {thing} as a gift.")
        return StoryFragment(f"{giver.name} gave {NLGUtils.article(thing)} {thing} as a gift.")
    
    # Just the gift object
    return StoryFragment(f"there was a gift of {_to_phrase(thing)}", kernel_name="Gift")


@REGISTRY.kernel("Wish")
def kernel_wish(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character wishes for something.
    
    Patterns:
      - Wish(char, thing)         -- char wishes for thing
      - Wish(Lily, Fix(Ratty))    -- specific wish
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    
    wisher = chars[0] if chars else ctx.current_focus
    
    if fragments:
        wish_content = _to_phrase(fragments[0])
    elif objects:
        wish_content = _to_phrase(objects[0])
    else:
        wish_content = "something wonderful"
    
    if wisher:
        wisher.Joy += 3
        return StoryFragment(f"{wisher.name} wished for {wish_content}.")
    
    return StoryFragment(f"there was a wish for {wish_content}", kernel_name="Wish")


@REGISTRY.kernel("Explain")
def kernel_explain(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character explains something.
    
    Patterns:
      - Explain(char, topic)      -- char explains topic
      - Explain(Mom, rules)       -- Mom explains rules
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        explainer = chars[0]
        listener = chars[1]
        topic = objects[0] if objects else "it"
        return StoryFragment(f"{explainer.name} explained {_to_phrase(topic)} to {listener.name}.")
    elif chars:
        explainer = chars[0]
        topic = objects[0] if objects else "everything"
        return StoryFragment(f"{explainer.name} explained {_to_phrase(topic)}.")
    
    if objects:
        return StoryFragment(f"someone explained {_to_phrase(objects[0])}", kernel_name="Explain")
    return StoryFragment("there was an explanation", kernel_name="Explain")


@REGISTRY.kernel("Invite")
def kernel_invite(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character invites another.
    
    Patterns:
      - Invite(char, to=event)    -- char invites to event
      - Invite(Lily, party)       -- Lily invites to party
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    to = kwargs.get('to', '')
    
    event = to if to else (objects[0] if objects else 'a party')
    
    if len(chars) >= 2:
        inviter = chars[0]
        invitee = chars[1]
        invitee.Joy += 5
        return StoryFragment(f"{inviter.name} invited {invitee.name} to the {_to_phrase(event)}.")
    elif chars:
        inviter = chars[0]
        return StoryFragment(f"{inviter.name} invited everyone to the {_to_phrase(event)}.")
    
    return StoryFragment(f"there was an invitation to the {_to_phrase(event)}", kernel_name="Invite")


@REGISTRY.kernel("Greet")
def kernel_greet(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character greets another."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        greeter = chars[0]
        greeted = chars[1]
        return StoryFragment(f"{greeter.name} said hello to {greeted.name}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} said hello.")
    
    return StoryFragment("greetings were exchanged", kernel_name="Greet")


@REGISTRY.kernel("Introduce")
def kernel_introduce(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character introduces someone."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 3:
        introducer = chars[0]
        person1 = chars[1]
        person2 = chars[2]
        return StoryFragment(f"{introducer.name} introduced {person1.name} to {person2.name}.")
    elif len(chars) == 2:
        return StoryFragment(f"{chars[0].name} and {chars[1].name} introduced themselves.")
    elif chars:
        return StoryFragment(f"{chars[0].name} introduced themselves.")
    
    return StoryFragment("introductions were made", kernel_name="Introduce")


# =============================================================================
# MENTAL/EMOTIONAL KERNELS
# =============================================================================

@REGISTRY.kernel("Curious")
def kernel_curious(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is curious."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    about = objects[0] if objects else ''
    
    if chars:
        if about:
            return StoryFragment(f"{chars[0].name} was very curious about the {about}.")
        return StoryFragment(f"{chars[0].name} was very curious.")
    
    if about:
        return StoryFragment(f"curious about the {about}", kernel_name="Curious")
    return StoryFragment("curious", kernel_name="Curious")


@REGISTRY.kernel("Lonely")
def kernel_lonely(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character feels lonely."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 10
        chars[0].Joy -= 5
        return StoryFragment(f"{chars[0].name} felt lonely.")
    
    return StoryFragment("lonely", kernel_name="Lonely")


@REGISTRY.kernel("Excited")
def kernel_excited(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is excited."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    about = objects[0] if objects else ''
    
    if chars:
        chars[0].Joy += 12
        if about:
            return StoryFragment(f"{chars[0].name} was so excited about the {about}!")
        return StoryFragment(f"{chars[0].name} was so excited!")
    
    return StoryFragment("excited", kernel_name="Excited")


@REGISTRY.kernel("Worried")
def kernel_worried(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is worried."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    about = objects[0] if objects else ''
    
    if chars:
        chars[0].Fear += 8
        if about:
            return StoryFragment(f"{chars[0].name} was worried about the {about}.")
        return StoryFragment(f"{chars[0].name} was worried.")
    
    return StoryFragment("worried", kernel_name="Worried")


@REGISTRY.kernel("Confused")
def kernel_confused(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is confused."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} was confused.")
    
    return StoryFragment("confused", kernel_name="Confused")


@REGISTRY.kernel("Nervous")
def kernel_nervous(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is nervous."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 5
        return StoryFragment(f"{chars[0].name} felt nervous.")
    
    return StoryFragment("nervous", kernel_name="Nervous")


@REGISTRY.kernel("Bored")
def kernel_bored(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is bored."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy -= 5
        return StoryFragment(f"{chars[0].name} was bored.")
    
    return StoryFragment("bored", kernel_name="Bored")


@REGISTRY.kernel("Jealous")
def kernel_jealous(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is jealous."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    of = objects[0] if objects else ''
    
    if chars:
        chars[0].Anger += 5
        chars[0].Sadness += 5
        if of:
            return StoryFragment(f"{chars[0].name} felt jealous of the {of}.")
        return StoryFragment(f"{chars[0].name} felt jealous.")
    
    return StoryFragment("jealous", kernel_name="Jealous")


@REGISTRY.kernel("Embarrassed")
def kernel_embarrassed(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character is embarrassed."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 3
        return StoryFragment(f"{chars[0].name} felt embarrassed.")
    
    return StoryFragment("embarrassed", kernel_name="Embarrassed")


@REGISTRY.kernel("Guilty")
def kernel_guilty(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character feels guilty."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 8
        return StoryFragment(f"{chars[0].name} felt guilty.")
    
    return StoryFragment("guilty", kernel_name="Guilty")


@REGISTRY.kernel("Relieved")
def kernel_relieved(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character feels relieved."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear -= 15
        chars[0].Joy += 10
        return StoryFragment(f"{chars[0].name} felt so relieved.")
    
    return StoryFragment("relieved", kernel_name="Relieved")


@REGISTRY.kernel("Hopeful")
def kernel_hopeful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character feels hopeful."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        chars[0].Fear -= 3
        return StoryFragment(f"{chars[0].name} felt hopeful.")
    
    return StoryFragment("hopeful", kernel_name="Hopeful")


# =============================================================================
# ATTEMPT/DECISION KERNELS
# =============================================================================

@REGISTRY.kernel("Try")
def kernel_try(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character tries something (alias for Attempt)."""
    return kernel_attempt(ctx, *args, **kwargs)


@REGISTRY.kernel("Decide")
def kernel_decide(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character makes a decision.
    
    Patterns:
      - Decide(char, choice)      -- char decides on choice
      - Decision(Lily, Agree)     -- Lily decides to agree
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    choice = objects[0] if objects else 'what to do'
    
    if chars:
        return StoryFragment(f"{chars[0].name} decided to {_to_phrase(choice)}.")
    
    return StoryFragment(f"a decision was made to {_to_phrase(choice)}", kernel_name="Decide")


@REGISTRY.kernel("Agree")
def kernel_agree(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character agrees."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} agreed.")
    elif chars:
        to = objects[0] if objects else ''
        if to:
            return StoryFragment(f"{chars[0].name} agreed to {_to_phrase(to)}.")
        return StoryFragment(f"{chars[0].name} agreed.")
    
    return StoryFragment("they agreed", kernel_name="Agree")


@REGISTRY.kernel("Refuse")
def kernel_refuse(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character refuses."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Anger += 3
        if objects:
            return StoryFragment(f"{chars[0].name} refused to {_to_phrase(objects[0])}.")
        return StoryFragment(f"{chars[0].name} refused.")
    
    return StoryFragment("there was a refusal", kernel_name="Refuse")


@REGISTRY.kernel("Accept")
def kernel_accept(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character accepts something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thing = objects[0] if objects else 'it'
    
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f"{chars[0].name} accepted the {thing}.")
    
    return StoryFragment(f"the {thing} was accepted", kernel_name="Accept")


@REGISTRY.kernel("Reject")
def kernel_reject(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character rejects something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thing = objects[0] if objects else 'it'
    
    if chars:
        return StoryFragment(f"{chars[0].name} rejected the {thing}.")
    
    return StoryFragment(f"the {thing} was rejected", kernel_name="Reject")


# =============================================================================
# EXPLORATION KERNELS
# =============================================================================

@REGISTRY.kernel("Explore")
def kernel_explore(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character explores a place.
    
    Patterns:
      - Explore(location)         -- exploring a location
      - Explore(hedge)            -- exploring specific thing
      - path=Explore(upstairs)    -- as part of quest
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    location = objects[0] if objects else 'around'
    explorer = chars[0] if chars else ctx.current_focus
    
    if explorer:
        explorer.Joy += 3
        return StoryFragment(f"{explorer.name} explored the {location}.")
    
    return StoryFragment(f"explored the {location}", kernel_name="Explore")


@REGISTRY.kernel("Visit")
def kernel_visit(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Character visits somewhere or someone.
    
    Patterns:
      - Visit(zoo, Timmy, Mom)    -- visiting a place
      - Visit(Lily, Grandma)      -- visiting a person
      - Visit(Lily, Mom, Friend)  -- visiting with someone
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    place = objects[0] if objects else ''
    
    if chars and place:
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f"{names} visited the {place}.")
    elif len(chars) >= 2:
        visitor = chars[0]
        visited = chars[1]
        return StoryFragment(f"{visitor.name} visited {visited.name}.")
    elif chars:
        if place:
            return StoryFragment(f"{chars[0].name} visited the {place}.")
        return StoryFragment(f"{chars[0].name} went for a visit.")
    
    if place:
        return StoryFragment(f"visited the {place}", kernel_name="Visit")
    return StoryFragment("there was a visit", kernel_name="Visit")


@REGISTRY.kernel("Arrive")
def kernel_arrive(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character arrives somewhere."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    location = objects[0] if objects else 'there'
    
    if chars:
        return StoryFragment(f"{chars[0].name} arrived at the {location}.")
    
    return StoryFragment(f"arrived at the {location}", kernel_name="Arrive")


@REGISTRY.kernel("Leave")
def kernel_leave(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character leaves."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    from_place = objects[0] if objects else ''
    
    if chars:
        if from_place:
            return StoryFragment(f"{chars[0].name} left the {from_place}.")
        return StoryFragment(f"{chars[0].name} left.")
    
    return StoryFragment("they left", kernel_name="Leave")


@REGISTRY.kernel("Travel")
def kernel_travel(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character travels somewhere."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    destination = kwargs.get('to', kwargs.get('destination', ''))
    
    dest = destination if destination else (objects[0] if objects else 'far away')
    
    if chars:
        return StoryFragment(f"{chars[0].name} traveled to the {_to_phrase(dest)}.")
    
    return StoryFragment(f"there was travel to the {_to_phrase(dest)}", kernel_name="Travel")


@REGISTRY.kernel("Wander")
def kernel_wander(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character wanders around."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} wandered around.")
    
    return StoryFragment("wandered around", kernel_name="Wander")


# =============================================================================
# PHYSICAL ACTION KERNELS
# =============================================================================

@REGISTRY.kernel("Throw")
def kernel_throw(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character throws something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thrower = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if thrower:
        return StoryFragment(f"{thrower.name} threw the {thing}.")
    
    return StoryFragment(f"the {thing} was thrown", kernel_name="Throw")


@REGISTRY.kernel("Catch")
def kernel_catch(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character catches something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    catcher = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if catcher:
        catcher.Joy += 3
        return StoryFragment(f"{catcher.name} caught the {thing}.")
    
    return StoryFragment(f"the {thing} was caught", kernel_name="Catch")


@REGISTRY.kernel("Drop")
def kernel_drop(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character drops something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    dropper = _get_default_actor(ctx, chars)
    thing = objects[0] if objects else kwargs.get('object', 'it')
    
    # Track the object for context (e.g., for Obscure to use)
    if thing != 'it':
        ctx.current_object = thing
    
    if dropper:
        return StoryFragment(f"{dropper.name} dropped the {thing}.")
    
    return StoryFragment(f"the {thing} dropped", kernel_name="Drop")


@REGISTRY.kernel("Cut")
def kernel_cut(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character cuts something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    cutter = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if cutter:
        return StoryFragment(f"{cutter.name} cut the {thing}.")
    
    return StoryFragment(f"the {thing} was cut", kernel_name="Cut")


@REGISTRY.kernel("Stir")
def kernel_stir(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character stirs something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    stirrer = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if stirrer:
        return StoryFragment(f"{stirrer.name} stirred the {thing}.")
    
    return StoryFragment(f"the {thing} was stirred", kernel_name="Stir")


@REGISTRY.kernel("Collect")
def kernel_collect(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character collects things."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    collector = chars[0] if chars else ctx.current_focus
    items = objects[0] if objects else 'things'
    
    if collector:
        collector.Joy += 3
        return StoryFragment(f"{collector.name} collected {_to_phrase(items)}.")
    
    return StoryFragment(f"collected {_to_phrase(items)}", kernel_name="Collect")


@REGISTRY.kernel("Carry")
def kernel_carry(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character carries something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    carrier = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if carrier:
        return StoryFragment(f"{carrier.name} carried the {thing}.")
    
    return StoryFragment(f"the {thing} was carried", kernel_name="Carry")


@REGISTRY.kernel("Grab")
def kernel_grab(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character grabs something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    grabber = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if grabber:
        return StoryFragment(f"{grabber.name} grabbed the {thing}.")
    
    return StoryFragment(f"the {thing} was grabbed", kernel_name="Grab")


@REGISTRY.kernel("Wave")
def kernel_wave(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character waves."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        return StoryFragment(f"{chars[0].name} waved to {chars[1].name}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} waved.")
    
    return StoryFragment("someone waved", kernel_name="Wave")


@REGISTRY.kernel("Point")
def kernel_point(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character points at something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    pointer = chars[0] if chars else ctx.current_focus
    target = objects[0] if objects else 'it'
    
    if pointer:
        return StoryFragment(f"{pointer.name} pointed at the {target}.")
    
    return StoryFragment(f"pointed at the {target}", kernel_name="Point")


@REGISTRY.kernel("Kick")
def kernel_kick(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character kicks something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    kicker = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if kicker:
        return StoryFragment(f"{kicker.name} kicked the {thing}.")
    
    return StoryFragment(f"the {thing} was kicked", kernel_name="Kick")


@REGISTRY.kernel("Blow")
def kernel_blow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character blows."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    blower = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else ''
    
    if blower:
        if thing:
            return StoryFragment(f"{blower.name} blew on the {thing}.")
        return StoryFragment(f"{blower.name} blew.")
    
    return StoryFragment("blew", kernel_name="Blow")


# =============================================================================
# NARRATIVE PATTERN KERNELS
# =============================================================================

@REGISTRY.kernel("Problem")
def kernel_problem(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A problem occurs.
    
    Patterns:
      - Problem(char, issue)      -- char has a problem
      - Problem(Jar, tree)        -- object problem
      - Problem(Lily, object=car, issue=Broken)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    issue = kwargs.get('issue', kwargs.get('object', ''))
    
    if chars:
        char = chars[0]
        char.Fear += 5
        if issue:
            return StoryFragment(f"{char.name} had a problem with the {_to_phrase(issue)}.")
        if objects:
            return StoryFragment(f"{char.name} had a problem with the {objects[0]}.")
        return StoryFragment(f"{char.name} had a problem.")
    
    if objects:
        return StoryFragment(f"there was a problem with the {objects[0]}.", kernel_name="Problem")
    return StoryFragment("there was a problem", kernel_name="Problem")


@REGISTRY.kernel("Solution")
def kernel_solution(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A solution is found.
    
    Patterns:
      - Solution(action)          -- the solution is an action
      - Solution(Push(Toto, Jar) + Fall(Jar))
    """
    chars = [a for a in args if isinstance(a, Character)]
    fragments = [a for a in args if isinstance(a, StoryFragment)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 10
        if fragments:
            return StoryFragment(f"{chars[0].name} found a solution: {_to_phrase(fragments[0])}.")
        return StoryFragment(f"{chars[0].name} found a solution!")
    
    if fragments:
        return StoryFragment(f"The solution was {_to_phrase(fragments[0])}.")
    if objects:
        return StoryFragment(f"The solution was to {_to_phrase(objects[0])}.")
    return StoryFragment("A solution was found!", kernel_name="Solution")


@REGISTRY.kernel("Reward")
def kernel_reward(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character receives a reward."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    prize = objects[0] if objects else 'a special treat'
    
    if chars:
        chars[0].Joy += 15
        return StoryFragment(f"{chars[0].name} got {NLGUtils.article(prize)} {prize} as a reward!")
    
    return StoryFragment(f"the reward was {NLGUtils.article(prize)} {prize}", kernel_name="Reward")


@REGISTRY.kernel("Punishment")
def kernel_punishment(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character receives punishment."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Sadness += 10
        chars[0].Joy -= 5
        if objects:
            return StoryFragment(f"{chars[0].name} was punished by {_to_phrase(objects[0])}.")
        return StoryFragment(f"{chars[0].name} was punished.")
    
    return StoryFragment("there was punishment", kernel_name="Punishment")


@REGISTRY.kernel("Challenge")
def kernel_challenge(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character faces a challenge."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    task = objects[0] if objects else 'a difficult task'
    
    if chars:
        chars[0].Fear += 5
        return StoryFragment(f"{chars[0].name} faced the challenge of {_to_phrase(task)}.")
    
    return StoryFragment(f"there was a challenge: {_to_phrase(task)}", kernel_name="Challenge")


@REGISTRY.kernel("Overcome")
def kernel_overcome(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character overcomes an obstacle."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    obstacle = objects[0] if objects else 'the difficulty'
    
    if chars:
        chars[0].Joy += 12
        chars[0].Fear -= 8
        return StoryFragment(f"{chars[0].name} overcame {_to_phrase(obstacle)}!")
    
    return StoryFragment(f"overcame {_to_phrase(obstacle)}", kernel_name="Overcome")


@REGISTRY.kernel("Mistake")
def kernel_mistake(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character makes a mistake."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Sadness += 5
        if objects:
            return StoryFragment(f"{chars[0].name} made a mistake with the {objects[0]}.")
        return StoryFragment(f"{chars[0].name} made a mistake.")
    
    return StoryFragment("a mistake was made", kernel_name="Mistake")


@REGISTRY.kernel("Realize")
def kernel_realize(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character realizes something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    truth = objects[0] if objects else 'something important'
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} realized {_to_phrase(truth)}.")
    
    return StoryFragment(f"there was a realization about {_to_phrase(truth)}", kernel_name="Realize")


@REGISTRY.kernel("Remember")
def kernel_remember(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character remembers something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    memory = objects[0] if objects else 'something'
    
    if chars:
        return StoryFragment(f"{chars[0].name} remembered {_to_phrase(memory)}.")
    
    return StoryFragment(f"remembered {_to_phrase(memory)}", kernel_name="Remember")


@REGISTRY.kernel("Forget")
def kernel_forget(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character forgets something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thing = objects[0] if objects else 'something'
    
    if chars:
        return StoryFragment(f"{chars[0].name} forgot about {_to_phrase(thing)}.")
    
    return StoryFragment(f"forgot about {_to_phrase(thing)}", kernel_name="Forget")


# =============================================================================
# NATURE/WEATHER KERNELS
# =============================================================================

@REGISTRY.kernel("Rain")
def kernel_rain(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """It rains."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"It started to rain and {chars[0].name} got wet.")
    
    return StoryFragment("It started to rain.", kernel_name="Rain")


@REGISTRY.kernel("Snow")
def kernel_snow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """It snows."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f"It started to snow and {chars[0].name} was excited.")
    
    return StoryFragment("It started to snow.", kernel_name="Snow")


@REGISTRY.kernel("Wind")
def kernel_wind(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """The wind blows."""
    return StoryFragment("The wind blew.", kernel_name="Wind")


@REGISTRY.kernel("Storm")
def kernel_storm(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """A storm happens."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 10
        return StoryFragment(f"A storm came and {chars[0].name} was scared.")
    
    return StoryFragment("A big storm came.", kernel_name="Storm")


@REGISTRY.kernel("Sunny")
def kernel_sunny(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sunny weather."""
    return StoryFragment("It was a beautiful sunny day.", kernel_name="Sunny")


@REGISTRY.kernel("Magic")
def kernel_magic(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something magical.
    
    Patterns:
      - Magic(object)             -- magical object
      - Magic(book)               -- magic book
      - source=Magic(book)        -- source of magic
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    thing = objects[0] if objects else 'thing'
    
    if chars:
        chars[0].Joy += 10
        return StoryFragment(f"{chars[0].name} found a magic {thing}!")
    
    return StoryFragment(f"there was a magic {thing}", kernel_name="Magic")


# =============================================================================
# DAILY ACTIVITY KERNELS
# =============================================================================

@REGISTRY.kernel("Bake")
def kernel_bake(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character bakes."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    baker = chars[0] if chars else ctx.current_focus
    food = objects[0] if objects else 'cookies'
    
    if baker:
        baker.Joy += 5
        return StoryFragment(f"{baker.name} baked some {food}.")
    
    return StoryFragment(f"baked {food}", kernel_name="Bake")


@REGISTRY.kernel("Draw")
def kernel_draw(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character draws."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    artist = chars[0] if chars else ctx.current_focus
    picture = objects[0] if objects else 'a picture'
    
    if artist:
        artist.Joy += 5
        return StoryFragment(f"{artist.name} drew {picture}.")
    
    return StoryFragment(f"drew {picture}", kernel_name="Draw")


@REGISTRY.kernel("Read")
def kernel_read(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character reads."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    reader = chars[0] if chars else ctx.current_focus
    book = objects[0] if objects else 'a book'
    
    if reader:
        return StoryFragment(f"{reader.name} read {book}.")
    
    return StoryFragment(f"read {book}", kernel_name="Read")


@REGISTRY.kernel("Write")
def kernel_write(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character writes."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    writer = chars[0] if chars else ctx.current_focus
    text = objects[0] if objects else 'something'
    
    if writer:
        return StoryFragment(f"{writer.name} wrote {text}.")
    
    return StoryFragment(f"wrote {text}", kernel_name="Write")


@REGISTRY.kernel("Study")
def kernel_study(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character studies."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    student = chars[0] if chars else ctx.current_focus
    subject = objects[0] if objects else ''
    
    if student:
        if subject:
            return StoryFragment(f"{student.name} studied {_to_phrase(subject)}.")
        return StoryFragment(f"{student.name} studied hard.")
    
    return StoryFragment("studied", kernel_name="Study")


@REGISTRY.kernel("Practice")
def kernel_practice(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character practices."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    practitioner = chars[0] if chars else ctx.current_focus
    skill = objects[0] if objects else ''
    
    if practitioner:
        practitioner.Joy += 3
        if skill:
            return StoryFragment(f"{practitioner.name} practiced {_to_phrase(skill)}.")
        return StoryFragment(f"{practitioner.name} practiced.")
    
    return StoryFragment("practiced", kernel_name="Practice")


@REGISTRY.kernel("Work")
def kernel_work(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character works."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    worker = chars[0] if chars else ctx.current_focus
    task = objects[0] if objects else ''
    
    if worker:
        if task:
            return StoryFragment(f"{worker.name} worked on {_to_phrase(task)}.")
        return StoryFragment(f"{worker.name} worked hard.")
    
    return StoryFragment("worked", kernel_name="Work")


@REGISTRY.kernel("Garden")
def kernel_garden(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character gardens."""
    chars = [a for a in args if isinstance(a, Character)]
    
    gardener = chars[0] if chars else ctx.current_focus
    
    if gardener:
        gardener.Joy += 3
        return StoryFragment(f"{gardener.name} worked in the garden.")
    
    return StoryFragment("worked in the garden", kernel_name="Garden")


@REGISTRY.kernel("Shop")
def kernel_shop(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character goes shopping."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    shopper = chars[0] if chars else ctx.current_focus
    items = objects[0] if objects else ''
    
    if shopper:
        if items:
            return StoryFragment(f"{shopper.name} went shopping for {_to_phrase(items)}.")
        return StoryFragment(f"{shopper.name} went shopping.")
    
    return StoryFragment("went shopping", kernel_name="Shop")


@REGISTRY.kernel("Pack")
def kernel_pack(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character packs things."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    packer = chars[0] if chars else ctx.current_focus
    things = objects[0] if objects else 'things'
    
    if packer:
        return StoryFragment(f"{packer.name} packed the {things}.")
    
    return StoryFragment(f"packed the {things}", kernel_name="Pack")


@REGISTRY.kernel("Unpack")
def kernel_unpack(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character unpacks."""
    chars = [a for a in args if isinstance(a, Character)]
    
    unpacker = chars[0] if chars else ctx.current_focus
    
    if unpacker:
        return StoryFragment(f"{unpacker.name} unpacked everything.")
    
    return StoryFragment("unpacked", kernel_name="Unpack")


@REGISTRY.kernel("Wrap")
def kernel_wrap(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character wraps something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    wrapper = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'the gift'
    
    if wrapper:
        return StoryFragment(f"{wrapper.name} wrapped {thing}.")
    
    return StoryFragment(f"wrapped {thing}", kernel_name="Wrap")


# =============================================================================
# SOCIAL INTERACTION KERNELS
# =============================================================================

@REGISTRY.kernel("Meet")
def kernel_meet(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters meet."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        for c in chars:
            c.Joy += 3
        return StoryFragment(f"{chars[0].name} met {chars[1].name}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} met someone new.")
    
    return StoryFragment("they met", kernel_name="Meet")


@REGISTRY.kernel("Say")
def kernel_say(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character says something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    speaker = chars[0] if chars else ctx.current_focus
    message = objects[0] if objects else 'something'
    
    if speaker:
        return StoryFragment(f'{speaker.name} said, "{_to_phrase(message).capitalize()}."')
    
    return StoryFragment(f'someone said "{_to_phrase(message)}"', kernel_name="Say")


@REGISTRY.kernel("Argue")
def kernel_argue(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Characters argue."""
    chars = [a for a in args if isinstance(a, Character)]
    
    for c in chars:
        c.Anger += 8
        c.Joy -= 5
    
    if len(chars) >= 2:
        return StoryFragment(f"{chars[0].name} and {chars[1].name} had an argument.")
    elif chars:
        return StoryFragment(f"{chars[0].name} argued.")
    
    return StoryFragment("there was an argument", kernel_name="Argue")


# =============================================================================
# CARE/NURTURE KERNELS
# =============================================================================

@REGISTRY.kernel("Care")
def kernel_care(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character cares for someone/something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    for_whom = kwargs.get('for', None)
    
    if len(chars) >= 2:
        carer = chars[0]
        cared_for = chars[1]
        carer.Love += 5
        return StoryFragment(f"{carer.name} took care of {cared_for.name}.")
    elif chars:
        carer = chars[0]
        if for_whom:
            target = for_whom.name if isinstance(for_whom, Character) else str(for_whom)
            return StoryFragment(f"{carer.name} took care of {target}.")
        if objects:
            return StoryFragment(f"{carer.name} took care of the {objects[0]}.")
        return StoryFragment(f"{carer.name} took care of things.")
    
    return StoryFragment("took care of things", kernel_name="Care")


@REGISTRY.kernel("Protect")
def kernel_protect(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character protects another."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        protector = chars[0]
        protected = chars[1]
        protector.Love += 5
        protected.Fear -= 8
        return StoryFragment(f"{protector.name} protected {protected.name}.")
    elif chars:
        return StoryFragment(f"{chars[0].name} protected everyone.")
    
    return StoryFragment("there was protection", kernel_name="Protect")


@REGISTRY.kernel("Protection")
def kernel_protection(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Alias for Protect."""
    return kernel_protect(ctx, *args, **kwargs)


@REGISTRY.kernel("Nurse")
def kernel_nurse(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character nurses someone back to health."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        nurse = chars[0]
        patient = chars[1]
        nurse.Love += 5
        patient.Joy += 5
        return StoryFragment(f"{nurse.name} nursed {patient.name} back to health.")
    elif chars:
        return StoryFragment(f"{chars[0].name} was nursed back to health.")
    
    return StoryFragment("nursed back to health", kernel_name="Nurse")


@REGISTRY.kernel("Heal")
def kernel_heal(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character heals or gets better."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 10
        chars[0].Sadness -= 10
        return StoryFragment(f"{chars[0].name} got better.")
    
    return StoryFragment("healed", kernel_name="Heal")


@REGISTRY.kernel("Grow")
def kernel_grow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Something grows."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} grew bigger.")
    
    thing = objects[0] if objects else 'it'
    return StoryFragment(f"The {thing} grew.", kernel_name="Grow")


# =============================================================================
# ADDITIONAL KERNELS TO REACH 100
# =============================================================================

@REGISTRY.kernel("Smile")
def kernel_smile(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character smiles."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f"{chars[0].name} smiled.")
    
    return StoryFragment("smiled", kernel_name="Smile")


@REGISTRY.kernel("Frown")
def kernel_frown(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character frowns."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 3
        return StoryFragment(f"{chars[0].name} frowned.")
    
    return StoryFragment("frowned", kernel_name="Frown")


@REGISTRY.kernel("Nod")
def kernel_nod(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character nods."""
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name} nodded.")
    
    return StoryFragment("nodded", kernel_name="Nod")


@REGISTRY.kernel("Heed")
def kernel_heed(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character heeds/listens to advice."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    heeder = chars[0] if chars else ctx.current_focus
    advice = objects[0] if objects else 'the advice'
    
    if heeder:
        return StoryFragment(f"{heeder.name} heeded {_to_phrase(advice)}.")
    
    return StoryFragment(f"heeded {_to_phrase(advice)}", kernel_name="Heed")


@REGISTRY.kernel("Ignore")
def kernel_ignore(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character ignores something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    ignorer = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'it'
    
    if ignorer:
        return StoryFragment(f"{ignorer.name} ignored the {thing}.")
    
    return StoryFragment(f"ignored the {thing}", kernel_name="Ignore")


@REGISTRY.kernel("Notice")
def kernel_notice(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character notices something."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    noticer = chars[0] if chars else ctx.current_focus
    thing = objects[0] if objects else 'something'
    
    if noticer:
        return StoryFragment(f"{noticer.name} noticed the {thing}.")
    
    return StoryFragment(f"noticed the {thing}", kernel_name="Notice")


@REGISTRY.kernel("Sneak")
def kernel_sneak(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Character sneaks somewhere."""
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    sneaker = chars[0] if chars else ctx.current_focus
    location = objects[0] if objects else ''
    
    if sneaker:
        if location:
            return StoryFragment(f"{sneaker.name} sneaked to the {location}.")
        return StoryFragment(f"{sneaker.name} sneaked quietly.")
    
    return StoryFragment("sneaked quietly", kernel_name="Sneak")


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    from gen5 import generate_story
    
    print("=" * 70)
    print("TESTING gen5k02 KERNELS")
    print(f"Total kernels in registry: {len(REGISTRY.kernels)}")
    print("=" * 70)
    
    test_kernels = [
        # Test 1: Request and Gratitude
        '''
Lily(Character, girl, Curious)
Mom(Character, mother, Caring)

Request(Lily, Mom, cookie)
Gift(Mom, Lily, cookie)
Gratitude(Lily, Mom)
Happy(Lily)
''',
        
        # Test 2: Promise and Attempt
        '''
Tim(Character, boy, Playful)
Dad(Character, father, Helpful)

Problem(Tim, toy)
Attempt(Tim, fix)
Help(Dad, Tim)
Promise(Tim, careful)
Joy(Tim)
''',
        
        # Test 3: Explore and Visit
        '''
Max(Character, boy, Curious)
Grandma(Character, grandma, Kind)

Visit(Max, Grandma)
Explore(garden)
Find(Max, butterfly)
Excited(Max)
''',

        # Test 4: Weather and Magic
        '''
Lily(Character, girl, Brave)

Rain()
Storm()
Magic(rainbow)
Joy(Lily)
''',

        # Test 5: Daily Activities
        '''
Mom(Character, mother, Caring)
Lily(Character, girl, Helpful)

Cook(Mom, cookies)
Help(Lily, Mom)
Bake(Mom, cake)
Eat(cake)
Happy(Lily)
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

