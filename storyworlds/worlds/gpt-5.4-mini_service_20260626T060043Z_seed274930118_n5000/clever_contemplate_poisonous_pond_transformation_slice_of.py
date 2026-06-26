#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/clever_contemplate_poisonous_pond_transformation_slice_of.py
================================================================================

A small slice-of-life story world set by a pond: a clever child contemplates a
poisonous thing, makes a careful choice, and watches a quiet transformation
unfold.

Seed words used:
- clever
- contemplate
- poisonous

Core feature:
- Transformation

Setting:
- pond

Style:
- Slice of Life
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
    worn_by: Optional[str] = None
    plural: bool = False
    stage: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the pond"
    affords: set[str] = field(default_factory=lambda: {"contemplate", "careful_move", "watch", "transform"})


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.steps: list[str] = []

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
        clone.facts = dict(self.facts)
        clone.steps = list(self.steps)
        return clone


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    tad = world.entities.get("tadpole")
    if not tad:
        return out
    if tad.meters.get("grown", 0.0) < THRESHOLD:
        return out
    if tad.stage == "frog":
        return out
    tad.stage = "frog"
    tad.label = "small frog"
    out.append("The tadpole finished its transformation into a small frog.")
    return out


def _r_clear_water(world: World) -> list[str]:
    pond = world.entities.get("pond")
    if not pond:
        return []
    if pond.meters.get("poison", 0.0) < THRESHOLD:
        return []
    if pond.meters.get("cleaned", 0.0) < THRESHOLD:
        return []
    if pond.meters.get("clear", 0.0) >= THRESHOLD:
        return []
    pond.meters["clear"] = 1.0
    pond.meters["poison"] = 0.0
    return ["The pond water looked clear again."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_transform, _r_clear_water):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def creature_description(creature: Entity) -> str:
    if creature.stage == "frog":
        return "a small frog"
    return "a tadpole"


def setting_detail() -> str:
    return "The pond sat still under the morning light, with reeds leaning over the bank."


def tell(hero_name: str, hero_type: str, companion_name: str, companion_type: str) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    companion = world.add(Entity(id=companion_name, kind="character", type=companion_type, label=companion_name))
    pond = world.add(Entity(id="pond", type="pond", label="the pond", meters={"clear": 1.0}))
    berry = world.add(Entity(id="berry", type="berry", label="poisonous berry", phrase="a poisonous berry", meters={"poison": 1.0}))
    tadpole = world.add(Entity(id="tadpole", type="tadpole", label="a tadpole", stage="tadpole", meters={"grown": 0.0}))

    hero.memes["curiosity"] = 1.0
    hero.memes["care"] = 1.0
    companion.memes["calm"] = 1.0

    world.say(f"{hero_name} was a clever little {hero_type} who liked to sit by {world.setting.place} and contemplate small changes.")
    world.say(f"{hero_name} and {companion_name} often visited the water to listen to the reeds and watch the {creature_description(tadpole)} wiggle between the stems.")
    world.say(f"One morning, they noticed {berry.label} near the shore, and {hero_name} frowned because poisonous things did not belong close to the water.")
    world.para()

    world.say(setting_detail())
    world.say(f"{hero_name} stood very still and contemplate(d) the problem, trying to think of the safest way to help.")
    world.say(f"Instead of touching the berry with bare hands, {hero_name} found a little scoop and nudged it into a leaf cup.")
    pond.meters["cleaned"] = 1.0
    propagate(world)
    world.say(f"{companion_name} smiled and held the leaf cup while {hero_name} carried it away from the bank.")
    world.para()

    tadpole.meters["grown"] = 1.0
    propagate(world)
    world.say(f"By afternoon, the {creature_description(tadpole)} had grown legs, and then it became a small frog.")
    world.say(f"{hero_name} laughed softly, because the pond was safe again and the little frog had a new shape to hop with.")

    world.facts.update(
        hero=hero,
        companion=companion,
        pond=pond,
        berry=berry,
        tadpole=tadpole,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a gentle slice-of-life story about {hero.id} by a pond, where a clever child contemplates something poisonous and makes a careful choice.",
        f"Tell a short story that includes a quiet pond, a poisonous berry, and a transformation from tadpole to frog.",
        f"Write a child-friendly story about noticing a danger, thinking carefully, and watching a small transformation happen near the pond.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    tadpole = f["tadpole"]
    berry = f["berry"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a clever little {hero.type}, and {companion.id}, who goes with {hero.id} to the pond.",
        ),
        QAItem(
            question=f"What problem did {hero.id} notice near the pond?",
            answer=f"{hero.id} noticed {berry.label} near the shore and understood that it was poisonous, so it should not stay close to the water.",
        ),
        QAItem(
            question=f"What changed in the story besides the berry being moved?",
            answer=f"The tadpole grew legs and transformed into a small frog, so the pond held a quiet little transformation too.",
        ),
        QAItem(
            question=f"How did {hero.id} handle the poisonous berry?",
            answer=f"{hero.id} used a little scoop and a leaf cup instead of bare hands, which was a clever and careful choice.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pond?",
            answer="A pond is a small body of still water, often with reeds, little animals, and quiet edges to sit beside.",
        ),
        QAItem(
            question="What does poisonous mean?",
            answer="Poisonous means something can hurt people or animals if they touch it or eat it, so it should be handled very carefully.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a different form, like a tadpole growing into a frog.",
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
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.stage:
            bits.append(f"stage={e.stage}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(hero_name="Mina", hero_type="girl", companion_name="Grandma", companion_type="grandmother"),
    StoryParams(hero_name="Owen", hero_type="boy", companion_name="Aunt Jo", companion_type="woman"),
    StoryParams(hero_name="Nori", hero_type="girl", companion_name="Papa", companion_type="father"),
]


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    seed: Optional[int] = None


ASP_RULES = r"""
poisonous(berry).
at_place(pond, pond).

transforms(tadpole,frog) :- stage(tadpole,tadpole), grown(tadpole).

careful(hero) :- clever(hero), contemplate(hero), sees(hero, poisonous_berry).
safe_move(hero, poisonous_berry) :- careful(hero).

valid_story(hero, pond) :- clever(hero), contemplate(hero), poisonous(poisonous_berry), transformation(tadpole,frog), setting(pond).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "pond"))
    lines.append(asp.fact("clever", "hero"))
    lines.append(asp.fact("contemplate", "hero"))
    lines.append(asp.fact("poisonous", "poisonous_berry"))
    lines.append(asp.fact("transformation", "tadpole", "frog"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    models = asp.solve(asp_program("#show valid_story/2."), models=1)
    ok = bool(models)
    if ok:
        print("OK: ASP program is satisfiable for the intended world shape.")
        return 0
    print("Mismatch: ASP program did not admit the intended story shape.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life pond story world with a poisonous detail and a transformation.")
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Unsupported gender choice.")
    if args.gender == "girl":
        hero_type = "girl"
    elif args.gender == "boy":
        hero_type = "boy"
    else:
        hero_type = rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(["Mina", "Owen", "Nori", "Tess", "Arlo", "Pia"])
    companion_name = args.companion or rng.choice(["Grandma", "Papa", "Aunt Jo", "Uncle Ben"])
    companion_type = "grandmother" if companion_name == "Grandma" else (
        "father" if companion_name == "Papa" else ("woman" if companion_name == "Aunt Jo" else "man")
    )
    return StoryParams(hero_name=hero_name, hero_type=hero_type, companion_name=companion_name, companion_type=companion_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.hero_name, params.hero_type, params.companion_name, params.companion_type)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.hero_name} by the pond"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
