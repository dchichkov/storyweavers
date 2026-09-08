#!/usr/bin/env python3
"""
A small bedtime storyworld about kale, a mudroom surprise, and learning to pause.

The world models a child who wants to hide a kale leaf in a boot before bed.
A quiet clue, a helpful grown-up, and a cautious choice turn the surprise into
a gentle ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAME_POOL = ["Luna", "Milo", "Nina", "Toby", "Ivy", "Theo"]
HELPER_POOL = ["Grandma", "Dad", "Mom", "Aunt Jo"]
BOOT_COLORS = ["red", "yellow", "blue", "green"]
SURPRISES = [
    {
        "name": "a tiny garden snail",
        "clue": "the boot gave a soft, slow scrape",
        "reaction": "a little snail peeked from beneath the kale leaf",
        "helper": "placed a leaf beside the boot and guided the snail onto it",
        "lesson": "a surprise is safer when you stop, look, and ask for help",
        "ending": "the snail rested on its leafy raft until the moon made a silver path across the mudroom floor",
    },
    {
        "name": "a sleepy field mouse",
        "clue": "the boot made one faint, furry rustle",
        "reaction": "two bright eyes blinked from the shadow under the kale",
        "helper": "held a basket nearby and gently made a quiet path to the garden door",
        "lesson": "a hidden surprise can belong to someone who needs care",
        "ending": "the mouse curled in the basket while the mudroom grew still and warm around it",
    },
    {
        "name": "a curious tree frog",
        "clue": "the boot gave a tiny damp plop",
        "reaction": "a green frog wiggled free from beneath the kale leaf",
        "helper": "covered the frog with a bowl, slid paper underneath, and carried it outside",
        "lesson": "caution means moving slowly when a small creature may be frightened",
        "ending": "the frog hopped into the wet grass, leaving one bright dot of mud by the door",
    },
    {
        "name": "a lost ladybug",
        "clue": "the kale leaf trembled although the room was still",
        "reaction": "a red ladybug climbed onto the boot's shiny buckle",
        "helper": "opened the door a crack and offered a twig as a safe bridge",
        "lesson": "gentle patience can turn a startling moment into a kind one",
        "ending": "the ladybug crossed the twig and disappeared beneath a moonlit marigold",
    },
]


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "Grandma"
    boot_color: str = "red"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance_to_door", "kale_freshness", "safety"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "worry", "surprise", "relief", "care"):
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str = "mudroom"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _seed_number(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) * (i + 1) for i, ch in enumerate(
        f"{params.name}|{params.helper}|{params.boot_color}"
    ))


def _subject(label: str) -> str:
    return label if label and label[0].isupper() else label.capitalize()


def tell_world(params: StoryParams) -> World:
    rng = random.Random(_seed_number(params))
    surprise = SURPRISES[_seed_number(params) % len(SURPRISES)]
    w = World()
    child = w.add(Entity(
        id="child",
        kind="character",
        label=params.name,
        meters={"distance_to_door": 7.0, "kale_freshness": 1.0, "safety": 0.0},
        memes={"curiosity": 2.0, "worry": 0.0, "surprise": 0.0, "relief": 0.0, "care": 0.0},
    ))
    helper = w.add(Entity(id="helper", kind="character", label=params.helper))
    boot = w.add(Entity(
        id="boot",
        kind="object",
        label=f"{params.boot_color} boot",
        meters={"distance_to_door": 4.0, "kale_freshness": 0.0, "safety": 0.0},
        memes={},
    ))
    kale = w.add(Entity(
        id="kale",
        kind="food",
        label="a crisp kale leaf",
        meters={"distance_to_door": 3.0, "kale_freshness": 1.0, "safety": 0.0},
        memes={},
    ))
    w.facts.update(params=params, child=child, helper=helper, boot=boot, kale=kale, surprise=surprise)

    w.say(f"At bedtime, {params.name} padded into the mudroom in striped pajamas.")
    w.say(f"Beside the door stood a {params.boot_color} boot, still dusty from the garden.")
    w.say(f"{params.name} had found {kale.label} on the supper plate and decided to hide it in the boot as a funny surprise for {params.helper}.")
    w.say(f'"It will be the quietest joke in the whole house," {params.name} whispered.')
    w.para()

    child.memes["curiosity"] += 1
    child.meters["distance_to_door"] = 4.0
    w.say(f"{params.name} lifted the boot and tucked the kale inside.")
    w.say(f"But before the joke was ready, {surprise['clue']}.")
    child.memes["surprise"] = 1.0
    child.memes["worry"] = 1.0
    w.say(f"Then {surprise['reaction']}.")
    w.say(f"{params.name} froze with one hand on the boot and one foot halfway to the stairs.")
    w.say(f'"Should I run?" {params.name} asked.')
    w.say(f'"No running in the mudroom," {params.helper} answered softly. "Tell me what you saw."')
    w.para()

    w.say(f"{params.helper} knelt beside {params.name}, keeping both hands still.")
    w.say(f'"It is {surprise["name"]}," said {params.helper}. "Let us make a safe plan before we touch anything."')
    w.say(f'"I can wait," {params.name} said. "What should I do?"')
    w.say(f'"Step back, keep the door clear, and watch while I {surprise["helper"]}."')
    w.say(f"{params.name} stepped back and listened.")
    child.memes["worry"] = 0.0
    child.memes["relief"] = 1.0
    child.memes["care"] = 2.0
    child.meters["distance_to_door"] = 1.0
    child.meters["safety"] = 1.0
    boot.meters["safety"] = 1.0
    kale.meters["safety"] = 1.0
    w.say(f"When the little visitor was safe, {params.helper} smiled.")
    w.say(f'"Your surprise became a rescue," said {params.helper}. "That is a much better bedtime story."')
    w.say(f"{params.name} nodded. The kale was no longer a secret joke; it was part of a careful plan.")
    w.para()

    w.say(f"Before climbing into bed, {params.name} remembered the new rule: {surprise['lesson']}.")
    w.say(surprise["ending"].capitalize() + ".")
    w.facts.update(
        resolved=True,
        visitor=surprise["name"],
        clue=surprise["clue"],
        lesson=surprise["lesson"],
        ending=surprise["ending"],
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    visitor = world.facts["visitor"]
    return [
        f"Write a gentle bedtime story about {p.name}, kale, and a surprise in a {p.boot_color} boot in the mudroom.",
        f"Tell a cautionary story in which {p.name} pauses and asks {p.helper} for help when {visitor} appears.",
        f"Create a child-friendly mudroom adventure with kale, careful dialogue, and a peaceful moonlit ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    s = world.facts["surprise"]
    return [
        QAItem(
            question=f"What did {p.name} put in the {p.boot_color} boot?",
            answer=f"{p.name} put a crisp kale leaf in the {p.boot_color} boot as a quiet surprise.",
        ),
        QAItem(
            question="What caused the surprise in the mudroom?",
            answer=f"{s['clue'].capitalize()} Then {s['reaction']}.",
        ),
        QAItem(
            question=f"How did {p.name} and {p.helper} respond?",
            answer=f"{p.name} stopped and asked for help. {p.helper} made a safe plan and {s['helper']}.",
        ),
        QAItem(
            question="What lesson did the bedtime story teach?",
            answer=f"It taught that {s['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should someone move carefully around a small animal?",
            answer="Moving carefully helps keep the animal from becoming frightened or hurt.",
        ),
        QAItem(
            question="What is kale?",
            answer="Kale is a leafy green vegetable that people can eat.",
        ),
        QAItem(
            question="Why is asking a trusted grown-up useful during a surprise?",
            answer="A trusted grown-up can help notice what is happening and choose a safe next step.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 3) for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}")
    lines.append(f"  facts={{resolved: {world.facts.get('resolved')}, visitor: {world.facts.get('visitor')!r}}}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_plan(Child) :- pauses(Child), asks_help(Child), visitor_present.
kind_choice(Child) :- safe_plan(Child), moves_slowly(Child).
resolved_story(Child) :- kind_choice(Child), visitor_safe.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("visitor_present"),
        asp.fact("pauses", "luna"),
        asp.fact("asks_help", "luna"),
        asp.fact("moves_slowly", "luna"),
        asp.fact("visitor_safe"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show resolved_story/1."))
    found = set(asp.atoms(model, "resolved_story"))
    expected = {("luna",)}
    if found != expected:
        print("MISMATCH between ASP and Python story resolution:")
        print("  ASP:", sorted(found))
        print("  PY :", sorted(expected))
        return 1
    sample = generate(StoryParams(seed=22))
    if not sample.world or not sample.world.facts.get("resolved"):
        print("MISMATCH: generated story did not resolve.")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A kale bedtime surprise in a mudroom.")
    ap.add_argument("--name", choices=NAME_POOL)
    ap.add_argument("--helper", choices=HELPER_POOL)
    ap.add_argument("--boot-color", choices=BOOT_COLORS)
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
    return StoryParams(
        name=args.name or rng.choice(NAME_POOL),
        helper=args.helper or rng.choice(HELPER_POOL),
        boot_color=args.boot_color or rng.choice(BOOT_COLORS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved_story/1."))
        print(sorted(asp.atoms(model, "resolved_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, name in enumerate(NAME_POOL):
            params = StoryParams(
                name=name,
                helper=HELPER_POOL[index % len(HELPER_POOL)],
                boot_color=BOOT_COLORS[index % len(BOOT_COLORS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
