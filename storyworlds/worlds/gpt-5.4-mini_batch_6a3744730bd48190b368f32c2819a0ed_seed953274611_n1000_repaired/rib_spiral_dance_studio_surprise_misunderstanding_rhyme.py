#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rib_spiral_dance_studio_surprise_misunderstanding_rhyme.py
===========================================================================================

A standalone story world for a tiny fairy-tale dance studio domain.

Premise:
A child in a dance studio gets tangled in a spiral ribbon, a misunderstanding
creates tension, a surprise gift changes the mood, and a rhyme helps everyone
repair the moment.

This world is built to produce complete, child-facing stories with:
- a concrete setting: dance studio
- required seed words: rib, spiral
- narrative instruments: Surprise, Misunderstanding, Rhyme
- a fairy-tale tone
- a world model with meters and memes
- a reasonableness gate
- an inline ASP twin for parity checks

Run it:
    python storyworlds/worlds/gpt-5.4-mini/rib_spiral_dance_studio_surprise_misunderstanding_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/rib_spiral_dance_studio_surprise_misunderstanding_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/rib_spiral_dance_studio_surprise_misunderstanding_rhyme.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

STORY_KIND = "dance studio fairy tale"
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"tangled": 0.0, "music": 0.0, "bright": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "surprise": 0.0, "understanding": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy"}
        male = {"boy", "father", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    name: str
    name_gender: str
    helper_name: str
    helper_gender: str
    elder_name: str
    elder_gender: str
    ribbon: str
    swirl: str
    surprise: str
    misunderstanding: str
    rhyme: str
    seed: Optional[int] = None
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
class Config:
    id: str
    label: str
    ribbon_label: str
    swirl_label: str
    surprise_label: str
    misunderstanding_label: str
    rhyme_label: str
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


NAMES_GIRL = ["Mira", "Lena", "Suri", "Elin", "Pippa", "Nora"]
NAMES_BOY = ["Tobin", "Robin", "Milo", "Nico", "Arlo", "Bram"]
ELDER_GIRL = ["Queen Rowan", "Aunt Elia"]
ELDER_BOY = ["King Tavin", "Uncle Maro"]


class World:
    def __init__(self):
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


def _touch_story_state(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    stage = world.get("stage")
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    stage.meters["music"] += 1
    world.say(
        f"In a little dance studio with mirrors like silver ponds, {child.id} and {helper.id} "
        f"whirled between the ribbons and the bright floorboards."
    )
    world.say(
        f"{child.id} loved the studio because every step could become a spell."
    )


def _mystery(world: World) -> None:
    child = world.get("child")
    ribbon = world.get("ribbon")
    stage = world.get("stage")
    child.memes["worry"] += 1
    ribbon.meters["tangled"] += 1
    stage.meters["music"] += 0
    world.say(
        f"Then a long spiral ribbon slipped into a twist, and the rib-shaped prop basket tipped over the bench."
    )
    world.say(
        f"{child.id} stared at the spiral and frowned, because the studio suddenly felt too quiet."
    )


def _misunderstanding(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    elder = world.get("elder")
    child.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{child.id} thought {helper.id} had broken the ribbon on purpose, and {helper.id} thought {child.id} was blaming {helper.pronoun('object')}."
    )
    world.say(
        f"That was the misunderstanding, and for a moment their feet forgot the music."
    )


def _surprise(world: World) -> None:
    elder = world.get("elder")
    child = world.get("child")
    helper = world.get("helper")
    child.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"Just then {elder.id} arrived with a surprise: a golden ribbon pin and a fresh coil that shimmered like moonlight."
    )
    world.say(
        f'"I brought a new ribbon for the dance," {elder.id} said, "and I brought a rhyme to mend the hurt."'
    )


def _rhyme(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    elder = world.get("elder")
    child.memes["understanding"] += 1
    helper.memes["understanding"] += 1
    world.say(
        '"Twist is not a truce, and blame is not a song," '
        f'{elder.id} rhymed softly. "A kind word helps the whole room along."'
    )
    world.say(
        f"{child.id} blinked, then {helper.id} blinked, and both understood that the spiral ribbon had tangled by chance."
    )


def _resolve(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    ribbon = world.get("ribbon")
    stage = world.get("stage")
    ribbon.meters["tangled"] = 0.0
    stage.meters["bright"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Together they unknotted the spiral ribbon, and the studio brightened as if a candle had been lit behind the mirrors."
    )
    world.say(
        f"Then {child.id} and {helper.id} laughed, bowed, and danced a careful little circle to show the day was mended."
    )
    world.say(
        f"From that day on, the rib-shaped prop basket stayed neat, the spiral ribbon stayed safe, and the fairy-tale studio rang with kinder steps."
    )


def reasonableness_ok(params: StoryParams) -> bool:
    return all([
        params.ribbon == "spiral ribbon",
        params.swirl == "spiral",
        params.surprise in SURPRISES,
        params.misunderstanding in MISUNDERSTANDINGS,
        params.rhyme in RHYMES,
    ])


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for surprise in SURPRISES:
            for misunderstanding in MISUNDERSTANDINGS:
                if s == "dance studio":
                    out.append((s, surprise, misunderstanding))
    return out


SETTINGS = ["dance studio"]
SURPRISES = {
    "golden ribbon pin": "a golden ribbon pin",
    "fresh ribbon coil": "a fresh ribbon coil",
    "music box": "a tiny music box",
}
MISUNDERSTANDINGS = {
    "blame": "a blame misunderstanding",
    "broken": "a broken-ribbon misunderstanding",
}
RHYMES = {
    "twist": "Twist is not a truce, and blame is not a song",
    "step": "A kind step mends the mess and keeps the music long",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Dance studio fairy tale world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--misunderstanding", choices=sorted(MISUNDERSTANDINGS))
    ap.add_argument("--rhyme", choices=sorted(RHYMES))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
    setting = args.setting or "dance studio"
    surprise = args.surprise or rng.choice(list(SURPRISES))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    rhyme = args.rhyme or rng.choice(list(RHYMES))
    name_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    elder_gender = rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if name_gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice([n for n in (NAMES_GIRL + NAMES_BOY) if n != name])
    elder = args.elder or rng.choice(ELDER_GIRL if elder_gender == "girl" else ELDER_BOY)
    params = StoryParams(
        name=name, name_gender=name_gender,
        helper_name=helper, helper_gender=helper_gender,
        elder_name=elder, elder_gender=elder_gender,
        ribbon="spiral ribbon", swirl="spiral",
        surprise=surprise, misunderstanding=misunderstanding, rhyme=rhyme,
    )
    if not reasonableness_ok(params):
        raise StoryError("Invalid fairy-tale dance studio parameters.")
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(id="child", kind="character", type=params.name_gender, label=params.name, role="child"))
    world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name, role="helper"))
    world.add(Entity(id="elder", kind="character", type=params.elder_gender, label=params.elder_name, role="elder"))
    world.add(Entity(id="stage", type="place", label="the dance studio"))
    world.add(Entity(id="ribbon", type="thing", label="spiral ribbon"))
    world.add(Entity(id="rib", type="thing", label="rib-shaped prop basket"))
    return world


def tell(world: World, params: StoryParams) -> None:
    _touch_story_state(world)
    world.para()
    _mystery(world)
    _misunderstanding(world)
    world.para()
    _surprise(world)
    _rhyme(world)
    world.para()
    _resolve(world)
    world.facts = {
        "setting": "dance studio",
        "surprise": params.surprise,
        "misunderstanding": params.misunderstanding,
        "rhyme": params.rhyme,
        "name": params.name,
        "helper": params.helper_name,
        "elder": params.elder_name,
    }


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a fairy-tale story set in a dance studio that includes the words rib and spiral.",
        f"Tell a story about {f['name']} in a dance studio where a misunderstanding is fixed by a surprise and a rhyme.",
        "Write a child-friendly fairy tale where a spiral ribbon causes trouble, but kind words make the ending bright.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Where does the story happen?",
         "It happens in a dance studio with mirrors, ribbons, and bright floorboards."),
        ("What caused the trouble?",
         "A spiral ribbon got tangled, and that led to a misunderstanding between the children."),
        ("How was the misunderstanding fixed?",
         "A kind elder arrived with a surprise and spoke a rhyme that helped everyone understand."),
        ("What changed at the end?",
         "The ribbon was untangled, the studio felt bright again, and the children danced happily together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a spiral?",
         "A spiral is a shape that winds around and around, like a curl or a twist."),
        ("What is a surprise?",
         "A surprise is something that happens unexpectedly and can make people gasp or smile."),
        ("What is a misunderstanding?",
         "A misunderstanding is when people think the wrong thing about each other."),
        ("What is a rhyme?",
         "A rhyme is a line with words that sound musical together at the end."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(setting, surprise, misunderstanding) :- setting("dance studio"), surprise(S), misunderstanding(M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "dance studio")]
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        if set(asp_valid_combos()) != set(valid_combos()):
            rc = 1
            print("MISMATCH: ASP and Python valid_combos differ.")
        else:
            print("OK: ASP and Python gates match.")
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            rc = 1
            print("MISMATCH: generated story was empty.")
        else:
            print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if not reasonableness_ok(params):
        raise StoryError("Invalid story parameters.")
    world = build_world(params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(
        name="Mira", name_gender="girl",
        helper_name="Robin", helper_gender="boy",
        elder_name="Queen Rowan", elder_gender="girl",
        ribbon="spiral ribbon", swirl="spiral",
        surprise="golden ribbon pin", misunderstanding="blame", rhyme="twist",
    ),
    StoryParams(
        name="Tobin", name_gender="boy",
        helper_name="Lena", helper_gender="girl",
        elder_name="King Tavin", elder_gender="boy",
        ribbon="spiral ribbon", swirl="spiral",
        surprise="fresh ribbon coil", misunderstanding="broken", rhyme="step",
    ),
]


def resolve_many(args: argparse.Namespace, rng: random.Random, n: int) -> list[StorySample]:
    out: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(out) < n and i < max(50, n * 50):
        i += 1
        params = resolve_params(args, random.Random((args.seed or 0) + i))
        params.seed = (args.seed or 0) + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        out.append(sample)
    return out


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
            print(row)
        return

    samples: list[StorySample]
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        try:
            if args.n == 1:
                params = resolve_params(args, random.Random(base_seed))
                params.seed = base_seed
                samples = [generate(params)]
            else:
                samples = resolve_many(args, random.Random(base_seed), args.n)
        except StoryError as err:
            print(err)
            return

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
            header = f"### {p.name} in the dance studio"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
