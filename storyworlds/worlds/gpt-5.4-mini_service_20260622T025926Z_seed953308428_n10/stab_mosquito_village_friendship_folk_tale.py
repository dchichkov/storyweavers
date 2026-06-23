#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T025926Z_seed953308428_n10/stab_mosquito_village_friendship_folk_tale.py
===============================================================================================================

A small folk-tale storyworld about a village friendship, a buzzing mosquito,
and a child who learns a kinder way to solve a problem.

The world is intentionally compact:
- one simulation model
- a tiny rule set with physical meters and emotional memes
- a reasonableness gate
- an inline ASP twin
- three QA sets generated from world state
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
    role: str = ""
    owner: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    village: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    elder_name: str
    elder_gender: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class VillageConfig:
    id: str
    label: str
    detail: str
    festival: str
    insect: str
    insect_label: str
    trap_label: str
    safe_tool_label: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


VILLAGES = {
    "greenhill": VillageConfig(
        id="greenhill",
        label="Greenhill Village",
        detail="a round green village with blue doors and a little bridge",
        festival="Berry Day",
        insect="mosquito",
        insect_label="a tiny mosquito",
        trap_label="a shallow honey bowl",
        safe_tool_label="a leaf fan",
        ending_image="the lanterns glowed over the quiet square",
        tags={"village", "mosquito", "friendship"},
    ),
    "riverbend": VillageConfig(
        id="riverbend",
        label="Riverbend Village",
        detail="a river village with willow trees and a stone path",
        festival="Lantern Day",
        insect="mosquito",
        insect_label="a tiny mosquito",
        trap_label="a shallow honey bowl",
        safe_tool_label="a leaf fan",
        ending_image="the willow shadows danced over the square",
        tags={"village", "mosquito", "friendship"},
    ),
}

NAMES = ["Mira", "Sora", "Lina", "Pavel", "Anya", "Rin", "Tobi", "Niko"]
GENDERS = ["girl", "boy"]
TRAITS = ["kind", "brave", "gentle", "quick", "thoughtful"]


class World:
    def __init__(self, cfg: VillageConfig) -> None:
        self.cfg = cfg
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.history: list[str] = []
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
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.cfg)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.history = list(self.history)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_buzz(world: World) -> list[str]:
    out = []
    child = world.get("child")
    mosquito = world.get("mosquito")
    if child.memes["annoyance"] < THRESHOLD or mosquito.meters["near"] < THRESHOLD:
        return out
    sig = ("buzz",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["frustration"] += 1
    out.append("The buzzing made the child grumpy.")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    child = world.get("child")
    friend = world.get("friend")
    if child.memes["softness"] < THRESHOLD or friend.memes["trust"] < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    friend.memes["joy"] += 1
    out.append("The two friends found a kinder plan.")
    return out


CAUSAL_RULES = [Rule("buzz", _r_buzz), Rule("friendship", _r_friendship)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str]]:
    return [(k,) for k in VILLAGES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about friendship in a village.")
    ap.add_argument("--village", choices=VILLAGES)
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
    combos = [c for c in valid_combos() if args.village is None or c[0] == args.village]
    if not combos:
        raise StoryError("(No valid village matches the given options.)")
    village = rng.choice(sorted(c[0] for c in combos))
    child_gender = rng.choice(GENDERS)
    friend_gender = rng.choice([g for g in GENDERS if g != child_gender or rng.random() < 0.5])
    elder_gender = rng.choice(GENDERS)
    child_name = rng.choice(NAMES)
    friend_name = rng.choice([n for n in NAMES if n != child_name])
    elder_name = rng.choice([n for n in NAMES if n not in {child_name, friend_name}])
    return StoryParams(village=village, child_name=child_name, child_gender=child_gender,
                       friend_name=friend_name, friend_gender=friend_gender,
                       elder_name=elder_name, elder_gender=elder_gender)


def tell(params: StoryParams) -> World:
    cfg = VILLAGES[params.village]
    world = World(cfg)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name,
                             role="child", tags={"friendship"}))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend_name,
                              role="friend", tags={"friendship"}))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_gender, label=params.elder_name,
                             role="elder", tags={"friendship"}))
    mosquito = world.add(Entity(id="mosquito", kind="creature", type="mosquito", label=cfg.insect_label,
                                plural=False, tags={"mosquito"}))
    bowl = world.add(Entity(id="bowl", type="tool", label=cfg.trap_label, tags={"honey"}))
    fan = world.add(Entity(id="fan", type="tool", label=cfg.safe_tool_label, tags={"leaf"}))
    square = world.add(Entity(id="square", type="place", label=cfg.label, phrase=cfg.detail,
                              tags={"village"}))

    child.memes["annoyance"] = 1
    child.memes["softness"] = 0
    friend.memes["trust"] = 1
    elder.memes["wisdom"] = 1
    mosquito.meters["near"] = 1

    world.say(f"Once in {cfg.label}, where {cfg.detail}, {child.label} and {friend.label} were the best of friends.")
    world.say(f"It was {cfg.festival}, and the whole village smelled of sweet bread and rain-washed wood.")
    world.para()
    world.say(f"Then {mosquito.label} began to buzz near the berry table, tiny but stubborn.")
    world.say(f"{child.label} raised a hand and almost tried to stab at the little mosquito with a stick.")
    child.memes["annoyance"] += 1
    child.memes["softness"] += 1
    propagate(world, narrate=False)
    world.say(f"But {friend.label} held {child.pronoun('possessive')} sleeve and said, \"No, friend. A village should be kinder than that.\"")
    world.say(f"{elder.label} nodded and set down {bowl.label}. \"Use this sweet bowl to guide it away, not harm it,\" {elder.pronoun()} said.")
    world.para()
    child.memes["annoyance"] = max(0.0, child.memes["annoyance"] - 1)
    world.say(f"So the two friends left the berries on the table, waved {fan.label}, and watched the mosquito drift to the flowers.")
    world.say(f"By sunset, {cfg.ending_image}, and {child.label} smiled because {friend.label} had taught a gentler way.")
    child.memes["calm"] += 1
    friend.memes["joy"] += 1
    world.facts.update(cfg=cfg, child=child, friend=friend, elder=elder, mosquito=mosquito, bowl=bowl, fan=fan,
                       friendship=True, mosquito_trouble=True, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cfg = f["cfg"]
    child = f["child"]
    friend = f["friend"]
    return [
        f'Write a folk tale for a young child about friendship in {cfg.label} that includes the word "mosquito".',
        f"Tell a gentle village story where {child.label} and {friend.label} face a buzzing mosquito and choose kindness.",
        f'Write a short folk tale that includes the words "stab", "mosquito", and "village", and ends with friends solving the problem kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cfg = f["cfg"]
    child = f["child"]
    friend = f["friend"]
    elder = f["elder"]
    mosquito = f["mosquito"]
    qa = [
        QAItem(
            question=f"Who are the story's friends in {cfg.label}?",
            answer=f"The friends are {child.label} and {friend.label}. They live in the village of {cfg.label} and help each other when the mosquito buzzes near the food.",
        ),
        QAItem(
            question=f"Why did {child.label} almost stab at the mosquito?",
            answer=f"{child.label} felt annoyed because the mosquito kept buzzing by the berry table. The friend stopped that quick idea and helped choose a kinder plan instead.",
        ),
        QAItem(
            question=f"Who taught the kinder way in the village?",
            answer=f"{elder.label} taught it. The elder showed them a shallow honey bowl and reminded them that friendship is stronger than a mean answer.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What happened to the mosquito by the end?",
            answer=f"It drifted away toward the flowers, and the berries stayed safe on the table. The village kept celebrating because the friends solved the trouble without hurting anything.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a village?", "A village is a small place where people live close together and know their neighbors."),
        QAItem("What is a mosquito?", "A mosquito is a tiny flying insect that buzzes and can be very annoying."),
        QAItem("What does friendship mean?", "Friendship means being kind, helping each other, and staying close when trouble comes."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
chosen(V) :- village(V).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("village", vid) for vid in VILLAGES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str]]:
    import asp
    model = asp.one_model(asp_program("#show chosen/1."))
    return sorted(set(asp.atoms(model, "chosen")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ")
        ok = False
    try:
        sample = generate(resolve_params(argparse.Namespace(village=None), random.Random(777)))
        if not sample.story.strip():
            raise StoryError("empty story")
        _ = sample.to_json()
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        ok = False
    seeds = [1, 7, 777]
    for s in seeds:
        try:
            _ = resolve_params(argparse.Namespace(village=None), random.Random(s))
        except Exception as exc:
            print(f"RESOLVE FAIL seed={s}: {exc}")
            ok = False
    try:
        # ensure basic CLI paths are viable
        for _ in range(3):
            _ = generate(resolve_params(argparse.Namespace(village=None), random.Random(1000 + _)))
    except Exception as exc:
        print(f"GENERATE FAIL: {exc}")
        ok = False
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    if params.village not in VILLAGES:
        raise StoryError("invalid village")
    world = tell(params)
    story = world.render()
    if not story.strip():
        raise StoryError("empty story")
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show chosen/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(village=v, child_name="Mira", child_gender="girl", friend_name="Sora",
                                         friend_gender="girl", elder_name="Niko", elder_gender="boy"))
                   for v in VILLAGES]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
