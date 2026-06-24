#!/usr/bin/env python3
"""
A standalone storyworld for a comedic conference misunderstanding.

Seed premise:
- Koa attends a conference.
- A "root" reference is misunderstood in dialogue.
- The misunderstanding creates tension, then resolves with a funny clarification.
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

THEME = "conference"
FOCUS_WORDS = {"koa", "root", "conference"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
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
    place: str
    setting_word: str = "conference"


@dataclass
class Topic:
    id: str
    label: str
    misunderstanding: str
    clarification: str
    comedy_image: str


@dataclass
class StoryParams:
    topic: str
    name: str
    colleague: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
    "hall": Setting(place="the conference hall"),
    "lobby": Setting(place="the lobby"),
    "breakroom": Setting(place="the break room"),
}

TOPICS = {
    "root": Topic(
        id="root",
        label="root",
        misunderstanding=(
            "When someone said they needed the root, Koa thought they meant a root "
            "from the ground, like a carrot-shaped plant part."
        ),
        clarification=(
            "The speaker meant the root of the problem, not a vegetable."
        ),
        comedy_image=(
            "Koa carefully held up a tiny potted root as if it were the keynote slide."
        ),
    ),
    "koa": Topic(
        id="koa",
        label="Koa",
        misunderstanding=(
            "When the host called for Koa, the room went quiet because Koa thought "
            "they were asking for a special chair or a microphone brand."
        ),
        clarification=(
            "The host was simply asking for Koa to come to the front."
        ),
        comedy_image=(
            "Koa waved at the microphone like it was a new friend with a name tag."
        ),
    ),
    "conference": Topic(
        id="conference",
        label="conference",
        misunderstanding=(
            "When someone said the conference had a lot of roots, Koa looked under "
            "the chairs for actual plant roots instead of the roots of ideas."
        ),
        clarification=(
            "The speaker meant origins, reasons, and the starting point of a story."
        ),
        comedy_image=(
            "Koa found only tangled cords and looked very proud of the wrong discovery."
        ),
    ),
}

NAMES = ["Koa", "Milo", "Nina", "Ari", "Lena", "Jun"]
COLLEAGUES = ["the speaker", "the host", "a friendly volunteer", "a puzzled editor"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedic conference story world with a misunderstanding.")
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--name")
    ap.add_argument("--colleague", choices=COLLEAGUES)
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
    topic = args.topic or rng.choice(list(TOPICS))
    name = args.name or rng.choice(NAMES)
    colleague = args.colleague or rng.choice(COLLEAGUES)
    return StoryParams(topic=topic, name=name, colleague=colleague)


def valid_story(params: StoryParams) -> bool:
    return params.topic in TOPICS and bool(params.name) and bool(params.colleague)


def _python_gate() -> list[tuple[str, str, str]]:
    combos = []
    for topic in TOPICS:
        for name in NAMES:
            for colleague in COLLEAGUES:
                combos.append((topic, name, colleague))
    return combos


ASP_RULES = r"""
topic(root).
topic(koa).
topic(conference).

name(koa_name). name(milo_name). name(nina_name). name(ari_name). name(lena_name). name(jun_name).
colleague(speaker). colleague(host). colleague(volunteer). colleague(editor).

valid(T,N,C) :- topic(T), name(N), colleague(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in TOPICS:
        lines.append(asp.fact("topic", t))
    for n in NAMES:
        lines.append(asp.fact("name", n.lower()))
    for c in COLLEAGUES:
        lines.append(asp.fact("colleague", c.replace("the ", "").replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(_python_gate())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} buzzed with badges, water cups, and tiny paper signs."


def generate_story(world: World, params: StoryParams) -> None:
    topic = TOPICS[params.topic]
    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    colleague = world.add(Entity(id="colleague", kind="character", type="adult", label=params.colleague))

    hero.memes["curiosity"] = 1
    hero.memes["confusion"] = 0
    hero.memes["joy"] = 0
    colleague.memes["patience"] = 1

    world.say(f"{hero.id} arrived at the conference hall with a bright badge and a careful step.")
    world.say(setting_detail(world.setting))
    world.say(f"{hero.id} listened hard because {params.colleague} was about to explain something important.")
    world.para()

    world.say(f"Then {params.colleague} said they needed the {topic.label}.")
    world.say(topic.misunderstanding)
    hero.memes["confusion"] += 1
    hero.meters["attention"] = 1
    world.say(f"{hero.id} nodded seriously and searched for a way to help.")
    world.say(topic.comedy_image)
    world.para()

    hero.memes["confusion"] += 1
    world.say(f"{params.colleague} blinked, then laughed kindly and said, '{topic.clarification}'")
    world.say(f"{hero.id} laughed too, because the mix-up was harmless and very silly.")
    hero.memes["joy"] += 2
    hero.memes["confusion"] = 0
    world.say(f"In the end, {hero.id} sat by the table with a grin, and the conference felt friendly again.")

    world.facts.update(
        hero=hero,
        colleague=colleague,
        topic=topic,
        setting=world.setting,
        resolved=True,
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS["hall"])
    generate_story(world, params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    topic = f["topic"]
    hero = f["hero"]
    return [
        f'Write a short comedy story about {hero.id} at a conference where the word "{topic.label}" causes a misunderstanding.',
        f"Tell a child-friendly dialogue story in which {hero.id} mishears a conference request and then learns the funny meaning.",
        f'Write a gentle, funny story that includes the words "koa", "root", and "conference".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    topic = f["topic"]
    colleague = f["colleague"]
    return [
        QAItem(
            question=f"Where was {hero.id} when the misunderstanding happened?",
            answer=f"{hero.id} was at the conference in the conference hall.",
        ),
        QAItem(
            question=f"What word caused the confusion for {hero.id}?",
            answer=f"The word was '{topic.label}'. {topic.misunderstanding}",
        ),
        QAItem(
            question=f"Who explained the funny mix-up to {hero.id}?",
            answer=f"{colleague.label} explained it kindly and cleared up the misunderstanding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a conference?",
            answer="A conference is a meeting where people gather to share ideas, listen, ask questions, and talk about a topic.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think a word or situation means one thing, but it really means something else.",
        ),
        QAItem(
            question="Why do people tell jokes at a comedy story?",
            answer="People tell jokes to make the story playful, surprising, and fun to hear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} {e.type:8} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(topic="root", name="Koa", colleague="the speaker"),
    StoryParams(topic="koa", name="Milo", colleague="the host"),
    StoryParams(topic="conference", name="Nina", colleague="a friendly volunteer"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            if not valid_story(params):
                raise StoryError("invalid story parameters")
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
            header = f"### {p.name} / {p.topic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
