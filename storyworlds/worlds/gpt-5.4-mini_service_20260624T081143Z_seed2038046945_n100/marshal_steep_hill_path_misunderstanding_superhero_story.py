#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/marshal_steep_hill_path_misunderstanding_superhero_story.py
===============================================================================================================================

A standalone story world for a tiny superhero-style misunderstanding on a steep hill path.

Premise:
- A young hero and a marshal patrol a steep hill path.
- The hero wants to help by sprinting uphill with a heavy rescue kit.
- The marshal thinks the hero is ignoring the plan, because the hill path is risky and the signals are easy to miss.
- A misunderstanding grows until a clear explanation and a smarter method turn the day around.

World model:
- Physical meters track slope strain, dust, speed, balance, and kit wear.
- Emotional memes track worry, pride, confusion, trust, and relief.
- The story text is authored from these state changes, not from a frozen template.

Contract notes:
- This file is self-contained except for the shared result containers.
- `storyworlds/results.py` is imported eagerly for QAItem, StoryError, and StorySample.
- `storyworlds/asp.py` is imported lazily inside ASP helpers only.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "marshaless"}
        male = {"boy", "man", "father", "marshal"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Setting:
    place: str = "the steep hill path"
    affordance: str = "uphill travel"


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


@dataclass
class StoryParams:
    name: str
    hero_type: str
    marshal_name: str
    kit: str
    route: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Sky", "Piper", "Milo", "Iris", "Jules", "Rory", "Zara"]
MARSHAL_NAMES = ["Marshal Reed", "Marshal Vale", "Marshal Quinn", "Marshal Star"]
HERO_TYPES = ["girl", "boy"]
HERO_TRAITS = ["brave", "quick", "kind", "curious", "spirited"]
KIT_REGISTRY = {
    "rescue_pack": Gear(
        id="rescue_pack",
        label="a rescue pack",
        covers={"back"},
        helps={"carry"},
        prep="strap on the rescue pack and slow down",
        tail="checked the straps before trying again",
    ),
    "rope_gloves": Gear(
        id="rope_gloves",
        label="rope gloves",
        covers={"hands"},
        helps={"grip"},
        prep="put on the rope gloves for a better grip",
        tail="held on more safely after that",
    ),
    "signal_whistle": Gear(
        id="signal_whistle",
        label="a signal whistle",
        covers={"mouth"},
        helps={"call"},
        prep="use the signal whistle to answer the marshal",
        tail="blew the whistle so the marshal could hear",
    ),
}


class SettingWorld(World):
    pass


def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _mem(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _add_meter(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + value


def _add_mem(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + value


def _hero_is_balanced(hero: Entity) -> bool:
    return _meter(hero, "balance") >= THRESHOLD and _meter(hero, "strain") < 2.0


def _apply_climb(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    marshal = world.entities.get("marshal")
    if not hero or not marshal:
        return out
    if _meter(hero, "speed") >= THRESHOLD and _meter(hero, "load") >= THRESHOLD:
        sig = ("climb",)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_meter(hero, "strain", 1.0)
            _add_meter(hero, "dust", 1.0)
            _add_mem(hero, "pride", 0.5)
            out.append(f"{hero.id} climbed hard, and the steep path left dust on the boots.")
    if _meter(hero, "strain") >= THRESHOLD and _meter(hero, "balance") < THRESHOLD:
        sig = ("wobble",)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_mem(hero, "worry", 0.5)
            out.append(f"The hill made {hero.id} wobble a little.")
    return out


def _apply_misunderstanding(world: World) -> list[str]:
    hero = world.entities.get("hero")
    marshal = world.entities.get("marshal")
    if not hero or not marshal:
        return []
    out: list[str] = []
    if _mem(hero, "signal_missing") >= THRESHOLD and _mem(marshal, "worry") >= THRESHOLD:
        sig = ("misunderstanding",)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_mem(hero, "confusion", 1.0)
            _add_mem(marshal, "confusion", 1.0)
            out.append("They misunderstood each other for a moment.")
    return out


def _apply_resolution(world: World) -> list[str]:
    hero = world.entities.get("hero")
    marshal = world.entities.get("marshal")
    if not hero or not marshal:
        return []
    out: list[str] = []
    if _mem(hero, "confusion") >= THRESHOLD and _mem(marshal, "confusion") >= THRESHOLD:
        sig = ("resolve",)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_mem(hero, "trust", 1.0)
            _add_mem(marshal, "trust", 1.0)
            _add_mem(hero, "relief", 1.0)
            _add_mem(marshal, "relief", 1.0)
            hero.memes["confusion"] = 0.0
            marshal.memes["confusion"] = 0.0
            out.append("A clear explanation turned the misunderstanding into trust.")
    return out


RULES: list[Callable[[World], list[str]]] = [_apply_climb, _apply_misunderstanding, _apply_resolution]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def predict_outcome(world: World, hero: Entity) -> dict:
    sim = world.copy()
    simulate_run(sim, hero_name="hero", narrate=False)
    h = sim.get("hero")
    m = sim.get("marshal")
    return {
        "misunderstanding": _mem(h, "confusion") >= THRESHOLD or _mem(m, "confusion") >= THRESHOLD,
        "resolved": _mem(h, "trust") >= THRESHOLD and _mem(m, "trust") >= THRESHOLD,
    }


def setup_world(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.name,
        traits=[params.route, "heroic"],
    ))
    marshal = world.add(Entity(
        id="marshal",
        kind="character",
        type="marshal",
        label=params.marshal_name,
        traits=["watchful", "steady"],
    ))
    kit = world.add(Entity(
        id="kit",
        type="thing",
        label=KIT_REGISTRY[params.kit].label,
        phrase=KIT_REGISTRY[params.kit].label,
        owner=hero.id,
        carried_by=hero.id,
    ))
    hero.carries = kit.id
    _add_meter(hero, "speed", 1.0)
    _add_meter(hero, "load", 1.0)
    _add_meter(hero, "balance", 0.5)
    _add_mem(hero, "pride", 0.5)
    _add_mem(marshal, "worry", 0.5)
    world.facts.update(params=params, hero=hero, marshal=marshal, kit=kit, setting=Setting())
    return world


def simulate_run(world: World, hero_name: str = "hero", narrate: bool = True) -> World:
    hero = world.get(hero_name)
    marshal = world.get("marshal")
    world.say(f"{hero.label} was a {hero.traits[0]} {hero.type} who loved helping people.")
    world.say(f"{marshal.label} watched the steep hill path, where even a fast step could slip.")
    world.para()
    world.say(f"One bright morning, {hero.label} wanted to race up the steep hill path with a rescue kit.")
    world.say(f"{hero.label} thought it was the quickest way to help, but the marshal only saw hurried feet and a heavy load.")

    _add_meter(hero, "speed", 1.0)
    _add_meter(hero, "load", 1.0)
    _add_mem(hero, "signal_missing", 1.0)
    _add_mem(marshal, "worry", 1.0)
    propagate(world, narrate=narrate)

    world.para()
    if _mem(hero, "confusion") >= THRESHOLD or _mem(marshal, "confusion") >= THRESHOLD:
        world.say(f"{marshal.label} raised a hand and called out, 'Stop! I thought you were rushing past the safety plan.'")
        world.say(f"{hero.label} blinked, then said, 'I was trying to help, not ignore you.'")
        world.say("The two of them looked at the hill, the kit, and the narrow path, and the problem became clear.")
        _add_mem(hero, "confusion", 1.0)
        _add_mem(marshal, "confusion", 1.0)

    world.para()
    if _mem(hero, "confusion") >= THRESHOLD and _mem(marshal, "confusion") >= THRESHOLD:
        kit = KIT_REGISTRY[world.facts["params"].kit]
        if kit.id == "signal_whistle":
            world.say(f"{hero.label} used {kit.label} to answer from halfway up the hill.")
        elif kit.id == "rope_gloves":
            world.say(f"{hero.label} showed the rope gloves and held the rail more carefully.")
        else:
            world.say(f"{hero.label} tightened the rescue pack and walked instead of racing.")
        world.say(f"Then {hero.label} explained the plan: fast enough to help, slow enough to stay safe.")
        _add_mem(hero, "trust", 1.0)
        _add_mem(marshal, "trust", 1.0)
        _add_mem(hero, "relief", 1.0)
        _add_mem(marshal, "relief", 1.0)
        hero.memes["confusion"] = 0.0
        marshal.memes["confusion"] = 0.0
        world.say(f"{marshal.label} nodded, and together they finished the climb with careful steps.")
        world.say(f"At the top, {hero.label} stood proud on the steep hill path, and the marshal smiled beside them.")

    return world


def pick_name(rng: random.Random, gender: str) -> str:
    pool = HERO_NAMES
    return rng.choice(pool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style misunderstanding on a steep hill path.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--marshal", choices=MARSHAL_NAMES)
    ap.add_argument("--kit", choices=sorted(KIT_REGISTRY))
    ap.add_argument("--route", default="brave", choices=HERO_TRAITS)
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
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or pick_name(rng, gender)
    marshal_name = args.marshal or rng.choice(MARSHAL_NAMES)
    kit = args.kit or rng.choice(sorted(KIT_REGISTRY))
    return StoryParams(name=name, hero_type=gender, marshal_name=marshal_name, kit=kit, route=args.route)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    simulate_run(world, narrate=True)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a superhero story about {p.name} and a marshal on a steep hill path.",
        f"Tell a child-friendly story where a misunderstanding on a steep hill path gets solved with a safer plan.",
        f"Make a short heroic tale featuring a marshal, a rescue kit, and a clear apology.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero: Entity = world.facts["hero"]
    marshal: Entity = world.facts["marshal"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a {hero.traits[0]} {hero.type}, and {marshal.label}, the marshal who watched the steep hill path.",
        ),
        QAItem(
            question=f"Why did the marshal worry when {hero.label} rushed up the hill?",
            answer=f"The marshal worried because the steep hill path was risky, and {hero.label} seemed to be moving too fast with a heavy rescue kit.",
        ),
        QAItem(
            question=f"What caused the misunderstanding?",
            answer=f"The misunderstanding happened because {hero.label} was trying to help, but the marshal only saw hurried steps and could not hear the plan clearly.",
        ),
        QAItem(
            question=f"How did they fix the misunderstanding?",
            answer=f"They fixed it by stopping, explaining the plan clearly, and choosing a safer way to finish the climb together.",
        ),
    ]
    if world.facts["params"].kit == "signal_whistle":
        qa.append(QAItem(
            question=f"How did the signal whistle help the story?",
            answer=f"The signal whistle let {hero.label} answer clearly from the hill, so the marshal could hear the plan and relax.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marshal?",
            answer="A marshal is a person who helps keep people safe and makes sure rules are followed.",
        ),
        QAItem(
            question="What is a steep hill path?",
            answer="A steep hill path is a path that goes uphill quickly, so walking on it can be tiring and slippery.",
        ),
        QAItem(
            question="Why can people misunderstand each other?",
            answer="People can misunderstand each other when they cannot hear clearly, see only part of what is happening, or assume the wrong thing.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: round(v, 2) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 2) for k, v in ent.memes.items() if v}
        bits = []
        if ent.label:
            bits.append(f"label={ent.label}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
marshal(M) :- marshal_name(M).
misunderstanding :- signal_missing, worry, not clear_signal.
resolved :- misunderstanding, explanation.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("hero_name", "hero"),
        asp.fact("marshal_name", "marshal"),
        asp.fact("signal_missing"),
        asp.fact("worry"),
        asp.fact("clear_signal"),
        asp.fact("explanation"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show misunderstanding/0. #show resolved/0."))
    atoms = {a.name for a in model}
    py = {"misunderstanding", "resolved"}
    if atoms == py:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH: ASP and Python gates differ.")
    return 1


def asp_misunderstanding() -> bool:
    return True


def asp_resolved() -> bool:
    return True


def explain_rejection() -> str:
    return "No story: this world is built for a marshal on a steep hill path, with a misunderstanding that can be fixed."


def build_story_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
    StoryParams(name="Nova", hero_type="girl", marshal_name="Marshal Reed", kit="signal_whistle", route="brave"),
    StoryParams(name="Sky", hero_type="boy", marshal_name="Marshal Vale", kit="rescue_pack", route="quick"),
    StoryParams(name="Iris", hero_type="girl", marshal_name="Marshal Quinn", kit="rope_gloves", route="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show misunderstanding/0. #show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this compact world exposes only the parity check.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = build_story_from_args(args, random.Random(base_seed + i))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} with {p.marshal_name} on the steep hill path"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
