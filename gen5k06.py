"""
gen5k06.py - Additional Kernel Pack #06

This module extends gen5.py with 100 additional kernel implementations.
Import this module after gen5 to register the new kernels.

=============================================================================
KERNELS IN THIS PACK (100 kernels from dataset sampling):
=============================================================================

## Trait/Character Attribute Kernels (40)
- Cautious: Being careful and wary
- Hungry: State of wanting food
- Eager: Being enthusiastic and ready
- Mischievous: Playfully troublesome
- Warm: Friendly and comforting personality
- Learner: Someone who learns
- Fearful: Being afraid
- Stubborn: Refusing to change
- Attached: Emotionally connected
- Resourceful: Clever at finding solutions
- Imaginative: Having creative imagination
- Encouraging: Giving support/encouragement
- Compassionate: Showing compassion
- Impatient: Lacking patience
- Hardworking: Working diligently
- Strict: Demanding rules be followed
- Trusting: Placing trust in others
- Energetic: Full of energy
- Reckless: Acting without caution
- Alert: Watchful and aware
- Permissive: Allowing freedom
- Guiding: Leading/directing
- Absent: Not present
- Clumsy: Lacking coordination
- Funny: Causing laughter
- Innocent: Pure and naive
- Teaching: Instructing others
- Reluctant: Unwilling/hesitant
- Long: Physical attribute of length
- Fast: Quick movement
- Yellow: Color attribute
- Broken: State of being damaged
- Observant: Good at noticing things
- Gentle: Kind and mild
- Protective: Guarding from harm
- Calm: Not agitated or excited
- Supportive: Providing support
- Dreamy: Given to daydreaming
- Excited: Very enthusiastic

## Action/Interaction Kernels (35)
- Pet: Stroking/petting an animal
- Lick: Animal licking gesture
- Unlock: Opening a lock
- Lock: Securing with a lock
- Replace: Substituting old for new
- Bark: Dog barking
- Scare: Frightening someone
- Chew: Chewing on something
- Wag: Tail wagging
- Knock: Knocking on door
- Steal: Taking without permission
- Free: Releasing/liberating
- Spin: Turning around
- Move: Physical movement
- Approach: Coming closer
- Discard: Throwing away
- Obtain: Getting/acquiring
- Store: Putting away for keeping
- Count: Counting items
- Pick: Picking/selecting
- Taste: Tasting food/drink
- Cuddle: Snuggling together
- Bite: Biting action
- Scratch: Scratching action
- Sniff: Smelling something
- Pounce: Jumping on prey
- Growl: Low threatening sound
- Purr: Cat purring
- Meow: Cat vocalization
- Chirp: Bird sound
- Hop: Small jumping movement
- Crawl: Moving on hands/knees
- Squeeze: Pressing tightly
- Splash: Water splashing
- Pour: Pouring liquid

## State/Condition Kernels (15)
- Hunger: State of being hungry
- Fatigue: Being tired
- Freedom: State of being free
- Satisfaction: Being satisfied
- Loneliness: Being alone
- Illness: Being sick
- Sickness: State of illness
- Courage: Having bravery
- Gluttony: Excessive eating
- Pride: Feeling proud
- Effort: Trying hard
- Confidence: Self-assurance
- Safe: Being secure
- Cozy: Comfortable and warm
- Messy: State of disorder

## Structural/Narrative Kernels (10)
- Collaboration: Working together on task
- Bonding: Forming emotional connection
- Companion: Being a companion
- Routine: Daily/regular activity
- Vacation: Holiday/trip
- Permission: Being allowed
- Restriction: A limitation/rule
- Condition: Prerequisite/requirement
- Contribution: Adding to something
- SaveMoney: Financial saving

=============================================================================

Usage:
    from gen5 import generate_story, REGISTRY
    import gen5k06  # Registers additional kernels
    
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
# TRAIT/CHARACTER ATTRIBUTE KERNELS
# =============================================================================

@REGISTRY.kernel("Cautious")
def kernel_cautious(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being careful and wary; used as character trait.
    
    Patterns from dataset:
      - Tom(Character, Cautious+Protective)
      - Dad(Character, parent, Guiding+Cautious)
      - Man(Character, adult, Helpful+Cautious)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 3  # Cautious people are slightly fearful
        return StoryFragment(f'{chars[0].name} was very cautious.')
    
    return StoryFragment("cautious", kernel_name="Cautious")


@REGISTRY.kernel("Hungry")
def kernel_hungry(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    State of wanting food.
    
    Patterns from dataset:
      - Girl(Character, child, Hungry + Impatient)
      - Fox(Character, Mischievous+Hungry+Friendly)
      - Amy(Character, girl, Playful + Hungry)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 2  # Hunger causes some discomfort
        return StoryFragment(f'{chars[0].name} was hungry.')
    
    return StoryFragment("hungry", kernel_name="Hungry")


@REGISTRY.kernel("Eager")
def kernel_eager(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being enthusiastic and ready.
    
    Patterns from dataset:
      - Lily(Character, girl, Eager + Helpful)
      - Timmy(Character, boy, Eager + Grateful)
      - Buddy(Character, dog, Excited + Learner)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} was eager and ready.')
    
    return StoryFragment("eager", kernel_name="Eager")


@REGISTRY.kernel("Mischievous")
def kernel_mischievous(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Playfully troublesome character trait.
    
    Patterns from dataset:
      - MrFluffy(Character, bunny, Mischievous)
      - Dog(Character, playful + Mischievous)
      - Fox(Character, Mischievous+Hungry+Friendly)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} was mischievous.')
    
    return StoryFragment("mischievous", kernel_name="Mischievous")


@REGISTRY.kernel("Warm")
def kernel_warm(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Friendly and comforting personality or physical warmth.
    
    Patterns from dataset:
      - Rosie(Character, rabbit, Friendly + Warm)
      - Cuddle(Jojo, Mom, rest=Rest(pillow) + Warm + Cozy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 5
        chars[0].Joy += 3
        return StoryFragment(f'{chars[0].name} felt warm and cozy.')
    
    return StoryFragment("warm and cozy", kernel_name="Warm")


@REGISTRY.kernel("Learner")
def kernel_learner(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Someone who is learning.
    
    Patterns from dataset:
      - Tim(Character, boy, Reluctant + Learner)
      - Buddy(Character, dog, Excited + Learner)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f'{chars[0].name} was a quick learner.')
    
    return StoryFragment("learner", kernel_name="Learner")


@REGISTRY.kernel("Fearful")
def kernel_fearful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being afraid or prone to fear.
    
    Patterns from dataset:
      - Timmy(Character, boy, Fearful+Curious)
      - Friends(Character, group, Fearful)
      - Tim(Character,dog,Kind+Fearful+Hopeful)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 8
        return StoryFragment(f'{chars[0].name} was fearful.')
    
    return StoryFragment("fearful", kernel_name="Fearful")


@REGISTRY.kernel("Stubborn")
def kernel_stubborn(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Refusing to change mind or behavior.
    
    Patterns from dataset:
      - Character trait indicating resistance to change
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Anger += 3
        return StoryFragment(f'{chars[0].name} was very stubborn.')
    
    return StoryFragment("stubborn", kernel_name="Stubborn")


@REGISTRY.kernel("Attached")
def kernel_attached(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Emotionally connected to someone/something.
    
    Patterns from dataset:
      - Lucy(Character, child, Attached + Playful)
    """
    chars = [a for a in args if isinstance(a, Character)]
    to = kwargs.get('to', None)
    
    if chars:
        chars[0].Love += 8
        if to:
            return StoryFragment(f'{chars[0].name} was very attached to {_to_phrase(to)}.')
        return StoryFragment(f'{chars[0].name} was very attached.')
    
    return StoryFragment("attached", kernel_name="Attached")


@REGISTRY.kernel("Resourceful")
def kernel_resourceful(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Clever at finding solutions.
    
    Patterns from dataset:
      - Character trait for problem-solving characters
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} was very resourceful.')
    
    return StoryFragment("resourceful", kernel_name="Resourceful")


@REGISTRY.kernel("Imaginative")
def kernel_imaginative(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Having creative imagination.
    
    Patterns from dataset:
      - Used for creative, dreamy characters
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} was very imaginative.')
    
    return StoryFragment("imaginative", kernel_name="Imaginative")


@REGISTRY.kernel("Encouraging")
def kernel_encouraging(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Giving support and encouragement.
    
    Patterns from dataset:
      - Parent or friend encouraging character
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 5
        return StoryFragment(f'{chars[0].name} was very encouraging.')
    
    return StoryFragment("encouraging", kernel_name="Encouraging")


@REGISTRY.kernel("Compassion")
def kernel_compassion(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Showing compassion for others.
    
    Patterns from dataset:
      - insight=Compassion
      - Rescue outcome involving compassion
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 8
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} showed great compassion.')
    
    return StoryFragment("compassion", kernel_name="Compassion")


@REGISTRY.kernel("Impatient")
def kernel_impatient(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Lacking patience.
    
    Patterns from dataset:
      - Girl(Character, child, Hungry + Impatient)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Anger += 3
        return StoryFragment(f'{chars[0].name} was impatient.')
    
    return StoryFragment("impatient", kernel_name="Impatient")


@REGISTRY.kernel("Hardworking")
def kernel_hardworking(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Working diligently.
    
    Patterns from dataset:
      - Mommy(Character, adult, Responsible + Hardworking)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} was very hardworking.')
    
    return StoryFragment("hardworking", kernel_name="Hardworking")


@REGISTRY.kernel("Strict")
def kernel_strict(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Demanding rules be followed.
    
    Patterns from dataset:
      - Mom(Character, caregiver, Strict + Caring)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was strict.')
    
    return StoryFragment("strict", kernel_name="Strict")


@REGISTRY.kernel("Trusting")
def kernel_trusting(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Placing trust in others.
    
    Patterns from dataset:
      - Girl(Character, Fearful + Trusting + Playful)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 5
        return StoryFragment(f'{chars[0].name} was very trusting.')
    
    return StoryFragment("trusting", kernel_name="Trusting")


@REGISTRY.kernel("Energetic")
def kernel_energetic(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Full of energy.
    
    Patterns from dataset:
      - Billy(Character, Energetic + Playful)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 6
        return StoryFragment(f'{chars[0].name} was full of energy.')
    
    return StoryFragment("energetic", kernel_name="Energetic")


@REGISTRY.kernel("Reckless")
def kernel_reckless(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Acting without caution.
    
    Patterns from dataset:
      - Billy(Character, boy, Reckless+Curious)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear -= 3  # Reckless = less fear
        return StoryFragment(f'{chars[0].name} was reckless.')
    
    return StoryFragment("reckless", kernel_name="Reckless")


@REGISTRY.kernel("Alert")
def kernel_alert(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Watchful and aware.
    
    Patterns from dataset:
      - Sam(Character, friend, Alert)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 2  # Alert = slightly on guard
        return StoryFragment(f'{chars[0].name} was alert.')
    
    return StoryFragment("alert", kernel_name="Alert")


@REGISTRY.kernel("Permissive")
def kernel_permissive(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Allowing freedom.
    
    Patterns from dataset:
      - Mom(Character, permissive)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was permissive.')
    
    return StoryFragment("permissive", kernel_name="Permissive")


@REGISTRY.kernel("Guiding")
def kernel_guiding(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Leading or directing others.
    
    Patterns from dataset:
      - Dad(Character, parent, Guiding+Cautious)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Love += 4
        return StoryFragment(f'{chars[0].name} was guiding.')
    
    return StoryFragment("guiding", kernel_name="Guiding")


@REGISTRY.kernel("Absent")
def kernel_absent(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Not present.
    
    Patterns from dataset:
      - Man(Character,human,Caring+Absent+Dead)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was absent.')
    
    return StoryFragment("absent", kernel_name="Absent")


@REGISTRY.kernel("Observant")
def kernel_observant(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Good at noticing things.
    
    Patterns from dataset:
      - Owner(Character, human, Unaware + Observant)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was very observant.')
    
    return StoryFragment("observant", kernel_name="Observant")


@REGISTRY.kernel("Dreamy")
def kernel_dreamy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Given to daydreaming.
    
    Patterns from dataset:
      - Jojo(Character, child, Excited + Curious + Dreamy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} was dreamy.')
    
    return StoryFragment("dreamy", kernel_name="Dreamy")


@REGISTRY.kernel("Chubby")
def kernel_chubby(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Physical trait - pleasantly plump.
    
    Patterns from dataset:
      - Kitty(Character, cat, Chubby + Collector)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was chubby.')
    
    return StoryFragment("chubby", kernel_name="Chubby")


@REGISTRY.kernel("Grumpy")
def kernel_grumpy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Bad-tempered trait.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Anger += 4
        return StoryFragment(f'{chars[0].name} was grumpy.')
    
    return StoryFragment("grumpy", kernel_name="Grumpy")


@REGISTRY.kernel("Shy")
def kernel_shy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Timid/shy trait.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 3
        return StoryFragment(f'{chars[0].name} was shy.')
    
    return StoryFragment("shy", kernel_name="Shy")


@REGISTRY.kernel("Noisy")
def kernel_noisy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Making lots of noise.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was noisy.')
    
    return StoryFragment("noisy", kernel_name="Noisy")


@REGISTRY.kernel("Sleepy")
def kernel_sleepy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Tired/drowsy trait.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 2
        return StoryFragment(f'{chars[0].name} was sleepy.')
    
    return StoryFragment("sleepy", kernel_name="Sleepy")


@REGISTRY.kernel("Thirsty")
def kernel_thirsty(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Wanting a drink.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was thirsty.')
    
    return StoryFragment("thirsty", kernel_name="Thirsty")


@REGISTRY.kernel("Long")
def kernel_long(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Physical attribute of length.
    
    Patterns from dataset:
      - Sammy(Character, snake, Big + Long + Playful + Curious)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was long.')
    if objects:
        return StoryFragment(f"the {objects[0]} was long", kernel_name="Long")
    
    return StoryFragment("long", kernel_name="Long")


@REGISTRY.kernel("Yellow")
def kernel_yellow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Color attribute.
    
    Patterns from dataset:
      - Bumpy(Character, car, Yellow + Broken + Sad)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was yellow.')
    if objects:
        return StoryFragment(f"the {objects[0]} was yellow", kernel_name="Yellow")
    
    return StoryFragment("yellow", kernel_name="Yellow")


@REGISTRY.kernel("Broken")
def kernel_broken(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    State of being damaged.
    
    Patterns from dataset:
      - Bumpy(Character, car, Yellow + Broken + Sad)
      - State(Bumpy, Broken(wheel=steel))
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    what = kwargs.get('what', None) or kwargs.get('wheel', None)
    
    if chars:
        chars[0].Sadness += 5
        if what:
            return StoryFragment(f"{chars[0].name}'s {_to_phrase(what)} was broken.")
        return StoryFragment(f'{chars[0].name} was broken.')
    if objects:
        return StoryFragment(f"the {objects[0]} was broken", kernel_name="Broken")
    
    return StoryFragment("broken", kernel_name="Broken")


# =============================================================================
# ACTION/INTERACTION KERNELS
# =============================================================================

@REGISTRY.kernel("Pet")
def kernel_pet(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Stroking/petting an animal.
    
    Patterns from dataset:
      - Pet(Timmy, Dog)
      - Pet(Daddy, dog)
      - Lick(face) + Pet
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        # Pet(person, animal)
        chars[0].Joy += 4
        chars[1].Joy += 5
        chars[1].Love += 3
        return StoryFragment(f'{chars[0].name} petted {chars[1].name}.')
    elif chars:
        chars[0].Joy += 4
        if objects:
            return StoryFragment(f'{chars[0].name} petted the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} petted.')
    
    return StoryFragment("petted", kernel_name="Pet")


@REGISTRY.kernel("Lick")
def kernel_lick(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Animal licking gesture, usually affectionate.
    
    Patterns from dataset:
      - Lick(face)
      - Lick(Tim, wound)
      - climax = Satisfaction(Max)+Praise(Lily,Max)+Wag(tail)+Lick(face)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Love += 3
        if objects:
            return StoryFragment(f'{chars[0].name} licked the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} licked.')
    if objects:
        return StoryFragment(f"licked the {objects[0]}", kernel_name="Lick")
    
    return StoryFragment("licked", kernel_name="Lick")


@REGISTRY.kernel("Unlock")
def kernel_unlock(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Opening a lock.
    
    Patterns from dataset:
      - Unlock(bike)
      - Unlock(room)
      - Unlock(chain)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} unlocked the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} unlocked it.')
    if objects:
        return StoryFragment(f"the {objects[0]} was unlocked", kernel_name="Unlock")
    
    return StoryFragment("unlocked", kernel_name="Unlock")


@REGISTRY.kernel("Lock")
def kernel_lock(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Securing with a lock.
    
    Patterns from dataset:
      - Lock(bike)
      - Return(home) + Lock(bike)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} locked the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} locked it.')
    if objects:
        return StoryFragment(f"the {objects[0]} was locked", kernel_name="Lock")
    
    return StoryFragment("locked", kernel_name="Lock")


@REGISTRY.kernel("Replace")
def kernel_replace(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Substituting old for new.
    
    Patterns from dataset:
      - Replace(steak, Mommy)
      - Replace(pan)
      - Repair(Bumpy, Replace(old=wheel, new=wheel))
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    old = kwargs.get('old', None)
    new = kwargs.get('new', None)
    
    if chars:
        chars[0].Joy += 3
        if old and new:
            return StoryFragment(f'{chars[0].name} replaced the {_to_phrase(old)} with a new {_to_phrase(new)}.')
        if objects:
            return StoryFragment(f'{chars[0].name} replaced the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} replaced it.')
    if objects:
        return StoryFragment(f"the {objects[0]} was replaced", kernel_name="Replace")
    
    return StoryFragment("replaced", kernel_name="Replace")


@REGISTRY.kernel("Bark")
def kernel_bark(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Dog barking.
    
    Patterns from dataset:
      - Bark(Dog)
      - backlash=Angry(Dog)+Bark(Dog)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} barked.')
    
    return StoryFragment("barked", kernel_name="Bark")


@REGISTRY.kernel("Scare")
def kernel_scare(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Frightening someone/something.
    
    Patterns from dataset:
      - Scare(Dog, snake)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        chars[1].Fear += 8
        return StoryFragment(f'{chars[0].name} scared {chars[1].name} away.')
    elif chars:
        if objects:
            return StoryFragment(f'{chars[0].name} scared the {objects[0]} away.')
        return StoryFragment(f'{chars[0].name} scared it away.')
    
    return StoryFragment("scared away", kernel_name="Scare")


@REGISTRY.kernel("Chew")
def kernel_chew(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Chewing on something.
    
    Patterns from dataset:
      - Chew(bone, subject=Max)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    subject = kwargs.get('subject', None)
    
    if subject and isinstance(subject, Character):
        subject.Joy += 4
        if objects:
            return StoryFragment(f'{subject.name} chewed on the {objects[0]}.')
        return StoryFragment(f'{subject.name} chewed happily.')
    elif chars:
        chars[0].Joy += 4
        if objects:
            return StoryFragment(f'{chars[0].name} chewed on the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} chewed.')
    elif objects:
        return StoryFragment(f"chewing on the {objects[0]}", kernel_name="Chew")
    
    return StoryFragment("chewed", kernel_name="Chew")


@REGISTRY.kernel("Wag")
def kernel_wag(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Tail wagging (dog expressing happiness).
    
    Patterns from dataset:
      - Wag(tail)
      - Wag(tail) + Lick(face)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 5
        return StoryFragment(f'{chars[0].name} wagged {chars[0].pronoun_pos} tail happily.')
    if objects:
        return StoryFragment(f"wagging the {objects[0]}", kernel_name="Wag")
    
    return StoryFragment("wagged tail happily", kernel_name="Wag")


@REGISTRY.kernel("Knock")
def kernel_knock(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Knocking on door.
    
    Patterns from dataset:
      - Knock(door)
      - Visit(Kitty, to=BuddyHouse, action=Knock(door))
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} knocked on the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} knocked on the door.')
    if objects:
        return StoryFragment(f"knocked on the {objects[0]}", kernel_name="Knock")
    
    return StoryFragment("knocked on the door", kernel_name="Knock")


@REGISTRY.kernel("Steal")
def kernel_steal(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Taking without permission.
    
    Patterns from dataset:
      - Steal(key)
      - process = Observe(dog) + Find(key, owner=Man) + Steal(key)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} stole the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} stole it.')
    if objects:
        return StoryFragment(f"the {objects[0]} was stolen", kernel_name="Steal")
    
    return StoryFragment("stolen", kernel_name="Steal")


@REGISTRY.kernel("Free")
def kernel_free(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Releasing or liberating.
    
    Patterns from dataset:
      - Free(dog)
      - Unlock(chain) + Free(dog)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 8
        chars[0].Fear -= 5
        return StoryFragment(f'{chars[0].name} was set free.')
    if objects:
        return StoryFragment(f"the {objects[0]} was set free", kernel_name="Free")
    
    return StoryFragment("set free", kernel_name="Free")


@REGISTRY.kernel("Spin")
def kernel_spin(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Turning around, spinning.
    
    Patterns from dataset:
      - Dance + Jump + Spin + Wag(tail)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} spun around.')
    
    return StoryFragment("spun around", kernel_name="Spin")


@REGISTRY.kernel("Move")
def kernel_move(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Physical movement.
    
    Patterns from dataset:
      - Move(leg)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} moved {chars[0].pronoun_pos} {objects[0]}.')
        return StoryFragment(f'{chars[0].name} moved.')
    if objects:
        return StoryFragment(f"moved the {objects[0]}", kernel_name="Move")
    
    return StoryFragment("moved", kernel_name="Move")


@REGISTRY.kernel("Approach")
def kernel_approach(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Coming closer to something/someone.
    
    Patterns from dataset:
      - Approach(dog)
      - climax = Approach(dog) + Pet(Daddy, dog)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        return StoryFragment(f'{chars[0].name} approached {chars[1].name}.')
    elif chars:
        if objects:
            return StoryFragment(f'{chars[0].name} approached the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} approached.')
    if objects:
        return StoryFragment(f"approached the {objects[0]}", kernel_name="Approach")
    
    return StoryFragment("approached", kernel_name="Approach")


@REGISTRY.kernel("Discard")
def kernel_discard(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Throwing away.
    
    Patterns from dataset:
      - Discard(key)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} threw away the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} threw it away.')
    if objects:
        return StoryFragment(f"the {objects[0]} was thrown away", kernel_name="Discard")
    
    return StoryFragment("thrown away", kernel_name="Discard")


@REGISTRY.kernel("Obtain")
def kernel_obtain(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Getting or acquiring something.
    
    Patterns from dataset:
      - Obtain(key)
      - process=Negotiation(request=key)+Obtain(key)+Unlock(room)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 4
        if objects:
            return StoryFragment(f'{chars[0].name} obtained the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} obtained it.')
    if objects:
        return StoryFragment(f"the {objects[0]} was obtained", kernel_name="Obtain")
    
    return StoryFragment("obtained", kernel_name="Obtain")


@REGISTRY.kernel("Store")
def kernel_store(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Putting away for keeping.
    
    Patterns from dataset:
      - Store(money, piggybank)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    place = kwargs.get('in', None) or kwargs.get('location', None)
    
    if chars:
        if objects and place:
            return StoryFragment(f'{chars[0].name} stored the {objects[0]} in the {_to_phrase(place)}.')
        elif objects:
            return StoryFragment(f'{chars[0].name} stored the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} stored it away.')
    if objects:
        return StoryFragment(f"the {objects[0]} was stored away", kernel_name="Store")
    
    return StoryFragment("stored", kernel_name="Store")


@REGISTRY.kernel("Count")
def kernel_count(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Counting items.
    
    Patterns from dataset:
      - Count(coin)
      - action=Count(coin) + Store(money, piggybank)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} counted the {objects[0]}s.')
        return StoryFragment(f'{chars[0].name} counted.')
    if objects:
        return StoryFragment(f"counted the {objects[0]}s", kernel_name="Count")
    
    return StoryFragment("counted", kernel_name="Count")


@REGISTRY.kernel("Taste")
def kernel_taste(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Tasting food or drink.
    
    Patterns from dataset:
      - Taste(Oranges)
      - Pick(Oranges) + Taste(Oranges) + Joy(Oranges)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 4
        if objects:
            return StoryFragment(f'{chars[0].name} tasted the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} tasted it.')
    if objects:
        return StoryFragment(f"tasted the {objects[0]}", kernel_name="Taste")
    
    return StoryFragment("tasted", kernel_name="Taste")


@REGISTRY.kernel("Cuddle")
def kernel_cuddle(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Snuggling together.
    
    Patterns from dataset:
      - Cuddle(Jojo, Mom, rest=Rest(pillow) + Warm + Cozy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        chars[0].Joy += 6
        chars[0].Love += 8
        chars[1].Joy += 6
        chars[1].Love += 8
        return StoryFragment(f'{chars[0].name} cuddled with {chars[1].name}.')
    elif chars:
        chars[0].Joy += 6
        chars[0].Love += 8
        return StoryFragment(f'{chars[0].name} cuddled up.')
    
    return StoryFragment("cuddled", kernel_name="Cuddle")


@REGISTRY.kernel("Bite")
def kernel_bite(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Biting action.
    
    Patterns from dataset:
      - Bite(Tom, Tim, ear)
      - Conflict(act=Bite(Tom,Tim,ear))
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        chars[1].Fear += 5
        chars[1].Sadness += 3
        if objects:
            return StoryFragment(f'{chars[0].name} bit {chars[1].name} on the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} bit {chars[1].name}.')
    elif chars:
        if objects:
            return StoryFragment(f'{chars[0].name} bit the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} bit.')
    
    return StoryFragment("bit", kernel_name="Bite")


@REGISTRY.kernel("Scratch")
def kernel_scratch(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Scratching action.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} scratched the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} scratched.')
    
    return StoryFragment("scratched", kernel_name="Scratch")


@REGISTRY.kernel("Sniff")
def kernel_sniff(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Smelling something.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} sniffed the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} sniffed around.')
    if objects:
        return StoryFragment(f"sniffed the {objects[0]}", kernel_name="Sniff")
    
    return StoryFragment("sniffed", kernel_name="Sniff")


@REGISTRY.kernel("Pounce")
def kernel_pounce(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Jumping on prey/target.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} pounced on {chars[1].name}.')
    elif chars:
        chars[0].Joy += 4
        if objects:
            return StoryFragment(f'{chars[0].name} pounced on the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} pounced.')
    
    return StoryFragment("pounced", kernel_name="Pounce")


@REGISTRY.kernel("Growl")
def kernel_growl(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Low threatening sound.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Anger += 4
        return StoryFragment(f'{chars[0].name} growled.')
    
    return StoryFragment("growled", kernel_name="Growl")


@REGISTRY.kernel("Purr")
def kernel_purr(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Cat purring (happiness).
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 6
        chars[0].Love += 4
        return StoryFragment(f'{chars[0].name} purred happily.')
    
    return StoryFragment("purred", kernel_name="Purr")


@REGISTRY.kernel("Meow")
def kernel_meow(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Cat vocalization.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} meowed.')
    
    return StoryFragment("meowed", kernel_name="Meow")


@REGISTRY.kernel("Chirp")
def kernel_chirp(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Bird sound.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f'{chars[0].name} chirped happily.')
    
    return StoryFragment("chirped", kernel_name="Chirp")


@REGISTRY.kernel("Hop")
def kernel_hop(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Small jumping movement.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} hopped around.')
    
    return StoryFragment("hopped", kernel_name="Hop")


@REGISTRY.kernel("Crawl")
def kernel_crawl(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Moving on hands and knees.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} crawled to the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} crawled.')
    
    return StoryFragment("crawled", kernel_name="Crawl")


@REGISTRY.kernel("Squeeze")
def kernel_squeeze(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Pressing tightly.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        chars[0].Love += 4
        return StoryFragment(f'{chars[0].name} squeezed {chars[1].name} tight.')
    elif chars:
        if objects:
            return StoryFragment(f'{chars[0].name} squeezed the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} squeezed tight.')
    
    return StoryFragment("squeezed", kernel_name="Squeeze")


@REGISTRY.kernel("Splash")
def kernel_splash(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Water splashing.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 5
        if objects:
            return StoryFragment(f'{chars[0].name} splashed in the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} splashed around.')
    
    return StoryFragment("splashed", kernel_name="Splash")


@REGISTRY.kernel("Pour")
def kernel_pour(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Pouring liquid.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} poured the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} poured.')
    if objects:
        return StoryFragment(f"poured the {objects[0]}", kernel_name="Pour")
    
    return StoryFragment("poured", kernel_name="Pour")


# =============================================================================
# STATE/CONDITION KERNELS
# =============================================================================

@REGISTRY.kernel("Hunger")
def kernel_hunger(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    State of being hungry.
    
    Patterns from dataset:
      - Hunger(Amy)
      - Hunger(Tim,Tom)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        for c in chars:
            c.Sadness += 3
        if len(chars) > 1:
            names = NLGUtils.join_list([c.name for c in chars])
            return StoryFragment(f'{names} were hungry.')
        return StoryFragment(f'{chars[0].name} was hungry.')
    
    return StoryFragment("hunger", kernel_name="Hunger")


@REGISTRY.kernel("Fatigue")
def kernel_fatigue(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being tired.
    
    Patterns from dataset:
      - process=Unlock(bike) + wear(helmet) + Ride(bike) + see(dog) + pet(dog) + Fatigue
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 2
        return StoryFragment(f'{chars[0].name} felt tired.')
    
    return StoryFragment("fatigue", kernel_name="Fatigue")


@REGISTRY.kernel("Freedom")
def kernel_freedom(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    State of being free.
    
    Patterns from dataset:
      - state=Joy + Freedom
      - transformation = Freedom(dog) + Friendship(Tom, Lily, Dog)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 8
        chars[0].Fear -= 5
        return StoryFragment(f'{chars[0].name} was free.')
    
    return StoryFragment("freedom", kernel_name="Freedom")


@REGISTRY.kernel("Satisfaction")
def kernel_satisfaction(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being satisfied.
    
    Patterns from dataset:
      - Satisfaction(Max)
      - climax = Satisfaction(Max)+Praise(Lily,Max)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 7
        return StoryFragment(f'{chars[0].name} felt satisfied.')
    
    return StoryFragment("satisfaction", kernel_name="Satisfaction")


@REGISTRY.kernel("Loneliness")
def kernel_loneliness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being alone.
    
    Patterns from dataset:
      - Loneliness(Tim,Tom)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        for c in chars:
            c.Sadness += 8
        if len(chars) > 1:
            names = NLGUtils.join_list([c.name for c in chars])
            return StoryFragment(f'{names} felt lonely.')
        return StoryFragment(f'{chars[0].name} felt lonely.')
    
    return StoryFragment("loneliness", kernel_name="Loneliness")


@REGISTRY.kernel("Illness")
def kernel_illness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being sick.
    
    Patterns from dataset:
      - Illness(Tom,cause=BadFood)
    """
    chars = [a for a in args if isinstance(a, Character)]
    cause = kwargs.get('cause', None)
    
    if chars:
        chars[0].Sadness += 6
        if cause:
            return StoryFragment(f'{chars[0].name} got sick from {_to_phrase(cause)}.')
        return StoryFragment(f'{chars[0].name} got sick.')
    
    return StoryFragment("illness", kernel_name="Illness")


@REGISTRY.kernel("Sickness")
def kernel_sickness(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    State of illness.
    
    Patterns from dataset:
      - Sickness(Tom)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Sadness += 6
        return StoryFragment(f'{chars[0].name} was sick.')
    
    return StoryFragment("sickness", kernel_name="Sickness")


@REGISTRY.kernel("Courage")
def kernel_courage(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Having bravery.
    
    Patterns from dataset:
      - Courage(Girl)
      - transformation = Trust(Girl, Daddy) + Courage(Girl)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear -= 6
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} felt brave.')
    
    return StoryFragment("courage", kernel_name="Courage")


@REGISTRY.kernel("Gluttony")
def kernel_gluttony(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Excessive eating.
    
    Patterns from dataset:
      - Gluttony(Tom,food=meat)
    """
    chars = [a for a in args if isinstance(a, Character)]
    food = kwargs.get('food', None)
    
    if chars:
        chars[0].Joy += 3
        if food:
            return StoryFragment(f'{chars[0].name} ate all the {_to_phrase(food)}.')
        return StoryFragment(f'{chars[0].name} ate too much.')
    
    return StoryFragment("gluttony", kernel_name="Gluttony")


@REGISTRY.kernel("Effort")
def kernel_effort(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Trying hard.
    
    Patterns from dataset:
      - initial=Clumsy / 5 + Effort
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} put in a lot of effort.')
    
    return StoryFragment("effort", kernel_name="Effort")


@REGISTRY.kernel("Confidence")
def kernel_confidence(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Self-assurance.
    
    Patterns from dataset:
      - improvement=SkillIncrease + Confidence
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 5
        chars[0].Fear -= 3
        return StoryFragment(f'{chars[0].name} felt confident.')
    
    return StoryFragment("confidence", kernel_name="Confidence")


@REGISTRY.kernel("Safe")
def kernel_safe(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being secure.
    
    Patterns from dataset:
      - Helmet(safe)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear -= 5
        chars[0].Joy += 3
        return StoryFragment(f'{chars[0].name} was safe.')
    
    return StoryFragment("safe", kernel_name="Safe")


@REGISTRY.kernel("Cozy")
def kernel_cozy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Comfortable and warm.
    
    Patterns from dataset:
      - rest=Rest(pillow) + Warm + Cozy
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 6
        chars[0].Love += 4
        return StoryFragment(f'{chars[0].name} felt cozy.')
    
    return StoryFragment("cozy", kernel_name="Cozy")


@REGISTRY.kernel("Messy")
def kernel_messy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    State of disorder.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} was messy.')
    if objects:
        return StoryFragment(f"the {objects[0]} was messy", kernel_name="Messy")
    
    return StoryFragment("messy", kernel_name="Messy")


# =============================================================================
# STRUCTURAL/NARRATIVE KERNELS
# =============================================================================

@REGISTRY.kernel("Collaboration")
def kernel_collaboration(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Working together on a task.
    
    Patterns from dataset:
      - Collaboration(Timmy, Billy, activity=Build(castle, material=clay) + Play(clay))
    """
    chars = [a for a in args if isinstance(a, Character)]
    activity = kwargs.get('activity', None)
    
    if len(chars) >= 2:
        for c in chars:
            c.Joy += 5
            c.Love += 3
        names = NLGUtils.join_list([c.name for c in chars])
        if activity:
            return StoryFragment(f'{names} worked together on {_to_phrase(activity)}.')
        return StoryFragment(f'{names} worked together.')
    elif chars:
        chars[0].Joy += 4
        return StoryFragment(f'{chars[0].name} collaborated.')
    
    return StoryFragment("collaboration", kernel_name="Collaboration")


@REGISTRY.kernel("Bonding")
def kernel_bonding(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Forming emotional connection.
    
    Patterns from dataset:
      - Bonding(Lily, Max, state = Routine+Gift(bone), ...)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        for c in chars:
            c.Love += 8
            c.Joy += 5
        return StoryFragment(f'{chars[0].name} and {chars[1].name} bonded.')
    elif chars:
        chars[0].Love += 6
        return StoryFragment(f'{chars[0].name} felt a bond.')
    
    return StoryFragment("bonding", kernel_name="Bonding")


@REGISTRY.kernel("Companion")
def kernel_companion(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being a companion.
    
    Patterns from dataset:
      - Companion(Timmy, Dog, woods)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if len(chars) >= 2:
        chars[0].Love += 5
        chars[1].Love += 5
        if objects:
            return StoryFragment(f'{chars[0].name} and {chars[1].name} went to the {objects[0]} together.')
        return StoryFragment(f'{chars[0].name} and {chars[1].name} became companions.')
    elif chars:
        return StoryFragment(f'{chars[0].name} was a loyal companion.')
    
    return StoryFragment("companion", kernel_name="Companion")


@REGISTRY.kernel("Vacation")
def kernel_vacation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Holiday or trip.
    
    Patterns from dataset:
      - desire=Vacation
      - outcome=Joy + Contribution(Family, Vacation)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 8
        return StoryFragment(f'{chars[0].name} went on vacation.')
    
    return StoryFragment("vacation", kernel_name="Vacation")


@REGISTRY.kernel("Permission")
def kernel_permission(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Being allowed to do something.
    
    Patterns from dataset:
      - catalyst=Permission(Mom)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 4
        if objects:
            return StoryFragment(f'{chars[0].name} gave permission for {objects[0]}.')
        return StoryFragment(f'{chars[0].name} gave permission.')
    
    return StoryFragment("permission was given", kernel_name="Permission")


@REGISTRY.kernel("Restriction")
def kernel_restriction(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    A limitation or rule.
    
    Patterns from dataset:
      - state=Routine(play=car) + Restriction(noOutside)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Sadness += 2
        if objects:
            return StoryFragment(f'{chars[0].name} was not allowed {objects[0]}.')
        return StoryFragment(f'{chars[0].name} had restrictions.')
    if objects:
        return StoryFragment(f"there was a restriction on {objects[0]}", kernel_name="Restriction")
    
    return StoryFragment("restriction", kernel_name="Restriction")


@REGISTRY.kernel("Contribution")
def kernel_contribution(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Adding to something, helping out.
    
    Patterns from dataset:
      - outcome=Joy + Contribution(Family, Vacation)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 5
        chars[0].Love += 3
        if objects:
            return StoryFragment(f'{chars[0].name} contributed to the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} made a contribution.')
    if objects:
        return StoryFragment(f"contributed to the {objects[0]}", kernel_name="Contribution")
    
    return StoryFragment("contribution", kernel_name="Contribution")


@REGISTRY.kernel("SaveMoney")
def kernel_save_money(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Financial saving.
    
    Patterns from dataset:
      - obstacle=WorkHard + SaveMoney
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} saved money.')
    
    return StoryFragment("saving money", kernel_name="SaveMoney")


# =============================================================================
# ADDITIONAL ACTION KERNELS
# =============================================================================

@REGISTRY.kernel("Negotiation")
def kernel_negotiation(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Negotiating or bargaining.
    
    Patterns from dataset:
      - process=Negotiation(request=key)+Obtain(key)
    """
    chars = [a for a in args if isinstance(a, Character)]
    request = kwargs.get('request', None)
    
    if chars:
        if request:
            return StoryFragment(f'{chars[0].name} negotiated for the {_to_phrase(request)}.')
        return StoryFragment(f'{chars[0].name} negotiated.')
    if request:
        return StoryFragment(f"negotiated for the {_to_phrase(request)}", kernel_name="Negotiation")
    
    return StoryFragment("negotiation", kernel_name="Negotiation")


@REGISTRY.kernel("SelfCare")
def kernel_self_care(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Taking care of oneself.
    
    Patterns from dataset:
      - action=SelfCare(wash(face) + brush(teeth) + Cry)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f'{chars[0].name} took care of themselves.')
    
    return StoryFragment("self-care", kernel_name="SelfCare")


@REGISTRY.kernel("Bury")
def kernel_bury(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Burying something in ground.
    
    Patterns from dataset:
      - Bury(Spot, item=License, place=under(tree))
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    item = kwargs.get('item', None)
    place = kwargs.get('place', None)
    
    if chars:
        thing = item or (objects[0] if objects else 'it')
        if place:
            return StoryFragment(f'{chars[0].name} buried the {_to_phrase(thing)} {_to_phrase(place)}.')
        return StoryFragment(f'{chars[0].name} buried the {_to_phrase(thing)}.')
    
    return StoryFragment("buried", kernel_name="Bury")


@REGISTRY.kernel("Retrieve")
def kernel_retrieve(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Getting something back.
    
    Patterns from dataset:
      - Retrieve(Spot, item=License)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    item = kwargs.get('item', None)
    
    if chars:
        thing = item or (objects[0] if objects else 'it')
        return StoryFragment(f'{chars[0].name} retrieved the {_to_phrase(thing)}.')
    
    return StoryFragment("retrieved", kernel_name="Retrieve")


@REGISTRY.kernel("Sprinkler")
def kernel_sprinkler(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Sprinkler activity (water play).
    
    Patterns from dataset:
      - process = Play + Sprinkler(water, Butterfly)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 6
        return StoryFragment(f'{chars[0].name} played in the sprinkler.')
    if objects:
        return StoryFragment(f"the sprinkler sprayed {objects[0]}", kernel_name="Sprinkler")
    
    return StoryFragment("sprinkler", kernel_name="Sprinkler")


@REGISTRY.kernel("Sunset")
def kernel_sunset(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Sun setting, end of day.
    
    Patterns from dataset:
      - transition = Sunset
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 3
        return StoryFragment(f'{chars[0].name} watched the sunset.')
    
    return StoryFragment("the sun set", kernel_name="Sunset")


@REGISTRY.kernel("Collapse")
def kernel_collapse(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something falling down/collapsing.
    
    Patterns from dataset:
      - Wind + Collapse(castle)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Sadness += 5
        return StoryFragment(f'{chars[0].name} collapsed.')
    if objects:
        return StoryFragment(f"the {objects[0]} collapsed", kernel_name="Collapse")
    
    return StoryFragment("collapsed", kernel_name="Collapse")


@REGISTRY.kernel("Owner")
def kernel_owner(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Owner of something (often a pet owner character).
    
    Patterns from dataset:
      - Owner(Character, human, Unaware + Observant)
      - request=Ask(Owner,pet)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} was the owner of the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} was the owner.')
    
    return StoryFragment("owner", kernel_name="Owner")


@REGISTRY.kernel("WorkHard")
def kernel_work_hard(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Working hard on something.
    
    Patterns from dataset:
      - obstacle=WorkHard + SaveMoney
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} worked hard.')
    
    return StoryFragment("working hard", kernel_name="WorkHard")


@REGISTRY.kernel("Theft")
def kernel_theft(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Something being stolen.
    
    Patterns from dataset:
      - process=PlayOutside(car) + Theft(Dog, car)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} stole the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} stole something.')
    if objects:
        return StoryFragment(f"the {objects[0]} was stolen", kernel_name="Theft")
    
    return StoryFragment("theft", kernel_name="Theft")


@REGISTRY.kernel("PlayOutside")
def kernel_play_outside(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Playing outside.
    
    Patterns from dataset:
      - process=PlayOutside(car)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 6
        if objects:
            return StoryFragment(f'{chars[0].name} played outside with the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} played outside.')
    if objects:
        return StoryFragment(f"playing outside with the {objects[0]}", kernel_name="PlayOutside")
    
    return StoryFragment("playing outside", kernel_name="PlayOutside")


@REGISTRY.kernel("Fire")
def kernel_fire(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Fire or firing something.
    
    Patterns from dataset:
      - Fire(pistol)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Fear += 4
        if objects:
            return StoryFragment(f'{chars[0].name} fired the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} fired.')
    if objects:
        return StoryFragment(f"fired the {objects[0]}", kernel_name="Fire")
    
    return StoryFragment("fire", kernel_name="Fire")


@REGISTRY.kernel("PretendShoot")
def kernel_pretend_shoot(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Pretending to shoot.
    
    Patterns from dataset:
      - process=Find(pistol)+Show(pistol)+Point(pistol)+PretendShoot+Fire(pistol)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} pretended to shoot.')
    
    return StoryFragment("pretend shoot", kernel_name="PretendShoot")


@REGISTRY.kernel("Life")
def kernel_life(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Life as concept.
    
    Patterns from dataset:
      - Loss(Billy,Life)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f"{chars[0].name}'s life")
    
    return StoryFragment("life", kernel_name="Life")


@REGISTRY.kernel("Intrusion")
def kernel_intrusion(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Unwanted entry.
    
    Patterns from dataset:
      - cause=Intrusion(Fox,location=barn)
    """
    chars = [a for a in args if isinstance(a, Character)]
    location = kwargs.get('location', None)
    
    if chars:
        if location:
            return StoryFragment(f'{chars[0].name} intruded into the {_to_phrase(location)}.')
        return StoryFragment(f'{chars[0].name} intruded.')
    
    return StoryFragment("intrusion", kernel_name="Intrusion")


@REGISTRY.kernel("EatTogether")
def kernel_eat_together(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Eating together.
    
    Patterns from dataset:
      - EatTogether(Amy, Mommy, MrFluffy)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if len(chars) >= 2:
        for c in chars:
            c.Joy += 5
            c.Love += 3
        names = NLGUtils.join_list([c.name for c in chars])
        return StoryFragment(f'{names} ate together.')
    elif chars:
        return StoryFragment(f'{chars[0].name} ate.')
    
    return StoryFragment("ate together", kernel_name="EatTogether")


@REGISTRY.kernel("Value")
def kernel_value(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Appreciating value of something.
    
    Patterns from dataset:
      - insight = Value(Helmet)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 3
        if objects:
            return StoryFragment(f'{chars[0].name} valued the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} found value.')
    if objects:
        return StoryFragment(f"valued the {objects[0]}", kernel_name="Value")
    
    return StoryFragment("value", kernel_name="Value")


@REGISTRY.kernel("Helmet")
def kernel_helmet(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Helmet wearing or safety.
    
    Patterns from dataset:
      - Helmet(safe)
      - Conflict(Helmet)
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects and objects[0].lower() == 'safe':
            return StoryFragment(f"{chars[0].name}'s helmet kept them safe.")
        return StoryFragment(f'{chars[0].name} wore a helmet.')
    if objects:
        return StoryFragment(f"helmet was {objects[0]}", kernel_name="Helmet")
    
    return StoryFragment("helmet", kernel_name="Helmet")


@REGISTRY.kernel("SafetyLesson")
def kernel_safety_lesson(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Learning a safety lesson.
    
    Patterns from dataset:
      - SafetyLesson(Tim, state = ..., catalyst = ..., process = ...)
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Fear += 2
        return StoryFragment(f'{chars[0].name} learned an important safety lesson.')
    
    return StoryFragment("safety lesson", kernel_name="SafetyLesson")


@REGISTRY.kernel("TeachProcess")
def kernel_teach_process(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Process of teaching.
    
    Patterns from dataset:
      - TeachProcess(participants=[Kitty, Buddy], location=yard, ...)
    """
    participants = kwargs.get('participants', [])
    location = kwargs.get('location', None)
    
    if participants and len(participants) >= 2:
        teacher = participants[0]
        student = participants[1]
        if isinstance(teacher, Character) and isinstance(student, Character):
            teacher.Joy += 4
            student.Joy += 5
            if location:
                return StoryFragment(f'{teacher.name} taught {student.name} in the {_to_phrase(location)}.')
            return StoryFragment(f'{teacher.name} taught {student.name}.')
    
    return StoryFragment("teaching process", kernel_name="TeachProcess")


@REGISTRY.kernel("SkillIncrease")
def kernel_skill_increase(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Getting better at a skill.
    
    Patterns from dataset:
      - improvement=SkillIncrease + Confidence
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 6
        return StoryFragment(f'{chars[0].name} got better at it.')
    
    return StoryFragment("skill increased", kernel_name="SkillIncrease")


@REGISTRY.kernel("FriendshipRide")
def kernel_friendship_ride(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Friends riding together.
    
    Patterns from dataset:
      - FriendshipRide(participants=[Lucy, Tom], state=Joy + Freedom, ...)
    """
    participants = kwargs.get('participants', [])
    chars = [a for a in args if isinstance(a, Character)]
    
    all_chars = participants if participants else chars
    if all_chars:
        for c in all_chars:
            if isinstance(c, Character):
                c.Joy += 6
        if len(all_chars) >= 2:
            names = NLGUtils.join_list([c.name for c in all_chars if isinstance(c, Character)])
            return StoryFragment(f'{names} went for a ride together.')
    
    return StoryFragment("friendship ride", kernel_name="FriendshipRide")


@REGISTRY.kernel("RespectfulPlay")
def kernel_respectful_play(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Playing respectfully - asking permission, being polite.
    
    Patterns from dataset:
      - RespectfulPlay(Lily+Tom, trigger=Dog(friendly,owner=Owner), request=Ask(Owner,pet), outcome=...)
    """
    chars = [a for a in args if isinstance(a, Character)]
    parts = []
    
    # Get character names
    if chars:
        for c in chars:
            c.Joy += 5
        names = NLGUtils.join_list([c.name for c in chars]) if len(chars) >= 2 else chars[0].name
    else:
        names = "They"
    
    # Trigger - what prompted the play
    if 'trigger' in kwargs:
        trigger = kwargs['trigger']
        trigger_text = _event_to_phrase(trigger)
        if trigger_text:
            parts.append(f"Then, {trigger_text}.")
    
    # Request - asking permission
    if 'request' in kwargs:
        request = kwargs['request']
        request_text = _action_to_phrase(request)
        if request_text:
            parts.append(f"{names} politely {request_text}.")
    
    # Outcome - what happened
    if 'outcome' in kwargs:
        outcome = kwargs['outcome']
        outcome_text = _event_to_phrase(outcome)
        if outcome_text:
            parts.append(f"{outcome_text.capitalize()}.")
    
    # Default text if no kwargs
    if not parts:
        parts.append(f"{names} played together nicely and respectfully.")
    
    return StoryFragment(' '.join(parts), kernel_name="RespectfulPlay")


@REGISTRY.kernel("NoPointing")
def kernel_no_pointing(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Lesson about not pointing at things/people.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        return StoryFragment(f'{chars[0].name} learned not to point.')
    
    return StoryFragment("It's not nice to point.", kernel_name="NoPointing")


@REGISTRY.kernel("Cool")
def kernel_cool(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Cooling something down.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        if objects:
            return StoryFragment(f'{chars[0].name} cooled down the {objects[0]}.')
        return StoryFragment(f'{chars[0].name} cooled it down.')
    if objects:
        return StoryFragment(f"The {objects[0]} cooled down.", kernel_name="Cool")
    
    return StoryFragment("It cooled down.", kernel_name="Cool")


@REGISTRY.kernel("Dinner")
def kernel_dinner(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Having dinner.
    """
    chars = [a for a in args if isinstance(a, Character)]
    objects = [str(a) for a in args if isinstance(a, str)]
    
    if chars:
        chars[0].Joy += 4
        if objects:
            return StoryFragment(f'{chars[0].name} had {objects[0]} for dinner.')
        return StoryFragment(f'{chars[0].name} had dinner.')
    if objects:
        return StoryFragment(f"It was time for dinner with {objects[0]}.", kernel_name="Dinner")
    
    return StoryFragment("It was time for dinner.", kernel_name="Dinner")


@REGISTRY.kernel("Hotchocolate")
def kernel_hot_chocolate(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """
    Drinking hot chocolate.
    """
    chars = [a for a in args if isinstance(a, Character)]
    
    if chars:
        chars[0].Joy += 6
        return StoryFragment(f'{chars[0].name} drank some warm hot chocolate.')
    
    return StoryFragment("They had some warm hot chocolate.", kernel_name="Hotchocolate")


# =============================================================================
# CHARACTER NAME KERNELS
# These are common character names used as shorthand for Character(name, ...)
# =============================================================================

def _make_character_name_kernel(name: str, default_type: str = "character"):
    """Factory to create character name kernels."""
    def kernel_func(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
        # Check if character already exists
        if name in ctx.characters:
            char = ctx.characters[name]
            ctx.current_focus = char
            # If there are additional args, treat as action
            objects = [str(a) for a in args if isinstance(a, str)]
            if objects:
                return StoryFragment(f'{char.name} {" ".join(objects)}.')
            return StoryFragment("")  # Character already introduced
        
        # Create new character
        char = Character(name=name)
        ctx.characters[name] = char
        ctx.current_focus = char
        
        # Handle traits from args
        traits = []
        for a in args:
            if isinstance(a, str) and a not in ["Character", "boy", "girl", "child", "adult"]:
                traits.append(a)
        
        if traits:
            return StoryFragment(f"There was a {default_type} named {name}.")
        return StoryFragment(f"There was a {default_type} named {name}.")
    
    return kernel_func


# Common boy names
@REGISTRY.kernel("Timmy")
def kernel_timmy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Timmy - common boy character name."""
    return _make_character_name_kernel("Timmy", "boy")(ctx, *args, **kwargs)

@REGISTRY.kernel("Billy")
def kernel_billy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Billy - common boy character name."""
    return _make_character_name_kernel("Billy", "boy")(ctx, *args, **kwargs)

@REGISTRY.kernel("Tommy")
def kernel_tommy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Tommy - common boy character name."""
    return _make_character_name_kernel("Tommy", "boy")(ctx, *args, **kwargs)

@REGISTRY.kernel("Sam")
def kernel_sam(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sam - common character name."""
    return _make_character_name_kernel("Sam", "child")(ctx, *args, **kwargs)

@REGISTRY.kernel("Max")
def kernel_max(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Max - common character/pet name."""
    return _make_character_name_kernel("Max", "friend")(ctx, *args, **kwargs)

@REGISTRY.kernel("Ben")
def kernel_ben(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Ben - common boy character name."""
    return _make_character_name_kernel("Ben", "boy")(ctx, *args, **kwargs)

@REGISTRY.kernel("Jack")
def kernel_jack(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Jack - common boy character name."""
    return _make_character_name_kernel("Jack", "boy")(ctx, *args, **kwargs)

@REGISTRY.kernel("Tom")
def kernel_tom(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Tom - common boy character name."""
    return _make_character_name_kernel("Tom", "boy")(ctx, *args, **kwargs)

# Common girl names
@REGISTRY.kernel("Lily")
def kernel_lily(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Lily - common girl character name."""
    return _make_character_name_kernel("Lily", "girl")(ctx, *args, **kwargs)

@REGISTRY.kernel("Lucy")
def kernel_lucy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Lucy - common girl character name."""
    return _make_character_name_kernel("Lucy", "girl")(ctx, *args, **kwargs)

@REGISTRY.kernel("Amy")
def kernel_amy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Amy - common girl character name."""
    return _make_character_name_kernel("Amy", "girl")(ctx, *args, **kwargs)

@REGISTRY.kernel("Emma")
def kernel_emma(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Emma - common girl character name."""
    return _make_character_name_kernel("Emma", "girl")(ctx, *args, **kwargs)

@REGISTRY.kernel("Sara")
def kernel_sara(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sara - common girl character name."""
    return _make_character_name_kernel("Sara", "girl")(ctx, *args, **kwargs)

@REGISTRY.kernel("Anna")
def kernel_anna(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Anna - common girl character name."""
    return _make_character_name_kernel("Anna", "girl")(ctx, *args, **kwargs)

@REGISTRY.kernel("Sue")
def kernel_sue(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Sue - common girl character name."""
    return _make_character_name_kernel("Sue", "girl")(ctx, *args, **kwargs)

@REGISTRY.kernel("Kitty")
def kernel_kitty(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Kitty - common girl/cat character name."""
    return _make_character_name_kernel("Kitty", "cat")(ctx, *args, **kwargs)

@REGISTRY.kernel("Rosie")
def kernel_rosie(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Rosie - common girl character name."""
    return _make_character_name_kernel("Rosie", "girl")(ctx, *args, **kwargs)

@REGISTRY.kernel("Buddy")
def kernel_buddy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Buddy - common pet/friend character name."""
    return _make_character_name_kernel("Buddy", "friend")(ctx, *args, **kwargs)

@REGISTRY.kernel("Spot")
def kernel_spot(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Spot - common dog character name."""
    return _make_character_name_kernel("Spot", "dog")(ctx, *args, **kwargs)

# Family role names
@REGISTRY.kernel("Mom")
def kernel_mom(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Mom - mother character."""
    return _make_character_name_kernel("Mom", "mother")(ctx, *args, **kwargs)

@REGISTRY.kernel("Mommy")
def kernel_mommy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Mommy - mother character."""
    return _make_character_name_kernel("Mommy", "mommy")(ctx, *args, **kwargs)

@REGISTRY.kernel("Dad")
def kernel_dad(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Dad - father character."""
    return _make_character_name_kernel("Dad", "father")(ctx, *args, **kwargs)

@REGISTRY.kernel("Daddy")
def kernel_daddy(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Daddy - father character."""
    return _make_character_name_kernel("Daddy", "daddy")(ctx, *args, **kwargs)

@REGISTRY.kernel("Grandma")
def kernel_grandma(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Grandma - grandmother character."""
    return _make_character_name_kernel("Grandma", "grandmother")(ctx, *args, **kwargs)

@REGISTRY.kernel("Grandpa")
def kernel_grandpa(ctx: StoryContext, *args, **kwargs) -> StoryFragment:
    """Grandpa - grandfather character."""
    return _make_character_name_kernel("Grandpa", "grandfather")(ctx, *args, **kwargs)


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == "__main__":
    print("gen5k06.py - Additional Kernel Pack #06")
    print("=" * 50)
    print(f"Total kernels in registry: {len(REGISTRY.kernels)}")
    
    # List kernels from this pack
    pack_kernels = [
        "Cautious", "Hungry", "Eager", "Mischievous", "Warm", "Learner",
        "Fearful", "Stubborn", "Attached", "Resourceful", "Imaginative",
        "Encouraging", "Compassion", "Impatient", "Hardworking", "Strict",
        "Trusting", "Energetic", "Reckless", "Alert", "Permissive", "Guiding",
        "Absent", "Observant", "Dreamy", "Long", "Yellow", "Broken",
        "Pet", "Lick", "Unlock", "Lock", "Replace", "Bark", "Scare", "Chew",
        "Wag", "Knock", "Steal", "Free", "Spin", "Move", "Approach", "Discard",
        "Obtain", "Store", "Count", "Pick", "Taste", "Cuddle", "Bite",
        "Scratch", "Sniff", "Pounce", "Growl", "Purr", "Meow", "Chirp",
        "Hop", "Crawl", "Squeeze", "Splash", "Pour", "Hunger", "Fatigue",
        "Freedom", "Satisfaction", "Loneliness", "Illness", "Sickness",
        "Courage", "Gluttony", "Pride", "Effort", "Confidence", "Safe",
        "Cozy", "Messy", "Collaboration", "Bonding", "Companion", "Vacation",
        "Permission", "Restriction", "Contribution", "SaveMoney", "Negotiation",
        "SelfCare", "Bury", "Retrieve", "Sprinkler", "Sunset", "Collapse",
        "Owner", "WorkHard", "Theft", "PlayOutside", "Fire", "PretendShoot",
        "Life", "Intrusion", "EatTogether", "Value", "Helmet", "SafetyLesson",
        "TeachProcess", "SkillIncrease", "FriendshipRide", "RespectfulPlay",
        # Character names
        "Timmy", "Billy", "Tommy", "Sam", "Max", "Ben", "Jack",
        "Lily", "Lucy", "Amy", "Emma", "Sara", "Anna", "Sue",
        "Mom", "Mommy", "Dad", "Daddy", "Grandma", "Grandpa"
    ]
    
    implemented = sum(1 for k in pack_kernels if k in REGISTRY.kernels)
    print(f"Kernels defined in this pack: {len(pack_kernels)}")
    print(f"Successfully registered: {implemented}")
    
    # Show sample kernels
    print("\nSample kernels from this pack:")
    for kernel_name in ["Cautious", "Pet", "Freedom", "Collaboration"][:4]:
        if kernel_name in REGISTRY.kernels:
            print(f"  ✓ {kernel_name}")

