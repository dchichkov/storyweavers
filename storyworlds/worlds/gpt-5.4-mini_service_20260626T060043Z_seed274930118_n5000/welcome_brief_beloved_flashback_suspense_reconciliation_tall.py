#!/usr/bin/env python3
"""
A tall-tale storyworld about a welcome, a brief misunderstanding, a beloved
object, a flashback, suspense, and reconciliation.
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

WELCOME_WORDS = ("welcome", "brief", "beloved")


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    neighbor_name: str
    beloved: str
    seed: Optional[int] = None


SETTINGS = {
    "ridge": "the windy ridge",
    "harbor": "the little harbor",
    "prairie": "the golden prairie",
    "crossroads": "the dusty crossroads",
}

HERO_TYPES = {
    "boy": "boy",
    "girl": "girl",
    "man": "man",
    "woman": "woman",
}

BELOVEDS = {
    "lantern": ("lantern", "a beloved brass lantern"),
    "dog": ("dog", "a beloved hound dog"),
    "wagon": ("wagon", "a beloved red wagon"),
    "piano": ("piano", "a beloved little piano"),
    "hat": ("hat", "a beloved felt hat"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with welcome, brief, beloved, flashback, suspense, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--beloved", choices=BELOVEDS)
    ap.add_argument("--name")
    ap.add_argument("--neighbor")
    ap.add_argument("--gender", choices=["girl", "boy", "woman", "man"])
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
    place = args.place or rng.choice(list(SETTINGS))
    beloved = args.beloved or rng.choice(list(BELOVEDS))
    hero_type = args.gender or rng.choice(list(HERO_TYPES))
    hero_name = args.name or rng.choice(["Mabel", "Clara", "Hank", "Otis", "June", "Nell", "Bo", "Ira"])
    neighbor = args.neighbor or rng.choice(["Milo", "Della", "Ruth", "Ezra", "Pearl", "Silas"])
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, neighbor_name=neighbor, beloved=beloved)


def _hero_phrase(p: StoryParams) -> str:
    return f"{p.hero_name}, the {p.hero_type}"


def _beloved_phrase(p: StoryParams) -> str:
    return BELOVEDS[p.beloved][1]


def tell(params: StoryParams) -> World:
    world = World(place=SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    neighbor = world.add(Entity(id="neighbor", kind="character", type="person", label=params.neighbor_name))
    item = world.add(Entity(
        id="beloved",
        kind="thing",
        type=params.beloved,
        label=BELOVEDS[params.beloved][0],
        phrase=_beloved_phrase(params),
        owner=hero.id,
        caretaker=hero.id,
    ))
    item.meters["pride"] = 1.0
    hero.memes["love"] = 1.0
    hero.memes["welcome"] = 1.0

    # Act 1: welcome and setup
    world.say(
        f"On {world.place}, {params.hero_name} was as sturdy as a fence post and as kind as sunrise."
    )
    world.say(
        f"The whole hill knew {params.hero_name} for a welcome word, a brief grin, and a heart that held {item.phrase} dear."
    )
    world.say(
        f"Every evening, {params.hero_name} carried {item.pronoun('possessive')} {item.label} like a treasure from a king's attic."
    )

    # Flashback
    world.para()
    hero.memes["flashback"] = 1.0
    world.say(
        f"Now, a flashback blew through {world.place} like a trumpet blast."
    )
    world.say(
        f"Long before this day, {params.hero_name} had found the {item.label} beneath an old cottonwood, dust-covered and lonely."
    )
    world.say(
        f"{params.hero_name} had whispered, 'Well now, you are mine to mend and love,' and ever since, the {item.label} had been beloved."
    )

    # Suspense: brief disappearance
    world.para()
    hero.memes["suspense"] = 1.0
    item.meters["missing"] = 1.0
    world.say(
        f"But one brief blink before supper, a gust of prairie wind snatched the {item.label} from the porch rail."
    )
    world.say(
        f"{params.hero_name} stared at the empty spot and felt the air grow tight as a fiddle string."
    )
    world.say(
        f"Even {params.neighbor_name}, who was no stranger to rough weather, looked around as if the clouds themselves were hiding something."
    )

    # Search and tension
    world.para()
    hero.memes["worry"] = 1.0
    world.say(
        f"{params.hero_name} searched by the fence, then the well, then the barn, calling, 'Beloved {item.label}, come on home!'"
    )
    world.say(
        f"The wind answered with a whistle, and for a spell it seemed the night might keep the {item.label} forever."
    )

    # Reconciliation
    world.para()
    hero.memes["relief"] = 1.0
    neighbor.memes["guilt"] = 1.0
    item.meters["missing"] = 0.0
    item.carried_by = hero.id
    neighbor.memes["reconciliation"] = 1.0
    world.say(
        f"Then {params.neighbor_name} came running from behind the feed shed, holding the {item.label} with both hands and a sheepish smile."
    )
    world.say(
        f"'{params.hero_name}, I meant to help, not borrow,' {params.neighbor_name} said. 'I'm sorry for the scare.'"
    )
    world.say(
        f"{params.hero_name} laughed, took back {item.phrase}, and said, 'You're welcome at my door any time, as long as you tell me first.'"
    )
    world.say(
        f"So the two friends mended their fuss under a sky as wide as a wagon road, and the {item.label} shone brighter for being found."
    )

    world.facts.update(hero=hero, neighbor=neighbor, item=item, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a tall-tale story about a welcome, a brief scare, and a beloved {p.beloved}.",
        f"Tell a child-friendly story set at {SETTINGS[p.place]} where {p.hero_name} loses and finds a cherished object.",
        f"Write a short story with a flashback, suspense, and reconciliation on {SETTINGS[p.place]}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    item: Entity = world.facts["item"]
    hero: Entity = world.facts["hero"]
    neighbor: Entity = world.facts["neighbor"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {p.hero_name}, who lives near {SETTINGS[p.place]} and loves {item.phrase}.",
        ),
        QAItem(
            question=f"What happened in the flashback?",
            answer=f"In the flashback, {p.hero_name} found {item.phrase} under an old cottonwood and decided to care for it.",
        ),
        QAItem(
            question=f"Why was there suspense in the middle?",
            answer=f"There was suspense because a brief gust of wind made the beloved {item.label} disappear from the porch.",
        ),
        QAItem(
            question=f"How was the problem resolved?",
            answer=f"{p.neighbor_name} brought the {item.label} back, apologized, and {p.hero_name} welcomed the neighbor's honesty, so the friends reconciled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something that happened earlier than the main action.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of worry or excitement about what might happen next.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for x in sample.prompts:
        lines.append(x)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} carried_by={e.carried_by}")
    return "\n".join(out)


ASP_RULES = r"""
hero(hero).
neighbor(neighbor).
beloved(item).
flashback(shown) :- hero(hero), beloved(item).
suspense(shown) :- beloved(item), missing(item).
reconciliation(shown) :- neighbor(neighbor), returned(item).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "welcome_place"),
    ]
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in BELOVEDS:
        lines.append(asp.fact("beloved_kind", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show flashback/1.\n#show suspense/1.\n#show reconciliation/1."))
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    expected = {("flashback", 1), ("suspense", 1), ("reconciliation", 1)}
    if atoms == expected:
        print("OK: ASP twin contains flashback, suspense, and reconciliation.")
        return 0
    print("MISMATCH: ASP twin did not yield expected atoms.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="ridge", hero_name="Mabel", hero_type="woman", neighbor_name="Silas", beloved="lantern"),
    StoryParams(place="harbor", hero_name="Bo", hero_type="boy", neighbor_name="Pearl", beloved="dog"),
    StoryParams(place="prairie", hero_name="June", hero_type="girl", neighbor_name="Ezra", beloved="wagon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show flashback/1.\n#show suspense/1.\n#show reconciliation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show flashback/1.\n#show suspense/1.\n#show reconciliation/1."))
        print(sorted((sym.name, len(sym.arguments)) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
