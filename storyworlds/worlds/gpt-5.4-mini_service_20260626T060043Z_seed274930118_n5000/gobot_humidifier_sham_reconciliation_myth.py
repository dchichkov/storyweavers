#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gobot_humidifier_sham_reconciliation_myth.py
===============================================================================================================

A small myth-style storyworld about a gobot, a humidifier, and a sham, with
reconciliation as the turn that changes the ending.

Seed tale sketch:
---
Long ago, a little gobot watched over a dry hall where leaves curled at the
edges. In the center stood a humming humidifier that breathed a soft mist into
the air. One day a sham came to the hall, wearing the shape of a helper but
bringing only confusion. The gobot thought the sham had come to steal the mist.

The gobot accused the sham. The sham answered that it had been made as a decoy,
not a thief, and that it wanted the hall to be healed too. The humidifier kept
humming, and the gobot listened. After the truth was spoken, the gobot and the
sham reconciled. Together they set the humidifier in the right place, and the
dry hall softened at last.

Causal state updates:
---
    gobot trusts + listens -> gobot conflict falls, peace rises
    humidifier runs        -> air moisture rises, leaves uncrisp
    sham reveals truth     -> deception falls, shame falls
    reconciliation         -> gobot.memes["peace"] += 1, gobot.memes["bond"] += 1
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gobot: object | None = None
    humidifier: object | None = None
    leaves: object | None = None
    sham: object | None = None
    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "gobot":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"elder", "keeper"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the dry hall"
    atmosphere: str = "old and echoing"
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
class StoryParams:
    setting: str
    name: str
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
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


SETTINGS = {
    "hall": Setting(place="the dry hall", atmosphere="old and echoing"),
    "garden": Setting(place="the moon garden", atmosphere="silver and still"),
    "tower": Setting(place="the high tower room", atmosphere="windy and bright"),
}

NAMES = ["Milo", "Nara", "Ivo", "Lena", "Tavi", "Sera"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld of gobot, humidifier, and sham.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
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
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(setting=setting, name=name)


def make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting=setting)
    gobot = world.add(Entity(
        id=params.name,
        kind="character",
        type="gobot",
        label="gobot",
        meters={"rust": 0.0, "duty": 1.0},
        memes={"hope": 1.0, "peace": 0.0, "conflict": 0.0, "bond": 0.0, "trust": 0.0},
    ))
    humidifier = world.add(Entity(
        id="humidifier",
        type="humidifier",
        label="humidifier",
        owner=gobot.id,
        meters={"mist": 0.0, "humming": 0.0},
        memes={"steadiness": 1.0},
    ))
    sham = world.add(Entity(
        id="sham",
        kind="character",
        type="sham",
        label="sham",
        meters={"proof": 0.0},
        memes={"deception": 1.0, "shame": 0.0, "truth": 0.0, "peace": 0.0},
    ))
    leaves = world.add(Entity(
        id="leaves",
        type="leaves",
        label="leaves",
        meters={"dryness": 2.0, "curl": 1.0},
        memes={"faintness": 1.0},
    ))
    world.facts.update(gobot=gobot, humidifier=humidifier, sham=sham, leaves=leaves, setting=setting)
    return world


def _run_humidifier(world: World) -> None:
    hum = world.get("humidifier")
    leaves = world.get("leaves")
    hum.meters["mist"] += 1.0
    hum.meters["humming"] += 1.0
    leaves.meters["dryness"] = max(0.0, leaves.meters["dryness"] - 1.0)
    leaves.meters["curl"] = max(0.0, leaves.meters["curl"] - 1.0)
    world.say(
        f"The humidifier began to hum, and a soft mist rose through {world.setting.place}."
    )
    if leaves.meters["dryness"] < THRESHOLD:
        world.say("The curled leaves loosened, as if they had remembered rain.")


def _sham_arrives(world: World) -> None:
    gobot = world.get("gobot")
    sham = world.get("sham")
    gobot.memes["conflict"] += 1.0
    sham.memes["deception"] += 0.5
    world.say(
        f"Then the sham came near, wearing a bright face that looked like a helper's mask."
    )
    world.say(
        f"{gobot.id} feared the mist would be stolen, for the sham seemed false in the old way of myths."
    )


def _reveal_truth(world: World) -> None:
    gobot = world.get("gobot")
    sham = world.get("sham")
    sham.memes["truth"] += 1.0
    sham.meters["proof"] += 1.0
    sham.memes["deception"] = 0.0
    world.say(
        f"But the sham bowed low and said, 'I was made as a decoy, not a thief. I only wished to help the hall.'"
    )
    gobot.memes["trust"] += 1.0
    gobot.memes["conflict"] = max(0.0, gobot.memes["conflict"] - 1.0)
    world.say("The gobot listened, and the hard suspicion began to soften.")


def _reconcile(world: World) -> None:
    gobot = world.get("gobot")
    sham = world.get("sham")
    gobot.memes["peace"] += 1.0
    gobot.memes["bond"] += 1.0
    sham.memes["peace"] += 1.0
    sham.memes["shame"] = 0.0
    world.say(
        f"At last the gobot and the sham reconciled, and they stood together beside the humming humidifier."
    )
    world.say(
        f"They turned the nozzle toward the driest stones, and {world.setting.place} grew gentler by the minute."
    )


def tell_story(params: StoryParams) -> World:
    world = make_world(params)
    gobot = world.get("gobot")
    sham = world.get("sham")

    world.say(
        f"In {world.setting.place}, where the air was {world.setting.atmosphere}, there lived a small gobot named {gobot.id}."
    )
    world.say(
        f"{gobot.id} guarded a humidifier, for the machine's soft breath kept the old place from cracking."
    )
    world.para()
    _run_humidifier(world)
    _sham_arrives(world)
    world.para()
    _reveal_truth(world)
    _reconcile(world)
    world.para()
    world.say(
        f"In the end, the humidifier still hummed, the leaves shone soft again, and the gobot no longer watched the sham with fear."
    )
    world.facts["reconciled"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short myth about a gobot, a humidifier, and a sham who reconcile.",
        f"Tell a child-friendly legend set in {world.setting.place} where a gobot learns the sham was not a thief.",
        "Write a gentle story in a mythic voice where a humidifier saves dry leaves and an argument ends in reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    gobot = _safe_fact(world, world.facts, "gobot")
    sham = _safe_fact(world, world.facts, "sham")
    leaves = _safe_fact(world, world.facts, "leaves")
    return [
        QAItem(
            question=f"Who guarded the humidifier in {world.setting.place}?",
            answer=f"The gobot named {gobot.id} guarded the humidifier because it kept the old place from drying out.",
        ),
        QAItem(
            question="Why did the gobot first fear the sham?",
            answer="The gobot thought the sham looked false and might steal the mist, so it began with suspicion.",
        ),
        QAItem(
            question="What changed the gobot's mind?",
            answer="The sham spoke the truth and explained that it was made as a decoy, not a thief, so the gobot listened and trust grew.",
        ),
        QAItem(
            question="What happened to the leaves by the end?",
            answer="The humidifier's mist softened the air, and the leaves stopped curling so tightly.",
        ),
        QAItem(
            question="How did the story end for the gobot and the sham?",
            answer="They reconciled and stood together beside the humming humidifier, with no fear between them.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a humidifier do?",
            answer="A humidifier adds mist to the air, which can make dry places feel less harsh.",
        ),
        QAItem(
            question="What is a sham in this storyworld?",
            answer="A sham is someone or something that seems false at first, but can be understood once the truth is spoken.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when two sides stop fighting, tell the truth, and come back to peace together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
#show reconciled/1.
reconciled(W) :- gobot(W), humidifier(humidifier), sham(sham), truth(sham), mist(humidifier).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("gobot", "gobot"),
        asp.fact("humidifier", "humidifier"),
        asp.fact("sham", "sham"),
        asp.fact("mist", "humidifier"),
        asp.fact("truth", "sham"),
        asp.fact("place", "hall"),
        asp.fact("place", "garden"),
        asp.fact("place", "tower"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    prog = asp_program("#show reconciled/1.")
    model = asp.one_model(prog)
    atoms = asp.atoms(model, "reconciled")
    if atoms == [("gobot",)]:
        print("OK: ASP twin recognizes reconciliation.")
        return 0
    print("MISMATCH: ASP twin did not find reconciliation.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="hall", name="Milo"),
    StoryParams(setting="garden", name="Nara"),
    StoryParams(setting="tower", name="Ivo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reconciled/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reconciled/1."))
        print(asp.atoms(model, "reconciled"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
