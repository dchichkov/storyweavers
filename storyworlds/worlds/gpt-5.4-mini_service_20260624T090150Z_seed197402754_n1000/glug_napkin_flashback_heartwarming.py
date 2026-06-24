#!/usr/bin/env python3
"""
storyworlds/worlds/glug_napkin_flashback_heartwarming.py
========================================================

A small heartwarming storyworld about a child, a careful drink, a napkin, and
a gentle flashback that helps everyone solve a tiny mess kindly.

Seed tale shape:
- A child is enjoying a drink.
- The drink makes a glug sound and spills a little.
- A napkin becomes important.
- A remembered lesson from a flashback helps the child make things right.
- The ending proves the mess is cleaned and the feeling is warm.

This world is intentionally small and constraint-checked: the spill must be
real, the napkin must plausibly help, and the flashback must connect to the
resolution rather than acting like a random garnish.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen table"
    affords: set[str] = field(default_factory=set)


@dataclass
class Drink:
    id: str
    label: str
    phrase: str
    color: str
    mess: str
    sound: str = "glug"
    risky: bool = True


@dataclass
class Keep:
    id: str
    label: str
    phrase: str
    helps: set[str]
    fix: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def spill_risk(world: World, child: Entity, drink: Drink) -> bool:
    return drink.risky and drink.mess in {"wet", "sticky"}


def choose_keep(drink: Drink) -> Optional[Keep]:
    for k in KEEPS:
        if drink.mess in k.helps:
            return k
    return None


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        child = next((e for e in world.entities.values() if e.kind == "character"), None)
        cup = next((e for e in world.entities.values() if e.type == "cup"), None)
        napkin = next((e for e in world.entities.values() if e.type == "napkin"), None)
        if child and cup and cup.meters.get("spilled", 0.0) >= THRESHOLD and napkin and napkin.worn_by == child.id:
            sig = ("wipe", cup.id)
            if sig not in world.fired:
                world.fired.add(sig)
                cup.meters["spilled"] = 0.0
                child.memes["care"] = child.memes.get("care", 0.0) + 1
                out.append("The napkin wiped the spill away.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def flashback_line(hero: Entity, helper: Entity) -> str:
    return (
        f"As {hero.pronoun('subject').capitalize()} looked at the wet spot, "
        f"{hero.pronoun('subject')} remembered a warm afternoon when {helper.id} "
        f"showed {hero.pronoun('object')} how a napkin could turn a mess into a fix."
    )


def tell(setting: Setting, drink: Drink, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="grandma"))
    cup = world.add(Entity(id="Cup", type="cup", label=drink.label, phrase=drink.phrase, owner=hero.id))
    napkin = world.add(Entity(id="Napkin", type="napkin", label="napkin", phrase="a soft napkin", owner=hero.id))

    hero.memes["joy"] = 1.0
    hero.memes["love"] = 1.0
    helper.memes["warmth"] = 1.0

    world.say(
        f"{hero.id} sat at {setting.place} with a cup of {drink.phrase}. "
        f"The room was calm and sunny, and the {drink.sound} sound made {hero.id} smile."
    )
    world.say(
        f"{hero.id} took a sip, but the cup tilted and made a little {drink.sound}. "
        f"{hero.id}'s {drink.label} spilled on the table."
    )
    cup.meters["spilled"] = 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0

    world.para()
    world.say(flashback_line(hero, helper))
    world.say(
        f"{helper.id} had said, \"When something spills, breathe first, then use a napkin gently.\""
    )
    world.say(
        f"{hero.id} nodded, picked up the napkin, and remembered that helping was a kind of love."
    )

    world.para()
    napkin.worn_by = hero.id
    propagate(world, narrate=True)
    if cup.meters.get("spilled", 0.0) < THRESHOLD:
        hero.memes["worry"] = 0.0
        hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
        helper.memes["warmth"] = helper.memes.get("warmth", 0.0) + 1.0
        world.say(
            f"{hero.id} wiped the table clean, and the little mess disappeared. "
            f"{helper.id} smiled because {hero.id} had remembered the kind lesson."
        )
    else:
        world.say(f"{hero.id} kept trying, but the spill still needed help.")

    world.para()
    world.say(
        f"In the end, {hero.id} had a dry table, a clean napkin, and a cozy feeling "
        f"that stayed longer than the spill."
    )
    world.facts.update(hero=hero, helper=helper, cup=cup, napkin=napkin, drink=drink, setting=setting)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen table", affords={"drink"}),
    "porch": Setting(place="the porch table", affords={"drink"}),
    "picnic": Setting(place="the picnic blanket", affords={"drink"}),
}

DRINKS = {
    "juice": Drink(id="juice", label="juice", phrase="sweet orange juice", color="orange", mess="wet"),
    "milk": Drink(id="milk", label="milk", phrase="cool milk", color="white", mess="wet"),
    "cocoa": Drink(id="cocoa", label="cocoa", phrase="warm cocoa", color="brown", mess="sticky"),
}

KEEPS = [
    Keep(id="napkin", label="napkin", phrase="a soft napkin", helps={"wet", "sticky"}, fix="wipe"),
]

NAMES = ["Milo", "Nora", "Pip", "Lina", "Toby", "Ada", "Ivy", "Ben"]
HELPERS = ["grandmother", "grandfather"]
TYPES = {"grandmother": "grandmother", "grandfather": "grandfather"}


@dataclass
class StoryParams:
    place: str
    drink: str
    name: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for drink in DRINKS:
            if "drink" in setting.affords:
                combos.append((place, drink))
    return combos


def explain_rejection(place: str, drink: str) -> str:
    return f"(No story: {drink} does not fit a gentle spill-and-napkin tale at {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming spill-and-napkin storyworld with a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
              and (args.drink is None or c[1] == args.drink)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, drink = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, drink=drink, name=name, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming story for a little child involving a glug, a napkin, and a flashback.',
        f"Tell a gentle story where {f['hero'].id} spills {f['drink'].phrase} and remembers a kind lesson about a napkin.",
        f"Write a cozy story at {f['setting'].place} that ends with a clean table and a warm feeling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, cup, drink = f["hero"], f["helper"], f["cup"], f["drink"]
    return [
        QAItem(
            question=f"What happened when {hero.id} took a sip of {drink.label}?",
            answer=f"The cup tilted and made a little glug, and some {drink.label} spilled on the table.",
        ),
        QAItem(
            question=f"Why did {hero.id} remember the flashback about {helper.id}?",
            answer=f"{hero.id} remembered when {helper.id} showed how a napkin could clean up a spill kindly.",
        ),
        QAItem(
            question=f"How did the story end at {f['setting'].place}?",
            answer=f"{hero.id} wiped the spill away with a napkin, and the table ended clean and cozy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a napkin for?",
            answer="A napkin is a soft cloth or paper used to wipe hands, mouths, and small spills.",
        ),
        QAItem(
            question="What does glug sound like?",
            answer="Glug is a bubbly pouring sound, like liquid moving out of a cup.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risky(Drink) :- drink(Drink).
fix(napkin, Drink) :- drink(Drink), mess(Drink, wet).
fix(napkin, Drink) :- drink(Drink), mess(Drink, sticky).

valid_story(Place, Drink) :- setting(Place), drink(Drink), affords(Place, drink),
                             risky(Drink), fix(napkin, Drink).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for did, d in DRINKS.items():
        lines.append(asp.fact("drink", did))
        lines.append(asp.fact("mess", did, d.mess))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    combos = set(valid_combos())
    if combos == set(asp_valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(combos)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], DRINKS[params.drink], params.name, "girl" if params.name in {"Nora", "Lina", "Ada", "Ivy"} else "boy", params.helper)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="kitchen", drink="juice", name="Milo", helper="grandmother"),
    StoryParams(place="porch", drink="cocoa", name="Nora", helper="grandfather"),
    StoryParams(place="picnic", drink="milk", name="Pip", helper="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for place, drink in triples:
            print(f"  {place:8} {drink}")
        return

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
