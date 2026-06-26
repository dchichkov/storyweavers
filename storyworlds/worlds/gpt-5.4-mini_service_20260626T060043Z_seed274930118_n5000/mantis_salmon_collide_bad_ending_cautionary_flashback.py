#!/usr/bin/env python3
"""
A small adventure-style story world about a mantis, a salmon, and a risky
collision near a rushing river. The tale is built as a simulated sequence with
a cautionary flashback and a bad ending when the warning is ignored.
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

WORLD_NAME = "mantis_salmon_collide_bad_ending_cautionary_flashback"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    name: str = ""
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "mantis":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "salmon":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class River:
    name: str = "the river"
    current: float = 1.0
    rocks: bool = True
    bank: str = "reed bank"


@dataclass
class StoryParams:
    place: str = "riverbank"
    hero_name: str = "Mira"
    companion_name: str = "Silt"
    seed: Optional[int] = None


@dataclass
class World:
    river: River
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: a mantis, a salmon, and a warning they should have heeded.")
    ap.add_argument("--place", default="riverbank", choices=["riverbank"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero-name")
    ap.add_argument("--companion-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place,
        hero_name=args.hero_name or rng.choice(["Mira", "Lina", "Tess", "Ari"]),
        companion_name=args.companion_name or rng.choice(["Silt", "Pip", "Nori", "Reed"]),
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("creature", "mantis"),
            asp.fact("creature", "salmon"),
            asp.fact("can_collide", "mantis", "salmon"),
            asp.fact("setting", "riverbank"),
            asp.fact("hazard", "current"),
            asp.fact("hazard", "rocks"),
        ]
    )


ASP_RULES = r"""
danger(A,B) :- can_collide(A,B).
bad_ending(A,B) :- danger(A,B), hazard(current), hazard(rocks).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show danger/2.\n#show bad_ending/2."))
    danger = set(asp.atoms(model, "danger"))
    bad = set(asp.atoms(model, "bad_ending"))
    py_danger = {("mantis", "salmon")}
    py_bad = {("mantis", "salmon")}
    if danger == py_danger and bad == py_bad:
        print("OK: ASP parity matches Python gates.")
        return 0
    print("MISMATCH:")
    print("ASP danger:", sorted(danger))
    print("PY danger:", sorted(py_danger))
    print("ASP bad:", sorted(bad))
    print("PY bad:", sorted(py_bad))
    return 1


def _cautionary_flashback(world: World, hero: Entity, fish: Entity) -> None:
    if "flashback" in world.fired:
        return
    world.fired.add("flashback")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    fish.memes["warning"] = fish.memes.get("warning", 0) + 1
    world.say(
        f"Long before the stormy crossing, {hero.name} remembered a flashback: "
        f"a stranded beetle had once slipped from a stone and vanished in the rushing water."
    )
    world.say(
        f'That memory made the moment feel cautionary. "Do not leap at the edge when the current is hungry," '
        f'{hero.name} had told {fish.name} then.'
    )


def _approach_river(world: World, hero: Entity, fish: Entity) -> None:
    world.say(
        f"{hero.name} crept along {world.river.bank} while {fish.name} flashed silver in the water below."
    )
    world.say(
        f"The adventure felt small at first, but the river tugged hard at every leaf and twig."
    )


def _collision(world: World, hero: Entity, fish: Entity) -> None:
    if "collide" in world.fired:
        return
    world.fired.add("collide")
    hero.meters["impact"] = hero.meters.get("impact", 0) + 1
    fish.meters["impact"] = fish.meters.get("impact", 0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    fish.memes["panic"] = fish.memes.get("panic", 0) + 1
    world.say(
        f"Then the mantis and the salmon collided at the edge of the stone. Water splashed high, and both lost their footing."
    )


def _bad_ending(world: World, hero: Entity, fish: Entity) -> None:
    if "ending" in world.fired:
        return
    world.fired.add("ending")
    hero.meters["safety"] = 0
    fish.meters["safety"] = 0
    hero.memes["regret"] = hero.memes.get("regret", 0) + 1
    world.say(
        f"{hero.name} reached for the bank too late. The current pulled the lesson away, and the salmon slipped downstream into the dark reeds."
    )
    world.say(
        f"It was a bad ending: the warning had been clear, but the river was quicker than pride."
    )


def generate_world(params: StoryParams) -> World:
    world = World(river=River())
    hero = world.add(Entity(id="mantis", kind="character", type="mantis", name=params.hero_name, role="tracker"))
    fish = world.add(Entity(id="salmon", kind="character", type="salmon", name=params.companion_name, role="guide"))
    world.facts["hero"] = hero
    world.facts["fish"] = fish
    world.facts["place"] = params.place

    world.say(
        f"{hero.name} was a brave little mantis who loved trail-hopping through tall grass and over bright stones."
    )
    world.say(
        f"{fish.name} was a quick salmon who knew every twist of the stream and every safe place to slip past the rocks."
    )

    world.para()
    _approach_river(world, hero, fish)
    _cautionary_flashback(world, hero, fish)
    world.para()
    hero.memes["determination"] = hero.memes.get("determination", 0) + 1
    world.say(
        f'Even so, {hero.name} whispered, "I can make it across first," and stepped onto the wet stone.'
    )
    _collision(world, hero, fish)
    _bad_ending(world, hero, fish)

    world.facts["danger"] = True
    world.facts["resolved"] = False
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    fish = world.facts["fish"]
    return [
        f'Write a short Adventure story about a mantis named {hero.name} and a salmon named {fish.name} near a river.',
        f'Tell a cautionary flashback tale where {hero.name} ignores a warning and collides with a salmon in a rushing stream.',
        f'Write a child-facing story that uses the words "mantis", "salmon", and "collide", and ends in a bad ending with a lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    fish = world.facts["fish"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.name}, a little mantis, and {fish.name}, a quick salmon, traveling by the river.",
        ),
        QAItem(
            question=f"What did the flashback remind {hero.name} of?",
            answer="It reminded the mantis of an earlier warning about how a hungry current can take away a careless climber.",
        ),
        QAItem(
            question=f"What happened when the mantis and the salmon met at the stone?",
            answer="They collided at the edge of the river, splashed hard, and lost the safe footing they needed.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly, with the salmon slipping downstream and the mantis learning too late that the warning had been true.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salmon?",
            answer="A salmon is a fish that lives in water and can swim upstream against strong moving water.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a warning so someone can avoid a mistake or danger.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part that remembers something from before the main moment in the story.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items())}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items())}}}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def resolve_all(args: argparse.Namespace) -> list[StoryParams]:
    return [
        StoryParams(place="riverbank", hero_name="Mira", companion_name="Silt"),
        StoryParams(place="riverbank", hero_name="Ari", companion_name="Nori"),
        StoryParams(place="riverbank", hero_name="Tess", companion_name="Reed"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show danger/2.\n#show bad_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show danger/2.\n#show bad_ending/2."))
        print("danger:", sorted(asp.atoms(model, "danger")))
        print("bad_ending:", sorted(asp.atoms(model, "bad_ending")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = resolve_all(args)
        for p in params_list:
            samples.append(generate(p))
    else:
        rng = random.Random(base_seed)
        for i in range(args.n):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
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
