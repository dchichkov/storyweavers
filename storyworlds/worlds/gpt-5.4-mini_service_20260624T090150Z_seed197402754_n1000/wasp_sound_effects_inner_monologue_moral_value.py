#!/usr/bin/env python3
"""
Storyworld: wasp_sound_effects_inner_monologue_moral_value
===========================================================

A small fairy-tale storyworld about a wasp, a sweet treat, brave quiet help,
sound effects, inner monologue, and a gentle moral.

The story is built from simulated state:
- the wasp is drawn by sweetness,
- the child feels fear and wants to swat,
- the elder uses a kinder plan,
- the ending proves that gentleness solved the problem.

This file follows the shared storyworld contract:
- StoryParams plus parser / resolve_params / generate / emit / main
- eager result imports
- lazy ASP helper import inside ASP helpers
- inline ASP_RULES twin and a Python reasonableness gate
"""

from __future__ import annotations

import argparse
import dataclasses
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    outdoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    sweet: str
    region: str
    at_risk_from: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    offer: str
    result: str
    helps_against: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.current_threat: str = ""

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


SETTINGS = {
    "cottage": Setting(place="the little cottage", outdoors=False, affords={"window"}),
    "garden": Setting(place="the rose garden", outdoors=True, affords={"window"}),
    "orchard": Setting(place="the apple orchard", outdoors=True, affords={"window"}),
}

TREAT = Treat(
    id="honey_cake",
    label="honey cake",
    phrase="a round honey cake with golden crumbs",
    sweet="sweet",
    region="table",
    at_risk_from={"wasp"},
)

FIXES = [
    Fix(
        id="cover",
        label="a clean bowl",
        offer="lift a clean bowl over the honey cake",
        result="put a clean bowl over the honey cake",
        helps_against={"wasp"},
    ),
    Fix(
        id="window",
        label="an open window",
        offer="open the window wide",
        result="open the window wide",
        helps_against={"wasp"},
    ),
    Fix(
        id="fan",
        label="a paper fan",
        offer="fan the wasp gently toward the window",
        result="fan the wasp gently toward the window",
        helps_against={"wasp"},
    ),
]

GIRL_NAMES = ["Mira", "Luna", "Ivy", "Nora", "Ayla", "Wren"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Tomas", "Ravi", "Owen"]
TRAITS = ["brave", "curious", "gentle", "small", "cheerful", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "window" in setting.affords:
            combos.append((place, TREAT.id))
    return combos


def prize_at_risk(treat: Treat) -> bool:
    return "wasp" in treat.at_risk_from


def select_fix(treat: Treat) -> Optional[Fix]:
    for fix in FIXES:
        if "wasp" in fix.helps_against:
            return fix
    return None


def explain_rejection(place: str, treat: Treat) -> str:
    return (
        f"(No story: {treat.label} at {place} would not create a fair wasp problem "
        f"with a gentle solution.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale wasp storyworld with sound effects and a moral.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=[TREAT.id])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    if args.place and args.treat:
        if not prize_at_risk(TREAT):
            raise StoryError(explain_rejection(args.place, TREAT))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.treat is None or c[1] == args.treat)]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    place, treat = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, treat=treat, name=name, gender=gender, elder=elder, trait=trait)


def sound(word: str) -> str:
    return {"buzz": "bzzz", "flutter": "frrt", "tap": "tap tap", "swish": "swish"}.get(word, word)


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id="Elder", kind="character", type=params.elder, label=f"the {params.elder}"))
    wasp = world.add(Entity(id="Wasp", kind="character", type="wasp", label="a wasp"))
    treat = world.add(Entity(id="Treat", type="treat", label=TREAT.label, phrase=TREAT.phrase))

    child.memes["curiosity"] = 1
    child.memes["fear"] = 0
    child.memes["kindness"] = 0
    treat.meters["sweetness"] = 1

    world.say(
        f"Once upon a time, in {setting.place}, there lived a little {params.trait} {params.gender} named {params.name}."
    )
    world.say(
        f"{params.name} loved {TREAT.phrase}, because its {TREAT.sweet} smell made the room feel like a feast."
    )
    world.para()
    world.say(
        f"One afternoon, {params.name} heard {sound('buzz')} {sound('buzz')} at the window."
    )
    world.say(
        f"A striped wasp drifted in, drawn by the sweetness, and it made the air tremble with {sound('flutter')}."
    )
    child.memes["fear"] += 1
    child.meters["alert"] = 1
    world.say(
        f'Inside {params.name}\'s head, a small voice whispered, "I should hide."'
    )
    world.say(
        f'Another thought answered, "If I wave hard, it may sting."'
    )
    world.para()
    world.say(
        f"{params.elder.capitalize()} looked up from the hearth and said, "
        f'"Do not strike, little one. A wasp is only looking for a sweet path."'
    )
    world.say(
        f"Then {params.elder} pointed to the cake and the window and suggested, "
        f"\"Let us choose the gentle way.\""
    )
    fix = select_fix(TREAT)
    if fix is None:
        raise StoryError("No gentle fix is available for this story.")
    world.facts["fix"] = fix
    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["wasp"] = wasp
    world.facts["treat"] = treat
    world.facts["setting"] = setting

    world.say(
        f"{params.name} swallowed a trembling breath, then obeyed."
    )
    world.say(
        f"With careful hands, {params.name} helped {params.elder} {fix.result}."
    )
    world.say(
        f"The wasp hummed at the cake once more, made a soft {sound('tap')}, and flew toward the open air."
    )
    child.memes["fear"] = 0
    child.memes["kindness"] += 1
    child.memes["relief"] = 1
    world.say(
        f"At last, {params.name} smiled, because the cake stayed safe and the wasp found its way out."
    )
    world.say(
        f"And {params.elder} said, \"A gentle hand can solve what a frightened fist only worsens.\""
    )
    world.say(
        f"That was the moral of the day: kindness is braver than a quick swat."
    )
    world.facts["resolved"] = True
    world.facts["moral"] = "kindness is braver than a quick swat"
    return world


ASP_RULES = r"""
place(cottage). place(garden). place(orchard).
treat(honey_cake).
wasp_problem(Place) :- place(Place).
can_fix(Place) :- place(Place), treat(honey_cake).
valid_story(Place, honey_cake) :- wasp_problem(Place), can_fix(Place).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("treat", TREAT.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asps - py))
    print("  only in python:", sorted(py - asps))
    return 1


def generation_prompts(world: World) -> list[str]:
    p = world.facts["child"]
    elder = world.facts["elder"]
    return [
        f'Write a short fairy tale for a child named {p.id} about a wasp, a sweet cake, and a gentle solution.',
        f"Tell a simple story where {p.id} hears a wasp buzzing in {world.setting.place} and {elder.pronoun('subject')} chooses kindness.",
        "Write a fairy tale that includes sound effects, an inner monologue, and a moral about gentleness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    fix = world.facts["fix"]
    moral = world.facts["moral"]
    return [
        QAItem(
            question=f"Who heard the wasp buzzing in {world.setting.place}?",
            answer=f"{child.id} heard the wasp buzzing in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {elder.label} suggest to keep the honey cake safe?",
            answer=f"{elder.label.capitalize()} suggested that they {fix.offer}. That was the gentle plan.",
        ),
        QAItem(
            question=f"What was the moral at the end of the story?",
            answer=f"The moral was that {moral}.",
        ),
        QAItem(
            question=f"What did {child.id}'s inner voice worry about?",
            answer=(
                f"{child.id}'s inner voice worried about getting stung, so {child.id} wanted to hide and swat."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What sound does a wasp make?",
            answer="A wasp usually makes a buzzing sound, like bzzz, when it flies.",
        ),
        QAItem(
            question="Why should you not hit a wasp with your hand?",
            answer="It is safer not to hit a wasp, because rough swatting can make it sting or make the situation worse.",
        ),
        QAItem(
            question="What does a gentle choice mean?",
            answer="A gentle choice means using care and calm hands instead of hurting or rushing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
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
    StoryParams(place="cottage", treat="honey_cake", name="Mira", gender="girl", elder="grandmother", trait="gentle"),
    StoryParams(place="garden", treat="honey_cake", name="Theo", gender="boy", elder="grandfather", trait="curious"),
    StoryParams(place="orchard", treat="honey_cake", name="Ivy", gender="girl", elder="grandmother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
