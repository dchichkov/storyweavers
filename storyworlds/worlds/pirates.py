#!/usr/bin/env python3
"""
storyworlds/worlds/pirates.py
=============================

A standalone *story world* sketch for "The Pirates and the Forbidden Spark" and
close, *constraint-checked* variations of it. Typed entities with accumulating 
physical *meters* and emotional *memes*, a forward-chaining causal rule engine, 
a predict-then-warn beat, a reasonableness gate, and a state-driven renderer).

Initial story (used to build a world model):
---
The Pirates and the Forbidden Spark

Lily and Tom turned the living room into a wild island. The sofa was their
pirate ship, a broom became a sword, an old shoebox held their treasure, and
a crayon map showed the way to the gold.

"Captain Tom and Explorer Lily!" Tom shouted. "Let's find the treasure cave!"

But the cave - the space under the big table, behind the long dark curtains
- was dark. Very dark.

"We need a light," said Lily.

Tom's eyes lit up. "I know! Matches! I saw a box in the kitchen drawer."

Lily bit her lip. "Tom, we're not allowed to touch matches. Mom said."

"Don't be such a scaredy-cat," Tom said, and ran to get them.

Scritch! The first match flared to life. For one second it was wonderful -- a
tiny golden flame, just like a real lantern. Then the flame leaned, kissed the
bottom of the curtain, and a little line of orange began to climb.

"Tom!" Lily screamed. "Fire! The curtain!"

"MOM!"

Mom came running. In a flash she grabbed the bucket from the cleaning closet,
filled it at the sink, and threw the water -- whoosh -- right over the curtain.
The flame hissed and died, leaving only a wet, smoky smell and two very
frightened pirates.

For a moment, nobody spoke.

Then Mom knelt down and hugged them both. "I'm not angry that you're scared,"
she said softly. "I'm glad you called me. But you must always remember:
matches are not toys. Fire can grow faster than you can run. Promise me --
never, ever again."

"We promise," whispered Lily and Tom together.

The next day, Mom had a surprise. She handed them a flashlight that clicked on
bright as a star, and a little camping lantern that glowed warm and safe.

"Now," she smiled, "what does a pirate need to explore a dark cave?"

Tom held up the lantern. Lily clicked on the flashlight.

"Safe light!" they cheered.

And the pirates sailed off to find their treasure -- bright, brave, and safe.

Causal state updates:
---
    forbidden flame near target  -> target.burning += 1
                                    target.scorched += 1
    something burning            -> room.danger += 1
                                    each child.fear += 1

Scripted social/emotional beats:
---
    pretend-play setup           -> each child.joy += 1
    forbidden shortcut suggested -> instigator.bravado += 1
    warning given                -> cautioner.caution += 1
    warning ignored              -> instigator.defiance += 1
    older cautioner overrules    -> instigator.bravery -> 0
                                    both children.relief += 1
    rescue succeeds              -> target.burning -> 0 ; room.danger -> 0
    lesson accepted              -> both children.relief/love/lesson += 1
                                    both children.fear -> 0
    safe lights adopted          -> both children.joy/safety += 1
    rescue fails                 -> room.burning += 1 ; fear keeps rising
    grim lesson accepted         -> both children.relief/love/lesson += 1

"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# (``python storyworlds/worlds/pirates.py``): add the package dir (storyworlds/)
# to the path so ``results`` resolves regardless of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# A response below this common-sense score is *known to the world but refused*:
# the model prefers smarter, safer alternatives (see the note above RESPONSES).
SENSE_MIN = 2

# Initial "nerve" of the instigator, and which traits make a cautious cautioner.
# Used to decide whether the cautioner can talk the instigator out of it.
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, mother, father, tool, target, room
    label: str = ""                # short reference, e.g. "curtain", "the parent"
    traits: list[str] = field(default_factory=list)
    role: str = ""                 # "instigator" | "cautioner" | "parent"
    age: int = 0                   # background fact -- never stated, only branched on
    attrs: dict = field(default_factory=dict)  # relation, comfort toy, school, ...
    flammable: bool = False        # can this object catch fire?
    makes_flame: bool = False      # is this a flame source (forbidden tool)?
    gives_light: bool = False      # safe light substitute?
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Theme:
    """The pretend-play frame the children build in the living room."""
    id: str
    scene: str           # "a wild island"
    rig: str             # the full "the sofa was..." sentence of props
    captain: str         # title for the instigator: "Captain"
    mate: str            # title for the cautioner: "Explorer"
    goal: str            # "the treasure cave"
    dark_spot: str       # "the space under the big table"
    cave_word: str       # "cave"
    role_solo: str       # "a pirate"
    role_plural: str     # "pirates"
    send_off: str        # "sailed off to find their treasure"


@dataclass
class Forbidden:
    """A flame-making tool the children are not allowed to touch."""
    id: str
    cry: str             # the excited shout: "Matches!"
    label: str           # how it's referred to: "matches" / "the lighter"
    phrase: str          # "a box of matches"
    where: str           # "in the kitchen drawer"
    unit: str            # the thing that flares: "the first match"
    strike: str          # onomatopoeia: "Scritch!"
    not_toy: str         # the lesson clause: "matches are not toys"
    plural: bool = True
    makes_flame: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Flammable:
    """The thing near the dark spot that catches fire."""
    id: str
    label: str           # "curtain"
    the: str             # "the curtain"
    near: str            # where the flame touches: "the bottom of the curtain"
    drape: str           # how it dresses the dark spot: "hung with long dark curtains"
    spread: int = 2      # how fast/fierce a fire it makes (curtains burn fastest)
    flammable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class SafeLight:
    """A battery light that meets the same need (light) without a flame."""
    id: str
    label: str           # "flashlight"
    phrase: str          # "a flashlight"
    glow: str            # "clicked on bright as a star"
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    """An adult way to put the fire out, ranked by common sense and power."""
    id: str
    sense: int           # higher = safer / smarter; below SENSE_MIN it is refused
    power: int           # how big a fire it can actually put out (vs fire severity)
    text: str            # success narration body, may contain "{target}"
    fail: str            # failure narration body, may contain "{target}"
    qa_text: str         # clean past-tense success phrase for Q&A, may contain "{target}"
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}                # read back by the Q&A generators

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

    # -- narration helpers --------------------------------------------------
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]            # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spread(world: World) -> list[str]:
    """Something burning -> the room gets dangerous and the children get scared."""
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__fire__")              # marker; narrated by the screenplay beat
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spread", tag="physical", apply=_r_spread),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* hazard and a *sensible* response.
# ---------------------------------------------------------------------------
def hazard_at_risk(forbidden: Forbidden, target: Flammable) -> bool:
    """Would using this tool near this target actually start a fire?"""
    return forbidden.makes_flame and target.flammable


def sensible_responses() -> list[Response]:
    """The adult responses we are willing to put in a story (common-sense gate)."""
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def fire_severity(target: Flammable, delay: int) -> int:
    """How fierce the fire is: a fast-burning target plus the head start it got
    before a grown-up arrived (delay).  This is what a response must overpower."""
    return target.spread + delay


def is_contained(response: Response, target: Flammable, delay: int) -> bool:
    """Did the method actually beat the fire?  If not, the place burns down --
    even a sensible response can be too late once the fire is big enough."""
    return response.power >= fire_severity(target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int,
                trait: str) -> bool:
    """Does the cautioner talk the instigator out of it, so *no fire happens*?

    Happens when the cautioner is the older sibling: a big brother/sister carries
    enough weight (their caution plus the warning beat) to overrule the
    instigator's nerve.  This is the "near-miss" / averted outcome."""
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    # +1 mirrors the caution the warning beat adds before the decision.
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


# ---------------------------------------------------------------------------
# Prediction: the cautioner runs the world model forward on a copy to foresee
# the danger before speaking (mirrors the parent's prediction in puddles.py).
# ---------------------------------------------------------------------------
def predict_fire(world: World, target_id: str) -> dict:
    """Simulate lighting the flame near the target silently; report the danger."""
    sim = world.copy()
    _do_forbidden(sim, sim.get(target_id), narrate=False)
    return {
        "ignites": sim.get(target_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def _do_forbidden(world: World, target: Entity, narrate: bool = True) -> None:
    """The accident: the flame catches the target, fire spreads."""
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {a.id} and {b.id} turned the living room into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} shouted. '
        f'"Let\'s find {theme.goal}!"'
    )


def need_light(world: World, b: Entity, theme: Theme, target: Flammable) -> None:
    world.say(
        f"But the {theme.cave_word} -- {theme.dark_spot}, {target.drape} -- "
        f"swallowed the light from the window."
    )
    world.say(f'{b.id} peered inside. "We need a light," {b.pronoun()} said.')


def tempt(world: World, a: Entity, forbidden: Forbidden) -> None:
    a.memes["bravado"] += 1
    # A bold child (high initial bravery) jumps on the idea harder.
    lit = "eyes lit up at once" if a.memes["bravery"] >= 6 else "eyes lit up"
    world.say(
        f'{a.id}\'s {lit}. "I know! {forbidden.cry} I saw '
        f'{forbidden.phrase} {forbidden.where}."'
    )
    world.say("For one breath, the idea felt clever.")


def warn(world: World, b: Entity, a: Entity, forbidden: Forbidden,
         target: Flammable, parent: Entity) -> None:
    """The cautioner foresees the danger via the world model and warns."""
    pred = predict_fire(world, "target")
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    # A very cautious child (initial trait + this beat) pushes back harder.
    extra = ""
    if b.memes["caution"] >= 6:
        extra = (f' {b.pronoun().capitalize()} shook {b.pronoun("possessive")} '
                 f'head, sure it was a bad idea.')
    world.say(
        f'{b.id} bit {b.pronoun("possessive")} lip. "{a.id}, we\'re not allowed '
        f'to touch {forbidden.label}. {parent.label_word.capitalize()} said. '
        f'It can make a real flame, and {target.the} can catch."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    """The instigator goes ahead anyway (fire WILL start).  Use names, not bare
    pronouns, so the older-sibling case never reads as the cautioner 'giving up'
    and then a fire happening anyway -- the cautioner simply fails to stop them."""
    a.memes["defiance"] += 1
    them = "them" if forbidden.plural else "it"
    instigator_older_sib = a.attrs.get("relation") == "siblings" and a.age > b.age
    if instigator_older_sib:
        rel = "big brother" if a.type == "boy" else "big sister"
        if b.memes["trust"] >= 6:
            mid = (f"and because {a.id} was {b.pronoun('possessive')} {rel}, "
                   f"{b.id} trusted {a.pronoun('object')} and didn't stop "
                   f"{a.pronoun('object')}")
        else:
            mid = (f"and even though {b.id} wasn't sure, {a.id} was "
                   f"{b.pronoun('possessive')} {rel}, so {b.id} didn't stop "
                   f"{a.pronoun('object')}")
        world.say(
            f'"Don\'t be such a scaredy-cat," {a.id} said, {mid}. '
            f"Then {a.id} ran to get {them}."
        )
    else:
        world.say(
            f'"Don\'t be such a scaredy-cat," {a.id} said, and ran to get {them}.'
        )


def back_down(world: World, a: Entity, b: Entity, forbidden: Forbidden,
              parent: Entity, theme: Theme) -> None:
    """The averted outcome: the cautioner (the older sibling) overrules the
    instigator, who gives up the idea -- so no fire ever starts."""
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    them = "them" if forbidden.plural else "it"
    were = "they were" if forbidden.plural else "it was"
    rel = "big brother" if b.type == "boy" else "big sister"
    world.say(
        f'"Don\'t be such a scaredy-cat," {a.id} said. But {b.id} was '
        f"{a.pronoun('possessive')} {rel}, so {a.id} looked at "
        f"{b.pronoun('object')}, thought better of it, and gave up the idea."
    )
    world.say(
        f"They left {them} right where {were} and went to tell "
        f"{parent.label_word.capitalize()} how dark the {theme.cave_word} had been."
    )


def ignite(world: World, target_ent: Entity, forbidden: Forbidden,
           target: Flammable) -> None:
    _do_forbidden(world, target_ent)          # fires the spread rule (danger, fear)
    world.say(
        f"{forbidden.strike} {forbidden.unit[0].upper()}{forbidden.unit[1:]} "
        f"flared to life. For one second it was wonderful, a tiny golden flame "
        f"pretending to be a lantern. Then the flame leaned, kissed {target.near}, "
        f"and a little line of orange began to climb."
    )


def alarm(world: World, b: Entity, a: Entity, target: Flammable, parent: Entity) -> None:
    world.say(f'"{a.id}! Fire! {target.The}!" {b.id} screamed.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response,
           target_ent: Entity, target: Flammable, theme: Theme) -> None:
    target_ent.meters["burning"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(
        f"{parent.label_word.capitalize()} came running. In a flash "
        f"{parent.pronoun()} {body}."
    )
    world.say(
        f"The flame hissed and died, leaving only a smoky smell and two very "
        f"frightened {theme.role_plural}."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity,
           forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and hugged them both. "
        f'"I\'m not angry that you\'re scared," {parent.pronoun()} said softly. '
        f'"I\'m glad you called me. But you must always remember: '
        f'{forbidden.not_toy}. Fire can grow faster than you can run. '
        f'Promise me -- never, ever again."'
    )
    world.say(f'"We promise," whispered {b.id} and {a.id} together.')
    comfort = b.attrs.get("comfort")
    if comfort:
        world.say(f"{b.id} held {b.pronoun('possessive')} {comfort} close and nodded.")


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity,
              theme: Theme, l1: SafeLight, l2: SafeLight) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    if any(e.meters["scorched"] >= THRESHOLD for e in world.entities.values()):
        next_day = "The next day, after the scary part had been talked through"
    else:
        next_day = "The next day, after everyone had talked it through"
    world.say(
        f"{next_day}, {parent.label_word.capitalize()} had a surprise. "
        f"{parent.pronoun().capitalize()} handed them {l1.phrase} that {l1.glow}, "
        f"and {l2.phrase} that {l2.glow}."
    )
    world.say(
        f'"Now," {parent.pronoun()} smiled, "what does {theme.role_solo} need to '
        f'explore a dark {theme.cave_word}?"'
    )
    world.say(f"{a.id} held up the {l2.label}. {b.id} clicked on the {l1.label}.")
    world.say('"Safe light!" they cheered.')
    pet = world.facts.get("pet")
    if pet:
        world.say(f"Even {pet} padded along behind them.")
    world.say(
        f"This time, the {theme.role_plural} {theme.send_off} -- bright, brave, "
        f"and safe."
    )


# -- the "oopsie" branch: the method didn't work and the place burned down -----
def rescue_fail(world: World, parent: Entity, response: Response,
                target_ent: Entity, target: Flammable) -> None:
    """The chosen method is too weak for the fire; it spreads to the room."""
    if "room" in world.entities:
        world.get("room").meters["burning"] += 1
    target_ent.meters["burning"] += 1
    propagate(world, narrate=False)               # danger + fear keep climbing
    body = response.fail.replace("{target}", target.label)
    world.say(
        f"{parent.label_word.capitalize()} came running and {body}."
    )
    world.say(f"The flames leapt from {target.the} to the sofa and raced up the walls.")


def escape_and_loss(world: World, parent: Entity, a: Entity, b: Entity,
                    theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"There was no time to be heroes. {parent.label_word.capitalize()} grabbed "
        f"{a.id} and {b.id} by the hand and rushed them out the front door, into "
        f"the cold night air."
    )
    pet = world.facts.get("pet")
    if pet:
        world.say(
            f"{parent.pronoun().capitalize()} scooped up {pet} too, and they all "
            f"tumbled out onto the lawn."
        )
    world.say(
        "From the sidewalk they watched the windows glow orange, and by the time "
        "the fire trucks screamed up the street, the little house was full of smoke."
    )
    world.say(
        "Their whole game -- the sofa, the crayon map, every bit of it -- was gone."
    )


def grim_lesson(world: World, parent: Entity, a: Entity, b: Entity,
                forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1                  # they are safe, and that is what counts
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    comfort = b.attrs.get("comfort")
    clutch = (f" {b.id} clutched {b.pronoun('possessive')} {comfort}, the one toy "
              f"that had made it out with them." if comfort else "")
    world.say(
        f'{parent.label_word.capitalize()} knelt on the cold grass and held them '
        f'tight. "You\'re safe. That\'s all that matters," {parent.pronoun()} '
        f'whispered.{clutch}'
    )
    world.say(
        f"But {a.id} and {b.id} never forgot what they learned that night: "
        f"{forbidden.not_toy}, and fire can grow faster than anyone can run."
    )
    world.say(
        "After that, when a game grew too dark, they called a grown-up instead."
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse five-beat shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(theme: Theme, forbidden: Forbidden, target: Flammable,
         lights: tuple[SafeLight, SafeLight], response: Response,
         instigator: str = "Tom", instigator_gender: str = "boy",
         cautioner: str = "Lily", cautioner_gender: str = "girl",
         trait: str = "careful", parent_type: str = "mother",
         delay: int = 0, instigator_age: int = 6, cautioner_age: int = 4,
         relation: str = "siblings", trust: int = 7,
         comfort: str = "", pet: str = "") -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender,
                         role="instigator", traits=["bold"], age=instigator_age,
                         attrs={"relation": relation}))
    b = world.add(Entity(id=cautioner, kind="character", type=cautioner_gender,
                         role="cautioner", traits=[trait], age=cautioner_age,
                         attrs={"relation": relation, "comfort": comfort}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              role="parent", label="the parent"))

    # Initial character memes (background emotional state) that later beats read.
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    world.facts["pet"] = pet
    world.facts["relation"] = relation
    world.add(Entity(id="room", type="room", label="the room"))
    tool = world.add(Entity(id="tool", type="tool", label=forbidden.label,
                            makes_flame=True))
    tgt = world.add(Entity(id="target", type="target", label=target.label,
                           flammable=target.flammable))
    l1, l2 = lights

    # Act 1 -- the pretend world and the dark spot that needs light.
    play_setup(world, a, b, theme)
    need_light(world, b, theme, target)

    # Act 2 -- temptation and a grounded warning.
    world.para()
    tempt(world, a, forbidden)
    warn(world, b, a, forbidden, target, parent)

    # Decision: can the cautioner talk the instigator out of it (no fire at all)?
    averted = would_avert(relation, a.age, b.age, trait)

    if averted:
        # Averted -- the near-miss.  The instigator backs down; no fire happens,
        # and they go straight to the safe alternative.
        back_down(world, a, b, forbidden, parent, theme)
        world.para()
        safe_gift(world, parent, a, b, theme, l1, l2)
        severity, contained = 0, True
    else:
        defy(world, a, b, forbidden)

        # Act 3 -- the accident: the flame catches the target (rule fires).
        world.para()
        ignite(world, tgt, forbidden, target)
        alarm(world, b, a, target, parent)

        # Does the method beat the fire?  Severity (a fast target + the head start
        # the fire got) vs. the response's power -- happy vs. "oopsie".
        severity = fire_severity(target, delay)
        tgt.meters["severity"] = float(severity)
        contained = is_contained(response, target, delay)

        world.para()
        if contained:
            # Act 4 -- a calm, sensible rescue and the lesson.
            rescue(world, parent, response, tgt, target, theme)
            lesson(world, parent, a, b, forbidden)
            # Act 5 -- the safe alternative and a bright, brave, safe ending.
            world.para()
            safe_gift(world, parent, a, b, theme, l1, l2)
        else:
            # Act 4' -- the method fails; the fire wins (the cautionary ending).
            rescue_fail(world, parent, response, tgt, target)
            escape_and_loss(world, parent, a, b, theme)
            grim_lesson(world, parent, a, b, forbidden)

    outcome = "averted" if averted else ("contained" if contained else "burned")
    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        instigator=a, cautioner=b, parent=parent, theme=theme,
        forbidden=forbidden, target_cfg=target, target=tgt, tool=tool,
        lights=(l1, l2), response=response,
        ignited=tgt.meters["scorched"] >= THRESHOLD,
        outcome=outcome, rescued=contained, severity=severity, delay=delay,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a wild island",
        rig=(
            "The sofa was their pirate ship, a broom became a sword, an old shoebox "
            "held their treasure, and a crayon map showed the way to the gold."
        ),
        captain="Captain",
        mate="Explorer",
        goal="the treasure cave",
        dark_spot="the space under the big table",
        cave_word="cave",
        role_solo="a pirate",
        role_plural="pirates",
        send_off="sailed off to find their treasure",
    ),
    "explorers": Theme(
        id="explorers",
        scene="a deep jungle",
        rig=(
            "The sofa was their jeep, a broom became a machete, an old shoebox held "
            "their supplies, and a crayon map showed the way to the lost temple."
        ),
        captain="Captain",
        mate="Scout",
        goal="the hidden temple",
        dark_spot="the space under the big table",
        cave_word="tunnel",
        role_solo="an explorer",
        role_plural="explorers",
        send_off="set off to find the lost temple",
    ),
    "astronauts": Theme(
        id="astronauts",
        scene="a faraway planet",
        rig=(
            "The sofa was their rocket, a broom became a space flag, an old shoebox "
            "held their moon rocks, and a crayon map showed the way to the crater."
        ),
        captain="Commander",
        mate="Pilot",
        goal="the dark crater",
        dark_spot="the space under the big table",
        cave_word="crater",
        role_solo="an astronaut",
        role_plural="astronauts",
        send_off="blasted off to explore the crater",
    ),
}

FORBIDDEN = {
    "matches": Forbidden(
        id="matches",
        cry="Matches!",
        label="matches",
        phrase="a box of matches",
        where="in the kitchen drawer",
        unit="the first match",
        strike="Scritch!",
        not_toy="matches are not toys",
        plural=True,
        tags={"matches", "fire", "call_adult"},
    ),
    "lighter": Forbidden(
        id="lighter",
        cry="A lighter!",
        label="the lighter",
        phrase="a lighter",
        where="on the coffee table",
        unit="the little flame",
        strike="Click!",
        not_toy="a lighter is not a toy",
        plural=False,
        tags={"lighter", "fire", "call_adult"},
    ),
    "candle": Forbidden(
        id="candle",
        cry="A candle!",
        label="the candle",
        phrase="a candle and the long matches",
        where="on the mantel",
        unit="the candle flame",
        strike="Scritch!",
        not_toy="candles are not toys",
        plural=False,
        tags={"candle", "fire", "call_adult"},
    ),
}

TARGETS = {
    "curtain": Flammable(
        id="curtain",
        label="curtain",
        the="the curtain",
        near="the bottom of the curtain",
        drape="hung with long dark curtains",
        spread=3,
        flammable=True,
        tags={"curtain", "flammable"},
    ),
    "blanket": Flammable(
        id="blanket",
        label="blanket",
        the="the blanket",
        near="the edge of the blanket",
        drape="draped with a big fuzzy blanket",
        spread=2,
        flammable=True,
        tags={"blanket", "flammable"},
    ),
    "tablecloth": Flammable(
        id="tablecloth",
        label="tablecloth",
        the="the tablecloth",
        near="the hem of the long tablecloth",
        drape="half-covered by a long tablecloth",
        spread=2,
        flammable=True,
        tags={"tablecloth", "flammable"},
    ),
    # Decoy: not flammable -> no fire, no rescue, no lesson.  Used to show the
    # reasonableness gate refuse a story (cf. jacket+puddles in puddles.py).
    "tiles": Flammable(
        id="tiles",
        label="tile wall",
        the="the tile wall",
        near="the cool tiles",
        drape="edged by a cold tile wall",
        flammable=False,
        tags={"tiles"},
    ),
}

SAFE_LIGHTS = {
    "flashlight": SafeLight(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="clicked on bright as a star",
        tags={"flashlight"},
    ),
    "lantern": SafeLight(
        id="lantern",
        label="lantern",
        phrase="a little camping lantern",
        glow="glowed warm and safe",
        tags={"lantern"},
    ),
    "headlamp": SafeLight(
        id="headlamp",
        label="head-lamp",
        phrase="a head-lamp",
        glow="lit up the whole cave",
        tags={"headlamp"},
    ),
    "glowsticks": SafeLight(
        id="glowsticks",
        label="glow sticks",
        phrase="two bendy glow sticks",
        glow="shone green in the dark",
        plural=True,
        tags={"glowsticks"},
    ),
}

# ---------------------------------------------------------------------------
# Analysis section: ranking of responses by common sense and power.
# ---------------------------------------------------------------------------
# Original/base texts of reference stories that you'll make can be problematic, 
# it is not the greatest solution:  ```she grabbed the bucket from the closet,
# filled it at the sink, and threw the water -- whoosh -- right over the curtain```
# In this particular case, either grabbing a fire extinguisher from the kitchen, 
# or pulling down the curtain on the floor and putting them in a ball to get the 
# fire extinguished is a more sensible option.  Ideally storyworld models would 
# include such common sense options, and would prefer them.
#
# So: RESPONSES carries the weak water-bucket option for fidelity to the source,
# but ranks it below SENSE_MIN, so the model knows about it yet refuses to tell it
# (see sensible_responses / explain_response).  The default stories use the
# fire-extinguisher or pull-down-and-smother responses instead.
RESPONSES = {
    "extinguisher": Response(
        id="extinguisher",
        sense=3,
        power=4,
        text=(
            "grabbed the fire extinguisher from the kitchen and sprayed the flames "
            "until every spark was gone"
        ),
        fail=(
            "emptied the whole fire extinguisher, but the flames were already too big "
            "to stop"
        ),
        qa_text="put the flames out with the fire extinguisher",
        tags={"extinguisher", "fire"},
    ),
    "smother": Response(
        id="smother",
        sense=3,
        power=3,
        text=(
            "pulled the {target} down to the floor, balled it up, and pressed the "
            "flames out under a heavy rug"
        ),
        fail=(
            "tried to pull the {target} down, but the fire was climbing too fast to "
            "smother"
        ),
        qa_text="pulled the {target} down and smothered the flames under a heavy rug",
        tags={"smother", "fire"},
    ),
    "stomp": Response(
        id="stomp",
        sense=2,
        power=2,
        text=(
            "pulled the {target} down and stamped on the flames, hard and fast, until "
            "they were out"
        ),
        fail="stamped at the flames, but they only leapt higher",
        qa_text="pulled the {target} down and stamped the flames out",
        tags={"smother", "fire"},
    ),
    # Deliberately low common-sense (the original): kept for reference, refused by
    # the SENSE_MIN gate so it is never the chosen response.
    "water_bucket": Response(
        id="water_bucket",
        sense=1,
        power=1,
        text="filled a bucket at the sink and threw the water over the {target}",
        fail="threw a bucket of water over the {target}, but it was far too little",
        qa_text="threw a bucket of water over the {target}",
        tags={"water", "fire"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "clever", "cautious", "thoughtful", "sensible"]

# Background "possessions" -- never named outright, only used to colour a beat.
COMFORTS = ["stuffed rabbit", "toy dinosaur", "floppy teddy bear", "little plush owl"]
PETS = ["the cat", "the puppy", "their little dog", "the kitten"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(theme, forbidden, target) triples that pass the reasonableness gate."""
    combos = []
    if not sensible_responses():
        return combos
    for theme in THEMES:
        for fb_id, fb in FORBIDDEN.items():
            for tg_id, tg in TARGETS.items():
                if hazard_at_risk(fb, tg):
                    combos.append((theme, fb_id, tg_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    theme: str
    forbidden: str
    target: str
    light1: str
    light2: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0       # head start the fire gets; high enough -> it burns down
    # Background state -- never stated outright, only used to branch the prose.
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"   # "siblings" | "friends"
    trust: int = 7               # cautioner's initial trust in the instigator (0-10)
    comfort: str = ""            # cautioner's comfort toy (may be "")
    pet: str = ""                # family pet (may be "")
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.  Answerable WITHOUT the story.
KNOWLEDGE = {
    "matches": [("What are matches?",
                 "Matches are little sticks that make a small flame when you "
                 "scratch them. They are a grown-up tool, not a toy.")],
    "lighter": [("What is a lighter?",
                 "A lighter is a small tool grown-ups use to make a flame. "
                 "Children should never touch one.")],
    "candle": [("Why can a candle be dangerous?",
                "A candle has a real flame, and if it tips over or touches "
                "something it can start a fire.")],
    "fire": [("Why is fire dangerous?",
              "Fire is very hot and it can grow and spread faster than you can "
              "run, so it can burn things and hurt people quickly.")],
    "curtain": [("Why do curtains catch fire easily?",
                 "Curtains are made of thin cloth that burns fast, so a flame "
                 "near them can spread very quickly.")],
    "blanket": [("Can a blanket catch fire?",
                 "Yes. A blanket is cloth, and cloth burns, so a flame can set "
                 "it alight.")],
    "tablecloth": [("Is a tablecloth flammable?",
                    "Yes, a tablecloth is cloth and can catch fire, so keep "
                    "flames away from it.")],
    "call_adult": [("What should you do if something catches fire?",
                    "Get away from the fire and shout for a grown-up right away. "
                    "Calling for help fast is the bravest thing to do.")],
    "escape": [("What should you do if a fire gets too big to put out?",
                "Get outside right away and stay out. Never hide or go back for "
                "toys -- things can be replaced, but you cannot.")],
    "firefighters": [("Who puts out big fires?",
                      "Firefighters do. They come in fire trucks with hoses and "
                      "special gear to put big fires out.")],
    "extinguisher": [("What does a fire extinguisher do?",
                      "A fire extinguisher sprays out stuff that smothers a fire "
                      "and puts it out quickly. Grown-ups use it.")],
    "smother": [("How can you put out a small fire by smothering it?",
                 "You take away the air the fire needs, like by covering it with "
                 "a thick blanket, and the flames go out.")],
    "flashlight": [("What is a flashlight?",
                    "A flashlight is a light you turn on with a button. It uses "
                    "batteries, so it is bright and safe with no flame.")],
    "lantern": [("What is a camping lantern?",
                 "A camping lantern is a battery light that glows all around, so "
                 "you can see in the dark without any fire.")],
    "headlamp": [("What is a head-lamp?",
                  "A head-lamp is a little light you wear on your head, so your "
                  "hands stay free and there is no flame.")],
    "glowsticks": [("What are glow sticks?",
                    "Glow sticks are bendy sticks that shine with a soft light "
                    "when you snap them. They are cool to the touch and safe.")],
}
KNOWLEDGE_ORDER = ["matches", "lighter", "candle", "fire", "curtain", "blanket",
                   "tablecloth", "call_adult", "escape", "firefighters",
                   "extinguisher", "smother", "flashlight", "lantern", "headlamp",
                   "glowsticks"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    """A relation-aware noun for the two children (used only in Q&A)."""
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    a, b, fb, th, tg = (f["instigator"], f["cautioner"], f["forbidden"],
                        f["theme"], f["target_cfg"])
    l1, l2 = f["lights"]
    outcome = f.get("outcome")
    if outcome == "averted":
        sib = "brother" if b.type == "boy" else "sister"
        return [
            f'Write a fire-safety story for a 3-to-5-year-old where two children '
            f'playing {th.role_plural} are tempted to use {fb.label} for light, '
            f'but a wiser child stops them before anything happens. Include the '
            f'word "{fb.label}".',
            f"Tell a near-miss story where {a.id} wants to light {fb.label}, but "
            f"listens to {b.id}, {a.pronoun('possessive')} older {sib}, and gives "
            f"up the idea; the next day they use safe light instead.",
            f'Write a gentle story where an older sibling talks a younger one out '
            f'of touching {fb.label}, teaching "{fb.not_toy}", with a calm, safe '
            f'ending and no fire at all.',
        ]
    burned = outcome == "burned"
    base = (
        f'Write a fire-safety story for a 3-to-5-year-old where two children '
        f'playing {th.role_plural} are tempted to use {fb.label} for light and '
        f'something catches fire. Include the word "{fb.label}".'
    )
    if burned:
        return [
            base,
            f"Tell a cautionary story where {a.id} ignores {b.id}'s warning and "
            f"lights {fb.label} near {tg.the}, but the fire spreads too fast to "
            f"put out and the house burns down -- though everyone escapes safely.",
            f'Write a story with a sad, scary ending that teaches '
            f'"{fb.not_toy}": the family loses their home to a fire but stays '
            f'safe, and the children never play with fire again.',
        ]
    return [
        base,
        f"Tell a gentle cautionary story where {a.id} ignores {b.id}'s warning "
        f"and lights {fb.label} near {tg.the}, and a calm grown-up puts the fire "
        f"out and is glad the children called for help instead of being angry.",
        f'Write a simple story that teaches "{fb.not_toy}" and ends with the '
        f'children using {l1.phrase} and {l2.phrase} for safe light.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    fb, th, tg, resp = f["forbidden"], f["theme"], f["target_cfg"], f["response"]
    l1, l2 = f["lights"]
    pw = parent.label_word
    them = "them" if fb.plural else "it"
    pair = pair_noun(a, b, f.get("relation", "friends"))
    # Keep story QA heavily parametrized by sampled story state. These should
    # vary with names, relation, pretend frame, forbidden tool, flammable target,
    # adult response, safe-light substitute, and outcome as much as possible.
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when {a.id} and {b.id} play {th.role_plural}?",
            answer=(
                f"It is about {pair}, {a.id} and {b.id}, who were playing "
                f"{th.role_plural}, and {a.id}'s {pw} who came to help."
            ),
        ),
        QAItem(
            question=f"What pretend game did {a.id} and {b.id} make in the living room?",
            answer=(
                f"They turned the living room into {th.scene} and pretended to be "
                f"{th.role_plural} looking for {th.goal}. The pretend game made "
                f"{th.dark_spot} feel like part of the adventure."
            ),
        ),
        QAItem(
            question=f"Why did {a.id} and {b.id} need light for {th.goal}?",
            answer=(
                f"They wanted to explore {th.dark_spot}, where {tg.the} made the "
                f"pretend {th.cave_word} dark. That darkness made {fb.label} seem "
                f"tempting even though it could make a real flame."
            ),
        ),
        QAItem(
            question=f"What did {a.id} want to use near {tg.the}, and what did {b.id} say?",
            answer=(
                f"{a.id} wanted to use {fb.label}, but {b.id} warned that they were "
                f"not allowed to touch {fb.label}. {b.id} also knew it could make "
                f"a real flame near {tg.the}."
            ),
        ),
    ]
    if f.get("ignited"):
        qa.append(QAItem(
            question=f"What happened when {a.id} lit {them} near {tg.the}?",
            answer=(
                f"{tg.The} caught fire -- a little line of flame began to climb up it, "
                f"and the children were very scared. The danger came from using "
                f"{fb.label} near something flammable."
            ),
        ))
    if f.get("outcome") == "averted":
        sib = "brother" if b.type == "boy" else "sister"
        qa.append(QAItem(
            question=(
                f"What did {a.id} do after {b.id} warned {a.pronoun('object')} "
                f"about {fb.label}?"
            ),
            answer=(
                f"{a.id} listened to {b.id}, {a.pronoun('possessive')} big {sib}, and "
                f"gave up the idea, so no fire ever started. They told {pw} about "
                f"the dark {th.cave_word} instead of touching {fb.label}."
            ),
        ))
        qa.append(QAItem(
            question=f"What safe lights did {a.id}'s {pw} give for {th.dark_spot}?",
            answer=(
                f"{parent.pronoun().capitalize()} gave them {l1.phrase} and "
                f"{l2.phrase} so they could explore with safe light. Those lights "
                f"met the same need without making fire."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {a.id} and {b.id}'s {th.role_plural} game end with "
                f"{l1.label} and {l2.label}?"
            ),
            answer=(
                f"Safely -- they used safe light instead of {fb.label}, and nobody "
                f"got hurt and nothing burned. The game could continue because they "
                f"chose a safer tool."
            ),
        ))
    elif f.get("outcome") == "contained":
        body = resp.qa_text.replace("{target}", tg.label)
        qa.append(QAItem(
            question=f"How did {a.id}'s {pw} put out the fire on {tg.the}?",
            answer=(
                f"{pw.capitalize()} came running and {body}. The quick response "
                f"stopped the fire before it spread through the room."
            ),
        ))
        qa.append(QAItem(
            question=f"Was {a.id}'s {pw} angry after {a.id} used {fb.label}?",
            answer=(
                f"No. {pw.capitalize()} hugged them, was glad they called for help, "
                f"and reminded them that {fb.not_toy} and that fire can grow faster "
                f"than you can run."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What safer lights replaced {fb.label} in {a.id} and {b.id}'s "
                f"{th.role_plural} game?"
            ),
            answer=(
                f"{parent.pronoun().capitalize()} gave them {l1.phrase} and "
                f"{l2.phrase} so they could explore with safe light. The new lights "
                f"let them keep the adventure without the flame."
            ),
        ))
        qa.append(QAItem(
            question=f"How did {a.id} and {b.id} feel after the fire near {tg.the} was out?",
            answer=(
                f"They felt brave, happy, and safe, and they promised never to play "
                f"with {fb.label} again. The ending turns the scary lesson into a "
                f"safer way to keep playing."
            ),
        ))
    elif f.get("outcome") == "burned":
        fail = resp.fail.replace("{target}", tg.label)
        qa.append(QAItem(
            question=f"Could {a.id}'s {pw} put out the fire after {tg.the} caught?",
            answer=(
                f"No. {pw.capitalize()} {fail}, and the fire raced through the whole "
                f"house. The family had to escape because the fire was already too "
                f"big for that response."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did the story end for {a.id} and {b.id} after {fb.label} "
                f"set {tg.the} on fire?"
            ),
            answer=(
                f"Everyone got out safely, but the house burned down. {a.id} and "
                f"{b.id} were safe, though very sad to lose their home. Afterward, "
                f"they knew to call a grown-up whenever a game grew too dark."
            ),
        ))
        qa.append(QAItem(
            question=f"What did {a.id} and {b.id} learn about {fb.label} and {th.goal}?",
            answer=(
                f"{fb.not_toy[0].upper()}{fb.not_toy[1:]}, and that fire can grow "
                f"faster than anyone can run. The lesson came from seeing how quickly "
                f"one unsafe flame became bigger than their game."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    outcome = f.get("outcome")
    tags: set[str] = set(f["forbidden"].tags) | set(f["target_cfg"].tags)
    if outcome == "burned":
        tags |= set(f["response"].tags) | {"escape", "firefighters"}  # no safe lights
    elif outcome == "contained":
        tags |= set(f["response"].tags)
        for light in f["lights"]:                 # safe lights in the happy ending
            tags |= set(light.tags)
    else:                                         # averted: no fire, no response used
        for light in f["lights"]:
            tags |= set(light.tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [n for n, on in (("flammable", e.flammable),
                                 ("makes_flame", e.makes_flame),
                                 ("gives_light", e.gives_light)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    # Happy: a sensible response that beats the fire (delay small enough).
    # Older brother + high trust -> the "she trusted him" defiance branch.
    StoryParams(
        theme="pirates",
        forbidden="matches",
        target="curtain",
        light1="flashlight",
        light2="lantern",
        response="extinguisher",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=8,
        comfort="stuffed rabbit",
        pet="the puppy",
    ),
    # Friends, low trust -> no sibling clause; firm cautious warning.
    StoryParams(
        theme="explorers",
        forbidden="lighter",
        target="blanket",
        light1="headlamp",
        light2="lantern",
        response="smother",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="clever",
        delay=0,
        instigator_age=5,
        cautioner_age=5,
        relation="friends",
        trust=3,
    ),
    # Oopsie: the method is too weak for a fast fire -> the place burns down.
    StoryParams(
        theme="astronauts",
        forbidden="candle",
        target="tablecloth",
        light1="flashlight",
        light2="glowsticks",
        response="stomp",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=1,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=4,
        comfort="toy dinosaur",
        pet="the cat",
    ),
    # Averted: the cautioner is the older sibling, so the instigator gives up the
    # idea and no fire ever starts -- straight to the safe alternative.
    StoryParams(
        theme="pirates",
        forbidden="lighter",
        target="curtain",
        light1="glowsticks",
        light2="flashlight",
        response="extinguisher",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Tom",
        cautioner_gender="boy",
        parent="father",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
        pet="their little dog",
    ),
    # Even the extinguisher can be too late once the fire gets a big head start.
    StoryParams(
        theme="pirates",
        forbidden="matches",
        target="curtain",
        light1="headlamp",
        light2="lantern",
        response="extinguisher",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=2,
        comfort="floppy teddy bear",
    ),
]


def explain_rejection(forbidden: Forbidden, target: Flammable) -> str:
    if not target.flammable:
        return (f"(No story: {forbidden.label} can make a flame, but {target.the} "
                f"won't catch fire -- no fire means no rescue and no lesson. "
                f"Pick a flammable target like a curtain or a blanket.)")
    if not forbidden.makes_flame:
        return (f"(No story: {target.the} is flammable, but {forbidden.label} "
                f"makes no flame, so nothing ignites.)")
    return "(No story: this combination has no fire hazard.)"


def outcome_of(params: StoryParams) -> str:
    """'averted', 'contained', or 'burned' for a set of params (no narration)."""
    if would_avert(params.relation, params.instigator_age,
                   params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response],
                             TARGETS[params.target], params.delay)
    return "contained" if contained else "burned"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (f"(Refusing response '{rid}': it scores too low on common sense "
            f"(sense={r.sense} < {SENSE_MIN}). A storyworld should prefer safer, "
            f"smarter responses. Try: {better}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (hazard_at_risk / sensible_responses / valid_combos) AND the outcome model
# (would_avert / is_contained / outcome_of).  The rules are inline below; the
# facts are generated from the registries above so the two can never drift.
# Uses the shared `asp` helper + clingo, imported lazily so the prose engine
# runs without them.  See `python pirates.py --verify`.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(F, Tg) :- makes_flame(F), flammable(Tg).
sensible(R)   :- response(R), sense(R, S), sense_min(M), S >= M.
valid(T, F, Tg) :- theme(T), forbidden(F), target(Tg), hazard(F, Tg).

% --- outcome inference (averted | contained | burned) ----------------------
% Averted iff the cautioner is the older sibling (mirrors would_avert: their
% caution + the warning beat always clears bravery_init in that case).
cautious_now(T)  :- trait(T), is_cautious(T).
init_caution(5)  :- trait(T), cautious_now(T).
init_caution(3)  :- trait(T), not cautious_now(T).
cautioner_older  :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4)         :- cautioner_older.
bonus(0)         :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted          :- cautioner_older, authority(A), bravery_init(BR), A > BR.

% Otherwise the fire happens; a response contains it only if its power matches
% the fire's severity (spread of the target plus the head start = delay).
severity(Sp + D) :- chosen_target(Tg), spread(Tg, Sp), delay(D).
resp_power(P)    :- chosen_response(R), power(R, P).
contained        :- resp_power(P), severity(V), P >= V.

outcome(averted)   :- averted.
outcome(contained) :- not averted, contained.
outcome(burned)    :- not averted, not contained.
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid, f in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", fid))
        if f.makes_flame:
            lines.append(asp.fact("makes_flame", fid))
        if f.plural:
            lines.append(asp.fact("forbidden_plural", fid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.flammable:
            lines.append(asp.fact("flammable", tid))
        lines.append(asp.fact("spread", tid, t.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    for lid in SAFE_LIGHTS:
        lines.append(asp.fact("light", lid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (theme, forbidden, target) triples."""
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    """Derive the ending (averted | contained | burned) for one scenario."""
    import asp
    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    """Check the inline ASP reasoner agrees with the Python gate + outcome."""
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} "
              f"python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(300):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a forbidden spark, a safe "
                    "alternative. Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2],
                    help="head start the fire gets before help arrives; higher "
                         "makes it more likely the place burns down (random if unset)")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    # Clingo (ASP) modes -- the inline declarative reasoner (needs clingo).
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.target and not TARGETS[args.target].flammable:
        fb = FORBIDDEN[args.forbidden] if args.forbidden else next(iter(FORBIDDEN.values()))
        raise StoryError(explain_rejection(fb, TARGETS[args.target]))
    if args.forbidden and args.target:
        fb, tg = FORBIDDEN[args.forbidden], TARGETS[args.target]
        if not hazard_at_risk(fb, tg):
            raise StoryError(explain_rejection(fb, tg))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, forbidden, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    light1, light2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    # Background state (seeded): ages, relationship, trust, and a couple of
    # possessions.  Never stated outright -- only used to branch the prose.
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    comfort = rng.choice(COMFORTS + ["", ""])
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(
        theme=theme,
        forbidden=forbidden,
        target=target,
        light1=light1,
        light2=light2,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
        comfort=comfort,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(
        THEMES[params.theme], FORBIDDEN[params.forbidden], TARGETS[params.target],
        (SAFE_LIGHTS[params.light1], SAFE_LIGHTS[params.light2]),
        RESPONSES[params.response],
        params.instigator, params.instigator_gender,
        params.cautioner, params.cautioner_gender,
        params.trait, params.parent, params.delay,
        params.instigator_age, params.cautioner_age, params.relation,
        params.trust, params.comfort, params.pet,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, forbidden, target) combos:\n")
        for theme, forbidden, target in combos:
            print(f"  {theme:10} {forbidden:8} {target}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (f"### {p.instigator} & {p.cautioner}: {p.forbidden} near "
                      f"{p.target} ({p.theme}, {p.response}, {outcome_of(p)})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
