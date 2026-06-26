#!/usr/bin/env python3
"""
A tiny nursery-rhyme story world about a child on a Quest, a yellow spell of
jaundice, a ripe fig, and a diary that helps set things right.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "child"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    name: str
    gender: str
    quest: str
    treasure: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

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


QUESTS = {
    "nursery": {
        "name": "the nursery lane quest",
        "place": "the nursery lane",
        "turn": "the yellow hush",
    }
}

TREASURES = {
    "fig": {
        "label": "fig",
        "phrase": "a sweet purple fig",
        "kind": "fruit",
    },
    "diary": {
        "label": "diary",
        "phrase": "a little paper diary with a blue ribbon",
        "kind": "book",
    },
    "star": {
        "label": "star",
        "phrase": "a shiny paper star",
        "kind": "token",
    },
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandma": "grandma",
}


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def narrate_nursery(world: World, hero: Entity, helper: Entity, quest: str, treasure: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who trod to the lane in morning light, "
        f"with a Quest to find {treasure.phrase} and make the day feel right."
    )
    world.say(
        f"'{hero.id},' said {helper.label}, 'mind the quest and keep your cheer; "
        f"for a yellow spell called jaundice has made {hero.pronoun('possessive')} face seem queer.'"
    )


def apply_jaundice(world: World, hero: Entity) -> None:
    hero.meters["jaundice"] = hero.meters.get("jaundice", 0.0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.fired.add(("jaundice", hero.id))
    world.trace.append(f"{hero.id} grows pale-yellow with worry.")


def helper_warns(world: World, helper: Entity, hero: Entity, treasure: Entity) -> None:
    world.say(
        f"The {helper.label} peered in the diary and saw the Quest would sway, "
        f"if {hero.id} ignored the rest and hurried on their way."
    )
    world.say(
        f"'A fig can stain a palm,' said {helper.label}, 'and a tired child can cry; "
        f"so we must walk, and write, and wait, and let the brave bird fly.'"
    )


def quest_turn(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.say(
        f"So {hero.id} held the diary close and sat beneath the tree, "
        f"while {helper.label} fetched a ripe fig and read the plan with glee."
    )
    world.say(
        f"The pages said, 'When jaws are soft and hearts are calm, the Quest goes sweet; "
        f"one small fig, one written line, and little feet meet little feet.'"
    )
    treasure.meters["found"] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0


def resolve(world: World, hero: Entity, helper: Entity, treasure: Entity) -> None:
    hero.meters["jaundice"] = 0.0
    hero.memes["worry"] = 0.0
    world.say(
        f"Then {hero.id} nibbled the fig, and wrote a note in the diary, neat and clear; "
        f"the yellow spell grew soft and light, and all the sky seemed near."
    )
    world.say(
        f"{helper.label} smiled to see {hero.id} laugh again and skip along the green; "
        f"for the Quest was done, the diary shone, and the fig-stain was not seen."
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"jaundice": 0.0},
        memes={"worry": 0.0, "hope": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper if params.helper in {"mother", "father", "grandma"} else "adult",
        label=params.helper,
    ))
    treasure_cfg = TREASURES[params.treasure]
    treasure = world.add(Entity(
        id=params.treasure,
        type=treasure_cfg["kind"],
        label=treasure_cfg["label"],
        phrase=treasure_cfg["phrase"],
        meters={"found": 0.0},
    ))
    world.facts.update(hero=hero, helper=helper, treasure=treasure, params=params, quest=params.quest)

    narrate_nursery(world, hero, helper, params.quest, treasure)
    world.para()
    helper_warns(world, helper, hero, treasure)
    apply_jaundice(world, hero)
    world.say(
        f"{hero.id} felt quite weary, with a tummy like a drum; "
        f"but the diary stayed tucked safe, and the Quest was not yet done."
    )
    world.para()
    quest_turn(world, hero, helper, treasure)
    resolve(world, hero, helper, treasure)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short nursery-rhyme story about {p.name} on a Quest with jaundice, a fig, and a diary.",
        f"Tell a gentle rhyme where a child named {p.name} uses a diary to finish a Quest after feeling yellow and tired.",
        f"Create a child-facing story with the words jaundice, fig, and diary, ending in a happy little rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    treasure: Entity = f["treasure"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do on the nursery lane?",
            answer=f"{hero.id} was on a Quest to find {treasure.phrase}.",
        ),
        QAItem(
            question=f"Why did {helper.label} worry about {hero.id} at first?",
            answer=f"{helper.label} worried because {hero.id} had jaundice and looked yellow and weary.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel better and finish the Quest?",
            answer=f"A sweet fig and the little diary helped {hero.id} calm down and finish the Quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is jaundice?",
            answer="Jaundice is when a person or pet can look yellow because their body needs help.",
        ),
        QAItem(
            question="What is a fig?",
            answer="A fig is a soft, sweet fruit with tiny seeds inside.",
        ),
        QAItem(
            question="What is a diary for?",
            answer="A diary is a small book where someone can write thoughts, plans, or little stories.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special journey to look for something or do an important task.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.extend(world.trace)
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("quest", "nursery"),
        asp.fact("treasure", "fig"),
        asp.fact("treasure", "diary"),
        asp.fact("symptom", "jaundice"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
quest_story(nursery,fig,diary,jaundice).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show quest_story/4."))
    atoms = set(asp.atoms(model, "quest_story"))
    expected = {("nursery", "fig", "diary", "jaundice")}
    if atoms == expected:
        print("OK: ASP and Python agree.")
        return 0
    print(f"Mismatch: {sorted(atoms)} vs {sorted(expected)}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme Quest about jaundice, a fig, and a diary.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--quest", choices=["nursery"], default=None)
    ap.add_argument("--treasure", choices=list(TREASURES), default=None)
    ap.add_argument("--helper", choices=list(HELPERS), default=None)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


NAMES = {
    "girl": ["Mina", "Lily", "Rose", "Nina"],
    "boy": ["Tom", "Milo", "Ben", "Pip"],
}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(
        name=args.name or rng.choice(NAMES[gender]),
        gender=gender,
        quest=args.quest or "nursery",
        treasure=args.treasure or rng.choice(["fig", "diary"]),
        helper=args.helper or rng.choice(list(HELPERS)),
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_story/4."))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show quest_story/4."))
        print(asp.atoms(model, "quest_story"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(name="Mina", gender="girl", quest="nursery", treasure="fig", helper="mother"),
            StoryParams(name="Tom", gender="boy", quest="nursery", treasure="diary", helper="grandma"),
        ]
        samples = [generate(p) for p in combos]
    else:
        for _ in range(args.n):
            p = resolve_params(args, rng)
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
