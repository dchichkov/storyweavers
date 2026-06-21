#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/unicycle_slave_nanny_bad_ending_rhyming_story.py
============================================================================

A standalone storyworld for a small rhyming cautionary tale: a child wants to
show off on a unicycle, waves around an old card bearing the hurtful word
"slave," ignores a nanny's warning, and suffers a bad ending after a fall.

The world model keeps the focus on sensible, child-facing safety:
- the word "slave" appears only as a hurtful old label on an object from a box,
  and the nanny explicitly corrects it;
- the real conflict is physical risk: riding a unicycle on an unsafe surface
  while carrying something and hurrying;
- the ending is bad, but not catastrophic: the child is bruised, the toy is
  broken, the show is spoiled, and the lesson lands.

The prose is rendered in simple rhyming couplets driven by simulated state.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RISK_LIMIT = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nanny"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"nanny": "nanny", "mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    surface: str
    hazard: int
    line1: str
    line2: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    heavy: int
    wobble: int
    old_label: str
    line1: str
    line2: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pace:
    id: str
    label: str
    extra_risk: int
    line1: str
    line2: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    cargo: str
    pace: str
    child_name: str
    child_gender: str
    nanny_name: str
    nanny_style: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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


PLACES = {
    "hall": Place(
        id="hall",
        label="hall",
        scene="the long front hall",
        surface="smooth floorboards",
        hazard=1,
        line1="The long hall shone with stripe and wall,",
        line2="and little wheels made clicky calls.",
        tags={"hall", "inside"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="kitchen",
        scene="the busy kitchen doorway",
        surface="slick tiles",
        hazard=2,
        line1="The kitchen tiles were bright and slick,",
        line2="a shiny place for slips too quick.",
        tags={"kitchen", "tiles"},
    ),
    "stairs": Place(
        id="stairs",
        label="stairs",
        scene="the top of the stairs",
        surface="steep steps",
        hazard=3,
        line1="The stair tops waited, steep and tall,",
        line2="the worst small place for wheels at all.",
        tags={"stairs", "fall"},
    ),
}

CARGO = {
    "card": Cargo(
        id="card",
        label="old card",
        phrase="an old paper card",
        heavy=0,
        wobble=1,
        old_label="slave",
        line1='From a dusty box came one old card,',
        line2='with ugly print that landed hard.',
        tags={"card", "word"},
    ),
    "puppet": Cargo(
        id="puppet",
        label="rag puppet",
        phrase="a rag puppet from the attic box",
        heavy=1,
        wobble=1,
        old_label="slave",
        line1="A rag puppet with one button eye",
        line2='had a faded tag from days gone by.',
        tags={"puppet", "toy", "word"},
    ),
    "tray": Cargo(
        id="tray",
        label="tin tray",
        phrase="a wobbling tin tray from dress-up play",
        heavy=1,
        wobble=2,
        old_label="slave",
        line1="A tin tray rattled in the light,",
        line2='with an old stamped word that was not right.',
        tags={"tray", "word"},
    ),
}

PACES = {
    "slow": Pace(
        id="slow",
        label="slowly",
        extra_risk=0,
        line1="At first the child rolled small and slow,",
        line2="with careful toes and cautious flow.",
        tags={"slow"},
    ),
    "showoff": Pace(
        id="showoff",
        label="showing off",
        extra_risk=1,
        line1="Then pride puffed up the little ride,",
        line2="and show-off thoughts swelled up inside.",
        tags={"showoff"},
    ),
    "rush": Pace(
        id="rush",
        label="rushing",
        extra_risk=2,
        line1="Then hurry hummed, 'Go fast! Go fast!'",
        line2="and careful chances blew right past.",
        tags={"rush"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tessa", "Nora", "Molly", "Ada"]
BOY_NAMES = ["Milo", "Theo", "Benji", "Rowan", "Felix", "Owen"]
NANNY_NAMES = ["Nanny June", "Nanny Bea", "Nanny Ruth", "Nanny May"]
NANNY_STYLES = ["gentle", "firm", "calm"]


def risk_score(place: Place, cargo: Cargo, pace: Pace) -> int:
    return place.hazard + cargo.heavy + cargo.wobble + pace.extra_risk


def valid_combo(place: Place, cargo: Cargo, pace: Pace) -> bool:
    return risk_score(place, cargo, pace) >= RISK_LIMIT


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for cargo_id, cargo in CARGO.items():
            for pace_id, pace in PACES.items():
                if valid_combo(place, cargo, pace):
                    out.append((place_id, cargo_id, pace_id))
    return out


def explain_rejection(place: Place, cargo: Cargo, pace: Pace) -> str:
    score = risk_score(place, cargo, pace)
    return (
        f"(No story: {place.label} + {cargo.label} + {pace.label} is not risky enough "
        f"for this bad-ending world (risk={score} < {RISK_LIMIT}). Pick steeper stairs, "
        f"a wobblier object, or a faster pace.)"
    )


def line_pair(a: str, b: str) -> str:
    return f"{a}\n{b}"


def introduce(world: World, child: Entity, nanny: Entity, place: Place) -> None:
    world.say(
        line_pair(
            f"{child.id} found a unicycle bright and small,",
            f"and begged to ride through {place.scene} and all.",
        )
    )
    world.say(
        line_pair(
            f"{nanny.id} watched with eyes that cared,",
            f"and stayed nearby because {nanny.pronoun()} was prepared.",
        )
    )
    child.memes["joy"] += 1
    child.meters["balance"] += 1


def find_cargo(world: World, child: Entity, nanny: Entity, cargo: Cargo) -> None:
    world.say(line_pair(cargo.line1, cargo.line2))
    world.say(
        line_pair(
            f'{child.id} read the word "{cargo.old_label}" with a grin,',
            f"but {nanny.id} said, \"That hurtful word should not stay in.\"",
        )
    )
    world.say(
        line_pair(
            f'"We never call a person that," {nanny.id} said right away,',
            f'"it is an old cruel word, so we choose kinder words today."',
        )
    )
    child.memes["defiance"] += 1
    world.facts["corrected_word"] = True


def attempt(world: World, child: Entity, place: Place, cargo: Cargo, pace: Pace) -> None:
    world.para()
    world.say(line_pair(place.line1, place.line2))
    world.say(line_pair(pace.line1, pace.line2))
    world.say(
        line_pair(
            f"Yet {child.id} grabbed {cargo.phrase} tight,",
            f"and climbed the unicycle for a circus sight.",
        )
    )
    child.meters["load"] += cargo.heavy + cargo.wobble
    child.meters["risk"] += risk_score(place, cargo, pace)
    if pace.extra_risk >= 1:
        child.memes["pride"] += 1
    if pace.extra_risk >= 2:
        child.memes["hurry"] += 1


def warn(world: World, child: Entity, nanny: Entity, place: Place, cargo: Cargo, pace: Pace) -> None:
    risk = risk_score(place, cargo, pace)
    level = "too wild" if risk >= 5 else "not safe"
    world.say(
        line_pair(
            f'"Please stop," said {nanny.id}, "that ride is {level} now,',
            f'{place.surface} and extra cargo do not mix somehow."',
        )
    )
    world.say(
        line_pair(
            f'"Put down the {cargo.label} and climb right back to floor,',
            f'"a unicycle is for one small job, not one thing more."',
        )
    )
    child.memes["warned"] += 1


def fall(world: World, child: Entity, cargo: Cargo, place: Place) -> None:
    world.para()
    severity = risk_score(place, cargo, PACES[world.facts["pace"].id])
    child.meters["fell"] += 1
    child.meters["bruise"] += 1
    if severity >= 5:
        child.meters["big_cry"] += 1
    world.say(
        line_pair(
            "The wheel gave one sharp wobble, then one sickening slide,",
            f"and down went child and cargo from the shaky ride.",
        )
    )
    if place.id == "stairs":
        world.say(
            line_pair(
                "Bump-bump the unicycle knocked on every stair,",
                "and clattery fear flew thick through all the air.",
            )
        )
    else:
        world.say(
            line_pair(
                "The floor flashed hard and far too near,",
                "and play turned in a blink to pain and fear.",
            )
        )
    child.memes["fear"] += 1
    world.facts["fell"] = True


def damage(world: World, child: Entity, cargo: Cargo, nanny: Entity) -> None:
    world.say(
        line_pair(
            f"The {cargo.label} broke with a papery snap or tinny clang,",
            "and all the proud pretend-show ended with a bang.",
        )
    )
    world.say(
        line_pair(
            f"{child.id} held a bruised knee and cried and cried,",
            f"while {nanny.id} wrapped {child.pronoun('possessive')} arms and stayed beside.",
        )
    )
    world.facts["broken_cargo"] = cargo.label
    world.facts["injury"] = "bruised knee"


def bad_ending(world: World, child: Entity, nanny: Entity) -> None:
    world.say(
        line_pair(
            "No claps arrived, no cheerful tune,",
            "just tears and silence in the room.",
        )
    )
    world.say(
        line_pair(
            f'{nanny.id} said softly, "Brave means stopping too,"',
            f"but the bad end stayed because {child.id} did not do.",
        )
    )
    world.say(
        line_pair(
            "The unicycle leaned still against the wall that night,",
            "a lonely wheel in pale and sorry light.",
        )
    )
    child.memes["regret"] += 1
    world.facts["outcome"] = "bad"


def tell(
    place: Place,
    cargo: Cargo,
    pace: Pace,
    child_name: str,
    child_gender: str,
    nanny_name: str,
    nanny_style: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            attrs={"nanny_style": nanny_style},
        )
    )
    nanny = world.add(
        Entity(
            id=nanny_name,
            kind="character",
            type="nanny",
            label="the nanny",
            role="nanny",
            attrs={"style": nanny_style},
        )
    )
    uni = world.add(
        Entity(
            id="unicycle",
            kind="thing",
            type="unicycle",
            label="unicycle",
            phrase="a small red unicycle",
            tags={"unicycle", "wheel"},
        )
    )
    prop = world.add(
        Entity(
            id="cargo",
            kind="thing",
            type="cargo",
            label=cargo.label,
            phrase=cargo.phrase,
            attrs={"old_label": cargo.old_label},
            tags=set(cargo.tags),
        )
    )
    room = world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=place.label,
            phrase=place.scene,
            tags=set(place.tags),
        )
    )

    world.facts.update(
        child=child,
        nanny=nanny,
        unicycle=uni,
        cargo=prop,
        cargo_cfg=cargo,
        place=room,
        place_cfg=place,
        pace=pace,
        risk=risk_score(place, cargo, pace),
    )

    introduce(world, child, nanny, place)
    world.para()
    find_cargo(world, child, nanny, cargo)
    attempt(world, child, place, cargo, pace)
    warn(world, child, nanny, place, cargo, pace)
    fall(world, child, cargo, place)
    damage(world, child, cargo, nanny)
    world.para()
    bad_ending(world, child, nanny)
    return world


KNOWLEDGE = {
    "unicycle": [
        (
            "What is a unicycle?",
            "A unicycle is a cycle with one wheel instead of two. It takes a lot of balance, so it should be used carefully in a safe place."
        )
    ],
    "nanny": [
        (
            "What does a nanny do?",
            "A nanny is a grown-up who helps care for children. A good nanny watches closely, keeps children safe, and gives calm rules."
        )
    ],
    "stairs": [
        (
            "Why are stairs dangerous for wheels?",
            "Stairs go up and down in steps, so wheels can bounce and slip on them. That makes falling much more likely."
        )
    ],
    "tiles": [
        (
            "Why can tile floors be slippery?",
            "Tiles can feel smooth and slick under wheels or shoes. If something wobbles, it can slide faster than you expect."
        )
    ],
    "hurtful_word": [
        (
            'Why was the word "slave" corrected in the story?',
            'Because "slave" is a cruel word tied to people being owned and hurt. The nanny was right to say we should never call a person that.'
        )
    ],
    "balance": [
        (
            "Why is carrying extra things hard on a unicycle?",
            "A unicycle already needs balance from your whole body. Carrying something extra can make you wobble and lose control."
        )
    ],
    "hurry": [
        (
            "Why can hurrying make accidents happen?",
            "When you hurry, you stop noticing little dangers. Fast choices can turn a small wobble into a fall."
        )
    ],
}

KNOWLEDGE_ORDER = ["unicycle", "nanny", "stairs", "tiles", "balance", "hurry", "hurtful_word"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    nanny = f["nanny"]
    cargo = f["cargo_cfg"]
    place = f["place_cfg"]
    pace = f["pace"]
    return [
        'Write a short rhyming cautionary story for a 3-to-5-year-old that includes the words "unicycle", "slave", and "nanny", and ends badly.',
        f"Tell a rhyming story where {child.id} ignores {nanny.id}'s warning, rides a unicycle in {place.scene}, and falls while carrying {cargo.phrase}.",
        f'Write a child-facing poem-story where the hurtful old word "{cargo.old_label}" is corrected by a nanny, but the child still makes an unsafe choice and the ending stays sad.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    nanny = f["nanny"]
    cargo = f["cargo_cfg"]
    place = f["place_cfg"]
    pace = f["pace"]
    risk = f["risk"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child trying to show off on a unicycle, and {nanny.id}, the nanny who tried to keep things safe."
        ),
        (
            f'Why did {nanny.id} correct the word "{cargo.old_label}"?',
            f"{nanny.id} said it was a hurtful old word and should not be used for people. That correction mattered because the nanny was teaching kindness before the fall even happened."
        ),
        (
            f"Why was the ride unsafe?",
            f"The ride was unsafe because {child.id} was on a unicycle in {place.scene} while carrying {cargo.phrase}. That mix made the balance problem worse, and the {pace.label} pace pushed the risk even higher."
        ),
        (
            f"What happened when {child.id} ignored the warning?",
            f"{child.id} fell off the unicycle, bruised a knee, and the {cargo.label} broke. The bad ending came from not stopping when the nanny said the ride was not safe."
        ),
        (
            "How did the story end?",
            "It ended sadly, with no show, a crying child, and a lonely unicycle left still by the wall. The ending proves that pride and hurry can spoil play instead of making it grand."
        ),
    ]
    if risk >= 5:
        qa.append(
            (
                f"Why was this a very dangerous choice instead of a small mistake?",
                f"It was very dangerous because the place itself was hard for wheels, and carrying extra cargo added even more wobble. Once {child.id} hurried in spite of the warning, a fall became much more likely."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"unicycle", "nanny", "balance", "hurtful_word"}
    place = f["place_cfg"]
    pace = f["pace"]
    if place.id == "stairs":
        tags.add("stairs")
    if place.id == "kitchen":
        tags.add("tiles")
    if pace.id == "rush":
        tags.add("hurry")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    facts = {k: v for k, v in world.facts.items() if k in {"risk", "outcome", "injury", "broken_cargo", "fell", "corrected_word"}}
    if facts:
        lines.append(f"  facts={facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="stairs",
        cargo="tray",
        pace="rush",
        child_name="Milo",
        child_gender="boy",
        nanny_name="Nanny June",
        nanny_style="firm",
    ),
    StoryParams(
        place="kitchen",
        cargo="puppet",
        pace="showoff",
        child_name="Lila",
        child_gender="girl",
        nanny_name="Nanny Bea",
        nanny_style="gentle",
    ),
    StoryParams(
        place="hall",
        cargo="tray",
        pace="rush",
        child_name="Theo",
        child_gender="boy",
        nanny_name="Nanny May",
        nanny_style="calm",
    ),
    StoryParams(
        place="stairs",
        cargo="card",
        pace="slow",
        child_name="Nora",
        child_gender="girl",
        nanny_name="Nanny Ruth",
        nanny_style="firm",
    ),
]


ASP_RULES = r"""
risk(P,C,A,S) :- place_hazard(P,PH), cargo_heavy(C,CH), cargo_wobble(C,CW), pace_risk(A,AR), S = PH + CH + CW + AR.
valid(P,C,A) :- risk(P,C,A,S), risk_limit(L), S >= L.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("place_hazard", place_id, place.hazard))
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("cargo_heavy", cargo_id, cargo.heavy))
        lines.append(asp.fact("cargo_wobble", cargo_id, cargo.wobble))
    for pace_id, pace in PACES.items():
        lines.append(asp.fact("pace", pace_id))
        lines.append(asp.fact("pace_risk", pace_id, pace.extra_risk))
    lines.append(asp.fact("risk_limit", RISK_LIMIT))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "unicycle" not in sample.story or "nanny" not in sample.story or "slave" not in sample.story:
            raise StoryError("Smoke test failed: generated story missing required seed words or empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming bad-ending storyworld: an unsafe unicycle ride, a nanny's warning, and a sad result."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--pace", choices=PACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--nanny-name", choices=NANNY_NAMES)
    ap.add_argument("--nanny-style", choices=NANNY_STYLES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cargo and args.pace:
        place = PLACES[args.place]
        cargo = CARGO[args.cargo]
        pace = PACES[args.pace]
        if not valid_combo(place, cargo, pace):
            raise StoryError(explain_rejection(place, cargo, pace))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.pace is None or combo[2] == args.pace)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cargo_id, pace_id = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    nanny_name = args.nanny_name or rng.choice(NANNY_NAMES)
    nanny_style = args.nanny_style or rng.choice(NANNY_STYLES)
    return StoryParams(
        place=place_id,
        cargo=cargo_id,
        pace=pace_id,
        child_name=child_name,
        child_gender=child_gender,
        nanny_name=nanny_name,
        nanny_style=nanny_style,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.cargo not in CARGO:
        raise StoryError(f"(Invalid cargo: {params.cargo})")
    if params.pace not in PACES:
        raise StoryError(f"(Invalid pace: {params.pace})")
    world = tell(
        place=PLACES[params.place],
        cargo=CARGO[params.cargo],
        pace=PACES[params.pace],
        child_name=params.child_name,
        child_gender=params.child_gender,
        nanny_name=params.nanny_name,
        nanny_style=params.nanny_style,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cargo, pace) combos:\n")
        for place, cargo, pace in combos:
            print(f"  {place:8} {cargo:7} {pace}")
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
            header = f"### {p.child_name}: {p.place}, {p.cargo}, {p.pace}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
