#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/plasticene_cautionary_misunderstanding_flashback_myth.py
========================================================================================

A standalone story world for a small mythic cautionary tale about a child who
mistakes a treasured lump of plasticene for something wondrous, then remembers a
warning in a flashback and chooses a safer, kinder use.

The world is intentionally tiny:
- one child
- one elder helper
- one precious plasticene object
- one misunderstood moment
- one cautionary flashback
- one gentle resolution

The simulation tracks physical meters and emotional memes, and story text is
rendered from those state changes.
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
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "elder": "elder"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Myth:
    id: str
    scene: str
    place: str
    omen: str
    title: str
    ending_image: str

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
class Plasticene:
    id: str
    label: str
    phrase: str
    color: str
    shape: str
    mystery: str
    safe_use: str
    tags: set[str] = field(default_factory=set)

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
class Warning:
    id: str
    lesson: str
    flashback: str
    misunderstanding: str
    reply: str
    tags: set[str] = field(default_factory=set)

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
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
@dataclass
class StoryParams:
    myth: str
    plasticene: str
    warning: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
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


MYTHS = {
    "mountain": Myth("mountain", "a bright mountain shrine", "the shrine", "wind and thunder", "The Hill of Quiet Clay", "the child held the lantern beside the clay"),
    "river": Myth("river", "a moonlit riverbank", "the riverbank", "mist and singing water", "The River of Echoing Hands", "the child set the clay beside the river stones"),
    "grove": Myth("grove", "an old grove of fig trees", "the grove", "soft leaves and owl-song", "The Grove of Listening Leaves", "the child cradled the clay under the fig boughs"),
}

PLASTICENE = {
    "red": Plasticene("red", "plasticene", "a lump of red plasticene", "red", "small star", "looked like a heart or a sun", "make a tiny statue"),
    "blue": Plasticene("blue", "plasticene", "a lump of blue plasticene", "blue", "wave", "looked like a fish or a sky-stone", "make a little boat"),
    "green": Plasticene("green", "plasticene", "a lump of green plasticene", "green", "leaf", "looked like a leaf or a sleeping beetle", "make a leaf charm"),
}

WARNINGS = {
    "soften": Warning("soften", "keep it away from the fire", "In a flashback, the elder had said the clay would soften in the fire and lose its shape.", "the child had misunderstood the warning as a promise of magic", "that was not the kind of magic anyone should test", tags={"fire", "flashback"}),
    "rain": Warning("rain", "keep it from the rain", "In a flashback, the elder had said the clay would wash away in hard rain and stain the path.", "the child had misunderstood the warning as a joke about the river spirit", "the river spirit was only warning about loss", tags={"water", "flashback"}),
    "drop": Warning("drop", "hold it with both hands", "In a flashback, the elder had said the clay could drop to the stones and break into dusty bits.", "the child had misunderstood the warning as a riddle", "the riddle had really been a kindness", tags={"stones", "flashback"}),
}

CHILDREN = [
    ("Mira", "girl"),
    ("Taro", "boy"),
    ("Lina", "girl"),
    ("Niko", "boy"),
]
ELDERS = [
    ("Aunt Sera", "woman"),
    ("Old Ivo", "man"),
    ("Grandmother Vale", "woman"),
    ("Uncle Ren", "man"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(m, p, w) for m in MYTHS for p in PLASTICENE for w in WARNINGS]


def caution_reasonable(params: StoryParams) -> bool:
    return params.plasticene in PLASTICENE and params.warning in WARNINGS and params.myth in MYTHS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic cautionary tale with a flashback and a misunderstanding.")
    ap.add_argument("--myth", choices=MYTHS)
    ap.add_argument("--plasticene", choices=PLASTICENE)
    ap.add_argument("--warning", choices=WARNINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
    myth = args.myth or rng.choice(list(MYTHS))
    plasticene = args.plasticene or rng.choice(list(PLASTICENE))
    warning = args.warning or rng.choice(list(WARNINGS))
    if not caution_reasonable(StoryParams(myth, plasticene, warning, "", "girl", "", "woman")):
        raise StoryError("No valid story combination.")
    name, gender = (args.name, args.gender) if args.name and args.gender else rng.choice(CHILDREN)
    if args.gender and not args.name:
        pool = [x for x in CHILDREN if x[1] == args.gender]
        name, gender = rng.choice(pool)
    elder, elder_gender = (args.elder, args.elder_gender) if args.elder and args.elder_gender else rng.choice(ELDERS)
    return StoryParams(myth, plasticene, warning, name, gender, elder, elder_gender)


def asp_facts() -> str:
    import asp
    lines = []
    for k in MYTHS:
        lines.append(asp.fact("myth", k))
    for k in PLASTICENE:
        lines.append(asp.fact("plasticene", k))
    for k in WARNINGS:
        lines.append(asp.fact("warning", k))
        lines.append(asp.fact("flashback", k))
    return "\n".join(lines)


ASP_RULES = r"""
valid(M,P,W) :- myth(M), plasticene(P), warning(W).
flashback(W) :- warning(W).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    print("OK: ASP matches Python." if ok else "MISMATCH: ASP and Python differ.")
    return 0 if ok else 1


def tell(params: StoryParams) -> World:
    world = World()
    myth = MYTHS[params.myth]
    clay = PLASTICENE[params.plasticene]
    warning = WARNINGS[params.warning]
    child = world.add(Entity(params.child_name, kind="character", type=params.child_gender, role="child", age=6, traits=["curious", "dreaming"]))
    elder = world.add(Entity(params.elder_name, kind="character", type=params.elder_gender, role="elder", age=60))
    child.memes["wonder"] += 1
    child.memes["trust"] += 1
    elder.memes["care"] += 1
    world.say(f"Long ago, when {myth.place} still listened, {child.id} carried {clay.phrase} through {myth.scene}.")
    world.say(f"{child.id} thought {clay.phrase} was a sign from the old gods, because it {clay.mystery}.")
    world.para()
    world.say(f"{child.id} wanted to {clay.safe_use}, but {elder.id} had given a warning before: {warning.lesson}.")
    world.say(f"The child only half remembered. {warning.misunderstanding}.")
    world.para()
    child.memes["confusion"] += 1
    child.memes["temptation"] += 1
    world.say(warning.flashback)
    world.say(f"Then the memory returned at once: {warning.reply}.")
    child.memes["fear"] += 1
    if params.warning == "soften":
        child.meters["heat"] += 0.0
        world.say(f"{child.id} looked at the fire and finally understood that a true treasure can be ruined in a moment.")
    elif params.warning == "rain":
        world.say(f"{child.id} looked toward the river and understood that something precious must be kept dry and safe.")
    else:
        world.say(f"{child.id} knelt lower and held the clay with both hands, careful as a temple priest with a sacred bowl.")
    world.para()
    child.memes["resolve"] += 1
    child.memes["love"] += 1
    world.say(f"So {child.id} chose the safer path. {myth.ending_image.capitalize()}, and {child.id} shaped {clay.safe_use} instead of chasing a false miracle.")
    world.say(f"{elder.id} smiled, for the old warning had become wisdom.")
    world.facts.update(child=child, elder=elder, myth=myth, clay=clay, warning=warning, outcome="safe")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic cautionary story that includes the word "plasticene" and a flashback warning.',
        f"Tell a story where {f['child'].id} misunderstands an elder's warning about {f['clay'].label}, remembers it later, and makes a safer choice.",
        f'Write a short myth-like tale for children with the themes Cautionary, Misunderstanding, and Flashback, using "plasticene".',
    ]


def story_qa(world: World) -> list[QAItem]:
    c, e, myth, clay, warning = world.facts["child"], world.facts["elder"], world.facts["myth"], world.facts["clay"], world.facts["warning"]
    return [
        QAItem(question="What did the child carry?", answer=f"{c.id} carried {clay.phrase} through {myth.place}. It seemed magical because it was so bright and small."),
        QAItem(question="What was the misunderstanding?", answer=f"{c.id} misunderstood {e.id}'s warning and thought it was a story about magic instead of safety. The flashback later showed that the warning was meant to protect the clay."),
        QAItem(question="How did the story end?", answer=f"It ended safely: {c.id} remembered the warning, chose the safer path, and made {clay.safe_use} instead. The old lesson became wisdom in the ending image."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is plasticene?", answer="Plasticene is a soft, moldable material that people can press and shape with their hands. It is good for making little figures and pretend treasures."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is a scene that shows something from before the main moment. Writers use it to help the reader remember an old warning or a past event."),
        QAItem(question="What does cautionary mean?", answer="Cautionary means the story is trying to warn you about a mistake. It shows a bad idea first so the safer choice feels important."),
    ]


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
        if e.age:
            bits.append(f"age={e.age}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams("mountain", "red", "soften", "Mira", "girl", "Aunt Sera", "woman"),
    StoryParams("river", "blue", "rain", "Taro", "boy", "Old Ivo", "man"),
    StoryParams("grove", "green", "drop", "Lina", "girl", "Grandmother Vale", "woman"),
]


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.myth and args.myth not in MYTHS:
        raise StoryError("Unknown myth.")
    if args.plasticene and args.plasticene not in PLASTICENE:
        raise StoryError("Unknown plasticene.")
    if args.warning and args.warning not in WARNINGS:
        raise StoryError("Unknown warning.")
    myth = args.myth or rng.choice(list(MYTHS))
    plasticene = args.plasticene or rng.choice(list(PLASTICENE))
    warning = args.warning or rng.choice(list(WARNINGS))
    if args.gender and not args.name:
        pool = [x for x in CHILDREN if x[1] == args.gender]
        if not pool:
            raise StoryError("No child name matches that gender.")
        name, gender = rng.choice(pool)
    else:
        name, gender = (args.name, args.gender) if args.name and args.gender else rng.choice(CHILDREN)
    elder, elder_gender = (args.elder, args.elder_gender) if args.elder and args.elder_gender else rng.choice(ELDERS)
    return StoryParams(myth, plasticene, warning, name, gender, elder, elder_gender)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        smoke = generate(CURATED[0])
        if not smoke.story:
            raise SystemExit(1)
        print(smoke.story.splitlines()[0])
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for t in combos:
            print(*t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
