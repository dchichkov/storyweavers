#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bump_dim_guy_bravery_fable.py
===========================================================================================================

A small fable-style story world about a guy, a dim path, a bump in the way,
and the brave choice that turns a stumble into a kind act.

Premise:
- A little guy walks home at dusk with a lantern that is too dim.
- He bumps a hidden stone on the path and nearly drops his basket.
- Instead of grumbling, he uses bravery to ask for help and share his light.
- The path becomes safer, and the ending proves the change: the lantern is
  bright enough now, and the guy is gentler than before.

World model:
- Physical meters track light, balance, heaviness, steadiness, and brightness.
- Emotional memes track courage, worry, pride, kindness, and calm.
- The story changes because the guy's state changes, not because of a frozen
  paragraph with swapped nouns.

The tale is intentionally fable-like: simple, concrete, and ending with a small
moral-shaped image.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "guy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the lane"
    light: str = "dusk"
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class ProblemDef:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AidDef:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    tail: str


@dataclass
class StoryParams:
    setting: str
    problem: str
    object: str
    aid: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lane": Setting(place="the lane", light="dusk", affords={"bump"}),
    "orchard": Setting(place="the orchard path", light="evening", affords={"bump"}),
    "hill": Setting(place="the hill road", light="twilight", affords={"bump"}),
}

PROBLEMS = {
    "bump": ProblemDef(
        id="bump",
        verb="walk carefully",
        gerund="walking carefully",
        rush="stumble over the hidden stone",
        mess="unsteady",
        zone={"feet"},
        keyword="bump-dim",
        tags={"bump", "dim", "path"},
    ),
}

OBJECTS = {
    "lantern": ObjectDef(
        id="lantern",
        label="lantern",
        phrase="a small lantern with a dim wick",
        region="hand",
    ),
    "basket": ObjectDef(
        id="basket",
        label="basket",
        phrase="a woven basket of apples",
        region="arm",
    ),
}

AIDS = {
    "match": AidDef(
        id="match",
        label="bright match",
        phrase="a bright match",
        helps={"dim"},
        covers={"hand"},
        tail="they touched the wick to the bright match",
    ),
    "lamp": AidDef(
        id="lamp",
        label="hired lamp",
        phrase="a hired lamp on a hook",
        helps={"dim"},
        covers={"hand"},
        tail="they hung the lantern beside the hired lamp",
    ),
    "friendlight": AidDef(
        id="friendlight",
        label="neighbor's lamp",
        phrase="a neighbor's lamp",
        helps={"dim"},
        covers={"hand", "path"},
        tail="their neighbor walked beside them with a lamp",
    ),
}

GENDER_NAMES = ["Milo", "Ezra", "Otis", "Theo", "Ned", "Ivo", "Luca", "Arlo"]
TRAITS = ["small", "thoughtful", "quiet", "steady", "simple"]


# ---------------------------------------------------------------------------
# World helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    guy = world.add(Entity(
        id=params.name,
        kind="character",
        type="guy",
        meters={"balance": 1.0, "brightness": 0.0, "steady": 0.5},
        memes={"bravery": 1.0, "worry": 0.0, "kindness": 0.0, "pride": 0.0},
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase=OBJECTS["lantern"].phrase,
        owner=guy.id,
        caretaker=guy.id,
        worn_by=guy.id,
        meters={"light": 0.5, "brightness": 0.5},
    ))
    basket = world.add(Entity(
        id="basket",
        type="basket",
        label="basket",
        phrase=OBJECTS["basket"].phrase,
        owner=guy.id,
        caretaker=guy.id,
        worn_by=guy.id,
        meters={"heaviness": 0.6},
    ))
    aid = world.add(Entity(
        id=params.aid,
        type="aid",
        label=AIDS[params.aid].label,
        phrase=AIDS[params.aid].phrase,
    ))
    world.facts.update(guy=guy, lantern=lantern, basket=basket, aid=aid)
    return world


def dim_path_story(world: World, problem: ProblemDef) -> None:
    guy: Entity = world.facts["guy"]
    lantern: Entity = world.facts["lantern"]
    basket: Entity = world.facts["basket"]

    world.say(
        f"{guy.id} was a small guy who liked to come home before the stars were fully awake."
    )
    world.say(
        f"He carried {lantern.phrase} and {basket.phrase}, and he believed a little light could be enough."
    )
    world.say(
        f"On {world.setting.place}, the {world.setting.light} made the stones look soft and sleepy."
    )
    world.para()

    guy.memes["worry"] += 1.0
    guy.meters["balance"] -= 0.2
    lantern.meters["light"] -= 0.3
    lantern.meters["brightness"] -= 0.2
    world.say(
        f"But the light was too dim, and when {guy.id} tried to {problem.verb}, his foot hit a hidden stone."
    )
    guy.meters["balance"] -= 0.5
    guy.memes["bravery"] += 0.2
    world.say(
        f"He bumped the stone, caught the basket in both hands, and stood still instead of making a fuss."
    )
    world.say(
        f"That quiet pause showed more bravery than a loud boast ever could."
    )


def resolve_with_aid(world: World, problem: ProblemDef, aid: AidDef) -> None:
    guy: Entity = world.facts["guy"]
    lantern: Entity = world.facts["lantern"]

    world.para()
    guy.memes["kindness"] += 1.0
    guy.memes["pride"] += 0.0
    world.say(
        f"{guy.id} asked for help, and a kind neighbor brought {aid.phrase}."
    )
    world.say(
        f"They made a better plan: {aid.tail}, and the little lantern grew warmer and brighter."
    )
    lantern.meters["light"] = 1.0
    lantern.meters["brightness"] = 1.0
    guy.meters["balance"] = 1.0
    guy.memes["worry"] = 0.0
    world.say(
        f"Then {guy.id} could {problem.gerund} again, only this time the lane looked safe and clear."
    )
    world.say(
        f"At the end, the guy walked home with steady steps, a bright lantern, and a kinder heart than before."
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    g = f["guy"]
    return [
        f'Write a short fable about a guy named {g.id}, a dim lantern, and a brave choice.',
        f"Tell a child-friendly story where {g.id} bumps a stone on a dim path and answers with bravery.",
        f'Write a simple fable that includes the word "{world.facts["problem"].keyword}" and ends with a brighter light.',
    ]


def story_qa(world: World) -> list[QAItem]:
    g: Entity = world.facts["guy"]
    lantern: Entity = world.facts["lantern"]
    aid: Entity = world.facts["aid"]
    problem: ProblemDef = world.facts["problem"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {g.id}, a small guy who is walking home with a dim lantern and a basket."
        ),
        QAItem(
            question=f"What went wrong on the path?",
            answer=f"The path was dim, so {g.id} bumped a hidden stone while trying to {problem.verb}."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The lantern became bright again, and {g.id} chose bravery and kindness instead of worry."
        ),
        QAItem(
            question=f"How did {aid.label} help?",
            answer=f"{aid.label.capitalize()} helped make the lantern brighter, which made the walk safer."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel nervous or scared."
        ),
        QAItem(
            question="Why can a dim light be a problem at night?",
            answer="A dim light makes it harder to see stones, steps, and other things on the path."
        ),
        QAItem(
            question="What is a lantern for?",
            answer="A lantern holds light so people can see better when it is dark."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(sorted(e.meters.items()))} memes={dict(sorted(e.memes.items()))}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem(bump).
setting(lane).
setting(orchard).
setting(hill).

dim(problem, bump).
has_moral(bravery).

can_story(S, P, A) :- setting(S), problem(P), aid(A), has_moral(bravery).
valid_choice(S, P, A) :- can_story(S, P, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    lines.append(asp.fact("has_moral", "bravery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_choices() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_choice/3."))
    return sorted(set(asp.atoms(model, "valid_choice")))


def python_valid_choices() -> list[tuple]:
    return sorted((s, p, a) for s in SETTINGS for p in PROBLEMS for a in AIDS)


def asp_verify() -> int:
    py = set(python_valid_choices())
    cl = set(asp_valid_choices())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} choices).")
        return 0
    print("Mismatch between ASP and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or "bump"
    obj = args.object or "lantern"
    aid = args.aid or rng.choice(list(AIDS))
    if problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if obj not in OBJECTS:
        raise StoryError("Unknown object.")
    if aid not in AIDS:
        raise StoryError("Unknown aid.")
    return StoryParams(
        setting=setting,
        problem=problem,
        object=obj,
        aid=aid,
        name=args.name or rng.choice(GENDER_NAMES),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    problem = PROBLEMS[params.problem]
    aid = AIDS[params.aid]
    dim_path_story(world, problem)
    resolve_with_aid(world, problem, aid)
    world.facts.update(problem=problem, aid=aid)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-style story world about bravery and a dim path.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--object", choices=list(OBJECTS))
    ap.add_argument("--aid", choices=list(AIDS))
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_choice/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_choices()
        print(f"{len(combos)} valid choices:")
        for row in combos:
            print(" ".join(row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for aid in AIDS:
                params = StoryParams(setting=setting, problem="bump", object="lantern", aid=aid, name="Milo")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
