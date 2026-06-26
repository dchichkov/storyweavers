#!/usr/bin/env python3
"""
Story world: a jeweler's sudden wallop mystery.

A small, child-friendly simulation where a curious child visits a jeweler,
there is a sudden wallop, and clues, foreshadowing, and friendship guide the
resolution. The story is state-driven rather than a frozen template.
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

TRY_LABELS = ["window", "drawer", "counter", "box", "bag"]
GEM_LABELS = ["blue gem", "red gem", "amber pin", "silver key", "tiny pearl"]
CHAR_NAMES = ["Milo", "Nina", "Pip", "Lina", "Toby", "June", "Arlo", "Sia"]
ADJECTIVES = ["curious", "brave", "gentle", "quiet", "bright", "patient"]


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little jewelry shop"
    detail: str = "glass cases"
    secret_spot: str = "back room"


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    jeweler_name: str
    jewel: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery about a jeweler, curiosity, and friendship.")
    ap.add_argument("--place", choices=["shop", "market", "museum"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--jeweler-name")
    ap.add_argument("--jewel", choices=["blue gem", "red gem", "amber pin", "silver key", "tiny pearl"])
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
    place = args.place or rng.choice(["shop", "market", "museum"])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHAR_NAMES)
    jeweler_name = args.jeweler_name or rng.choice([n for n in CHAR_NAMES if n != name])
    jewel = args.jewel or rng.choice(GEM_LABELS)
    return StoryParams(place=place, name=name, gender=gender, jeweler_name=jeweler_name, jewel=jewel)


def _setup_world(params: StoryParams) -> World:
    setting = Setting(
        place={"shop": "the little jewelry shop", "market": "the busy market", "museum": "the old museum"}[params.place],
        detail={"shop": "glass cases", "market": "bright stalls", "museum": "quiet rooms"}[params.place],
        secret_spot={"shop": "back room", "market": "storage tent", "museum": "side gallery"}[params.place],
    )
    w = World(setting)
    child_type = params.gender
    child = w.add(Entity(id="child", kind="character", type=child_type, label=params.name))
    jeweler = w.add(Entity(id="jeweler", kind="character", type="person", label=params.jeweler_name))
    gem = w.add(Entity(id="gem", type="jewel", label=params.jewel, phrase=f"a small {params.jewel}", owner=jeweler.id, caretaker=jeweler.id))
    clue = w.add(Entity(id="clue", type="clue", label="scratch mark"))
    child.memes["curiosity"] = 1
    jeweler.memes["care"] = 1
    w.facts.update(child=child, jeweler=jeweler, gem=gem, clue=clue, params=params)
    return w


def _predict_loss(world: World) -> bool:
    return bool(world.facts["gem"].meters.get("lost", 0) >= 1)


def tell_story(world: World) -> None:
    child: Entity = world.facts["child"]
    jeweler: Entity = world.facts["jeweler"]
    gem: Entity = world.facts["gem"]
    clue: Entity = world.facts["clue"]

    world.say(
        f"{child.label} was a {random.choice(ADJECTIVES)} child who liked looking closely at tiny things."
    )
    world.say(
        f"One afternoon, {child.label} visited {world.setting.place}, where {jeweler.label} showed {child.pronoun('object')} {gem.phrase} in {world.setting.detail}."
    )
    world.para()

    world.say(
        f"{child.label} felt a sudden tug of curiosity and leaned nearer to see the shine."
    )
    world.say(
        f"Then there was a sudden wallop from the door slamming in the wind, and the display rattled."
    )
    gem.meters["shaken"] = 1
    clue.meters["seen"] = 1
    world.facts["foreshadowed"] = True
    world.say(
        f"{jeweler.label} had noticed a faint scratch mark earlier, as if something in the shop had been ready to move."
    )
    world.para()

    world.say(
        f"{child.label} did not run away. Instead, {child.label} and {jeweler.label} looked together under the counter and beside the cases."
    )
    if not _predict_loss(world):
        world.say(
            f"They found the {gem.label} tucked safely near the {world.setting.secret_spot}, where the wallop had nudged it, not stolen it."
        )
        gem.meters["found"] = 1
        world.facts["resolved"] = True
    else:
        gem.meters["lost"] = 1
        world.say(
            f"The clue led them farther in, and after a careful search they found the {gem.label} at last."
        )
        world.facts["resolved"] = True

    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["friendship"] = child.memes.get("friendship", 0) + 1
    jeweler.memes["friendship"] = jeweler.memes.get("friendship", 0) + 1
    world.say(
        f"{child.label} smiled, because the mystery was solved and the jeweler was glad to have a friend who stayed and helped."
    )
    world.say(
        f"By evening, the shop was calm again, and the {gem.label} glittered safely in its place."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a short mystery for a child named {p.name} about a jeweler and a sudden wallop.',
        f"Tell a gentle story where {p.name} uses curiosity to help {p.jeweler_name} find {p.jewel}.",
        f"Write a small friendship mystery set in {world.setting.place} with clues and a careful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    jeweler: Entity = f["jeweler"]
    gem: Entity = f["gem"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"It was about {child.label}, who visited {world.setting.place} and helped {jeweler.label} with the mystery.",
        ),
        QAItem(
            question=f"What happened that made the shop feel surprising?",
            answer="A sudden wallop from the slamming door made the display rattle and turned the quiet visit into a mystery.",
        ),
        QAItem(
            question=f"What did {jeweler.label} show {child.label}?",
            answer=f"{jeweler.label} showed {child.label} {gem.phrase} inside the shop.",
        ),
        QAItem(
            question=f"How did friendship help at the end?",
            answer=f"{child.label} stayed to help, and that friendship made the search easier and the ending happy.",
        ),
        QAItem(
            question=f"What clue had been noticed before the mystery got bigger?",
            answer="A faint scratch mark had foreshadowed that something in the shop might move when the wallop happened.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a jeweler do?",
            answer="A jeweler works with jewelry, showing, fixing, and keeping gems and shiny things safe.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more and look closely at things.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints something important may happen later in the story.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people help one another, stay kind, and care about each other.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("role", "jeweler"),
            asp.fact("theme", "curiosity"),
            asp.fact("theme", "foreshadowing"),
            asp.fact("theme", "friendship"),
            asp.fact("event", "sudden"),
            asp.fact("event", "wallop"),
        ]
    )


ASP_RULES = r"""
role(jeweler).
theme(curiosity).
theme(foreshadowing).
theme(friendship).
event(sudden).
event(wallop).

mystery_story :- role(jeweler), event(sudden), event(wallop), theme(curiosity), theme(foreshadowing), theme(friendship).
#show mystery_story/0.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    ok = any(sym.name == "mystery_story" for sym in model)
    if ok:
        print("OK: ASP twin recognizes the mystery story features.")
        return 0
    print("MISMATCH: ASP twin did not recognize the story features.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    tell_story(world)
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
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: type={e.type} label={e.label!r} meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


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
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="shop", name="Milo", gender="boy", jeweler_name="Iris", jewel="blue gem"),
            StoryParams(place="market", name="Nina", gender="girl", jeweler_name="Owen", jewel="amber pin"),
            StoryParams(place="museum", name="Pip", gender="boy", jeweler_name="Mara", jewel="silver key"),
        ]
        samples = [generate(p) for p in curated]
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
