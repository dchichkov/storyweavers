#!/usr/bin/env python3
"""
storyworlds/worlds/machinery_cheapo_teat_sound_effects_quest_detective.py
======================================================================

Story world: *The Case of the Missing Click*.

Domain sketch
-------------
A short, child-friendly "Detective Story" simulation. The detective kid
clues together **sound effects** to track down a strange noise that
stopped a beloved backyard contraption from working.

Seed words used (must appear in prose somewhere): ``machinery``,
``cheapo``, ``teat``.

Narrative instruments required: ``Sound Effects``, ``Quest``, style close
to ``Detective Story``.

Premise
-------
Mira is a little detective who keeps a notebook of every sound her
backyard makes. Today her favorite **machinery** -- the old hand-pump --
will not make its friendly "plip-plip" sound, so the tin duck on the
spout stays dry and its little rubber **teat** is empty. Mira takes
this as a *quest*: she follows *sound effects* (a hum, a clink, a
faint squeak) to a rusty gear inside the pump. The turn: she traces
each clue from one place to the next. The resolution: she rigs a
**cheapo** paperclip hook, fishes the gear free, and the pump is
clucking and spitting water for the duck again.

The world model below encodes this premise as typed entities
(detective, parent helper, machinery, gear, etc.) with physical
``meters`` (water, wear, sound) and emotional ``memes`` (curiosity,
pride, helper) that drive the prose.

Story quality discipline (cf. storyworlds/STORY.md):
* State-driven prose, not a frozen paragraph with swapped nouns.
* A clear beginning, a clue-driven middle turn, and an ending image
  that proves what changed (the pump makes sound again, the duck
  gets water).
* No leaked ids, raw debug language, scaffold phrases, or doubled
  articles in story text or QA.
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

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which a numeric effect has accumulated enough to be narrated.
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Sound vocabulary -- the *narrative instrument* for the quest.  Each clue is
# a name + a literal "what it sounds like" phrase, so the prose can carry
# sound without naming internal ids.
# ---------------------------------------------------------------------------
SOUND_LIBRARY: list[tuple[str, str]] = [
    ("hum",      "a low steady hum, like a tired bee behind the wall"),
    ("clink",    "a small sharp clink, like a spoon tapping a tin cup"),
    ("squeak",   "a thin squeak, like a mouse turning in a squeaky chair"),
    ("thud",     "a soft thud, like a boot stepping on a sponge"),
    ("drip",     "a slow drip, like one drop at the end of a leaky tap"),
    ("plip",     "a happy plip, like a drop falling back into a full bowl"),
    ("cluck",    "a wooden cluck, like a little duck made of tin"),
    ("whirr",    "a busy whirr, like a top spinning fast under a hand"),
]

SOUND_BY_ID = {sid: desc for sid, desc in SOUND_LIBRARY}
SOUND_IDS = [sid for sid, _ in SOUND_LIBRARY]


# ---------------------------------------------------------------------------
# Typed entities.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # detective, kid, helper, machine, gear, ...
    label: str = ""                # short reference
    phrase: str = ""               # full noun phrase used in prose
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    helper: Optional[str] = None   # who can lend a hand
    place: str = ""                # where the entity lives / sits
    plugged: bool = False          # rubber teat: fitted onto the duck spout
    movable: bool = False          # gear: can be fished out by a cheapo hook
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective_girl"}
        male = {"boy", "father", "dad", "man", "detective_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if getattr(self, "plural", False) else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Settings.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)   # which machinery kinds sit here


# ---------------------------------------------------------------------------
# Machinery: a contraption whose job is to make a sound effect (and a result).
# ---------------------------------------------------------------------------
@dataclass
class Machinery:
    id: str
    noun: str            # "hand pump", "tin whistle", "wooden music box"
    phrase: str          # full noun phrase for prose
    sound: str           # the SOUND_LIBRARY id it makes when working
    result: str          # what it does when working: "spits water for the duck"
    broken_reason: str   # what stopped it: "the gear slipped off its peg"
    place: str           # where it lives in the world
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Helpers -- characters who can appear in the case.
# ---------------------------------------------------------------------------
@dataclass
class Helper:
    id: str
    noun: str            # "neighbor", "older cousin", "grandfather"
    skill: str           # what they are good at: "tools", "puzzles"
    tip: str             # the sentence of advice they offer the kid


# ---------------------------------------------------------------------------
# Clue -- a sound effect placed at a location, hinting toward a cause.
# ---------------------------------------------------------------------------
@dataclass
class Clue:
    id: str
    sound: str           # SOUND_LIBRARY id
    where: str           # "by the spout", "under the handle"
    points_to: str       # which machinery part it points at
    order: int           # 1..3, in the order the kid should notice them


# ---------------------------------------------------------------------------
# World: entity store + narration buffer.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.clues: list[Clue] = []
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    # -- entity helpers ---------------------------------------------------
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    # -- narration helpers -----------------------------------------------
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.clues = list(self.clues)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules -- forward-chained until fixpoint.  Each rule produces one or
# more sentences (which are appended to the world) and bumps meters/memes.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_notebook_full(world: World) -> list[str]:
    """The detective's notebook has cataloged every heard sound -> curiosity."""
    for actor in world.characters():
        if actor.type not in {"detective_girl", "detective_boy"}:
            continue
        if actor.meters["heard"] < 3:
            continue
        sig = ("notebook", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["curiosity"] += 1
        return []  # narrated separately by the screenplay, not the engine
    return []


def _r_clue_chain(world: World) -> list[str]:
    """Each newly heard clue tightens the chain -> progress."""
    for actor in world.characters():
        if actor.type not in {"detective_girl", "detective_boy"}:
            continue
        n = actor.meters["heard"]
        if n < THRESHOLD:
            continue
        sig = ("chain", actor.id, int(n))
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["progress"] += 1
    return []


def _r_cheapo_hook(world: World) -> list[str]:
    """A cheapo hook in hand + a movable gear still stuck -> ready to fish."""
    actor = next((e for e in world.characters()
                  if e.type in {"detective_girl", "detective_boy"}), None)
    if actor is None:
        return []
    if actor.meters["hook"] < THRESHOLD:
        return []
    sig = ("hook_ready", actor.id)
    if sig in world.fired:
        continue_ = False
        return []
    world.fired.add(sig)
    actor.memes["pride"] += 1
    return []


def _r_pump_fixed(world: World) -> list[str]:
    """Gear recovered + teat plugged -> pump sound returns, duck gets water."""
    out: list[str] = []
    for ent in world.entities.values():
        if ent.type == "gear" and ent.meters["freed"] >= THRESHOLD:
            sig = ("pump_fixed", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["back"] += 1
            out.append(
                "Soon the pump was clucking and spitting water again."
            )
            # the rubber teat plugged back on, so the duck drinks
            for e in world.entities.values():
                if e.type == "teat" and e.plugged:
                    e.meters["full"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="notebook", tag="social", apply=_r_notebook_full),
    Rule(name="chain", tag="cognitive", apply=_r_clue_chain),
    Rule(name="cheapo_hook", tag="physical", apply=_r_cheapo_hook),
    Rule(name="pump_fixed", tag="physical", apply=_r_pump_fixed),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Forward-chain every rule to fixpoint; optionally append sentences."""
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
# Constraint helpers.
# ---------------------------------------------------------------------------
def clue_chain_ok(machinery: Machinery, clues: list[Clue]) -> bool:
    """A quest is reasonable only when the chain has 3 clues, ordered, each
    pointing to a real part of the contraption, and the broken reason is
    exactly what the final clue points at."""
    if [c.order for c in clues] != [1, 2, 3]:
        return False
    if clues[-1].points_to != machinery.broken_reason.split()[-1]:
        # The final clue should hint at the broken part (the *gear*, etc.)
        return False
    return True


def select_clues(machinery: Machinery) -> Optional[list[Clue]]:
    """Pick the 3-clue chain for this machinery (None if none available)."""
    chain = CLUE_CHAINS.get(machinery.id)
    return list(chain) if chain else None


# ---------------------------------------------------------------------------
# Verbs -- each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def noise_text(sound_id: str) -> str:
    """Return the *prose* description of a sound effect (never the id)."""
    return SOUND_BY_ID.get(sound_id, "a small sound")


def introduce(world: World, hero: Entity) -> None:
    extra = ", who kept a notebook of every sound her backyard made"
    if hero.type == "detective_boy":
        extra = ", who kept a notebook of every sound his backyard made"
    world.say(
        f"{hero.id} was a little detective{extra}."
    )


def loves_sounds(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} had drawn pictures of every sound "
        f"the backyard made, so {hero.pronoun()} knew exactly what should "
        f"be there on a normal morning."
    )


def setup_machinery(world: World, hero: Entity, machine: Machinery, teat: Entity,
                    duck: Entity) -> None:
    world.say(
        f"In the middle of the yard sat {machine.phrase}, and beside it "
        f"stood {duck.phrase}, waiting."
    )
    world.say(
        f"On the duck's spout sat {teat.phrase}, ready to fill with water "
        f"from the pump."
    )


def notice_silence(world: World, hero: Entity, machine: Machinery) -> None:
    world.say(
        f"But that morning the yard was too quiet. {machine.noun.capitalize()} "
        f"was supposed to make {noise_text(machine.sound)}, and instead it "
        f"made nothing at all."
    )
    world.say(
        f"{hero.id} frowned, opened {hero.pronoun('possessive')} notebook, "
        f"and wrote one word at the top: *missing*."
    )


def accept_quest(world: World, hero: Entity, machine: Machinery) -> None:
    hero.memes["quest"] += 1
    world.say(
        f'"I will find that sound," {hero.pronoun()} said. '
        f'"Every case has a clue, and every clue makes a sound."'
    )
    world.say(
        f"So {hero.id} began the quest, listening for the first sound effect "
        f"that did not belong."
    )


def hear_first_clue(world: World, hero: Entity, clue: Clue) -> None:
    hero.meters["heard"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"The first clue came {clue.where}: {noise_text(clue.sound)}."
    )


def hear_second_clue(world: World, hero: Entity, prev: Clue, clue: Clue) -> None:
    hero.meters["heard"] += 1
    world.say(
        f"Following the first sound, {hero.pronoun()} found the next clue "
        f"{clue.where}: {noise_text(clue.sound)}."
    )


def hear_third_clue(world: World, hero: Entity, clue: Clue, machine: Machinery) -> None:
    hero.meters["heard"] += 1
    hero.memes["progress"] += 1
    world.say(
        f"The third and last clue was right by {machine.noun}: "
        f"{noise_text(clue.sound)}. That was the sound the machinery should "
        f"never have made."
    )


def meet_helper(world: World, hero: Entity, helper_ent: Entity,
                helper: Helper) -> None:
    helper_ent.memes["help"] += 1
    world.say(
        f"On the way, {hero.id} met {helper.phrase}, who was very good "
        f"at {helper.skill}."
    )
    world.say(
        f'"{helper.tip}" {helper_ent.pronoun()} said, smiling.'
    )


def craft_cheapo_hook(world: World, hero: Entity, gear: Entity) -> None:
    hero.meters["hook"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} found a paperclip on the path, bent it into a tiny hook "
        f"with steady fingers, and tied a bit of string to it. It was a "
        f"cheapo tool, but it was clever."
    )


def fish_gear(world: World, hero: Entity, gear: Entity) -> None:
    gear.meters["freed"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} lowered the cheapo hook down into "
        f"the pump, fished around, and gently pulled the loose part free."
    )
    world.say(
        f"It was a small round gear, the kind that makes machinery sing "
        f"when it spins the right way."
    )


def reattach(world: World, hero: Entity, gear: Entity, teat: Entity) -> None:
    teat.plugged = True
    world.say(
        f"{hero.id} slipped the gear back where it belonged and pressed "
        f"{teat.phrase} snug onto the duck's spout."
    )


def ending_image(world: World, hero: Entity, machine: Machinery,
                 teat: Entity, duck: Entity) -> None:
    propagate(world, narrate=False)             # fires _r_pump_fixed
    world.say(
        f"Then {hero.id} pressed the handle, and the pump made "
        f"{noise_text(machine.sound)} again, bright and quick."
    )
    world.say(
        f"Water ran down the spout, the rubber teat filled, and "
        f"{duck.phrase} tipped its head to drink."
    )
    world.say(
        f"{hero.id} closed {hero.pronoun('possessive')} notebook with a "
        f"happy sigh, because the case of the missing click was solved."
    )


# ---------------------------------------------------------------------------
# Screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, machinery: Machinery, helper_def: Helper,
         hero_name: str, hero_type: str, hero_traits: list[str]) -> World:
    world = World(setting)
    world.setting = setting

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label="the detective",
        traits=["little"] + hero_traits,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type={"detective_girl": "mother", "detective_boy": "father"}.get(hero_type, "mother"),
        label="the parent",
    ))
    helper = world.add(Entity(
        id=helper_def.id,
        kind="character",
        type="helper",
        label=helper_def.noun,
        phrase=f"a kind {helper_def.noun}",
    ))
    machine = world.add(Entity(
        id=machinery.id,
        kind="thing",
        type="machinery",
        label=machinery.noun,
        phrase=machinery.phrase,
        place=machinery.place,
    ))
    gear = world.add(Entity(
        id="loose_gear",
        kind="thing",
        type="gear",
        label="loose gear",
        phrase="a small loose gear",
        movable=True,
        place=machinery.place,
    ))
    teat = world.add(Entity(
        id="rubber_teat",
        kind="thing",
        type="teat",
        label="rubber teat",
        phrase="a soft rubber teat",
        owner=hero.id,
    ))
    duck = world.add(Entity(
        id="tin_duck",
        kind="thing",
        type="duck",
        label="tin duck",
        phrase="a little tin duck with a bright beak",
    ))

    clues = select_clues(machinery) or []
    world.clues = list(clues)

    # Act 1 -- who, what the yard sounds like, what is missing today.
    introduce(world, hero)
    loves_sounds(world, hero)
    setup_machinery(world, hero, machine, teat, duck)
    world.para()
    notice_silence(world, hero, machine)
    accept_quest(world, hero, machine)

    # Act 2 -- the sound-effects quest: each clue narrows the chain.
    world.para()
    if len(clues) >= 3:
        hear_first_clue(world, hero, clues[0])
        hear_second_clue(world, hero, clues[0], clues[1])
        hear_third_clue(world, hero, clues[2], machine)

    # Helper appears with one good tip (cheap to render, high payoff).
    meet_helper(world, hero, helper, helper_def)

    # Act 3 -- the cheapo hook, the gear, and the ending image.
    world.para()
    craft_cheapo_hook(world, hero, gear)
    fish_gear(world, hero, gear)
    reattach(world, hero, gear, teat)
    ending_image(world, hero, machine, teat, duck)

    propagate(world, narrate=False)

    world.facts.update(
        hero=hero,
        parent=parent,
        helper=helper_def,
        machinery=machinery,
        gear=gear,
        teat=teat,
        duck=duck,
        clues=clues,
        heard=hero.meters["heard"],
        hook=hero.meters["hook"],
        freed=gear.meters["freed"],
        resolved=gear.meters["freed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False, affords={"pump"}),
    "porch":    Setting(place="the porch",    indoor=True,  affords={"music_box"}),
    "workshop": Setting(place="the workshop", indoor=True,  affords={"whistle"}),
    "garden":   Setting(place="the garden",   indoor=False, affords={"pump", "whistle"}),
}

MACHINERY = {
    "pump": Machinery(
        id="pump",
        noun="hand pump",
        phrase="an old hand pump with a wooden handle",
        sound="plip",
        result="spits water for the duck",
        broken_reason="the gear slipped off its peg",
        place="backyard",
        tags={"pump", "water"},
    ),
    "music_box": Machinery(
        id="music_box",
        noun="music box",
        phrase="a small wooden music box with a brass key",
        sound="cluck",
        result="plays a wooden tune",
        broken_reason="the gear slipped off its peg",
        place="porch",
        tags={"music", "wood"},
    ),
    "whistle": Machinery(
        id="whistle",
        noun="tin whistle",
        phrase="a tin whistle hanging on a hook by the door",
        sound="whirr",
        result="whistles a clear note",
        broken_reason="the gear slipped off its peg",
        place="workshop",
        tags={"whistle", "tin"},
    ),
}

HELPERS = {
    "neighbor": Helper(
        id="neighbor",
        noun="neighbor",
        skill="tools",
        tip="Small things come loose when nobody watches; a little hook can bring them back.",
    ),
    "cousin": Helper(
        id="cousin",
        noun="older cousin",
        skill="puzzles",
        tip="Listen twice: the second sound is the one that tells you where to look.",
    ),
    "grandfather": Helper(
        id="grandfather",
        noun="grandfather",
        skill="machines",
        tip="Cheapo tools can fix big problems, as long as you are patient with them.",
    ),
}

# For every machinery kind, a 3-clue chain of sound effects. The chain only
# counts as *reasonable* if clue_chain_ok() returns True.
CLUE_CHAINS: dict[str, list[Clue]] = {
    "pump": [
        Clue(id="c1", sound="hum",    where="by the wall behind the pump", points_to="gear", order=1),
        Clue(id="c2", sound="clink",  where="under the wooden handle",     points_to="gear", order=2),
        Clue(id="c3", sound="squeak", where="inside the pump body",        points_to="gear", order=3),
    ],
    "music_box": [
        Clue(id="c1", sound="thud",  where="on the shelf above the box",   points_to="gear", order=1),
        Clue(id="c2", sound="drip",  where="from the lid hinge",            points_to="gear", order=2),
        Clue(id="c3", sound="squeak",where="inside the box when it tips",   points_to="gear", order=3),
    ],
    "whistle": [
        Clue(id="c1", sound="hum",    where="by the tin of spare parts",   points_to="gear", order=1),
        Clue(id="c2", sound="clink",  where="on the workbench edge",       points_to="gear", order=2),
        Clue(id="c3", sound="squeak", where="inside the whistle tube",      points_to="gear", order=3),
    ],
}

GIRL_NAMES = ["Mira", "Nora", "Pip", "Sela", "Iris", "Tessa", "Lila", "June"]
BOY_NAMES = ["Theo", "Oren", "Walt", "Jude", "Kai", "Sammy", "Nico", "Ren"]
TRAITS = ["sharp-eared", "patient", "bright", "careful", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    """(place, machinery) pairs that pass the reasonableness constraint."""
    out = []
    for place, s in SETTINGS.items():
        for mid in s.affords:
            m = MACHINERY[mid]
            if clue_chain_ok(m, CLUE_CHAINS[mid]):
                out.append((place, mid))
    return out


# ---------------------------------------------------------------------------
# Per-story parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    machinery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three sets: prompts, story-grounded, world knowledge.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, machine = f["hero"], f["machinery"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that uses the '
        f'words "machinery", "cheapo", and "teat", and follows a child who '
        f'tracks sound effects to solve the case of a quiet {machine.noun}.',
        f'Tell a short case-file story where a child detective named {hero.id} '
        f'follows a chain of sound effects to fix a broken {machine.noun} and '
        f'fill a little duck\'s rubber teat.',
        f'Write a simple, kid-friendly mystery on the theme "the missing '
        f'click", where the hero uses three sound effects as clues and a '
        f'cheapo paperclip hook to finish the quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, machine, helper, gear, teat, duck = (
        f["hero"], f["machinery"], f["helper"], f["gear"], f["teat"], f["duck"],
    )
    clues = f["clues"]
    sub = hero.pronoun("subject")
    obj = hero.pronoun("object")
    pos = hero.pronoun("possessive")
    place = world.setting.place
    s1 = noise_text(clues[0].sound) if len(clues) > 0 else "a small sound"
    s2 = noise_text(clues[1].sound) if len(clues) > 1 else "another small sound"
    s3 = noise_text(clues[2].sound) if len(clues) > 2 else "a final small sound"

    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the case of the missing click about, and where does "
                f"{hero.id} begin the investigation?"
            ),
            answer=(
                f"It is about little detective {hero.id}, who begins the "
                f"investigation in {place} when {pos} {machine.noun} stops "
                f"making its usual sound."
            ),
        ),
        QAItem(
            question=(
                f"Why did {hero.id} decide to begin a sound-effects quest on "
                f"the morning the {machine.noun} went quiet?"
            ),
            answer=(
                f"{hero.id} decided to begin the quest because {pos} "
                f"{machine.noun} should have been making {noise_text(machine.sound)}, "
                f"and instead it made nothing. {sub.capitalize()} opened {pos} "
                f"notebook and wrote one word at the top: *missing*."
            ),
        ),
        QAItem(
            question=(
                f"What were the three sound effects {hero.id} followed during "
                f"the quest in {place}?"
            ),
            answer=(
                f"The first sound effect was {s1}. The second sound effect "
                f"was {s2}. The third and last sound effect was {s3}, which "
                f"came from right inside the {machine.noun} itself."
            ),
        ),
        QAItem(
            question=(
                f"How did the {helper.noun} help {hero.id} with the case of "
                f"the missing click in {place}?"
            ),
            answer=(
                f'The {helper.noun} was very good at {helper.skill}, and said, '
                f'"{helper.tip}" That advice gave {hero.id} the idea to keep '
                f"listening carefully and to try a small homemade tool."
            ),
        ),
        QAItem(
            question=(
                f"What cheapo tool did {hero.id} use to finish the case of "
                f"the missing click?"
            ),
            answer=(
                f"{hero.id} bent a paperclip into a tiny hook, tied a bit of "
                f"string to it, and used the cheapo hook to fish the loose "
                f"gear out from inside the {machine.noun}."
            ),
        ),
        QAItem(
            question=(
                f"How did the story show that {hero.id} had solved the case "
                f"of the missing click at the end?"
            ),
            answer=(
                f"At the end, the {machine.noun} made "
                f"{noise_text(machine.sound)} again, water ran down the spout, "
                f"the rubber teat filled, and the little tin duck tipped its "
                f"head to drink. {hero.id} closed {pos} notebook with a "
                f"happy sigh because the mystery was solved."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """Generic child-level questions about the world's elements."""
    return [
        QAItem(
            question="What is a detective?",
            answer=(
                "A detective is a person whose job is to look closely at "
                "small clues and to figure out what really happened."
            ),
        ),
        QAItem(
            question="What is a sound effect?",
            answer=(
                "A sound effect is a sound that stands for something, like a "
                "door creak for a haunted house or a plip for a drop of water."
            ),
        ),
        QAItem(
            question="What is a quest?",
            answer=(
                "A quest is a small journey to find or to fix one important "
                "thing, with a clear goal at the end."
            ),
        ),
        QAItem(
            question="What does machinery mean?",
            answer=(
                "Machinery is the name for machines and the working parts "
                "inside them, like gears, handles, and wheels."
            ),
        ),
        QAItem(
            question="What does cheapo mean?",
            answer=(
                "Cheapo means very simple and inexpensive, like a paperclip "
                "used as a hook instead of a real tool."
            ),
        ),
        QAItem(
            question="What is a teat on a feeding bottle or toy?",
            answer=(
                "A teat is the soft rubber tip that liquid comes out of, "
                "shaped like a small drop so it can fit into a mouth."
            ),
        ),
    ]


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
        if getattr(e, "place", ""):
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:12} ({e.type:14}) {' '.join(bits)}")
    lines.append("  clues:")
    for c in world.clues:
        lines.append(f"    {c.order}. {c.sound:6} @ {c.where} -> {c.points_to}")
    return "\n".join(lines)


# Curated set for --all.
CURATED = [
    StoryParams(place="backyard", machinery="pump",     name="Mira", gender="girl", helper="neighbor",    trait="sharp-eared"),
    StoryParams(place="porch",    machinery="music_box", name="Theo", gender="boy",  helper="cousin",     trait="patient"),
    StoryParams(place="workshop", machinery="whistle",   name="Pip",  gender="girl", helper="grandfather",trait="careful"),
]


def explain_rejection(machinery: str) -> str:
    return (
        f"(No story: '{machinery}' is not a registered machinery kind. "
        f"Try one of: {sorted(MACHINERY)}.)"
    )


# ---------------------------------------------------------------------------
# Inline ASP twin -- declarative counterpart to clue_chain_ok + valid_combos().
# Uses the shared `asp` helper; imported lazily so the prose engine works
# without clingo installed.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A machinery is "broken" only when its reason mentions the loose gear.
broken(M) :- reason(M, R), contains(R, gear).

% A clue chain is well-formed when it has exactly three clues ordered 1,2,3.
chain_ok(M) :- clue(M, 1, _), clue(M, 2, _), clue(M, 3, _), not dup_order(M).
dup_order(M) :- clue(M, O, _), clue(M, O2, _), O != O2.

% A place affords a machinery only when both are registered and the
% clue chain on that machinery is well-formed.
valid(Place, M) :- setting(Place), affords(Place, M), broken(M), chain_ok(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for mid in sorted(s.affords):
            lines.append(asp.fact("affords", pid, mid))
    for mid, m in MACHINERY.items():
        lines.append(asp.fact("machinery", mid))
        lines.append(asp.fact("reason", mid, m.broken_reason.replace(" ", "_")))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    for mid, chain in CLUE_CHAINS.items():
        for c in chain:
            lines.append(asp.fact("clue", mid, c.order, c.sound))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "Story world sketch: 'The Case of the Missing Click' -- a "
            "kid-detective tracks sound effects to fix a broken machinery "
            "and refill a rubber teat."
        ),
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--machinery", choices=MACHINERY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    """Randomize anything not pinned; reject explicit invalid combinations."""
    if args.machinery and not select_clues(MACHINERY[args.machinery]):
        raise StoryError(explain_rejection(args.machinery))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.machinery is None or c[1] == args.machinery)]
    if not combos:
        raise StoryError("(No valid (place, machinery) combination matches.)")

    place, machinery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        machinery=machinery,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + 3 Q&A sets."""
    hero_type = "detective_girl" if params.gender == "girl" else "detective_boy"
    helper_def = HELPERS[params.helper]
    world = tell(
        SETTINGS[params.place],
        MACHINERY[params.machinery],
        helper_def,
        params.name,
        hero_type,
        [params.trait, "patient"],
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, machinery) combos:\n")
        for place, mid in triples:
            print(f"  {place:9} {mid}")
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
            header = f"### {p.name}: case of the missing click ({p.machinery} at {p.place})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
