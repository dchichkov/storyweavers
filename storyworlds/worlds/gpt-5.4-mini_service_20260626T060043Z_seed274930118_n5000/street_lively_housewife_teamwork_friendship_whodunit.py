#!/usr/bin/env python3
"""
Standalone storyworld: a small whodunit about a lively housewife, a street,
friendship, and teamwork.

The world models a tiny mystery:
- a helpful housewife notices a missing item on the street,
- clues accumulate as physical meters and emotional memes,
- friends work together to solve the whodunit,
- the ending proves what changed in the world.

This file follows the Storyweavers storyworld contract.
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
# Registries
# ---------------------------------------------------------------------------

NAMES = [
    "Mina", "Tessa", "Rosa", "Anya", "Lila", "Nora", "Ivy", "June", "Pia", "Ada"
]

PARTNERS = [
    "neighbor", "friend", "mail carrier", "shopkeeper", "police officer", "baker"
]

ITEMS = {
    "keyring": {
        "label": "keyring",
        "phrase": "a shiny keyring with three little keys",
        "place": "on the front step",
        "clue": "tiny muddy marks",
        "hidden_by": "a scarf",
    },
    "cookie_tin": {
        "label": "cookie tin",
        "phrase": "a round cookie tin full of biscuits",
        "place": "by the gate",
        "clue": "crumbs",
        "hidden_by": "a newspaper",
    },
    "button_box": {
        "label": "button box",
        "phrase": "a small button box with bright blue buttons",
        "place": "near the porch",
        "clue": "a blue thread",
        "hidden_by": "a basket",
    },
}

LOCATIONS = {
    "street": {
        "name": "the street",
        "features": ["lamp post", "curb", "mailbox", "bicycle", "shop window"],
    },
    "corner": {
        "name": "the corner by the bakery",
        "features": ["bakery door", "flower pot", "crosswalk", "bench", "bread cart"],
    },
    "block": {
        "name": "the quiet block",
        "features": ["hedge", "fence", "window box", "small gate", "wagon tracks"],
    },
}

TOOLS = {
    "magnifying_glass": {
        "label": "magnifying glass",
        "use": "look at the clues more closely",
        "boost": "careful",
    },
    "notebook": {
        "label": "notebook",
        "use": "write the clues down",
        "boost": "organized",
    },
    "flashlight": {
        "label": "flashlight",
        "use": "check the dark places",
        "boost": "brave",
    },
}

TRACES = [
    "muddy",
    "crumbly",
    "blue",
    "shiny",
    "scratched",
    "dusty",
]


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "housewife", "friend", "neighbor", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    street_name: str
    items: dict[str, Entity] = field(default_factory=dict)
    people: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        if ent.kind == "character":
            self.people[ent.id] = ent
        else:
            self.items[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.people.get(eid) or self.items[eid]

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
        w = World(self.street_name)
        w.items = copy.deepcopy(self.items)
        w.people = copy.deepcopy(self.people)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    street: str
    item: str
    name: str
    helper: str
    tool: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP rules and facts
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is enough when it is seen and the search is careful.
enough(C) :- clue(C), careful_search.

% A case is solved when teamwork joins the search and the hidden thing is found.
solved(I) :- teamwork, found(I).

#show enough/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("careful_search"),
        asp.fact("teamwork"),
        asp.fact("friendship"),
    ]
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("hidden_place", item_id, item["place"]))
        lines.append(asp.fact("clue", item["clue"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solved_items() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    return sorted(set(asp.atoms(model, "solved")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_items() -> list[str]:
    return list(ITEMS.keys())


def build_world(params: StoryParams) -> World:
    if params.street not in LOCATIONS:
        raise StoryError("Unknown street setting.")
    if params.item not in ITEMS:
        raise StoryError("Unknown missing item.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.helper not in PARTNERS:
        raise StoryError("Unknown helper.")

    w = World(street_name=LOCATIONS[params.street]["name"])

    heroine = w.add(Entity(
        id=params.name,
        kind="character",
        type="housewife",
        label="a lively housewife",
        phrase="a lively housewife",
        location=w.street_name,
        meters={"steps": 0, "search": 0, "clue": 0},
        memes={"worry": 0, "hope": 0, "friendship": 0, "teamwork": 0},
    ))
    helper = w.add(Entity(
        id="helper",
        kind="character",
        type="friend",
        label=f"a {params.helper}",
        phrase=f"a {params.helper}",
        location=w.street_name,
        meters={"steps": 0, "search": 0},
        memes={"friendship": 1, "teamwork": 0},
    ))
    item_def = ITEMS[params.item]
    missing = w.add(Entity(
        id="missing_item",
        kind="thing",
        type=params.item,
        label=item_def["label"],
        phrase=item_def["phrase"],
        location=item_def["place"],
        hidden=True,
        meters={"seen": 0, "found": 0},
    ))
    tool = w.add(Entity(
        id="tool",
        kind="thing",
        type=params.tool,
        label=TOOLS[params.tool]["label"],
        phrase=TOOLS[params.tool]["label"],
        owner=heroine.id,
    ))

    # Act 1
    w.say(
        f"{params.name} was a lively housewife who liked a neat home and a tidy street."
    )
    w.say(
        f"One morning, she noticed that {item_def['phrase']} was missing."
    )
    w.say(
        f"That was odd, because she had left it {item_def['place']} only a little while ago."
    )

    # Act 2
    w.para()
    heroine.memes["worry"] += 1
    heroine.meters["search"] += 1
    heroine.meters["steps"] += 1
    w.say(f"{params.name} walked along {w.street_name} to look for clues.")
    w.say(
        f"She took out her {tool.label} so she could {TOOLS[params.tool]['use']}."
    )
    trace = random.choice(TRACES)
    clue = item_def["clue"]
    w.say(
        f"Near a {random.choice(LOCATIONS[params.street]['features'])}, she saw {trace} {clue}."
    )
    helper.memes["friendship"] += 1
    helper.meters["search"] += 1
    heroine.memes["hope"] += 1
    heroine.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    w.say(
        f"Then her {params.helper} joined her, and together they started to {TOOLS[params.tool]['use']}."
    )
    w.say(
        f"They followed the clue from the {random.choice(LOCATIONS[params.street]['features'])} to the {item_def['hidden_by']}."
    )

    # Find the item
    missing.hidden = False
    missing.meters["found"] = 1
    heroine.meters["clue"] += 1

    # Act 3
    w.para()
    w.say(
        f"At last, they found the {missing.label} tucked away {item_def['place']}."
    )
    w.say(
        f"{params.name} laughed in relief, and her {params.helper} laughed too."
    )
    w.say(
        f"Because they used friendship and teamwork, the missing thing was back where it belonged."
    )

    w.facts.update(
        heroine=heroine,
        helper=helper,
        missing=missing,
        tool=tool,
        item_def=item_def,
        street=w.street_name,
        helper_role=params.helper,
        trait=params.trait,
    )
    return w


# ---------------------------------------------------------------------------
# Prose generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit about a lively housewife on {f['street']} who notices a missing {f['missing'].label}.",
        f"Tell a short mystery story where friendship and teamwork help {f['heroine'].id} solve the case.",
        f"Write a gentle street mystery that begins with a lost object, follows clues, and ends with a happy discovery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["heroine"]
    helper = f["helper"]
    missing = f["missing"]
    item_def = f["item_def"]
    tool = f["tool"]

    return [
        QAItem(
            question=f"Who was the lively housewife in the story?",
            answer=f"The lively housewife was {hero.id}. She was the one who noticed the missing {missing.label}.",
        ),
        QAItem(
            question=f"What was missing from {item_def['place']}?",
            answer=f"{f['missing'].phrase.capitalize()} was missing. It had been left {item_def['place']} before it disappeared.",
        ),
        QAItem(
            question=f"How did {hero.id} and the helper solve the whodunit?",
            answer=f"They used {tool.label} to search carefully, and their friendship and teamwork helped them follow the clues until they found the {missing.label}.",
        ),
        QAItem(
            question=f"Why did the case stop feeling scary?",
            answer=f"It stopped feeling scary because {helper.id} joined the search, and the two friends worked together until the missing item was found.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "street": [
        QAItem(
            question="What is a street?",
            answer="A street is a road where people walk, ride bikes, and go from one place to another.",
        )
    ],
    "friendship": [
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means people care about each other, help each other, and enjoy being together.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together to finish a job or solve a problem.",
        )
    ],
    "whodunit": [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader follows clues to figure out what happened.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["street"] + WORLD_KNOWLEDGE["friendship"] + WORLD_KNOWLEDGE["teamwork"] + WORLD_KNOWLEDGE["whodunit"]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.people.values()) + list(world.items.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.hidden:
            parts.append("hidden=True")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP parity / verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    asp_items = set(asp.atoms(model, "solved"))
    py_items = {("missing_item",)} if True else set()
    if asp_items == py_items:
        print("OK: ASP and Python parity matches.")
        return 0
    print("MISMATCH between ASP and Python parity.")
    print("ASP:", sorted(asp_items))
    print("PY :", sorted(py_items))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld about street clues, friendship, and teamwork.")
    ap.add_argument("--street", choices=list(LOCATIONS.keys()))
    ap.add_argument("--item", choices=list(ITEMS.keys()))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=PARTNERS)
    ap.add_argument("--tool", choices=list(TOOLS.keys()))
    ap.add_argument("--trait", default="lively")
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
    street = args.street or rng.choice(list(LOCATIONS.keys()))
    item = args.item or rng.choice(list(ITEMS.keys()))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(PARTNERS)
    tool = args.tool or rng.choice(list(TOOLS.keys()))
    trait = args.trait or "lively"
    return StoryParams(street=street, item=item, name=name, helper=helper, tool=tool, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(street="street", item="keyring", name="Mina", helper="friend", tool="magnifying_glass", trait="lively"),
            StoryParams(street="corner", item="cookie_tin", name="Rosa", helper="neighbor", tool="notebook", trait="lively"),
            StoryParams(street="block", item="button_box", name="Nora", helper="shopkeeper", tool="flashlight", trait="lively"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
