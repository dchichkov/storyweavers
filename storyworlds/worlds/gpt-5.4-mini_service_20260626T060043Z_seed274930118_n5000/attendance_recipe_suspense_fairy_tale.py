#!/usr/bin/env python3
"""
storyworlds/worlds/attendance_recipe_suspense_fairy_tale.py
===========================================================

A small fairy-tale storyworld about attendance, a secret recipe, and a suspenseful
race to finish a feast before the bell rings.

Premise:
- A young steward must take attendance for a royal gathering.
- The gathering depends on a recipe that must be followed exactly.
- Something is missing, and the missing thing creates suspense.
- A helper or parent figure guides the child toward a safe, happy ending.

The world model tracks:
- physical meters: distance, hunger, dryness, steam, ink, brightness
- emotional memes: worry, hope, courage, relief, affection, suspense

The story is generated from simulated state rather than swapped nouns:
- the attendance list may be incomplete
- the recipe may be incomplete or misplaced
- the hero may have to search, ask, and then resolve the problem

This file is standalone and follows the Storyweavers world contract.
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
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "princess", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "prince", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Recipe:
    id: str
    label: str
    dish: str
    missing_step: str
    rescue: str
    ingredient: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.recipe_found = False
        self.attendance_complete = False
        self.suspense = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.recipe_found = self.recipe_found
        w.attendance_complete = self.attendance_complete
        w.suspense = self.suspense
        return w


SETTINGS = {
    "castle": Setting(place="the castle hall", indoor=True, affords={"feast", "counting"}),
    "cottage": Setting(place="the little cottage kitchen", indoor=True, affords={"baking", "counting"}),
    "garden": Setting(place="the moonlit garden", indoor=False, affords={"feast", "counting"}),
}

ACTIVITIES = {
    "feast": Activity(
        id="feast",
        verb="serve the feast",
        gerund="serving the feast",
        rush="hurry to the tables",
        risk="the feast could stay unfinished and cold",
        zone={"torso"},
        keyword="feast",
        tags={"feast", "hot"},
    ),
    "baking": Activity(
        id="baking",
        verb="bake the cake",
        gerund="baking the cake",
        rush="hurry to the oven",
        risk="the batter could burn or go missing",
        zone={"torso", "hands"},
        keyword="recipe",
        tags={"recipe", "cake"},
    ),
    "counting": Activity(
        id="counting",
        verb="call the guests",
        gerund="calling the guests",
        rush="run to the doorway",
        risk="someone might be left out of attendance",
        zone={"head"},
        keyword="attendance",
        tags={"attendance", "guests"},
    ),
}

PRIZES = {
    "ledger": Prize(
        label="attendance ledger",
        phrase="a neat attendance ledger with gold corners",
        type="ledger",
    ),
    "scroll": Prize(
        label="recipe scroll",
        phrase="a secret recipe scroll tied with blue ribbon",
        type="scroll",
    ),
    "cake": Prize(
        label="cake",
        phrase="a tall cake with sugared roses",
        type="cake",
        genders={"girl", "boy"},
    ),
}

RECIPES = {
    "mooncake": Recipe(
        id="mooncake",
        label="mooncake recipe",
        dish="mooncake",
        missing_step="the final whisper of vanilla",
        rescue="add the missing vanilla and stir three more times",
        ingredient="vanilla",
        tags={"recipe", "cake", "moon"},
    ),
    "berrytart": Recipe(
        id="berrytart",
        label="berry tart recipe",
        dish="berry tart",
        missing_step="the jam had not been warmed",
        rescue="warm the jam and pour it gently over the crust",
        ingredient="jam",
        tags={"recipe", "berries"},
    ),
    "honeybun": Recipe(
        id="honeybun",
        label="honey bun recipe",
        dish="honey bun",
        missing_step="the honey had not been stirred in",
        rescue="stir in the honey and let the dough rest",
        ingredient="honey",
        tags={"recipe", "honey"},
    ),
}

HERO_NAMES = ["Elsa", "Mina", "Rose", "Lily", "Nora", "Clara"]
HELPER_NAMES = ["the queen", "the baker", "the old mouse", "the kind king"]
TRAITS = ["brave", "gentle", "careful", "curious", "patient", "small"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    recipe: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                for recipe_id in RECIPES:
                    if act_id == "counting" and prize_id == "ledger":
                        combos.append((place, act_id, prize_id, recipe_id))
                    if act_id == "baking" and prize_id in {"scroll", "cake"}:
                        combos.append((place, act_id, prize_id, recipe_id))
                    if act_id == "feast" and prize_id in {"ledger", "scroll"}:
                        combos.append((place, act_id, prize_id, recipe_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld of attendance, recipe, and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["queen", "baker", "mouse", "king"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.recipe is None or c[3] == args.recipe)]
    if not combos:
        raise StoryError("No valid fairy-tale combination matches the given options.")

    place, activity, prize, recipe = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(["queen", "baker", "mouse", "king"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, recipe=recipe,
                       name=name, gender=gender, helper=helper, trait=trait)


def _hero_type(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=_hero_type(params.gender),
                            traits=["little", params.trait], meters={"hope": 0.0}, memes={"worry": 0.0}))
    helper_type = {"queen": "queen", "baker": "woman", "mouse": "thing", "king": "king"}[params.helper]
    helper_label = {"queen": "the queen", "baker": "the baker", "mouse": "the old mouse", "king": "the king"}[params.helper]
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_label,
                              meters={"calm": 0.0}, memes={"affection": 0.0}))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label,
                             phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=helper.id))
    recipe = RECIPES[params.recipe]

    world.say(f"Once in {world.setting.place}, little {params.name} was a {params.trait} child who kept careful attendance at every feast.")
    world.say(f"{params.name} loved the {recipe.label} because it promised {recipe.dish}, sweet as a story told beside a fire.")
    world.say(f"{params.name}'s {helper_label} kept a {prize.label} near the table, because the royal meal depended on it.")

    world.lines.append("")
    if params.activity == "counting":
        hero.memes["worry"] += 1
        world.say(f"But when the bells began to ring, the attendance ledger was not on the shelf.")
        world.say(f"{params.name} searched the doorway, and the hallway seemed to hold its breath.")
        world.say(f"{helper_label.capitalize()} said, 'Without the attendance list, someone may be missed.'")
        world.say(f"That made the little {params.gender} feel suspense prickling in the dark corners.")
    elif params.activity == "baking":
        hero.memes["worry"] += 1
        world.say(f"But when the oven glowed, the recipe scroll was missing from the sugar tin.")
        world.say(f"{params.name} opened one drawer after another, while the kitchen stayed very still.")
        world.say(f"{helper_label.capitalize()} whispered, 'If the scroll stays lost, the cake may fail.'")
        world.say(f"The room felt full of suspense, like a candle flickering in a draft.")
    else:
        hero.memes["worry"] += 1
        world.say(f"But while the moon rose, the guests had not been counted, and the feast could not begin.")
        world.say(f"{params.name} held the attendance ledger close and saw that the recipe scroll was tucked behind it.")
        world.say(f"{helper_label.capitalize()} paused and said, 'First the list, then the feast, dear one.'")
        world.say(f"The waiting made even the spoon rack seem quiet and suspenseful.")

    world.lines.append("")
    if params.activity == "counting":
        world.say(f"At last, {params.name} found the attendance ledger under a silver napkin.")
        world.say(f"{params.name} read the names aloud, one by one, and the missing laughter returned to the hall.")
        world.say(f"Then the {prize.label} helped the guests sit in their places, and the feast could begin.")
    elif params.activity == "baking":
        world.say(f"At last, {params.name} found the recipe scroll in the flour jar.")
        world.say(f"{params.name} followed the recipe step by step: {recipe.missing_step}, and then {recipe.rescue}.")
        world.say(f"The oven gave a warm hum, and the {prize.label} came out golden and proud.")
    else:
        world.say(f"At last, {params.name} finished the attendance list and saw every guest was present.")
        world.say(f"Then the {helper_label} uncovered the recipe scroll, and the kitchen grew bright with relief.")
        world.say(f"Together they served the feast, and the {prize.label} rested safely beside the plates.")

    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 1.0
    helper.memes["affection"] = 1.0
    world.facts = {
        "hero": hero,
        "helper": helper,
        "prize": prize,
        "recipe": recipe,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f"Write a fairy tale about {p.name}, attendance at {world.setting.place}, and a missing recipe.",
        f"Tell a suspenseful story where a little {p.gender} must keep attendance and save a recipe before the feast begins.",
        f"Write a child-friendly fairy tale with a secret recipe, a worried helper, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    recipe = f["recipe"]
    helper = f["helper"].label_word
    prize = f["prize"].label
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about little {p.name}, a {p.trait} child in {world.setting.place}."
        ),
        QAItem(
            question=f"What was missing that made the story suspenseful?",
            answer=f"The missing thing was the {recipe.label}. Without it, the feast could not be finished the right way."
        ),
        QAItem(
            question=f"How did the problem get solved?",
            answer=f"{p.name} found the missing {recipe.label}, followed the steps carefully, and then the {helper} could help finish everything."
        ),
        QAItem(
            question=f"What important list did {p.name} keep?",
            answer=f"{p.name} kept the attendance ledger, so the guests could be counted and nobody would be left out."
        ),
        QAItem(
            question=f"What stayed safe at the end?",
            answer=f"The {prize} stayed safe, and the feast ended with relief instead of worry."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    recipe = world.facts["recipe"]
    return [
        QAItem(
            question="What is attendance?",
            answer="Attendance is a count or list of who is present, so everyone can be noticed and nobody is forgotten."
        ),
        QAItem(
            question="What is a recipe?",
            answer="A recipe is a set of directions that tells you how to make food step by step."
        ),
        QAItem(
            question="Why can a missing recipe cause trouble?",
            answer="If a recipe is missing, the cook may not know the right steps or ingredients, so the food might not turn out well."
        ),
        QAItem(
            question=f"Why was the {recipe.label} helpful?",
            answer=f"The {recipe.label} gave the exact steps for making {recipe.dish}, which helped the characters finish the feast safely."
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="castle", activity="counting", prize="ledger", recipe="mooncake",
                name="Elsa", gender="girl", helper="queen", trait="careful"),
    StoryParams(place="cottage", activity="baking", prize="scroll", recipe="berrytart",
                name="Mina", gender="girl", helper="baker", trait="curious"),
    StoryParams(place="garden", activity="feast", prize="cake", recipe="honeybun",
                name="Lily", gender="girl", helper="king", trait="brave"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("covers", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.plural:
            lines.append(asp.fact("plural", pid))
    for rid, r in RECIPES.items():
        lines.append(asp.fact("recipe", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act, Prize, Recipe) :- affords(Place, Act), setting(Place), activity(Act), prize(Prize), recipe(Recipe),
    compatible(Act, Prize).
compatible(counting, ledger).
compatible(baking, scroll).
compatible(baking, cake).
compatible(feast, ledger).
compatible(feast, scroll).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
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
            header = f"### {p.name}: {p.activity} at {p.place} (recipe: {p.recipe})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
