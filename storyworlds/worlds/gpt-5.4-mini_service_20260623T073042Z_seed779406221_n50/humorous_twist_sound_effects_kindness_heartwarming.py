#!/usr/bin/env python3
"""
storyworlds/worlds/humorous_twist_sound_effects_kindness_heartwarming.py
=======================================================================

A small standalone storyworld about a kind child, a small mishap, a humorous
twist, and a heartwarming fix with playful sound effects.

The seed-inspired premise:
- A child wants to help with something simple.
- A tiny mistake creates a funny mess or misunderstanding.
- Sound effects and a twist keep the scene lively.
- Kindness turns the moment warm again.

The world is intentionally compact so every story has a clear beginning,
a state-driven middle turn, and a gentle ending image that proves change.
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoors: bool
    props: list[str] = field(default_factory=list)


@dataclass
class Twist:
    id: str
    setup: str
    sound: str
    reveal: str
    kind: str = "humorous"
    tag: str = "twist"


@dataclass
class HelpfulThing:
    id: str
    label: str
    phrase: str
    sound: str
    helps: str
    tag: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    twist: str
    helper: str
    name: str
    child_type: str
    adult: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting("the kitchen", True, ["mixing bowl", "spoon", "flour"]),
    "garden": Setting("the garden", False, ["watering can", "hose", "bucket"]),
    "laundry": Setting("the laundry room", True, ["basket", "sock pile", "towel"]),
}

TWISTS = {
    "swap": Twist(
        id="swap",
        setup="a bowl that looked empty",
        sound="plip!",
        reveal="the bowl was not empty at all; it had a tiny cookie stuck to the bottom",
    ),
    "echo": Twist(
        id="echo",
        setup="a quiet hallway",
        sound="boing!",
        reveal="the sound bounced back in a silly echo and made everyone giggle",
    ),
    "muddle": Twist(
        id="muddle",
        setup="a tidy pile",
        sound="fwump!",
        reveal="the tidy pile had a sneaky kitten sleeping inside it",
    ),
}

HELPERS = {
    "tea_towel": HelpfulThing(
        id="tea_towel",
        label="tea towel",
        phrase="a soft tea towel",
        sound="swish!",
        helps="wiped the flour without fuss",
        tag="cloth",
    ),
    "spoon": HelpfulThing(
        id="spoon",
        label="big spoon",
        phrase="a big wooden spoon",
        sound="clink!",
        helps="stirred the mess into something neat",
        tag="tool",
    ),
    "basket": HelpfulThing(
        id="basket",
        label="basket",
        phrase="a little basket",
        sound="thump!",
        helps="held everything in one safe place",
        tag="container",
    ),
}

GIRL_NAMES = ["Maya", "Lena", "Nora", "Ivy", "Zoe", "Ava"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Leo", "Ben"]
TRAITS = ["helpful", "curious", "gentle", "cheerful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for twist in TWISTS:
            for helper in HELPERS:
                if place == "garden" and helper == "tea_towel":
                    continue
                combos.append((place, twist, helper))
    return combos


def prize_label(kind: str) -> str:
    return {"tea_towel": "tea towel", "spoon": "spoon", "basket": "basket"}[kind]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming story world with a humorous twist and sound effects."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
              and (args.twist is None or c[1] == args.twist)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, twist, helper = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, twist, helper, name, child_type, adult, trait)


def tell(setting: Setting, twist: Twist, helper: HelpfulThing, child_name: str,
         child_type: str, adult_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type, role="child",
        memes={"kindness": 1.0, "joy": 1.0, "embarrassment": 0.0},
    ))
    adult = world.add(Entity(
        id="Adult", kind="character", type=adult_type, role="adult",
        label="the parent", memes={"warmth": 1.0, "patience": 1.0},
    ))
    prop = world.add(Entity(
        id="prop", type="thing", label=helper.label, meters={"mess": 0.0},
        attrs={"sound": helper.sound},
    ))
    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["prop"] = prop
    world.facts["helper"] = helper
    world.facts["twist"] = twist
    world.facts["trait"] = trait

    world.say(
        f"{child_name} was a {trait} little {child_type} who loved helping in {setting.place}."
    )
    world.say(
        f"One day, {child_name} tried to help with {helper.phrase} while {adult.label_word} watched."
    )
    world.para()
    world.say(
        f'Then came the twist: {twist.setup}. "{twist.sound}" went the room, '
        f"and everyone blinked."
    )
    if setting.indoors:
        prop.meters["mess"] += 1
    child.memes["surprise"] = 1.0
    adult.memes["surprise"] = 1.0

    if helper.id == "tea_towel":
        world.say(
            f"{child_name} held up the towel. {twist.reveal}. {adult.label_word.capitalize()} laughed first."
        )
    elif helper.id == "spoon":
        world.say(
            f"{child_name} gave the spoon a careful stir: {helper.sound} {twist.reveal}."
        )
    else:
        world.say(
            f"{child_name} opened the basket and found the answer hiding there: {twist.reveal}."
        )

    world.para()
    child.memes["kindness"] += 1.0
    adult.memes["warmth"] += 1.0
    world.say(
        f"{child_name} smiled, said sorry for the mix-up, and helped again more carefully."
    )
    world.say(
        f'{helper.sound} {helper.helps}. Soon the little surprise felt funny instead of bad.'
    )
    world.say(
        f"{adult.label_word.capitalize()} ruffled {child_name}'s hair and said, "
        f'"That was a silly twist, but you were kind about it."'
    )
    world.say(
        f"By the end, {child_name} was still {trait}, and the room felt warm and bright."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    twist = f["twist"]
    return [
        f'Write a heartwarming story for a young child where {child.id} hears a funny sound like "{twist.sound}" and keeps helping kindly.',
        f"Tell a small humorous story in {world.setting.place} where a twist turns a simple job into a giggle, but kindness fixes it.",
        f'Write a gentle story that uses the sound effect "{helper.sound}" and ends with a kind apology and a warm smile.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    helper = f["helper"]
    twist = f["twist"]
    return [
        QAItem(
            question=f"Who is the story about in {world.setting.place}?",
            answer=f"It is about {child.id}, a kind little {child.type}, and {adult.label_word}, who stayed nearby to help.",
        ),
        QAItem(
            question=f"What funny twist happened when {child.id} tried to help?",
            answer=f"The moment took a funny turn when {twist.setup} and then {twist.sound} made everyone look up.",
        ),
        QAItem(
            question=f"How did {child.id} stay kind after the surprise?",
            answer=f"{child.id} said sorry, kept helping, and used {helper.label} more carefully. That kindness made the moment feel warm again.",
        ),
        QAItem(
            question=f"What sound effect appears in the story besides the twist?",
            answer=f"The story uses {helper.sound} and also {twist.sound}, so the scene feels playful and lively.",
        ),
    ]


KNOWLEDGE = {
    "tea_towel": [("What is a tea towel?", "A tea towel is a soft cloth used to dry dishes or wipe up small spills.")],
    "spoon": [("What does a spoon do?", "A spoon is used for stirring, scooping, and eating.")],
    "basket": [("What is a basket for?", "A basket can hold things together so they do not roll away.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and caring about other people.")],
    "sound": [("What is a sound effect in a story?", "A sound effect is a made-up word like bang or swoosh that helps the story feel lively.")],
    "twist": [("What is a twist in a story?", "A twist is a surprising turn that changes what is happening in a fun or unexpected way.")],
}
KNOWLEDGE_ORDER = ["kindness", "sound", "twist", "tea_towel", "spoon", "basket"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["helper"].tag, "kindness", "sound", "twist"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_params() -> list[StoryParams]:
    out = []
    for place, twist, helper in valid_combos():
        out.append(StoryParams(place, twist, helper, "Maya", "girl", "mother", "gentle"))
    return out


CURATED = [
    StoryParams("kitchen", "swap", "tea_towel", "Maya", "girl", "mother", "helpful"),
    StoryParams("garden", "echo", "basket", "Leo", "boy", "father", "curious"),
    StoryParams("laundry", "muddle", "spoon", "Nora", "girl", "mother", "cheerful"),
]


ASP_RULES = r"""
place(kitchen). place(garden). place(laundry).
twist(swap). twist(echo). twist(muddle).
helper(tea_towel). helper(spoon). helper(basket).

valid(P,T,H) :- place(P), twist(T), helper(H), not bad(P,H).
bad(garden, tea_towel).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = tell(setting, TWISTS[params.twist], HELPERS[params.helper],
                 params.name, params.child_type, params.adult, params.trait)
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
        print(f"{len(combos)} compatible combos:\n")
        for p, t, h in combos:
            print(f"  {p:8} {t:8} {h}")
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
