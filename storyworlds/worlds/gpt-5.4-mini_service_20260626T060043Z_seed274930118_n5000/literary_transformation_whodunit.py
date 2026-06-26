#!/usr/bin/env python3
"""
storyworlds/worlds/literary_transformation_whodunit.py
======================================================

A small whodunit storyworld about a literary scene, a mysterious transformation,
and a child-friendly reveal.

Premise:
- A careful reader notices something in the story room has changed.
- The change is physical and visible: a plain object has transformed into a new
  literary object.
- The detective must trace clues, question a helper, and discover who did it.

The story stays close to a whodunit: clue, suspicion, deduction, reveal.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    literary: bool = False


@dataclass
class StoryParams:
    place: str
    victim: str
    culprit: str
    transformed_into: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Location):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _meter(x: float) -> bool:
    return x >= THRESHOLD


def _capitalize(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Location(id="library", label="the little library", literary=True),
    "study": Location(id="study", label="the quiet study", literary=True),
    "attic": Location(id="attic", label="the book-lined attic", literary=True),
}

TRANSFORMATIONS = {
    "pumpkin": {
        "result_label": "a pumpkin-shaped bookmark",
        "result_phrase": "a pumpkin-shaped bookmark with a gold ribbon",
        "result_type": "bookmark",
        "clue": "orange paper crumbs",
        "method": "folded and tied",
        "method_text": "folded it into a new shape and tied on a ribbon",
        "story_verb": "turn into a pumpkin-shaped bookmark",
    },
    "lantern": {
        "result_label": "a paper lantern",
        "result_phrase": "a paper lantern with star cutouts",
        "result_type": "lantern",
        "clue": "tiny paper stars",
        "method": "cut and opened",
        "method_text": "cut a pattern into it and opened it like a flower",
        "story_verb": "turn into a paper lantern",
    },
    "dragon": {
        "result_label": "a dragon puppet",
        "result_phrase": "a bright dragon puppet with a paper tail",
        "result_type": "puppet",
        "clue": "green glitter flakes",
        "method": "glued and stitched",
        "method_text": "glued on scales and stitched on a tail",
        "story_verb": "turn into a dragon puppet",
    },
}

CHARACTER_TRAITS = ["curious", "careful", "brave", "patient", "quiet", "clever"]
NAMES = ["Mina", "Owen", "Nora", "Leo", "Ava", "Sam", "Ivy", "Theo"]


@dataclass
class StoryContext:
    location: Location
    victim: Entity
    culprit: Entity
    transformed_into: dict
    detective: Entity
    helper: Entity


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The victim is at risk if the culprit has transformation energy and the same
% object is being handled.
at_risk(V) :- transformed(V, _), touched_by_culprit(V), clue_matches(V), motive(C), culprit(C).

% The culprit is plausible if the object changes in a literary place and the clue
% fits the kind of transformation.
plausible_culprit(C) :- culprit(C), literary_place(L), in_place(C, L), motive(C).

% A full mystery is valid when there is exactly one victim, one culprit, and the
% transformed object can be explained by the clue trail.
valid_story(L, V, C) :- literary_place(L), transformed(V, _), culprit(C),
                        clue_matches(V), motive(C), in_place(C, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, loc in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if loc.literary:
            lines.append(asp.fact("literary_place", sid))
    for key in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# World-building
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)

    victim = world.add(Entity(
        id="Victim",
        kind="thing",
        type="book",
        label="book",
        phrase="an old plain book",
        location=place.id,
        meters={"plain": 1.0, "changed": 0.0},
        memes={"mystery": 0.0},
    ))
    culprit = world.add(Entity(
        id="Culprit",
        kind="character",
        type=params.culprit,
        label=params.culprit,
        phrase=f"a {params.culprit} with ink on their fingers",
        location=place.id,
        traits=["sly", "secretive"],
        meters={"ink": 1.0},
        memes={"guilt": 0.0, "nervous": 0.0},
    ))
    detective = world.add(Entity(
        id="Detective",
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
        phrase=f"{params.detective_name}, the little detective",
        location=place.id,
        traits=["careful", "curious"],
        meters={"attention": 1.0},
        memes={"wonder": 1.0, "certainty": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        phrase=f"{params.helper_name}, a helpful friend",
        location=place.id,
        traits=["helpful"],
        meters={"attention": 1.0},
        memes={"concern": 1.0},
    ))
    transformed = TRANSFORMATIONS[params.transformed_into]
    world.facts.update(
        place=place,
        victim=victim,
        culprit=culprit,
        detective=detective,
        helper=helper,
        transformed=transformed,
    )
    return world


def _transformation_event(world: World) -> None:
    victim = world.get("Victim")
    culprit = world.get("Culprit")
    t = world.facts["transformed"]

    if ("transform", victim.id) in world.fired:
        return
    world.fired.add(("transform", victim.id))

    victim.label = t["result_label"]
    victim.phrase = t["result_phrase"]
    victim.type = t["result_type"]
    victim.meters["plain"] = 0.0
    victim.meters["changed"] = 1.0
    victim.meters["crafted"] = 1.0
    culprit.memes["guilt"] = 1.0
    culprit.memes["nervous"] = 1.0


def setup_story(world: World) -> None:
    d = world.get("Detective")
    h = world.get("Helper")
    v = world.get("Victim")
    c = world.get("Culprit")
    t = world.facts["transformed"]

    world.say(
        f"In {world.place.label}, {d.label} found {v.phrase} on a table by the window."
    )
    world.say(
        f"Nothing looked broken, but the book did not look like a book anymore. "
        f"It had somehow changed into {t['result_phrase']}."
    )

    world.para()
    world.say(
        f"{d.label} narrowed {d.pronoun('possessive')} eyes. "
        f"Something in the room had happened quietly, and the clue was likely nearby."
    )
    world.say(
        f"{h.label} pointed at the floor. "
        f"There were {t['clue']} by the table and a faint trail of {c.phrase.split()[-3] if 'fingers' in c.phrase else 'ink'}."
    )


def suspect_and_reveal(world: World) -> None:
    d = world.get("Detective")
    h = world.get("Helper")
    v = world.get("Victim")
    c = world.get("Culprit")
    t = world.facts["transformed"]

    world.para()
    world.say(
        f"{d.label} asked {h.label} who had been near the book. "
        f"{h.label} whispered that only {c.label} had touched it after the story circle."
    )
    world.say(
        f"That was the missing piece: {c.label} had {t['method_text']} while making a surprise for the shelf."
    )
    _transformation_event(world)

    world.para()
    world.say(
        f"{d.label} looked at the changed book again and smiled. "
        f"The puzzle fit: the {t['clue']} came from the craft, and the new shape matched the secret gift."
    )
    world.say(
        f"{c.label} blushed and admitted the truth. "
        f"{c.pronoun().capitalize()} had only wanted to make something magical for the room."
    )

    world.para()
    world.say(
        f"In the end, {v.phrase} stayed safely on the table, and "
        f"{d.label} placed it beside the shelf where everyone could admire it."
    )
    world.say(
        f"The little mystery was solved, and the room felt literary and bright again."
    )


def tell(params: StoryParams) -> World:
    world = make_world(params)
    setup_story(world)
    suspect_and_reveal(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    t = f["transformed"]
    return [
        f'Write a child-friendly whodunit about a literary room where a plain book seems to {t["story_verb"]}.',
        f'Tell a short mystery story in which a careful detective solves who made {t["result_phrase"]}.',
        f'Write a story with clues, suspicion, and a gentle reveal in a library setting, using the word "literary".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    h = f["helper"]
    c = f["culprit"]
    v = f["victim"]
    t = f["transformed"]

    return [
        QAItem(
            question=f"What did {d.label} find in {world.place.label}?",
            answer=f"{d.label} found {v.phrase} in {world.place.label}. It had already changed shape, so it looked like a mystery right away.",
        ),
        QAItem(
            question=f"What clue helped {d.label} notice who changed the book?",
            answer=f"The clue was {t['clue']} near the table, which matched the craft work that made the new shape.",
        ),
        QAItem(
            question=f"Who had touched the book before the transformation?",
            answer=f"{c.label} had touched the book before it changed. That is why {h.label}'s whispered hint mattered so much.",
        ),
        QAItem(
            question=f"How did the detective solve the mystery?",
            answer=f"{d.label} listened to {h.label}, noticed the {t['clue']}, and matched the clue to the craft that {c.label} had done.",
        ),
        QAItem(
            question=f"What did the book become by the end?",
            answer=f"The book became {t['result_phrase']}. The new object stayed on the table as proof that the transformation really happened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps the detective figure out what happened.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully, asks questions, and uses clues to solve a problem.",
        ),
        QAItem(
            question="What does literary mean?",
            answer="Literary means it has to do with books, stories, reading, or writing.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
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
# Trace / verification
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_stories = sorted(set(asp.atoms(model, "valid_story")))
    py_stories = sorted((p, "Victim", "Culprit") for p in SETTINGS if SETTINGS[p].literary)
    if len(asp_stories) == len(py_stories):
        print(f"OK: clingo gate matches the simple literary-place universe ({len(asp_stories)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print("  clingo:", asp_stories)
    print("  python:", py_stories)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A literary transformation whodunit storyworld."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--victim", choices=TRANSFORMATIONS.keys())
    ap.add_argument("--culprit", choices=["artist", "scribe", "poet", "binder"])
    ap.add_argument("--transformed-into", choices=TRANSFORMATIONS.keys())
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for victim in TRANSFORMATIONS:
            for transformed_into in TRANSFORMATIONS:
                if victim == transformed_into:
                    combos.append((place, victim, transformed_into))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    victim = args.victim or rng.choice(list(TRANSFORMATIONS.keys()))
    transformed_into = args.transformed_into or rng.choice(list(TRANSFORMATIONS.keys()))
    culprit = args.culprit or rng.choice(["artist", "scribe", "poet", "binder"])
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if detective_type == "girl" else "girl")
    detective_name = args.detective_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != detective_name])

    if victim not in TRANSFORMATIONS:
        raise StoryError("Unknown victim transformation key.")
    if transformed_into not in TRANSFORMATIONS:
        raise StoryError("Unknown result transformation key.")
    if not SETTINGS[place].literary:
        raise StoryError("This storyworld only supports literary places.")

    return StoryParams(
        place=place,
        victim=victim,
        culprit=culprit,
        transformed_into=transformed_into,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_name=helper_name,
        helper_type=helper_type,
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


CURATED = [
    StoryParams(
        place="library",
        victim="pumpkin",
        culprit="scribe",
        transformed_into="pumpkin",
        detective_name="Mina",
        detective_type="girl",
        helper_name="Owen",
        helper_type="boy",
    ),
    StoryParams(
        place="study",
        victim="lantern",
        culprit="poet",
        transformed_into="lantern",
        detective_name="Nora",
        detective_type="girl",
        helper_name="Sam",
        helper_type="boy",
    ),
    StoryParams(
        place="attic",
        victim="dragon",
        culprit="binder",
        transformed_into="dragon",
        detective_name="Leo",
        detective_type="boy",
        helper_name="Ivy",
        helper_type="girl",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} valid literary stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.detective_name}: {p.place} mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
