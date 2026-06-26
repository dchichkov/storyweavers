#!/usr/bin/env python3
"""
A tiny tall-tale storyworld about idioms and sound effects.

Premise:
A child hears a strange idiom from a big-voiced grownup, takes it literally,
and the resulting mix-up causes a comical, state-driven tumble of sound effects.
The tale resolves when the grownup explains the idiom and the child turns the
misunderstanding into a playful performance.

This file is self-contained except for the shared results/asp helpers.
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
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    vibe: str


@dataclass
class Idiom:
    id: str
    phrase: str
    literal_image: str
    meaning: str
    sound: str
    effect: str
    trigger: str


@dataclass
class Propset:
    id: str
    label: str
    phrase: str
    sound: str


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    idiom: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "barn": Setting(place="the red barn", vibe="wide-open"),
    "porch": Setting(place="the porch", vibe="windy"),
    "market": Setting(place="the market square", vibe="busy"),
    "dock": Setting(place="the dock", vibe="splashy"),
}

IDIOMS = {
    "raining_cats": Idiom(
        id="raining_cats",
        phrase="it's raining cats and dogs",
        literal_image="a sky full of silly falling cats and dogs",
        meaning="it is raining very hard",
        sound="PLOP! PLOP! WHOOSH!",
        effect="wet",
        trigger="rain",
    ),
    "butterflies": Idiom(
        id="butterflies",
        phrase="butterflies in my stomach",
        literal_image="tiny butterflies fluttering in a belly",
        meaning="feeling nervous",
        sound="FLITTER-FLUTTER!",
        effect="tickle",
        trigger="fear",
    ),
    "loud_as_bell": Idiom(
        id="loud_as_bell",
        phrase="loud as a bell",
        literal_image="a bell shaking the whole room",
        meaning="very loud",
        sound="CLANG! CLANG!",
        effect="noise",
        trigger="voice",
    ),
    "feet_fly": Idiom(
        id="feet_fly",
        phrase="my feet are flying",
        literal_image="feet with tiny wings zooming around",
        meaning="moving very fast",
        sound="ZIP-ZAP-ZOOM!",
        effect="speed",
        trigger="running",
    ),
}

PROPS = {
    "bell": Propset(id="bell", label="a brass bell", phrase="a brass bell", sound="CLANG!"),
    "umbrella": Propset(id="umbrella", label="a striped umbrella", phrase="a striped umbrella", sound="WHUMP!"),
    "lantern": Propset(id="lantern", label="a round lantern", phrase="a round lantern", sound="BONG!"),
}

HERO_NAMES = ["Milo", "Nina", "Eli", "June", "Pip", "Tessa", "Arlo", "Ruby"]
HELPERS = ["grandpa", "grandma", "uncle", "aunt", "neighbor"]
GENDERS = ["girl", "boy"]


def reasonableness_gate(idiom: Idiom, setting: Setting) -> None:
    if not setting.place:
        raise StoryError("This story needs a place with room for a tall-tale misunderstanding.")
    if idiom.id not in IDIOMS:
        raise StoryError("Unknown idiom.")
    if idiom.trigger not in {"rain", "fear", "voice", "running"}:
        raise StoryError("Unsupported idiom trigger.")


def tell(setting: Setting, idiom: Idiom, hero_name: str, gender: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, role="child", memes={"curiosity": 1.0}))
    grownup = world.add(Entity(id=helper, kind="character", type="adult", role="helper", memes={"warmth": 1.0}))
    prop = world.add(Entity(id="prop", kind="thing", type="prop", label="the prop", phrase="a curious prop", owner=hero.id))

    world.say(f"{hero.id} was a small {gender} with big eyes and bigger wondering.")
    world.say(f"One day, {hero.pronoun('possessive')} {helper} said, \"{idiom.phrase}.\"")
    world.say(f"{hero.id} took the words in the tallest, most literal way and imagined {idiom.literal_image}.")

    world.para()
    world.say(f"At {world.setting.place}, the air went hush-hush.")
    world.say(f"Then came the sound: {idiom.sound}")
    hero.memes["surprise"] = 1.0
    hero.memes["worry"] = 1.0
    hero.meters["stare"] = 1.0

    if idiom.id == "raining_cats":
        world.say(f"Thunk! Thunk! {hero.id} grabbed {prop.label} and shouted, \"The sky is dropping kitties!\"")
        prop.meters["damp"] = 1.0
        hero.meters["splash"] = 1.0
    elif idiom.id == "butterflies":
        world.say(f"{hero.id} held {hero.pronoun('possessive')} belly and whispered, \"My stomach has tiny wings!\"")
        hero.meters["wiggle"] = 1.0
    elif idiom.id == "loud_as_bell":
        world.say(f"{hero.id} cupped {hero.pronoun('possessive')} ears and hollered, \"The bell is talking!\"")
        prop.meters["ring"] = 1.0
        hero.meters["flinch"] = 1.0
    elif idiom.id == "feet_fly":
        world.say(f"{hero.id} leapt up and ran in circles, certain {hero.pronoun('possessive')} feet had sprouted wings.")
        hero.meters["run"] = 1.0

    world.para()
    world.say(f"{helper.capitalize()} laughed a gentle laugh and said, \"Oh, {hero.id}, that idiom means {idiom.meaning}.\"")
    hero.memes["relief"] = 1.0
    hero.memes["joy"] = 1.0
    world.say(f"Then {hero.id} smiled so hard {hero.pronoun('possessive')} cheeks looked ready to pop.")
    world.say(f"{hero.id} turned the mix-up into a game and shouted the idiom back with a grand, singing voice.")
    world.say(f"The whole place answered with one last sound: {idiom.sound} and a happy, echoing ha-HA!")

    world.facts.update(hero=hero, helper=grownup, idiom=idiom, prop=prop, setting=setting)
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about idioms and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--idiom", choices=IDIOMS)
    ap.add_argument("--gender", choices=GENDERS)
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
    place = args.place or rng.choice(sorted(SETTINGS))
    idiom = args.idiom or rng.choice(sorted(IDIOMS))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    reasonableness_gate(IDIOMS[idiom], SETTINGS[place])
    return StoryParams(place=place, idiom=idiom, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short tall tale for a child that includes the idiom "{f["idiom"].phrase}" and a loud sound effect.',
        f"Tell a playful story where {f['hero'].id} misunderstands an idiom at {f['setting'].place} and then learns what it means.",
        f"Make a child-friendly story with a big sound effect, a silly literal mistake, and a happy explanation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    idiom = f["idiom"]
    return [
        QAItem(
            question=f"What did {hero.id} think {idiom.phrase} meant?",
            answer=f"{hero.id} thought it meant {idiom.literal_image}.",
        ),
        QAItem(
            question=f"Who explained the idiom to {hero.id}?",
            answer=f"{helper.id} explained that it meant {idiom.meaning}.",
        ),
        QAItem(
            question=f"What sound kept showing up in the story?",
            answer=f"The story kept echoing {idiom.sound} as the silly misunderstanding grew and then turned cheerful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    idiom = f["idiom"]
    return [
        QAItem(
            question="What is an idiom?",
            answer="An idiom is a saying whose real meaning is not the same as the plain words.",
        ),
        QAItem(
            question="Why do people use sound effects in stories?",
            answer="People use sound effects to make a story feel lively, funny, or exciting, almost like you can hear it happening.",
        ),
        QAItem(
            question="What does the idiom mean here?",
            answer=f'In this story, "{idiom.phrase}" means {idiom.meaning}.',
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", idiom="raining_cats", name="Milo", gender="boy", helper="grandpa"),
    StoryParams(place="porch", idiom="butterflies", name="Nina", gender="girl", helper="aunt"),
    StoryParams(place="market", idiom="loud_as_bell", name="Eli", gender="boy", helper="uncle"),
    StoryParams(place="dock", idiom="feet_fly", name="Ruby", gender="girl", helper="grandma"),
]


ASP_RULES = r"""
hero(H) :- hero_name(H).
idiom(I) :- idiom_name(I).
place(P) :- place_name(P).

misunderstands(H, I) :- hero(H), idiom(I).
sounds(L) :- idiom_sound(_, L).
valid_story(P, I, H) :- place(P), idiom(I), hero(H), setting_ok(P), idiom_ok(I).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place_name", p))
        lines.append(asp.fact("setting_ok", p))
    for i in IDIOMS:
        lines.append(asp.fact("idiom_name", i))
        lines.append(asp.fact("idiom_sound", i, IDIOMS[i].sound))
        lines.append(asp.fact("idiom_ok", i))
    for h in HERO_NAMES:
        lines.append(asp.fact("hero_name", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set((p, i, h) for p in SETTINGS for i in IDIOMS for h in HERO_NAMES)
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python registry cross-product ({len(py_set)} stories).")
        return 0
    print("MISMATCH:")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    idiom = IDIOMS[params.idiom]
    world = tell(setting, idiom, params.name, params.gender, params.helper)
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
        print(asp_program("#show valid_story/3."))
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
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.idiom} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
