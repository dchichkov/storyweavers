#!/usr/bin/env python3
"""
pesto_happy_ending_detective_story.py
=====================================

A small detective-style story world about a missing jar of pesto, a careful
search, and a happy ending.

Seed tale:
---
Detective Mina loved quiet clues, shiny notebook pages, and helping neighbors.
One afternoon, Mrs. Bell asked Mina to find the missing jar of pesto for the
big supper. Mina searched the kitchen, the pantry, and the hallway. She noticed
green smudges on a spoon, a trail of basil leaves, and tiny footprints near the
back door. The clues led Mina to the garden shed, where the chef's helper had
put the pesto aside so it would stay cold. Mina returned the pesto, everyone
laughed, and the supper became a happy celebration.

This world turns that tale into a small simulation:
- a missing item with physical location and ownership,
- clues that can be collected by a detective,
- a suspect who may have moved the item for a good reason,
- a turn where the clues reveal the truth,
- and a happy ending where the jar is found and dinner is saved.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

DETECTIVE_TRAITS = ["careful", "curious", "kind", "brave", "patient", "sharp-eyed"]
DETECTIVE_NAMES = ["Mina", "Nora", "Ivy", "Leo", "Tess", "Arlo", "June", "Rory"]
OWNER_NAMES = ["Mrs. Bell", "Mr. Finch", "Aunt Rosa", "Chef Daria", "Grandpa Sam"]
HELPER_NAMES = ["Theo", "Lina", "Pip", "Mara", "Jules", "Finn"]
LOCATIONS = ["kitchen", "pantry", "hallway", "garden shed", "cool cupboard", "back porch"]
HAPPY_ENDINGS = [
    "everyone sat down to a warm supper",
    "the table filled with smiles and clapping",
    "the family shared the meal with happy faces",
]

CLUE_KINDS = {
    "green_smudge": "a green smudge",
    "basil_leaf": "a little basil leaf",
    "tiny_footprints": "tiny footprints",
    "cool_breeze": "a cool breeze",
}

ASP_RULES = r"""
% A jar is missing when it is not in the kitchen and not in the detective's hand.
missing(J) :- jar(J), located(J, L), L != kitchen, not held(J).

% A clue is visible if it points toward the true hiding place.
relevant(C) :- clue(C), points_to(C, L), located(J, L), jar(J), missing(J).

% A good ending happens when the jar is found and returned to the owner.
happy_end :- found(J), returned(J), jar(J), owned_by(J, O), owner(O).

% The detective can solve the case only if enough relevant clues exist.
solved :- 3 { seen(C) : relevant(C) }.
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    location: str = ""
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    helper: object | None = None
    jar: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Clue:
    id: str
    label: str
    points_to: str
    seen: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    detective_name: str
    detective_trait: str
    owner_name: str
    helper_name: str
    location: str
    seed: Optional[int] = None
    params: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class World:
    detective: Entity
    owner: Entity
    helper: Entity
    jar: Entity
    clues: list[Clue]
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world about pesto and a happy ending.")
    ap.add_argument("--detective-name", choices=DETECTIVE_NAMES)
    ap.add_argument("--detective-trait", choices=DETECTIVE_TRAITS)
    ap.add_argument("--owner-name", choices=OWNER_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--location", choices=LOCATIONS)
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.location not in {"garden shed", "cool cupboard", "back porch"}:
        pass
    if params.detective_name == params.helper_name:
        pass
    if params.owner_name == params.helper_name:
        pass
    if params.owner_name == params.detective_name:
        pass


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("jar", "pesto"))
    lines.append(asp.fact("owned_by", "pesto", "owner"))
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
    lines.append(asp.fact("located", "pesto", "hidden_place"))
    lines.append(asp.fact("clue", "smudge"))
    lines.append(asp.fact("points_to", "smudge", "hidden_place"))
    lines.append(asp.fact("clue", "leaf"))
    lines.append(asp.fact("points_to", "leaf", "hidden_place"))
    lines.append(asp.fact("clue", "footprints"))
    lines.append(asp.fact("points_to", "footprints", "hidden_place"))
    lines.append(asp.fact("seen", "smudge"))
    lines.append(asp.fact("seen", "leaf"))
    lines.append(asp.fact("seen", "footprints"))
    lines.append(ASP_RULES)
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/0.\n#show solved/0."))
    atoms = {a.name for a in model}
    if {"happy_end", "solved"} <= atoms:
        print("OK: ASP rules support a solved happy-ending pesto case.")
        return 0
    print("MISMATCH: ASP verification failed.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        detective_name=getattr(args, "detective_name", None) or rng.choice(DETECTIVE_NAMES),
        detective_trait=getattr(args, "detective_trait", None) or rng.choice(DETECTIVE_TRAITS),
        owner_name=getattr(args, "owner_name", None) or rng.choice(OWNER_NAMES),
        helper_name=getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES),
        location=getattr(args, "location", None) or rng.choice(LOCATIONS),
    )
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    detective = Entity(
        id="detective",
        kind="character",
        type="girl" if params.detective_name in {"Mina", "Nora", "Ivy", "Tess", "June"} else "boy",
        label=params.detective_name,
        location="street",
    )
    owner = Entity(
        id="owner",
        kind="character",
        type="woman" if "Mrs." in params.owner_name or "Aunt" in params.owner_name else "man",
        label=params.owner_name,
        location="home",
    )
    helper = Entity(
        id="helper",
        kind="character",
        type="boy" if params.helper_name in {"Theo", "Pip", "Finn", "Jules", "Arlo", "Leo", "Rory"} else "girl",
        label=params.helper_name,
        location=params.location,
    )
    jar = Entity(
        id="pesto",
        kind="thing",
        type="jar",
        label="jar of pesto",
        owner=owner.id,
        location=params.location,
    )
    clues = [
        Clue("smudge", CLUE_KINDS["green_smudge"], params.location),
        Clue("leaf", CLUE_KINDS["basil_leaf"], params.location),
        Clue("footprints", CLUE_KINDS["tiny_footprints"], params.location),
    ]
    return World(detective=detective, owner=owner, helper=helper, jar=jar, clues=clues)


def narrate(world: World, params: StoryParams) -> None:
    d = world.detective
    o = world.owner
    h = world.helper
    jar = world.jar

    world.say(f"{d.label} was a {params.detective_trait} detective who liked quiet clues and neat notebook pages.")
    world.say(f"One afternoon, {o.label} said that the jar of pesto was missing from the kitchen.")
    world.para()
    world.say(f"{d.label} looked in the kitchen, then the pantry, and then the hallway.")
    world.say("A green smudge on a spoon, a basil leaf near the floor, and tiny footprints gave the case a path to follow.")
    world.say(f"The trail led to the {params.location}, where {h.label} had tucked the pesto away.")
    world.para()
    world.say(f"{h.label} explained that the jar had been moved so it would stay cool until supper.")
    world.say(f"{d.label} smiled, carried the pesto back, and {o.label} thanked everyone for finding it.")
    world.say(f"In the end, {random.choice(HAPPY_ENDINGS)}, with the pesto ready for dinner and the whole house feeling bright.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.facts.update(
        detective=world.detective,
        owner=world.owner,
        helper=world.helper,
        jar=world.jar,
        clues=world.clues,
        params=params,
    )
    narrate(world, params)
    prompts = [
        "Write a short detective story for a child about a missing jar of pesto and a happy ending.",
        f"Tell a gentle mystery where {params.detective_name} follows clues to find pesto for {params.owner_name}.",
        "Write a simple story with clues, a careful search, and supper saved by finding the pesto.",
    ]
    story_qa = [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {world.detective.label}, a {params.detective_trait} helper who followed the clues.",
        ),
        QAItem(
            question=f"Why was the pesto missing?",
            answer=f"The pesto had been moved to the {params.location} so it could stay cool until supper.",
        ),
        QAItem(
            question="What clues helped solve the case?",
            answer="A green smudge, a basil leaf, and tiny footprints pointed the detective toward the hiding place.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The pesto was brought back, everyone was happy, and supper turned into a cheerful celebration.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is pesto?",
            answer="Pesto is a green sauce or paste made from basil, oil, cheese, and nuts, and people often put it on food.",
        ),
        QAItem(
            question="Why are detectives careful?",
            answer="Detectives are careful because clues can be small, and looking closely helps them understand what happened.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(sample: StorySample) -> str:
    w = sample.world
    lines = ["--- world trace ---"]
    lines.append(f"detective={w.detective.label} trait={sample.params.detective_trait}")
    lines.append(f"owner={w.owner.label}")
    lines.append(f"helper={w.helper.label} location={w.helper.location}")
    lines.append(f"jar_location={w.jar.location}")
    lines.append(f"clues={[c.label for c in w.clues]}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample))
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("Mina", "careful", "Mrs. Bell", "Theo", "garden shed"),
        StoryParams("Nora", "sharp-eyed", "Aunt Rosa", "Lina", "cool cupboard"),
        StoryParams("Leo", "curious", "Chef Daria", "Pip", "back porch"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/0.\n#show happy_end/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show solved/0.\n#show happy_end/0."))
        print("ASP model atoms:")
        for atom in model:
            print(atom)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in curated_params()]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        i = 0
        seen: set[str] = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
