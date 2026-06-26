#!/usr/bin/env python3
"""
A small detective-story world where a child detective follows a cluster of steam,
learns a moral value, and ends with a clear lesson learned.

The mystery is always child-facing and concrete:
- a warm source makes a cluster of steam
- someone makes a quick, unfair guess
- the detective checks the clues
- the truth is kinder than the guess
- the story ends with a moral value and a lesson learned

This file is standalone and follows the Storyweavers contract.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    source: str
    steam_shape: str
    source_label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Value:
    id: str
    label: str
    moral: str
    lesson: str
    color: str


@dataclass
class Case:
    id: str
    clue: str
    suspicion: str
    truth: str
    resolution: str
    steam_reason: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        indoors=True,
        source="kettle",
        steam_shape="a cluster of steam",
        source_label="the kettle",
        affords={"boil", "investigate"},
    ),
    "laundry": Setting(
        place="the laundry room",
        indoors=True,
        source="dryer",
        steam_shape="a cluster of warm steam",
        source_label="the dryer vent",
        affords={"boil", "investigate"},
    ),
    "bathroom": Setting(
        place="the bathroom",
        indoors=True,
        source="shower",
        steam_shape="a foggy cluster of steam",
        source_label="the shower",
        affords={"boil", "investigate"},
    ),
}

VALUES = {
    "honesty": Value(
        id="honesty",
        label="honesty",
        moral="tell the truth before making a guess",
        lesson="It is better to ask and check than to blame too fast.",
        color="bright blue",
    ),
    "kindness": Value(
        id="kindness",
        label="kindness",
        moral="be gentle with people when a mystery feels scary",
        lesson="A kind question can solve a problem without hurting anyone.",
        color="soft yellow",
    ),
    "care": Value(
        id="care",
        label="care",
        moral="look after shared things and tidy up after yourself",
        lesson="A careful helper can fix a mess before it grows bigger.",
        color="green",
    ),
}

CASES = {
    "kettle_mistake": Case(
        id="kettle_mistake",
        clue="a shiny window with a damp circle",
        suspicion="someone thought the circle was a ghost",
        truth="the kettle had made steam that gathered into a cluster on the glass",
        resolution="the detective opened the lid and showed the warm water underneath",
        steam_reason="hot water made steam that rose and collected together",
        tags={"steam", "window", "kitchen"},
    ),
    "dryer_hiss": Case(
        id="dryer_hiss",
        clue="tiny wet dots near a humming vent",
        suspicion="someone thought the vent was leaking",
        truth="the dryer had puffed warm air that turned into steam near the cool wall",
        resolution="the detective found a towel left over the vent and moved it away",
        steam_reason="warm air met cool air and made a little cluster of moisture",
        tags={"steam", "laundry"},
    ),
    "shower_fog": Case(
        id="shower_fog",
        clue="a foggy mirror with one clear handprint",
        suspicion="someone thought the bathroom was haunted",
        truth="the shower had filled the room with steam that gathered in a cluster",
        resolution="the detective cracked the door open and let the fog drift away",
        steam_reason="hot water made steam that liked to hang in a warm room",
        tags={"steam", "bathroom"},
    ),
}

HEROES = [
    ("Mina", "girl", "mother"),
    ("Noah", "boy", "father"),
    ("Ivy", "girl", "father"),
    ("Ben", "boy", "mother"),
]

TRAITS = ["careful", "curious", "brave", "patient", "sharp-eyed"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    case: str
    value: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CASES:
            for vid in VALUES:
                combos.append((sid, cid, vid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world about steam, clues, and moral lessons.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    sid = args.setting or rng.choice(list(SETTINGS))
    cid = args.case or rng.choice(list(CASES))
    vid = args.value or rng.choice(list(VALUES))

    hero_name, hero_gender, hero_parent = rng.choice(HEROES)
    gender = args.gender or hero_gender
    parent = args.parent or hero_parent
    name = args.name or hero_name
    trait = args.trait or rng.choice(TRAITS)

    if args.gender and args.gender != hero_gender and not args.name:
        # still okay; choose a matching name for requested gender
        name, _, parent = rng.choice([h for h in HEROES if h[1] == args.gender])

    return StoryParams(
        setting=sid,
        case=cid,
        value=vid,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def _pronoun_word(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    case = CASES[params.case]
    value = VALUES[params.value]

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=case.clue, location=setting.place))
    source = world.add(Entity(
        id=setting.source,
        kind="thing",
        type=setting.source,
        label=setting.source_label,
        location=setting.place,
        meters={"heat": 1.0, "steam": 0.0},
        tags={"steam", setting.source},
    ))
    value_token = world.add(Entity(
        id=value.id,
        kind="thing",
        type="value",
        label=value.label,
        phrase=value.moral,
        meters={"glow": 1.0},
        tags={value.id, "lesson"},
    ))

    hero.memes["curiosity"] = 1.0
    hero.memes["confidence"] = 1.0

    world.say(
        f"{hero.label} was a {params.trait} little detective who liked quiet mysteries."
    )
    world.say(
        f"One day, {hero.label} and {hero.pronoun('possessive')} {params.parent} went to {setting.place}, "
        f"where {setting.source_label} gave off {setting.steam_shape}."
    )
    world.say(
        f"{hero.label} noticed {case.clue}, and that made {hero.pronoun('subject')} stop and think."
    )

    world.para()
    source.meters["steam"] = 1.0
    clue.meters["damp"] = 1.0
    hero.memes["suspicion"] = 1.0
    world.say(
        f"A tiny {case.suspicion} spread through the room, because the steam looked odd from far away."
    )
    world.say(
        f"{hero.label} did not guess right away. {hero.pronoun('subject').capitalize()} looked closer at the clue, "
        f"followed the warm air, and found the truth."
    )
    world.say(
        f"The truth was simple: {case.truth}."
    )

    world.para()
    hero.memes["relief"] = 1.0
    parent.memes["pride"] = 1.0
    world.say(
        f"{case.resolution.capitalize()}, and the scary guess faded into nothing."
    )
    world.say(
        f"{hero.label} smiled, because the mystery was solved without blaming anyone."
    )
    world.say(
        f"The case taught {value.label}: {value.lesson}"
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        clue=clue,
        source=source,
        value=value,
        case=case,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    case: Case = f["case"]  # type: ignore[assignment]
    value: Value = f["value"]  # type: ignore[assignment]
    return [
        f'Write a short detective story for a small child that includes "{case.clue}" and the word "steam".',
        f"Tell a gentle mystery where {hero.label} checks clues before blaming anyone, and the story ends with {value.label}.",
        f"Write a story in which a child detective solves a steam mystery in {world.setting.place} and learns a lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    case: Case = f["case"]  # type: ignore[assignment]
    value: Value = f["value"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who solved the mystery in {setting.place}?",
            answer=f"{hero.label} solved it by looking closely instead of guessing too fast.",
        ),
        QAItem(
            question=f"What made the cluster of steam?",
            answer=f"{setting.source_label} made the steam, and it gathered into a cluster near the cool surface.",
        ),
        QAItem(
            question=f"What did {hero.label} learn from the case?",
            answer=f"{hero.label} learned {value.label}: {value.lesson}",
        ),
        QAItem(
            question=f"Why did the mystery seem scary at first?",
            answer=f"It seemed scary because {case.suspicion}, but the detective checked the clues and found the truth.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]  # type: ignore[assignment]
    value: Value = f["value"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is steam?",
            answer="Steam is warm water vapor that rises from hot water or other warm places.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to find the truth.",
        ),
        QAItem(
            question="What is honesty?",
            answer=f"Honesty means telling the truth and not making up a guess when you should check first. In this story, it was tied to {value.label}.",
        ),
        QAItem(
            question=f"Why can a room feel foggy in {setting.place}?",
            answer="A room can feel foggy when warm steam meets cooler air and makes tiny water drops.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.location:
            bits.append(f"location={e.location!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- place(S).
steam_case(C) :- case(C).
value(V) :- moral_value(V).

valid(S,C,V) :- place(S), case(C), moral_value(V).
valid_story(S,C,V) :- valid(S,C,V).

% The story is reasonableness-checked by requiring steam to be part of the case.
steam_mystery(C) :- case_uses_steam(C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("case_uses_steam", cid))
        for t in sorted(case.tags):
            lines.append(asp.fact("tagged", cid, t))
    for vid in VALUES:
        lines.append(asp.fact("moral_value", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Sample generation / output
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="kitchen", case="kettle_mistake", value="honesty", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="laundry", case="dryer_hiss", value="care", name="Noah", gender="boy", parent="father", trait="careful"),
    StoryParams(setting="bathroom", case="shower_fog", value="kindness", name="Ivy", gender="girl", parent="father", trait="patient"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/3.\n#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3.\n"))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.case} / {p.value}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
