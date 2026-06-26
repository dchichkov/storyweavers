#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/spectacular_squat_glisten_lesson_learned_transformation_pirate.py
================================================================================

A standalone *story world* sketch for a pirate tale in which a young cabin
child discovers a peculiar squat, glistening treasure on the sand, learns the
real lesson of being a pirate (and not just finding loot), and is transformed
by the choice he makes with it.

Initial story (used to build a world model):
---
Once upon a time, there was a small cabin boy named Finn who sailed aboard a
spectacular tall ship called the Glisten. The Glisten was a squat, heavy
little brig with patched sails, and she rocked and rolled as she chased the
silver dawns across the warm sea.

Finn was sure that being a pirate only meant finding treasure, and he was
sure the very best treasure was the shiny kind that glittered when you held
it up. One morning, after a storm had tossed the crew about like marbles in
a tin, the lookout called down that there was a small island just ahead,
and on the white sand lay something that made the whole ship hold its breath.

When the longboat scraped the beach, Finn splashed ashore first and found a
small squat chest, salt-crusted and heavy, with a copper lock that caught
the sun and seemed to glisten like a caught firefly. The captain, a one-eyed
woman called Mara with a parrot on her shoulder, warned the crew not to
touch it, but Finn, whose only rule was "shiny means mine," could not help
himself and pried the lock with his belt knife.

Inside, instead of gold, the chest held a single old book, a tarnished
compass, and a folded letter that began: "To whoever opens me -- the
treasure is not the chest. It is what you choose to do for your crew when
no one is watching." Finn frowned. That was not the kind of treasure he
had imagined at all.

That night a storm came back, fiercer than the first, and the longboat was
dashed against the rocks. The crew huddled under the patched awning, cold
and hungry, while the captain tried to mend the sail with shaking hands.
Finn, who now held the book and the compass in his arms, looked at the
sobbing parrot, at the tired captain, at the youngest sailor, little Pip,
who was shivering under a wet coat.

And so Finn made his choice. He did not keep the chest for himself. He
shared out the small rations fairly, he read aloud from the book by lantern
light so the crew had something warm to listen to, and he used the compass
to find the safe path back to the ship. By morning the storm had tired
itself out, the Glisten rode steady on the glassy sea, and the captain
placed a small brass star on Finn's collar. Finn had not found a chest of
gold, but he had found something better -- he had become the kind of pirate
the sea could trust. And from that day on, whenever a sailor asked him what
treasure was for, he would smile and say, "It is for the people you sail
with."

Causal state updates:
---
    see_chest(actor)            -> actor.greed   += 1
    touch_chest(actor)          -> actor.risk    += 1
    open_chest(actor)           -> actor.lesson  += 1
    open_chest(actor)           -> actor.knowledge += 1   (the letter, the book)
    share_with_crew(actor)      -> actor.kindness += 1
    share_with_crew(actor)      -> crew.trust    += 1
    navigate_home(actor)        -> actor.skill    += 1
    navigate_home(actor)        -> crew.safety    += 1
    captain_reward(actor)       -> actor.rank     += 1  (brass star)

Scripted social/emotional beats:
---
    captain_warned + child_touched -> crew.tension += 1     (a rule was broken)
    night_storm                    -> crew.fear    += 1
    child_kind_choice              -> crew.trust   -> max ; actor.greed -> 0
    child_kind_choice              -> actor.transformation += 1  (a real change)
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
# (``python .../spectacular_squat_glisten_lesson_learned_transformation_pirate.py``):
# add the package dir (storyworlds/) to the path so ``results`` resolves
# regardless of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # cabin_boy, captain, parrot, chest, ...
    label: str = ""                # short reference, e.g. "the captain"
    phrase: str = ""               # full noun phrase, e.g. "a squat salt-crusted chest"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "captain", "mother", "mom"}
        male = {"boy", "man", "cabin_boy", "father", "dad", "pirate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom", "father": "dad",
            "cabin_boy": "the cabin boy",
            "captain": "the captain",
            "parrot": "the parrot",
            "sailor": "the sailor",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the white sand beach"
    weather: str = "after a storm"        # "after a storm" | "sunny" | "stormy night"
    sea: str = "the warm sea"              # flavour text only
    ship_name: str = "the Glisten"


@dataclass
class Treasure:
    """The glistening squat thing on the sand."""
    id: str
    label: str            # "chest", "crate", "bundle"
    shape: str            # "squat", "long", "round"
    cover: str            # "salt-crusted", "mossy", "tarnished"
    lock: str             # "copper lock", "iron clasp", "rope tie"
    contents: str         # physical summary, used for narration: "a book, a compass, a letter"


@dataclass
class Lesson:
    """The kind of choice the cabin boy can make with the contents of the chest."""
    id: str
    verb: str            # "share the rations and read the book aloud"
    result: str          # "the crew huddled warm and hopeful until morning"
    shared_kind: str     # "shared out the small rations fairly"


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()       # idempotency for the rule engine
        self.paragraphs: list[list[str]] = [[]]
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


def _crew_total(world: World, key: str) -> float:
    """Sum a meme across every crew member who isn't the cabin boy."""
    return sum(e.memes[key] for e in world.characters() if e.type != "cabin_boy")


def _crew_set(world: World, key: str, value: float) -> None:
    for e in world.characters():
        if e.type != "cabin_boy":
            e.memes[key] = value


def _r_tension(world: World) -> list[str]:
    """A warned chest, touched by the cabin boy -> crew tension rises."""
    if "tension" in {n for (n, *_) in world.fired}:
        return []
    boy = next((e for e in world.characters() if e.type == "cabin_boy"), None)
    if not boy:
        return []
    if boy.meters["risk"] < THRESHOLD:
        return []
    sig = ("tension", boy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _crew_set(world, "tension", _crew_total(world, "tension") + 1)
    return [f"The crew held its breath as the lock clicked open."]


def _r_kind_clears_greed(world: World) -> list[str]:
    """If the boy chose the kind action, his greed falls to 0."""
    boy = next((e for e in world.characters() if e.type == "cabin_boy"), None)
    if not boy:
        return []
    if boy.memes["kindness"] < THRESHOLD:
        return []
    sig = ("clear_greed", boy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boy.memes["greed"] = 0.0
    return [f"The greed that had tugged at him fell quiet, like a wave pulling back."]


def _r_kind_clears_tension(world: World) -> list[str]:
    """If the boy chose the kind action, the crew tension falls to 0."""
    boy = next((e for e in world.characters() if e.type == "cabin_boy"), None)
    if not boy:
        return []
    if boy.memes["kindness"] < THRESHOLD:
        return []
    sig = ("clear_tension", boy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _crew_set(world, "tension", 0.0)
    boy.memes["transformation"] += 1
    return [f"The crew looked at him differently now -- not as the boy who broke the rule, but as the boy who mended it."]


def _r_rank_rises(world: World) -> list[str]:
    """captain_reward + kindness + skill -> the boy's rank rises."""
    boy = next((e for e in world.characters() if e.type == "cabin_boy"), None)
    cap = next((e for e in world.characters() if e.type == "captain"), None)
    if not (boy and cap):
        return []
    if boy.meters["rank"] < THRESHOLD:
        return []
    sig = ("rank", boy.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    boy.memes["rank"] += 1
    return [f"The captain pinned a small brass star to {boy.id}'s collar."]


CAUSAL_RULES: list[Rule] = [
    Rule(name="tension", tag="social", apply=_r_tension),
    Rule(name="clear_greed", tag="social", apply=_r_kind_clears_greed),
    Rule(name="clear_tension", tag="social", apply=_r_kind_clears_tension),
    Rule(name="rank", tag="social", apply=_r_rank_rises),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* story.
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    """(place_id, treasure_id, lesson_id, gender) -- the gated space."""
    out = []
    for place_id, s in SETTINGS.items():
        if not s.affords_storm:
            continue
        for tid in TREASURE_IDS_FOR_PLACE.get(place_id, []):
            for lid, lesson in LESSONS.items():
                if lesson.id == "share":
                    out.append((place_id, tid, lid, "boy"))
    return out


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_detail(setting: Setting) -> str:
    if setting.weather == "after a storm":
        return (f"The {setting.sea} had calmed itself, and the air still smelled "
                f"of rain and warm wood.")
    if setting.weather == "sunny":
        return f"The {setting.sea} was a bright, flat sheet, and the sun sat high."
    return f"The {setting.sea} was dark and rolling, and the wind pulled at every rope."


def introduce(world: World, hero: Entity, ship: Entity, setting: Setting) -> None:
    trait = next((t for t in hero.traits if t not in {"little", "cabin"}), "cheerful")
    world.say(
        f"{hero.id} was a {trait} little cabin boy who sailed aboard "
        f"{ship.phrase}, a spectacular tall ship called {setting.ship_name}."
    )
    world.say(
        f"{setting.ship_name} was a squat, heavy little brig with patched sails, "
        f"and she rocked and rolled as she chased the silver dawns across "
        f"{setting.sea}."
    )


def loves_treasure(world: World, hero: Entity) -> None:
    hero.memes["greed"] += 1
    world.say(
        f"{hero.id} was sure that being a pirate only meant finding treasure, "
        f"and he was sure the very best treasure was the shiny kind that "
        f"glittered when you held it up."
    )


def arrive(world: World, setting: Setting, treasure: Treasure) -> None:
    day = {"after a storm": "One morning, after a storm had tossed the crew about like marbles in a tin, ",
           "sunny": "One bright morning, ",
           "stormy night": "When the sky had gone purple and the sails began to snap, "}.get(
        setting.weather, "One day, ")
    world.say(
        f"{day}the lookout called down that there was a small island just "
        f"ahead, and on the white sand lay something that made the whole ship "
        f"hold its breath."
    )


def beach_landing(world: World, hero: Entity, treasure: Treasure) -> None:
    world.say(
        f"When the longboat scraped the beach, {hero.id} splashed ashore first "
        f"and found a small {treasure.shape} {treasure.label}, {treasure.cover} "
        f"and heavy, with a {treasure.lock} that caught the sun and seemed to "
        f"glisten like a caught firefly."
    )


def captain_warn(world: World, hero: Entity, treasure: Treasure) -> None:
    cap = world.get("Captain")
    world.say(
        f"The captain, a one-eyed woman with a parrot on her shoulder, warned "
        f"the crew not to touch the {treasure.label}, but {hero.id}, whose only "
        f"rule was \"shiny means mine,\" could not help himself and pried the "
        f"{treasure.lock.split(' ', 1)[-1]} with his belt knife."
    )


def open_chest(world: World, hero: Entity, treasure: Treasure) -> None:
    hero.meters["risk"] += 1
    hero.memes["lesson"] += 1
    hero.memes["knowledge"] += 1
    propagate(world, narrate=False)         # fires the risk->tension rule
    world.say(
        f"Inside, instead of gold, the {treasure.label} held {treasure.contents}. "
        f"The folded letter began: \"To whoever opens me -- the treasure is not "
        f"the {treasure.label}. It is what you choose to do for your crew when "
        f"no one is watching.\""
    )
    world.say(
        f"{hero.id} frowned. That was not the kind of treasure he had imagined at all."
    )


def night_storm(world: World, setting: Setting) -> None:
    world.say(
        f"That night the wind came back harder, and the longboat was dashed "
        f"against the rocks. The crew huddled under the patched awning, cold "
        f"and hungry, while the captain tried to mend the sail with shaking hands."
    )


def hard_choice(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id}, who now held the book and the compass in his arms, looked "
        f"at the tired captain, at the youngest sailor who was shivering under "
        f"a wet coat, and at the small parrot that would not stop muttering."
    )
    world.say(
        f"And so {hero.id} made his choice."
    )


def choose_kind(world: World, hero: Entity, lesson: Lesson) -> None:
    hero.memes["kindness"] += 1
    hero.memes["skill"] += 1
    _crew_set(world, "trust", _crew_total(world, "trust") + 1)
    _crew_set(world, "safety", _crew_total(world, "safety") + 1)
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} did not keep the chest for himself. He {lesson.verb}, and "
        f"by morning {lesson.result}."
    )


def captain_reward(world: World, hero: Entity, setting: Setting) -> None:
    hero.meters["rank"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The captain placed a small brass star on {hero.id}'s collar and said "
        f"that {hero.id} had not found a chest of gold, but something better -- "
        f"he had become the kind of pirate the sea could trust."
    )


def ending_image(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"From that day on, whenever a sailor asked {hero.id} what treasure "
        f"was for, he would smile and say, \"It is for the people you sail "
        f"with,\" and {setting.ship_name} would lean into the wind as if she "
        f"agreed."
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, treasure: Treasure, lesson: Lesson,
         hero_name: str = "Finn", hero_type: str = "cabin_boy",
         hero_traits: Optional[list[str]] = None,
         captain_type: str = "captain") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "cabin"] + (hero_traits or ["cheerful", "stubborn"]),
    ))
    ship = world.add(Entity(
        id="ship", kind="thing", type="ship", label="ship",
        phrase=f"a spectacular tall ship called {setting.ship_name}",
        plural=False,
    ))
    captain = world.add(Entity(
        id="Captain", kind="character", type=captain_type,
        label="the captain", phrase="a one-eyed captain with a parrot on her shoulder",
    ))
    parrot = world.add(Entity(
        id="Parrot", kind="thing", type="parrot", label="the parrot",
        phrase="a small parrot on the captain's shoulder",
    ))
    chest = world.add(Entity(
        id=treasure.id, kind="thing", type="chest", label=treasure.label,
        phrase=f"a {treasure.shape} {treasure.cover} {treasure.label}",
    ))

    # Act 1 -- setup: the ship, the boy, his shiny rule, the island.
    introduce(world, hero, ship, setting)
    loves_treasure(world, hero)
    world.para()
    arrive(world, setting, treasure)
    beach_landing(world, hero, treasure)

    # Act 2 -- conflict: the captain's warning, the opened chest, the storm.
    world.para()
    captain_warn(world, hero, treasure)
    open_chest(world, hero, treasure)
    world.para()
    night_storm(world, setting)
    hard_choice(world, hero)

    # Act 3 -- resolution: a kind choice, the captain's reward, the ending image.
    world.para()
    choose_kind(world, hero, lesson)
    captain_reward(world, hero, setting)
    ending_image(world, hero, setting)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        hero=hero, captain=captain, parrot=parrot, ship=ship, chest=chest,
        treasure=treasure, lesson=lesson, setting=setting,
        conflict=hero.meters["risk"] >= THRESHOLD,
        resolved=hero.memes["kindness"] >= THRESHOLD,
        transformation=hero.memes["transformation"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "beach": Setting(
        place="the white sand beach",
        weather="after a storm",
        sea="the warm sea",
        ship_name="the Glisten",
    ),
    "cove": Setting(
        place="the hidden cove",
        weather="sunny",
        sea="the glassy bay",
        ship_name="the Salt Lily",
    ),
    "reef": Setting(
        place="the bone-white reef",
        weather="stormy night",
        sea="the black rolling sea",
        ship_name="the Squat Crow",
    ),
}


@dataclass
class SettingR:
    """Auxiliary: which settings even support a glistening find + a storm."""
    affords_storm: bool = False


# Mirror SETTINGS with an auxiliary affordance table so the ASP gate can use it.
SETTING_AFFORDS = {
    "beach": True,
    "cove": True,
    "reef": True,
}


TREASURES = {
    "chest": Treasure(
        id="chest",
        label="chest",
        shape="squat",
        cover="salt-crusted",
        lock="copper lock",
        contents="a book, a tarnished compass, and a folded letter",
    ),
    "crate": Treasure(
        id="crate",
        label="crate",
        shape="squat",
        cover="mossy",
        lock="iron clasp",
        contents="an old book, a brass key, and a folded letter",
    ),
    "bundle": Treasure(
        id="bundle",
        label="bundle",
        shape="squat",
        cover="tarnished",
        lock="rope tie",
        contents="a book, a compass, and a folded letter",
    ),
}


TREASURE_IDS_FOR_PLACE = {
    "beach": ["chest", "crate", "bundle"],
    "cove": ["chest", "crate"],
    "reef": ["chest", "bundle"],
}


LESSONS = {
    "share": Lesson(
        id="share",
        verb="shared out the small rations fairly, read the book aloud by "
             "lantern light, and used the compass to find the safe path back "
             "to the ship",
        result="the storm had tired itself out and the crew was warm and hopeful",
        shared_kind="shared out the small rations fairly",
    ),
}


BOY_NAMES = ["Finn", "Pip", "Tom", "Jago", "Coby", "Reef", "Sail", "Brin"]
TRAITS = ["cheerful", "curious", "stubborn", "spirited", "lively"]


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    treasure: str
    lesson: str
    name: str
    gender: str
    captain_kind: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "treasure": [("What is treasure?",
                  "Treasure is something valuable that people look for and "
                  "keep safe, like gold, gems, or even an old book that "
                  "teaches you something important.")],
    "pirate": [("What is a pirate?",
                "A pirate is a sailor who lives by working on a ship, and "
                "who follows the rules of the sea and of their crew.")],
    "ship": [("What is a ship?",
              "A ship is a big boat with sails that carries people across "
              "the sea for adventures, trading, or exploration.")],
    "compass": [("What does a compass do?",
                 "A compass is a small tool with a needle that points north, "
                 "and it helps a sailor find the right way across the sea.")],
    "storm": [("What is a storm at sea?",
               "A storm at sea is when the wind blows very hard, the waves "
               "grow tall, and the rain comes down in sheets.")],
    "crew": [("What is a crew?",
              "A crew is the team of sailors who work together on a ship, "
              "each doing a different job to keep the ship safe.")],
    "lesson": [("What is a lesson?",
                "A lesson is something you learn, often by making a choice "
                "and then seeing what that choice does to the people "
                "around you.")],
    "transformation": [("What is a transformation?",
                        "A transformation is a real change inside a person, "
                        "so that the way they act and the way they think "
                        "becomes a better thing than it was before.")],
    "honest": [("What does it mean to be honest?",
                "Being honest means telling the truth and doing the right "
                "thing, even when no one is watching you do it.")],
}
KNOWLEDGE_ORDER = ["pirate", "ship", "crew", "treasure", "compass",
                   "storm", "lesson", "transformation", "honest"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, treasure, lesson, setting = (f["hero"], f["treasure"], f["lesson"], f["setting"])
    kw = "glisten"
    return [
        f'Write a short pirate story for a 4-to-7-year-old on the theme of '
        f'"finding real treasure" that uses the word "{kw}".',
        f"Tell a gentle pirate tale where a young cabin boy named {hero.id} "
        f"finds a {treasure.cover} {treasure.label} on {setting.place}, opens "
        f"it, and learns that the real treasure is how he chooses to treat his "
        f"crew after the storm.",
        f"Write a simple pirate story that uses the noun \"{kw}\" and ends "
        f"with the cabin boy giving the loot away so his crew can be safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, captain, treasure, lesson, setting = (f["hero"], f["captain"], f["treasure"],
                                                 f["lesson"], f["setting"])
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = setting.place
    ship = setting.ship_name
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} sails aboard {ship} and "
                f"finds the glistening treasure on {place}?"
            ),
            answer=(
                f"It is about a small cabin boy named {hero.id} who sails "
                f"aboard {ship}, a spectacular tall ship, and who finds a "
                f"{treasure.cover} {treasure.label} on {place} one morning."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id} believe a pirate was for before he opened "
                f"the {treasure.label} on {place}?"
            ),
            answer=(
                f"{hero.id} believed that being a pirate only meant finding "
                f"shiny treasure and keeping it for {obj}self, so the rule he "
                f"lived by was \"shiny means mine.\""
            ),
        ),
        QAItem(
            question=(
                f"What was inside the glistening {treasure.label} when {hero.id} "
                f"pried it open on {place}?"
            ),
            answer=(
                f"Inside the {treasure.label} was {treasure.contents}, and the "
                f"letter inside said the real treasure was what {hero.id} chose "
                f"to do for his crew when no one was watching."
            ),
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=(
                f"Why did the captain on {ship} tell the crew not to touch the "
                f"glistening {treasure.label} before {hero.id} opened it?"
            ),
            answer=(
                f"The captain warned the crew not to touch the {treasure.label} "
                f"because she is the one-eyed leader of {ship} and she did not "
                f"yet know what was inside; she wanted to keep her crew safe "
                f"first, but {hero.id}'s rule \"shiny means mine\" pulled him "
                f"in anyway."
            ),
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did {hero.id} use the things from the {treasure.label} to "
                f"help his crew on {ship} during the storm at {place}?"
            ),
            answer=(
                f"{hero.id} {lesson.verb}. The book gave the crew something "
                f"warm to listen to, the compass helped him find the safe path "
                f"back to {ship}, and the small rations were shared so no one "
                f"went hungry."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What did the captain of {ship} do for {hero.id} after the "
                f"storm on {place} because of his kind choice?"
            ),
            answer=(
                f"The captain pinned a small brass star on {hero.id}'s collar "
                f"and told him he had not found a chest of gold, but something "
                f"better -- he had become the kind of pirate the sea could trust."
            ),
        ))
    if f.get("transformation"):
        qa.append(QAItem(
            question=(
                f"How did {hero.id} change by the end of the storm on {place} "
                f"after he shared the loot from the glistening {treasure.label}?"
            ),
            answer=(
                f"{hero.id} was transformed. The greed that had tugged at him "
                f"fell quiet, his crew trusted him again, and he understood "
                f"that real treasure is what you do for the people you sail with."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="beach",
        treasure="chest",
        lesson="share",
        name="Finn",
        gender="boy",
        captain_kind="captain",
        trait="cheerful",
    ),
    StoryParams(
        place="cove",
        treasure="crate",
        lesson="share",
        name="Pip",
        gender="boy",
        captain_kind="captain",
        trait="curious",
    ),
    StoryParams(
        place="reef",
        treasure="bundle",
        lesson="share",
        name="Jago",
        gender="boy",
        captain_kind="captain",
        trait="spirited",
    ),
]


def explain_rejection(place: str, treasure_id: str, lesson_id: str) -> str:
    if place not in SETTINGS:
        return f"(No story: '{place}' is not a known island in this tale.)"
    if treasure_id not in TREASURE_IDS_FOR_PLACE.get(place, []):
        return (f"(No story: a glistening {treasure_id} is not the kind of find "
                f"that washes up at {place}; try one of "
                f"{sorted(TREASURE_IDS_FOR_PLACE.get(place, []))}.)")
    if lesson_id != "share":
        return (f"(No story: '{lesson_id}' is not a real lesson for the cabin "
                f"boy here; the only valid lesson is 'share'.)")
    return "(No story: this combination does not satisfy the story gate.)"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of valid_combos().  The rules
# are inline below; the facts are generated from the registries above so the
# two can never drift.  Uses the shared ``asp`` helper + clingo, imported
# lazily so the prose engine runs without them.  See ``--verify``.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting can host a storm + a glistening find.
can_storm(Place) :- setting(Place), affords_storm(Place).

% The find at a setting must be the right kind of treasure for that setting.
find_at(Place, T) :- can_storm(Place), treasure(T), allowed(Place, T).

% The lesson must be the kind of lesson a cabin boy can carry out.
valid_lesson(L) :- lesson(L), kind_lesson(L).

% A story is valid when its place can storm, it has a find, and the lesson fits.
valid(Place, T, L) :- find_at(Place, T), valid_lesson(L).
valid_story(Place, T, L, boy) :- valid(Place, T, L).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("setting_place", pid, s.place))
        lines.append(asp.fact("setting_sea", pid, s.sea))
        lines.append(asp.fact("setting_ship", pid, s.ship_name))
        lines.append(asp.fact("setting_weather", pid, s.weather))
    for pid, ok in SETTING_AFFORDS.items():
        if ok:
            lines.append(asp.fact("affords_storm", pid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("treasure_shape", tid, t.shape))
        lines.append(asp.fact("treasure_cover", tid, t.cover))
        lines.append(asp.fact("treasure_lock", tid, t.lock))
        lines.append(asp.fact("treasure_contents", tid, t.contents))
    for place, ids in TREASURE_IDS_FOR_PLACE.items():
        for tid in ids:
            lines.append(asp.fact("allowed", place, tid))
    for lid, lesson in LESSONS.items():
        lines.append(asp.fact("lesson", lid))
        if lesson.id == "share":
            lines.append(asp.fact("kind_lesson", lid))
        lines.append(asp.fact("lesson_verb", lid, lesson.verb))
        lines.append(asp.fact("lesson_result", lid, lesson.result))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): (place, treasure, lesson) triples."""
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    """(place, treasure, lesson, gender) -- gender-aware compatible stories."""
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_combos() -> list[tuple[str, str, str]]:
    """The Python mirror of the ASP gate -- (place, treasure, lesson) triples."""
    out = []
    for place, affords in SETTING_AFFORDS.items():
        if not affords:
            continue
        for tid in TREASURE_IDS_FOR_PLACE.get(place, []):
            for lid, lesson in LESSONS.items():
                if lesson.id == "share":
                    out.append((place, tid, lid))
    return sorted(set(out))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with python_valid_combos()."""
    clingo_set, python_set = set(asp_valid_combos()), set(python_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python_valid_combos() "
              f"({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python_valid_combos():")
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
        description="Story world sketch: a cabin boy, a glistening squat "
                    "chest, a lesson learned, a transformation. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--treasure", choices=list(TREASURES))
    ap.add_argument("--lesson", choices=list(LESSONS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy"])
    ap.add_argument("--captain-kind", choices=["captain"])
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
                    help="check the inline ASP gate matches python_valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the *explicit* options describe an invalid story."""
    if args.place and args.treasure and args.lesson:
        if (args.place, args.treasure, args.lesson) not in python_valid_combos():
            raise StoryError(explain_rejection(args.place, args.treasure, args.lesson))

    combos = [c for c in python_valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.treasure is None or c[1] == args.treasure)
              and (args.lesson is None or c[2] == args.lesson)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, treasure_id, lesson_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        treasure=treasure_id,
        lesson=lesson_id,
        name=name,
        gender="boy",
        captain_kind="captain",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(SETTINGS[params.place], TREASURES[params.treasure],
                 LESSONS[params.lesson], params.name, "cabin_boy",
                 [params.trait, "stubborn"], params.captain_kind)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, treasure, lesson) combos "
              f"({len(stories)} with gender):\n")
        for place, treasure_id, lesson_id in triples:
            genders = sorted(g for (pl, t, l, g) in stories
                             if (pl, t, l) == (place, treasure_id, lesson_id))
            print(f"  {place:6} {treasure_id:7} {lesson_id:6}  "
                  f"[{', '.join(genders)}]")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2,
                             ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (f"### {p.name}: {p.lesson} the {p.treasure} at "
                      f"{p.place}")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
