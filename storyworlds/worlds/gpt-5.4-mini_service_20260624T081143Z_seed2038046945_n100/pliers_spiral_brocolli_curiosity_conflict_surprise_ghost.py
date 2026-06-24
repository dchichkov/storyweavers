#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/pliers_spiral_brocolli_curiosity_conflict_surprise_ghost.py
====================================================================================================

A small ghost-story world built from the seed words:
pliers, spiral, brocolli.

The premise is a curious child in an old garden or tower notices a whispery
ghost near a spiral path. The tension comes from a stuck or tangled object
that cannot be fixed by guessing alone; the turn comes when the child uses
pliers carefully, and the surprise is that the ghost only wanted the brocolli
to be left alone or replanted in a gentler spot. The world tracks both physical
meters and emotional memes so the prose is state-driven rather than template-only.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"child", "girl", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    helps_with: set[str]
    safe: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    fragile: bool = False


@dataclass
class StoryParams:
    place: str
    clue: str
    tool: str
    name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "garden": Setting(place="the garden", detail="A spiral path curled between wet stones and bean rows.", affords={"search", "repair"}),
    "shed": Setting(place="the shed", detail="The shed smelled like dust, soil, and old wood.", affords={"search", "repair"}),
    "tower": Setting(place="the tower", detail="A narrow spiral stair wound upward beside a cracked window.", affords={"search"}),
}

TOOLS = {
    "pliers": Tool(id="pliers", label="pliers", verb="carefully use the pliers", helps_with={"bend_wire", "pull_thorn", "unhook"}),
}

CLUES = {
    "brocolli": Clue(id="brocolli", label="brocolli", phrase="a lopsided brocolli plant", location="garden", fragile=True),
    "sign": Clue(id="sign", label="sign", phrase="an old tin sign", location="shed", fragile=False),
    "lantern": Clue(id="lantern", label="lantern", phrase="a small lantern on the spiral stair", location="tower", fragile=False),
}

TRAITS = ["curious", "gentle", "brave", "careful"]
NAMES = ["Mina", "Theo", "Lena", "Arlo", "Nina", "Pip"]


def _make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name, meters={"curiosity": 0.0}, memes={"curiosity": 0.0, "conflict": 0.0, "surprise": 0.0}))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost", meters={"hush": 0.0}, memes={"mystery": 1.0}))
    clue = CLUES[params.clue]
    tool = TOOLS[params.tool]
    item = world.add(Entity(id=clue.id, type=clue.id, label=clue.label, phrase=clue.phrase, location=clue.location, meters={"stuck": 1.0 if clue.fragile else 0.0, "neatness": 0.0}, memes={"worry": 0.0}))
    world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.label, owner=child.id, location="pocket"))
    world.facts.update(child=child, ghost=ghost, clue=item, tool=tool, setting=setting)
    return world


def _warn_reasonable(params: StoryParams) -> None:
    if params.tool != "pliers":
        raise StoryError("This world only knows pliers as the useful tool.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.place == "tower" and params.clue == "brocolli":
        raise StoryError("The brocolli belongs in the garden, not the tower.")
    if params.place == "shed" and params.clue == "brocolli":
        raise StoryError("The brocolli story needs soil and a spiral path, so the shed is too plain.")


def generate_story(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    ghost: Entity = world.facts["ghost"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    tool: Tool = world.facts["tool"]  # type: ignore[assignment]

    world.say(f"{child.id} was a {world.facts['params'].trait} child who loved to look for hidden things.")
    world.say(f"One quiet afternoon, {child.id} followed a spiral path into {world.setting.place}. {world.setting.detail}")
    world.say(f"There, {child.id} found {clue.phrase} and heard a soft whisper near the leaves.")
    child.memes["curiosity"] += 1
    ghost.memes["mystery"] += 0.5
    world.para()
    world.say(f"{child.id} wanted to learn what the whisper meant, but the brocolli looked tangled and upset.")
    child.memes["conflict"] += 1
    clue.meters["stuck"] = 1.0
    world.say(f"The ghost drifted closer, then back, as if asking for help without words.")
    world.para()
    world.say(f"{child.id} remembered the pliers in {child.pronoun('possessive')} pocket and decided to use them gently.")
    clue.meters["stuck"] = 0.0
    clue.meters["neatness"] = 1.0
    world.say(f"With a careful turn, {child.id} used the pliers to unhook the little stems and set the brocolli upright.")
    child.memes["conflict"] = 0.0
    child.memes["surprise"] += 1
    ghost.memes["mystery"] = 0.0
    world.para()
    world.say(f"Then the ghost gave a tiny bow. It had not wanted a scare at all; it only wanted the brocolli safe and still.")
    world.say(f"{child.id} smiled at the spiral path, the neat green plant, and the quiet ghost fading like mist at dawn.")


def story_prompt(world: World) -> str:
    p = world.facts["params"]
    return f"Write a gentle ghost story about {p.name}, a spiral path, brocolli, and pliers."


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Why did {p.name} feel curious in the garden?",
            answer=f"{p.name} felt curious because the spiral path, the whisper, and the strange brocolli made the afternoon feel mysterious.",
        ),
        QAItem(
            question=f"What caused the conflict in the story?",
            answer=f"The conflict came from the tangled brocolli and the worry about fixing it the wrong way.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"It was solved when the child used the pliers gently to straighten the brocolli and make the ghost feel calm again.",
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer="The surprise was that the ghost was not trying to frighten anyone; it only wanted the brocolli cared for.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are pliers for?",
            answer="Pliers are a hand tool that can grip, bend, or pull small things that are hard to hold with bare fingers.",
        ),
        QAItem(
            question="What is a spiral?",
            answer="A spiral is a shape that curls around and around, like a winding stair or a shell.",
        ),
        QAItem(
            question="What is brocolli?",
            answer="Brocolli is a green vegetable with a thick stem and a bunch of small florets on top.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    _warn_reasonable(params)
    world = _make_world(params)
    world.facts["params"] = params
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[story_prompt(world)],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n-- trace --")
        for k, v in sample.world.facts.items():
            if k == "params":
                continue
            print(k, v)
    if qa:
        print()
        for section, items in (("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)):
            print(f"== {section} ==")
            for item in items:
                if isinstance(item, str):
                    print(item)
                else:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with pliers, spiral, and brocolli.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or ("brocolli" if place == "garden" else rng.choice(list(CLUES)))
    tool = args.tool or "pliers"
    if place == "tower" and clue == "brocolli":
        raise StoryError("The brocolli needs the garden setting.")
    if place == "shed" and clue == "brocolli":
        raise StoryError("The brocolli story needs the garden, not the shed.")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, clue=clue, tool=tool, name=name, trait=trait)


ASP_RULES = r"""
place(garden). place(shed). place(tower).
tool(pliers).
clue(brocolli). clue(sign). clue(lantern).

spiral(garden).
spiral(tower).

curiosity(Name) :- hero(Name).
conflict(Name) :- curiosity(Name), tangled(brocolli).
surprise(ghost) :- ghost_wants_care.

valid_story(P, C, T) :- place(P), clue(C), tool(T), not invalid(P, C, T).

invalid(tower, brocolli, pliers).
invalid(shed, brocolli, pliers).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        if place in {"garden", "tower"}:
            lines.append(asp.fact("spiral", place))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    lines.append(asp.fact("hero", "child"))
    lines.append(asp.fact("ghost_wants_care"))
    lines.append(asp.fact("tangled", "brocolli"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c, t) for p in SETTINGS for c in CLUES for t in TOOLS if not (p == "tower" and c == "brocolli") and not (p == "shed" and c == "brocolli")}
    asv = set(asp_valid_combos())
    if py == asv:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - asv))
    print("asp only:", sorted(asv - py))
    return 1


CURATED = [
    StoryParams(place="garden", clue="brocolli", tool="pliers", name="Mina", trait="curious"),
    StoryParams(place="garden", clue="sign", tool="pliers", name="Theo", trait="careful"),
]


def generate_one(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate_one(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            rng = random.Random(base + i)
            try:
                p = resolve_params(args, rng)
                p.seed = base + i
                s = generate_one(p)
            except StoryError as e:
                print(e)
                return
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, s in enumerate(samples):
        if len(samples) > 1 and not args.all:
            print(f"### variant {idx + 1}")
        elif args.all:
            p = s.params
            print(f"### {p.name}: {p.place} / {p.clue}")
        emit(s, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
