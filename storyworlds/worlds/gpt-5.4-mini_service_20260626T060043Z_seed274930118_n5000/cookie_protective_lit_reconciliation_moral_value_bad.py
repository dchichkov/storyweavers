#!/usr/bin/env python3
"""
storyworlds/worlds/cookie_protective_lit_reconciliation_moral_value_bad.py
===========================================================================

A small comedy storyworld about a cookie, something protective, a lit moment,
reconciliation, a moral value, and a bad ending.

Premise:
- A child really wants one special cookie.
- There is a tiny protective item that can keep the cookie safe from a mess.
- A lit candle / lit oven / lit lamp makes the moment feel important.

Tension:
- Greed, carelessness, or silliness risks ruining the cookie.

Turn:
- Someone warns the child.
- The child makes a messy choice anyway.

Resolution:
- The characters reconcile, but the ending is still bad for the cookie.
- The moral value is gently stated through the consequences.

The script follows the Storyweavers storyworld contract:
- self-contained stdlib-only script
- imports results eagerly and asp lazily
- defines StoryParams, parser/resolve/generate/emit/main
- includes ASP twin, validation, QA, and trace support
"""

from __future__ import annotations

import argparse
import copy
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
    worn_by: Optional[str] = None
    protective: bool = False
    lit: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "crumbs": 0.0,
                "smash": 0.0,
                "warmth": 0.0,
                "mess": 0.0,
            }
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "greed": 0.0,
                "worry": 0.0,
                "conflict": 0.0,
                "reconciliation": 0.0,
                "moral": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class CookieScene:
    cookie_style: str
    protective_item: str
    protective_phrase: str
    protective_lit_context: str
    danger: str
    danger_meter: str
    moral: str
    ending_image: str


@dataclass
class StoryParams:
    place: str
    cookie_style: str
    protective_item: str
    danger: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


COOKIE_STYLES = {
    "chocolate_chip": CookieScene(
        cookie_style="chocolate chip",
        protective_item="oven mitt",
        protective_phrase="a bright protective oven mitt",
        protective_lit_context="The little oven light was lit, and the cookie looked proud on the tray.",
        danger="drop",
        danger_meter="smash",
        moral="It is kinder to be careful than to be greedy.",
        ending_image="The cookie ended up crumbled on the floor, and everyone had to laugh through the crumbs.",
    ),
    "sugar": CookieScene(
        cookie_style="sugar",
        protective_item="cookie tin",
        protective_phrase="a shiny protective cookie tin",
        protective_lit_context="A lit candle on the table made the frosting sparkle like a tiny stage.",
        danger="squish",
        danger_meter="smash",
        moral="A treat stays happier when nobody grabs too fast.",
        ending_image="The cookie got squashed under a book, which was a very silly way for dessert to retire.",
    ),
    "ginger": CookieScene(
        cookie_style="ginger",
        protective_item="paper napkin",
        protective_phrase="a neat protective paper napkin",
        protective_lit_context="The lamp was lit over the table, making the cookie smell extra fancy.",
        danger="crack",
        danger_meter="smash",
        moral="Even a small cookie needs gentle hands.",
        ending_image="The cookie cracked in half, and the two halves stared at each other like offended twins.",
    ),
}

DANGERS = {
    "drop": "drop",
    "squish": "squish",
    "crack": "crack",
}

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"cookie"}),
    "table": Setting(place="the dining table", indoors=True, affords={"cookie"}),
    "pantry": Setting(place="the pantry", indoors=True, affords={"cookie"}),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ava", "Zoe", "Ella", "Mia", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Owen", "Max", "Theo", "Ben", "Sam", "Jack"]
TRAITS = ["silly", "curious", "mischievous", "cheerful", "hungry", "dramatic"]


def cookie_at_risk(scene: CookieScene) -> bool:
    return True


def select_protection(scene: CookieScene) -> str:
    return scene.protective_item


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for style in COOKIE_STYLES:
            for danger in DANGERS:
                combos.append((place, style, danger))
    return combos


def explain_rejection(place: str, style: str, danger: str) -> str:
    return f"(No story: the cookie scene at {place} with {style} and {danger} is not unreasonable here, so this should not reject.)"


def explain_gender(gender: str) -> str:
    return f"(No story: unsupported gender option {gender!r}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld about a cookie, something protective, a lit moment, reconciliation, and a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cookie-style", choices=COOKIE_STYLES)
    ap.add_argument("--protective-item", choices=["oven_mitt", "cookie_tin", "paper_napkin"])
    ap.add_argument("--danger", choices=DANGERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.gender and args.name is None:
        pass
    if args.cookie_style and args.protective_item:
        pass

    place = args.place or rng.choice(list(SETTINGS))
    style = args.cookie_style or rng.choice(list(COOKIE_STYLES))
    danger = args.danger or rng.choice(list(DANGERS))
    scene = COOKIE_STYLES[style]
    if args.protective_item:
        expected = {"oven_mitt": "oven mitt", "cookie_tin": "cookie tin", "paper_napkin": "paper napkin"}[args.protective_item]
        if expected != scene.protective_item:
            raise StoryError(f"(No story: {args.protective_item} does not fit the {style} cookie scene.)")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        cookie_style=style,
        protective_item=args.protective_item or scene.protective_item.replace(" ", "_"),
        danger=danger,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def _entity_name(params: StoryParams) -> tuple[str, str]:
    return params.name, params.parent


def tell(params: StoryParams) -> World:
    scene = COOKIE_STYLES[params.cookie_style]
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    cookie = world.add(Entity(
        id="cookie",
        type="cookie",
        label="cookie",
        phrase=f"a {scene.cookie_style} cookie",
        owner=hero.id,
        caretaker=parent.id,
    ))
    cookie.lit = True
    protector = world.add(Entity(
        id=scene.protective_item.replace(" ", "_"),
        type=scene.protective_item,
        label=scene.protective_item,
        phrase=scene.protective_phrase,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        lit=False,
    ))

    world.say(f"{hero.id} was a little {params.trait} {params.gender} who loved cookies more than bedtime.")
    world.say(f"One day, {hero.id}'s {params.parent} brought out {scene.cookie_style} {cookie.label}.")
    world.say(scene.protective_phrase.capitalize() + " was ready to help, and the little kitchen light was lit.")

    world.para()
    world.say(f"{hero.id} wanted to eat the cookie right away, because {hero.pronoun('subject')} was sure it would taste twice as good if {hero.pronoun('subject')} stared at it first.")
    world.say(f"But {params.parent} said, \"Use the {scene.protective_item} first, or the cookie might {params.danger}.\"")

    world.para()
    hero.memes["greed"] += 1
    hero.memes["worry"] += 1
    world.say(f"{hero.id} giggled, grabbed too fast, and forgot the warning.")
    if params.danger == "drop":
        cookie.meters["smash"] += 1
        world.say(f"The cookie slipped, bounced, and went skittering under the chair like it had a secret appointment.")
    elif params.danger == "squish":
        cookie.meters["smash"] += 1
        world.say(f"The cookie got squished flat, so flat it almost looked like a politely offended pancake.")
    else:
        cookie.meters["smash"] += 1
        world.say(f"The cookie cracked with a tiny snap, which sounded much funnier than it felt.")

    parent.memes["conflict"] += 1
    hero.memes["conflict"] += 1
    world.say(f"{params.parent.capitalize()} sighed, not because the cookie was lost, but because the whole moment had become silly in the wrong way.")

    world.para()
    hero.memes["reconciliation"] += 1
    parent.memes["reconciliation"] += 1
    world.say(f"{hero.id} apologized and nudged the {scene.protective_item} back into place.")
    world.say(f"{params.parent.capitalize()} forgave {hero.id} at once, because the important part was not the broken cookie, but the honest face making amends.")
    world.say(f"They shared the crumbs anyway, and the lit kitchen felt calm again.")

    world.para()
    hero.memes["moral"] += 1
    parent.memes["moral"] += 1
    world.say(scene.ending_image)
    world.say(scene.moral)

    world.facts.update(
        hero=hero,
        parent=parent,
        cookie=cookie,
        protector=protector,
        scene=scene,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    scene = f["scene"]
    params = f["params"]
    return [
        f'Write a short comedy story for a child named {hero.id} about a {scene.cookie_style} cookie, a {scene.protective_item}, and a lit kitchen moment.',
        f"Tell a story where {hero.id} wants to be careful, but also acts silly, and {params.parent} helps them reconcile after a cookie mistake.",
        f'Write a gentle bad-ending story that includes the words "cookie", "protective", and "lit".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    scene = f["scene"]
    params = f["params"]
    cookie = f["cookie"]
    return [
        QAItem(
            question=f"What kind of cookie was in the story?",
            answer=f"It was a {scene.cookie_style} cookie, and it was treated like the most important snack in the room.",
        ),
        QAItem(
            question=f"What protective thing was supposed to help?",
            answer=f"The protective item was {scene.protective_item}, which was meant to keep the cookie safe from silly trouble.",
        ),
        QAItem(
            question=f"What was lit in the scene?",
            answer=f"The kitchen light was lit, which made the little cookie moment feel extra dramatic and a little funny.",
        ),
        QAItem(
            question=f"Why did {params.parent} warn {hero.id}?",
            answer=f"{params.parent.capitalize()} warned {hero.id} because the cookie could {params.danger} if {hero.id} grabbed too fast.",
        ),
        QAItem(
            question=f"What happened after {hero.id} made the wrong choice?",
            answer=f"The cookie got ruined in a bad ending, but {hero.id} and {params.parent} reconciled and made up right away.",
        ),
        QAItem(
            question=f"What moral value did the story show?",
            answer=f"It showed that it is kinder to be careful than greedy, because the cookie would have gone better if {hero.id} had listened.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a protective thing?",
            answer="A protective thing helps keep something safe from harm, mess, heat, or bumps.",
        ),
        QAItem(
            question="Why can a lit candle or lamp matter in a story?",
            answer="A lit candle or lamp can make a moment feel warm, important, or funny, and it can also remind characters to be careful.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and make peace again after a problem.",
        ),
        QAItem(
            question="What is a moral value in a story?",
            answer="A moral value is the lesson about how to act kindly, carefully, or honestly.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when something goes wrong, even if the characters still learn from it or make up afterward.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        if e.lit:
            bits.append("lit=True")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", cookie_style="chocolate_chip", protective_item="oven_mitt", danger="drop", name="Mia", gender="girl", parent="mother", trait="silly"),
    StoryParams(place="table", cookie_style="sugar", protective_item="cookie_tin", danger="squish", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="pantry", cookie_style="ginger", protective_item="paper_napkin", danger="crack", name="Nora", gender="girl", parent="mother", trait="dramatic"),
]


ASP_RULES = r"""
cookie_story(P, S, D) :- place(P), style(S), danger(D).
has_protection(S, mitt) :- style(S), protective_item(mitt).
has_protection(S, tin) :- style(S), protective_item(tin).
has_protection(S, napkin) :- style(S), protective_item(napkin).

valid(P, S, D) :- place(P), style(S), danger(D), has_protection(S, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for s in COOKIE_STYLES:
        lines.append(asp.fact("style", s))
        lines.append(asp.fact("protective_item", COOKIE_STYLES[s].protective_item.replace(" ", "_")))
    for d in DANGERS:
        lines.append(asp.fact("danger", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    style = args.cookie_style or rng.choice(list(COOKIE_STYLES))
    danger = args.danger or rng.choice(list(DANGERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        cookie_style=style,
        protective_item=args.protective_item or COOKIE_STYLES[style].protective_item.replace(" ", "_"),
        danger=danger,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.cookie_style} cookie at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
