#!/usr/bin/env python3
"""
A small mystery-style storyworld about a child, a harbor boll, and the Atlantic.

The seed image is a cautionary little mystery:
a curious child wanders near an Atlantic pier, notices something odd about a
boll, follows clues, learns a lesson about safety near water, and ends with a
happy resolution.
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

STORY_STYLE = "Mystery"
FEATURES = ("Cautionary", "Lesson Learned", "Happy Ending")

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the Atlantic pier"
    indoor: bool = False
    water_nearby: bool = True


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    seed: Optional[int] = None


NAMES_GIRL = ["Mia", "Nora", "Lena", "Tia", "June", "Maya"]
NAMES_BOY = ["Eli", "Noah", "Theo", "Finn", "Max", "Owen"]


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------


SETTING = Setting(place="the Atlantic pier", indoor=False, water_nearby=True)

THINGS = {
    "boll": {
        "label": "boll",
        "phrase": "a heavy harbor boll",
        "type": "boll",
    },
    "lantern": {
        "label": "lantern",
        "phrase": "a small brass lantern",
        "type": "lantern",
    },
}

CLUES = [
    "a scrape of salt on the iron",
    "a little wet ribbon snagged on the boll",
    "footprints in the damp boards",
    "a note tucked under the lantern",
]

WORLD_KNOWLEDGE = {
    "boll": [
        QAItem(
            question="What is a boll at a harbor?",
            answer="A boll is a strong metal post near the water. Boats can tie ropes to it so they stay in place.",
        )
    ],
    "atlantic": [
        QAItem(
            question="What is the Atlantic?",
            answer="The Atlantic is a very big ocean. It has waves, salt water, and ships traveling across it.",
        )
    ],
    "mystery": [
        QAItem(
            question="What makes a story feel like a mystery?",
            answer="A mystery story has a puzzling problem, a few clues, and someone who tries to figure out what happened.",
        )
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def introduce(world: World, child: Entity, parent: Entity, thing: Entity) -> None:
    world.say(
        f"{child.id} was a curious little {child.type} who loved the Atlantic pier "
        f"because the wind smelled like salt and secrets."
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {parent.label} had told {child.pronoun('object')} "
        f"to stay away from the water, but {child.id} always noticed interesting things first."
    )
    world.say(
        f"One evening, {child.id} spotted {thing.phrase} standing near the edge like it was guarding a clue."
    )


def build_clue_chain(world: World, child: Entity, thing: Entity) -> None:
    world.para()
    world.say(
        f"{child.id} looked closer and found {random.choice(CLUES)}."
    )
    world.say(
        f"That made the {thing.label} seem less ordinary, and {child.id} wondered who had left the signs behind."
    )
    world.say(
        f"Near the pier, the waves kept tapping the wood as if they wanted to join the secret."
    )


def caution(world: World, child: Entity, parent: Entity, thing: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["unease"] = child.memes.get("unease", 0) + 1
    world.para()
    world.say(
        f"{child.id} leaned too close, and {child.pronoun('possessive')} {parent.label} stepped in at once."
    )
    world.say(
        f"\"Don't climb on the {thing.label},\" {parent.id} said. \"The boards are slick, and the Atlantic water is not a game.\""
    )
    world.say(
        f"{child.id} froze, because the warning sounded serious and true."
    )


def solve_mystery(world: World, child: Entity, parent: Entity, thing: Entity) -> None:
    world.para()
    world.say(
        f"{child.id} noticed the wet ribbon again and followed it to a dropped glove near the lantern."
    )
    world.say(
        f"Then {child.id} realized the clue trail was not a trap at all; it was how the harbor worker had marked where the rope should go."
    )
    world.say(
        f"{child.id} called for {parent.id}, and together they found the worker looking everywhere for the missing knot."
    )
    world.say(
        f"The worker thanked them and tied the rope safely around the {thing.label}, so the little puzzle was solved."
    )


def lesson_and_happy_ending(world: World, child: Entity, parent: Entity, thing: Entity) -> None:
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    child.memes["relief"] = child.memes.get("relief", 0) + 2
    child.memes["lesson"] = child.memes.get("lesson", 0) + 1
    world.para()
    world.say(
        f"{child.id} smiled and promised to keep a safer distance from the water next time."
    )
    world.say(
        f"{parent.id} hugged {child.pronoun('object')} and said that careful eyes and patient feet made the best kind of detective."
    )
    world.say(
        f"By the end of the evening, the {thing.label} stood secure, the Atlantic breeze felt gentle, and {child.id} walked home proud of the lesson learned."
    )


def tell_story(params: StoryParams) -> World:
    world = World(setting=SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    thing = world.add(Entity(id="Boll", type="boll", label="boll", phrase="a heavy harbor boll"))

    world.facts.update(child=child, parent=parent, thing=thing, place=params.place)
    introduce(world, child, parent, thing)
    build_clue_chain(world, child, thing)
    caution(world, child, parent, thing)
    solve_mystery(world, child, parent, thing)
    lesson_and_happy_ending(world, child, parent, thing)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Prompt/QA
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f"Write a short mystery story for a young child named {child.id} at the Atlantic pier.",
        f"Tell a cautionary tale where {child.id} notices a boll, learns a lesson, and ends happy.",
        f"Write a gentle mystery with the words boll and Atlantic, ending with a safe choice and a warm feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, thing = f["child"], f["parent"], f["thing"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, a curious child who visits the Atlantic pier with {parent.label}.",
        ),
        QAItem(
            question=f"What puzzling thing did {child.id} notice near the water?",
            answer=f"{child.id} noticed a heavy harbor boll standing near the edge like it was part of a mystery.",
        ),
        QAItem(
            question=f"What warning did {parent.id} give?",
            answer=f"{parent.id} warned {child.id} not to climb on the {thing.label} because the boards were slick and the Atlantic water was dangerous.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{child.id} followed the clues, found the missing rope mark, and helped the worker secure the {thing.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {child.id} learning to stay safer near the water and walking home proud of the lesson learned.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["boll"])
    out.extend(WORLD_KNOWLEDGE["atlantic"])
    out.extend(WORLD_KNOWLEDGE["mystery"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_story(C) :- child(C).
has_boll_mystery(B) :- thing(B), boll(B).
near_atlantic(P) :- place(P), atlantic(P).
cautionary_story(C) :- child_story(C), has_boll_mystery(_), near_atlantic(_).
lesson_learned(C) :- cautionary_story(C).
happy_ending(C) :- lesson_learned(C).

#show cautionary_story/1.
#show lesson_learned/1.
#show happy_ending/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("child", "hero"),
        asp.fact("thing", "boll1"),
        asp.fact("boll", "boll1"),
        asp.fact("place", "atlantic_pier"),
        asp.fact("atlantic", "atlantic_pier"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show cautionary_story/1. #show lesson_learned/1. #show happy_ending/1."))
    atoms = {(sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model}
    expected = {
        ("cautionary_story", ("hero",)),
        ("lesson_learned", ("hero",)),
        ("happy_ending", ("hero",)),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python story shape.")
        return 0
    print("MISMATCH between ASP and Python story shape.")
    print("ASP:", sorted(atoms))
    print("Expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld: boll, Atlantic, caution, lesson, happy ending.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--place", default="the Atlantic pier")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    place = args.place or "the Atlantic pier"
    if "atlantic" not in place.lower():
        raise StoryError("This world must stay near the Atlantic.")
    return StoryParams(name=name, gender=gender, parent=parent, place=place)


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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} kind={e.kind} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
        print(asp_program("#show cautionary_story/1. #show lesson_learned/1. #show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show cautionary_story/1. #show lesson_learned/1. #show happy_ending/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(name="Mia", gender="girl", parent="mother", place="the Atlantic pier"),
            StoryParams(name="Eli", gender="boy", parent="father", place="the Atlantic pier"),
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
