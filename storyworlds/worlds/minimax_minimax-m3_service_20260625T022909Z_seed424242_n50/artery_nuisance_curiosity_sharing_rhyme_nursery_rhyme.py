#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/artery_nuisance_curiosity_sharing_rhyme_nursery_rhyme.py
==============================================================================================================================

A standalone *story world* sketch for "The Busy Artery" tale and close,
constraint-checked variations of it.

Initial story (used to build a world model):
---
Once upon a time, in a quiet little village that sat beside a green hill,
there was a tiny red road called the Artery.  The Artery was the very
main road of the village, and every drop of red busyness traveled along it
to reach the busy Heart at the center of town.

Now, the Heart was a kind and helpful pump, and every morning it would
wake and call, "Bring me the red drops so I can send them out again!"  And
all morning long the Artery hummed and the red drops went round and round.

But one morning a Nuisance came to the Artery, and the Nuisance was a
stuck, lazy clot that would not move.  "Hmph," said the Nuisance, "I shall
sit right here in the middle of the road, and the red drops shall have to
go around."

The red drops tried to go around, but they grew curious and worried, and
they began to bunch and crowd.  "Oh dear," said the Artery, "I am getting
narrow and the road is hot.  We need help, dear friends."

So the Artery sent a tiny call down to the Heart, and the Heart sent
little helper cells named Sharing -- white, round, and jolly -- who came
skipping along the road.  Sharing sang a rhyme as they came:

    "Round we go, round we go, helping every red drop flow.
     Soft we work, soft we run, sharing help until we're done."

The little Sharing helpers wrapped the Nuisance gently, bit by bit, and
softened the stuck clot until at last it broke apart and floated away.
The Artery grew wide again, and the red drops went rushing happily along,
singing the rhyme with the helpers as they went.

And from that day on, whenever a Nuisance came to sit in the road, the
Artery remembered the rhyme, the helpers came running, and the village
stayed well and warm.

Causal state updates (simulated):
---
    do rush                  -> actor.curiosity += 1 ; actor.warmth += 1
    stuck clot appears      -> artery.narrowing += 1 ; drops.worry += 1
    helpers summoned        -> helpers.busy += 1 ; artery.calm += 1
    helpers dissolve clot   -> artery.flow += 1 ; drops.joy += 1
    rhyme sung together     -> shared.celebration += 1

Scripted social/emotional beats (Nursery-Rhyme style):
---
    * couplets when helpers arrive, when the clot dissolves, and at the end
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# A tiny "village" canon.  Each domain value is built up from these registries
# so the prose engine never has to invent names.

VILLAGES = ["Tinytown", "Hillside", "Bumblebrook", "Redbridge", "Willow End"]
ROAD_NAMES = ["Artery", "Long Lane", "River-Run", "Pump Path"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "place"
    type: str = "thing"            # artery, drop, heart, helper, clot, ...
    label: str = ""                # short reference
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    role: str = ""                 # narrator role: hero | helper | nuisance
    plural: bool = False
    # Two numeric dimensions: physical meters and emotional memes.
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"drop", "heart"}
        male = {"helper", "clot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    village: str = "Tinytown"
    road: str = "the Artery"
    has_hill: bool = True
    weather: str = "sunny"


@dataclass
class Nuisance:
    id: str
    label: str
    phrase: str
    rhyme_line: str         # the couplet line the nuisance "interrupts"


@dataclass
class Helpers:
    id: str
    label: str
    plural: bool
    rhyme: str              # the couplet they sing
    method: str             # body of the rescue sentence
    tail: str               # closing clause


HELPERS = [
    Helpers(
        id="sharing",
        label="Sharing",
        plural=True,
        rhyme=(
            '"Round we go, round we go, helping every red drop flow.\n'
            '     Soft we work, soft we run, sharing help until we\'re done."'
        ),
        method="wrapped the Nuisance gently, bit by bit",
        tail="wrapped the Nuisance until it broke apart and floated away",
    ),
    Helpers(
        id="curiosity",
        label="Curiosity",
        plural=False,
        rhyme=(
            '"Where, oh where, did the red drops go?\n'
            '     Come along, come along -- I will show, I will show!"'
        ),
        method="poked about the Nuisance with a friendly wiggle",
        tail="wiggled the Nuisance loose until it tumbled away",
    ),
]

NUISANCES = {
    "clot": Nuisance(
        id="clot",
        label="a stuck, lazy clot",
        phrase="a stuck, lazy clot that would not move",
        rhyme_line="a stuck clot sat right in the middle of the road",
    ),
    "block": Nuisance(
        id="block",
        label="a grumbly block",
        phrase="a grumbly block of old worry",
        rhyme_line="a grumbly block sat grumbling right in the middle",
    ),
    "stop": Nuisance(
        id="stop",
        label="a stubborn stop",
        phrase="a stubborn stop that would not budge",
        rhyme_line="a stubborn stop sat stubborn right in the middle",
    ),
}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules (forward-chained).
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_narrowing(world: World) -> list[str]:
    """Stuck clot present + drops worried -> artery narrows and feels hot."""
    for artery in [e for e in world.entities.values() if e.type == "artery"]:
        if artery.meters["narrowing"] < THRESHOLD:
            continue
        sig = ("narrow", artery.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        return [f"So the {artery.label} grew narrow, and the road felt hot."]
    return []


def _r_calm(world: World) -> list[str]:
    """Helpers arrived and busy -> artery calms a little, drops cheer up."""
    for helpers in [e for e in world.entities.values() if e.type == "helpers"]:
        if helpers.meters["busy"] < THRESHOLD:
            continue
        sig = ("calm", helpers.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        artery = next((e for e in world.entities.values() if e.type == "artery"), None)
        if artery is not None:
            artery.memes["calm"] += 1
        return [f"The {helpers.label} came skipping, and the {artery.label if artery else 'road'} felt calmer already."]
    return []


def _r_flow(world: World) -> list[str]:
    """Helpers dissolve the clot -> flow restored, drops joyful."""
    for helpers in [e for e in world.entities.values() if e.type == "helpers"]:
        if helpers.meters["dissolved"] < THRESHOLD:
            continue
        sig = ("flow", helpers.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        artery = next((e for e in world.entities.values() if e.type == "artery"), None)
        drops = next((e for e in world.entities.values() if e.type == "drops"), None)
        if artery is not None:
            artery.meters["flow"] += 1
        if drops is not None:
            drops.memes["joy"] += 1
        return [f"The {artery.label if artery else 'road'} grew wide again, and the red drops went rushing happily along."]
    return []


def _r_celebration(world: World) -> list[str]:
    """A shared rhyme at the end -> shared celebration meme."""
    for shared in [e for e in world.entities.values() if e.type == "shared"]:
        if shared.meters["rhyme"] < THRESHOLD:
            continue
        sig = ("celebration", shared.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        shared.memes["celebration"] += 1
        return [f"And from that day on, the rhyme was sung whenever a Nuisance came to sit in the road."]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="narrowing", tag="physical", apply=_r_narrowing),
    Rule(name="calm", tag="social", apply=_r_calm),
    Rule(name="flow", tag="physical", apply=_r_flow),
    Rule(name="celebration", tag="social", apply=_r_celebration),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
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
# Verbs.
# ---------------------------------------------------------------------------
def introduce(world: World, artery: Entity) -> None:
    desc = "sat beside a green hill" if world.setting.has_hill else "lay in a sunny fold"
    world.say(
        f"Once upon a time, in the quiet little village of "
        f"{world.setting.village} that {desc}, there was a tiny red road "
        f"called the {artery.label}."
    )
    world.say(
        f"The {artery.label} was the very main road of the village, and every "
        f"drop of red busyness traveled along it to reach the busy Heart at "
        f"the center of town."
    )


def morning_call(world: World, heart: Entity, artery: Entity) -> None:
    world.say(
        f"Now, the Heart was a kind and helpful pump, and every morning it "
        f'would wake and call, "Bring me the red drops so I can send them out '
        f'again!"  And all morning long the {artery.label} hummed and the red '
        f"drops went round and round."
    )


def nuisance_appears(world: World, artery: Entity, nuisance: Nuisance) -> None:
    artery.meters["narrowing"] += 1
    world.say(
        f"But one morning a Nuisance came to the {artery.label}, and the "
        f"Nuisance was {nuisance.phrase}."
    )
    world.say(
        f'"Hmph," said the Nuisance, "I shall sit right here in the middle '
        f'of the road, and the red drops shall have to go around."'
    )


def drops_worry(world: World, artery: Entity) -> None:
    drops = world.get("drops")
    drops.memes["worry"] += 1
    drops.memes["curiosity"] += 1
    world.say(
        f"The red drops tried to go around, but they grew curious and worried, "
        f"and they began to bunch and crowd."
    )
    world.say(
        f'"Oh dear," said the {artery.label}, "I am getting narrow and the road '
        f'is hot.  We need help, dear friends."'
    )


def artery_calls_help(world: World, artery: Entity, helpers_def: Helpers) -> None:
    helpers = world.add(Entity(
        id=helpers_def.id, kind="character", type="helpers",
        label=helpers_def.label, plural=helpers_def.plural,
        traits=["gentle", "jolly"],
    ))
    helpers.meters["busy"] += 1
    world.say(
        f"So the {artery.label} sent a tiny call down to the Heart, and the "
        f"Heart sent little helper cells named {helpers_def.label} -- white, "
        f"round, and jolly -- who came skipping along the road."
    )
    world.say(f"{helpers_def.label} sang a rhyme as they came:")
    world.say(helpers_def.rhyme)


def helpers_work(world: World, helpers_def: Helpers, nuisance: Nuisance) -> None:
    helpers = world.get(helpers_def.id)
    helpers.meters["dissolved"] += 1
    propagate(world, narrate=False)            # narration follows the verbs below
    world.say(
        f"The little {helpers_def.label} {helpers_def.method}, and softened "
        f"the stuck Nuisance until at last it broke apart and floated away."
    )


def shared_rhyme(world: World, artery: Entity, helpers_def: Helpers) -> None:
    shared = world.add(Entity(id="shared", kind="thing", type="shared", label="the village"))
    shared.meters["rhyme"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The red drops went rushing along, singing the rhyme with the "
        f"{helpers_def.label} as they went."
    )


def ending(world: World, artery: Entity, helpers_def: Helpers) -> None:
    world.say(
        f"And from that day on, whenever a Nuisance came to sit in the road, "
        f"the {artery.label} remembered the rhyme, the {helpers_def.label} came "
        f"running, and the village stayed well and warm."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, nuisance: Nuisance, helpers_def: Helpers,
         road_name: str) -> World:
    world = World(setting)
    setting.road = road_name

    artery = world.add(Entity(
        id="artery", kind="thing", type="artery",
        label=road_name, phrase=f"the tiny red road called the {road_name}",
        traits=["main", "red", "humming"],
    ))
    heart = world.add(Entity(
        id="heart", kind="character", type="heart",
        label="Heart", phrase="the busy Heart at the center of town",
        traits=["kind", "helpful"],
    ))
    drops = world.add(Entity(
        id="drops", kind="character", type="drop",
        label="red drops", plural=True, traits=["busy", "tiny"],
    ))

    # Act 1 -- setup.
    introduce(world, artery)
    morning_call(world, heart, artery)

    # Act 2 -- conflict.
    world.para()
    nuisance_appears(world, artery, nuisance)
    drops_worry(world, artery)

    # Act 3 -- resolution (helpers, rhyme, flow).
    world.para()
    artery_calls_help(world, artery, helpers_def)
    helpers_work(world, helpers_def, nuisance)
    shared_rhyme(world, artery, helpers_def)
    ending(world, artery, helpers_def)

    world.facts.update(
        setting=setting, artery=artery, heart=heart, drops=drops,
        nuisance=nuisance, helpers=helpers_def,
        helpers_label=helpers_def.label,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    village: str
    road: str
    nuisance: str
    helpers: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "artery": [
        ("What is an artery?",
         "An artery is a tube that carries blood away from the heart to the "
         "rest of the body."),
        ("Why is the artery important?",
         "The artery is important because it is the road the blood travels on "
         "to bring food and warmth to every part of you."),
    ],
    "nuisance": [
        ("What is a nuisance?",
         "A nuisance is something that gets in the way and causes trouble for "
         "the people or things around it."),
    ],
    "clot": [
        ("What is a clot?",
         "A clot is a small, sticky lump that can form when blood dries or "
         "sticks together inside the body."),
    ],
    "block": [
        ("What is a block in the road?",
         "A block in the road is something solid that stops things from moving "
         "along the way they should go."),
    ],
    "stop": [
        ("What is a stop in the road?",
         "A stop in the road is something that refuses to let things pass, "
         "like a little wall that will not move."),
    ],
    "curiosity": [
        ("What is curiosity?",
         "Curiosity is the feeling of wanting to find out about something new, "
         "the way a small creature peeks around a corner to see what is there."),
    ],
    "sharing": [
        ("What is sharing?",
         "Sharing is letting others use or have some of what you have, so "
         "everyone can enjoy it together."),
        ("Why is sharing helpful?",
         "Sharing is helpful because many hands working together can fix a "
         "problem that no single helper could fix alone."),
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is when two words end with the same sound, like 'flow' and "
         "'go'.  Rhymes make songs and stories feel musical and easy to remember."),
    ],
    "heart": [
        ("What does the heart do?",
         "The heart is a muscle that pumps blood around the body so every "
         "part gets the food and air it needs."),
    ],
}
KNOWLEDGE_ORDER = ["artery", "heart", "nuisance", "clot", "block", "stop",
                   "curiosity", "sharing", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    road = f["artery"].label
    nuisance = f["nuisance"]
    helpers = f["helpers"]
    return [
        f'Write a short Nursery-Rhyme story for a 3-to-5-year-old that uses '
        f'the words "artery" and "nuisance" and ends with the rhyme sung '
        f'together.',
        f"Tell a gentle village tale about a tiny red road called the {road}, "
        f"a stuck {nuisance.label} in its middle, and the {helpers.label} "
        f"helpers who come singing a rhyme to set things right.",
        f"Write a simple rhyming story that names the artery, names a "
        f"nuisance, and shows curiosity and sharing working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting, artery, drops, nuisance, helpers = (
        f["setting"], f["artery"], f["drops"], f["nuisance"], f["helpers"],
    )
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Where is the tiny red road called the {artery.label}, and "
                f"why is it so important to the village of {setting.village}?"
            ),
            answer=(
                f"The {artery.label} runs through the village of {setting.village}, "
                f"and it is the very main road.  Every drop of red busyness "
                f"travels along it to reach the busy Heart at the center of town."
            ),
        ),
        QAItem(
            question=(
                f"What did the red drops love to do each morning along the "
                f"{artery.label} before the Nuisance came?"
            ),
            answer=(
                f"Every morning the Heart would call, and the red drops would "
                f"go round and round along the {artery.label}, humming happily "
                f"as they carried their busyness to the center of town."
            ),
        ),
        QAItem(
            question=(
                f"What kind of Nuisance came to sit in the middle of the "
                f"{artery.label} and what did the red drops do about it?"
            ),
            answer=(
                f"The Nuisance was {nuisance.phrase}.  It sat in the middle of "
                f"the road and refused to move.  The red drops tried to go "
                f"around, but they grew curious and worried and began to bunch "
                f"and crowd."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did the {helpers.label} helpers come to help the "
                f"{artery.label}, and what rhyme did they sing as they came?"
            ),
            answer=(
                f"The {artery.label} sent a tiny call to the Heart, and the "
                f"Heart sent the {helpers.label} helpers, who came skipping "
                f"along the road.  They sang: {helpers.rhyme}"
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What did the {helpers.label} helpers do to the stuck Nuisance "
                f"in the {artery.label}, and how did the road feel afterwards?"
            ),
            answer=(
                f"They {helpers.method} and softened the stuck Nuisance until "
                f"it broke apart and floated away.  The {artery.label} grew "
                f"wide again, and the red drops went rushing happily along, "
                f"singing the rhyme with the helpers."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What did the village of {setting.village} remember to do "
                f"whenever a Nuisance came to sit in the {artery.label} after "
                f"that day?"
            ),
            answer=(
                f"They remembered the rhyme, the {helpers.label} helpers came "
                f"running, and the village stayed well and warm.  Curiosity "
                f"and sharing worked together, and the road stayed clear."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"artery", "nuisance", "rhyme"}
    tags.add(f["nuisance"].id)
    tags.add(f["helpers"].id)
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
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated set used by --all.
CURATED = [
    StoryParams(village="Tinytown",  road="Artery",    nuisance="clot",  helpers="sharing"),
    StoryParams(village="Hillside",  road="Long Lane", nuisance="block", helpers="curiosity"),
    StoryParams(village="Bumblebrook", road="River-Run", nuisance="stop", helpers="sharing"),
    StoryParams(village="Redbridge", road="Pump Path", nuisance="clot",  helpers="curiosity"),
    StoryParams(village="Willow End", road="Artery",   nuisance="block", helpers="sharing"),
]


# ---------------------------------------------------------------------------
# Inline ASP twin (clingo).
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when there is exactly one road, one nuisance, and at least
% one named helper that addresses both Curiosity and Sharing.
valid(V, R, N, H) :- village(V), road(R, V), nuisance(N),
                      helper(H), addresses_curiosity(H),
                      addresses_sharing(H).

% The helpers catalog is split by which value each helper "speaks to".
addresses_curiosity(curiosity).
addresses_sharing(sharing).
addresses_curiosity(sharing).
addresses_sharing(sharing).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for v in VILLAGES:
        lines.append(asp.fact("village", v))
    for r in ROAD_NAMES:
        lines.append(asp.fact("road", r, "any"))
        for v in VILLAGES:
            lines.append(asp.fact("road", r, v))
    for nid, n in NUISANCES.items():
        lines.append(asp.fact("nuisance", nid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Confirm the curated set is a subset of the ASP-valid stories."""
    model = asp_program("#show valid/4.")
    import asp
    atoms = asp.atoms(asp.one_model(model), "valid")
    valid_set = set(atoms)
    bad: list[StoryParams] = []
    for p in CURATED:
        key = (p.village, p.road, p.nuisance, p.helpers)
        if key not in valid_set:
            bad.append(p)
    if not bad:
        print(f"OK: every curated story matches the ASP gate ({len(CURATED)} checked).")
        return 0
    print("MISMATCH: curated stories rejected by ASP gate:")
    for p in bad:
        print(" ", (p.village, p.road, p.nuisance, p.helpers))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny artery, a nuisance, helpers "
                    "who rhyme it better.  Unspecified choices are random.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--road", choices=ROAD_NAMES)
    ap.add_argument("--nuisance", choices=list(NUISANCES))
    ap.add_argument("--helpers", choices=[h.id for h in HELPERS])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true",
                    help="list the (village, road, nuisance, helpers) sets derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the curated set against the inline ASP gate")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    village = args.village or rng.choice(VILLAGES)
    road = args.road or rng.choice(ROAD_NAMES)
    nuisance = args.nuisance or rng.choice(list(NUISANCES))
    helpers = args.helpers or rng.choice([h.id for h in HELPERS])
    if nuisance not in NUISANCES:
        raise StoryError(
            f"(No story: nuisance {nuisance!r} is not in the registry "
            f"{sorted(NUISANCES)}.)")
    if helpers not in {h.id for h in HELPERS}:
        raise StoryError(
            f"(No story: helpers {helpers!r} is not in the registry "
            f"{sorted(h.id for h in HELPERS)}.)")
    return StoryParams(village=village, road=road, nuisance=nuisance, helpers=helpers)


def generate(params: StoryParams) -> StorySample:
    setting = Setting(village=params.village, road=params.road)
    nuisance = NUISANCES[params.nuisance]
    helpers_def = next(h for h in HELPERS if h.id == params.helpers)
    world = tell(setting, nuisance, helpers_def, params.road)
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
        valid = asp_valid_stories()
        print(f"{len(valid)} valid (village, road, nuisance, helpers) tuples:\n")
        for v, r, n, h in valid:
            print(f"  {v:11} {r:10} {n:6} {h}")
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
            header = f"### {p.village}: {p.nuisance} on the {p.road} ({p.helpers})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
