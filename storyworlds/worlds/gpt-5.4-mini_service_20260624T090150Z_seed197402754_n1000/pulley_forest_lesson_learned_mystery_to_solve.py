#!/usr/bin/env python3
"""
A small whodunit-style storyworld in a forest around a pulley.

Premise:
- A child detective and a forest keeper use a pulley basket in the woods.
- Something important goes missing from the basket.
- The mystery is solved by following concrete clues.
- The ending leaves a clear lesson learned about checking clues before blaming.

This world is self-contained and follows the Storyweavers contract.
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

LESSON = "lesson learned"
MYSTERY = "mystery to solve"
CONFLICT = "conflict"

THEMES = {LESSON, MYSTERY, CONFLICT}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "keeper"}
        male = {"boy", "man", "father", "ranger"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str
    helper: str
    culprit: str
    item: str
    seed: Optional[int] = None


@dataclass
class CulpritProfile:
    id: str
    label: str
    clue: str
    motive: str
    track: str


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
class StoryParamsRegistry:
    pass


NAMES = ["Mina", "Theo", "Ava", "Noah", "Luna", "Eli", "Nora", "Finn"]
HELPERS = ["forest keeper", "older sister", "older brother", "park ranger"]
ITEMS = {
    "lantern": ("lantern", "a bright brass lantern"),
    "map": ("map", "a folded trail map"),
    "snackbox": ("snackbox", "a red snack box"),
    "whistle": ("whistle", "a small silver whistle"),
}

CULPRITS = {
    "raccoon": CulpritProfile(
        id="raccoon",
        label="a raccoon",
        clue="muddy paw prints",
        motive="to stash something shiny where no one would trip over it",
        track="the prints had tiny hand-like toes",
    ),
    "squirrel": CulpritProfile(
        id="squirrel",
        label="a squirrel",
        clue="crumbled acorn shells",
        motive="to hide a prize in a dry nest nook",
        track="the trail ended under a high branch",
    ),
    "fox": CulpritProfile(
        id="fox",
        label="a fox",
        clue="a strip of red fur",
        motive="to move the item for a game of hide-and-seek",
        track="the trail curved neatly through the ferns",
    ),
}

ASP_RULES = r"""
culprit(raccoon).
culprit(squirrel).
culprit(fox).

clue(raccoon, muddy_paws).
clue(squirrel, acorn_shells).
clue(fox, red_fur).

solves(X) :- clue(X, muddy_paws), found_muddy_paws.
solves(X) :- clue(X, acorn_shells), found_acorn_shells.
solves(X) :- clue(X, red_fur), found_red_fur.

resolved(X) :- culprit(X), solves(X).
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("found_muddy_paws") if "muddy paw prints" in FOUND_CLUES else "",
        asp.fact("found_acorn_shells") if "crumbled acorn shells" in FOUND_CLUES else "",
        asp.fact("found_red_fur") if "a strip of red fur" in FOUND_CLUES else "",
    ]).strip()


FOUND_CLUES: set[str] = set()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit in a forest with a pulley and a lesson learned.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--item", choices=ITEMS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CULPRITS:
        for item in ITEMS:
            combos.append(("forest", c, item))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.item and args.culprit not in CULPRITS:
        raise StoryError("Unknown culprit.")
    combos = valid_combos()
    culprit = args.culprit or rng.choice(sorted(CULPRITS))
    item = args.item or rng.choice(sorted(ITEMS))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, helper=helper, culprit=culprit, item=item)


def generate(params: StoryParams) -> StorySample:
    world = World()
    hero = world.add(Entity(id="child", kind="character", type="girl" if params.name in {"Mina", "Ava", "Luna", "Nora"} else "boy", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="keeper" if params.helper == "forest keeper" else "ranger", label=params.helper))
    item_label, item_phrase = ITEMS[params.item]
    missing = world.add(Entity(id="missing", type="thing", label=item_label, phrase=item_phrase, caretaker=helper.id))
    culprit = CULPRITS[params.culprit]

    world.say(f"{hero.label} came to the forest with {helper.label} and a pulley basket beside the old pine.")
    world.say(f"In the basket sat {missing.phrase}, because the forest paths were damp and careful hands kept things dry.")
    world.say(f"{hero.label} liked the pulley best. The rope rose and fell with a soft creak, like the woods were whispering back.")

    world.para()
    world.say(f"Then the basket was empty.")
    world.say(f"{hero.label} felt a sharp knot of worry. {helper.label.capitalize()} frowned and looked at the ground.")
    world.say(f"\"Who took it?\" {hero.label} asked. That was the big {MYSTERY}.")

    world.para()
    world.say(f"At first, {hero.label} blamed the wrong creature. The forest had many busy feet, and {hero.label} felt the {CONFLICT} growing.")
    if params.culprit == "raccoon":
        world.say("But the little muddy prints near the pulley were not deer tracks or rabbit hops. They had tiny hand-like toes.")
        world.say("A berry stain dotted the rope knot too, as if somebody with clever paws had climbed up after a snack.")
        FOUND_CLUES.add("muddy paw prints")
        world.say("Then a raccoon peeked from behind a stump, holding the missing thing with a sheepish grin.")
    elif params.culprit == "squirrel":
        world.say("But the shelf of bark under the pulley held broken acorn shells, and the trail climbed straight into a nest of leaves.")
        world.say("The ropes swayed under a high branch, where a squirrel had tucked the item away beside a dry bundle of moss.")
        FOUND_CLUES.add("crumbled acorn shells")
        world.say("The squirrel blinked, then admitted it had only meant to keep the thing safe from rain.")
    else:
        world.say("But a thin strip of red fur had snagged on the pulley hook, and the trail curved neatly through the ferns.")
        world.say("At the end of that trail stood a fox, ears low, returning the missing item with careful paws.")
        FOUND_CLUES.add("a strip of red fur")

    world.para()
    world.say(f"{helper.label} listened to the clues and said, \"The woods tell the truth if we look kindly enough.\"")
    world.say(f"{hero.label} nodded. The real answer mattered more than the first guess.")
    world.say(f"Together they lowered the pulley basket, put {missing.pronoun('object')} back inside, and tied the rope in a neat knot.")
    world.say(f"{hero.label} learned a lesson: in the forest, solve the mystery before you assign the blame.")
    world.say(f"By the end, the pulley hung still, the basket was full again, and the whole forest felt calm.")

    hero.memes["worry"] = 1.0
    hero.memes["suspicion"] = 1.0
    hero.memes["relief"] = 1.0
    hero.memes["lesson"] = 1.0
    missing.meters["height"] = 0.0
    world.facts = {
        "hero": hero,
        "helper": helper,
        "missing": missing,
        "culprit": culprit,
        "params": params,
        "clues": sorted(FOUND_CLUES),
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        "Write a child-friendly whodunit set in a forest with a pulley basket and one missing item.",
        f"Tell a mystery story where {p.name} and a {p.helper} notice that {ITEMS[p.item][1]} has vanished from the pulley basket.",
        "Write a gentle forest detective tale with clues, a mistaken guess, and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, missing, culprit = f["hero"], f["helper"], f["missing"], f["culprit"]
    return [
        QAItem(
            question=f"What mystery did {hero.label} and {helper.label} have to solve in the forest?",
            answer=f"They had to solve the mystery of who took {missing.phrase} from the pulley basket.",
        ),
        QAItem(
            question=f"What clue helped show it was {culprit.label}?",
            answer=f"The clue was {culprit.clue}, and it matched the trail near the pulley.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn by the end?",
            answer="The lesson was to follow the clues carefully before blaming someone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pulley?",
            answer="A pulley is a wheel and rope system that helps lift or lower things more easily.",
        ),
        QAItem(
            question="What is a forest?",
            answer="A forest is a place with many trees, plants, and animals.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues help them figure out what really happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mina", helper="forest keeper", culprit="raccoon", item="lantern"),
    StoryParams(name="Theo", helper="park ranger", culprit="squirrel", item="map"),
    StoryParams(name="Luna", helper="older sister", culprit="fox", item="whistle"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    py = {(c,) for c in CULPRITS}
    cl = set(asp_valid_combos())
    if cl == py:
        print("OK: ASP parity check passed.")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", sorted(cl))
    print("PY:", sorted(py))
    return 1


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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show resolved/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
