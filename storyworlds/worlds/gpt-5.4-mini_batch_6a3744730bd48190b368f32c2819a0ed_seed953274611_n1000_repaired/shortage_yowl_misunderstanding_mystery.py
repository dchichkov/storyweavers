#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shortage_yowl_misunderstanding_mystery.py
=========================================================================

A small storyworld about a mysterious shortage, a loud yowl, and a mistaken
reading of the clues. A child notices something missing, suspects the wrong
thing, follows the trail, and discovers a simple explanation that changes what
everyone does next.

The story leans mystery-like: a puzzling absence, a wrong guess, a revealing
trace, and a calm ending that proves what the real cause was.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SHORTAGE_NEEDS = {"food", "milk", "crackers", "supplies", "blankets"}
YOWL_SOURCES = {"cat", "kitten", "dog", "owl"}
MISREAD_OBJECTS = {"pantry", "basket", "table", "closet", "hallway"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    place: str
    shortage: str
    yowler: str
    witness: str
    witness_gender: str
    helper: str
    helper_gender: str
    misunderstanding: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    apply: callable
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    witness = world.get("witness")
    pantry = world.get("pantry")
    if pantry.meters["shortage"] >= THRESHOLD and ("notice",) not in world.fired:
        world.fired.add(("notice",))
        witness.memes["unease"] += 1
        out.append("__notice__")
    return out


def _r_yowl(world: World) -> list[str]:
    out: list[str] = []
    yowler = world.get("yowler")
    if yowler.meters["yowl"] >= THRESHOLD and ("yowl",) not in world.fired:
        world.fired.add(("yowl",))
        world.get("hallway").meters["echo"] += 1
        world.get("witness").memes["alarm"] += 1
        out.append("__yowl__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


RULES = [Rule("notice", _r_notice), Rule("yowl", _r_yowl)]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", p) for p in PLACES]
    for sid, s in SHORTAGES.items():
        lines.append(asp.fact("shortage", sid))
        lines.append(asp.fact("needs", sid, s.need))
    for yid, y in YOWLERS.items():
        lines.append(asp.fact("yowler", yid))
        lines.append(asp.fact("makes_yowl", yid))
    for m in MISTAKES:
        lines.append(asp.fact("misunderstanding", m))
    return "\n".join(lines)


ASP_RULES = r"""
warning(M) :- misunderstanding(M).
trouble(S) :- shortage(S).
mystery(X) :- warning(X), trouble(_).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_mystery() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/1."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    import asp
    py = {(p,) for p in mystery_tags()}
    cl = set(asp_mystery())
    if py != cl:
        print("MISMATCH in mystery tags")
        return 1
    try:
        sample = generate(default_params(random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def mystery_tags() -> list[str]:
    return ["mystery"]


@dataclass
class ShortageCfg:
    id: str
    need: str
    label: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class YowlCfg:
    id: str
    label: str
    source: str
    reason: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class PlaceCfg:
    id: str
    scene: str
    clue: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SHORTAGES = {
    "pantry": ShortageCfg(id="pantry", need="food", label="the pantry"),
    "basket": ShortageCfg(id="basket", need="crackers", label="the basket"),
    "closet": ShortageCfg(id="closet", need="blankets", label="the closet"),
}

YOWLERS = {
    "cat": YowlCfg(id="cat", label="the cat", source="cat", reason="wanted the door open"),
    "kitten": YowlCfg(id="kitten", label="the kitten", source="cat", reason="could not reach the shelf"),
    "dog": YowlCfg(id="dog", label="the dog", source="dog", reason="heard the pantry door"),
}

PLACES = {
    "kitchen": PlaceCfg(id="kitchen", scene="a quiet kitchen", clue="the crumb trail"),
    "hall": PlaceCfg(id="hall", scene="a long hallway", clue="the echo"),
    "porch": PlaceCfg(id="porch", scene="a dim porch", clue="the shadow by the step"),
}

MISTAKES = {"misunderstanding", "cat", "noise"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for shortage in SHORTAGES:
            for yowler in YOWLERS:
                if shortage in SHORTAGE_NEEDS and yowler in YOWL_SOURCES:
                    combos.append((place, shortage, yowler))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about a shortage and a yowl.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--shortage", choices=SHORTAGES)
    ap.add_argument("--yowler", choices=YOWLERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.shortage is None or c[1] == args.shortage)
              and (args.yowler is None or c[2] == args.yowler)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, shortage, yowler = rng.choice(sorted(combos))
    witness_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if witness_gender == "boy" else "boy"
    witness = rng.choice(["Mina", "June", "Nora", "Toby", "Eli"])
    helper = rng.choice(["Mom", "Dad", "Aunt Bea", "Uncle Ray"])
    misunderstanding = rng.choice(sorted(MISREAD_OBJECTS))
    return StoryParams(
        place=place,
        shortage=shortage,
        yowler=yowler,
        witness=witness,
        witness_gender=witness_gender,
        helper=helper,
        helper_gender=helper_gender,
        misunderstanding=misunderstanding,
    )


def setup_world(params: StoryParams) -> World:
    w = World()
    witness = w.add(Entity(id="witness", kind="character", type=params.witness_gender, label=params.witness, role="witness"))
    helper = w.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper, role="helper"))
    yowler = w.add(Entity(id="yowler", kind="character", type="thing", label=params.yowler, role="yowler"))
    pantry = w.add(Entity(id="pantry", type="place", label=SHORTAGES[params.shortage].label))
    hallway = w.add(Entity(id="hallway", type="place", label=PLACES[params.place].id))
    pantry.meters["shortage"] += 1
    yowler.meters["yowl"] += 1
    w.facts.update(params=params, witness=witness, helper=helper, yowler=yowler, pantry=pantry, hallway=hallway)
    return w


def tell(world: World, params: StoryParams) -> None:
    witness = world.get("witness")
    helper = world.get("helper")
    yowler = world.get("yowler")
    pantry = world.get("pantry")
    place = PLACES[params.place]
    shortage = SHORTAGES[params.shortage]
    world.say(f"{witness.label} was in {place.scene}, where something felt off.")
    world.say(f"At the pantry, there was a shortage: the shelf should have held {shortage.need}, but it did not.")
    world.para()
    world.say(f"Then a loud yowl cut through the quiet.")
    world.say(f"{witness.label} turned toward the sound and pointed at {params.misunderstanding}, sure that was the clue.")
    witness.memes["guess"] += 1
    world.say(f'“It must mean someone took it,” {witness.label} whispered, but that was the wrong idea.')
    world.para()
    pantry.meters["shortage"] += 1
    yowler.meters["yowl"] += 1
    propagate(world, narrate=False)
    world.say(f"{helper.label} knelt beside {witness.label} and followed the crumb trail instead.")
    world.say(f"The trail led to a tipped basket behind the chair, where the missing {shortage.need} had rolled away.')
    world.para()
    world.say(f'“Oh,” {witness.label} said. “The yowl was not a warning after all.”')
    world.say(f"{helper.label} smiled and gave the stray item back to the shelf, and the room felt tidy again.")
    world.say(f"After that, {witness.label} listened more carefully to clues, and the mystery was simple once the real trail was seen.")


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"What problem started the story?",
            answer=f"There was a shortage in the {SHORTAGES[p.shortage].label}, so something that should have been there was missing. That made the scene feel mysterious right away."
        ),
        QAItem(
            question=f"Why did {world.get('witness').label} think the yowl meant something else?",
            answer=f"{world.get('witness').label} misunderstood the sound and pointed at {p.misunderstanding}. The yowl seemed like a clue, but it only sounded frightening."
        ),
        QAItem(
            question="What was the real cause of the shortage?",
            answer=f"The missing {SHORTAGES[p.shortage].need} had rolled behind a chair with the tipped basket. Once the real trail was followed, the shortage made sense."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem("What is a shortage?", "A shortage means there is less of something than there should be. It leaves a place looking empty or unfinished."),
        QAItem("What is a yowl?", "A yowl is a loud cry, often from an animal. It can startle people because it sounds strong and sudden."),
        QAItem("What should you do when a clue seems confusing?", "Slow down and check the details one by one. A mystery often makes sense after you look again."),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a mystery story for a child that includes the words shortage and yowl.",
        f"Tell a story where {world.get('witness').label} hears a yowl, sees a shortage, and first makes the wrong guess.",
        f"Write a gentle mystery where a misunderstanding leads to a false clue, but the real cause is found by following the trail.",
    ]


def generate(params: StoryParams) -> StorySample:
    if params.shortage not in SHORTAGE_NEEDS or params.yowler not in YOWL_SOURCES:
        raise StoryError("This combination does not support a shortage mystery.")
    world = setup_world(params)
    tell(world, params)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"  {e.id}: meters={meters} memes={memes} label={e.label}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def default_params(rng: random.Random) -> StoryParams:
    return resolve_params(argparse.Namespace(place=None, shortage=None, yowler=None), rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show mystery/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mystery tags:", asp_mystery())
        print("Valid combos:", valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place, shortage, yowler in valid_combos():
            params = StoryParams(
                place=place,
                shortage=shortage,
                yowler=yowler,
                witness="Mina",
                witness_gender="girl",
                helper="Mom",
                helper_gender="girl",
                misunderstanding="pantry",
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
