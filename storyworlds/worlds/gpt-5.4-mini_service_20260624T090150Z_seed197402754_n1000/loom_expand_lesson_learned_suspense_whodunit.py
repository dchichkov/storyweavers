#!/usr/bin/env python3
"""
Storyworld: Loom Expand Lesson Learned Suspense Whodunit
========================================================

A small simulated whodunit-style story world about a child, a loom,
a mysterious missing piece, and a safe way to solve the tangle.

Seed tale concept:
- A child loves weaving at a loom.
- Something small goes missing: a shuttle, a ribbon, or a pattern card.
- The room becomes suspenseful because the clues are inside the workshop.
- The mystery expands as more evidence appears.
- The child learns a lesson about careful work, and the ending proves the change.

This world keeps the prose concrete and state-driven rather than relying on a
frozen template. The same simulated facts drive the story and the QA.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
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
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the weaving room"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    clue: str
    weather: str = ""


@dataclass
class ItemSpec:
    label: str
    phrase: str
    type: str
    tag: str
    fragile: bool = False


@dataclass
class ToolSpec:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.suspense: float = 0.0
        self.clues: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.suspense = self.suspense
        c.clues = list(self.clues)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "weaving_room": Setting(place="the weaving room", indoors=True, affords={"loom", "expand"}),
    "attic": Setting(place="the attic", indoors=True, affords={"loom", "expand"}),
    "sunroom": Setting(place="the sunroom", indoors=True, affords={"loom", "expand"}),
}

ACTIVITIES = {
    "loom": Activity(
        id="loom",
        verb="work at the loom",
        gerund="weaving at the loom",
        rush="run to the loom",
        mess="tangle",
        clue="thread",
        weather="",
    ),
    "expand": Activity(
        id="expand",
        verb="expand the pattern",
        gerund="expanding the pattern",
        rush="pull the cloth wider",
        mess="tangle",
        clue="border",
        weather="",
    ),
}

ITEMS = {
    "ribbon": ItemSpec(
        label="ribbon",
        phrase="a bright ribbon",
        type="ribbon",
        tag="ribbon",
        fragile=True,
    ),
    "pattern_card": ItemSpec(
        label="pattern card",
        phrase="a neat pattern card",
        type="card",
        tag="pattern",
        fragile=False,
    ),
    "shuttle": ItemSpec(
        label="shuttle",
        phrase="a wooden shuttle",
        type="shuttle",
        tag="shuttle",
        fragile=False,
    ),
}

TOOLS = {
    "magnifier": ToolSpec(
        id="magnifier",
        label="a little magnifying glass",
        prep="get a little magnifying glass",
        tail="used the magnifying glass to follow the clues",
    ),
    "ruler": ToolSpec(
        id="ruler",
        label="a ruler",
        prep="take a ruler to measure the cloth",
        tail="used the ruler to check the edges",
    ),
}


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Mina", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Ben", "Eli", "Noah"]
TRAITS = ["curious", "careful", "brave", "patient", "bright", "quiet"]


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def traceable_story(world: World) -> None:
    pass


def _story_clue(world: World, text: str) -> None:
    world.clues.append(text)
    world.suspense += 1.0
    world.say(text)


def _suspense_line(world: World, hero: Entity, parent: Entity, item: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} noticed something was wrong: {hero.pronoun('possessive')} {item.label} was missing, "
        f"and the tidy room suddenly felt quiet."
    )
    world.say(
        f"{parent.label_word} looked under the loom bench and behind the basket, but the clue did not appear."
    )
    _story_clue(world, f"Then {hero.id} saw a loose thread near the loom, and the mystery began to expand.")
    world.say(
        f"{hero.id} wanted to {activity.verb}, but first {hero.pronoun()} had to solve the small puzzle."
    )


def _predict_issue(world: World, hero: Entity, item: Entity, activity: Activity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["careless"] = sim.get(hero.id).memes.get("careless", 0) + 1
    return True if item.label else False


def _resolve_mystery(world: World, hero: Entity, parent: Entity, item: Entity, activity: Activity) -> tuple[str, str]:
    # The clue chain is state-driven: thread -> shuttle -> item.
    clue1 = f"{hero.id} followed the loose thread to the shuttle."
    clue2 = f"Behind the shuttle, {hero.pronoun('subject')} found the {item.label} tucked beside the yarn basket."
    world.say(clue1)
    world.say(clue2)
    world.say(
        f"That was the answer: the {item.label} had not been stolen at all. It had simply slid behind the basket."
    )
    return clue1, clue2


def _lesson(world: World, hero: Entity, parent: Entity, item: Entity, activity: Activity, tool: ToolSpec) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0) + 1
    world.say(
        f"{hero.id} smiled and said {hero.pronoun('subject')} would look slowly before worrying next time."
    )
    world.say(
        f"Then {hero.id} used {tool.label} and got back to {activity.gerund}, with {item.label} safe on the table."
    )
    world.say(
        f"{parent.label_word} smiled too, because the little mystery had been solved with patience, not panic."
    )


def tell(
    setting: Setting,
    activity: Activity,
    item_spec: ItemSpec,
    hero_name: str,
    hero_type: str,
    hero_traits: list[str],
    parent_type: str,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    item = world.add(Entity(id="item", kind="thing", type=item_spec.type, label=item_spec.label, phrase=item_spec.phrase, owner=hero.id))
    tool = world.add(Entity(id="Tool", kind="thing", type="tool", label=TOOLS["magnifier"].label))

    hero.memes["love"] = 1
    hero.memes["suspense"] = 0
    parent.memes["worry"] = 1

    world.say(
        f"{hero.id} was a {hero_traits[0]} little {hero.type} who loved {activity.gerund} in {setting.place}."
    )
    world.say(f"{hero.id} especially liked {item_spec.phrase} because it made every woven line feel special.")
    world.say(f"One day, {hero.id} and {parent.label_word} came into {setting.place} to {activity.verb}.")

    world.para()
    _suspense_line(world, hero, parent, item, activity)

    world.para()
    world.say(f"{parent.label_word} said they should look carefully instead of pulling the cloth too hard.")
    world.say(f"{hero.id} listened, took {TOOLS['magnifier'].label}, and started again from the first clue.")
    _resolve_mystery(world, hero, parent, item, activity)
    _lesson(world, hero, parent, item, activity, TOOLS["magnifier"])

    world.facts.update(
        hero=hero,
        parent=parent,
        item=item,
        tool=tool,
        activity=activity,
        setting=setting,
        item_spec=item_spec,
        resolved=True,
        lesson_learned=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, item, activity = f["hero"], f["parent"], f["item"], f["activity"]
    return [
        f'Write a short suspenseful story for a child about a {hero.type} named {hero.id} who wants to {activity.verb} but cannot find the {item.label}.',
        f'Create a whodunit-style story where {hero.id} and {hero.pronoun("possessive")} {parent.label_word} solve the mystery of the missing {item.label} in {f["setting"].place}.',
        f'Write a gentle lesson-learned story that uses the words "loom" and "expand" and ends with {hero.id} learning to look carefully.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, item, activity = f["hero"], f["parent"], f["item"], f["activity"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.label_word} in {f['setting'].place}.",
        ),
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was where the {item.label} had gone when {hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the problem?",
            answer=f"A loose thread near the loom helped {hero.id} follow the clues and find the {item.label}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned to look carefully before worrying, because the missing {item.label} was only hidden, not gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a loom?",
            answer="A loom is a tool used for weaving threads into cloth.",
        ),
        QAItem(
            question="What does expand mean?",
            answer="To expand means to make something bigger or wider.",
        ),
        QAItem(
            question="What is a magnifying glass for?",
            answer="A magnifying glass helps you look at small details more closely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- place(S).
activity(A) :- act(A).
item(I) :- artifact(I).

mystery(A,I) :- activity(A), item(I), clue_for(A,C), item_tag(I,C).
suspense(A) :- mystery(A,_).
lesson_learned(S) :- suspense(S), resolved(S).

valid_story(P,A,I) :- place(P), act(A), artifact(I), mystery(A,I).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("place", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("act", a))
        lines.append(asp.fact("clue_for", a, ACTIVITIES[a].clue))
    for i, spec in ITEMS.items():
        lines.append(asp.fact("artifact", i))
        lines.append(asp.fact("item_tag", i, spec.tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    # Minimal parity check: the ASP twin should recognize a story exists for each registry pair.
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "valid_story"))
    python_set = {(p, a, i) for p in SETTINGS for a in ACTIVITIES for i in ITEMS}
    if atoms != python_set:
        print("MISMATCH between ASP and Python registries.")
        only_a = sorted(atoms - python_set)
        only_p = sorted(python_set - atoms)
        if only_a:
            print("only in ASP:", only_a)
        if only_p:
            print("only in python:", only_p)
        return 1
    print(f"OK: ASP parity check passed ({len(atoms)} combinations).")
    return 0


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: loom, expand, suspense, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    item = args.item or rng.choice(list(ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    if activity not in SETTINGS[place].affords:
        raise StoryError("That activity does not fit this setting.")
    return StoryParams(place=place, activity=activity, item=item, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        ITEMS[params.item],
        params.name,
        params.gender,
        [params.trait, "careful"],
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"suspense={world.suspense}")
    lines.append(f"clues={world.clues}")
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
    StoryParams(place="weaving_room", activity="loom", item="shuttle", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="sunroom", activity="expand", item="pattern_card", name="Theo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="attic", activity="loom", item="ribbon", name="Lily", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
