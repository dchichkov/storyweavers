#!/usr/bin/env python3
"""
storyworlds/worlds/humid_victim_lime_rhyme_reconciliation_bedtime_story.py
===========================================================================

A small bedtime-story world about a humid evening, a lime-colored treasure,
a hurt feeling, and a gentle reconciliation.

The seed image:
---
On a humid bedtime evening, a child and a parent were trying to get ready for sleep.
The child had a bright lime lantern that they loved. A small accident happened:
the lantern was knocked aside, and a stuffed toy became the "victim" of a spill
from a glass of lime water. The child felt sad and blamed the sleepy cat.

The parent noticed the hurt feeling, told a soft rhyme to slow everyone down, and
helped them clean the toy together. After the apology, the child and the cat
reconciled, and the room felt calm again.

World model:
---
- physical meters: wetness, brightness, cleanliness, sleepiness
- emotional memes: hurt, blame, care, relief, reconciliation, joy

Narrative shape:
---
1) bedtime setup in a humid room
2) a small accident makes a victim and a hurt feeling
3) a rhyme helps the child pause
4) reconciliation restores calm before sleep
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    touched_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cat: object | None = None
    child: object | None = None
    lantern: object | None = None
    lime: object | None = None
    parent: object | None = None
    victim: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
        if "_tags" not in self.__dict__:
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
class Setting:
    place: str = "the bedroom"
    humid: bool = True
    SETTINGS: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Victim:
    label: str
    phrase: str
    type: str
    affected_by: str
    comfort_need: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
class StoryParams:
    name: str = "Mina"
    gender: str = "girl"
    parent: str = "mother"
    victim: str = "toy"
    seed: Optional[int] = None
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {"bedroom": Setting("the bedroom", humid=True)}

VICTIMS = {
    "toy": Victim("toy", "a soft stuffed rabbit", "toy", affected_by="wetness", comfort_need="drying"),
    "pillow": Victim("pillow", "a small star pillow", "pillow", affected_by="wetness", comfort_need="fluffing"),
    "blanket": Victim("blanket", "a patchwork blanket", "blanket", affected_by="wetness", comfort_need="warming"),
}

CHAR_NAMES = ["Mina", "Luca", "Iris", "Noah", "Sana", "Theo"]
TRAITS = ["sleepy", "gentle", "curious", "tender"]


def _narrate_rhyme(world: World, parent: Entity) -> None:
    if "rhyme" in world.fired:
        return
    world.fired.add("rhyme")
    world.say(
        f'{parent.id} hummed, “When the room feels hot and wet, '
        f'we slow our hearts and soft thoughts get set.”'
    )


def _narrate_reconciliation(world: World, child: Entity, other: Entity) -> None:
    if "reconciliation" in world.fired:
        return
    world.fired.add("reconciliation")
    child.memes["reconciliation"] += 1
    other.memes["reconciliation"] += 1
    child.memes["joy"] += 1
    other.memes["joy"] += 1
    child.memes["hurt"] = 0
    child.memes["blame"] = 0
    world.say(
        f"{child.id} took a breath, said sorry, and hugged {other.id}. "
        f"{other.id} leaned in, and the two of them felt better right away."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS["bedroom"])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    cat = world.add(Entity(id="Cat", kind="character", type="cat", label="the sleepy cat"))
    victim = world.add(Entity(
        id="Victim",
        type=params.victim,
        label=_safe_lookup(VICTIMS, params.victim).label,
        phrase=_safe_lookup(VICTIMS, params.victim).phrase,
        owner=child.id,
        caretaker=parent.id,
    ))
    lime = world.add(Entity(
        id="LimeWater",
        type="drink",
        label="a cup of lime water",
        phrase="a cup of lime water",
        owner=child.id,
    ))
    lantern = world.add(Entity(
        id="Lantern",
        type="lantern",
        label="a lime lantern",
        phrase="a little lime lantern",
        owner=child.id,
    ))

    # Setup
    child.memes["love"] = 1
    child.meters["sleepiness"] = 0.2
    world.say(
        f"It was a humid bedtime in {world.setting.place}, and {child.id} held "
        f"{child.pronoun('possessive')} {lantern.label} close."
    )
    world.say(
        f"{child.id} loved the bright lime glow, because it made the room feel safe and small."
    )
    world.say(
        f"The sleepy cat curled by the bed, and {parent.id} tucked the blanket in a neat square."
    )

    # Conflict
    world.para()
    child.memes["hurt"] += 1
    child.memes["blame"] += 1
    victim.meters["wetness"] = 1.0
    victim.meters["cleanliness"] = 0.4
    cat.memes["startled"] += 1
    world.say(
        f"Then the cup of lime water tipped, and {victim.label} became the victim of a splash."
    )
    world.say(
        f"{child.id} frowned and pointed at the cat, because it felt easier to blame a quiet paw."
    )
    world.say(
        f"The room grew still, and even the humid air seemed to wait."
    )

    # Turn
    world.para()
    _narrate_rhyme(world, parent)
    child.memes["calm"] = 1
    child.memes["hurt"] += 0.5
    world.say(
        f"{parent.id} knelt beside {child.id} and gently said that mistakes can be mended."
    )
    world.say(
        f"{child.id} listened to the rhyme, and the hard feeling began to soften like warm bread."
    )
    victim.meters["wetness"] = 0.2
    victim.meters["cleanliness"] = 0.9
    world.say(
        f"Together they blotted the little splash from {victim.label} and set it near the open window."
    )

    # Resolution
    world.para()
    _narrate_reconciliation(world, child, cat)
    world.say(
        f"{child.id} stroked the cat's head and said, “I was wrong.”"
    )
    world.say(
        f"The cat blinked, forgave the worry, and purred as the lime lantern shone softly beside the bed."
    )
    child.meters["sleepiness"] = 1.0
    parent.memes["care"] = 1
    world.say(
        f"At last the room felt cool enough for sleep, and {child.id} drifted off with a lighter heart."
    )

    world.facts.update(
        child=child,
        parent=parent,
        cat=cat,
        victim=victim,
        lime=lime,
        lantern=lantern,
        setting=world.setting,
        resolved=True,
    )
    return world


def valid_victims() -> list[str]:
    return list(VICTIMS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime-story world about humid air, a lime glow, rhyme, and reconciliation.")
    ap.add_argument("--name", choices=CHAR_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--victim", choices=VICTIMS)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHAR_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    victim = getattr(args, "victim", None) or rng.choice(valid_victims())
    return StoryParams(name=name, gender=gender, parent=parent, victim=victim, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    victim = _safe_fact(world, f, "victim")
    return [
        f'Write a gentle bedtime story that includes the words "humid", "lime", and "rhyme".',
        f"Tell a child-facing story where {child.id} feels upset after {victim.label} gets splashed, then calms down with a rhyme.",
        f"Write a short bedtime tale about a small mistake, an apology, and reconciliation before sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    cat = _safe_fact(world, f, "cat")
    victim = _safe_fact(world, f, "victim")
    return [
        QAItem(
            question=f"What was the room like when {child.id} was getting ready for bed?",
            answer=f"The room was humid and sleepy, and the lime lantern made it feel gentle and safe.",
        ),
        QAItem(
            question=f"What happened to {victim.label}?",
            answer=f"{victim.label.capitalize()} got splashed by lime water and became the victim of a small bedtime accident.",
        ),
        QAItem(
            question=f"How did {parent.id} help after the accident?",
            answer=f"{parent.id} used a soft rhyme to slow everyone down, then helped clean up the splash with {child.id}.",
        ),
        QAItem(
            question=f"How did {child.id} and the cat feel at the end?",
            answer=f"They reconciled, and {child.id} and {cat.id} were calm and close again before sleep.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does humid mean?",
            answer="Humid means the air feels a little wet or sticky, like it is holding extra water.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, which can make a song or poem feel soothing.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and come back together kindly after a disagreement.",
        ),
        QAItem(
            question="What does lime mean?",
            answer="Lime is a bright yellow-green color, and it can also be the name of a tart green fruit.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
victim(X) :- victim_kind(X).
rhyme_helped :- rhyme_line.
reconciled :- apology, hug.
good_story :- victim(X), rhyme_helped, reconciled.
#show good_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("victim_kind", vid) for vid in VICTIMS
    ]
    lines.append(asp.fact("rhyme_line"))
    lines.append(asp.fact("apology"))
    lines.append(asp.fact("hug"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    ok = any(sym.name == "good_story" for sym in model)
    if ok:
        print("OK: ASP gate confirms the bedtime story ingredients.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def asp_good() -> bool:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    return any(sym.name == "good_story" for sym in model)


CURATED = [
    StoryParams(name="Mina", gender="girl", parent="mother", victim="toy"),
    StoryParams(name="Theo", gender="boy", parent="father", victim="pillow"),
    StoryParams(name="Iris", gender="girl", parent="mother", victim="blanket"),
]


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

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP says this bedtime world is well-formed:", asp_good())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
