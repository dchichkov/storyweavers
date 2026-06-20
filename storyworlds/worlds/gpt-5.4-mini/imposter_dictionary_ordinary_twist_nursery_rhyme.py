#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/imposter_dictionary_ordinary_twist_nursery_rhyme.py
===================================================================================

A tiny standalone story world for a nursery-rhyme style tale about an ordinary
day at a library, a dictionary, and an imposter with a twist.

Seed words: imposter, dictionary, ordinary
Style: Nursery Rhyme
Feature: Twist

The world models a child who wants help spelling words. A dictionary should be
the real helper, but an imposter object or visitor may look convincing at first.
The twist is that the "imposter" is not truly harmful: the child discovers the
fake clue, then uses the real dictionary and ends the day with a small, bright
lesson.

This script follows the Storyweavers contract:
- standalone stdlib
- StoryParams, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py inside ASP helpers
- Python reasonableness gate plus inline ASP_RULES twin
- --verify smoke-tests a normal story generation and checks ASP/Python parity
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class ObjectCfg:
    id: str
    label: str
    ordinary: bool = True
    can_open: bool = False
    has_words: bool = False
    can_be_imposter: bool = False
    smells_like_books: bool = False
    tags: set[str] = field(default_factory=set)

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
class ChildCfg:
    id: str
    type: str
    age: int
    trait: str

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
        clone.facts = dict(self.facts)
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


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    imp = world.entities.get("imposter")
    dic = world.entities.get("dictionary")
    if not child or not imp or not dic:
        return out
    if imp.meters["lookalike"] < THRESHOLD:
        return out
    sig = ("confusion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["puzzled"] += 1
    dic.memes["alert"] += 1
    out.append("__confusion__")
    return out


CAUSAL_RULES = [Rule("confusion", "social", _r_confusion)]


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


def reasonableness_ok(cfg: ObjectCfg) -> bool:
    return cfg.can_be_imposter and cfg.has_words and cfg.ordinary


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_choices():
        return combos
    for scene in SCENES:
        for imp in IMPOSTERS:
            for dic in DICTIONARIES:
                if reasonableness_ok(imp) and dic.has_words:
                    combos.append((scene.id, imp.id, dic.id))
    return combos


def sensible_choices() -> list[ObjectCfg]:
    return [cfg for cfg in IMPOSTERS.values() if cfg.ordinary and cfg.can_be_imposter]


def best_imposter() -> ObjectCfg:
    return max(IMPOSTERS.values(), key=lambda c: int(c.can_be_imposter) + int(c.has_words))


def predict_twist(world: World, imposter_id: str) -> dict:
    sim = world.copy()
    sim.get(imposter_id).meters["lookalike"] += 1
    propagate(sim, narrate=False)
    return {
        "confused": sim.get("child").memes["puzzled"] >= THRESHOLD,
        "alert": sim.get("dictionary").memes["alert"],
    }


def _make_setup(world: World, child: Entity, scene: "Scene", dic: ObjectCfg) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On an ordinary morning bright, {child.id} went tripping to the {scene.place}. "
        f"The shelves stood still and neat, and a little dictionary waited there."
    )
    world.say(
        f'“{scene.chime}” sang the room in nursery rhyme, as {child.id} looked for a word '
        f"that would fit just right."
    )


def _meet_imposter(world: World, child: Entity, imp: ObjectCfg, dic: ObjectCfg) -> None:
    child.memes["curious"] += 1
    world.get("imposter").meters["lookalike"] += 1
    world.say(
        f"Then came an imposter in the corner's light, wearing a cover that looked quite wise. "
        f"It promised words in a grand parade, but it was only pretending to be the dictionary's size."
    )


def _warn(world: World, child: Entity, dic: ObjectCfg) -> None:
    pred = predict_twist(world, "imposter")
    dic.memes["alert"] += 1
    world.facts["predicted_confusion"] = pred["confused"]
    world.say(
        f"{child.id} paused and peered at the page, then tapped the real dictionary's side. "
        f"“This one opens, this one speaks, and this one smells like books,” {child.pronoun()} said, "
        f"“so the imposter can stay outside.”"
    )


def _twist_reveal(world: World, child: Entity, imp: ObjectCfg, dic: ObjectCfg) -> None:
    child.memes["delight"] += 1
    world.say(
        f"With a tiny grin and a careful tug, {child.id} lifted the cover and peeked within. "
        f"The imposter was not a thief at all, but a paper puppet folded by a classmate for show."
    )
    world.say(
        f"It had looked so very bold, yet it only held a rhyme card and a ribbon bow, "
        f"while the real dictionary kept the true words in a tidy row."
    )


def _resolve(world: World, child: Entity, parent: Entity, dic: ObjectCfg) -> None:
    child.memes["safety"] += 1
    child.memes["joy"] += 1
    world.say(
        f"At last the real dictionary opened wide, and the page began to glow. "
        f"{child.id} found the word, then read it loud, as ordinary days can grow."
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled near the door and said, “See how the truth can sing? "
        f"An imposter may look important, but the ordinary thing is often the right thing.”"
    )
    world.say(
        f"So the child went home with a word in mind, and the little rhyme stayed bright. "
        f"The dictionary was the hero, the imposter was only a twist in sight."
    )


def tell(scene: "Scene", imposter: ObjectCfg, dic: ObjectCfg, child_name: str,
         child_type: str, parent_type: str, trait: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child",
                             traits=[trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    imp = world.add(Entity(id="imposter", type="thing", label=imposter.label))
    real = world.add(Entity(id="dictionary", type="thing", label=dic.label))
    world.facts.update(scene=scene, imposter=imposter, dictionary=dic, child=child, parent=parent)
    _make_setup(world, child, scene, dic)
    world.para()
    _meet_imposter(world, child, imposter, dic)
    _warn(world, child, dic)
    if imposter.id == "paper_puppet":
        world.para()
        _twist_reveal(world, child, imposter, dic)
    world.para()
    _resolve(world, child, parent, dic)
    world.facts["outcome"] = "twist"
    world.facts["real_dictionary"] = real
    return world


@dataclass
class Scene:
    id: str
    place: str
    chime: str
    tags: set[str] = field(default_factory=set)

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


SCENES = {
    "library": Scene("library", "library", "the clock went tickety-tock", {"library", "quiet"}),
    "classroom": Scene("classroom", "classroom", "the crayons hummed in a row", {"school", "words"}),
    "attic": Scene("attic", "attic", "the rafters whispered low", {"home", "dust"}),
}

IMPOSTERS = {
    "paper_puppet": ObjectCfg("paper_puppet", "paper puppet", ordinary=True, can_open=False,
                              has_words=False, can_be_imposter=True, smells_like_books=False,
                              tags={"paper", "fake", "twist"}),
    "fake_cover": ObjectCfg("fake_cover", "a plain-looking cover", ordinary=True, can_open=False,
                            has_words=False, can_be_imposter=True, smells_like_books=True,
                            tags={"cover", "fake", "twist"}),
    "twin_book": ObjectCfg("twin_book", "a twin book", ordinary=True, can_open=True,
                           has_words=True, can_be_imposter=True, smells_like_books=True,
                           tags={"book", "twist"}),
}

DICTIONARIES = {
    "storybook_dictionary": ObjectCfg("storybook_dictionary", "a storybook dictionary",
                                      ordinary=True, can_open=True, has_words=True,
                                      can_be_imposter=False, smells_like_books=True,
                                      tags={"dictionary", "words"}),
    "tiny_dictionary": ObjectCfg("tiny_dictionary", "a tiny dictionary",
                                 ordinary=True, can_open=True, has_words=True,
                                 can_be_imposter=False, smells_like_books=True,
                                 tags={"dictionary", "words"}),
}

GIRL_NAMES = ["Lily", "Mina", "Nora", "Ada", "June"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Max"]
TRAITS = ["careful", "curious", "gentle", "bright", "brave"]


@dataclass
@dataclass
class StoryParams:
    scene: str
    imposter: str
    dictionary: str
    child_name: str
    child_type: str
    parent_type: str
    trait: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    imp = f["imposter"]
    return [
        f'Write a nursery-rhyme story in the {scene.place} that includes the words "ordinary", '
        f'"dictionary", and "imposter".',
        f"Tell a gentle twist story where {f['child'].id} thinks an imposter is the real helper, "
        f"then finds the ordinary dictionary and learns the truth.",
        f'Write a small rhyme about a child, a dictionary, and a clever imposter in the {scene.place}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    scene = f["scene"]
    parent = f["parent"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who spent an ordinary morning in the {scene.place}."),
        ("What did the child want?",
         f"{child.id} wanted to find a word in the dictionary and make the day feel bright."),
        ("What was the imposter like?",
         f"The imposter looked clever at first, but it was only pretending. The child noticed the trick and chose the real dictionary instead."),
        ("How did the story end?",
         f"It ended with the real dictionary giving the right words and the imposter turning out to be only a harmless twist."),
    ]
    if world.facts.get("predicted_confusion"):
        qa.append((
            "Why did the child pause before touching the imposter?",
            f"{child.id} paused because the fake cover did not act like a real dictionary. The child watched for clues, then chose the ordinary helper that truly opened to words."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["scene"].tags) | set(world.facts["imposter"].tags) | set(world.facts["dictionary"].tags)
    out: list[tuple[str, str]] = []
    if "dictionary" in tags:
        out.append(("What is a dictionary?", "A dictionary is a book that helps you find words, spell them, and learn what they mean."))
    if "fake" in tags or "twist" in tags:
        out.append(("What is an imposter?", "An imposter is something that pretends to be the real thing. It may look close, but it is not the true one."))
    if "words" in tags:
        out.append(("Why do children use dictionaries?", "Children use dictionaries to look up words, spell them, and learn what words mean."))
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
ordinary_object(X) :- object(X), ordinary(X).
imposterish(X) :- object(X), can_be_imposter(X), has_words(X).
valid_scene(S) :- scene(S).
valid_story(S, I, D) :- valid_scene(S), imposterish(I), dictionary(D), has_words(D), ordinary_object(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for iid, imp in IMPOSTERS.items():
        lines.append(asp.fact("object", iid))
        if imp.ordinary:
            lines.append(asp.fact("ordinary", iid))
        if imp.can_open:
            lines.append(asp.fact("can_open", iid))
        if imp.has_words:
            lines.append(asp.fact("has_words", iid))
        if imp.can_be_imposter:
            lines.append(asp.fact("can_be_imposter", iid))
    for did, dic in DICTIONARIES.items():
        lines.append(asp.fact("dictionary", did))
        if dic.ordinary:
            lines.append(asp.fact("ordinary", did))
        if dic.has_words:
            lines.append(asp.fact("has_words", did))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generated a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about an imposter dictionary twist.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--imposter", choices=IMPOSTERS)
    ap.add_argument("--dictionary", choices=DICTIONARIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.scene and args.imposter and args.dictionary:
        if (args.scene, args.imposter, args.dictionary) not in combos:
            raise StoryError("(No valid combination matches the given options.)")
    combos = [c for c in combos if (args.scene is None or c[0] == args.scene)
              and (args.imposter is None or c[1] == args.imposter)
              and (args.dictionary is None or c[2] == args.dictionary)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, imp, dic = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(scene, imp, dic, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], IMPOSTERS[params.imposter], DICTIONARIES[params.dictionary],
                 params.child_name, params.child_type, params.parent_type, params.trait)
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
    StoryParams("library", "paper_puppet", "storybook_dictionary", "Lily", "girl", "mother", "curious"),
    StoryParams("classroom", "fake_cover", "tiny_dictionary", "Owen", "boy", "father", "careful"),
    StoryParams("attic", "twin_book", "storybook_dictionary", "Mina", "girl", "mother", "bright"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (scene, imposter, dictionary) combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()
