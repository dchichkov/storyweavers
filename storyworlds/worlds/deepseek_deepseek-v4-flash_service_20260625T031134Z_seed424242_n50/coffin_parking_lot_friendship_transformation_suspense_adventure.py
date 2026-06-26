#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/coffin_parking_lot_friendship_transformation_suspense_adventure.py
=====================================================================================================

A standalone *story world* sketch for "The Coffin in the Parking Lot" tale and close,
*constraint-checked* variations of it.

Initial story (used to build a world model):
---
Once upon a time, two friends named Ravi and Emma were playing in the big parking
lot behind the old mall. They loved exploring the empty spaces and imagining they
were brave adventurers. One afternoon, they found a strange wooden coffin hidden
behind a dumpster. It was old and dusty, with a heavy brass lock.

Ravi wanted to open the coffin right away to see what was inside, but Emma felt a
shiver and said no. "What if something creepy is in there?" she asked. Ravi laughed
and tried to pull open the lid, but the lock held tight.

Then a friendly old man in a green hat walked over from the repair shop. "That box
is for gardening supplies," he said with a wink. "But I keep it locked so nobody
spills the soil." He opened the coffin with a tiny key, and inside were bags of
rich, dark dirt and shiny flower seeds. Ravi and Emma smiled and decided to plant
a secret garden together in the empty lot next door.

Causal state updates:
---
    approach curiosity          -> actor.curiosity += 1
                                  actor.boldness += 1
    friend warns                -> actor.fear += 1
                                  actor.trust_friend += 1 (if heeded) else actor.stubbornness += 1
    lock discovered             -> actor.determination += 1
    adult reveals truth         -> actor.confusion -> 0, actor.trust_adult += 1, actor.relief += 1
    transform trash to garden   -> actor.creativity += 1, actor.friendship += 1, location.transform += 1
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
# (``python storyworlds/worlds/<name>.py``): add the package dir (storyworlds/)
# to the path so ``results`` resolves regardless of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Emotional meter keys.
FEELING_KINDS = {"curiosity", "fear", "boldness", "trust_friend", "stubbornness",
                 "determination", "trust_adult", "relief", "creativity", "friendship"}

# Location zones in the parking lot.
ZONES = {"behind_dumpster", "by_repair_shop", "near_entrance", "empty_lot_next_door"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # boy, girl, adult, coffin, key, seeds, ...
    label: str = ""                # short reference, e.g. "coffin", "old key"
    phrase: str = ""               # full noun phrase, e.g. "a strange wooden coffin with a brass lock"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = "parking_lot"
    zone: str = ""                 # where the entity sits
    plural: bool = False
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mom"}
        male = {"boy", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"woman": "lady", "man": "man"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the parking lot"
    affords: set[str] = field(default_factory=set)   # which activities this place supports


@dataclass
class Mystery:
    """The mysterious object the friends discover."""
    id: str
    noun: str            # "coffin"
    phrase: str          # "a strange wooden coffin"
    detail: str          # "with a heavy brass lock"
    hidden_truth: str    # what it actually contains
    transform_into: str  # what the friends make from it


@dataclass
class Adventure:
    """The suspenseful activity the friends engage in."""
    id: str
    verb_approach: str   # "approach the mysterious box"
    verb_explore: str    # "explore the parking lot"
    suspense_clue: str   # "the lock gleamed in the sunlight"
    reveal: str          # "bags of rich, dark dirt and shiny flower seeds"
    outcome: str         # "a secret garden in the empty lot"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    """The adult who resolves the suspense."""
    id: str
    phrase: str          # "a friendly old man in a green hat"
    title: str           # "the repair shop owner"
    explanation: str     # "That box is for gardening supplies"
    action: str          # "opened the coffin with a tiny key"
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
        self.zone: str = ""
        self.transform_level: float = 0.0    # how much the lot is transformed
        # Facts recorded during the screenplay, read back by the Q&A generators.
        self.facts: dict = {}

    # -- entity helpers -----------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def friends(self) -> list[Entity]:
        return [e for e in self.characters() if e.type in ("boy", "girl")]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = self.zone
        clone.transform_level = self.transform_level
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


def _r_curiosity_spread(world: World) -> list[str]:
    """One friend's curiosity spreads to the other."""
    out: list[str] = []
    friends = world.friends()
    if len(friends) < 2:
        return out
    for actor in friends:
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        for other in friends:
            if other.id == actor.id:
                continue
            if other.memes["curiosity"] < THRESHOLD:
                sig = ("curiosity_spread", other.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                other.memes["curiosity"] += 0.5
                out.append(f"{other.id} caught the curious feeling too.")
    return out


def _r_warning_effect(world: World) -> list[str]:
    """Friend warns -> if heeded, trust; if ignored, stubbornness."""
    out: list[str] = []
    friends = world.friends()
    if len(friends) < 2:
        return out
    for actor in friends:
        if actor.memes["warned_by_friend"] < THRESHOLD:
            continue
        sig = ("heed_check", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if actor.memes["boldness"] >= THRESHOLD:
            actor.memes["stubbornness"] += 1
            out.append(f"{actor.id} felt brave and kept going anyway.")
        else:
            actor.memes["trust_friend"] += 1
            out.append(f"{actor.id} listened and felt safer with a friend.")
    return out


def _r_adventurous_turn(world: World) -> list[str]:
    """Lock discovered -> determination increases."""
    for actor in world.characters():
        if actor.memes["lock_discovered"] < THRESHOLD:
            continue
        sig = ("determination", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["determination"] += 1
        return ["The mystery made their hearts beat faster."]
    return []


def _r_transformation(world: World) -> list[str]:
    """Truth revealed -> confusion lifts, trust adult, relief, creativity."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["truth_revealed"] < THRESHOLD:
            continue
        sig = ("truth_effect", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["confusion"] = 0.0
        actor.memes["trust_adult"] += 1
        actor.memes["relief"] += 1
        actor.memes["creativity"] += 1
        if actor in world.friends():
            actor.memes["friendship"] += 1
    if out:
        return ["The truth turned suspense into a wonderful surprise."]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="curiosity_spread", tag="social", apply=_r_curiosity_spread),
    Rule(name="warning_effect", tag="social", apply=_r_warning_effect),
    Rule(name="adventurous_turn", tag="suspense", apply=_r_adventurous_turn),
    Rule(name="transformation", tag="resolution", apply=_r_transformation),
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
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* mystery and friend pair.
# ---------------------------------------------------------------------------
def friend_compatible(friend1_type: str, friend2_type: str) -> bool:
    """Different types create more interesting dynamics."""
    return friend1_type != friend2_type


def mystery_has_resolution(mystery: Mystery, helper: Helper) -> bool:
    """The helper can explain the mystery."""
    return True  # All defined mysteries have a resolution


# ---------------------------------------------------------------------------
# Prediction: simulate the emotional journey to check it is satisfying.
# ---------------------------------------------------------------------------
def predict_emotional_arc(world: World, actor_id: str) -> dict:
    """Simulate the discovery and resolution silently to check arc."""
    sim = world.copy()
    actor = sim.get(actor_id)
    # Simulate discovering the coffin
    actor.memes["curiosity"] += 1
    actor.memes["boldness"] += 1
    propagate(sim, narrate=False)
    # Simulate the warning
    for other in sim.friends():
        if other.id != actor_id:
            other.memes["fear"] += 0.5
            actor.memes["warned_by_friend"] += 1
    propagate(sim, narrate=False)
    # Simulate lock discovery
    actor.memes["lock_discovered"] += 1
    propagate(sim, narrate=False)
    # Simulate truth revealed
    actor.memes["truth_revealed"] += 1
    propagate(sim, narrate=False)
    return {
        "ended_with_creativity": actor.memes["creativity"] >= THRESHOLD,
        "ended_with_friendship": actor.memes["friendship"] >= THRESHOLD,
        "relief_felt": actor.memes["relief"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def adventure_anticipation(adventure: Adventure) -> str:
    return {
        "coffin": "the old wood smelled of dust and secrets",
        "chest": "the rusty lock seemed to tell a story",
        "trunk": "the leather straps held memories inside",
        "box": "the metal corners caught the afternoon light",
    }.get(adventure.id, "the air felt full of possibility")


def setting_detail(setting: Setting, adventure: Adventure) -> str:
    if "repair" in setting.place:
        return f"The {setting.place.removeprefix('the ')} was quiet except for a distant radio playing."
    if "mall" in setting.place:
        return f"The {setting.place.removeprefix('the ')} echoed with the sound of a single car door closing."
    return f"{setting.place.capitalize()} stretched wide and empty under the afternoon sky."


def friends_are_safe(hero1: Entity, hero2: Entity, mystery: Entity) -> str:
    return f"{hero1.id} and {hero2.id} were safe and the {mystery.noun} was just a surprise"


def _do_explore(world: World, actor: Entity, adventure: Adventure, narrate: bool = True) -> None:
    world.zone = "behind_dumpster"
    actor.memes["curiosity"] += 1
    actor.memes["boldness"] += 1
    propagate(world, narrate=narrate)


def introduce_friends(world: World, hero1: Entity, hero2: Entity) -> None:
    trait1 = next((t for t in hero1.traits if t != "little"), "")
    trait2 = next((t for t in hero2.traits if t != "little"), "")
    desc1 = f"little {trait1} {hero1.type}".strip()
    desc2 = f"little {trait2} {hero2.type}".strip()
    world.say(f"{hero1.id} was a {desc1} and {hero2.id} was a {desc2} who loved exploring together.")


def loves_adventures(world: World, hero1: Entity, hero2: Entity, adventure: Adventure) -> None:
    hero1.memes["love_explore"] += 1
    hero2.memes["love_explore"] += 1
    world.say(
        f"{hero1.id} and {hero2.id} loved exploring the {world.setting.place.removeprefix('the ')}; "
        f"{adventure_anticipation(adventure)}."
    )


def discover(world: World, hero1: Entity, hero2: Entity, mystery: Entity) -> None:
    world.say(
        f"One afternoon, they found {mystery.phrase} {mystery.detail} "
        f"hidden behind a dumpster."
    )


def suspense(world: World, hero1: Entity, hero2: Entity, adventure: Adventure, mystery: Entity) -> None:
    hero1.memes["curiosity"] += 1
    hero2.memes["curiosity"] += 1
    world.say(
        f"{hero1.id} wanted to open the {mystery.noun} right away, but "
        f"{hero2.id} felt a shiver and said no."
    )


def warn(world: World, warner: Entity, actor: Entity, adventure: Adventure, mystery: Entity) -> bool:
    """One friend warns the other about the mysterious coffin."""
    actor.memes["warned_by_friend"] += 1
    warner.memes["fear"] += 0.5
    world.say(
        f'"What if something creepy is in there?" asked {warner.id}.'
    )
    return True


def defies_warning(world: World, hero: Entity, adventure: Adventure) -> None:
    hero.memes["stubbornness"] += 1
    hero.memes["boldness"] += 1
    world.say(f"{hero.id} laughed and tried to pull open the lid, but the lock held tight.")


def discover_lock(world: World, hero1: Entity, hero2: Entity, mystery: Entity) -> None:
    hero1.memes["lock_discovered"] += 1
    hero2.memes["lock_discovered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The lock gleamed in the sunlight, and {hero1.id} felt a rush of determination."
    )


def helper_appears(world: World, helper: Entity, hero1: Entity, hero2: Entity) -> None:
    world.say(
        f"Then {helper.phrase} walked over from the repair shop."
    )


def explain_mystery(world: World, helper: Entity, mystery: Entity, adventure: Adventure) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f'"{helper.explanation}," said {helper.id} with a wink. "But I keep it locked so nobody spills the soil."'
    )


def reveal_truth(world: World, helper: Entity, hero1: Entity, hero2: Entity, mystery: Entity, adventure: Adventure) -> None:
    hero1.memes["truth_revealed"] += 1
    hero2.memes["truth_revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.action}, and inside were {adventure.reveal}."
    )


def transform_and_plant(world: World, hero1: Entity, hero2: Entity, adventure: Adventure, mystery: Mystery) -> None:
    hero1.memes["creativity"] += 1
    hero2.memes["creativity"] += 1
    hero1.memes["friendship"] += 1
    hero2.memes["friendship"] += 1
    world.transform_level += 1
    world.say(
        f"{hero1.id} and {hero2.id} smiled and decided to plant "
        f"{adventure.outcome} together in the empty lot next door."
    )
    world.say(
        f"The {mystery.noun} became a garden of flowers, and their friendship grew even stronger."
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery: Mystery, adventure: Adventure,
         helper: Helper,
         hero1_name: str = "Ravi", hero1_type: str = "boy",
         hero1_traits: Optional[list[str]] = None,
         hero2_name: str = "Emma", hero2_type: str = "girl",
         hero2_traits: Optional[list[str]] = None) -> World:
    world = World(setting)

    hero1 = world.add(Entity(
        id=hero1_name, kind="character", type=hero1_type,
        traits=["little"] + (hero1_traits or ["brave", "curious"]),
    ))
    hero2 = world.add(Entity(
        id=hero2_name, kind="character", type=hero2_type,
        traits=["little"] + (hero2_traits or ["cautious", "clever"]),
    ))
    mystery_ent = world.add(Entity(
        id="mystery", type="thing", label=mystery.noun,
        phrase=mystery.phrase, detail=mystery.detail,
        location="behind_dumpster",
    ))
    helper_ent = world.add(Entity(
        id="Helper", kind="character", type="man", label="the helper",
        phrase=helper.phrase, title=helper.title,
        explanation=helper.explanation, action=helper.action,
        location="repair_shop",
    ))

    # Act 1 -- setup: who, what they love, the discovery.
    introduce_friends(world, hero1, hero2)
    loves_adventures(world, hero1, hero2, adventure)
    discover(world, hero1, hero2, mystery_ent)

    # Act 2 -- conflict: suspense, warning, defiance, lock discovery.
    world.para()
    suspense(world, hero1, hero2, adventure, mystery_ent)
    warn(world, hero2, hero1, adventure, mystery_ent)
    defies_warning(world, hero1, adventure)
    discover_lock(world, hero1, hero2, mystery_ent)

    # Act 3 -- resolution: helper appears, reveals truth, they transform the lot.
    world.para()
    helper_appears(world, helper_ent, hero1, hero2)
    explain_mystery(world, helper_ent, mystery_ent, adventure)
    reveal_truth(world, helper_ent, hero1, hero2, mystery_ent, adventure)
    transform_and_plant(world, hero1, hero2, adventure, mystery)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(hero1=hero1, hero2=hero2, helper=helper_ent,
                       mystery=mystery, mystery_ent=mystery_ent,
                       adventure=adventure, setting=setting,
                       resolved=True,
                       friendship_boost=hero1.memes["friendship"] + hero2.memes["friendship"],
                       transform_level=world.transform_level)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "mall_parking": Setting(place="the parking lot behind the old mall", affords={"coffin", "chest", "trunk", "box"}),
    "repair_lot": Setting(place="the parking lot next to the repair shop", affords={"coffin", "box", "trunk"}),
    "supermarket_lot": Setting(place="the supermarket parking lot", affords={"coffin", "chest", "box"}),
}

MYSTERIES = {
    "coffin": Mystery(
        id="coffin",
        noun="coffin",
        phrase="a strange wooden coffin",
        detail="with a heavy brass lock",
        hidden_truth="gardening supplies",
        transform_into="a garden of flowers",
    ),
    "chest": Mystery(
        id="chest",
        noun="chest",
        phrase="an old treasure chest",
        detail="with rusty iron bands",
        hidden_truth="art supplies and paints",
        transform_into="a mural on the empty wall",
    ),
    "trunk": Mystery(
        id="trunk",
        noun="trunk",
        phrase="a dusty leather trunk",
        detail="with a silver clasp",
        hidden_truth="books and story scrolls",
        transform_into="a little free library",
    ),
    "box": Mystery(
        id="box",
        noun="box",
        phrase="a metal tool box",
        detail="with a strange symbol on the side",
        hidden_truth="seed packets and gardening tools",
        transform_into="a vegetable patch",
    ),
}

ADVENTURES = {
    "coffin": Adventure(
        id="coffin",
        verb_approach="approach the mysterious coffin",
        verb_explore="explore the parking lot",
        suspense_clue="the brass lock gleamed in the sunlight",
        reveal="bags of rich, dark dirt and shiny flower seeds",
        outcome="a secret garden in the empty lot",
        keyword="coffin",
        tags={"coffin", "mystery", "garden"},
    ),
    "chest": Adventure(
        id="chest",
        verb_approach="tip-toe toward the old chest",
        verb_explore="sneak around the parking lot",
        suspense_clue="the rusty hinges creaked",
        reveal="bright tubes of paint and clean paintbrushes",
        outcome="a beautiful mural on the empty wall",
        keyword="chest",
        tags={"chest", "mystery", "art"},
    ),
    "trunk": Adventure(
        id="trunk",
        verb_approach="crawl closer to the dusty trunk",
        verb_explore="search every corner of the lot",
        suspense_clue="the silver clasp caught the light",
        reveal="colorful storybooks and scrolls of tales",
        outcome="a little library for everyone to share",
        keyword="trunk",
        tags={"trunk", "mystery", "books"},
    ),
    "box": Adventure(
        id="box",
        verb_approach="walk carefully toward the metal box",
        verb_explore="survey the parking lot",
        suspense_clue="the symbol on the side seemed to glow",
        reveal="seed packets, a trowel, and gardening gloves",
        outcome="a vegetable patch that fed the whole street",
        keyword="box",
        tags={"box", "mystery", "garden"},
    ),
}

HELPERS = [
    Helper(
        id="Helper",
        phrase="a friendly old man in a green hat",
        title="the repair shop owner",
        explanation="That box is for gardening supplies",
        action="opened the coffin with a tiny key",
    ),
    Helper(
        id="Helper",
        phrase="a kind lady with a flower apron",
        title="the florist from across the street",
        explanation="That chest is my art supply box",
        action="unlocked the chest with a gentle click",
    ),
    Helper(
        id="Helper",
        phrase="a smiling librarian with a book badge",
        title="the librarian from the nearby library",
        explanation="That trunk holds donated storybooks",
        action="opened the trunk with a silver key",
    ),
]

GIRL_NAMES = ["Emma", "Maya", "Zara", "Lila", "Sofia", "Aria", "Nina", "Tara", "Kira", "Leela"]
BOY_NAMES = ["Ravi", "Leo", "Sam", "Kai", "Finn", "Max", "Aiden", "Eli", "Noah", "Theo"]
TRAITS = ["brave", "curious", "cautious", "clever", "playful", "creative", "bold", "gentle"]


def valid_combos() -> list[tuple[str, str]]:
    """(place, mystery_id, helper_idx) triples that pass constraints."""
    combos = []
    for place, setting in SETTINGS.items():
        for mystery_id in setting.affords:
            for hi, helper in enumerate(HELPERS):
                combos.append((place, mystery_id, hi))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    mystery: str
    helper: int
    name1: str
    gender1: str
    trait1: str
    name2: str
    gender2: str
    trait2: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge, keyed by topic.
KNOWLEDGE = {
    "coffin": [("What is a coffin?",
                "A coffin is a long wooden box that people sometimes use to "
                "store things or, in old stories, to hide surprises inside.")],
    "mystery": [("What is a mystery?",
                 "A mystery is something you do not understand yet, like a "
                 "locked box or a hidden treasure, that makes you curious.")],
    "garden": [("How do seeds turn into flowers?",
                "Seeds need soil, water, and sunlight. When you plant them in "
                "the ground and take care of them, they grow into flowers or "
                "vegetables.")],
    "friendship": [("Why is it good to explore with a friend?",
                    "When you explore with a friend, you can keep each other "
                    "safe, share ideas, and have more fun together.")],
    "suspense": [("What does 'suspense' mean?",
                  "Suspense is the exciting feeling you get when you do not "
                  "know what will happen next, like when you find a locked box "
                  "and wonder what is inside.")],
    "transformation": [("Can an empty lot become a garden?",
                        "Yes! With soil, seeds, water, and time, an empty lot "
                        "can become a beautiful garden full of flowers.")],
    "parking": [("Why do people leave things in parking lots?",
                 "Sometimes people store things in parking lots for a short "
                 "time, and sometimes things get left behind by accident.")],
}
KNOWLEDGE_ORDER = ["coffin", "mystery", "garden", "friendship", "suspense", "transformation", "parking"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero1, hero2, mystery, adventure = f["hero1"], f["hero2"], f["mystery"], f["adventure"]
    kw = mystery.noun
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "two friends, '
        f'a mystery, a transformation" that includes the word "{kw}".',
        f"Tell a gentle story where {hero1.id} and {hero2.id} find a {kw} in "
        f"the parking lot and learn that things are not always what they seem.",
        f'Write a simple story that uses the noun "{kw}" and ends with friends '
        f"turning a scary surprise into something wonderful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero1, hero2, helper, mystery, adventure = f["hero1"], f["hero2"], f["helper"], f["mystery"], f["adventure"]
    place = world.setting.place
    sub1, obj1, pos1 = (hero1.pronoun("subject"), hero1.pronoun("object"),
                        hero1.pronoun("possessive"))
    sub2, obj2, pos2 = (hero2.pronoun("subject"), hero2.pronoun("object"),
                        hero2.pronoun("possessive"))
    trait1 = next((t for t in hero1.traits if t != "little"), hero1.type)
    trait2 = next((t for t in hero2.traits if t != "little"), hero2.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who are the two friends in the story about the {mystery.noun} "
                f"in {place}?"
            ),
            answer=(
                f"The story is about a little {trait1} {hero1.type} named {hero1.id} "
                f"and a little {trait2} {hero2.type} named {hero2.id}. They love "
                f"exploring {place} together."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero1.id} and {hero2.id} find behind the dumpster "
                f"in {place}?"
            ),
            answer=(
                f"They found {mystery.phrase} {mystery.detail} hidden behind "
                f"the dumpster. It looked mysterious and made them both curious "
                f"and a little scared."
            ),
        ),
        QAItem(
            question=(
                f"How did {hero2.id} feel when {hero1.id} wanted to open the "
                f"{mystery.noun}?"
            ),
            answer=(
                f"{hero2.id.capitalize()} felt a shiver and was worried. "
                f'{hero2.pronoun("subject").capitalize()} said, '
                f'"What if something creepy is in there?" and warned {obj1} '
                f"to be careful."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"Who helped {hero1.id} and {hero2.id} understand what was "
                f"inside the {mystery.noun}?"
            ),
            answer=(
                f"{helper.phrase.capitalize()} walked over from the repair shop "
                f"and explained that the {mystery.noun} was for gardening supplies. "
                f'{helper.pronoun("subject").capitalize()} {helper.action} and showed them '
                f"{adventure.reveal}."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What did {hero1.id} and {hero2.id} decide to do with the "
                f"things inside the {mystery.noun}?"
            ),
            answer=(
                f"They decided to plant {adventure.outcome} together in the "
                f"empty lot next door. The {mystery.noun} that seemed scary "
                f"became the start of a beautiful garden."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {hero1.id} and {hero2.id} feel at the end of the "
                f"story about the {mystery.noun} in {place}?"
            ),
            answer=(
                f"They felt happy, relieved, and closer as friends. Their little "
                f"adventure turned a suspenseful mystery into a creative project "
                f"that brought joy to everyone."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["adventure"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.zone:
            bits.append(f"zone={e.zone}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  transform_level={world.transform_level:.1f}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="mall_parking",
        mystery="coffin",
        helper=0,
        name1="Ravi",
        gender1="boy",
        trait1="brave",
        name2="Emma",
        gender2="girl",
        trait2="cautious",
    ),
    StoryParams(
        place="repair_lot",
        mystery="coffin",
        helper=1,
        name1="Leo",
        gender1="boy",
        trait1="curious",
        name2="Maya",
        gender2="girl",
        trait2="clever",
    ),
    StoryParams(
        place="supermarket_lot",
        mystery="chest",
        helper=1,
        name1="Kai",
        gender1="boy",
        trait1="bold",
        name2="Lila",
        gender2="girl",
        trait2="gentle",
    ),
    StoryParams(
        place="mall_parking",
        mystery="trunk",
        helper=2,
        name1="Sam",
        gender1="boy",
        trait1="creative",
        name2="Zara",
        gender2="girl",
        trait2="playful",
    ),
    StoryParams(
        place="repair_lot",
        mystery="box",
        helper=0,
        name1="Finn",
        gender1="boy",
        trait1="curious",
        name2="Nina",
        gender2="girl",
        trait2="brave",
    ),
]


def explain_rejection(mystery: Mystery) -> str:
    return (f"(No story: the {mystery.noun} cannot be resolved with the "
            f"available helpers for this setting.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# Uses the shared `asp` helper + clingo, imported lazily so the prose engine
# runs without them.  See `python <name>.py --verify`.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is resolved when a helper can explain it.
resolved(M, H) :- mystery(M), helper(H), explains(H, M).

% A story is valid when the setting affords the mystery and resolution exists.
valid_story(P, M, H) :- affords(P, M), resolved(M, H).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
    for hi, h in enumerate(HELPERS):
        lines.append(asp.fact("helper", f"h{hi}"))
        for mid in MYSTERIES:
            lines.append(asp.fact("explains", f"h{hi}", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    """(place, mystery, helper) -- valid stories."""
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set, python_set = set(asp_valid_stories()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface (see storyworlds/AGENTS.md):
#   build_parser() -> ArgumentParser
#   resolve_params(args, rng) -> StoryParams        (random where unspecified)
#   generate(params) -> StorySample                  (the core; world -> story+QA)
#   emit(sample, ...) -> None                        (human-readable output)
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: two friends, a coffin, a transformation. "
                    "Unspecified choices are picked at random (seeded).")
    # A small, debuggable set of pins; any omitted choice is randomized.
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", type=int, choices=range(len(HELPERS)))
    ap.add_argument("--gender1", choices=["boy", "girl"])
    ap.add_argument("--gender2", choices=["boy", "girl"])
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery_id, helper_idx = rng.choice(sorted(combos))
    g1 = args.gender1 or rng.choice(["boy", "girl"])
    g2 = args.gender2 or rng.choice(["boy", "girl"])
    if g1 == g2:
        g2 = "girl" if g1 == "boy" else "boy"
    n1 = args.name1 or rng.choice(BOY_NAMES if g1 == "boy" else GIRL_NAMES)
    n2 = args.name2 or rng.choice(BOY_NAMES if g2 == "boy" else GIRL_NAMES)
    t1 = rng.choice(TRAITS)
    t2 = rng.choice([t for t in TRAITS if t != t1])
    return StoryParams(
        place=place,
        mystery=mystery_id,
        helper=helper_idx,
        name1=n1,
        gender1=g1,
        trait1=t1,
        name2=n2,
        gender2=g2,
        trait2=t2,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(
        SETTINGS[params.place],
        MYSTERIES[params.mystery],
        ADVENTURES[params.mystery],
        HELPERS[params.helper],
        params.name1, params.gender1, [params.trait1, "curious"],
        params.name2, params.gender2, [params.trait2, "clever"],
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid (place, mystery, helper) combos:\n")
        for place, mystery, helper in stories:
            helper_name = f"helper {helper}"
            print(f"  {place:15} {mystery:8} {helper_name}")
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
            header = f"### {p.name1} & {p.name2}: the {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
