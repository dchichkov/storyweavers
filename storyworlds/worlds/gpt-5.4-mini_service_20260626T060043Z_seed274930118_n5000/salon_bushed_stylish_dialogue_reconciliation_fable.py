#!/usr/bin/env python3
"""
A small fable-like storyworld about a salon visit, a bushed character, stylish
pride, dialogue, and reconciliation.
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
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Salon:
    name: str
    kind: str = "salon"
    tidy: bool = True
    chairs: int = 2


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, salon: Salon) -> None:
        self.salon = salon
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


SALONS = {
    "salon": Salon(name="the little salon", tidy=True, chairs=3),
}

NAMES = ["Pip", "Mina", "Ivy", "Tari", "Luna", "Nico", "Sage", "Milo"]
TRAITS = ["stylish", "careful", "bright", "kind", "gentle", "proud"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like salon storyworld.")
    ap.add_argument("--setting", choices=SALONS.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    setting = args.setting or "salon"
    hero_name = args.name or rng.choice(NAMES)
    friend_name = args.friend or rng.choice([n for n in NAMES if n != hero_name])
    return StoryParams(setting=setting, hero_name=hero_name, friend_name=friend_name)


def tell(params: StoryParams) -> World:
    world = World(SALONS[params.setting])
    hero = world.add(Entity(id=params.hero_name, kind="character", type="rabbit", traits=["stylish"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="fox", traits=["bushed"]))

    hero.memes["pride"] = 1
    friend.memes["weariness"] = 1
    friend.meters["tired"] = 1

    world.say(
        f"In {world.salon.name}, {hero.id} kept a stylish scarf straight and smiled at the mirror."
    )
    world.say(
        f"At the door came {friend.id}, bushed from a long walk, with a wilted bow and a sorry sigh."
    )
    world.para()
    world.say(
        f"{hero.id} said, 'You look worn out.'"
    )
    world.say(
        f"{friend.id} answered, 'I do not feel stylish today.'"
    )
    world.say(
        f"{hero.id} replied, 'A good heart is more stylish than any ribbon.'"
    )
    world.say(
        f"{friend.id} looked up, and their ears softened."
    )
    world.para()

    friend.memes["hurt"] = 1
    hero.memes["kindness"] = 1
    world.say(
        f"{hero.id} took a comb, brushed {friend.pronoun('possessive')} fur, and placed a neat clip near {friend.pronoun('possessive')} ear."
    )
    friend.memes["pride"] = 1
    friend.memes["hurt"] = 0
    friend.memes["reconciled"] = 1
    hero.memes["reconciled"] = 1
    world.say(
        f"{friend.id} smiled again, and the two friends left the salon side by side, both stylish now in a kinder way."
    )

    world.facts.update(hero=hero, friend=friend, salon=world.salon)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short fable set in a salon about a stylish friend helping a bushed one.",
        f"Tell a gentle story in {world.salon.name} where two friends use dialogue to reconcile.",
        "Write a child-friendly fable that ends with kindness making someone stylish again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {friend.id} meet?",
            answer=f"They met in {world.salon.name}, a salon where the mirror and chairs waited for visitors.",
        ),
        QAItem(
            question=f"Why did {friend.id} seem unhappy at first?",
            answer=f"{friend.id} was bushed from a long walk, so {friend.pronoun('possessive')} bow looked wilted and {friend.id} did not feel stylish.",
        ),
        QAItem(
            question=f"How did the friends make things better?",
            answer=f"They talked kindly, and {hero.id} brushed {friend.pronoun('possessive')} fur until {friend.id} smiled again. That was their reconciliation.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salon?",
            answer="A salon is a place where people or animals go to have hair, fur, or style cared for.",
        ),
        QAItem(
            question="What does bushed mean?",
            answer="Bushed means very tired, as if a long day has worn you out.",
        ),
        QAItem(
            question="What does stylish mean?",
            answer="Stylish means neat, attractive, and pleasing to look at.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when friends who were upset make peace and feel friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("\n== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
salon(salon).
style_word(stylish).
feeling(bushed).
feature(dialogue).
feature(reconciliation).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "salon"),
        asp.fact("style_word", "stylish"),
        asp.fact("feeling", "bushed"),
        asp.fact("feature", "dialogue"),
        asp.fact("feature", "reconciliation"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show feature/1."))
    feats = set(asp.atoms(model, "feature"))
    want = {("dialogue",), ("reconciliation",)}
    if feats == want:
        print("OK: ASP facts match Python story features.")
        return 0
    print("Mismatch in ASP verification.")
    return 1


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
        print(asp_program("#show feature/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show feature/1."))
        feats = sorted(set(asp.atoms(model, "feature")))
        print(feats)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        sample = generate(StoryParams(setting="salon", hero_name="Pip", friend_name="Mina"))
        samples = [sample]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
