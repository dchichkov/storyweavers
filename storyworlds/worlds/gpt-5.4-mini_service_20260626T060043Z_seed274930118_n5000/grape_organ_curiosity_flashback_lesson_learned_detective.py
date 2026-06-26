#!/usr/bin/env python3
"""
Standalone storyworld: a small detective story about Curiosity, a Flashback,
and a Lesson Learned.

Premise:
- A curious child detective notices a missing grape in a music room.
- The room has an organ, and the sound of the organ triggers a flashback.
- The child follows clues, learns what happened, and ends with a clear lesson.

This world is intentionally tiny and constraint-checked:
- The grape must be plausibly misplaced or missing.
- The organ must matter to the investigation.
- Curiosity drives the search, Flashback reveals hidden context, and Lesson
  Learned resolves the mystery in a child-friendly way.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True


@dataclass
class Scene:
    grape_place: str
    clue_place: str
    flashback_trigger: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "music_room": Setting(place="the music room", indoor=True),
    "school_hall": Setting(place="the school hall", indoor=True),
    "grand_room": Setting(place="the grand room", indoor=True),
}

NAMES_GIRL = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
NAMES_BOY = ["Leo", "Finn", "Ben", "Theo", "Max"]


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


def choose_scene(setting_key: str) -> Scene:
    if setting_key == "music_room":
        return Scene(
            grape_place="on the piano bench",
            clue_place="under the organ keys",
            flashback_trigger="the deep organ note",
            lesson="look carefully before jumping to conclusions",
        )
    if setting_key == "school_hall":
        return Scene(
            grape_place="near the snack shelf",
            clue_place="by the organ cart",
            flashback_trigger="the organ's echo",
            lesson="ask questions and follow each clue patiently",
        )
    if setting_key == "grand_room":
        return Scene(
            grape_place="behind the velvet curtain",
            clue_place="beside the organ pedals",
            flashback_trigger="the organ's humming chord",
            lesson="kindness matters when someone makes a mistake",
        )
    raise StoryError("unknown setting")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with Curiosity, Flashback, and Lesson Learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, name=name, gender=gender, parent=parent)


def narrate_flashback(world: World, hero: Entity, scene: Scene) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} was a curious little detective who loved solving small mysteries."
    )
    world.say(
        f"One quiet day, {hero.id} walked into {world.setting.place} and noticed something odd: "
        f"a red grape was missing from the snack plate."
    )
    world.say(
        f"Near the organ, {hero.id} heard {scene.flashback_trigger}, and suddenly a flashback popped into {hero.pronoun('possessive')} mind."
    )
    world.say(
        f"In the flashback, {hero.id} remembered seeing a helper carry snacks while the organ music began."
    )


def solve_mystery(world: World, hero: Entity, parent: Entity, scene: Scene) -> None:
    grape = world.add(Entity(id="grape", type="grape", label="grape"))
    organ = world.add(Entity(id="organ", type="organ", label="organ"))
    world.facts.update(hero=hero, parent=parent, grape=grape, organ=organ, scene=scene)

    world.say(
        f"{hero.id} followed the clue to {scene.clue_place} and found a little grape skin, which proved the snack had been moved, not lost."
    )
    world.say(
        f"Then {hero.id} looked behind {scene.grape_place} and saw the grape tucked safely away where it had rolled after the room filled with music."
    )
    world.say(
        f"{hero.id} smiled and told {hero.pronoun('possessive')} {parent.type} that the mystery was solved."
    )
    world.say(
        f"The lesson learned was simple: {scene.lesson}."
    )
    world.say(
        f"At the end, the grape was back on the snack plate, the organ stood quietly in the corner, and {hero.id} felt proud of {hero.pronoun('possessive')} careful thinking."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    scene = choose_scene(params.setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    narrate_flashback(world, hero, scene)
    world.para()
    solve_mystery(world, hero, parent, scene)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    scene = f["scene"]
    return [
        f"Write a short detective story for a child about {hero.id} finding a missing grape in {world.setting.place}.",
        f"Tell a gentle mystery story where an organ sound causes a flashback and helps {hero.id} solve the case.",
        f"Write a story with Curiosity, Flashback, and Lesson Learned set in {world.setting.place}, using a grape and an organ.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    scene = f["scene"]
    return [
        QAItem(
            question=f"Why did {hero.id} start investigating in {world.setting.place}?",
            answer=f"{hero.id} was curious and noticed that a grape was missing, so {hero.pronoun()} began to investigate like a little detective.",
        ),
        QAItem(
            question="What caused the flashback in the story?",
            answer=f"The flashback started when {hero.id} heard {scene.flashback_trigger} near the organ.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned to {scene.lesson}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} feel sure the mystery was solved?",
            answer=f"{hero.id}'s {parent.type} stayed nearby, and that helped {hero.id} feel calm and proud after solving the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grape?",
            answer="A grape is a small round fruit that people can eat as a snack.",
        ),
        QAItem(
            question="What is an organ?",
            answer="An organ is a large musical instrument that makes deep sounds when someone plays its keys and pedals.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and tries to solve a mystery.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind:9}) type={e.type}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- character(X).
mystery_started :- curiosity(X), grape_missing.
flashback :- hears_organ(X), mystery_started.
lesson_learned :- flashback, clue_found.
#show mystery_started/0.
#show flashback/0.
#show lesson_learned/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("character", "hero"),
        asp.fact("grape_missing"),
        asp.fact("hears_organ", "hero"),
        asp.fact("curiosity", "hero"),
        asp.fact("clue_found"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show mystery_started/0.\n#show flashback/0.\n#show lesson_learned/0."))
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    expected = {("mystery_started", 0), ("flashback", 0), ("lesson_learned", 0)}
    if atoms == expected:
        print("OK: ASP rules fire as expected.")
        return 0
    print("MISMATCH: ASP rules did not produce expected atoms.")
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"PROMPT {i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_started/0.\n#show flashback/0.\n#show lesson_learned/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="music_room", name="Mia", gender="girl", parent="mother"),
            StoryParams(setting="school_hall", name="Leo", gender="boy", parent="father"),
            StoryParams(setting="grand_room", name="Nora", gender="girl", parent="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
