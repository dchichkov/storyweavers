#!/usr/bin/env python3
"""
storyworlds/worlds/triplet_tar_millennium_parking_lot_quest_transformation.py
=============================================================================

A standalone story world for a small Space Adventure tale set in a parking lot.

Premise:
- Three siblings, a triplet crew, find a strange tar-black patch in a parking lot.
- The patch hides a tiny mystery tied to a lost millennium beacon.
- A quest, a transformation, and a mystery to solve drive the story.
- The ending should prove what changed in the world, not just in wording.

The world is intentionally small and constraint-checked:
- A valid story must have a real mystery, a plausible quest, and a transformation
  that genuinely helps solve it.
- The parking lot setting is central and cannot be swapped out.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
# Parameters / registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    crew: str
    mystery: str
    transformation: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class CrewSpec:
    kind: str
    name_a: str
    name_b: str
    name_c: str
    label: str


@dataclass(frozen=True)
class MysterySpec:
    id: str
    clue: str
    hidden_item: str
    hidden_label: str
    danger: str
    reveal: str


@dataclass(frozen=True)
class TransformationSpec:
    id: str
    trigger: str
    form: str
    benefit: str
    closing_image: str


@dataclass(frozen=True)
class QuestSpec:
    id: str
    goal: str
    route: str
    tension: str
    success: str


SETTINGS = {
    "parking_lot": "the parking lot",
}

CREWS = {
    "triplet": CrewSpec(
        kind="triplet",
        name_a="Mira",
        name_b="Niko",
        name_c="Tess",
        label="triplet crew",
    ),
}

MYSTERIES = {
    "tar_millennium": MysterySpec(
        id="tar_millennium",
        clue="a shiny old badge half-buried in tar",
        hidden_item="millennium_beacon",
        hidden_label="millennium beacon",
        danger="sticky tar that glued their boots to the ground",
        reveal="the beacon was a map-light that could point the way home",
    ),
}

TRANSFORMATIONS = {
    "star_suits": TransformationSpec(
        id="star_suits",
        trigger="the beacon woke up",
        form="glimmering star suits",
        benefit="they could step lightly over the tar and read the beacon's glow",
        closing_image="their star suits faded into soft dust while the parking lot lights shone like tiny moons",
    ),
}

QUESTS = {
    "solve_mystery": QuestSpec(
        id="solve_mystery",
        goal="figure out what the tar was hiding",
        route="follow the clues across the parking lot",
        tension="the tar patch kept stretching like a black puddle and blocking the way",
        success="the crew solved the mystery and found the beacon's true signal",
    ),
}

GIRL_NAMES = ["Mira", "Tess", "Lina", "Zara", "Nova"]
BOY_NAMES = ["Niko", "Jace", "Finn", "Orin", "Kai"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, crew: str, mystery: str, transformation: str) -> bool:
    return (
        place == "parking_lot"
        and crew in CREWS
        and mystery in MYSTERIES
        and transformation in TRANSFORMATIONS
    )


def explain_invalid(place: str, crew: str, mystery: str, transformation: str) -> str:
    if place != "parking_lot":
        return "(No story: this world only works in a parking lot.)"
    if crew not in CREWS:
        return "(No story: the crew must be a triplet crew for this seed.)"
    if mystery not in MYSTERIES:
        return "(No story: the mystery must involve tar and the millennium beacon.)"
    if transformation not in TRANSFORMATIONS:
        return "(No story: the transformation must be the star-suit change.)"
    return "(No story: the requested combination is not reasonable here.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell_story(params: StoryParams) -> World:
    if not valid_combo(params.place, params.crew, params.mystery, params.transformation):
        raise StoryError(explain_invalid(params.place, params.crew, params.mystery, params.transformation))

    setting = SETTINGS[params.place]
    crew = CREWS[params.crew]
    mystery = MYSTERIES[params.mystery]
    transform = TRANSFORMATIONS[params.transformation]
    quest = QUESTS["solve_mystery"]

    world = World(setting=setting)
    a = world.add(Entity(id=crew.name_a, kind="character", type="girl", label=crew.name_a))
    b = world.add(Entity(id=crew.name_b, kind="character", type="boy", label=crew.name_b))
    c = world.add(Entity(id=crew.name_c, kind="character", type="girl", label=crew.name_c))
    beacon = world.add(Entity(
        id="beacon",
        kind="thing",
        type="device",
        label=mystery.hidden_label,
        phrase="a small silver beacon with a round lens",
    ))
    tar_patch = world.add(Entity(
        id="tar",
        kind="thing",
        type="tar",
        label="tar patch",
        phrase="a thick black tar patch",
    ))

    # act 1: setup
    world.say(
        f"On a bright evening in {setting}, the triplet crew {crew.name_a}, {crew.name_b}, and {crew.name_c} found a strange spot in the asphalt."
    )
    world.say(
        f"It looked like {tar_patch.phrase}, and half of {mystery.clue} stuck out of it like a tiny lost star."
    )
    world.say(
        f"The three of them had come on a {quest.goal}, because the old parking lot had whispered about a lost millennium signal for years."
    )

    # act 2: tension and quest
    world.para()
    a.memes["curiosity"] = a.memes.get("curiosity", 0.0) + 1
    b.memes["fear"] = b.memes.get("fear", 0.0) + 1
    c.memes["hope"] = c.memes.get("hope", 0.0) + 1
    world.say(
        f"{crew.name_a} wanted to touch the clue, but {mystery.danger} made {crew.name_b} step back."
    )
    world.say(
        f"Together they chose to {quest.route}, even while {quest.tension}."
    )
    world.say(
        f"They circled the spot, looking for a way to free the beacon without letting the tar win."
    )

    # transformation
    world.para()
    beacon.meters["mystery"] = 1.0
    beacon.memes["wake"] = 1.0
    world.say(
        f"Then {mystery.hidden_item} began to hum, and {transform.trigger}."
    )
    world.say(
        f"The siblings transformed into {transform.form}, and suddenly {transform.benefit}."
    )
    world.say(
        f"{crew.name_a} lifted the beacon, {crew.name_b} traced the glow, and {crew.name_c} called out the hidden path."
    )

    # resolution
    world.para()
    tar_patch.meters["sticky"] = 0.0
    beacon.meters["found"] = 1.0
    world.say(
        f"At last, {quest.success}. {mystery.reveal}."
    )
    world.say(
        f"Their {transform.closing_image}, and the parking lot no longer felt like a trap."
    )
    world.say(
        f"The triplet crew went home with clean shoes, a warm secret, and the comfort of knowing the millennium light had been found."
    )

    world.facts.update(
        setting=setting,
        crew=crew,
        mystery=mystery,
        transform=transform,
        quest=quest,
        characters=[a, b, c],
        beacon=beacon,
        tar_patch=tar_patch,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    crew: CrewSpec = f["crew"]
    mystery: MysterySpec = f["mystery"]
    quest: QuestSpec = f["quest"]
    transform: TransformationSpec = f["transform"]
    return [
        'Write a short space-adventure story for a child about a triplet crew in a parking lot.',
        f"Tell a mystery-to-solve tale where {crew.name_a}, {crew.name_b}, and {crew.name_c} investigate {mystery.clue}.",
        f"Write a story where a quest turns into a transformation and the team finds a millennium beacon.",
        f"Make the ending show how {transform.form} helped solve the mystery in the parking lot.",
        f"Use the words triplet, tar, and millennium in a child-friendly space adventure.",
        f"Include a quest that lets the crew {quest.route}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew: CrewSpec = f["crew"]
    mystery: MysterySpec = f["mystery"]
    transform: TransformationSpec = f["transform"]
    quest: QuestSpec = f["quest"]
    place = f["setting"]

    return [
        QAItem(
            question="Who went looking for the mystery in the parking lot?",
            answer=f"The triplet crew of {crew.name_a}, {crew.name_b}, and {crew.name_c} went looking for it together.",
        ),
        QAItem(
            question="What was hidden in the tar?",
            answer=f"The tar was hiding the {mystery.hidden_label}, which turned out to be a tiny millennium beacon.",
        ),
        QAItem(
            question="What made the crew transform?",
            answer=f"They transformed when the hidden beacon woke up, and the change gave them {transform.benefit}.",
        ),
        QAItem(
            question="What was the quest in the story?",
            answer=f"The quest was to {quest.goal} by following clues across {place}.",
        ),
        QAItem(
            question="Why was the tar a problem?",
            answer=f"The tar was a problem because {mystery.danger}, which made the path hard to cross.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the mystery solved, the beacon found, and the parking lot feeling safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tar?",
            answer="Tar is a thick, sticky black material that can stick to shoes, wheels, and paws.",
        ),
        QAItem(
            question="What is a millennium?",
            answer="A millennium is a very long time—one thousand years.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to find something important or solve a problem.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a puzzle where clues help you discover what is really happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", ""]
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid only in the parking lot with the triplet crew, tar mystery,
% and star-suit transformation.
valid_story(P, C, M, T) :- place(P), crew(C), mystery(M), transformation(T),
                           parking_lot(P), triplet_crew(C),
                           tar_mystery(M), star_suits(T).

% The mystery is a genuine mystery only if tar hides the beacon.
mystery_real(M) :- tar_mystery(M).

% The transformation must help the crew cross the tar and find the beacon.
helps_solve(T, M) :- star_suits(T), tar_mystery(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("place", "parking_lot"))
    lines.append(asp.fact("parking_lot", "parking_lot"))
    for cid in CREWS:
        lines.append(asp.fact("crew", cid))
        lines.append(asp.fact("triplet_crew", cid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("tar_mystery", mid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("star_suits", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("parking_lot", "triplet", "tar_millennium", "star_suits")} if valid_combo("parking_lot", "triplet", "tar_millennium", "star_suits") else set()
    asp_set = set(asp_valid_stories())
    if asp_set == py:
        print("OK: clingo gate matches Python validity.")
        return 0
    print("MISMATCH between clingo and Python validity:")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world in a parking lot.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--crew", choices=CREWS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--transformation", choices=TRANSFORMATIONS.keys())
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
    place = args.place or "parking_lot"
    crew = args.crew or "triplet"
    mystery = args.mystery or "tar_millennium"
    transformation = args.transformation or "star_suits"
    if not valid_combo(place, crew, mystery, transformation):
        raise StoryError(explain_invalid(place, crew, mystery, transformation))
    return StoryParams(place=place, crew=crew, mystery=mystery, transformation=transformation)


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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
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
    StoryParams(place="parking_lot", crew="triplet", mystery="tar_millennium", transformation="star_suits"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for item in stories:
            print("  ", item)
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
