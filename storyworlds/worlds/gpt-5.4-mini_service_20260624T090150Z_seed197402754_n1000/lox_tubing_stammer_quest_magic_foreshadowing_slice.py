#!/usr/bin/env python3
"""
A small slice-of-life story world about a child, a foreshadowed little quest,
a stubborn stammer, and a tiny bit of everyday magic.

The seed words are used as the core domain pieces:
- lox: the snack prize the child wants to share
- tubing: a craft-material / helper tool used to carry water for plants
- stammer: the child's nervous speech pattern that matters in the story

The story structure stays grounded in home life: a morning errand becomes a
gentle quest, a magical trick helps, and a foreshadowing detail pays off at the
end.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class World:
    place: str
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
# Content registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    quest: str
    magic: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mina", "Nora", "Tia", "Lina", "Zoe"],
    "boy": ["Owen", "Milo", "Theo", "Ben", "Jude"],
}
TRAITS = ["curious", "gentle", "patient", "thoughtful", "bright"]


@dataclass
class QuestPlan:
    label: str
    goal: str
    errand: str
    ending_image: str
    foreshadow: str
    payoff: str


@dataclass
class MagicTool:
    label: str
    action: str
    effect: str
    limitation: str


PLACES = {
    "kitchen": "the kitchen",
    "garden": "the little garden",
    "porch": "the porch",
    "sunroom": "the sunroom",
}

QUESTS = {
    "morning snack": QuestPlan(
        label="morning snack",
        goal="make breakfast for the family",
        errand="carry the lox plate carefully to the table",
        ending_image="the lox sat safe on the table beside warm toast",
        foreshadow="a tiny wobble in the plate made everyone slow down and watch it",
        payoff="the careful hands that first steadied the plate now helped steady the whole breakfast",
    ),
    "watering plants": QuestPlan(
        label="watering plants",
        goal="give the thirsty plants a drink",
        errand="guide the water through the tubing to the flower pots",
        ending_image="the tubing lay neatly beside the damp pots and bright leaves",
        foreshadow="a drip under the hose made the child notice where the water wanted to go",
        payoff="that early drip helped them aim the tubing the right way later",
    ),
    "quiet surprise": QuestPlan(
        label="quiet surprise",
        goal="set up a tiny surprise for a parent",
        errand="hide the note near the lox basket and wait",
        ending_image="the note and lox basket waited together like a little secret",
        foreshadow="the child almost stammered a clue, then pressed lips together and smiled",
        payoff="the almost-spoken clue turned into a happy reveal at the end",
    ),
}

MAGICS = {
    "glow sticker": MagicTool(
        label="a glow sticker",
        action="shine softly in the dim room",
        effect="made the child feel braver and steadier",
        limitation="it only glowed when someone took a slow breath first",
    ),
    "tuning spoon": MagicTool(
        label="a tuning spoon",
        action="give a tiny friendly hum",
        effect="helped words come out one at a time",
        limitation="it worked best when held with both hands",
    ),
    "blue ribbon": MagicTool(
        label="a blue ribbon",
        action="flash like a little reminder",
        effect="helped the child remember the plan",
        limitation="it could not do the job alone; it only pointed the way",
    ),
}

# ASP compatibility: a world is valid if the quest can plausibly use the magic.
QUEST_MAGIC_SUPPORT = {
    "morning snack": {"glow sticker", "tuning spoon"},
    "watering plants": {"blue ribbon", "glow sticker"},
    "quiet surprise": {"blue ribbon", "tuning spoon"},
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_magic_ok(Q, M) :- quest(Q), magic(M), supports(Q, M).
valid_story(P, Q, M) :- place(P), quest_magic_ok(Q, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
        for m in sorted(QUEST_MAGIC_SUPPORT[q]):
            lines.append(asp.fact("supports", q, m))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_triples() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_triples())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for quest in QUESTS:
            for magic in MAGICS:
                if magic in QUEST_MAGIC_SUPPORT[quest]:
                    combos.append((place, quest, magic))
    return combos


def explain_rejection(quest: str, magic: str) -> str:
    return (
        f"(No story: {magic} does not fit the little quest '{quest}'. "
        f"Choose a magic tool that supports that quest.)"
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.gender,
        label=params.name,
        phrase=f"little {params.gender} {params.name}",
        meters={"calm": 1.0},
        memes={"hope": 1.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        phrase=f"the {params.parent}",
        meters={"care": 1.0},
        memes={"watchful": 1.0},
    ))
    quest = QUESTS[params.quest]
    magic = MAGICS[params.magic]

    lox = world.add(Entity(
        id="lox",
        kind="thing",
        label="lox",
        phrase="a small plate of lox",
        owner=hero.id,
    ))
    tubing = world.add(Entity(
        id="tubing",
        kind="thing",
        label="tubing",
        phrase="a coil of tubing",
        owner=parent.id,
    ))
    charm = world.add(Entity(
        id="magic",
        kind="thing",
        label=magic.label,
        phrase=magic.label,
        owner=parent.id,
    ))

    world.facts.update(
        hero=hero, parent=parent, quest=quest, magic=magic, lox=lox, tubing=tubing, charm=charm
    )
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    quest: QuestPlan = f["quest"]
    magic: MagicTool = f["magic"]
    lox: Entity = f["lox"]
    tubing: Entity = f["tubing"]

    trait = random.choice(TRAITS)
    world.say(f"{hero.label} was a {trait} child who liked small jobs that felt like quests.")
    world.say(
        f"One morning, {hero.label} had a {quest.label} to do: {quest.goal}. "
        f"On the counter sat {lox.phrase}, and beside the sink lay {tubing.phrase}."
    )
    world.say(
        f"{world.place.capitalize()} was quiet and warm, and {quest.foreshadow}."
    )

    world.para()
    hero.memes["desire"] += 1.0
    world.say(
        f"{hero.label} wanted to start at once, but {hero.pronoun('possessive')} words "
        f"came in a nervous stammer when the task felt big."
    )
    world.say(
        f"{parent.label_word if hasattr(parent, 'label_word') else parent.label} "
        f"did not rush {hero.pronoun('object')}; instead, the {params.parent} held up "
        f"{magic.label} and said, '{magic.action.capitalize()}.'"
    )
    world.say(
        f"That small bit of magic {magic.effect}, though {magic.limitation}."
    )

    world.para()
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.say(
        f"{hero.label} took a slow breath, and the stammer softened into one careful sentence. "
        f"Together, they used {tubing.label} for {quest.errand}."
    )
    world.say(
        f"The {quest.foreshadow.lower()}, and that made the next step feel easier."
    )
    world.say(
        f"At last, {hero.label} finished the quest, and {quest.payoff}. "
        f"The day stayed simple and kind, like a good morning should."
    )

    world.para()
    world.say(
        f"By the end, {quest.ending_image}, and {hero.label} smiled because the little quest was done."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: QuestPlan = f["quest"]
    magic: MagicTool = f["magic"]
    return [
        f"Write a slice-of-life story about {hero.label}, a small {quest.label} quest, and {magic.label}.",
        f"Tell a gentle story where a child with a stammer learns to finish a {quest.label} with a little magic.",
        f"Write a morning story that includes lox, tubing, foreshadowing, and a happy finish.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    quest: QuestPlan = f["quest"]
    magic: MagicTool = f["magic"]
    return [
        QAItem(
            question=f"What was {hero.label} trying to do in the story?",
            answer=f"{hero.label} was trying to finish a {quest.label} quest and {quest.goal}.",
        ),
        QAItem(
            question=f"Why did {hero.label} use {magic.label}?",
            answer=(
                f"{hero.label} used {magic.label} because the task felt big and the stammer made "
                f"words come out slowly. The little magic helped {hero.pronoun('object')} feel braver."
            ),
        ),
        QAItem(
            question=f"What was the foreshadowing clue in the story?",
            answer=f"The clue was that {quest.foreshadow.lower()}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {quest.ending_image}, after {hero.label} finished the quest.",
        ),
        QAItem(
            question=f"Where were the lox and tubing in the story?",
            answer=(
                f"The lox was on the counter, and the tubing was near the sink before it helped with "
                f"the quest."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    quest: QuestPlan = f["quest"]
    magic: MagicTool = f["magic"]
    return [
        QAItem(
            question="What is lox?",
            answer="Lox is thin, salty salmon that people often eat with bread or bagels.",
        ),
        QAItem(
            question="What is tubing?",
            answer="Tubing is a hollow tube or hose that can carry air or water from one place to another.",
        ),
        QAItem(
            question="What is a stammer?",
            answer="A stammer is when a person has trouble getting words out smoothly and may repeat sounds.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints at something important later.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or job that someone tries to finish, usually with care and purpose.",
        ),
        QAItem(
            question="What does magic mean in a story like this?",
            answer="Magic in a story is something special that helps or changes things in a surprising way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life quest storyworld with lox, tubing, stammer, magic, and foreshadowing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.quest and args.magic and args.magic not in QUEST_MAGIC_SUPPORT[args.quest]:
        raise StoryError(explain_rejection(args.quest, args.magic))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.magic is None or c[2] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, quest, magic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        name=name,
        gender=gender,
        parent=parent,
        place=place,
        quest=quest,
        magic=magic,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(name="Mina", gender="girl", parent="mother", place="kitchen", quest="morning snack", magic="glow sticker"),
    StoryParams(name="Owen", gender="boy", parent="father", place="garden", quest="watering plants", magic="blue ribbon"),
    StoryParams(name="Tia", gender="girl", parent="mother", place="porch", quest="quiet surprise", magic="tuning spoon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_triples()
        print(f"{len(triples)} compatible (place, quest, magic) combos:\n")
        for p, q, m in triples:
            print(f"  {p:9} {q:16} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.quest} at {p.place} (magic: {p.magic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
