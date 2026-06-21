#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gerbil_big_transformation_curiosity_mystery.py
==============================================================================

A tiny mystery storyworld about a curious child, a gerbil, and a strange
transformation into something big. The world is built around a few state changes:
curiosity rises, clues accumulate, a hidden change is discovered, and the ending
proves what became big.

The stories stay child-facing and concrete: a small pet cage, a strange sound,
a missing object, a surprising discovery, and a calm explanation at the end.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    hiding_place: str
    clue_sound: str
    glow: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Transformation:
    id: str
    source: str
    result: str
    reveal: str
    effect: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Mystery:
    id: str
    hook: str
    question: str
    answer: str
    tags: set[str] = field(default_factory=set)
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str
    transformation: str
    mystery: str
    hero_name: str
    hero_type: str
    pet_name: str
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


SETTINGS = {
    "cage_room": Setting(
        id="cage_room",
        place="the little room beside the kitchen",
        mood="quiet and warm",
        hiding_place="under the blanket",
        clue_sound="a soft scritch-scritch",
        glow="a tiny yellow glow",
        tags={"mystery", "gerbil"},
    ),
    "attic": Setting(
        id="attic",
        place="the dusty attic",
        mood="still and echoey",
        hiding_place="behind an old trunk",
        clue_sound="a quick patter",
        glow="a square of moonlight",
        tags={"mystery", "gerbil"},
    ),
}

TRANSFORMATIONS = {
    "big_footprints": Transformation(
        id="big_footprints",
        source="the floor",
        result="huge footprints",
        reveal="the marks kept growing until they looked as big as a plate",
        effect="big",
        tags={"big", "transformation"},
    ),
    "big_shadow": Transformation(
        id="big_shadow",
        source="the wall",
        result="a big shadow",
        reveal="the shadow stretched high and wide when the lamp turned on",
        effect="big",
        tags={"big", "transformation"},
    ),
    "big_balloon": Transformation(
        id="big_balloon",
        source="the bag",
        result="a big balloon",
        reveal="the little bundle puffed up until it was big and round",
        effect="big",
        tags={"big", "transformation"},
    ),
}

MYSTERIES = {
    "vanishing_seed": Mystery(
        id="vanishing_seed",
        hook="a seed had vanished from the shelf",
        question="who took it and where did it go?",
        answer="the gerbil had hidden it as a treasure",
        tags={"curiosity", "mystery"},
    ),
    "muffled_noise": Mystery(
        id="muffled_noise",
        hook="there was a muffled noise in the dark corner",
        question="what was making that secret sound?",
        answer="the gerbil was moving a little toy and making the sound on purpose",
        tags={"curiosity", "mystery"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Tom", "Ben", "Noah", "Eli", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid in TRANSFORMATIONS:
            for mid in MYSTERIES:
                combos.append((sid, tid, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child, a gerbil, a mystery, and a big surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--pet-name")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.transformation is None or c[1] == args.transformation)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, transformation, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    pet_name = args.pet_name or rng.choice(["Nibbles", "Pip", "Mochi", "Gizmo"])
    return StoryParams(
        setting=setting,
        transformation=transformation,
        mystery=mystery,
        hero_name=name,
        hero_type=gender,
        pet_name=pet_name,
    )


def _build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError(f"Unknown transformation: {params.transformation}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")

    world = World()
    setting = SETTINGS[params.setting]
    trans = TRANSFORMATIONS[params.transformation]
    mystery = MYSTERIES[params.mystery]

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, traits=["curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label="the parent"))
    gerbil = world.add(Entity(id=params.pet_name, kind="character", type="thing", label="the gerbil", traits=["small", "quick"], tags={"gerbil"}))
    clue = world.add(Entity(id="clue", label=trans.result, tags=trans.tags))
    mystery_obj = world.add(Entity(id="mystery", label=mystery.hook, tags=mystery.tags))

    hero.memes["curiosity"] = 2.0
    hero.memes["wonder"] = 1.0
    gerbil.meters["small"] = 1.0
    gerbil.meters["active"] = 1.0
    world.facts.update(
        hero=hero,
        parent=parent,
        gerbil=gerbil,
        setting=setting,
        transformation=trans,
        mystery=mystery,
        clue=clue,
        mystery_obj=mystery_obj,
    )

    world.say(
        f"{hero.id} lived in {setting.place}, a {setting.mood} place where "
        f"{mystery.hook}."
    )
    world.say(
        f"One day, {hero.id} noticed the {setting.clue_sound} near the gerbil cage."
    )
    world.para()
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} leaned closer. {hero.pronoun().capitalize()} wanted to know "
        f"{mystery.question}"
    )
    world.say(
        f"Inside the dim corner, the gerbil looked very small beside "
        f"{setting.glow}."
    )

    world.para()
    if trans.effect == "big":
        world.say(
            f"Then something strange happened. {trans.reveal.capitalize()}."
        )
        gerbil.meters["size"] = 3.0
        gerbil.labels = None
        clue.meters["big"] = 1.0
    hero.memes["surprise"] = 1.0

    world.para()
    world.say(
        f"{hero.id} blinked and looked again. The tiny gerbil was no longer tiny; "
        f"{gerbil.label_word if gerbil.label else 'it'} seemed {trans.effect} and "
        f"full of secrets."
    )
    world.say(
        f"{hero.id} called softly, and the gerbil poked its nose out from "
        f"{setting.hiding_place}."
    )

    world.para()
    world.say(
        f"At last {hero.id} understood the mystery: {mystery.answer}. "
        f"The curious look on {hero.id}'s face turned into a smile."
    )
    world.say(
        f"That night, the gerbil stayed safe in its cage, and the big clue was no "
        f"longer scary at all."
    )
    world.say(
        f"Now {hero.id} knew that curiosity could lead to a secret answer, and a "
        f"small gerbil could make a very big surprise."
    )

    world.facts["outcome"] = "solved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    trans = f["transformation"]
    return [
        f'Write a child-friendly mystery story that includes the words "gerbil" and "big".',
        f"Tell a story where {hero.id} gets curious, follows a clue, and discovers why {mystery.hook}.",
        f"Write a gentle mystery with a gerbil and a big surprise, where curiosity leads to the answer.",
        f"Create a short story about {hero.id} and a gerbil that becomes part of a big transformation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    trans = f["transformation"]
    gerbil = f["gerbil"]
    setting = f["setting"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and the gerbil in {setting.place}. {hero.id} is the child who follows the clue and notices the change."),
        ("What made the story feel mysterious?",
         f"{mystery.hook} made the room feel mysterious. The clue sound and the hidden answer kept {hero.id} wondering what was happening."),
        ("What happened to the gerbil?",
         f"The gerbil became part of a big surprise. {trans.reveal.capitalize()}, so {hero.id} saw that the little pet was connected to the mystery."),
        ("How did the story end?",
         f"It ended with the mystery solved and everyone calm again. {hero.id} understood the answer, and the gerbil stayed safe while the big clue made sense."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gerbil?",
            answer="A gerbil is a small furry pet that likes to scurry, dig, and hide things.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes you ask questions and look for answers when something seems strange.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood yet, so people look for clues and try to solve it.",
        ),
        QAItem(
            question="What does big mean?",
            answer="Big means larger than usual. A thing can become big in size, or it can feel big and important in a story.",
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("big", tid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("curiosity", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, M) :- setting(S), transformation(T), mystery(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, transformation=None, mystery=None, name=None, gender=None, pet_name=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"MISMATCH: story generation smoke test failed: {exc}")
    return 0 if ok else 1


CURATED = [
    StoryParams(
        setting="cage_room",
        transformation="big_footprints",
        mystery="vanishing_seed",
        hero_name="Mia",
        hero_type="girl",
        pet_name="Nibbles",
    ),
    StoryParams(
        setting="attic",
        transformation="big_shadow",
        mystery="muffled_noise",
        hero_name="Tom",
        hero_type="boy",
        pet_name="Pip",
    ),
    StoryParams(
        setting="cage_room",
        transformation="big_balloon",
        mystery="muffled_noise",
        hero_name="Lily",
        hero_type="girl",
        pet_name="Gizmo",
    ),
]


def explain_invalid(args: argparse.Namespace) -> str:
    return "(No story: these options do not form a valid mystery transformation.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.transformation is None or c[1] == args.transformation)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError(explain_invalid(args))
    setting, transformation, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    pet_name = args.pet_name or rng.choice(["Nibbles", "Pip", "Mochi", "Gizmo"])
    return StoryParams(
        setting=setting,
        transformation=transformation,
        mystery=mystery,
        hero_name=name,
        hero_type=gender,
        pet_name=pet_name,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, t, m in asp_valid_combos():
            print(f"  {s:10} {t:16} {m}")
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
            header = f"### {p.hero_name}: {p.setting} / {p.transformation} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
