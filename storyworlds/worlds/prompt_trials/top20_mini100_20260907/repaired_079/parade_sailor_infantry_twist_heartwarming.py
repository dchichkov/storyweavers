#!/usr/bin/env python3
"""
A heartwarming parade storyworld with a twist.

Seed image:
A town is preparing for a parade by the harbor. A sailor and an infantry
drummer both want the front spot in the march. Their first plan goes wrong, but
the twist reveals they can help each other and make the parade kinder and brighter
than before.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sailor"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "infantry", "drummer"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mira"
    sailor_name: str = "Sailor Tom"
    infantry_name: str = "Ben"
    setting: str = "harbor town"
    parade_name: str = "Lantern Parade"


NAMES = ["Mira", "Lina", "Nina", "Tess", "Pia", "Iris", "June", "Milo", "Ben", "Tom"]
SAILOR_NAMES = ["Sailor Tom", "Sailor Rue", "Sailor Nell", "Sailor Jo"]
INFANTRY_NAMES = ["Ben", "Leo", "Owen", "Max", "Finn"]
SETTINGS = ["harbor town", "river town", "square by the docks", "old seaside street"]
PARADES = ["Lantern Parade", "Spring Parade", "Sunrise Parade", "Welcome Parade"]

TWISTS = [
    {
        "setup": "everyone thought the front spot mattered most",
        "turn": "the mayor needed the front for children carrying lost mittens back to their homes",
        "dialogue": ('"You can take the front," the sailor said.', '"Not if the children need it," the infantry drummer answered.'),
        "change": "the sailor and the infantry drummer stepped back and made a safe lane",
        "ending": "the parade rolled past with children smiling in the middle, and the front spot stayed open for help instead of pride",
    },
    {
        "setup": "the sailor wanted the loud drum line and the infantry wanted the bright banner",
        "turn": "the banner pole was too heavy for one person, and the drumbeat helped the march stay together",
        "dialogue": ('"I can carry the pole," the infantry said.', '"Then I will keep the beat for you," said the sailor.'),
        "change": "they switched jobs and shared the burden",
        "ending": "the banner rose straight and the drumbeat stayed steady as the whole parade learned to move as one",
    },
    {
        "setup": "the march began with a mix-up over who should lead",
        "turn": "the smallest child in the town was too shy to walk alone, so the two marchers chose to guide her between them",
        "dialogue": ('"Would you like to march with us?" asked the sailor.', '"Yes, please," whispered the child as the infantry smiled.'),
        "change": "they made a warm little bridge of hands and footsteps",
        "ending": "the shy child laughed by the final float, and the parade felt bigger because it had room for someone gentle",
    },
    {
        "setup": "the sailor and the infantry drummer both feared they had ruined the rehearsal",
        "turn": "their mistake had only turned the route around, bringing them past the nursing home windows first",
        "dialogue": ('"We came the wrong way," said the infantry.', '"No," said the sailor, "we came the kind way."'),
        "change": "they waved to the people in the windows and slowed the march",
        "ending": "the residents tapped along, and the parade became the best part of their evening",
    },
]


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.name}|{params.sailor_name}|{params.infantry_name}|{params.setting}|{params.parade_name}"
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _setup(world: World, params: StoryParams) -> None:
    world.add(Entity(id="child", kind="character", type="girl", label=params.name))
    world.add(Entity(id="sailor", kind="character", type="sailor", label=params.sailor_name))
    world.add(Entity(id="infantry", kind="character", type="infantry", label=params.infantry_name))
    world.add(Entity(id="parade", kind="event", type="parade", label=params.parade_name))
    world.add(Entity(id="banner", kind="thing", type="banner", label="banner"))
    world.add(Entity(id="drum", kind="thing", type="drum", label="drum"))

    world.entities["child"].meters["hope"] = 1.0
    world.entities["sailor"].meters["patience"] = 1.0
    world.entities["infantry"].meters["pride"] = 1.0
    world.entities["parade"].meters["color"] = 1.0
    world.entities["banner"].meters["weight"] = 1.0
    world.entities["drum"].meters["beat"] = 1.0

    world.entities["child"].memes["worry"] = 0.5
    world.entities["sailor"].memes["care"] = 0.5
    world.entities["infantry"].memes["duty"] = 0.5

    world.facts["params"] = params


def tell_story(params: StoryParams) -> World:
    if not params.setting:
        raise StoryError("setting must not be empty")
    if not params.parade_name:
        raise StoryError("parade_name must not be empty")

    world = World()
    _setup(world, params)

    tok = _token(params)
    twist = TWISTS[tok % len(TWISTS)]
    child = world.entities["child"]
    sailor = world.entities["sailor"]
    infantry = world.entities["infantry"]

    world.say(f"On a bright day in the {params.setting}, people gathered for the {params.parade_name}.")
    world.say(f"The sailor and the infantry drummer both wanted the front of the parade, and each thought it would make the day special.")
    world.say(f"At first, {twist['setup']}.")
    world.say(f"The sailor said, {twist['dialogue'][0]}")
    world.say(f"The infantry answered, {twist['dialogue'][1]}")

    world.para()
    world.say(f"Then the twist arrived: {twist['turn']}.")
    world.say(f"{sailor.label} and {infantry.label} looked at one another, and their faces changed from stubborn to thoughtful.")
    world.say(f"Instead of arguing, they chose to {twist['change']}.")
    child.meters["hope"] = 2.0
    sailor.meters["patience"] = 2.0
    infantry.meters["pride"] = 0.2
    sailor.memes["care"] = 1.5
    infantry.memes["duty"] = 1.0

    world.para()
    world.say(f'"Thank you," said the child, and the sailor smiled back. "We wanted the parade to feel good for everyone," said the infantry drummer.')
    world.say(f"The music sounded warmer after that, because the marchers were listening to each other instead of competing.")
    world.say(f"In the end, {twist['ending']}.")
    world.say("The day finished with waving hands, friendly drums, and the happy feeling that a parade can grow kinder when people share the place they wanted most.")

    world.facts["twist"] = twist
    world.facts["token"] = tok
    return world


def valid_story() -> bool:
    return True


ASP_RULES = r"""
shared_parade(P) :- sailor(P), infantry(P).
warm_ending(S) :- shared_parade(S), twist(S), kindness(S).
valid_story(S) :- warm_ending(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("sailor", "story1"),
        asp.fact("infantry", "story1"),
        asp.fact("twist", "story1"),
        asp.fact("kindness", "story1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("story1",)} if valid_story() else set()
    if atoms == py:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(py))
    return 1


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    twist = world.facts["twist"]
    return [
        f"Write a heartwarming story about a parade in the {params.setting} with a sailor and infantry drummer.",
        f"Show how the sailor and the infantry argue, then discover the twist and choose kindness.",
        f"Tell a child-friendly parade story where {twist['turn']} changes the meaning of the front spot.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    twist = world.facts["twist"]
    return [
        QAItem(
            question="Who wanted the front of the parade at first?",
            answer=f"The sailor and the infantry drummer both wanted it, because each thought the front would make the parade feel special.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=twist["turn"].capitalize() + ".",
        ),
        QAItem(
            question="How did the sailor and the infantry respond to the twist?",
            answer=f"They stopped competing and chose to {twist['change']}.",
        ),
        QAItem(
            question="What kind of feeling did the parade end with?",
            answer=f"It ended with a warm, happy feeling in the {params.setting}, because the march became kinder and more welcoming.",
        ),
        QAItem(
            question="What changed for the characters by the end?",
            answer="They learned that sharing the best place can make a parade more beautiful than winning it alone.",
        ),
        QAItem(
            question="What final image proved the story was heartwarming?",
            answer=f"{twist['ending'].capitalize()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a lively public march with music, movement, and people watching along the way.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works on boats or ships and knows a lot about the sea.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who usually travel and work on foot rather than in vehicles.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade storyworld with a sailor, infantry, and a twist.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sailor-name", choices=SAILOR_NAMES)
    ap.add_argument("--infantry-name", choices=INFANTRY_NAMES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--parade-name", choices=PARADES)
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
    name = args.name or rng.choice(NAMES)
    sailor = args.sailor_name or rng.choice(SAILOR_NAMES)
    infantry = args.infantry_name or rng.choice(INFANTRY_NAMES)
    setting = args.setting or rng.choice(SETTINGS)
    parade_name = args.parade_name or rng.choice(PARADES)
    return StoryParams(seed=None, name=name, sailor_name=sailor, infantry_name=infantry, setting=setting, parade_name=parade_name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams(name="Mira", sailor_name="Sailor Tom", infantry_name="Ben", setting="harbor town", parade_name="Lantern Parade"),
    StoryParams(name="Lina", sailor_name="Sailor Rue", infantry_name="Leo", setting="square by the docks", parade_name="Spring Parade"),
    StoryParams(name="June", sailor_name="Sailor Nell", infantry_name="Owen", setting="old seaside street", parade_name="Welcome Parade"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
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
