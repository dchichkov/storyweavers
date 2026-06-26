#!/usr/bin/env python3
"""
well_misunderstanding_friendship_moral_value_fable.py
======================================================

A small fable-style story world about a well, a misunderstanding, friendship,
and a moral value.

Seed tale shape:
- Two friends share a village well.
- One misunderstands the other's actions and feels hurt.
- A small act of kindness reveals the truth.
- Friendship is restored and a moral is stated through the ending.

The simulation keeps track of physical state in meters and emotional state in
memes. The prose is driven by those state changes rather than a fixed template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    village: str
    hero_a: str
    hero_b: str
    hero_a_type: str
    hero_b_type: str
    moral: str
    seed: Optional[int] = None


VILLAGES = {
    "sunny_hamlet": "the sunny hamlet",
    "little_valley": "the little valley",
    "quiet_lanes": "the quiet lanes",
}

NAMES = {
    "girl": ["Mina", "Lina", "Tara", "Nora", "Ivy"],
    "boy": ["Pip", "Tobin", "Eli", "Jory", "Nate"],
}

MORALS = [
    "kindness",
    "patience",
    "honesty",
    "sharing",
    "forgiveness",
]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    a = world.get("friend_a")
    b = world.get("friend_b")
    if a.memes.get("hurt", 0) >= THRESHOLD and b.meters.get("well_bucket_returned", 0) >= THRESHOLD:
        sig = ("misunderstanding",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        a.memes["misunderstanding"] = 1
        out.append(f"{a.label} thought {b.label} had been unkind.")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    a = world.get("friend_a")
    b = world.get("friend_b")
    if a.memes.get("understood", 0) >= THRESHOLD and b.memes.get("understood", 0) >= THRESHOLD:
        sig = ("friendship_restored",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        a.memes["friendship"] = a.memes.get("friendship", 0) + 1
        b.memes["friendship"] = b.memes.get("friendship", 0) + 1
        a.memes["hurt"] = 0
        b.memes["hurt"] = 0
        out.append("Their friendship grew warm again.")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("friendship", _r_friendship)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def tell(village_key: str, hero_a_type: str, hero_b_type: str, hero_a_name: str, hero_b_name: str, moral: str) -> World:
    world = World()
    village = VILLAGES[village_key]
    well = world.add(Entity(id="well", kind="thing", type="well", label="the well"))
    well.meters["water"] = 1
    a = world.add(Entity(id="friend_a", kind="character", type=hero_a_type, label=hero_a_name, traits=["young", "kind"]))
    b = world.add(Entity(id="friend_b", kind="character", type=hero_b_type, label=hero_b_name, traits=["young", "helpful"]))
    world.facts.update(village=village, moral=moral, well=well, hero_a=a, hero_b=b)

    world.say(f"In {village}, {a.label} and {b.label} were friends who met beside the village well.")
    world.say(f"They liked to share water, stories, and small chores, because friendship made the day feel lighter.")

    world.para()
    world.say(f"One hot morning, {a.label} found the bucket empty and saw {b.label} near the well.")
    a.memes["hurt"] = 1
    world.say(f"{a.label} frowned and thought {b.label} had taken the last water for {b.label.lower()}self.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"But {b.label} had only carried the bucket to a child who was thirsty on the far path.")
    b.meters["well_bucket_returned"] = 1
    world.say(f"{b.label} came back with the bucket and set it down, then explained the kindness that had been done.")
    a.memes["understood"] = 1
    b.memes["understood"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{a.label} felt ashamed for the misunderstanding, and then grateful for the truth.")
    world.say(f"{a.label} offered the next turn at the well, and {b.label} smiled.")
    world.say(f"From then on, they remembered the moral value of {moral}: do not judge a friend before you know the whole story.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about friends beside a well that ends by teaching {f['moral']}.",
        f"Tell a child-friendly story in which {f['hero_a'].label} and {f['hero_b'].label} have a misunderstanding at the well and then become friends again.",
        "Write a gentle moral tale about a village well, a mistaken feeling, and a kind explanation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["hero_a"]
    b = world.facts["hero_b"]
    village = world.facts["village"]
    moral = world.facts["moral"]
    return [
        QAItem(
            question=f"Where did {a.label} and {b.label} meet in the story?",
            answer=f"They met beside the village well in {village}.",
        ),
        QAItem(
            question=f"What did {a.label} misunderstand about {b.label}?",
            answer=f"{a.label} thought {b.label} had taken the last water for selfish reasons, but that was not true.",
        ),
        QAItem(
            question=f"How did the friends fix the problem?",
            answer=f"{b.label} explained the truth, and then {a.label} shared the next turn at the well.",
        ),
        QAItem(
            question=f"What moral value does the story teach?",
            answer=f"It teaches {moral}: do not judge a friend before you know the whole story.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a well?",
            answer="A well is a deep hole in the ground built to reach water.",
        ),
        QAItem(
            question="Why do people care about water in a village?",
            answer="People need water for drinking, cooking, and staying healthy.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something is true, but they are mistaken.",
        ),
        QAItem(
            question="Why is friendship important?",
            answer="Friendship helps people trust each other, share, and feel less lonely.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (village, a_type, b_type)
        for village in VILLAGES
        for a_type in {"girl", "boy"}
        for b_type in {"girl", "boy"}
    ]


@dataclass
class StoryRegistry:
    pass


ASP_RULES = r"""
% A story is reasonable when it has a village, two friends, a well, a misunderstanding,
% and a restoration of friendship after the truth is explained.
friendship_restored(V) :- well(V), misunderstanding(V), kindness_shown(V), truth_told(V).
valid_story(V, A, B) :- well(V), friend(A), friend(B), A != B.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for k in VILLAGES:
        lines.append(asp.fact("well", k))
    for g in {"girl", "boy"}:
        lines.append(asp.fact("friend", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style well story world about misunderstanding and friendship.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--hero-a-type", choices=["girl", "boy"])
    ap.add_argument("--hero-b-type", choices=["girl", "boy"])
    ap.add_argument("--hero-a-name")
    ap.add_argument("--hero-b-name")
    ap.add_argument("--moral", choices=MORALS)
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
    village = args.village or rng.choice(list(VILLAGES))
    hero_a_type = args.hero_a_type or rng.choice(["girl", "boy"])
    hero_b_type = args.hero_b_type or rng.choice(["girl", "boy"])
    if hero_a_type == hero_b_type and args.hero_a_name is None and args.hero_b_name is None:
        pass
    moral = args.moral or rng.choice(MORALS)
    a_name = args.hero_a_name or rng.choice(NAMES[hero_a_type])
    b_name = args.hero_b_name or rng.choice([n for n in NAMES[hero_b_type] if n != a_name] or NAMES[hero_b_type])
    return StoryParams(village=village, hero_a=a_name, hero_b=b_name, hero_a_type=hero_a_type, hero_b_type=hero_b_type, moral=moral)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.village, params.hero_a_type, params.hero_b_type, params.hero_a, params.hero_b, params.moral)
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
    StoryParams(village="sunny_hamlet", hero_a="Mina", hero_b="Pip", hero_a_type="girl", hero_b_type="boy", moral="patience"),
    StoryParams(village="little_valley", hero_a="Nora", hero_b="Eli", hero_a_type="girl", hero_b_type="boy", moral="honesty"),
    StoryParams(village="quiet_lanes", hero_a="Tara", hero_b="Jory", hero_a_type="girl", hero_b_type="boy", moral="kindness"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
