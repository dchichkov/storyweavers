#!/usr/bin/env python3
"""
Storyworld: Smorgasbord Detective

A small TinyStories-style domain about a child detective, a messy buffet table,
bare footprints, and a kind helper who makes the case solvable. The world is
simulated: clues, footprints, missing items, and the final reveal all come from
state changes, not from a frozen paragraph with swapped names.
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
    barefoot: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    setting: str
    affords: set[str] = field(default_factory=set)


@dataclass
class SuspectProfile:
    id: str
    label: str
    kind: str
    hides: str
    motive: str


@dataclass
class Clue:
    id: str
    label: str
    reveal: str
    near: str


@dataclass
class Tool:
    id: str
    label: str
    use: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

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
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = _copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def record(self, msg: str) -> None:
        self.trace.append(msg)


@dataclass
class StoryParams:
    place: str
    detective: str
    detective_type: str
    helper: str
    helper_type: str
    suspect: str
    seed: Optional[int] = None


PLACES = {
    "museum": Place(name="the museum hall", setting="museum", affords={"smorgasbord"}),
    "school": Place(name="the school gym", setting="school", affords={"smorgasbord"}),
    "station": Place(name="the station kitchen", setting="station", affords={"smorgasbord"}),
}

DETECTIVE_NAMES = ["Milo", "Maya", "Nina", "Theo", "Luca", "Ruby", "Ivy", "Owen"]
HELPER_NAMES = ["Mrs. Finch", "Mr. Bell", "Aunt June", "Uncle Ray"]
SUSPECTS = [
    SuspectProfile("cook", "the cook", "adult", "the missing spoon", "to keep the buffet tidy"),
    SuspectProfile("student", "the student", "child", "the jam jar", "to make a sweet sandwich"),
    SuspectProfile("cat", "the cat", "animal", "the warm roll", "to nibble quietly"),
]

TOOLS = {
    "notebook": Tool("notebook", "a tiny notebook", "write down clues"),
    "lamp": Tool("lamp", "a small lamp", "see under tables"),
    "chalk": Tool("chalk", "a piece of chalk", "mark footprints"),
}

CLUES = {
    "barefoot_print": Clue("barefoot_print", "bare footprints", "the footprints were small and bare", "the buffet table"),
    "crumbs": Clue("crumbs", "crumbs", "there were crumbs leading to the side door", "the soup bowl"),
    "smorgasbord": Clue("smorgasbord", "the smorgasbord", "the buffet was set with many little dishes", "the center table"),
}

KNOWLEDGE = {
    "smorgasbord": [
        (
            "What is a smorgasbord?",
            "A smorgasbord is a table with many different foods so people can choose what they want to eat.",
        )
    ],
    "barefoot": [
        (
            "What does barefoot mean?",
            "Barefoot means not wearing shoes or socks on your feet.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks careful questions to solve a mystery.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means helping someone, sharing, or speaking gently so they feel cared for.",
        )
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world about a smorgasbord mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
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
    place = args.place or rng.choice(list(PLACES))
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    suspect = args.suspect or rng.choice([s.id for s in SUSPECTS])
    if suspect not in {s.id for s in SUSPECTS}:
        raise StoryError("Unknown suspect.")
    return StoryParams(
        place=place,
        detective=detective,
        detective_type="boy" if detective in {"Milo", "Theo", "Luca", "Owen"} else "girl",
        helper=helper,
        helper_type="adult",
        suspect=suspect,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("This story needs a valid place.")
    if params.suspect not in {s.id for s in SUSPECTS}:
        raise StoryError("This suspect cannot appear in the mystery.")


def _build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    detective = world.add(Entity(
        id=params.detective,
        kind="character",
        type=params.detective_type,
        label=params.detective,
        meters={"curiosity": 1.0, "confidence": 0.5},
        memes={"mystery": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper,
        meters={"kindness": 1.0},
        memes={"warmth": 1.0},
    ))
    suspect = next(s for s in SUSPECTS if s.id == params.suspect)
    culprit = world.add(Entity(
        id=suspect.id,
        kind="character",
        type=suspect.kind,
        label=suspect.label,
        meters={"hunger": 1.0 if suspect.id == "cat" else 0.0},
        memes={"nervous": 1.0 if suspect.id != "cat" else 0.0},
    ))
    notebook = world.add(Entity(id="notebook", type="tool", label=TOOLS["notebook"].label))
    lamp = world.add(Entity(id="lamp", type="tool", label=TOOLS["lamp"].label))
    chalk = world.add(Entity(id="chalk", type="tool", label=TOOLS["chalk"].label))
    spoon = world.add(Entity(id="spoon", type="object", label="silver spoon", owner="kitchen"))
    bowl = world.add(Entity(id="bowl", type="object", label="jam bowl", owner="table"))
    world.facts.update(
        detective=detective,
        helper=helper,
        suspect=culprit,
        tools=[notebook, lamp, chalk],
        spoon=spoon,
        bowl=bowl,
        clue_smorgasbord=CLUES["smorgasbord"],
        clue_barefoot=CLUES["barefoot_print"],
        clue_crumbs=CLUES["crumbs"],
    )
    return world


def tell(world: World) -> None:
    d: Entity = world.facts["detective"]
    h: Entity = world.facts["helper"]
    s: Entity = world.facts["suspect"]
    sm = world.facts["clue_smorgasbord"]
    fp = world.facts["clue_barefoot"]
    cr = world.facts["clue_crumbs"]

    world.say(f"{d.label} was a small detective who loved quiet mysteries.")
    world.say(f"One afternoon, {d.label} walked into {world.place.name} and saw the smorgasbord waiting in a neat row of little dishes.")
    world.say(f"{d.pronoun().capitalize()} wrote in a tiny notebook, because detectives like to notice everything.")
    world.para()

    world.say(f"Then {d.label} spotted {sm['label'] if isinstance(sm, dict) else sm.label}.")
    world.say(f"{fp.label.capitalize()} near the buffet told a story all by itself: {fp.reveal}.")
    world.say(f"\"Who walked here without shoes?\" {d.label} whispered.")
    world.say(f"\"Maybe the thief was in a hurry,\" {h.label} said kindly. \"Let's look at the crumbs too.\"")
    world.para()

    # tension: suspect found near evidence
    suspect_near = s.id == "cat"
    world.facts["suspect_near_crumbs"] = suspect_near
    world.say(f"{d.label} followed {cr.label} to the side door.")
    if suspect_near:
        world.say(f"There, {s.label} sat very still, looking guilty even though {s.pronoun()} was only licking {s.pronoun('possessive')} paws.")
    else:
        world.say(f"There, {s.label} stood beside the table, blinking fast and trying not to look at the jam bowl.")
    world.say(f"\"Did you take the spoon?\" {d.label} asked.")
    world.say(f"\"No,\" {s.pronoun().capitalize()} said. {h.label} noticed {s.pronoun('possessive')} shaky voice.")
    world.para()

    # kindness + reveal
    world.say(f"{h.label} knelt down and smiled. \"You can tell us the truth. Nobody is in trouble for being honest,\" {h.label} said.")
    if s.id == "cat":
        world.say("The cat gave a tiny mew and nudged the spoon from behind a napkin. It had been hiding there all along.")
    else:
        world.say(f"{s.label} pointed to the napkin pile and admitted the spoon had slipped there when {s.pronoun()} reached for a sweet roll.")
    world.say(f"{d.label} marked the trail with chalk, then the mystery made sense.")
    world.say(f"The barefoot footprints had come from the kitchen runner, not the suspect.")
    world.say(f"In the end, {h.label} helped return the spoon, and the smorgasbord stayed tidy for everyone.")
    world.say(f"{d.label} smiled because the case was solved with clues, questions, and kindness.")

    world.facts["resolved"] = True
    world.facts["kindness"] = True
    world.facts["barefoot"] = True


def generation_prompts(world: World) -> list[str]:
    d: Entity = world.facts["detective"]
    h: Entity = world.facts["helper"]
    return [
        'Write a child-friendly detective story about a smorgasbord and a barefoot clue.',
        f"Tell a short mystery where {d.label} asks questions, {h.label} is kind, and the barefoot footprints matter.",
        "Write a gentle detective story with dialogue, foreshadowing, and a kind ending at a smorgasbord table.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d: Entity = world.facts["detective"]
    h: Entity = world.facts["helper"]
    s: Entity = world.facts["suspect"]
    return [
        QAItem(
            question=f"Who solved the mystery in the story?",
            answer=f"{d.label} solved the mystery by noticing clues and asking careful questions.",
        ),
        QAItem(
            question=f"What clue showed that someone had walked around barefoot?",
            answer="The barefoot footprints near the buffet showed that someone had walked there without shoes.",
        ),
        QAItem(
            question=f"How did {h.label} help?",
            answer=f"{h.label} helped by speaking kindly, encouraging honesty, and helping {d.label} follow the clues.",
        ),
        QAItem(
            question=f"Who turned out to be connected to the missing spoon?",
            answer=f"{s.label} was connected to the missing spoon, but the story ends with the truth being found kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["smorgasbord", "barefoot", "detective", "kindness"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


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
        bits = []
        if e.barefoot:
            bits.append("barefoot=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.label} {' '.join(bits)}")
    lines.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="museum", detective="Milo", detective_type="boy", helper="Mrs. Finch", helper_type="adult", suspect="cook"),
    StoryParams(place="school", detective="Maya", detective_type="girl", helper="Mr. Bell", helper_type="adult", suspect="student"),
    StoryParams(place="station", detective="Ruby", detective_type="girl", helper="Aunt June", helper_type="adult", suspect="cat"),
]


ASP_RULES = r"""
place(museum). place(school). place(station).
affords(museum, smorgasbord). affords(school, smorgasbord). affords(station, smorgasbord).
keyword(smorgasbord). keyword(barefoot). keyword(detective). keyword(kindness).

compat(Place, Theme) :- affords(Place, Theme), keyword(Theme).
story(Place) :- compat(Place, smorgasbord).
#show compat/2.
#show story/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("affords", pid, "smorgasbord"))
    for k in ["smorgasbord", "barefoot", "detective", "kindness"]:
        lines.append(asp.fact("keyword", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compat/2."))
    clingo_set = set(asp.atoms(model, "compat"))
    py_set = {(p, "smorgasbord") for p in PLACES}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(py_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story/1."))
    return sorted(set(asp.atoms(model, "story")))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = _build_world(params)
    tell(world)
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
        print(asp_program("#show story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show story/1."))
        print(sorted(set(asp.atoms(model, "story"))))
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
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.detective} at {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
