#!/usr/bin/env python3
"""
storyworlds/worlds/mammoth_jargon_sari_lesson_learned_dialogue_adventure.py
===========================================================================

A small adventure storyworld about a child exploring a dusty market-museum with
a friendly guide, a puzzling mammoth exhibit, a sari, and too much jargon.

The seed tale imagined here:
- A child loves adventure and enters a place full of old things.
- A guide uses jargon that confuses the child.
- A sari is needed as a safe helper tool during the adventure.
- A mammoth clue turns a tricky situation into a lesson learned.
- Dialogue carries the turn from confusion to understanding.

World model:
- typed entities with physical meters and emotional memes
- state-driven plot with setup, confusion, turn, and resolution
- a reasonableness gate over compatible story combos
- an inline ASP twin that mirrors the Python gate
- three QA sets generated from state, not by parsing prose
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Robust import path resolution for nested output directories.
_HERE = os.path.abspath(os.path.dirname(__file__))
while True:
    if os.path.exists(os.path.join(_HERE, "results.py")):
        if _HERE not in sys.path:
            sys.path.insert(0, _HERE)
        break
    parent = os.path.dirname(_HERE)
    if parent == _HERE:
        break
    _HERE = parent

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    guide: str
    obstacle: str
    hero: str
    hero_type: str
    guide_type: str
    thread: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.lines = [[]]
        return w


def _resolve_result_root() -> None:
    pass


def _init_meter(e: Entity, key: str) -> None:
    e.meters.setdefault(key, 0.0)


def _init_meme(e: Entity, key: str) -> None:
    e.memes.setdefault(key, 0.0)


def _rule_confusion(world: World) -> None:
    hero = world.get("hero")
    guide = world.get("guide")
    if hero.memes.get("confused", 0) >= THRESHOLD and ("confusion",) not in world.fired:
        world.fired.add(("confusion",))
        guide.memes["patient"] = guide.memes.get("patient", 0) + 1


def _rule_lesson(world: World) -> None:
    hero = world.get("hero")
    clue = world.get("mammoth")
    if clue.meters.get("revealed", 0) >= THRESHOLD and ("lesson",) not in world.fired:
        world.fired.add(("lesson",))
        hero.memes["lesson"] = hero.memes.get("lesson", 0) + 1
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1


def propagate(world: World) -> None:
    _rule_confusion(world)
    _rule_lesson(world)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for guide in GUIDES:
            for obstacle in OBSTACLES:
                if obstacle == "tiny door" and place != "museum":
                    continue
                combos.append((place, guide, obstacle))
    return combos


PLACES = {
    "museum": "the old museum hall",
    "bazaar": "the lantern bazaar",
    "camp": "the desert camp",
}

GUIDES = {
    "ranger": "a careful ranger",
    "aunt": "an adventurous aunt",
    "teacher": "a patient teacher",
}

OBSTACLES = {
    "locked case": "a locked glass case",
    "high shelf": "a high shelf",
    "tiny door": "a tiny door behind the exhibit",
}

THREADS = {
    "map": "a faded map",
    "key": "a brass key",
    "ribbon": "a red ribbon",
}

HERO_NAMES = ["Mina", "Noor", "Lina", "Ari", "Zara", "Tari"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["curious", "brave", "restless", "patient"]


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    guide = world.add(Entity(id="guide", kind="character", type=params.guide_type, label=params.guide))
    mammoth = world.add(Entity(id="mammoth", kind="thing", type="mammoth", label="the mammoth clue"))
    sari = world.add(Entity(id="sari", kind="thing", type="sari", label="a bright sari"))
    obstacle = world.add(Entity(id="obstacle", kind="thing", type="thing", label=params.obstacle))
    thread = world.add(Entity(id="thread", kind="thing", type="thing", label=params.thread))

    for e in (hero, guide, mammoth, sari, obstacle, thread):
        _init_meter(e, "revealed")
        _init_meter(e, "blocked")
        _init_meme(e, "joy")
        _init_meme(e, "confused")
        _init_meme(e, "patient")
        _init_meme(e, "lesson")

    world.facts.update(place=params.place, guide=params.guide, obstacle=params.obstacle,
                       hero=params.hero, hero_type=params.hero_type,
                       guide_type=params.guide_type, thread=params.thread)

    world.say(f"{params.hero} loved adventure, so {params.hero} went into {params.place} with {params.guide}.")
    world.say(f"Inside, a mammoth picture stood near {params.obstacle}, and old voices liked to use jargon.")
    world.say(f'"What does that jargon mean?" {params.hero} asked.')
    world.say(f'"It means the clue is hidden by the exhibit," {params.guide} said, pointing to {params.thread}.')
    hero.memes["confused"] += 1
    guide.memes["patient"] += 1

    world.para()
    world.say(f"{params.hero} frowned. The jargon sounded big, but the place felt small.")
    world.say(f'Then {params.hero} found {sari.label.lower()} and held it like a safe flag.')
    sari.meters["revealed"] += 1
    world.say(f'"Could this help?" {params.hero} asked.')
    world.say(f'"Yes," {params.guide} said. "Use the sari to reach the thread, and we will open the case together."')

    world.para()
    world.say(f"{params.hero} tied the sari to the thread and pulled carefully.")
    obstacle.meters["blocked"] += 1
    mammoth.meters["revealed"] += 1
    propagate(world)
    world.say(f'The case opened, and the mammoth clue came into the light.')
    world.say(f'"Oh!" {params.hero} said. "The jargon was just a hard word for a simple idea."')
    world.say(f'"That is the lesson learned," {params.guide} said. "Big words should still lead to clear help."')
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f'Write a short adventure story for a young child set in {p["place"]} that includes "mammoth", "jargon", and "sari".',
        f"Tell a dialogue-driven story where {p['hero']} asks what jargon means, uses a sari, and learns something from a mammoth clue.",
        f'Write a gentle adventure with a lesson learned in which "{p["hero"]}" and a guide solve a small problem with a sari.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    hero = world.get("hero")
    guide = world.get("guide")
    mammoth = world.get("mammoth")
    sari = world.get("sari")
    return [
        QAItem(
            question=f"Why did {p['hero']} ask about the jargon in {p['place']}?",
            answer=f"{p['hero']} asked because the guide used a big word that made the clue sound confusing. The answer turned out to be simple once they looked at the sari and the thread together.",
        ),
        QAItem(
            question=f"How did the sari help {p['hero']} during the adventure?",
            answer=f"The sari gave {p['hero']} a safe way to reach the thread and open the case. It turned a tricky moment into a careful fix instead of a panic.",
        ),
        QAItem(
            question=f"What did the mammoth clue help the children learn?",
            answer=f"The mammoth clue helped them learn that jargon should still lead to clear help. It also showed that a calm helper and a useful tool can solve a problem together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is jargon?",
            answer="Jargon is special language that people in one group use. It can sound confusing if you do not know the meaning yet.",
        ),
        QAItem(
            question="What is a sari?",
            answer="A sari is a long cloth garment worn in many places. In stories, it can also be a useful piece of cloth for helping with a task.",
        ),
        QAItem(
            question="What is a mammoth?",
            answer="A mammoth was a very large animal from long ago, like an elephant with long tusks and thick fur.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
place(museum;bazaar;camp).
guide(ranger;aunt;teacher).
obstacle("locked case";"high shelf";"tiny door").
valid(P,G,O) :- place(P), guide(G), obstacle(O), not invalid(P,O).
invalid(P,"tiny door") :- P != museum.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in PLACES:
        lines.append(asp.fact("place", k))
    for k in GUIDES:
        lines.append(asp.fact("guide", k))
    for k in OBSTACLES:
        lines.append(asp.fact("obstacle", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, guide=None, obstacle=None, hero=None, hero_type=None, guide_type=None, thread=None), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    if not ok:
        print("MISMATCH")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
        return 1
    print(f"OK: {len(py)} combos, smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with mammoth, jargon, and sari.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--thread", choices=THREADS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--guide-type", choices=HERO_TYPES)
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.guide is None or c[1] == args.guide)
              and (args.obstacle is None or c[2] == args.obstacle)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, guide, obstacle = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    guide_type = args.guide_type or rng.choice(HERO_TYPES)
    thread = args.thread or rng.choice(list(THREADS.values()))
    return StoryParams(place=place, guide=guide, obstacle=obstacle, hero=hero,
                       hero_type=hero_type, guide_type=guide_type, thread=thread)


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


CURATED = [
    StoryParams(place="museum", guide="ranger", obstacle="locked case", hero="Mina", hero_type="girl", guide_type="boy", thread="a brass key"),
    StoryParams(place="bazaar", guide="aunt", obstacle="high shelf", hero="Noor", hero_type="boy", guide_type="girl", thread="a red ribbon"),
]


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
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
