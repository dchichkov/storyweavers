#!/usr/bin/env python3
"""
storyworlds/worlds/stick_suspense_repetition_teamwork_folk_tale.py
===================================================================

A small folk-tale storyworld about a clever stick, a risky crossing, and
friends who solve the problem together.

Seed tale (imagined from the prompt):
---
A little rabbit wanted to bring warm berry bread to Grandmother across a creek.
The stepping stones looked slippery, and the current hid under the reeds.
A fox found a long stick, and the friends used it to test each stone, one by
one, while repeating a careful chant. Together they crossed safely and shared
the bread at the far bank.

World idea:
---
A small group of forest friends must cross a creek with a basket of bread.
A stick can be used as a probe and balancing pole. The story builds suspense
through repeated checks, a wobbling stone, and the dark water below. The turn
comes when the friends work as a team and the stick becomes a shared tool.

Causal state updates:
---
    careful testing with the stick   -> steadiness += 1, fear += 1 at first
    a wobbly stone                   -> suspense += 1, danger += 1
    friends coordinating together    -> teamwork += 1, fear -= 1, hope += 1
    safe crossing                    -> relief += 1, hunger lowers, basket stays dry

Narrative instruments:
---
    Suspense     -> the creek, the wobble, the pause before each step
    Repetition   -> "tap, tap", "one step, then another", a repeated chant
    Teamwork     -> each friend takes a role with the stick and the basket
    Folk-tale    -> simple forest roles, rhythmic prose, warm ending image
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TITLE = "The Stick and the Creek"

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("wet", "steadiness", "danger", "hunger"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "hope", "teamwork", "relief", "patience"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "goose", "grandmother", "aunt"}
        male = {"boy", "father", "fox", "rabbit", "badger", "bear", "mole"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    creek_name: str
    crossing: str
    far_side: str


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper1: str
    helper2: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "mossy_creek": Setting(
        place="the mossy creek",
        creek_name="Mossy Creek",
        crossing="stepping stones",
        far_side="the alder bank",
    ),
    "pine_brook": Setting(
        place="the pine brook",
        creek_name="Pine Brook",
        crossing="flat stones",
        far_side="the hill path",
    ),
    "silver_rill": Setting(
        place="the silver rill",
        creek_name="Silver Rill",
        crossing="small river stones",
        far_side="Grandmother's gate",
    ),
}

CHARACTERS = {
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "fox": {"type": "fox", "label": "fox"},
    "mole": {"type": "mole", "label": "mole"},
    "goose": {"type": "goose", "label": "goose"},
    "bear": {"type": "bear", "label": "bear"},
}

STICKS = {
    "long_stick": {
        "label": "long stick",
        "phrase": "a long, smooth stick",
        "length": "long",
        "purpose": "test the stones and steady a crossing",
    },
    "forked_stick": {
        "label": "forked stick",
        "phrase": "a forked stick with a sturdy end",
        "length": "forked",
        "purpose": "hook the basket and keep balance",
    },
    "walking_stick": {
        "label": "walking stick",
        "phrase": "a wooden walking stick",
        "length": "steady",
        "purpose": "help a careful step on the bank",
    },
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/5.
#show needs_stick/2.
#show teamwork_fix/3.

needs_stick(H, S) :- hero(H), setting(S), creek(S).
teamwork_fix(H, H1, H2) :- needs_stick(H, S), helper(H1), helper(H2), H1 != H2.
valid_story(S, H, H1, H2, Stick) :- needs_stick(H, S), teamwork_fix(H, H1, H2), stick(Stick).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("creek", sid))
    for cid, c in CHARACTERS.items():
        lines.append(asp.fact("character", cid))
        lines.append(asp.fact("hero", cid))
        lines.append(asp.fact("helper", cid))
    for stid in STICKS:
        lines.append(asp.fact("stick", stid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    return 0 if asp_valid_combos() else 1

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a stick, suspense, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=CHARACTERS)
    ap.add_argument("--helper1", choices=CHARACTERS)
    ap.add_argument("--helper2", choices=CHARACTERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(CHARACTERS))
    helper1 = args.helper1 or rng.choice([k for k in CHARACTERS if k != hero])
    helper2 = args.helper2 or rng.choice([k for k in CHARACTERS if k != hero and k != helper1])
    if hero in {helper1, helper2} or helper1 == helper2:
        raise StoryError("helpers must be different characters from the hero and from each other.")
    return StoryParams(setting=setting, hero=hero, helper1=helper1, helper2=helper2)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(id="hero", kind="character", type=CHARACTERS[params.hero]["type"], label=params.hero))
    h1 = world.add(Entity(id="helper1", kind="character", type=CHARACTERS[params.helper1]["type"], label=params.helper1))
    h2 = world.add(Entity(id="helper2", kind="character", type=CHARACTERS[params.helper2]["type"], label=params.helper2))
    stick_def = STICKS["long_stick"] if params.setting != "silver_rill" else STICKS["forked_stick"]

    stick = world.add(Entity(id="stick", kind="thing", type="stick", label=stick_def["label"], phrase=stick_def["phrase"], owner=hero.id))
    basket = world.add(Entity(id="basket", kind="thing", type="basket", label="basket of berry bread", phrase="a basket of warm berry bread", owner=hero.id))
    basket.meters["wet"] = 0.0
    basket.memes["hope"] = 1.0

    world.facts.update(
        hero=hero,
        helper1=h1,
        helper2=h2,
        stick=stick,
        basket=basket,
        setting=setting,
        stick_def=stick_def,
        params=params,
    )
    return world


def _tap(world: World, speaker: Entity, text: str) -> None:
    world.say(f"{speaker.label.capitalize()} said, \"{text}\"")


def _story_setup(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    h1: Entity = f["helper1"]
    h2: Entity = f["helper2"]
    basket: Entity = f["basket"]
    stick_def = f["stick_def"]

    world.say(
        f"Once in {world.setting.place}, {hero.label} carried {basket.phrase} and wished to reach {world.setting.far_side}."
    )
    world.say(
        f"Beside {hero.pronoun('object')} walked {h1.label} and {h2.label}, and together they had {stick_def['phrase']}."
    )
    world.say(
        f"They had heard that {world.setting.creek_name} could look calm and still hide a slippery pull below the reeds."
    )
    world.para()

    hero.memes["hope"] += 1
    hero.memes["fear"] += 1
    basket.meters["wet"] += 0
    world.say(
        f"{hero.label} looked at the water and felt a little shiver of fear, but the warm bread made {hero.pronoun('object')} keep going."
    )
    world.say(
        f"{h1.label} lifted the stick and said they would test each stone before anyone stepped out."
    )
    world.say("Tap, tap, tap, the stick went against the first stone.")


def _suspense_turn(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    h1: Entity = f["helper1"]
    h2: Entity = f["helper2"]
    basket: Entity = f["basket"]

    hero.memes["fear"] += 1
    h1.memes["patience"] += 1
    h2.memes["patience"] += 1
    world.para()
    world.say(
        f"The first stone held, and then the second held, but the third stone wobbled under the tip of the stick."
    )
    world.say(
        f"Everyone stopped at once. The creek whispered under them, and the basket of berry bread seemed suddenly very heavy."
    )
    world.say(
        f"\"Tap it again,\" said {h2.label}. \"One step, then another,\" said {h1.label}. \"One step, then another,\" they all repeated."
    )
    world.say(
        f"{hero.label} gripped the basket tighter while {h1.label} steadied the stick and {h2.label} watched the far bank for a safe place to land."
    )

    world.facts["wobble"] = True
    world.facts["suspense"] = True
    basket.memes["hope"] += 0.5
    basket.meters["wet"] += 0.0


def _teamwork_resolution(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    h1: Entity = f["helper1"]
    h2: Entity = f["helper2"]
    basket: Entity = f["basket"]
    stick: Entity = f["stick"]

    hero.memes["teamwork"] += 1
    h1.memes["teamwork"] += 1
    h2.memes["teamwork"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    hero.memes["hope"] += 1
    h1.memes["hope"] += 1
    h2.memes["hope"] += 1

    world.para()
    world.say(
        f"Then the three friends made a plan as old as the trees: one held the basket, one held the stick, and one called out the safe stones."
    )
    world.say(
        f"{h1.label} pressed the stick to the creek bed, {h2.label} took the basket from {hero.pronoun('object')}, and {hero.label} stepped only where the stick said the stone was firm."
    )
    world.say(
        f"Tap, tap, step. Tap, tap, step. The rhythm carried them forward like a song."
    )
    world.say(
        f"At last they reached {world.setting.far_side}, and the basket was still dry, and warm berry bread filled the air with a sweet smell."
    )
    world.say(
        f"{hero.label} laughed, {h1.label} laughed, and {h2.label} laughed too, for the creek had been crossed not by one brave heart, but by three friends working together."
    )

    world.facts["safe"] = True
    world.facts["resolved"] = True
    basket.meters["wet"] = 0.0
    basket.memes["relief"] += 1
    stick.memes["teamwork"] += 1


def _ending_image(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    basket: Entity = f["basket"]
    world.para()
    world.say(
        f"By the time the sun leaned low, {hero.label} was walking beside {basket.label} on the far bank, while the stick rested like a small brown staff in {hero.pronoun('possessive')} hand."
    )
    world.say(
        f"The creek still murmured behind them, but it sounded gentle now, as if it had told its test and found the friends wise enough to listen."
    )


def tell_world(params: StoryParams) -> World:
    world = _build_world(params)
    _story_setup(world)
    _suspense_turn(world)
    _teamwork_resolution(world)
    _ending_image(world)
    return world

# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        "Write a short folk tale about a stick that helps friends cross a dangerous creek.",
        f"Tell a suspenseful story where {p.hero} and two helpers use a stick, repeat a careful chant, and reach the far bank together.",
        "Write a child-friendly forest story with repetition, teamwork, and a safe ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    h1: Entity = f["helper1"]
    h2: Entity = f["helper2"]
    basket: Entity = f["basket"]
    stick: Entity = f["stick"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who carried the basket of berry bread at the beginning of the story?",
            answer=f"{hero.label} carried the basket of berry bread and wanted to reach {setting.far_side}.",
        ),
        QAItem(
            question=f"What did the friends use to test the stones in {setting.creek_name}?",
            answer=f"They used {stick.phrase} to tap each stone before stepping on it.",
        ),
        QAItem(
            question=f"Why did everyone stop when the stick touched the third stone?",
            answer="They stopped because the third stone wobbled, and the creek suddenly felt dangerous.",
        ),
        QAItem(
            question=f"How did the friends cross safely in the end?",
            answer=f"{h1.label} held the stick, {h2.label} watched the path, and {hero.label} stepped only on the firm stones while they worked together.",
        ),
        QAItem(
            question=f"What was special about the ending?",
            answer=f"The basket stayed dry, the bread was still warm, and the friends reached {setting.far_side} together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stick good for in a forest tale?",
            answer="A stick can help test the ground, steady a step, or reach something that is hard to touch.",
        ),
        QAItem(
            question="Why do stories repeat words like 'tap, tap, step'?",
            answer="Repeating words can make a story feel musical, careful, and suspenseful, like a chant the characters share.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people or animals help one another and share the work so a hard job becomes possible.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that could produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from this story ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions -- child-level knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Trace / generation
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main / modes
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="mossy_creek", hero="rabbit", helper1="fox", helper2="mole"),
    StoryParams(setting="pine_brook", hero="goose", helper1="rabbit", helper2="fox"),
    StoryParams(setting="silver_rill", hero="bear", helper1="goose", helper2="mole"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible story tuples")
        for row in models:
            print(" ".join(map(str, row)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.hero} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
