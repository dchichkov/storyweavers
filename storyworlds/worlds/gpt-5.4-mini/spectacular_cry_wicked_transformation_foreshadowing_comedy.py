#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spectacular_cry_wicked_transformation_foreshadowing_comedy.py
=============================================================================================

A tiny self-contained storyworld for a comedy about a dramatic cry, a wicked
sneak, and a spectacular transformation that was quietly foreshadowed from the
start.

The seed words are woven into a small simulated domain:
- spectacular
- cry
- wicked

The narrative instruments are:
- Transformation
- Foreshadowing

Style:
- Comedy

The world models a child, a prankish cat, a prop box, a costume piece, and a
patient grown-up. The child begins with an ordinary costume idea, the cat causes
a wicked little mess, the child cries out, the adult predicts the obvious trouble
from earlier hints, and the fix turns the child into a spectacularly silly hero.
The ending proves the change in state: the costume is transformed, the mood is
light, and the foreshadowing payoff lands cleanly.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/spectacular_cry_wicked_transformation_foreshadowing_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/spectacular_cry_wicked_transformation_foreshadowing_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/spectacular_cry_wicked_transformation_foreshadowing_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/spectacular_cry_wicked_transformation_foreshadowing_comedy.py --trace
    python storyworlds/worlds/gpt-5.4-mini/spectacular_cry_wicked_transformation_foreshadowing_comedy.py --json
    python storyworlds/worlds/gpt-5.4-mini/spectacular_cry_wicked_transformation_foreshadowing_comedy.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    clutter: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    messy: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Costume:
    id: str
    label: str
    phrase: str
    transform_to: str
    sparkle: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    sign: str
    danger: str
    mess: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    power: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    cat = world.entities.get("cat")
    if not cat or cat.meters["sneak"] < THRESHOLD:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "costume" in world.entities:
        world.get("costume").meters["spot"] += 1
    for e in list(world.entities.values()):
        if e.role == "child":
            e.memes["panic"] += 1
    out.append("__mess__")
    return out


CAUSAL_RULES = [Rule("mess", "physical", _r_mess)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_problem(world: World) -> dict:
    sim = world.copy()
    if "cat" in sim.entities:
        sim.get("cat").meters["sneak"] += 1
    propagate(sim, narrate=False)
    return {
        "spotted": sim.get("costume").meters["spot"] >= THRESHOLD,
        "panic": sum(e.memes["panic"] for e in sim.entities.values()),
    }


def setup(world: World, child: Entity, costume: Entity, toy: Entity, trouble: Trouble) -> None:
    child.memes["hope"] += 1
    world.say(
        f"On a bright afternoon, {child.id} opened the prop box in {world.setting.place}. "
        f"{world.setting.clutter} The whole room looked ready for a silly show."
    )
    world.say(
        f'{child.id} planned a {trouble.label} act with {costume.label} and {toy.label}, '
        f'and {child.pronoun("possessive")} grin was already spectacular.'
    )


def foreshadow(world: World, trouble: Trouble) -> None:
    world.say(
        f"At the edge of the room, a small sign gave a wicked hint of trouble: "
        f"{trouble.sign}. The cat had been staring at the costume ribbon for minutes."
    )


def attempt(world: World, child: Entity, costume: Entity, toy: Entity) -> None:
    child.memes["delight"] += 1
    world.say(
        f"{child.id} tied on {costume.phrase} and held up {toy.phrase}. "
        f'"Look at me," {child.pronoun()} said, "I am a spectacular hero!"'
    )


def trouble_makes_cry(world: World, child: Entity, cat: Entity, trouble: Trouble) -> None:
    cat.meters["sneak"] += 1
    propagate(world, narrate=False)
    child.memes["cry"] += 1
    world.say(
        f"Then {cat.id} made a wicked dash, slapped the {trouble.label}, and zoomed under the chair. "
        f"The {trouble.label} left a {trouble.mess} mark right across the costume."
    )
    world.say(f'"Aaaah!" {child.id} cried. "{trouble.danger}!"')


def adult_guess(world: World, adult: Entity, trouble: Trouble) -> None:
    pred = predict_problem(world)
    adult.memes["knowing"] += 1
    world.facts["predicted"] = pred
    world.say(
        f"{adult.label_word.capitalize()} peeked over the doorway and sighed with a smile. "
        f'"I saw that wicked cat circling the ribbon," {adult.pronoun()} said. '
        f'"That was foreshadowing."'
    )


def fix_it(world: World, adult: Entity, child: Entity, costume: Entity, fix: Fix) -> None:
    costume.meters["spot"] = 0.0
    costume.meters["transformed"] += 1
    child.memes["cry"] = 0.0
    child.memes["joy"] += 2
    adult.memes["joy"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came in with {fix.phrase} and {fix.action}. "
        f"Quickly, {adult.pronoun()} {fix.result}, and the costume changed into something even funnier."
    )
    world.say(
        f"{child.id} twirled in the mirror. The cape was crooked, the hat was sideways, "
        f"and somehow that made the whole thing more spectacular."
    )


def ending(world: World, child: Entity, costume: Entity) -> None:
    world.say(
        f"By the end, {child.id} was no longer just dressed up. {child.pronoun().capitalize()} "
        f"had been transformed into the silliest hero in the room, and the wicked little stain was gone."
    )
    world.say(
        f"The cat blinked from under the chair, the grown-up chuckled, and the spectacular parade began."
    )


SETTINGS = {
    "playroom": Setting("playroom", "the playroom", "There were paper stars on the floor and a cardboard castle by the wall."),
    "attic": Setting("attic", "the attic", "Old blankets, shiny buttons, and a tiny stage lamp were scattered everywhere."),
    "kitchen": Setting("kitchen", "the kitchen after lunch", "A cookie tin, two spoons, and a paper crown sat on the table."),
}

TOYS = {
    "wand": Toy("wand", "a glitter wand", "the glitter wand"),
    "drum": Toy("drum", "a toy drum", "the toy drum"),
    "duck": Toy("duck", "a squeaky duck", "the squeaky duck"),
}

COSTUMES = {
    "cape": Costume("cape", "a cape", "the shiny cape", "heroic", "sparkled"),
    "hat": Costume("hat", "a hat", "the funny hat", "tall", "wobbled"),
    "mask": Costume("mask", "a mask", "the mystery mask", "mysterious", "gleamed"),
}

TROUBLES = {
    "paint": Trouble("paint", "paint", "paint pot", "a drip-drip trail on the ribbon", "it was getting messier", "painty"),
    "jam": Trouble("jam", "jam", "jam jar", "a sticky paw print by the costume", "it was turning sticky", "sticky"),
    "ink": Trouble("ink", "ink", "ink bottle", "a black stripe across the hem", "it was turning dark", "inky"),
}

FIXES = {
    "napkin": Fix("napkin", "a napkin", "a big clean napkin", "waved", "wrapped the spot and tucked it away", 1),
    "patch": Fix("patch", "a patch kit", "a little patch kit", "patched", "made the costume even sillier with a bright patch", 2),
}

CHILD_NAMES = ["Mina", "Noa", "Benny", "Lena", "Toby", "Pia"]
ADULTS = ["mother", "father"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    toy: str
    costume: str
    trouble: str
    fix: str
    child: str
    gender: str
    adult: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, c) for s in SETTINGS for t in TOYS for c in COSTUMES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with foreshadowing and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULTS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TOYS:
        lines.append(asp.fact("toy", t))
    for c in COSTUMES:
        lines.append(asp.fact("costume", c))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,T,C) :- setting(S), toy(T), costume(C).
foreshadowed :- trouble(T), setting(S), valid_story(S,_,_), T = T.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import json as _json
    ok = True
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"FAILED: generate smoke test crashed: {e}")
        ok = False
    if set(asp_valid_combos()) != set(valid_combos()):
        print("FAILED: ASP and Python valid_combos mismatch")
        ok = False
    else:
        print(f"OK: gate matches ({len(valid_combos())} combos).")
    return 0 if ok else 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    toy = args.toy or rng.choice(list(TOYS))
    costume = args.costume or rng.choice(list(COSTUMES))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    fix = args.fix or rng.choice(list(FIXES))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    adult = args.adult or rng.choice(ADULTS)
    if args.fix and args.fix not in FIXES:
        raise StoryError("unknown fix")
    return StoryParams(setting, toy, costume, trouble, fix, child, gender, adult)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(params.child, kind="character", type=params.gender, role="child"))
    adult = world.add(Entity("Adult", kind="character", type=params.adult, label="the grown-up", role="adult"))
    cat = world.add(Entity("cat", kind="character", type="thing", label="the cat"))
    costume = world.add(Entity("costume", label=COSTUMES[params.costume].label, attrs={"transform_to": COSTUMES[params.costume].transform_to}))
    toy = world.add(Entity("toy", label=TOYS[params.toy].label))
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]

    setup(world, child, costume, toy, trouble)
    world.para()
    foreshadow(world, trouble)
    attempt(world, child, costume, toy)
    trouble_makes_cry(world, child, cat, trouble)
    adult_guess(world, adult, trouble)
    world.para()
    fix_it(world, adult, child, costume, fix)
    ending(world, child, costume)

    world.facts.update(child=child, adult=adult, cat=cat, costume=costume, toy=toy, trouble=trouble, fix=fix)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy story for a young child that includes the words "spectacular", "cry", and "wicked".',
        f"Tell a story where {f['child'].id} gets a wicked little surprise, starts to cry, and then ends up transformed into a spectacular version of a costume hero.",
        "Write a funny foreshadowing story where an obvious hint appears early and pays off later in a silly costume change.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, trouble = f["child"], f["adult"], f["trouble"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who wanted to make a silly show with a costume and a toy. The grown-up helped when the wicked mess appeared."),
        ("Why did {0} cry?".format(child.id),
         f"{child.id} cried because the cat made a wicked dash and spoiled the costume with {trouble.mess}. That surprise was noisy, sticky, and not very funny in the moment."),
        ("How was the problem solved?",
         f"{adult.label_word.capitalize()} brought a simple fix and turned the costume into something new. The old spot disappeared, and the result was even more spectacular."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is foreshadowing?",
         "Foreshadowing is a little hint that something important may happen later in a story. It helps the ending feel clever instead of random."),
        ("What is a transformation in a story?",
         "A transformation is when something changes into a new form or state. In a story, that change can be funny, magical, or surprising."),
        ("Why can a cat make a mess in a story?",
         "Cats are quick and curious, so a story cat can knock things over, chase ribbons, or leave a silly trail. That makes a neat comic problem."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("playroom", "wand", "cape", "paint", "patch", "Mina", "girl", "mother"),
    StoryParams("attic", "drum", "mask", "jam", "napkin", "Toby", "boy", "father"),
    StoryParams("kitchen", "duck", "hat", "ink", "patch", "Lena", "girl", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
