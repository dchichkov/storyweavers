#!/usr/bin/env python3
"""
A small storyworld about a child, a strange sound, and a harmless mystery.

Seed premise:
- A child hears a hissing sound around a bottle of disinfectant.
- The sound seems spooky at first and almost feels like it could terror-ize the room.
- The mystery is solved in a calm slice-of-life way: someone is cleaning, not scaring anyone.

The simulation tracks:
- physical state: where sound comes from, whether the bottle is open, whether a spill exists
- emotional state: curiosity, suspense, worry, relief, safety
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
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the apartment kitchen"
    indoor: bool = True


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    parent_name: str
    parent_type: str
    source: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting("the apartment kitchen", True),
    "bathroom": Setting("the bathroom", True),
    "hallway": Setting("the hallway", True),
}

SOURCES = {
    "spray": {
        "label": "a bottle of disinfectant spray",
        "sound": "hissss",
        "action": "spraying disinfectant",
        "mystery": "the bottle was making that hiss all by itself",
        "solve": "their parent was cleaning the counter",
        "risk": "the spray could make the floor slippery",
    },
    "wipes": {
        "label": "a pack of disinfectant wipes",
        "sound": "fwap-fwap",
        "action": "wiping the table with disinfectant wipes",
        "mystery": "the soft flapping sounds kept coming from the table",
        "solve": "their parent was cleaning up juice",
        "risk": "the wipes were just for cleaning, not for chasing anyone",
    },
}

GIRL_NAMES = ["Mia", "Luna", "Nina", "Sofia", "Ava", "Iris"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Milo", "Finn", "Ben"]


# ---------------------------------------------------------------------------
# World building and simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("unknown setting")
    if params.source not in SOURCES:
        raise StoryError("unknown source")

    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(
        id="hero", kind="character", type=params.hero_type, label=params.hero_name,
        meters={"curiosity": 1.0},
        memes={"curiosity": 1.0, "suspense": 0.0, "worry": 0.0, "relief": 0.0, "safety": 1.0},
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=params.parent_type, label=params.parent_name,
        meters={"calm": 1.0},
        memes={"calm": 1.0},
    ))
    source = SOURCES[params.source]
    obj = world.add(Entity(
        id="source", kind="thing", type=params.source, label=source["label"],
        meters={"open": 1.0},
    ))
    world.facts.update(hero=hero, parent=parent, source=obj, source_cfg=source)
    return world


def predict_sound(world: World) -> dict:
    src = world.facts["source_cfg"]
    return {
        "sound": src["sound"],
        "mystery": src["mystery"],
        "solve": src["solve"],
        "risk": src["risk"],
    }


def narrate_setup(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    src = world.facts["source_cfg"]
    world.say(f"{hero.label} was in {world.setting.place}, close enough to hear a tiny sound.")
    world.say(f"{parent.label} had left {src['label']} nearby after a quick cleaning job.")


def narrate_suspense(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    src = predict_sound(world)
    hero.memes["suspense"] += 1.0
    hero.memes["worry"] += 0.5
    world.say(
        f"Then came a soft {src['sound']}. It was such a small sound that it felt even spookier."
    )
    world.say(
        f"{hero.label} paused. The little hiss seemed like it might terror-ize the quiet room."
    )
    world.say(
        f"{hero.label} looked at {parent.label} and asked what was making the noise."
    )


def resolve_mystery(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    src = world.facts["source_cfg"]
    hero.memes["suspense"] = 0.0
    hero.memes["relief"] += 1.0
    hero.memes["safety"] += 1.0
    world.say(f"{parent.label} smiled and showed {hero.label} the answer.")
    world.say(f"It was only {src['solve']}. The disinfectant was there to help make things clean.")
    world.say(f"The sound was not a monster at all. It was just a normal sound from cleaning.")


def close_story(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    src = world.facts["source_cfg"]
    world.say(
        f"After that, {hero.label} listened more carefully and felt brave about ordinary noises."
    )
    world.say(
        f"{hero.label} even helped carry a cloth while {parent.label} finished {src['action']}."
    )
    world.say(
        f"The room stayed neat, the mystery was solved, and the day went on in a calm slice-of-life way."
    )


def generate_world(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world)
    world.para()
    narrate_suspense(world)
    world.para()
    resolve_mystery(world)
    close_story(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    parent = f["parent"].label
    src = f["source_cfg"]["label"]
    return [
        f'Write a short slice-of-life story for a child who hears a spooky sound near {src}.',
        f"Tell a gentle mystery story where {hero} thinks a sound might terror-ize the room, but {parent} explains it.",
        f"Write a calm story about disinfectant, suspense, and solving a tiny household mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    src = world.facts["source_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.label} feel suspense when the room got quiet?",
            answer=f"{hero.label} heard a small {src['sound']} from {src['label']}, and the strange little sound made the room feel suspenseful.",
        ),
        QAItem(
            question=f"What made {hero.label} think the sound might terror-ize the room?",
            answer=f"{hero.label} did not know where the noise came from, so the tiny {src['sound']} felt spooky for a moment.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{parent.label} explained that the noise came from {src['solve']}, so the disinfectant was just part of cleaning and not anything scary.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.label} felt relief and safety instead of worry, and the ordinary noise made sense.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is disinfectant for?",
            answer="Disinfectant is used to clean surfaces and help remove germs.",
        ),
        QAItem(
            question="Why can a small sound feel scary for a moment?",
            answer="A small sound can feel scary when you do not know what made it, because not knowing leaves room for suspense.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next or what something strange might mean.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(kitchen). setting(bathroom). setting(hallway).
source(spray). source(wipes).

sound(spray,hissss).
sound(wipes,"fwap-fwap").

mystery(spray,"the bottle was making that hiss all by itself").
mystery(wipes,"the soft flapping sounds kept coming from the table").

solve(spray,"their parent was cleaning the counter").
solve(wipes,"their parent was cleaning up juice").

risk(spray,"the spray could make the floor slippery").
risk(wipes,"the wipes were just for cleaning, not for chasing anyone").

reason_ok(S) :- source(S).
#show reason_ok/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, cfg in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("sound", sid, cfg["sound"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:  # pragma: no cover
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show reason_ok/1."))
    got = sorted(set(asp.atoms(model, "reason_ok")))
    want = sorted((k,) for k in SOURCES)
    if got == want:
        print("OK: ASP parity matches Python registries.")
        return 0
    print("MISMATCH:")
    print(" asp:", got)
    print(" py :", want)
    return 1


def asp_reasonable() -> list[tuple[str]]:
    import asp
    model = asp.one_model(asp_program("#show reason_ok/1."))
    return sorted(set(asp.atoms(model, "reason_ok")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life mystery storyworld with disinfectant, suspense, and a harmless sound.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    source = args.source or rng.choice(list(SOURCES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    hero_type = gender
    parent_type = parent
    return StoryParams(setting=setting, hero_name=name, hero_type=hero_type, parent_name=parent.capitalize(), parent_type=parent_type, source=source)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show reason_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_reasonable())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for source in SOURCES:
                params = StoryParams(
                    setting=setting,
                    hero_name="Mia",
                    hero_type="girl",
                    parent_name="Mom",
                    parent_type="mother",
                    source=source,
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
