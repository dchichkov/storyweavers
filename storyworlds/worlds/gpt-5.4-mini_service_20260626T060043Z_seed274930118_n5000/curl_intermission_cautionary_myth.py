#!/usr/bin/env python3
"""
storyworlds/worlds/curl_intermission_cautionary_myth.py
=======================================================

A small cautionary myth-world about a careless curl, a needed intermission,
and the lesson that a rushed hand can turn a small beauty into a bigger worry.

The seed image is simple:
---
A young keeper loves a bright curl of ribbon carried in a festival bowl.
During the first dance, the keeper refuses an intermission, keeps tugging at
the ribbon, and the curl tightens until it tangles the whole banner line.
An elder calls for a pause, the keeper finally stops, and the ribbon is
unwound before the celebration can continue.
---

This world models that tale as a tiny mythic simulation:
- physical meters: curl, strain, tangled, safe, luminous
- emotional memes: pride, worry, awe, patience, relief
- the central tension: whether the keeper honors the intermission before the
  ribbon-knot becomes a public snag
- the resolution: a pause, a careful untwist, and a brighter second half

The prose is intentionally mythic and child-facing, with a cautionary tone.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "elder"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "keeper"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hill shrine"
    sky: str = "golden"


@dataclass
class Relic:
    label: str
    phrase: str
    region: str
    spiral: str
    danger: str


@dataclass
class StoryParams:
    place: str
    relic: str
    name: str
    role: str
    elder: str
    temperament: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _decay(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.entities.get("keeper")
    ribbon = world.entities.get("relic")
    if not keeper or not ribbon:
        return out
    if keeper.meters.get("curl", 0.0) < THRESHOLD:
        return out
    if keeper.memes.get("pride", 0.0) < THRESHOLD:
        return out
    sig = ("tighten",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ribbon.meters["strain"] = ribbon.meters.get("strain", 0.0) + 1
    ribbon.meters["tangled"] = ribbon.meters.get("tangled", 0.0) + 1
    keeper.memes["worry"] = keeper.memes.get("worry", 0.0) + 1
    out.append("The curl tightened like a small storm in a string.")
    return out


def _intermission(world: World) -> list[str]:
    out: list[str] = []
    keeper = world.entities.get("keeper")
    ribbon = world.entities.get("relic")
    elder = world.entities.get("elder")
    if not keeper or not ribbon or not elder:
        return out
    if keeper.memes.get("worry", 0.0) < THRESHOLD:
        return out
    if world.fired and ("pause",) in world.fired:
        return out
    sig = ("pause",)
    world.fired.add(sig)
    keeper.memes["pride"] = max(0.0, keeper.memes.get("pride", 0.0) - 1)
    keeper.memes["patience"] = keeper.memes.get("patience", 0.0) + 1
    elder.memes["awe"] = elder.memes.get("awe", 0.0) + 1
    ribbon.meters["safe"] = ribbon.meters.get("safe", 0.0) + 1
    out.append("The elder called for an intermission, and the hall grew still.")
    return out


def _untwist(world: World) -> list[str]:
    out: list[str] = []
    ribbon = world.entities.get("relic")
    keeper = world.entities.get("keeper")
    elder = world.entities.get("elder")
    if not ribbon or not keeper or not elder:
        return out
    if ribbon.meters.get("tangled", 0.0) < THRESHOLD or keeper.memes.get("patience", 0.0) < THRESHOLD:
        return out
    sig = ("untwist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ribbon.meters["tangled"] = 0.0
    ribbon.meters["strain"] = 0.0
    ribbon.meters["safe"] = ribbon.meters.get("safe", 0.0) + 1
    keeper.memes["relief"] = keeper.memes.get("relief", 0.0) + 1
    elder.memes["relief"] = elder.memes.get("relief", 0.0) + 1
    out.append("Together they unwound the ribbon before the next drumbeat.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_decay, _intermission, _untwist):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "hill": Setting(place="the hill shrine", sky="golden"),
    "harbor": Setting(place="the harbor steps", sky="silver"),
    "orchard": Setting(place="the orchard gate", sky="pink"),
}

RELICS = {
    "ribbon": Relic(
        label="ribbon",
        phrase="a bright ceremonial ribbon",
        region="hands",
        spiral="curl",
        danger="tangled",
    ),
    "smoke": Relic(
        label="smoke",
        phrase="a curling incense thread",
        region="air",
        spiral="curl",
        danger="choked",
    ),
    "vine": Relic(
        label="vine",
        phrase="a green vine garland",
        region="arms",
        spiral="curl",
        danger="snagged",
    ),
}

TEMPERAMENTS = ["proud", "eager", "restless", "thoughtful", "careless"]
NAMES = ["Ari", "Nia", "Milo", "Lina", "Soren", "Ivo", "Mira", "Tali"]


def choose_relic_params(rng: random.Random) -> tuple[str, str]:
    return rng.choice(list(SETTINGS)), rng.choice(list(RELICS))


def is_reasonable(place: str, relic: str) -> bool:
    return True


def build_story(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id="keeper", kind="character", type=params.role, label=params.name))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label=f"the {params.elder}"))
    relic = world.add(Entity(id="relic", type=params.relic, label=RELICS[params.relic].label, phrase=RELICS[params.relic].phrase))

    hero.memes["pride"] = 1
    hero.memes["awe"] = 1
    elder.memes["wisdom"] = 1

    world.say(f"In {world.setting.place}, there was a little {params.temperament} {params.role} named {params.name}.")
    world.say(f"{hero.pronoun('subject').capitalize()} guarded {hero.pronoun('possessive')} {relic.label} like a secret star.")
    world.say(f"The people said the {relic.label} could make a festival shine if it was handled with care.")

    world.para()
    world.say(f"On the day of the dance, {params.name} kept the {relic.label} turning in a bright {RELICS[params.relic].spiral}.")
    world.say(f"But when the drums called for an intermission, {hero.pronoun('subject')} did not want to stop.")
    hero.meters["curl"] = 1.0
    hero.memes["pride"] = 2.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"The {params.elder} stepped close and warned that a hurried hand could make a small beauty become {RELICS[params.relic].danger}.")
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{params.name} finally bowed to the pause and breathed more slowly.")
    hero.memes["patience"] = hero.memes.get("patience", 0.0) + 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then the keeper untwisted the {relic.label}, and the hall shone again.")
    world.say(f"After that, the people remembered the old lesson: even a bright curl needs an intermission.")
    propagate(world, narrate=True)

    world.facts.update(hero=hero, elder=elder, relic=relic, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    relic = world.facts["relic"]
    hero = world.facts["hero"]
    return [
        f'Write a short myth for children about {p.name}, a {p.temperament} {p.role}, and a sacred {relic.label}.',
        f"Tell a cautionary tale where {hero.id} must respect an intermission before a bright curl turns troublesome.",
        f'Write a myth-like story using the words "curl" and "intermission" and ending with a wise pause.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    relic = world.facts["relic"]
    return [
        QAItem(
            question=f"Who was the story about in {world.setting.place}?",
            answer=f"It was about {p.name}, a {p.temperament} {p.role} who guarded the {relic.label}."
        ),
        QAItem(
            question="Why did the trouble begin?",
            answer=f"The trouble began because {p.name} kept turning the {relic.label} instead of stopping for the intermission."
        ),
        QAItem(
            question="How did the problem get fixed?",
            answer=f"The {p.elder} called for a pause, and then {p.name} untwisted the {relic.label} carefully so the festival could continue."
        ),
        QAItem(
            question="What lesson did the people remember?",
            answer="They remembered that a small curl can become a bigger mess if nobody pauses in time."
        ),
        QAItem(
            question=f"Who helped {p.name} most?",
            answer=f"The {elder.label} helped most by warning {hero.pronoun('object')} and calling the intermission at the right moment."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curl?",
            answer="A curl is a shape that bends around and around, like a spiral ribbon or a twist of smoke."
        ),
        QAItem(
            question="What is an intermission?",
            answer="An intermission is a pause in the middle of something, so people can rest before continuing."
        ),
        QAItem(
            question="Why do careful people pause before fixing a knot?",
            answer="They pause so they can think, use gentle hands, and avoid making the knot tighter."
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A relic is at risk when the keeper keeps curling it instead of pausing.
at_risk(R) :- relic(R), keeper_action(curl), not pause_called.

% An intermission is the reasonable cure for a tightening curl.
has_fix(R) :- at_risk(R), can_pause, relic(R).

valid_story(P, R) :- setting(P), relic(R), has_fix(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for rid, rel in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_label", rid, rel.label))
    lines.append(asp.fact("keeper_action", "curl"))
    lines.append(asp.fact("can_pause"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(p, r) for p in SETTINGS for r in RELICS if is_reasonable(p, r)}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches reasonableness ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary myth about curl and intermission.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=["keeper"])
    ap.add_argument("--elder", choices=["elder", "sage"])
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
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
    place = args.place or rng.choice(list(SETTINGS))
    relic = args.relic or rng.choice(list(RELICS))
    if not is_reasonable(place, relic):
        raise StoryError("No valid story matches the chosen place and relic.")
    name = args.name or rng.choice(NAMES)
    role = args.role or "keeper"
    elder = args.elder or rng.choice(["elder", "sage"])
    temperament = args.temperament or rng.choice(TEMPERAMENTS)
    return StoryParams(place=place, relic=relic, name=name, role=role, elder=elder, temperament=temperament)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    build_story(world, params)
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


CURATED = [
    StoryParams(place="hill", relic="ribbon", name="Ari", role="keeper", elder="elder", temperament="proud"),
    StoryParams(place="harbor", relic="smoke", name="Mira", role="keeper", elder="sage", temperament="careless"),
    StoryParams(place="orchard", relic="vine", name="Tali", role="keeper", elder="elder", temperament="restless"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for p, r in vals:
            print(f"  {p:8} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.relic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
