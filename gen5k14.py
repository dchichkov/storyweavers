#!/usr/bin/env python3
"""
gen5k14.py - Additional Kernel Pack #14

This pack implements 30 missing kernels from the coverage report, focusing on:
- Outdoor activities: Picnic, ParkVisit, Playday, Sail
- Emotional states: Dislike, Rejection, Obedience
- Actions: Clap, Hang, Demand, Confront, Cover, Spray, Load, Burn
- Events: Feast, Departure, Damage, Performance, Test
- Social: Borrow, Snack, Order, Appear, Instruction, Possession, Print, Prompt

KERNELS IMPLEMENTED:
- Picnic: Outdoor eating event in a pleasant setting
- If: Conditional statement or situation
- ParkVisit: Going to the park for recreation
- Playday: A day spent playing
- Dislike: Not liking something or someone
- Clap: Clapping hands in appreciation or rhythm
- Feast: A large celebratory meal
- Departure: Leaving or going away
- Damage: Harm or injury to something
- Obedience: Following rules or instructions
- Hang: Hanging something or hanging around
- Demand: Insistent request or requirement
- Print: Printing something (picture, document)
- Order: Ordering (food, commands, arrangement)
- Appear: Something or someone appearing
- Test: Testing or trying something out
- Borrow: Borrowing something from someone
- Snack: A small meal or treat
- Spray: Spraying liquid or substance
- Prompt: Prompting or encouraging action
- Load: Loading items onto something
- Performance: A show or performance event
- Confront: Facing someone or something directly
- Cover: Covering something up
- Sail: Sailing on water
- Rejection: Being rejected or refusing
- Instruction: Giving or receiving instructions
- Possession: Owning or having something
- Burn: Something burning or getting burned

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
# OUTDOOR ACTIVITIES
# =============================================================================

@REGISTRY.kernel("Picnic")
def kernel_picnic(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Outdoor eating event in a pleasant setting.
    
    Patterns from dataset:
      - Picnic(participants=[Mia, Mom, Tom, Lily], location=park, ...)
      - Routine(Picnic, basket(sandwich, juice))
      - Day(park, actions=Run+Swing+Picnic)
    
    Usage: Outdoor family/friend activity with food and fun.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    participants = kwargs.get('participants', chars)
    location = kwargs.get('location', 'park')
    food = kwargs.get('food', None)
    setup = kwargs.get('setup', None)
    
    parts = []
    
    # Get actor(s)
    if participants:
        for p in participants:
            if isinstance(p, Character):
                p.Joy += 8
        
        names = [p.name if isinstance(p, Character) else str(p) for p in participants]
        names_str = NLGUtils.join_list(names)
        parts.append(f"{names_str} had a lovely picnic at the {location}.")
    elif chars:
        char = chars[0]
        char.Joy += 8
        parts.append(f"{char.name} had a lovely picnic at the {location}.")
    else:
        parts.append(f"They had a wonderful picnic at the {location}.")
    
    # Food details
    if food:
        food_items = [str(f) for f in food] if hasattr(food, '__iter__') and not isinstance(food, str) else [str(food)]
        parts.append(f"They ate {NLGUtils.join_list(food_items)}.")
    
    return StoryFragment(' '.join(parts), kernel_name="Picnic")


@REGISTRY.kernel("ParkVisit")
def kernel_park_visit(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Going to the park for recreation.
    
    Patterns from dataset:
      - ParkVisit(Emma, place=park)
      - catalyst = ParkVisit
      - catalyst=ParkVisit(bench, pond, ducks)
    
    Usage: Catalyst for adventures, often leads to encounters and discoveries.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    place = kwargs.get('place', 'park')
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Joy += 6
        if objects:
            details = NLGUtils.join_list(objects)
            return StoryFragment(f"{char.name} went to the {place} where there was {details}.")
        return StoryFragment(f"{char.name} went to the {place} to play.")
    
    if objects:
        return StoryFragment(f"a visit to the {place} with {NLGUtils.join_list(objects)}", kernel_name="ParkVisit")
    
    return StoryFragment(f"a trip to the {place}", kernel_name="ParkVisit")


@REGISTRY.kernel("Playday")
def kernel_playday(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A day spent playing.
    
    Patterns from dataset:
      - Playday(Tom, state=Routine+Curiosity(...))
      - Playday(Tom+Sam, state=Routine+Rain+Slide, ...)
      - Playday(participants=[Max, Lily], setting=Park, ...)
    
    Usage: Frame for a story about playing, often with process and outcome.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    participants = kwargs.get('participants', chars)
    setting = kwargs.get('setting', 'outside')
    process = kwargs.get('process', None)
    outcome = kwargs.get('outcome', None)
    
    parts = []
    
    # Get participants
    if participants:
        for p in participants:
            if isinstance(p, Character):
                p.Joy += 10
        
        names = [p.name if isinstance(p, Character) else str(p) for p in participants]
        names_str = NLGUtils.join_list(names)
        parts.append(f"{names_str} had a wonderful day playing {setting}.")
    elif chars:
        char = chars[0]
        char.Joy += 10
        parts.append(f"{char.name} had a wonderful day playing {setting}.")
    else:
        parts.append(f"It was a wonderful day of playing.")
    
    # Process
    if process:
        process_text = _event_to_phrase(process)
        if process_text:
            parts.append(f"They {process_text}.")
    
    # Outcome
    if outcome:
        outcome_text = _event_to_phrase(outcome)
        if outcome_text:
            parts.append(f"{outcome_text}.")
    
    return StoryFragment(' '.join(parts), kernel_name="Playday")


@REGISTRY.kernel("Sail")
def kernel_sail(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Sailing on water.
    
    Patterns from dataset:
      - Sail(boat, location=bathtub)
      - Sail(boat, on=water)
      - Sail(squash, Tim+Sue)  -- sailing on something unusual
    
    Usage: Water-based activity, often with toy boats or adventures.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    vessel = objects[0] if objects else 'boat'
    location = kwargs.get('on', kwargs.get('location', 'water'))
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Joy += 7
        return StoryFragment(f"{char.name} sailed the {vessel} on the {location}.")
    
    # Multiple chars
    if len(chars) > 1:
        names = [c.name for c in chars]
        return StoryFragment(f"{NLGUtils.join_list(names)} sailed on the {vessel}.")
    
    return StoryFragment(f"sailing on the {location}", kernel_name="Sail")


# =============================================================================
# EMOTIONAL STATES & REACTIONS
# =============================================================================

@REGISTRY.kernel("Dislike")
def kernel_dislike(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Not liking something or someone.
    
    Patterns from dataset:
      - Dislike(Lily, object=sandwich)
      - feeling=Dislike(gift)
      - Taste(Lily, item=soup) + Dislike(Lily)
    
    Usage: Expressing displeasure or aversion.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    obj = kwargs.get('object', objects[0] if objects else None)
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Anger += 3
        char.Sadness += 2
        
        if obj:
            return StoryFragment(f"{char.name} did not like the {obj}.")
        return StoryFragment(f"{char.name} didn't like it at all.")
    
    if obj:
        return StoryFragment(f"disliked the {obj}", kernel_name="Dislike")
    
    return StoryFragment("dislike", kernel_name="Dislike")


@REGISTRY.kernel("Rejection")
def kernel_rejection(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being rejected or refusing someone.
    
    Patterns from dataset:
      - catalyst=Rejection(Friends)
      - Rejection(Tom, mineral)  -- rejecting an object
      - Ask(play, Cat) + Reject(Cat)
    
    Usage: Sad moment when someone is turned away or refused.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    rejected_thing = objects[0] if objects else None
    
    if char:
        char.Sadness += 8
        char.Anger += 3
        
        if rejected_thing:
            return StoryFragment(f"{char.name} rejected the {rejected_thing}.")
        elif len(chars) > 1:
            return StoryFragment(f"{char.name} rejected {chars[1].name}.")
        return StoryFragment(f"{char.name} faced rejection.")
    
    if rejected_thing:
        return StoryFragment(f"there was rejection of {rejected_thing}", kernel_name="Rejection")
    
    return StoryFragment("rejection", kernel_name="Rejection")


@REGISTRY.kernel("Obedience")
def kernel_obedience(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Following rules or instructions.
    
    Patterns from dataset:
      - Obedience(Timmy, rule=Mom)
      - lesson=Obedience + Listen(Mom)
      - Obedience(Lily)
    
    Usage: Positive behavior of following rules, often as a lesson.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    rule = kwargs.get('rule', None)
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Joy += 3
        
        if rule:
            rule_text = rule.name if isinstance(rule, Character) else str(rule)
            return StoryFragment(f"{char.name} listened and obeyed {rule_text}.")
        return StoryFragment(f"{char.name} was obedient and followed the rules.")
    
    return StoryFragment("obedience", kernel_name="Obedience")


# =============================================================================
# ACTIONS & GESTURES
# =============================================================================

@REGISTRY.kernel("Clap")
def kernel_clap(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Clapping hands in appreciation or rhythm.
    
    Patterns from dataset:
      - Clap + Praise(Not(Frightened))
      - Dance + Clap + Stomp
      - Smile(Tim, Mom) + Clap(Tim, Mom)
    
    Usage: Celebration, applause, or rhythmic activity.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        for char in chars:
            char.Joy += 5
        
        if len(chars) == 1:
            return StoryFragment(f"{chars[0].name} clapped happily.")
        else:
            names = [c.name for c in chars]
            return StoryFragment(f"{NLGUtils.join_list(names)} clapped their hands.")
    
    return StoryFragment("everyone clapped", kernel_name="Clap")


@REGISTRY.kernel("Hang")
def kernel_hang(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Hanging something or hanging around.
    
    Patterns from dataset:
      - Hang(picture)  -- hanging an object
      - Hang(branch)   -- holding onto branch
      - Capture + Hang + Surrender  -- being hung/suspended
    
    Usage: Physical action of suspending or being suspended.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    obj = objects[0] if objects else None
    
    char = chars[0] if chars else ctx.current_focus
    
    if char and obj:
        return StoryFragment(f"{char.name} hung the {obj} up.")
    elif obj:
        return StoryFragment(f"the {obj} was hung up", kernel_name="Hang")
    elif char:
        return StoryFragment(f"{char.name} hung on tight.")
    
    return StoryFragment("hung up", kernel_name="Hang")


@REGISTRY.kernel("Demand")
def kernel_demand(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Insistent request or requirement.
    
    Patterns from dataset:
      - Demand(Mom, give=toys, threat=Timeout)
      - Demand(orange, from=mom)
      - demand=Demand(Ben, return blocks)
    
    Usage: Forceful asking, often leads to conflict.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    give = kwargs.get('give', None)
    fr = kwargs.get('from', None)
    threat = kwargs.get('threat', None)
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Anger += 4
        
        if give:
            give_text = str(give)
            if threat:
                return StoryFragment(f'{char.name} demanded the {give_text} or else!')
            return StoryFragment(f'{char.name} demanded the {give_text}.')
        elif objects:
            return StoryFragment(f'{char.name} demanded {objects[0]}.')
        return StoryFragment(f'{char.name} made a demand.')
    
    return StoryFragment("a demand was made", kernel_name="Demand")


@REGISTRY.kernel("Confront")
def kernel_confront(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Facing someone or something directly.
    
    Patterns from dataset:
      - Confront(Tom, Monster, action=shout)
      - Stand(Duck, action=Confront(Frog), message=Fairness)
      - Confront(Sister)
    
    Usage: Brave act of standing up to someone/something.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    action = kwargs.get('action', None)
    message = kwargs.get('message', None)
    
    if len(chars) >= 2:
        chars[0].Fear -= 3
        chars[0].Anger += 3
        
        if action:
            return StoryFragment(f"{chars[0].name} confronted {chars[1].name} and {action}ed.")
        elif message:
            return StoryFragment(f'{chars[0].name} confronted {chars[1].name} about {message}.')
        return StoryFragment(f"{chars[0].name} bravely confronted {chars[1].name}.")
    
    if chars:
        char = chars[0]
        char.Fear -= 3
        return StoryFragment(f"{char.name} stood up and confronted them.")
    
    return StoryFragment("a confrontation happened", kernel_name="Confront")


@REGISTRY.kernel("Cover")
def kernel_cover(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Covering something up.
    
    Patterns from dataset:
      - Cover(tree)         -- taking cover under tree
      - Cover(Cloud, Sun)   -- cloud covering sun
      - Cover(blanket)      -- covering with blanket
    
    Usage: Protection, hiding, or obscuring something.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    obj = objects[0] if objects else None
    
    # Two characters - one covering another
    if len(chars) >= 2:
        return StoryFragment(f"{chars[0].name} covered {chars[1].name}.")
    
    # Character with object
    if char and obj:
        return StoryFragment(f"{char.name} was covered by the {obj}.")
    
    # Just object - taking cover or something being covered
    if obj:
        ctx.current_object = obj
        return StoryFragment(f"took cover under the {obj}", kernel_name="Cover")
    
    return StoryFragment("covered up", kernel_name="Cover")


@REGISTRY.kernel("Spray")
def kernel_spray(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Spraying liquid or substance.
    
    Patterns from dataset:
      - Spray(bottle, target=Flower)
      - Spray(doll)  -- spraying perfume on doll
      - Attack(Skunk, Spray(stink))
    
    Usage: Using spray bottle, or animal spraying (skunk).
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    target = kwargs.get('target', None)
    
    char = chars[0] if chars else ctx.current_focus
    spray_with = objects[0] if objects else 'water'
    
    if target:
        target_text = target.name if isinstance(target, Character) else str(target)
        if char:
            return StoryFragment(f"{char.name} sprayed the {target_text} with {spray_with}.")
        return StoryFragment(f"sprayed {target_text}", kernel_name="Spray")
    
    if char:
        return StoryFragment(f"{char.name} sprayed the {spray_with}.")
    
    return StoryFragment(f"the {spray_with} was sprayed", kernel_name="Spray")


@REGISTRY.kernel("Load")
def kernel_load(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Loading items onto something.
    
    Patterns from dataset:
      - Load(truck, wagon)
      - Load(hay, wagon)
      - Load(apples) + Load(bananas) + Load(bread) + PutIn(car)
    
    Usage: Putting items onto a vehicle or container.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    
    if len(objects) >= 2:
        item, container = objects[0], objects[1]
        if char:
            return StoryFragment(f"{char.name} loaded the {item} onto the {container}.")
        return StoryFragment(f"the {item} was loaded onto the {container}", kernel_name="Load")
    
    if objects:
        item = objects[0]
        if char:
            return StoryFragment(f"{char.name} loaded the {item}.")
        return StoryFragment(f"loaded the {item}", kernel_name="Load")
    
    return StoryFragment("loading up", kernel_name="Load")


@REGISTRY.kernel("Burn")
def kernel_burn(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something burning or getting burned.
    
    Patterns from dataset:
      - Burn(feather)    -- feather burning
      - Burn(tail)       -- tail getting burned
      - Burn(hand) + Burn(apron)
    
    Usage: Accident involving fire or heat, often in cautionary tales.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    what = objects[0] if objects else None
    
    char = chars[0] if chars else ctx.current_focus
    
    if char and what:
        char.Fear += 5
        char.Sadness += 4
        return StoryFragment(f"{char.name}'s {what} got burned!")
    
    if what:
        return StoryFragment(f"the {what} got burned", kernel_name="Burn")
    
    if char:
        char.Fear += 5
        return StoryFragment(f"{char.name} got burned!")
    
    return StoryFragment("something burned", kernel_name="Burn")


# =============================================================================
# EVENTS & SITUATIONS
# =============================================================================

@REGISTRY.kernel("Feast")
def kernel_feast(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A large celebratory meal.
    
    Patterns from dataset:
      - Feast(sausage)  -- feast on sausage
      - Feast(Timmy, food=pizza)
      - Feast(cake, participants=[Tom,Sue])
    
    Usage: Reward or celebration with food.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    food = kwargs.get('food', objects[0] if objects else 'delicious food')
    participants = kwargs.get('participants', chars)
    
    if participants:
        for p in participants:
            if isinstance(p, Character):
                p.Joy += 10
        
        names = [p.name if isinstance(p, Character) else str(p) for p in participants]
        names_str = NLGUtils.join_list(names)
        return StoryFragment(f"{names_str} enjoyed a wonderful feast of {food}.")
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Joy += 10
        return StoryFragment(f"{char.name} had a big feast of {food}.")
    
    return StoryFragment(f"a feast of {food}", kernel_name="Feast")


@REGISTRY.kernel("Departure")
def kernel_departure(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Leaving or going away.
    
    Patterns from dataset:
      - Departure(brother, cause=Trouble, farewell=goodbye+hug)
      - Sunset(event=Departure, cause=Evening, action=Bye)
      - Departure(Tim, Cat)
    
    Usage: Sad moment of parting, often followed by reunion.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    cause = kwargs.get('cause', None)
    farewell = kwargs.get('farewell', None)
    
    parts = []
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Sadness += 5
        
        if cause:
            parts.append(f"{char.name} had to leave because of {cause}.")
        else:
            parts.append(f"It was time for {char.name} to go.")
        
        if farewell:
            parts.append(f"They said goodbye with {farewell}.")
        else:
            parts.append("They waved goodbye sadly.")
        
        return StoryFragment(' '.join(parts), kernel_name="Departure")
    
    return StoryFragment("it was time to leave", kernel_name="Departure")


@REGISTRY.kernel("Damage")
def kernel_damage(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Harm or injury to something.
    
    Patterns from dataset:
      - Damage(coat)           -- coat got damaged
      - Damage(fan)            -- fan got damaged
      - consequence=Damage(Scarf, cause=Cat)
    
    Usage: Result of accident, often leads to repair or sadness.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    cause = kwargs.get('cause', None)
    obj = objects[0] if objects else ctx.current_object
    
    char = chars[0] if chars else ctx.current_focus
    
    if char:
        char.Sadness += 5
    
    if obj:
        if cause:
            return StoryFragment(f"the {obj} was damaged by {cause}.")
        return StoryFragment(f"the {obj} got damaged.")
    
    return StoryFragment("something got damaged", kernel_name="Damage")


@REGISTRY.kernel("Performance")
def kernel_performance(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A show or performance event.
    
    Patterns from dataset:
      - Performance(Musician, state=Routine+Play(drum)+...)
      - Performance(stage=high, audience=friends, actors=Tim+Sally)
    
    Usage: Music, plays, or shows being performed.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    stage = kwargs.get('stage', None)
    audience = kwargs.get('audience', None)
    actors = kwargs.get('actors', chars)
    content = kwargs.get('content', None)
    
    parts = []
    
    if actors:
        for a in actors:
            if isinstance(a, Character):
                a.Joy += 8
        
        names = [a.name if isinstance(a, Character) else str(a) for a in actors]
        names_str = NLGUtils.join_list(names)
        parts.append(f"{names_str} put on a wonderful performance!")
    else:
        parts.append("There was a wonderful performance!")
    
    if audience:
        aud_text = audience.name if isinstance(audience, Character) else str(audience)
        parts.append(f"The {aud_text} watched and cheered.")
    
    return StoryFragment(' '.join(parts), kernel_name="Performance")


@REGISTRY.kernel("Test")
def kernel_test(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Testing or trying something out.
    
    Patterns from dataset:
      - Test(toycar, across=bridge)
      - Test(cooking=broccoli+butter+garlic, target=Lily)
      - Roar(Lion) + Test(house(strong))
    
    Usage: Trying something to see if it works.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    target = kwargs.get('target', None)
    
    char = chars[0] if chars else ctx.current_focus
    obj = objects[0] if objects else ctx.current_object
    
    if char and obj:
        return StoryFragment(f"{char.name} tested the {obj}.")
    
    if obj:
        return StoryFragment(f"the {obj} was tested", kernel_name="Test")
    
    if target:
        target_text = target.name if isinstance(target, Character) else str(target)
        return StoryFragment(f"it was time to test {target_text}", kernel_name="Test")
    
    return StoryFragment("a test was done", kernel_name="Test")


# =============================================================================
# SOCIAL INTERACTIONS
# =============================================================================

@REGISTRY.kernel("Borrow")
def kernel_borrow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Borrowing something from someone.
    
    Patterns from dataset:
      - Borrow(folder, lender=Lily, borrower=Tom)
      - Borrow(bike, Timmy)
      - Borrow(Ornament, from=Mom)
    
    Usage: Taking something temporarily with permission.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    lender = kwargs.get('lender', kwargs.get('from', None))
    borrower = kwargs.get('borrower', chars[0] if chars else ctx.current_focus)
    item = objects[0] if objects else 'it'
    
    if borrower and lender:
        borrower_name = borrower.name if isinstance(borrower, Character) else str(borrower)
        lender_name = lender.name if isinstance(lender, Character) else str(lender)
        return StoryFragment(f"{borrower_name} borrowed the {item} from {lender_name}.")
    
    if borrower:
        borrower_name = borrower.name if isinstance(borrower, Character) else str(borrower)
        return StoryFragment(f"{borrower_name} borrowed the {item}.")
    
    return StoryFragment(f"the {item} was borrowed", kernel_name="Borrow")


@REGISTRY.kernel("Snack")
def kernel_snack(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A small meal or treat.
    
    Patterns from dataset:
      - Snack(crackers, cheese)
      - Discovery(Snack(bug), teacher=Tim)
      - Share(Snack, Timmy, Mom)
    
    Usage: Small food items, often shared or discovered.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    foods = objects if objects else ['snack']
    
    if char:
        char.Joy += 4
        if len(foods) > 1:
            return StoryFragment(f"{char.name} had a snack of {NLGUtils.join_list(foods)}.")
        return StoryFragment(f"{char.name} had a yummy {foods[0]}.")
    
    if objects:
        return StoryFragment(f"a snack of {NLGUtils.join_list(objects)}", kernel_name="Snack")
    
    return StoryFragment("snack time", kernel_name="Snack")


@REGISTRY.kernel("Order")
def kernel_order(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Ordering (food, commands, or arrangement).
    
    Patterns from dataset:
      - Order(pizza)              -- ordering food
      - Order + Happy             -- as state/result
      - Help(provider=Mom, action=Order(cocoa))
    
    Usage: Ordering food at restaurant or arranging things.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    item = objects[0] if objects else None
    
    if char and item:
        char.Joy += 3
        return StoryFragment(f"{char.name} ordered {item}.")
    
    if item:
        return StoryFragment(f"ordered {item}", kernel_name="Order")
    
    # Order as arrangement
    return StoryFragment("everything was put in order", kernel_name="Order")


@REGISTRY.kernel("Appear")
def kernel_appear(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something or someone appearing.
    
    Patterns from dataset:
      - Appear(rock, roof)        -- rock appears on roof
      - Appear(Cat) + Steal(Cat, bell)
      - Appear(LittleGirl) + Ask(...)
    
    Usage: Sudden appearance, often surprising.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    location = objects[0] if objects else None
    
    if chars:
        char = chars[0]
        if location:
            return StoryFragment(f"Suddenly, {char.name} appeared at the {location}!")
        return StoryFragment(f"Suddenly, {char.name} appeared!")
    
    if objects:
        obj = objects[0]
        if len(objects) > 1:
            return StoryFragment(f"The {obj} appeared on the {objects[1]}!")
        return StoryFragment(f"The {obj} appeared!", kernel_name="Appear")
    
    return StoryFragment("something appeared", kernel_name="Appear")


@REGISTRY.kernel("Instruction")
def kernel_instruction(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Giving or receiving instructions.
    
    Patterns from dataset:
      - Instruction(remote, steam)     -- instructions about remote and steam
      - Instruction(Mommy, putOn(coat))
      - catalyst=Instruction
    
    Usage: Teaching, explaining, or directing someone.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    
    if char and objects:
        topic = NLGUtils.join_list(objects)
        return StoryFragment(f"{char.name} gave instructions about {topic}.")
    
    if objects:
        return StoryFragment(f"instructions about {NLGUtils.join_list(objects)}", kernel_name="Instruction")
    
    if char:
        return StoryFragment(f"{char.name} gave careful instructions.")
    
    return StoryFragment("instructions were given", kernel_name="Instruction")


@REGISTRY.kernel("Possession")
def kernel_possession(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Owning or having something.
    
    Patterns from dataset:
      - Possession(belt)              -- owning a belt
      - Possession(toyCar)            -- having a toy car
      - Desire + Possession           -- wanting and having
    
    Usage: State of owning something, often cherished items.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    item = objects[0] if objects else 'treasure'
    
    if char:
        return StoryFragment(f"{char.name} had a special {item}.")
    
    return StoryFragment(f"possession of {item}", kernel_name="Possession")


@REGISTRY.kernel("Print")
def kernel_print(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Printing something (picture, document).
    
    Patterns from dataset:
      - Print(picture)
      - Idea(Timmy, plan=Print(picture))
      - Print(bracelet, styles=[sparkly, colourful])
    
    Usage: Using a printer to make copies or images.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    char = chars[0] if chars else ctx.current_focus
    item = objects[0] if objects else 'picture'
    
    if char:
        return StoryFragment(f"{char.name} printed a {item}.")
    
    return StoryFragment(f"the {item} was printed", kernel_name="Print")


@REGISTRY.kernel("Prompt")
def kernel_prompt(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Prompting or encouraging action.
    
    Patterns from dataset:
      - Prompt(Mom, clean)            -- mom prompts to clean
      - Prompt(Mom, question=Opinion)
      - Prompt(Girl, say(potato))     -- prompting to speak
    
    Usage: Encouraging someone to do or say something.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    question = kwargs.get('question', None)
    
    char = chars[0] if chars else ctx.current_focus
    action = objects[0] if objects else None
    
    if char and action:
        return StoryFragment(f"{char.name} prompted them to {action}.")
    
    if char and question:
        return StoryFragment(f"{char.name} asked about their {question}.")
    
    if char:
        return StoryFragment(f"{char.name} gave a gentle prompt.")
    
    return StoryFragment("there was a prompt", kernel_name="Prompt")


@REGISTRY.kernel("If")
def kernel_if(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Conditional statement or situation.
    
    Patterns from dataset:
      - If(Read(History), Make(sandwich))
      - If(Share(Food), Help(Pain) + Relief)
      - advice=If(Want, Manage)
    
    Usage: Expressing conditions and consequences.
    """
    args_list = list(args)
    
    # Try to identify condition and consequence
    if len(args_list) >= 2:
        condition = args_list[0]
        consequence = args_list[1]
        
        cond_text = _event_to_phrase(condition) if not isinstance(condition, str) else condition
        cons_text = _event_to_phrase(consequence) if not isinstance(consequence, str) else consequence
        
        if cond_text and cons_text:
            return StoryFragment(f"if {cond_text}, then {cons_text}", kernel_name="If")
    
    if args_list:
        text = _event_to_phrase(args_list[0]) if not isinstance(args_list[0], str) else str(args_list[0])
        return StoryFragment(f"if only {text}", kernel_name="If")
    
    return StoryFragment("if only", kernel_name="If")


# =============================================================================
# TEST RUNNER
# =============================================================================

if __name__ == "__main__":
    """Test the kernels in this pack."""
    print(f"\n{'='*70}")
    print(f"Testing gen5k14.py - Kernel Pack #14")
    print(f"{'='*70}\n")
    
    from gen5registry import REGISTRY as REG
    
    # Count kernels from this file
    this_file_kernels = [
        'Picnic', 'If', 'ParkVisit', 'Playday', 'Dislike', 'Clap', 'Feast',
        'Departure', 'Damage', 'Obedience', 'Hang', 'Demand', 'Print', 'Order',
        'Appear', 'Test', 'Borrow', 'Snack', 'Spray', 'Prompt', 'Load',
        'Performance', 'Confront', 'Cover', 'Sail', 'Rejection', 'Instruction',
        'Possession', 'Burn'
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
    print(f"Test specific kernels with:")
    print(f"  python sample.py -k Picnic -n 3 --seed 42")
    print(f"  python sample.py -k Feast -n 3 --seed 42")
    print(f"{'='*70}\n")

