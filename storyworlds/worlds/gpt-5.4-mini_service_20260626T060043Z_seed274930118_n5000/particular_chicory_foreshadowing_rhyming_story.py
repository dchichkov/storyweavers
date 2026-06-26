#!/usr/bin/env python3
"""
A standalone storyworld for a small rhyming tale with foreshadowing:
a particular little helper, a chicory ingredient, a small worry, and a
gentle turn toward a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

RHYME_ENDINGS = {
    "mild": "light",
    "bright": "night",
    "bloom": "room",
    "stir": "whir",
    "keep": "sleep",
    "glow": "snow",
}

NAME_PAIRS = [
    ("Mina", "girl"),
    ("Toby", "boy"),
    ("Nora", "girl"),
    ("Ezra", "boy"),
    ("Lumi", "girl"),
    ("Pip", "boy"),
]

NARRATIVE_BEATS = ["setup", "foreshadow", "worry", "turn", "ending"]


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True


@dataclass
class Ingredient:
    id: str
    label: str
    phrase: str
    smell: str
    color: str
    mood: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str


@dataclass
class StoryParams:
    place: str
    ingredient: str
    tool: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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


PLACES = {
    "kitchen": Place("the kitchen", indoors=True),
    "pantry": Place("the pantry", indoors=True),
    "garden_table": Place("the garden table", indoors=False),
}

INGREDIENTS = {
    "chicory": Ingredient(
        id="chicory",
        label="chicory",
        phrase="a little bowl of chicory",
        smell="earthy",
        color="brown",
        mood="plain",
    ),
    "honey": Ingredient(
        id="honey",
        label="honey",
        phrase="a tiny jar of honey",
        smell="sweet",
        color="gold",
        mood="warm",
    ),
    "berries": Ingredient(
        id="berries",
        label="berries",
        phrase="a bright cup of berries",
        smell="fruity",
        color="red",
        mood="cheery",
    ),
}

TOOLS = {
    "spoon": Tool(id="spoon", label="spoon", phrase="a little silver spoon", helps="stir"),
    "ladle": Tool(id="ladle", label="ladle", phrase="a curved wooden ladle", helps="scoop"),
    "mug": Tool(id="mug", label="mug", phrase="a sturdy mug", helps="hold"),
}

HELPERS = {
    "grandma": ("grandma", "mother"),
    "grandpa": ("grandpa", "father"),
    "aunt": ("aunt", "woman"),
    "uncle": ("uncle", "man"),
}


def rhyme(word: str) -> str:
    return RHYME_ENDINGS.get(word, word)


def make_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def story_name(ent: Entity) -> str:
    return ent.id


def foreshadow(world: World, child: Entity, ingredient: Ingredient, tool: Tool) -> None:
    child.memes["curious"] = child.memes.get("curious", 0) + 1
    world.say(
        f"{child.id} was a particular sort of little one, with eyes that shone so bright; "
        f"{child.pronoun().capitalize()} liked to peek at pots and peek again by night."
    )
    world.say(
        f"{child.id} found the chicory, brown and plain, and gave a thoughtful sigh; "
        f"the smell was earthy in the air, like leaves that had gone dry."
    )
    world.say(
        f"{child.pronoun().capitalize()} picked up {tool.phrase} and gave it a tiny spin; "
        f"that little spoon looked ready to stir, but trouble could creep in."
    )
    world.facts["foreshadowed"] = True


def warn(world: World, helper: Entity, child: Entity, ingredient: Ingredient) -> None:
    world.say(
        f'"Go gentle," {helper.id} said, "for chicory can scatter fast; '
        f'if it spills across the table, the clean white cloth won't last."'
    )
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.facts["worry"] = True
    world.facts["spill_risk"] = ingredient.id == "chicory"


def misstep(world: World, child: Entity, ingredient: Ingredient, tool: Tool) -> None:
    child.meters["mess"] = child.meters.get("mess", 0) + 1
    world.say(
        f"{child.id} tried to stir too quick, and the spoon made a whir-whir whirr; "
        f"the chicory dust rose like a cloud, a soft brown blur and burr."
    )
    world.say(
        f"A little puff flew to the cloth and dotted it with specks; "
        f"the tidy table now looked like it had tiny freckles on its decks."
    )
    world.facts["spill"] = True


def turn(world: World, helper: Entity, child: Entity, ingredient: Ingredient, tool: Tool) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.say(
        f"Then {helper.id} smiled and set a lid upon the bowl to keep; "
        f"\"Let's slow the stir and use the spoon the careful way,\" {helper.id} said sweetly, not to sleep."
    )
    world.say(
        f"{child.id} nodded, small and brave, and learned a safer dance; "
        f"{tool.phrase} went round and round, and every grain had chance."
    )
    world.facts["turn"] = True


def ending(world: World, child: Entity, helper: Entity, ingredient: Ingredient, tool: Tool) -> None:
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(
        f"In the end the chicory stayed mostly in the bowl, and the drink gave a cozy glow; "
        f"{child.id} sipped it by the window while the pale afternoon began its snow."
    )
    world.say(
        f"The table was wiped, the cloth was clean, and the little kitchen sang; "
        f"{child.id} had learned that slow and sure makes happy rhymes that rang."
    )
    world.facts["ending_clean"] = True


def build_story(world: World, child: Entity, helper: Entity, ingredient: Ingredient, tool: Tool) -> None:
    foreshadow(world, child, ingredient, tool)
    world.para()
    warn(world, helper, child, ingredient)
    misstep(world, child, ingredient, tool)
    world.para()
    turn(world, helper, child, ingredient, tool)
    ending(world, child, helper, ingredient, tool)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ingredient = f["ingredient"]
    return [
        f'Write a short rhyming story for a young child about {child.id}, {ingredient.label}, and a careful fix.',
        f'Tell a gentle foreshadowing story where {child.id} gets curious about {ingredient.phrase} and {helper.id} helps.',
        f'Write a simple story that includes the word "particular" and ends with a clean table and a calm smile.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    ingredient = f["ingredient"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {child.id}, a {child.type} who was particular and curious.",
        ),
        QAItem(
            question=f"What ingredient made the little problem start?",
            answer=f"The little problem started with {ingredient.label}, which was light and dusty enough to scatter.",
        ),
        QAItem(
            question=f"Who helped {child.id} keep things calm?",
            answer=f"{helper.id} helped by warning {child.id} to go slowly and use {tool.label} carefully.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the table was clean, the chicory stayed in the bowl, and {child.id} felt proud and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chicory?",
            answer="Chicory is a plant with a root that can be dried and used to make a warm, earthy drink.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small clue early on that helps you guess what might happen later.",
        ),
        QAItem(
            question="Why should people stir carefully when something dusty is in a bowl?",
            answer="Because dusty things can puff up or spill, and careful stirring helps keep the mess small.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if bits:
            lines.append(f"{e.id}: " + ", ".join(bits))
        else:
            lines.append(f"{e.id}:")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
foreshadowed :- curious(child).
spill_risk :- ingredient(chicory).
problem :- foreshadowed, spill_risk.
resolved :- problem, careful(turn).
#show foreshadowed/0.
#show spill_risk/0.
#show problem/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    parts = [
        asp.fact("curious", "child"),
        asp.fact("ingredient", "chicory"),
        asp.fact("careful", "turn"),
    ]
    return "\n".join(parts)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    shown = {sym.name for sym in model}
    expected = {"foreshadowed", "spill_risk", "problem", "resolved"}
    if shown == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected story-state symbols.")
    print("got:", sorted(shown))
    print("expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld with foreshadowing and chicory.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ingredient", choices=INGREDIENTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    ingredient = args.ingredient or "chicory"
    tool = args.tool or "spoon"
    place = args.place or "kitchen"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name
    if not name:
        name = rng.choice([n for n, g in NAME_PAIRS if g == gender])
    helper = args.helper or "grandma"
    if ingredient != "chicory":
        raise StoryError("This world is built around chicory; please choose --ingredient chicory.")
    if tool not in TOOLS:
        raise StoryError("Unknown tool.")
    return StoryParams(place=place, ingredient=ingredient, tool=tool, name=name, gender=gender, helper=helper)


def validate_params(params: StoryParams) -> None:
    if params.ingredient != "chicory":
        raise StoryError("This world needs chicory.")
    if params.tool not in TOOLS:
        raise StoryError("The tool must be one of the registered tools.")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = World(PLACES[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["particular", "curious"]))
    helper_type = HELPERS[params.helper][1]
    helper = world.add(Entity(id=params.helper, kind="character", type=helper_type))
    ingredient = INGREDIENTS[params.ingredient]
    tool = TOOLS[params.tool]
    child.meters["care"] = 1
    world.facts = {"child": child, "helper": helper, "ingredient": ingredient, "tool": tool}
    world.say(
        f"{child.id} was particular and bright, and liked to work just so; "
        f"the tidy little kitchen was the kind of place where careful stories grow."
    )
    build_story(world, child, helper, ingredient, tool)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="kitchen", ingredient="chicory", tool="spoon", name="Mina", gender="girl", helper="grandma"),
    StoryParams(place="pantry", ingredient="chicory", tool="ladle", name="Toby", gender="boy", helper="grandpa"),
    StoryParams(place="garden_table", ingredient="chicory", tool="mug", name="Lumi", gender="girl", helper="aunt"),
]


def asp_verify_gate() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {sym.name for sym in model}
    expected = {"foreshadowed", "spill_risk", "problem", "resolved"}
    return 0 if names == expected else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(sorted(sym.name for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
