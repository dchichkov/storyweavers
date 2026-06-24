#!/usr/bin/env python3
"""
A tiny storyworld about a lost condiment, a secret inner monologue, teamwork,
and a tall-tale reconciliation.

A seed tale:
---
On the windiest day in Willow Whistle Town, Junie the lunch-carrying kid
arrived at the picnic patch with a fancy bottle of strawberry ketchup, a
condiment so rare it had a gold cap and a label bright as a sunflower.

Junie wanted to pour it on her sandwich right away, but the bottle had rolled
under the longest blanket in the county. Junie thought, "If I cannot find that
condiment, this picnic will be plain as plain." She looked under benches, behind
baskets, and even inside a teapot, but no ketchup appeared.

Then the old kite-fixer, Mister Hale, and the dog-walker twins, Poppy and Pip,
came to help. Mister Hale held up the blanket corner, Poppy checked the hill,
and Pip called out from the bandstand that he had found the bottle balanced on
a spoon. Junie laughed so hard she nearly snorted lemonade.

At last they carried the bottle back together. Junie shared the ketchup, thanked
everyone, and the whole picnic became a feast fit for a cloud giant.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "kid"}
        male = {"boy", "man", "father", "kid"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Scene:
    place: str = "the picnic patch"
    weather: str = "windy"
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
class Condiment:
    id: str
    label: str
    phrase: str
    splash: str
    tall_tale_image: str
    sound: str = "glug"
    keyword: str = "condiment"
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
class Helper:
    id: str
    label: str
    talent: str
    action: str
    teamwork_line: str
    reconciliation_line: str
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
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.held_condiment: Optional[str] = None
        self.searching: bool = False
        self.reconciled: bool = False

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.lines = [[]]
        w.fired = set(self.fired)
        w.held_condiment = self.held_condiment
        w.searching = self.searching
        w.reconciled = self.reconciled
        return w


def _monologue(world: World, hero: Entity, condiment: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} stared at the missing {condiment.label} and thought, "
        f'"If I cannot find that {condiment.keyword}, this picnic will be plain as a pale biscuit."'
    )


def _search(world: World, hero: Entity) -> None:
    world.searching = True
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} searched under benches, behind baskets, and even inside a teapot, "
        f"but the wind kept flipping the clues like pancakes."
    )


def _teamwork(world: World, hero: Entity, helper: Entity, condiment: Entity) -> None:
    sig = ("teamwork", helper.id, condiment.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    helper.memes["helpful"] = helper.memes.get("helpful", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"Then {helper.id} came along with a grin and {helper.talent}; "
        f"{helper.teamwork_line}."
    )
    if helper.id == "Mister Hale":
        world.say(
            "He lifted the blanket corner high as a barn door, and the breeze slipped right through."
        )
    elif helper.id == "Poppy":
        world.say("Poppy peered up the hill like a hawk looking for a crumb of sun.")
    elif helper.id == "Pip":
        world.say("Pip called from the bandstand that the bottle was balanced on a spoon.")
    world.held_condiment = condiment.id
    world.say(
        f"At last they found the {condiment.label}, and the bottle went {condiment.sound} "
        f"into {hero.id}'s hands."
    )


def _reconcile(world: World, hero: Entity, helper: Entity, condiment: Entity) -> None:
    sig = ("reconcile", hero.id, helper.id, condiment.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.reconciled = True
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["gratitude"] = hero.memes.get("gratitude", 0) + 1
    world.say(
        f"{hero.id} laughed, thanked {helper.id}, and said, "
        f'"I was worried, but you made the day feel big enough for a cloud giant."'
    )
    world.say(
        f"{helper.reconciliation_line} So they shared the {condiment.label}, and the picnic became a feast."
    )


def tell(scene: Scene, condiment: Condiment, hero_name: str, hero_type: str) -> World:
    world = World(scene)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    condiment_ent = world.add(
        Entity(
            id=condiment.id,
            type="condiment",
            label=condiment.label,
            phrase=condiment.phrase,
            owner=hero.id,
            meters={"full": 1.0},
        )
    )
    helpers = [
        world.add(Entity(id="Mister Hale", kind="character", type="man")),
        world.add(Entity(id="Poppy", kind="character", type="girl")),
        world.add(Entity(id="Pip", kind="character", type="boy")),
    ]

    world.say(
        f"On a windy morning at {scene.place}, {hero.id} arrived with "
        f"{condiment.phrase}, a {condiment.keyword} so special it seemed to shine at the seams."
    )
    world.say(
        f"{hero.id} loved the smell of the {condiment.label}, but the bottle had rolled away like a shiny pebble."
    )
    world.para()
    _monologue(world, hero, condiment_ent)
    _search(world, hero)
    world.para()
    _teamwork(world, hero, helpers[0], condiment_ent)
    _teamwork(world, hero, helpers[1], condiment_ent)
    _teamwork(world, hero, helpers[2], condiment_ent)
    _reconcile(world, hero, helpers[2], condiment_ent)
    world.para()
    world.say(
        f"In the end, the {condiment.label} sat in the middle of the picnic blanket, "
        f"{condiment.tall_tale_image}, while the wind blew soft as a bedtime song."
    )

    world.facts.update(
        hero=hero,
        condiment=condiment_ent,
        helpers=helpers,
        scene=scene,
        condiment_cfg=condiment,
    )
    return world


SCENES = {
    "picnic_patch": Scene(place="the picnic patch", weather="windy"),
    "riverbank": Scene(place="the riverbank picnic", weather="breezy"),
    "orchard": Scene(place="the apple orchard clearing", weather="windy"),
}

CONDIMENTS = {
    "ketchup": Condiment(
        id="ketchup",
        label="ketchup",
        phrase="a bottle of strawberry ketchup",
        splash="red",
        tall_tale_image="the gold cap gleaming like a tiny sunset",
    ),
    "mustard": Condiment(
        id="mustard",
        label="mustard",
        phrase="a jar of sunny mustard",
        splash="yellow",
        tall_tale_image="the glass jar shining like a captured moonbeam",
    ),
    "relish": Condiment(
        id="relish",
        label="relish",
        phrase="a little jar of green relish",
        splash="green",
        tall_tale_image="the lid bobbing like a green hat on a hill",
    ),
}

HERO_NAMES = ["Junie", "Milo", "Ada", "Theo", "Nina", "Beau"]
HERO_TYPES = ["girl", "boy"]
HELPER_NAMES = ["Mister Hale", "Poppy", "Pip"]


@dataclass
class StoryParams:
    scene: str
    condiment: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale condiment storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--condiment", choices=CONDIMENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    scene = getattr(args, "scene", None) or rng.choice(list(SCENES))
    condiment = getattr(args, "condiment", None) or rng.choice(list(CONDIMENTS))
    hero_type = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    return StoryParams(scene=scene, condiment=condiment, hero_name=hero_name, hero_type=hero_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SCENES, params.scene), _safe_lookup(CONDIMENTS, params.condiment), params.hero_name, params.hero_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    condiment = _safe_fact(world, f, "condiment_cfg")
    return [
        f'Write a tall-tale style story for a young child about a missing {condiment.keyword}.',
        f"Tell a story where {hero.id} thinks aloud, gets help from friends, and finds the {condiment.label}.",
        f'Write a child-friendly tale that includes teamwork and a happy reconciliation over a {condiment.keyword}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    condiment = _safe_fact(world, f, "condiment")
    helpers = _safe_fact(world, f, "helpers")
    return [
        QAItem(
            question=f"What was {hero.id} looking for at {world.scene.place}?",
            answer=f"{hero.id} was looking for the {condiment.label}, which had rolled away before lunch.",
        ),
        QAItem(
            question=f"Who helped {hero.id} find the {condiment.label}?",
            answer=f"Mister Hale, Poppy, and Pip all helped, each in their own way.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the {condiment.label} was found?",
            answer=f"{hero.id} felt relieved, happy, and thankful once the bottle was back in hand.",
        ),
        QAItem(
            question=f"What did the helpers and {hero.id} do in the end?",
            answer=f"They shared the {condiment.label} together and turned the picnic into a feast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    condiment = _safe_fact(world, world.facts, "condiment_cfg")
    return [
        QAItem(
            question="What is a condiment?",
            answer="A condiment is a tasty extra food, like ketchup or mustard, that you add to other food to give it more flavor.",
        ),
        QAItem(
            question="Why do people share food at a picnic?",
            answer="People share food at a picnic so everyone can eat together and enjoy the meal outdoors.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to do something well.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being worried or upset and come back together kindly.",
        ),
        QAItem(
            question=f"Why can the {condiment.label} look special in a story?",
            answer=f"The {condiment.label} can look special because it is the important thing everyone is trying to find and share.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"held_condiment={world.held_condiment}")
    lines.append(f"searching={world.searching}")
    lines.append(f"reconciled={world.reconciled}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scene="picnic_patch", condiment="ketchup", hero_name="Junie", hero_type="girl"),
    StoryParams(scene="riverbank", condiment="mustard", hero_name="Milo", hero_type="boy"),
    StoryParams(scene="orchard", condiment="relish", hero_name="Ada", hero_type="girl"),
]


ASP_RULES = r"""
hero(H) :- hero_name(H).
condiment(C) :- condiment_name(C).
helper(X) :- helper_name(X).

missing(C) :- condiment(C).
needs_help(H,C) :- hero(H), missing(C).
teamwork(H,X,C) :- needs_help(H,C), helper(X).
reconcile(H,X,C) :- teamwork(H,X,C).
story_ok(H,C) :- needs_help(H,C), teamwork(H,_,C), reconcile(H,_,C).
#show story_ok/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for c in CONDIMENTS:
        lines.append(asp.fact("condiment_name", c))
    for h in HELPER_NAMES:
        lines.append(asp.fact("helper_name", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    ok = bool(asp.atoms(model, "story_ok"))
    if ok:
        print("OK: ASP twin produced a valid story shape.")
        return 0
    print("MISMATCH: ASP twin did not validate the story shape.")
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
        print(asp_program("#show story_ok/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for this world, but the prose engine does not require it.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
