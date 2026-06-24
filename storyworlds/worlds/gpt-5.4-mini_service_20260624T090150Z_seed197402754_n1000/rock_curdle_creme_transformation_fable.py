#!/usr/bin/env python3
"""
storyworlds/worlds/rock_curdle_creme_transformation_fable.py
============================================================

A small fable-like storyworld about a rock, a cup of creme, and a gentle
transformation. The world stays tiny and classical: one place, one worry, one
wise turn, and one ending image that proves something changed.

Seed tale that inspired the model:
---
A rough little rock sat beside a sunny garden table. A child had set down a
sweet cup of creme there to cool, but the heat could make the creme curdle.
The rock first bragged that it never changed. Then a bird and a breeze showed
the rock how change could be kind. The rock rolled into the shade to guard the
creme. Later the rain smoothed the rock, and the rock learned that becoming
gentler was not the same as being broken.

World model:
---
- The rock has physical roughness and emotional pride.
- The creme has temperature and freshness; if left in heat too long, it curdles.
- Shade and water are the two meaningful forces in the setting.
- The story's tension is whether the creme curdles before the rock can help.
- The resolution is a transformation: the rock becomes smoother, and the
  creme stays sweet.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld script
- shared result containers imported eagerly
- ASP helper imported lazily
- build_parser, resolve_params, generate, emit, main
- story, QA, trace, JSON, ASP, verify, show-asp modes
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    heat: float
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    weather: str
    name: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", heat=1.0, weather="warm", affords={"shade", "rain"}),
    "courtyard": Setting(place="the courtyard", heat=1.2, weather="hot", affords={"shade", "rain"}),
    "orchard": Setting(place="the orchard", heat=0.9, weather="mild", affords={"shade", "rain"}),
}

NAMES = ["Milo", "Nina", "Ivy", "Otto", "Lena", "Pip"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, weather, "creme") for place in SETTINGS for weather in {"warm", "hot", "mild"}]


def explain_rejection() -> str:
    return "(No story: this fable needs a place where shade and rain can both matter.)"


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_curdle(world: World) -> list[str]:
    out: list[str] = []
    creme = world.get("creme")
    if world.setting.heat < 1.1:
        return out
    if creme.meters.get("heat", 0.0) < THRESHOLD:
        return out
    if creme.meters.get("curdled", 0.0) >= THRESHOLD:
        return out
    sig = ("curdle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creme.meters["curdled"] = 1.0
    creme.memes["sad"] = creme.memes.get("sad", 0.0) + 1.0
    out.append("The creme began to curdle in the heat.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    rock = world.get("rock")
    if rock.meters.get("rain", 0.0) < THRESHOLD:
        return out
    if rock.meters.get("smooth", 0.0) >= THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rock.meters["rough"] = max(0.0, rock.meters.get("rough", 1.0) - 1.0)
    rock.meters["smooth"] = 1.0
    rock.memes["pride"] = max(0.0, rock.memes.get("pride", 1.0) - 1.0)
    rock.memes["wisdom"] = rock.memes.get("wisdom", 0.0) + 1.0
    out.append("The rock was transformed by rain into a smooth pebble.")
    return out


CAUSAL_RULES = [Rule("curdle", _r_curdle), Rule("transform", _r_transform)]


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


def predict_curdle(world: World) -> bool:
    sim = world.copy()
    sim.get("creme").meters["heat"] = sim.setting.heat
    propagate(sim, narrate=False)
    return bool(sim.get("creme").meters.get("curdled", 0.0) >= THRESHOLD)


def tell(setting: Setting, hero_name: str) -> World:
    world = World(setting)
    rock = world.add(Entity(
        id="rock",
        kind="thing",
        type="rock",
        label="rock",
        phrase="a rough little rock",
        place=setting.place,
        meters={"rough": 1.0, "smooth": 0.0, "rain": 0.0},
        memes={"pride": 1.0, "curiosity": 0.0, "wisdom": 0.0},
    ))
    creme = world.add(Entity(
        id="creme",
        kind="thing",
        type="creme",
        label="creme",
        phrase="a small cup of creme",
        caretaker=hero_name,
        place=setting.place,
        meters={"heat": setting.heat, "fresh": 1.0, "curdled": 0.0},
        memes={"delight": 1.0, "sad": 0.0},
    ))
    bird = world.add(Entity(
        id="bird",
        kind="thing",
        type="bird",
        label="bird",
        phrase="a bright little bird",
        place=setting.place,
        meters={},
        memes={"gentle": 1.0},
    ))
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type="child",
        label=hero_name,
        phrase=f"a child named {hero_name}",
        place=setting.place,
        meters={},
        memes={"hope": 1.0},
    ))

    world.say(
        f"At {setting.place}, a rough little rock sat beside a small cup of creme while "
        f"{hero_name} looked on."
    )
    world.say(
        f"The rock liked to boast that it would never change, but the bird said, "
        f"\"Even a rock can learn a kinder shape.\""
    )

    world.para()
    world.say(
        f"The day grew warmer, and {hero_name} worried that the creme might curdle if "
        f"nothing shielded it from the heat."
    )
    if predict_curdle(world):
        world.say("The rock noticed the warning and rolled closer to the shade.")
        creme.meters["heat"] = 0.4
        rock.memes["curiosity"] += 1.0
    else:
        world.say("The air stayed gentle, so the creme did not have to fight the heat.")
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then rain came softly over {setting.place}, and the rock let itself be washed."
    )
    rock.meters["rain"] = 1.0
    rock.meters["heat"] = 0.0
    creme.meters["fresh"] = 1.0
    propagate(world, narrate=True)

    world.say(
        f"In the end, the creme stayed sweet in the shade, and the rock was no longer "
        f"rough in the same way."
    )

    world.facts.update(
        setting=setting,
        child=child,
        rock=rock,
        creme=creme,
        bird=bird,
        curdled=bool(creme.meters.get("curdled", 0.0) >= THRESHOLD),
        transformed=bool(rock.meters.get("smooth", 0.0) >= THRESHOLD),
    )
    return world


SETTINGS_ORDER = ["garden", "courtyard", "orchard"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a young child about a rock, a curdle, and a creme.',
        f"Tell a gentle story where a rock in {f['setting'].place} learns that helping a creme "
        f"stay sweet can be wiser than bragging about being unchanged.",
        f"Write a simple fable that uses the words rock, curdle, and creme, and ends with a transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting = f["setting"].place
    child = f["child"].id
    return [
        QAItem(
            question=f"Where did the rock and the creme sit at the start of the fable?",
            answer=f"They sat together at {setting}, where {child} could watch them.",
        ),
        QAItem(
            question="Why did the child worry about the creme?",
            answer="The child worried because the day was warm, and heat can make creme curdle.",
        ),
        QAItem(
            question="What did the rock do when it understood the risk?",
            answer="The rock rolled into the shade to guard the creme from the hot part of the day.",
        ),
        QAItem(
            question="What changed after the rain came?",
            answer="The rock became smoother, so the story ended with a real transformation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rock?",
            answer="A rock is a hard piece of stone. Rocks can be rough at first and smoother after wind or rain works on them for a long time.",
        ),
        QAItem(
            question="What does it mean for creme to curdle?",
            answer="When creme curdles, it changes into clumps or little lumps because heat or sourness has changed its texture.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state or shape into another. In stories, it can mean someone learns, softens, grows, or becomes different in a clear way.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "garden"),
        asp.fact("setting", "courtyard"),
        asp.fact("setting", "orchard"),
        asp.fact("has_weather", "warm"),
        asp.fact("has_weather", "hot"),
        asp.fact("has_weather", "mild"),
        asp.fact("thing", "rock"),
        asp.fact("thing", "creme"),
        asp.fact("thing", "bird"),
        asp.fact("character", "child"),
        asp.fact("can_curdle", "creme"),
        asp.fact("can_transform", "rock"),
    ]
    for name, s in SETTINGS.items():
        lines.append(asp.fact("place_has", name, s.weather))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, W) :- setting(P), has_weather(W), place_has(P, W).
curdle_possible(C) :- can_curdle(C).
transforms(R) :- can_transform(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, w) for p, w, _ in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable about rock, curdle, creme, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--weather", choices=["warm", "hot", "mild"])
    ap.add_argument("--name", choices=NAMES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.weather:
        combos = [c for c in combos if c[1] == args.weather]
    if not combos:
        raise StoryError(explain_rejection())
    place, weather, _ = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, weather=weather, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, weather) combos:\n")
        for place, weather in combos:
            print(f"  {place:10} {weather}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, weather=SETTINGS[place].weather, name=NAMES[0])
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
