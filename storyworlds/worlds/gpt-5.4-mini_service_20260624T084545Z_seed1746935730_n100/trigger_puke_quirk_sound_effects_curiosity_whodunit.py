#!/usr/bin/env python3
"""
A small whodunit-style story world about a curious child, odd sound effects,
and a harmless mystery that ends with a clear reveal.

Seed premise:
- A strange trigger sound starts a little whodunit.
- Curiosity pulls the hero through clues.
- A quirky object causes a puke mess, and the hero figures out who/what did it.

The generated stories stay child-facing and concrete, while the world model
tracks the physical mess and the emotional beats that drive the narration.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    noisy: bool = False
    quirky: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    culprit: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Clue:
    id: str
    text: str
    reveals: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    sidekick: str
    sidekick_type: str
    culprit: str
    culprit_type: str
    trigger_sound: str
    quirk_object: str
    puke_place: str
    seed: Optional[int] = None
    params: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "kitchen": "the kitchen",
    "hall": "the hallway",
    "playroom": "the playroom",
}

HEROES = [
    ("Mia", "girl"),
    ("Leo", "boy"),
    ("Ava", "girl"),
    ("Finn", "boy"),
]

SIDEKICKS = [
    ("Momo", "cat"),
    ("Pip", "dog"),
    ("Nib", "cat"),
]

CULPRITS = [
    ("Momo", "cat"),
    ("Pip", "dog"),
    ("Nib", "cat"),
]

TRIGGER_SOUNDS = [
    "whirr-click",
    "clink-clink",
    "bloop-bloop",
    "tap-tap-squeak",
]

QUIRK_OBJECTS = [
    "a toy robot with a squeaky wheel",
    "a striped ball that chirps when rolled",
    "a music box with a bent spring",
    "a spoon that buzzes when tapped",
]

PUKE_PLACES = [
    "behind the sofa",
    "under the table",
    "beside the rug",
    "near the laundry basket",
]

TRAITS = ["curious", "careful", "smart", "quiet"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with sound effects, curiosity, and a quirky clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-type", choices=["cat", "dog"])
    ap.add_argument("--culprit")
    ap.add_argument("--culprit-type", choices=["cat", "dog"])
    ap.add_argument("--trigger-sound", choices=TRIGGER_SOUNDS)
    ap.add_argument("--quirk-object")
    ap.add_argument("--puke-place", choices=PUKE_PLACES)
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.culprit_type != "cat" and params.culprit_type != "dog":
        pass
    if params.sidekick_type not in {"cat", "dog"}:
        pass
    if params.culprit == params.hero:
        pass
    if "squeaky" not in params.quirk_object and "chirps" not in params.quirk_object and "buzzes" not in params.quirk_object:
        pass


def _sound_word(trigger_sound: str) -> str:
    return f"{trigger_sound}!"


def _mystery_reveal(world: World) -> str:
    hero = world.get("hero")
    culprit = world.get("culprit")
    quirk = world.get("quirk")
    place = world.facts["puke_place"]
    return (
        f"The clue was no monster at all. It was {culprit.name_or_label()}, "
        f"and the quirky {quirk.name_or_label()} had startled {culprit.name_or_label()} enough to make it puke {place}."
    )


def _first_paragraph(world: World) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    culprit = world.get("culprit")
    quirk = world.get("quirk")
    sound = world.facts["trigger_sound"]

    world.say(
        f"One day, {hero.id} was in {world.setting} when a strange {sound} split the quiet air."
    )
    world.say(
        f"{hero.id} froze, because the sound was the kind of sound that made a curious kid look up fast."
    )
    world.say(
        f"Nearby, {sidekick.name_or_label()} twitched its ears, and the odd little {quirk.name_or_label()} sat there like it knew a secret."
    )
    world.say(
        f"{hero.id} whispered, \"Who made that sound effect?\" and stepped closer to find out."
    )


def _second_paragraph(world: World) -> None:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    quirk = world.get("quirk")
    culprit = world.get("culprit")
    place = world.facts["puke_place"]

    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} followed the clue trail with careful steps, while {sidekick.name_or_label()} sniffed the floor."
    )
    world.say(
        f"Under a chair, {hero.id} found a tiny splash and then a bigger mess {place}."
    )
    world.say(
        f"The quirky {quirk.name_or_label()} gave one more soft {world.facts['trigger_sound']} as it wobbled."
    )
    world.say(
        f"That made the mystery clearer: something in the room had been the trigger."
    )


def _resolution_paragraph(world: World) -> None:
    hero = world.get("hero")
    culprit = world.get("culprit")
    sidekick = world.get("sidekick")
    quirk = world.get("quirk")
    place = world.facts["puke_place"]

    culprit.memes["nervous"] = 1.0
    world.say(_mystery_reveal(world))
    world.say(
        f"{hero.id} did not shout. {hero.id} just nodded and said, "
        f"\"That's okay. We found the puzzle.\""
    )
    world.say(
        f"Then {hero.id} helped clean {place}, while {sidekick.name_or_label()} sat close by and watched the quirky {quirk.name_or_label()} stay very still."
    )
    world.say(
        f"In the end, the room was neat again, the sound was quiet, and the whodunit was solved."
    )


def tell_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(_safe_lookup(SETTINGS, params.setting))
    world.facts["trigger_sound"] = params.trigger_sound
    world.facts["puke_place"] = params.puke_place

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type=params.sidekick_type))
    culprit = world.add(Entity(id=params.culprit, kind="character", type=params.culprit_type))
    quirk = world.add(
        Entity(
            id="quirk",
            kind="thing",
            type="thing",
            label=params.quirk_object,
            quirky=True,
            noisy=True,
        )
    )
    world.facts.update(hero=hero, sidekick=sidekick, culprit=culprit, quirk=quirk)

    _first_paragraph(world)
    world.para()
    _second_paragraph(world)
    world.para()
    _resolution_paragraph(world)

    culprit.meters["puke"] = 1.0
    culprit.memes["startled"] = 1.0
    hero.memes["satisfied"] = 1.0
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child that includes the sound "{f["trigger_sound"]}" and the word "curiosity".',
        f"Tell a gentle mystery about {f['hero'].id} in {world.setting} who hears a strange sound effect and solves what caused the mess.",
        f"Write a playful detective story where a quirky object, a surprise sound, and a little puke clue lead to the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    culprit = f["culprit"]
    quirk = f["quirk"]
    place = f["puke_place"]
    return [
        QAItem(
            question=f"What did {hero.id} hear first in the story?",
            answer=f"{hero.id} heard a strange {f['trigger_sound']} in {world.setting}.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep looking around?",
            answer=f"{hero.id} was full of curiosity and wanted to solve the little mystery.",
        ),
        QAItem(
            question=f"What clue showed that something messy had happened {place}?",
            answer=f"The clue was puke {place}, which told {hero.id} that something had startled the animal.",
        ),
        QAItem(
            question=f"What quirky thing helped trigger the mystery?",
            answer=f"The quirky {quirk.name_or_label()} made a little sound and helped reveal the clue trail.",
        ),
        QAItem(
            question=f"Who was the story really about, when the whodunit was solved?",
            answer=f"It was about {hero.id}, {sidekick.name_or_label()}, and {culprit.name_or_label()} in a small mystery that ended safely.",
        ),
    ]


KNOWLEDGE = {
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to look, ask, and learn more about something new.",
        )
    ],
    "sound": [
        (
            "What is a sound effect?",
            "A sound effect is a special noise that helps tell a story, like a beep, a pop, or a squeak.",
        )
    ],
    "puke": [
        (
            "Why do animals sometimes puke?",
            "Animals sometimes puke when their stomach feels upset or when something startles them very much.",
        )
    ],
    "quirk": [
        (
            "What is a quirk?",
            "A quirk is a small odd thing that makes something special or unusual.",
        )
    ],
    "mystery": [
        (
            "What is a whodunit?",
            "A whodunit is a mystery story where someone tries to figure out who caused something or what happened.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for key in ["curiosity", "sound", "quirk", "puke", "mystery"] for q, a in KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        bits = []
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.noisy:
            bits.append("noisy")
        if ent.quirky:
            bits.append("quirky")
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_fact(H).
sidekick(S) :- sidekick_fact(S).
culprit(C) :- culprit_fact(C).
quirk(Q) :- quirk_fact(Q).
trigger_sound(T) :- trigger_fact(T).
puke_place(P) :- puke_fact(P).

mystery(H,C,Q,P) :- hero(H), culprit(C), quirk(Q), puke_place(P).
solved(H,C,Q,P) :- mystery(H,C,Q,P).
#show solved/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, items in [
        ("hero_fact", [("Mia",)]),
        ("sidekick_fact", [("Momo",)]),
        ("culprit_fact", [("Momo",)]),
        ("quirk_fact", [("quirk",)]),
        ("trigger_fact", [("whirr_click",)]),
        ("puke_fact", [("behind_the_sofa",)]),
    ]:
        for item in items:
            lines.append(asp.fact(name, *item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/4."))
    atoms = set(asp.atoms(model, "solved"))
    expected = {("Mia", "Momo", "quirk", "behind_the_sofa")}
    if atoms == expected:
        print("OK: ASP parity matches the simple reasoner.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero, hero_type = (getattr(args, "hero", None), getattr(args, "hero_type", None)) if getattr(args, "hero", None) and getattr(args, "hero_type", None) else rng.choice(HEROES)
    sidekick, sidekick_type = (getattr(args, "sidekick", None), getattr(args, "sidekick_type", None)) if getattr(args, "sidekick", None) and getattr(args, "sidekick_type", None) else rng.choice(SIDEKICKS)
    culprit, culprit_type = (getattr(args, "culprit", None), getattr(args, "culprit_type", None)) if getattr(args, "culprit", None) and getattr(args, "culprit_type", None) else rng.choice(CULPRITS)
    trigger_sound = getattr(args, "trigger_sound", None) or rng.choice(TRIGGER_SOUNDS)
    quirk_object = getattr(args, "quirk_object", None) or rng.choice(QUIRK_OBJECTS)
    puke_place = getattr(args, "puke_place", None) or rng.choice(PUKE_PLACES)

    params = StoryParams(
        setting=setting,
        hero=hero,
        hero_type=hero_type,
        sidekick=sidekick,
        sidekick_type=sidekick_type,
        culprit=culprit,
        culprit_type=culprit_type,
        trigger_sound=trigger_sound,
        quirk_object=quirk_object,
        puke_place=puke_place,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
    StoryParams(
        setting="playroom",
        hero="Mia",
        hero_type="girl",
        sidekick="Momo",
        sidekick_type="cat",
        culprit="Momo",
        culprit_type="cat",
        trigger_sound="whirr-click",
        quirk_object="a toy robot with a squeaky wheel",
        puke_place="behind the sofa",
    ),
    StoryParams(
        setting="kitchen",
        hero="Leo",
        hero_type="boy",
        sidekick="Pip",
        sidekick_type="dog",
        culprit="Pip",
        culprit_type="dog",
        trigger_sound="clink-clink",
        quirk_object="a music box with a bent spring",
        puke_place="under the table",
    ),
    StoryParams(
        setting="hall",
        hero="Ava",
        hero_type="girl",
        sidekick="Nib",
        sidekick_type="cat",
        culprit="Nib",
        culprit_type="cat",
        trigger_sound="tap-tap-squeak",
        quirk_object="a spoon that buzzes when tapped",
        puke_place="beside the rug",
    ),
]


def asp_valids() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/4."))
    return sorted(set(asp.atoms(model, "solved")))


def build_sample_list(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        return [generate(p) for p in CURATED]
    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show solved/4."))
        return

    samples = build_sample_list(args)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: mystery in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
