#!/usr/bin/env python3
"""
storyworlds/worlds/doom_continue_sandbox_happy_ending_kindness_pirate.py
======================================================================

A tiny storyworld about a sandbox pirate tale where a bit of doom arrives,
the crew continues, and kindness leads to a happy ending.

Premise:
- A little pirate loves building and playing in a sandbox.
- A looming doom threatens the sand treasure or castle.
- The pirate and a kind helper continue anyway, fix the problem, and end happy.

The world model tracks both physical meters and emotional memes, and the story
is generated from the state transitions rather than from a frozen paragraph.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the sandbox"


@dataclass
class Trouble:
    id: str
    omen: str
    verb: str
    rush: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str = "hands"
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    kind: str = "friend"
    remedy: str = ""
    tail: str = ""


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _splash(world: World) -> list[str]:
    out: list[str] = []
    doom = world.facts["trouble"]
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("brave", 0.0) < THRESHOLD:
            continue
        if actor.meters.get(doom.mess, 0.0) < THRESHOLD:
            continue
        prize = world.get(world.facts["prize"].id)
        if prize.meters.get("dirty", 0.0) >= THRESHOLD:
            continue
        sig = ("splash", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
        out.append(f"The sand clung to {prize.label} and made it look worn.")
    return out


def _kindness_fix(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    trouble = world.facts["trouble"]
    prize = world.facts["prize"]
    if hero.memes.get("fear", 0.0) < THRESHOLD:
        return out
    if helper.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    if prize.meters.get("dirty", 0.0) < THRESHOLD:
        return out
    sig = ("kindness_fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] = 0.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1
    out.append(
        f"With kindness, they brushed the trouble away and kept the day going."
    )
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_splash, _kindness_fix):
            sents = rule(world)
            if sents:
                changed = True
                if narrate:
                    for s in sents:
                        world.say(s)


def tell_story(hero_name: str, hero_type: str, helper_type: str, seed: Optional[int] = None) -> World:
    world = World(Setting())
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type))
    treasure = world.add(Entity(id="Treasure", type="treasure", label="the little treasure chest", phrase="a little treasure chest"))
    trouble = Trouble(
        id="doom",
        omen="a gloomy shadow",
        verb="loom over the sandbox",
        rush="roll toward the sandbox",
        mess="fear",
        soil="sullied",
        tags={"doom"},
    )
    support = Helper(
        id="kindness",
        label="kindness",
        phrase="a kind helping hand",
        remedy="brush the sand away",
        tail="kept the little treasure safe",
    )

    hero.meters["brave"] = 1.0
    hero.memes["joy"] = 1.0
    helper.memes["kindness"] = 1.0
    treasure.meters["dirty"] = 0.0

    world.facts.update(hero=hero, helper=helper, prize=treasure, trouble=trouble, support=support)

    world.say(
        f"{hero.id} was a small {hero_type} pirate who loved the sandbox."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had a little treasure chest and a heart full of cheer."
    )
    world.para()
    world.say(
        f"Then a bit of doom came near, like {trouble.omen} ready to {trouble.verb}."
    )
    world.say(
        f"{hero.id} wanted to continue anyway, even though the sand looked mighty scary."
    )

    hero.memes["fear"] = 1.0
    hero.memes["resolve"] = 1.0
    helper.memes["kindness"] = 1.0
    treasure.meters["dirty"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"The kind helper smiled, knelt beside the chest, and helped {hero.id} {support.remedy}."
    )
    world.say(
        f"{hero.id} continued with courage, and the sandbox grew bright again."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["fear"] = 0.0
    helper.memes["kindness"] += 1
    treasure.meters["dirty"] = 0.0
    world.say(
        f"In the end, the little pirate kept the treasure safe, and the day ended in a happy ending."
    )

    return world


SETTINGS = {"sandbox": Setting(place="the sandbox")}

HEOR_NAMES = ["Milo", "Nina", "Toby", "Pia", "Ravi", "Sage", "Luna", "Kai"]
HERO_TYPES = ["boy", "girl"]
HELPER_TYPES = ["friend", "sibling", "parent", "mate"]


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


ASP_RULES = r"""
hero(H).
helper(K).
prize(P).
doom(T).
kindness(S).

continued(H) :- brave(H), fear(H), kindness(K).
happy_ending(H) :- continued(H), helped(K), safe(P).

valid_story(sandbox, H, K) :- hero(H), helper(K), place(sandbox).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "sandbox"),
        asp.fact("hero", "hero"),
        asp.fact("helper", "helper"),
        asp.fact("prize", "treasure"),
        asp.fact("doom", "doom"),
        asp.fact("kindness", "kindness"),
        asp.fact("brave", "hero"),
        asp.fact("fear", "hero"),
        asp.fact("helped", "helper"),
        asp.fact("safe", "treasure"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A sandbox pirate tale with doom, continue, kindness, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS.keys(), default="sandbox")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--helper", choices=HELPER_TYPES)
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
    return StoryParams(
        place=args.place or "sandbox",
        name=args.name or rng.choice(HEOR_NAMES),
        gender=args.gender or rng.choice(HERO_TYPES),
        helper=args.helper or rng.choice(HELPER_TYPES),
        seed=args.seed,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short pirate tale set in a sandbox where doom appears, but the child continues with kindness.",
        f"Tell a child-facing story about {hero.id}, a tiny pirate, who keeps going when doom comes near.",
        "Write a gentle sandbox adventure with a happy ending and a kind helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a small pirate who loved the sandbox.",
        ),
        QAItem(
            question="What problem came near the sandbox?",
            answer="A bit of doom came near and made the little treasure look dusty and sad.",
        ),
        QAItem(
            question=f"How did {hero.id} keep going?",
            answer=f"{hero.id} continued anyway, and the kind helper stayed beside {hero.id} with a gentle smile.",
        ),
        QAItem(
            question=f"What made the ending happy?",
            answer=f"Kindness helped clean up the trouble, so {hero.id} could smile and the sandbox day could end happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, being gentle, and caring about someone else's feelings.",
        ),
        QAItem(
            question="What is a sandbox?",
            answer="A sandbox is a small box or space filled with sand where children can play and build.",
        ),
        QAItem(
            question="What does continue mean?",
            answer="Continue means to keep going without stopping.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and things end well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params.name, params.gender, params.helper, params.seed)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("sandbox", "pirate", "kindness")]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print("OK: clingo gate matches valid_combos().")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible story combo(s):")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place="sandbox", name=n, gender=g, helper=h)) for n, g, h in [
            ("Milo", "boy", "friend"),
            ("Nina", "girl", "sibling"),
            ("Toby", "boy", "parent"),
            ("Pia", "girl", "mate"),
        ]]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
