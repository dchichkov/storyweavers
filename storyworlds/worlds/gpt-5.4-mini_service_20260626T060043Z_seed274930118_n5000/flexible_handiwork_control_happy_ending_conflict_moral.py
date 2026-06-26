#!/usr/bin/env python3
"""
A small fable-like story world about flexible handiwork, control, conflict,
and a happy ending with a moral value.
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


@dataclass
class StoryParams:
    setting: str = "the willow workshop"
    craft: str = "basket"
    material: str = "willow reeds"
    hero: str = "Mina"
    hero_kind: str = "rabbit"
    elder: str = "Tilda"
    elder_kind: str = "badger"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["skill", "frustration", "joy", "care", "pride", "control", "flexibility", "moral"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self) -> str:
        return "she" if self.kind in {"rabbit", "badger", "hare", "fox", "mouse", "cat"} else "they"

    def possessive(self) -> str:
        return "her" if self.pronoun() == "she" else "their"


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.params)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


def _r_splinter(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    if hero.memes["control"] < THRESHOLD:
        return out
    if hero.memes["flexibility"] >= THRESHOLD:
        return out
    if "splinter" in world.fired:
        return out
    if hero.meters["skill"] < THRESHOLD:
        world.fired.add("splinter")
        hero.meters["frustration"] += 1
        out.append("The reeds bent the wrong way and the craft began to look rough.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    if hero.meters["frustration"] < THRESHOLD or elder.memes["care"] < THRESHOLD:
        return out
    if "help" in world.fired:
        return out
    world.fired.add("help")
    hero.memes["flexibility"] += 1
    elder.memes["pride"] += 1
    out.append("The elder showed a gentler weave, and the rough start became useful.")
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    if hero.memes["flexibility"] < THRESHOLD:
        return out
    if "finish" in world.fired:
        return out
    world.fired.add("finish")
    hero.meters["skill"] += 1
    hero.memes["joy"] += 1
    hero.memes["moral"] += 1
    out.append("Soon the craft stood strong and light, because it was made with a flexible hand.")
    return out


CAUSAL_RULES = [_r_splinter, _r_help, _r_finish]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def intro(world: World) -> None:
    p = world.params
    world.say(
        f"In {p.setting}, {p.hero}, a young {p.hero_kind}, loved handiwork more than any game."
    )
    world.say(
        f"{p.hero} wanted to make a {p.craft} from {p.material}, and {p.hero} believed control would make it perfect."
    )


def conflict(world: World) -> None:
    p = world.params
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    world.para()
    world.say(
        f"At first, {p.hero} pulled the reeds too tightly and would not let anyone help."
    )
    hero.memes["control"] += 1
    hero.meters["skill"] += 0.5
    hero.memes["frustration"] += 0.5
    elder.memes["care"] += 1
    world.say(
        f"{p.elder}, the older {p.elder_kind}, warned that a craft grows better when hands can bend a little."
    )
    world.say(
        f"{p.hero} frowned and tried to keep full control, but the reeds started to slip and twist."
    )
    propagate(world, narrate=True)


def resolution(world: World) -> None:
    p = world.params
    hero = world.entities["hero"]
    elder = world.entities["elder"]
    world.para()
    if hero.meters["frustration"] >= THRESHOLD:
        world.say(
            f"Then {p.hero} listened, loosened the grip, and let {p.elder} show a softer way."
        )
    else:
        world.say(
            f"Then {p.hero} noticed the wiser path and loosened the grip before the work failed."
        )
    hero.memes["control"] = max(0.0, hero.memes["control"] - 0.5)
    hero.memes["flexibility"] += 1
    elder.memes["care"] += 0.5
    propagate(world, narrate=True)
    world.say(
        f"In the end, the {p.craft} held together well, and {p.hero} smiled at the tidy handiwork."
    )
    world.say(
        f"The moral was simple: control can start the work, but flexibility helps the work succeed."
    )


def tell(params: StoryParams) -> World:
    world = World(params)
    world.add(Entity(id="hero", kind=params.hero_kind, label=params.hero))
    world.add(Entity(id="elder", kind=params.elder_kind, label=params.elder))
    intro(world)
    conflict(world)
    resolution(world)
    world.facts.update(
        hero=world.entities["hero"],
        elder=world.entities["elder"],
        craft=params.craft,
        material=params.material,
        setting=params.setting,
        conflict=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short fable about {p.hero}, {p.material}, and learning flexibility without losing control.",
        f"Tell a child-friendly story in which {p.hero} makes a {p.craft} by hand and discovers a moral value.",
        "Write a fable with conflict, a happy ending, and a clear lesson about working gently with others.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"What did {p.hero} want to make in {p.setting}?",
            answer=f"{p.hero} wanted to make a {p.craft} from {p.material}.",
        ),
        QAItem(
            question=f"Why was there conflict in the story?",
            answer=f"There was conflict because {p.hero} tried to keep too much control and would not bend the work kindly at first.",
        ),
        QAItem(
            question="What changed the ending into a happy one?",
            answer="The young maker listened, became more flexible, and let the older helper show a gentler way.",
        ),
        QAItem(
            question="What was the moral of the story?",
            answer="The moral was that control can begin a task, but flexibility helps the handiwork succeed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is handiwork?",
            answer="Handiwork is something made by hand, often with care and skill.",
        ),
        QAItem(
            question="What does flexible mean?",
            answer="Flexible means able to bend, change, or adapt without breaking.",
        ),
        QAItem(
            question="What does control mean in a craft?",
            answer="Control means guiding something closely so it goes the way you want.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:5} ({e.kind:6}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
moral_ok :- flexible, handiwork, conflict, happy_ending.
#show moral_ok/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("flexible"),
        asp.fact("handiwork"),
        asp.fact("control"),
        asp.fact("conflict"),
        asp.fact("happy_ending"),
        asp.fact("moral_value"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show moral_ok/0."))
    ok = any(sym.name == "moral_ok" for sym in model)
    if ok:
        print("OK: ASP twin agrees that the story has a moral resolution.")
        return 0
    print("MISMATCH: ASP twin did not derive moral_ok.")
    return 1


@dataclass
class Registry:
    heroes: list[tuple[str, str]] = field(default_factory=lambda: [("Mina", "rabbit"), ("Pip", "mouse"), ("Lena", "hare")])
    elders: list[tuple[str, str]] = field(default_factory=lambda: [("Tilda", "badger"), ("Oren", "owl"), ("Brum", "beaver")])
    settings: list[str] = field(default_factory=lambda: ["the willow workshop", "the riverside shed", "the garden bench"])


REGISTRY = Registry()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style story world about flexible handiwork and control.")
    ap.add_argument("--setting", choices=REGISTRY.settings)
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=["rabbit", "mouse", "hare"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-kind", choices=["badger", "owl", "beaver"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(REGISTRY.settings)
    hero, hero_kind = (args.hero, args.hero_kind) if args.hero and args.hero_kind else rng.choice(REGISTRY.heroes)
    elder, elder_kind = (args.elder, args.elder_kind) if args.elder and args.elder_kind else rng.choice(REGISTRY.elders)
    if hero == elder:
        raise StoryError("hero and elder must be different characters")
    return StoryParams(setting=setting, hero=hero, hero_kind=hero_kind, elder=elder, elder_kind=elder_kind)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show moral_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show moral_ok/0."))
        print(f"moral_ok: {any(sym.name == 'moral_ok' for sym in model)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [StoryParams(setting=s, hero=h, hero_kind=hk, elder=e, elder_kind=ek)
                  for s in REGISTRY.settings
                  for (h, hk) in REGISTRY.heroes
                  for (e, ek) in REGISTRY.elders
                  if h != e]
        samples = [generate(p) for p in combos[: max(1, args.n)]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
