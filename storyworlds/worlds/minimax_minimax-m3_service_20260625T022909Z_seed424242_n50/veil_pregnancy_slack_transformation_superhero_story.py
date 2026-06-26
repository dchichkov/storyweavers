#!/usr/bin/env python3
"""
storyworlds/worlds/veil_pregnancy_slack_transformation_superhero_story.py
=======================================================================

A standalone *story world* sketch for "The Crystal Veil" tale -- a TinyStories
flavored superhero-style origin.  The seed asked for a small domain that
combines *veil*, *pregnancy*, and *slack* through a Transformation arc, written
in a warm Superhero Story register.

Initial story (used to build the world model):
---
Mira had a soft blue veil that her mother had hemmed for her, and the veil was
so light it slipped a finger of slack whenever she pulled it tight.  Mira's
mother was also expecting a baby, and the house felt full of small waiting
hushes.  Mira wanted to be a hero, but the world said she was too little.

One grey morning a glow slipped through the veil and brushed Mira's cheek.
The slack tightened all by itself, the cloth shimmered, and Mira felt her
hands hum.  The veil had chosen her.  Now the slack that once slipped through
her fingers became a taut, glowing cord she could throw.  She twirled the cord,
the veil became a cape, and Mira flew to help a lost kitten down from a roof.

She came home still wearing the cape, and her mother smiled and said the new
baby would have a brave sister.  The veil hung from the hook by the door,
shimmering softly, ready for the next time it was needed.

Causal state updates:
---
    wear veil                -> hero.bond += 1 ; veil.bond += 1
    slack slips              -> hero.frustration += 1 ; veil.slack += 1
    veil glow + slack slips  -> trigger Transformation (hero.transformed -> true,
                                veil.becomes("cord"), veil.becomes("cape"))
    hero transformed         -> hero.courage += 1 ; hero.helpful += 1
    good deed                -> hero.pride += 1 ; world.saved += 1
    mother waiting           -> family.anticipation += 1 ; mother.tiredness += 1
    baby mentioned           -> family.excitement += 1

The arc follows three beats: setup (the loose veil, the expecting mother), the
Transformation trigger (slack + glow), and the resolution (a small heroic deed
that proves the change happened).  All prose is driven by the simulated state
below; the renderer never just swaps nouns in a single paragraph.
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
# (``python storyworlds/worlds/<this>.py``): add the package dir (storyworlds/)
# to the path so ``results`` resolves regardless of the current directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Threshold at which an accumulated meter/meme is "embedded enough" to be
# narrated (mirrors the puddles.py convention).
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"               # "character" | "thing"
    type: str = "thing"               # girl, mother, veil, kitten, cape, cord ...
    label: str = ""                   # short reference, e.g. "veil"
    phrase: str = ""                  # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    state: str = ""                   # current shape (for the veil: "cloth"/"cord"/"cape")
    moods: set[str] = field(default_factory=set)   # visible emotional tags
    plural: bool = False              # "kittens" -> them, "veil" -> it
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "cat", "kitten", "queen"}
        male = {"boy", "father", "dad", "man", "king", "kingcat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    """Where the hero lives; mostly a flavor hook."""
    place: str = "a quiet little town"
    weather: str = "grey"            # "grey" | "sunny" | "rainy"


@dataclass
class VeilColor:
    """The hero's signature cloth; each color tints the glow and the cape tail."""
    name: str            # "blue", "silver", "violet", "gold"
    glow: str            # "soft blue", "pale silver", "violet shimmer", "warm gold"
    cape_phrase: str     # how the transformed cape is described


@dataclass
class GoodDeed:
    """A small rescue the hero pulls off after the Transformation."""
    id: str
    who: str            # "a lost kitten", "a trembling puppy", "a stuck sparrow"
    where: str          # "the church roof", "the old oak", "the garden shed"
    action: str         # verb phrase: "carry it gently back to its mother"
    mood: str           # "soft", "wobbly", "wide-eyed"
    twirl: str          # what twirling the cord does narratively


@dataclass
class GoodDeedCatalog:
    """The registry of plausible GoodDeeds; selected by the story RNG."""
    items: dict[str, GoodDeed]


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        """Throwaway clone for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]           # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_bond_grows(world: World) -> list[str]:
    """Wearing the veil increases both the hero's and the veil's bond."""
    for hero in world.characters():
        if hero.type in {"girl", "boy"} and hero.memes["bond"] >= THRESHOLD:
            veil = world.get("veil")
            if veil.meters["bond"] >= THRESHOLD:
                continue
            sig = ("bond", hero.id, veil.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            veil.meters["bond"] += 1
    return []


def _r_slack_pressure(world: World) -> list[str]:
    """Each slip of slack pushes the Transformation closer."""
    veil = world.entities.get("veil")
    if not veil:
        return []
    if veil.meters["slack"] < THRESHOLD:
        return []
    if veil.meters["pressure"] >= THRESHOLD:
        return []
    sig = ("pressure", veil.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    veil.meters["pressure"] += 1
    return []


def _r_transformation(world: World) -> list[str]:
    """Glow + slack slip together trigger the Transformation."""
    veil = world.entities.get("veil")
    if not veil or veil.meters["transformed"] >= THRESHOLD:
        return []
    if veil.meters["glow"] < THRESHOLD or veil.meters["slack"] < THRESHOLD:
        return []
    if veil.meters["pressure"] < THRESHOLD:
        return []
    sig = ("transform", veil.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    veil.meters["transformed"] += 1
    # The veil remembers its new shapes, so the renderer can describe them.
    veil.moods.add("cord")
    veil.moods.add("cape")
    hero = next((h for h in world.characters() if h.type in {"girl", "boy"}), None)
    if hero:
        hero.memes["courage"] += 1
        hero.memes["helpful"] += 1
        hero.memes["transformed"] = 1.0
    return ["__transform__"]              # marker; narrated by the screenplay beat


def _r_deed_pride(world: World) -> list[str]:
    """A completed good deed raises the hero's pride."""
    hero = next((h for h in world.characters() if h.type in {"girl", "boy"}), None)
    if not hero:
        return []
    if hero.memes["deed"] < THRESHOLD or hero.memes["pride"] >= THRESHOLD:
        return []
    sig = ("pride", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["pride"] += 1
    world.facts["saved"] = hero.memes["deed"]
    return []


def _r_mother_tired(world: World) -> list[str]:
    """The mother's tiredness is part of the home tone."""
    mother = next((c for c in world.characters() if c.type == "mother"), None)
    if not mother:
        return []
    if mother.meters["expecting"] < THRESHOLD or mother.meters["tiredness"] >= THRESHOLD:
        return []
    sig = ("tired", mother.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mother.meters["tiredness"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="bond", tag="physical", apply=_r_bond_grows),
    Rule(name="slack_pressure", tag="physical", apply=_r_slack_pressure),
    Rule(name="transformation", tag="magic", apply=_r_transformation),
    Rule(name="deed_pride", tag="social", apply=_r_deed_pride),
    Rule(name="mother_tired", tag="social", apply=_r_mother_tired),
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
                produced.extend(s for s in sents if s != "__transform__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Prediction helpers.
# ---------------------------------------------------------------------------
def predict_transformed(world: World) -> bool:
    """Will the Transformation trigger if the hero keeps wearing the veil?"""
    sim = world.copy()
    veil = sim.get("veil")
    veil.meters["glow"] += 1
    veil.meters["slack"] += 1
    veil.meters["pressure"] += 1
    propagate(sim, narrate=False)
    return sim.get("veil").meters["transformed"] >= THRESHOLD


def predict_pride(world: World) -> bool:
    """Would a completed good deed raise the hero's pride?"""
    sim = world.copy()
    hero = next((h for h in sim.characters() if h.type in {"girl", "boy"}), None)
    if not hero:
        return False
    hero.memes["deed"] += 1
    propagate(sim, narrate=False)
    return hero.memes["pride"] >= THRESHOLD


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    if setting.weather == "sunny":
        return f"The sky above {setting.place} was bright, and the windows caught the light."
    if setting.weather == "rainy":
        return f"Rain tapped softly on the roof above {setting.place}, and the lamps were warm."
    return f"The morning above {setting.place} was grey and quiet, and the lamps were just coming on."


def introduce(world: World, hero: Entity, mother: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "lively")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"{hero.id} was a {desc} who lived with {hero.pronoun('possessive')} "
        f"mother in {world.setting.place}."
    )


def veil_worn(world: World, hero: Entity, veil: Entity, color: VeilColor) -> None:
    hero.memes["bond"] += 1
    veil.meters["bond"] += 1
    world.say(
        f"{hero.pronoun('possessive').capitalize()} mother had hemmed a "
        f"{color.name} veil just for {hero.pronoun('object')}, and {hero.id} "
        f"wore it like a soft badge of courage."
    )


def mother_expecting(world: World, mother: Entity) -> None:
    mother.meters["expecting"] += 1
    mother.memes["anticipation"] += 1
    world.say(
        f"{mother.id} was also expecting a baby, so the house felt gentle and a "
        f"little full of waiting."
    )


def slack_notice(world: World, hero: Entity, veil: Entity, color: VeilColor) -> None:
    veil.meters["slack"] += 1
    hero.memes["frustration"] += 1
    world.say(
        f"But the veil was so light it slipped a finger of slack whenever "
        f"{hero.id} pulled it tight, and {hero.pronoun()} couldn't quite grip "
        f"the {color.name} cloth the way a hero should."
    )


def hero_wishes(world: World, hero: Entity) -> None:
    hero.memes["wish"] += 1
    world.say(
        f"{hero.id} wanted to be a hero, but the world said {hero.pronoun()} "
        f"was too little, and that made {hero.pronoun('object')} frown."
    )


def glow_appears(world: World, hero: Entity, veil: Entity, color: VeilColor) -> None:
    veil.meters["glow"] += 1
    world.say(
        f"One {world.setting.weather} morning a {color.glow} slipped through "
        f"the veil and brushed {hero.pronoun('possessive')} cheek."
    )


def transformation_beats(world: World, hero: Entity, veil: Entity, color: VeilColor) -> None:
    """The Transformation: slack tightens, veil becomes cord, then cape."""
    veil.meters["transformed"] += 1
    hero.memes["courage"] += 1
    hero.memes["helpful"] += 1
    hero.memes["transformed"] = 1.0
    propagate(world, narrate=False)         # let the rules mark the new shapes
    world.say(
        f"The slack tightened all by itself, and the cloth shimmered. "
        f"The veil had chosen {hero.id}."
    )
    world.say(
        f"Now the slack that once slipped through {hero.pronoun('possessive')} "
        f"fingers became a taut {color.glow} cord, and when {hero.pronoun()} "
        f"twirled it, the cord unfurled into {color.cape_phrase}."
    )


def hero_flies(world: World, hero: Entity, veil: Entity, deed: GoodDeed) -> None:
    """The cape carries the hero to the deed."""
    veil.meters["flown"] += 1
    world.say(
        f"With one brave hop, {hero.id} was up and over the rooftops, the "
        f"cape streaming behind {hero.pronoun('object')} like a small banner."
    )


def hero_rescues(world: World, hero: Entity, deed: GoodDeed) -> None:
    """The completed good deed (a small, kind rescue)."""
    hero.memes["deed"] += 1
    world.say(
        f"{hero.id} found {deed.who} on {deed.where}, {deed.mood} and unsure. "
        f"{hero.pronoun().capitalize()} twirled the cord once more -- {deed.twirl} -- "
        f"and {deed.action}."
    )
    propagate(world, narrate=False)         # raises hero.pride


def come_home(world: World, hero: Entity, mother: Entity, veil: Entity,
              color: VeilColor) -> None:
    """The hero returns; the mother greets; the new baby is mentioned."""
    mother.memes["excitement"] += 1
    world.say(
        f"{hero.id} came home still wearing {color.cape_phrase}, and {mother.id} "
        f"smiled when she saw it. \"You found it,\" she said softly."
    )
    world.say(
        f"{mother.id} rested a hand on her round belly and told {hero.id} that "
        f"the new baby would have a brave sister."
    )


def veil_hangs(world: World, veil: Entity, color: VeilColor) -> None:
    """The final image: the veil on its hook, ready."""
    veil.meters["resting"] += 1
    world.say(
        f"They hung the {color.name} veil back on the hook by the door, "
        f"and it shimmered softly, ready for the next time it was needed."
    )


# ---------------------------------------------------------------------------
# Screenplay: three-act shape driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, color: VeilColor, deed: GoodDeed,
         hero_name: str = "Mira", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         mother_type: str = "mother", mother_name: str = "Mama") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["lively", "brave"]),
    ))
    mother = world.add(Entity(
        id=mother_name, kind="character", type=mother_type,
        traits=["kind", "gentle"],
    ))
    veil = world.add(Entity(
        id="veil", kind="thing", type="veil",
        label=f"{color.name} veil",
        phrase=f"a {color.name} veil",
        owner=hero.id, state="cloth", moods={"cloth"},
    ))

    # Act 1 -- setup.
    introduce(world, hero, mother)
    mother_expecting(world, mother)
    veil_worn(world, hero, veil, color)
    slack_notice(world, hero, veil, color)
    hero_wishes(world, hero)

    # Act 2 -- the Transformation trigger.
    world.para()
    glow_appears(world, hero, veil, color)
    transformation_beats(world, hero, veil, color)

    # Act 3 -- the heroic deed and homecoming.
    world.para()
    hero_flies(world, hero, veil, deed)
    hero_rescues(world, hero, deed)
    world.para()
    come_home(world, hero, mother, veil, color)
    veil_hangs(world, veil, color)

    # Record facts for the Q&A generators.
    world.facts.update(
        hero=hero, mother=mother, veil=veil, color=color, deed=deed,
        setting=setting,
        transformed=hero.memes.get("transformed", 0) >= THRESHOLD,
        pride=hero.memes.get("pride", 0) >= THRESHOLD,
        expecting=mother.meters.get("expecting", 0) >= THRESHOLD,
        slack=veil.meters.get("slack", 0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "quiet": Setting(place="a quiet little town", weather="grey"),
    "harbor": Setting(place="a small harbor town", weather="sunny"),
    "hills":  Setting(place="a town beneath the green hills", weather="rainy"),
}

VEIL_COLORS = {
    "blue": VeilColor(
        name="blue",
        glow="soft blue glow",
        cape_phrase="a cape the color of the morning sky",
    ),
    "silver": VeilColor(
        name="silver",
        glow="pale silver light",
        cape_phrase="a cape that shone like moonlight",
    ),
    "violet": VeilColor(
        name="violet",
        glow="violet shimmer",
        cape_phrase="a cape as deep as a wildflower",
    ),
    "gold": VeilColor(
        name="gold",
        glow="warm gold light",
        cape_phrase="a cape that hummed like sunlight",
    ),
}

GOOD_DEEDS = {
    "kitten": GoodDeed(
        id="kitten",
        who="a lost kitten",
        where="the church roof",
        action="carried it gently down to its mother",
        mood="soft and worried",
        twirl="the cord caught the kitten like a small hammock",
    ),
    "puppy": GoodDeed(
        id="puppy",
        who="a trembling puppy",
        where="the old oak",
        action="wrapped it up and walked it back to its yard",
        mood="shaky and small",
        twirl="the cord looped under the puppy like a soft sling",
    ),
    "sparrow": GoodDeed(
        id="sparrow",
        who="a stuck sparrow",
        where="the garden shed",
        action="lifted the sparrow free and set it on a fence",
        mood="wide-eyed and chirping",
        twirl="the cord cupped the sparrow like a tiny basket",
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Nia", "Hana", "Rosa", "Ines", "Yara", "Pia"]
BOY_NAMES = ["Theo", "Ben", "Ari", "Kai", "Eli", "Sam", "Noah", "Finn"]
TRAITS = ["lively", "brave", "curious", "kind", "spirited", "gentle"]

HERO_TYPES = {"girl", "boy"}
MOTHER_TYPES = {"mother", "mom"}              # the only one we use here; kept open


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    setting: str
    color: str
    deed: str
    name: str
    gender: str
    mother_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "veil": [("What is a veil?",
              "A veil is a light piece of cloth you can wear over your head or "
              "your shoulders, often to keep still and feel calm.")],
    "cape": [("What is a superhero cape for?",
              "A cape is a long cloth that hangs from the shoulders and streams "
              "behind a hero when they run or fly, so the world can see them coming to help.")],
    "slack": [("What is slack in a rope or cloth?",
               "Slack is the loose bit left in a rope or cloth when it isn't pulled tight. "
               "Too much slack makes it hard to grip, but a little can let it move like a friend.")],
    "pregnancy": [("What does it mean when a mother is expecting a baby?",
                   "When a mother is expecting a baby, it means a baby is growing "
                   "inside her tummy, and the family is getting ready to welcome it.")],
    "transformation": [("What is a transformation?",
                        "A transformation is a big change in how something looks or "
                        "feels, like when a plain cloth becomes a shining cape.")],
    "cord": [("What is a cord?",
              "A cord is a strong thin rope, sometimes made of woven threads, that "
              "you can pull, throw, or tie.")],
    "glow": [("What is a glow?",
              "A glow is a soft, steady light that seems to come from inside "
              "something, like the moon behind a cloud.")],
    "hero": [("What is a hero?",
              "A hero is someone who chooses to help others, even when the help "
              "is small and kind.")],
}

KNOWLEDGE_ORDER = ["veil", "cape", "cord", "slack", "glow",
                   "pregnancy", "transformation", "hero"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, mother, veil, color, deed = (f["hero"], f["mother"], f["veil"],
                                        f["color"], f["deed"])
    return [
        f'Write a gentle superhero origin story for a 3-to-5-year-old that '
        f'uses the word "veil" and ends with a kind small rescue.',
        f'Tell a story where a {hero.type} named {hero.id} wears a {color.name} '
        f'veil, learns it can become a cape, and uses it to help {deed.who}.',
        f'Write a warm transformation story that includes the words "veil", '
        f'"slack", and "expecting", and shows how the change is felt at home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, mother, veil, color, deed, setting = (f["hero"], f["mother"], f["veil"],
                                                 f["color"], f["deed"], f["setting"])
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about and what is the {color.name} veil "
                f"that {hero.id} wears in {setting.place}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id}, who "
                f"lives with {pos} {mother.id} in {setting.place}. {pos.capitalize()} "
                f"{mother.id} had hemmed a {color.name} veil just for {obj}, and "
                f"{hero.id} wore it like a soft badge of courage."
            ),
        ),
        QAItem(
            question=(
                f"What was happening at home with {pos} {mother.id} while "
                f"{hero.id} was learning about the {color.name} veil?"
            ),
            answer=(
                f"{pos.capitalize()} {mother.id} was expecting a baby, so the "
                f"house felt gentle and a little full of waiting. {hero.id} knew "
                f"a new brother or sister was on the way."
            ),
        ),
        QAItem(
            question=(
                f"Why did the {color.name} veil slip a finger of slack and "
                f"frustrate {trait} {hero.id} at first?"
            ),
            answer=(
                f"The veil was so light that whenever {hero.id} pulled it tight, "
                f"a finger of slack slipped through {pos} fingers, and it was "
                f"hard to grip. That made {obj} frown, because {sub} wanted to "
                f"be a hero and grip the cloth the way heroes should."
            ),
        ),
        QAItem(
            question=(
                f"What changed the {color.name} veil into {color.cape_phrase} "
                f"and made the slack tighten on its own?"
            ),
            answer=(
                f"One {setting.weather} morning a {color.glow} slipped through "
                f"the veil and brushed {pos} cheek. The slack tightened all by "
                f"itself, the cloth shimmered, and the veil chose {hero.id}. "
                f"The slack turned into a taut {color.glow} cord, and when "
                f"{hero.pronoun()} twirled it, the cord unfurled into {color.cape_phrase}."
            ),
        ),
    ]
    if f.get("transformed"):
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} use {color.cape_phrase} to help "
                f"a small creature in {setting.place}?"
            ),
            answer=(
                f"With one brave hop {hero.id} was up and over the rooftops, the "
                f"cape streaming behind {obj}. {hero.pronoun().capitalize()} "
                f"found {deed.who} on {deed.where}, {deed.mood}, twirled the "
                f"cord so {deed.twirl}, and {deed.action}."
            ),
        ))
    if f.get("pride"):
        qa.append(QAItem(
            question=(
                f"How did {pos} {mother.id} greet {trait} {hero.id} when "
                f"{sub} came home wearing {color.cape_phrase}?"
            ),
            answer=(
                f"{pos.capitalize()} {mother.id} smiled when she saw the cape "
                f"and said, \"You found it.\" Then she rested a hand on her "
                f"round belly and told {hero.id} that the new baby would have a "
                f"brave sister."
            ),
        ))
    qa.append(QAItem(
        question=(
            f"Where did {trait} {hero.id} and {pos} {mother.id} put the "
            f"{color.name} veil at the end of the day in {setting.place}?"
        ),
        answer=(
            f"They hung the {color.name} veil back on the hook by the door, "
            f"and it shimmered softly, ready for the next time it was needed."
        ),
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    tags = {"veil", "cape", "slack", "transformation", "pregnancy"}
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
# CLI / trace.
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
        if e.moods:
            bits.append(f"moods={sorted(e.moods)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        setting="quiet",
        color="blue",
        deed="kitten",
        name="Mira",
        gender="girl",
        mother_name="Mama",
        trait="lively",
    ),
    StoryParams(
        setting="hills",
        color="violet",
        deed="sparrow",
        name="Lila",
        gender="girl",
        mother_name="Mama",
        trait="kind",
    ),
    StoryParams(
        setting="harbor",
        color="silver",
        deed="puppy",
        name="Theo",
        gender="boy",
        mother_name="Mama",
        trait="brave",
    ),
    StoryParams(
        setting="quiet",
        color="gold",
        deed="kitten",
        name="Hana",
        gender="girl",
        mother_name="Mama",
        trait="curious",
    ),
    StoryParams(
        setting="hills",
        color="blue",
        deed="puppy",
        name="Ari",
        gender="boy",
        mother_name="Mama",
        trait="gentle",
    ),
]


def explain_rejection(setting: Optional[str], color: Optional[str],
                      deed: Optional[str], gender: Optional[str]) -> str:
    parts = []
    if setting is not None and setting not in SETTINGS:
        parts.append(f"unknown --setting {setting!r}; try one of "
                     f"{sorted(SETTINGS)}.")
    if color is not None and color not in VEIL_COLORS:
        parts.append(f"unknown --color {color!r}; try one of "
                     f"{sorted(VEIL_COLORS)}.")
    if deed is not None and deed not in GOOD_DEEDS:
        parts.append(f"unknown --deed {deed!r}; try one of "
                     f"{sorted(GOOD_DEEDS)}.")
    if gender is not None and gender not in HERO_TYPES:
        parts.append(f"unknown --gender {gender!r}; try one of "
                     f"{sorted(HERO_TYPES)}.")
    if not parts:
        return "(No valid combination matches the given options.)"
    return "(No story: " + " ".join(parts) + ")"


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (the registries above, plus the Transformation trigger check).  The rules are
# inline below; the facts are generated from the registries so the two can
# never drift.  Uses the shared ``asp`` helper + clingo, imported lazily so the
# prose engine runs without them.  See ``python <this>.py --verify``.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting affords a story when it has a color, a deed, and a gender.
affords_setting(S) :- setting(S).
affords_color(C)  :- color(C).
affords_deed(D)   :- good_deed(D).

% A hero wears the veil from the start; the veil can become a cord and a cape.
wears_veil.
becomes_cord :- wears_veil, veil_slack, veil_glow, veil_pressure.
becomes_cape :- becomes_cord.

% The Transformation fires only when all four preconditions are present.
transformed :- becomes_cape.

% A good deed proves the change happened (and lets the hero come home).
has_deed :- good_deed(_).
proves_change :- transformed, has_deed.

% A valid story combines a setting, a color, a deed, and the Transformation.
valid(S, C, D, G) :- setting(S), color(C), good_deed(D), hero_type(G),
                     proves_change.
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in VEIL_COLORS:
        lines.append(asp.fact("color", cid))
    for did in GOOD_DEEDS:
        lines.append(asp.fact("good_deed", did))
    for g in HERO_TYPES:
        lines.append(asp.fact("hero_type", g))
    # Static preconditions the rules refer to.
    lines.append(asp.fact("veil_slack"))
    lines.append(asp.fact("veil_glow"))
    lines.append(asp.fact("veil_pressure"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    """(setting, color, deed, gender) tuples clingo says are valid."""
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python curated/reasonableness list."""
    clingo_set = set(asp_valid_stories())
    python_set = {(p.setting, p.color, p.deed, p.gender) for p in CURATED}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches curated set ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and curated set:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a soft blue veil, an expecting mother, "
                    "and a Transformation into a small superhero.  Unspecified "
                    "choices are picked at random (seeded).")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--color", choices=VEIL_COLORS)
    ap.add_argument("--deed", choices=GOOD_DEEDS)
    ap.add_argument("--gender", choices=sorted(HERO_TYPES))
    ap.add_argument("--name")
    ap.add_argument("--mother-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches the curated set")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Fill in any unspecified choices at random; refuse explicit impossibilities."""
    bad = []
    if args.setting is not None and args.setting not in SETTINGS:
        bad.append("setting")
    if args.color is not None and args.color not in VEIL_COLORS:
        bad.append("color")
    if args.deed is not None and args.deed not in GOOD_DEEDS:
        bad.append("deed")
    if args.gender is not None and args.gender not in HERO_TYPES:
        bad.append("gender")
    if bad:
        raise StoryError(explain_rejection(args.setting, args.color,
                                           args.deed, args.gender))

    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    color_id = args.color or rng.choice(sorted(VEIL_COLORS))
    deed_id = args.deed or rng.choice(sorted(GOOD_DEEDS))
    gender = args.gender or rng.choice(sorted(HERO_TYPES))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mother_name = args.mother_name or "Mama"
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        color=color_id,
        deed=deed_id,
        name=name,
        gender=gender,
        mother_name=mother_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(
        SETTINGS[params.setting], VEIL_COLORS[params.color],
        GOOD_DEEDS[params.deed], params.name, params.gender,
        [params.trait, "brave"], "mother", params.mother_name,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (setting, color, deed, gender) stories:\n")
        for setting, color, deed, gender in stories:
            print(f"  {setting:7} {color:7} {deed:8} {gender}")
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
            header = f"### {p.name}: {p.color} veil + {p.deed} ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
