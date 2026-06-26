#!/usr/bin/env python3
"""
A campground whodunit where a suspicious magic trick, a furious helper, and a
small conspiracy are resolved by careful clues rather than force.
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
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.role in {"girl", "woman", "mother", "ranger"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Campground:
    name: str = "the campground"
    has_magic_show: bool = True
    has_rumor_board: bool = True


@dataclass
class Clue:
    id: str
    thing: str
    truth: str
    hint: str


@dataclass
class StoryParams:
    name: str
    role: str
    helper: str
    culprit: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Campground) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story_bits: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story_bits.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_bits)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
NAMES = ["Mina", "Theo", "Iris", "Eli", "Nora", "Sam", "Luna", "Finn"]
ROLES = {
    "ranger": "ranger",
    "camper": "camper",
    "cook": "cook",
    "caretaker": "caretaker",
}
HELPERS = {
    "lantern": "a brass lantern",
    "map": "a folded trail map",
    "magnifier": "a pocket magnifier",
    "whistle": "a silver whistle",
}
CULPRITS = {
    "fox": "a sly fox",
    "neighbor": "a nervous neighbor",
    "magician": "the camp magician",
    "raccoon": "a bold raccoon",
}
CLUES = {
    "glitter": Clue("glitter", "glitter", "the magic show spilled glitter near the stage", "tiny sparkles on the pine needles"),
    "mud": Clue("mud", "mud", "someone hurried through the muddy path by the creek", "brown prints leading away from the tents"),
    "rope": Clue("rope", "rope", "a rope knot from the magic curtain was left behind", "a loose knot tied like a stage prop"),
    "pine": Clue("pine", "pine resin", "sticky pine resin was on the lantern handle", "sticky sap on a metal handle"),
}

MAGIC_PROPS = {
    "cloak": "a starry cloak",
    "hat": "a tall black hat",
    "wand": "a silver wand",
}

# ---------------------------------------------------------------------------
# Aspirational whodunit logic
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Campground whodunit with magic and a mystery to solve.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=sorted(ROLES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--clue", choices=sorted(CLUES))
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
    role = args.role or rng.choice(list(ROLES))
    helper = args.helper or rng.choice(list(HELPERS))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    clue = args.clue or rng.choice(list(CLUES))
    if culprit == "magician" and clue == "glitter":
        pass
    if args.culprit == "fox" and args.clue == "rope":
        raise StoryError("A fox would not plausibly leave a stage rope clue at the campground mystery.")
    return StoryParams(name=name, role=role, helper=helper, culprit=culprit, clue=clue)


def reasonableness_gate(params: StoryParams) -> bool:
    return True


ASP_RULES = r"""
campground(camp).
role(ranger). role(camper). role(cook). role(caretaker).
helper(lantern). helper(map). helper(magnifier). helper(whistle).
culprit(fox). culprit(neighbor). culprit(magician). culprit(raccoon).
clue(glitter). clue(mud). clue(rope). clue(pine).

mystery(C) :- clue(C).
suspect(X) :- culprit(X).
compatible(magician, glitter).
compatible(neighbor, rope).
compatible(raccoon, mud).
compatible(fox, pine).
valid(X,C) :- suspect(X), mystery(C), compatible(X,C).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("campground", "camp")]
    for r in ROLES:
        lines.append(asp.fact("role", r))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for c in CULPRITS:
        lines.append(asp.fact("culprit", c))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((c, clue) for c, clue in [("magician", "glitter"), ("neighbor", "rope"), ("raccoon", "mud"), ("fox", "pine")])
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} pairs).")
        return 0
    print("MISMATCH:")
    print(" python-only:", sorted(py - cl))
    print(" clingo-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story synthesis
# ---------------------------------------------------------------------------
def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.name, kind="character", role=params.role))
    helper = world.add(Entity(id="helper", kind="character", role="ranger" if params.helper == "lantern" else "caretaker"))
    culprit = world.add(Entity(id="culprit", kind="character", label=CULPRITS[params.culprit], role=params.culprit))
    clue = CLUES[params.clue]
    prop_name = "prop"

    world.facts.update(hero=hero, helper=helper, culprit=culprit, clue=clue, params=params)

    world.say(
        f"At the campground, {hero.id} noticed something odd near the magic tent. "
        f"Tonight's show was supposed to be wonderful, but the air already felt suspicious."
    )
    world.say(
        f"{hero.id} had come to watch the magician's trick, and a mystery was waiting beside the lantern-lit pines."
    )
    world.say(
        f"Then {hero.id} found {clue.hint}. That clue mattered because it matched a small detail from the magic stage."
    )

    world.say(
        f"{hero.id} asked the helper for a closer look. The helper was furious at the rumor that someone was blaming the wrong camper."
    )
    helper.memes["furious"] = 1
    hero.memes["curious"] = 1

    world.say(
        f"With a magnifier and a careful breath, {hero.id} followed the clue to {culprit.label.lower()}."
    )
    world.say(
        f"The evidence was plain: {clue.truth}. That made the true answer fit the whole scene like a key in a lock."
    )
    culprit.memes["nervous"] = 1

    world.say(
        f"In the end, {hero.id} explained the trick, the helper calmed down, and the campground rumor fell apart."
    )
    world.say(
        f"The magician's prop {prop_name} was returned, the wrong accusation was gone, and the night felt safe again under the stars."
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    clue = CLUES[p.clue]
    return [
        "Write a campground whodunit where a child solves a mystery with magic clues.",
        f"Tell a short story where {p.name} uses {HELPERS[p.helper]} to solve a suspicious event at the campground.",
        f"Write a gentle mystery in which a furious helper helps prove that {clue.thing} means the case has a real answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    clue: Clue = world.facts["clue"]
    hero: Entity = world.facts["hero"]
    culprit: Entity = world.facts["culprit"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"What kind of story is this about {p.name} at the campground?",
            answer=f"It is a campground whodunit, where {hero.id} has to solve a mystery by following clues instead of guessing.",
        ),
        QAItem(
            question=f"What clue helped {p.name} solve the mystery?",
            answer=f"{clue.hint.capitalize()} helped most, because it matched {clue.truth}.",
        ),
        QAItem(
            question=f"Why was the helper furious?",
            answer=f"The helper was furious because someone was making the wrong accusation, and the clue showed the truth was different.",
        ),
        QAItem(
            question=f"Who turned out to be tied to the mystery?",
            answer=f"The answer pointed to {culprit.label.lower()}, after {hero.id} put the clue together with the campground scene.",
        ),
        QAItem(
            question=f"How did {p.name} help the campsite feel safe again?",
            answer=f"{hero.id} explained the clue clearly, and that broke the conspiracy-like rumor so everyone could relax under the stars again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What is a campground?",
            answer="A campground is a place where people stay in tents or campers and spend time outside together.",
        ),
        QAItem(
            question="What does furious mean?",
            answer="Furious means very, very angry.",
        ),
        QAItem(
            question="What does magic often look like in a story?",
            answer="Magic often looks surprising, like a trick, a special object, or something that seems impossible.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(name="Mina", role="camper", helper="magnifier", culprit="magician", clue="glitter"),
    StoryParams(name="Theo", role="ranger", helper="lantern", culprit="neighbor", clue="rope"),
    StoryParams(name="Iris", role="caretaker", helper="map", culprit="fox", clue="pine"),
]


def generate(params: StoryParams) -> StorySample:
    world = World(Campground())
    generate_story(world, params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid clue/case pairs:")
        for c, clue in pairs:
            print(f"  {c:10} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
