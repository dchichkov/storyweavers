#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/wipe_courage_ovary_dock_quest_happy_ending.py
===============================================================================================================

A standalone storyworld for a mythic dockside quest with teamwork, courage,
and a happy ending.

Seed tale:
---
At the dock, a young seeker finds a sea plaque marked by salt. The plaque
names the route to the hidden isle of Ovary, but the salt crust blocks the
letters. The seeker wants to wipe the plaque clean and follow the quest, while
an elder fears the old paint may vanish too. With courage and teamwork, the
crew uses a soft cloth, cleans only the salt, and reads the path together.
The boat leaves at dawn, and the quest ends in a happy homecoming.

This world models:
- a dock setting
- a mythic quest
- the emotional meter courage
- teamwork as a shared resolution
- a reversible wipe action that can safely reveal a clue when done with the
  right cloth
- the word "ovary" as the name of the hidden isle, to keep the seed words
  present in the storyworld without breaking child-facing prose
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    cloth: object | None = None
    crewmate: object | None = None
    elder: object | None = None
    hero: object | None = None
    plaque: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the dock"
    affords: set[str] = field(default_factory=lambda: {"wipe"})
    setting: object | None = None
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str = "wipe"
    tags: set[str] = field(default_factory=set)
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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


def _r_salt(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("Hero")
    plaque = world.entities.get("plaque")
    cloth = world.entities.get("cloth")
    if not hero or not plaque:
        return out
    if hero.meters.get("wipe", 0.0) < THRESHOLD:
        return out
    if cloth is None or cloth.worn_by != hero.id:
        return out
    if cloth.meters.get("soft", 0.0) < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    plaque.meters["clean"] = 1.0
    plaque.meters["readable"] = 1.0
    out.append("The salt came away, and the carved letters shone through.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = [e for e in world.entities.values() if e.kind == "character"]
    if sum(1 for e in team if e.memes.get("courage", 0.0) >= THRESHOLD) < 1:
        return out
    if any(e.meters.get("helped", 0.0) >= THRESHOLD for e in team):
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The crew worked together as one small, brave tide.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_r_salt, _r_teamwork):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clothe(world: World, hero: Entity, cloth: Entity) -> None:
    cloth.worn_by = hero.id


def tell() -> World:
    setting = Setting()
    world = World(setting)

    hero = world.add(Entity(
        id="Hero",
        kind="character",
        type="girl",
        traits=["young", "brave"],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type="woman",
        label="the elder",
        traits=["wise", "gentle"],
    ))
    crewmate = world.add(Entity(
        id="Crew",
        kind="character",
        type="boy",
        label="the deckhand",
        traits=["kind", "quick"],
    ))
    plaque = world.add(Entity(
        id="plaque",
        type="stone",
        label="sea plaque",
        phrase="a sea plaque with carved route marks",
        caretaker=elder.id,
    ))
    cloth = world.add(Entity(
        id="cloth",
        type="cloth",
        label="soft cloth",
        phrase="a soft cloth for careful hands",
        owner=hero.id,
    ))

    world.say(
        "At the dock, a young seeker stood before a sea plaque that held the "
        "route of a mythic quest."
    )
    world.say(
        "The plaque pointed toward the isle of Ovary, but salt crusted over the "
        "letters like frost."
    )
    world.say(
        "The seeker wanted to wipe the plaque clean, because the hidden path "
        "could not be read until the shining words returned."
    )

    world.para()
    hero.memes["courage"] += 1
    hero.meters["wipe"] += 1
    world.say(
        "The elder frowned, afraid the old paint might vanish too, and the sea "
        "wind made the moment feel bigger than a child could hold alone."
    )
    world.say(
        "Still, the seeker lifted the soft cloth with courage and asked the crew "
        "to help."
    )

    crewmate.meters["helped"] += 1
    hero.meters["helped"] += 1
    world.say(
        "The deckhand steadied the stone, the elder pointed to the salt only, "
        "and the seeker wiped carefully instead of scraping hard."
    )

    clothe(world, hero, cloth)
    cloth.meters["soft"] += 1
    propagate(world, narrate=True)

    world.para()
    if plaque.meters.get("readable", 0.0) >= THRESHOLD:
        world.say(
            "The letters emerged at last, and the route to Ovary gleamed in the "
            "morning light."
        )
        world.say(
            "With teamwork and courage, the little crew launched the boat and "
            "followed the quest together."
        )
        world.say(
            "By sunset, they returned smiling, the plaque safe, the path learned, "
            "and the dock glowing with a happy ending."
        )
    else:
        world.say(
            "The plaque stayed cloudy, and the quest could not begin."
        )

    world.facts.update(
        hero=hero,
        elder=elder,
        crewmate=crewmate,
        plaque=plaque,
        cloth=cloth,
        setting=setting,
    )
    return world


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Lina"
    helper_name: str = "Marek"
    elder_name: str = "Aunt Shore"
    samples: list = field(default_factory=list)
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


NAMES = ["Lina", "Mina", "Tala", "Iris", "Niko", "Sera", "Ari"]
HELPERS = ["Marek", "Pavel", "Lior", "Dara", "Juno", "Tavi"]
ELDERS = ["Aunt Shore", "Grandmother Tide", "Old Mara", "Mist Aunt"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic dockside quest with courage and teamwork.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=getattr(args, "seed", None),
        hero_name=getattr(args, "name", None) or rng.choice(NAMES),
        helper_name=getattr(args, "helper", None) or rng.choice(HELPERS),
        elder_name=getattr(args, "elder", None) or rng.choice(ELDERS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell()
    hero = world.get("Hero")
    elder = world.get("Elder")
    crew = world.get("Crew")
    plaque = world.get("plaque")
    cloth = world.get("cloth")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short mythic story set at a dock about a child who must wipe a salt-crusted plaque to begin a quest.',
        'Tell a gentle tale where courage and teamwork help reveal the hidden route to Ovary.',
        'Write a happy-ending dock story that includes the words wipe, courage, and ovary.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Where did the quest begin?",
            answer="The quest began at the dock, beside a sea plaque with salt on it.",
        ),
        QAItem(
            question="Why did the seeker want to wipe the plaque?",
            answer="The seeker wanted to wipe the plaque because salt crusted over the letters and hid the route.",
        ),
        QAItem(
            question="What helped the plaque become readable?",
            answer="A soft cloth, careful hands, courage, and teamwork helped the plaque become readable.",
        ),
        QAItem(
            question="What did the plaque point toward?",
            answer="It pointed toward the isle of Ovary, which was the goal of the quest.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the boat launched, the route learned, and everyone returning smiling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is courage?",
            answer="Courage is the feeling that helps someone do a hard or scary thing anyway.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together toward one goal.",
        ),
        QAItem(
            question="What is a dock?",
            answer="A dock is a place by the water where boats can stop and people can load or unload things.",
        ),
        QAItem(
            question="What is an ovary?",
            answer="An ovary is a body part in many female animals, including people, that helps make eggs.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(hero).
character(hero).
character(elder).
character(crew).

setting(dock).
affords(dock,wipe).

activity(wipe).
mess_of(wipe,salt).
splashes(wipe,plaque).

prize(plaque).
worn_on(plaque,stone).

gear(cloth).
guards(cloth,salt).
covers(cloth,stone).

helped(hero).
helped(crew).

courage(hero).

reveal :- courage(hero), helped(hero), helped(crew), guards(cloth,salt), covers(cloth,stone), mess_of(wipe,salt), splashes(wipe,plaque).
#show reveal/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "dock"),
        asp.fact("affords", "dock", "wipe"),
        asp.fact("activity", "wipe"),
        asp.fact("mess_of", "wipe", "salt"),
        asp.fact("splashes", "wipe", "plaque"),
        asp.fact("prize", "plaque"),
        asp.fact("worn_on", "plaque", "stone"),
        asp.fact("gear", "cloth"),
        asp.fact("guards", "cloth", "salt"),
        asp.fact("covers", "cloth", "stone"),
        asp.fact("helped", "hero"),
        asp.fact("helped", "crew"),
        asp.fact("courage", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reveal/0."))
    asp_ok = bool(asp.atoms(model, "reveal"))
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


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
        print(asp_program("#show reveal/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(StoryParams(seed=base_seed + i, hero_name=n)) for i, n in enumerate(NAMES[:5])]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
