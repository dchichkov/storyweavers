#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gist_perception_zip_magic_surprise_tall_tale.py
===============================================================================

A small, self-contained tall-tale storyworld.

Seed words / features:
- gist
- perception
- zip
- Magic
- Surprise
- Tall Tale

Premise:
A child and a grown-up prepare a harmless magic trick for a town fair. The child
misreads the situation, thinks the trick has failed, and zips off to fetch help.
The surprise is that the "failing" trick was the trick all along: a hidden ribbon,
a clever pull, and a grand reveal that changes the child's perception.

The world is model-driven: entities accumulate physical meters and emotional memes,
causal rules update state, and the prose renderer narrates from that state.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

GIST_WORD = "gist"
PERCEPTION_WORD = "perception"
ZIP_WORD = "zip"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Theme:
    id: str
    setting: str
    stage: str
    tale_title: str
    big_image: str
    ending_image: str
    wonder_verb: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Prop:
    id: str
    label: str
    phrase: str
    makes_reveal: bool = False
    can_zip: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Surprise:
    id: str
    label: str
    effect: str
    reveal: str
    meter: str = "reveal"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        clone = World()
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
            value = __import__("collections").defaultdict(float)
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


def _r_gasp(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["startled"] < THRESHOLD:
        return out
    sig = ("gasp",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["confused"] += 1
    out.append("The child blinked twice and tried to make the tall tale fit what saw.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    stage = world.entities.get("stage")
    ribbon = world.entities.get("ribbon")
    child = world.entities.get("child")
    if not stage or not ribbon or not child:
        return out
    if stage.meters["ready"] < THRESHOLD or ribbon.meters["hidden"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stage.meters["shining"] += 1
    child.memes["wonder"] += 2
    out.append("A secret shine climbed the stage, as if the boards had remembered moonlight.")
    return out


CAUSAL_RULES = [Rule("gasp", "social", _r_gasp), Rule("reveal", "magic", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_surprises() -> list[Surprise]:
    return [s for s in SURPRISES.values() if s.meter == "reveal"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for prop_id, prop in PROPS.items():
            for surprise_id, surprise in SURPRISES.items():
                if prop.makes_reveal and surprise.meter == "reveal":
                    combos.append((theme, prop_id, surprise_id))
    return combos


@dataclass
@dataclass
class StoryParams:
    theme: str
    prop: str
    surprise: str
    hero: str
    hero_gender: str
    grownup: str
    grownup_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def tell(theme: Theme, prop: Prop, surprise: Surprise, hero_name: str, hero_gender: str,
         grownup_name: str, grownup_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=hero_gender, role="hero", label=hero_name))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_gender, role="guide", label=grownup_name))
    stage = world.add(Entity(id="stage", kind="thing", type="stage", label="the stage"))
    ribbon = world.add(Entity(id="ribbon", kind="thing", type="ribbon", label=prop.label))
    ticket = world.add(Entity(id="ticket", kind="thing", type="ticket", label=surprise.label))

    child.memes["curiosity"] += 1
    grownup.memes["calm"] += 1
    stage.meters["ready"] += 1
    ribbon.meters["hidden"] += 1

    world.say(
        f"Once, in a town so wide the wind could lose its way, {hero_name} and {grownup_name} stood beside {theme.stage} for {theme.tale_title}."
    )
    world.say(
        f"The day was full of {GIST_WORD}s and shiny guesses, but only the {PERCEPTION_WORD} of a good look would tell the whole truth."
    )
    world.say(
        f"Everyone said the setup was plain enough: {theme.big_image}"
    )

    world.para()
    world.say(
        f"{hero_name} squinted at {prop.phrase} and thought it looked too tiny for magic. 'Where is the trick?' {child.pronoun().capitalize()} asked."
    )
    child.memes["startled"] += 1
    child.memes["doubt"] += 1
    world.say(
        f"{grownup_name} smiled and said, 'Keep your {PERCEPTION_WORD} sharp; even a little {ZIP_WORD} can hide a big surprise.'"
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then came the hush before the fair. {hero_name} tugged once, and the hidden ribbon went {ZIP_WORD} through a loop as fast as a swallow crossing a lake."
    )
    ribbon.meters["hidden"] = 0
    ribbon.meters["pulled"] += 1
    surprise.meter = "reveal"
    stage.meters["ready"] += 1
    stage.meters["shining"] += 1
    ticket.meters["opened"] += 1
    world.say(
        f"Up rose {surprise.effect}, and the so-called ordinary thing became {surprise.reveal}."
    )
    world.say(
        f"The whole crowd laughed with delight, for the trick had been hidden in plain sight all along."
    )
    child.memes["wonder"] += 2
    child.memes["joy"] += 1

    world.para()
    world.say(
        f"{hero_name} blinked, then grinned from ear to ear. The child's {PERCEPTION_WORD} had changed: what looked small now looked clever, and what looked simple now looked grand."
    )
    world.say(
        f"By sunset, {theme.ending_image}, and {hero_name} told the {GIST_WORD} of the story to anyone who would listen."
    )

    world.facts.update(
        child=child,
        grownup=grownup,
        stage=stage,
        ribbon=ribbon,
        ticket=ticket,
        theme=theme,
        prop=prop,
        surprise=surprise,
        outcome="reveal",
    )
    return world


THEMES = {
    "fair": Theme("fair", "the fairground", "the tallest wagon in town", "The Zip of Moonlight", "a plain little stage with lanterns waiting", "the fairground glowed like a handful of dropped stars", "wonder"),
    "barn": Theme("barn", "the old barn", "a barn loft full of dust and hay", "The Zip of Thunder", "a hayloft with one lonely rope hanging down", "the barn windows flashed gold at the edges", "wonder"),
    "river": Theme("river", "the riverbank", "a river stage built on a raft", "The Zip of Riverbells", "a raft with blue paint and a rope curtain", "the river carried the applause downstream", "wonder"),
}

PROPS = {
    "zip_ribbon": Prop("zip_ribbon", "a ribbon", "a ribbon with a silver knot", makes_reveal=True, can_zip=True),
    "zip_curtain": Prop("zip_curtain", "a curtain cord", "a curtain cord with a bright tag", makes_reveal=True, can_zip=True),
    "zip_bag": Prop("zip_bag", "a bag clasp", "a little bag clasp with a brass click", makes_reveal=True, can_zip=True),
}

SURPRISES = {
    "lantern": Surprise("lantern", "the lantern show", "a lantern glow", "a moon-bright secret"),
    "paper_star": Surprise("paper_star", "the paper star", "a paper star", "a sky-sized surprise"),
    "toy_horse": Surprise("toy_horse", "the toy horse", "a toy horse", "a galloping surprise"),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Sadie", "June", "Pippa"]
BOY_NAMES = ["Otis", "Ben", "Clare", "Jasper", "Walt", "Theo"]
ADULT_NAMES = ["Aunt Bea", "Mr. Finn", "Mama Rose", "Uncle June", "Pa Hatch"]

KNOWLEDGE = {
    "gist": [("What is the gist of a story?", "The gist is the main idea, the big point you remember after the details are gone.")],
    "perception": [("What is perception?", "Perception is the way you notice and understand what you see, hear, and feel.")],
    "zip": [("What does zip mean?", "Zip can mean a quick little movement or sound, like something moving very fast.")],
    "magic": [("What is magic in a story?", "Magic is a surprising thing that seems impossible, but in a story it can happen and make the tale feel wondrous.")],
    "surprise": [("Why are surprises exciting?", "Surprises make people blink and smile because they did not know what was coming next.")],
    "tall_tale": [("What is a tall tale?", "A tall tale is a story told in a huge, playful way, with big exaggerations and a lot of fun.")],
}
KNOWLEDGE_ORDER = ["gist", "perception", "zip", "magic", "surprise", "tall_tale"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a child that uses the words "{GIST_WORD}", "{PERCEPTION_WORD}", and "{ZIP_WORD}".',
        f"Tell a magical surprise story where {f['child'].label} thinks the trick is plain, then learns the real {GIST_WORD} of it.",
        f"Write a playful tale with a sudden reveal, where {ZIP_WORD} helps show that first {PERCEPTION_WORD} was not enough.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, grownup, theme, prop, surprise = f["child"], f["grownup"], f["theme"], f["prop"], f["surprise"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label} and {grownup.label}, who worked together at {theme.stage}. {grownup.label} helped turn a small trick into a big surprise."
        ),
        QAItem(
            question=f"Why did {child.label} get confused at first?",
            answer=f"{child.label} used first {PERCEPTION_WORD} and thought {prop.phrase} looked too plain for magic. But the real trick was hidden, so the {GIST_WORD} was easy to miss at first."
        ),
        QAItem(
            question=f"What happened when the hidden ribbon went {ZIP_WORD}?",
            answer=f"The hidden ribbon went {ZIP_WORD} through the loop, and then {surprise.effect} appeared. That was the moment the tale changed from guessing to grinning."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.label} understanding the trick and smiling at the grand reveal. The ending image shows the fairground bright, the crowd happy, and the surprise fully seen."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {GIST_WORD, PERCEPTION_WORD, ZIP_WORD, "magic", "surprise", "tall_tale"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
    return out


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
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world wants a hidden reveal with a magical surprise, so the chosen parts must make a real zip-and-reveal possible.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.makes_reveal:
            lines.append(asp.fact("makes_reveal", pid))
        if p.can_zip:
            lines.append(asp.fact("can_zip", pid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("meter", sid, s.meter))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, P, S) :- theme(T), prop(P), surprise(S), makes_reveal(P), meter(S, "reveal").
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combos gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, prop=None, surprise=None, hero=None, hero_gender=None, grownup=None, grownup_gender=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-test generate() produced a story.")
    except Exception as ex:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale magic surprise storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup")
    ap.add_argument("--grownup-gender", choices=["woman", "man", "mother", "father"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    combos = [c for c in combos if (args.theme is None or c[0] == args.theme)
              and (args.prop is None or c[1] == args.prop)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, prop, surprise = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(ADULT_NAMES)
    grownup_gender = args.grownup_gender or rng.choice(["mother", "father", "woman", "man"])
    return StoryParams(theme, prop, surprise, hero, hero_gender, grownup, grownup_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], PROPS[params.prop], SURPRISES[params.surprise],
                 params.hero, params.hero_gender, params.grownup, params.grownup_gender)
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
    StoryParams("fair", "zip_ribbon", "lantern", "Mina", "girl", "Aunt Bea", "woman"),
    StoryParams("barn", "zip_curtain", "paper_star", "Otis", "boy", "Mr. Finn", "man"),
    StoryParams("river", "zip_bag", "toy_horse", "Nora", "girl", "Mama Rose", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for t, p, s in combos:
            print(f"  {t:8} {p:12} {s}")
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
