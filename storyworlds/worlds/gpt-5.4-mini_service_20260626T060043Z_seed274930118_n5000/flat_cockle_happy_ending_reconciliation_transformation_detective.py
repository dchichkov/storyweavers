#!/usr/bin/env python3
"""
storyworlds/worlds/flat_cockle_happy_ending_reconciliation_transformation_detective.py
======================================================================================

A small detective-story world about a puzzling flat tire, a cockle shell clue,
and a happy ending built from reconciliation and transformation.

The seed image:
A child detective notices a bicycle tire is flat near the boardwalk. Nearby is a
cockle shell. The clues point to a misunderstanding, not a villain. The detective
follows the trail, learns who was afraid, and helps two friends talk it through.
By the end, the broken plan becomes a new shared one, and the evening ends in
relief.

Story shape:
- Beginning: a small mystery is introduced
- Middle: clues, suspicion, and emotional friction
- Turn: the real cause is understood
- Ending: reconciliation and transformation produce a happy ending
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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    located_at: str = ""
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bike: object | None = None
    cockle: object | None = None
    maxe: object | None = None
    sam: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Scene:
    place: str = "the boardwalk"
    clue_place: str = "the sand"
    fair_weather: bool = True
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
class Case:
    mystery: str
    cause: str
    clue: str
    transformation: str
    resolution: str
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


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _m(obj: Entity, key: str) -> float:
    return obj.meters.get(key, 0.0)


def _e(obj: Entity, key: str) -> float:
    return obj.memes.get(key, 0.0)


def _add_m(obj: Entity, key: str, delta: float) -> None:
    obj.meters[key] = _m(obj, key) + delta


def _add_e(obj: Entity, key: str, delta: float) -> None:
    obj.memes[key] = _e(obj, key) + delta


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sent = rule(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_flat_clue(world: World) -> list[str]:
    out: list[str] = []
    bike = world.get("bike")
    if _m(bike, "flat") >= THRESHOLD and ("flat_clue",) not in world.fired:
        world.fired.add(("flat_clue",))
        out.append("The detective noticed the bicycle tire was flat.")
    return out


def _r_cockle_clue(world: World) -> list[str]:
    out: list[str] = []
    shell = world.get("cockle")
    if shell.located_at == "path" and ("cockle_clue",) not in world.fired:
        world.fired.add(("cockle_clue",))
        out.append("A small cockle shell glittered near the path like a tiny clue.")
    return out


def _r_suspect_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    sam = world.get("Sam")
    maxe = world.get("Max")
    if _e(sam, "worry") >= THRESHOLD and _e(maxe, "guilt") >= THRESHOLD and ("misunderstanding",) not in world.fired:
        world.fired.add(("misunderstanding",))
        out.append("The clues did not point to a bully after all; they pointed to a misunderstanding.")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    sam = world.get("Sam")
    maxe = world.get("Max")
    if _e(sam, "forgiveness") >= THRESHOLD and _e(maxe, "apology") >= THRESHOLD and ("reconcile",) not in world.fired:
        world.fired.add(("reconcile",))
        sam.memes["grudge"] = 0.0
        maxe.memes["fear"] = 0.0
        out.append("Sam and Max talked softly, and the sharp feeling between them melted away.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    bike = world.get("bike")
    if _e(bike, "fixed") >= THRESHOLD and ("transform",) not in world.fired:
        world.fired.add(("transform",))
        out.append("The broken afternoon transformed into a bright ride home.")
    return out


RULES = [_r_flat_clue, _r_cockle_clue, _r_suspect_misunderstanding, _r_reconciliation, _r_transformation]


def introduce(world: World) -> None:
    sam = world.get("Sam")
    world.say(
        f"Sam was a little detective who liked solving small mysteries around {world.scene.place}."
    )
    world.say(
        "He carried a notebook, watched footprints, and believed every puzzle had a real answer."
    )


def set_case(world: World, case: Case) -> None:
    world.facts["case"] = case
    world.say(
        f"One afternoon, a mystery waited by {world.scene.place}: {case.mystery}"
    )
    world.say(
        f"Sam scribbled the first clue in his notebook: {case.clue}"
    )


def discover(world: World) -> None:
    bike = world.get("bike")
    cockle = world.get("cockle")
    maxe = world.get("Max")
    sam = world.get("Sam")

    _add_e(sam, "curiosity", 1)
    _add_m(bike, "flat", 1)
    cockle.located_at = "path"
    propagate(world)

    world.para()
    world.say(
        "Sam looked at the tire, then at the cockle shell, and then at the little tracks in the sand."
    )
    _add_e(maxe, "worry", 1)
    world.say(
        "Max stood nearby with a scared face, because he thought Sam might blame him."
    )


def explain(world: World, case: Case) -> None:
    sam = world.get("Sam")
    maxe = world.get("Max")
    bike = world.get("bike")

    world.para()
    world.say(
        f"Sam followed the marks and realized what had happened: {case.cause}"
    )
    _add_e(maxe, "guilt", 1)
    world.say(
        "Max whispered that he had meant to move the shell, but he had been in a hurry and forgot."
    )
    world.say(
        "Sam listened instead of getting cross, because a good detective wanted the truth more than a villain."
    )
    _add_e(sam, "forgiveness", 1)
    _add_e(maxe, "apology", 1)
    _add_e(bike, "fixed", 1)
    bike.meters["flat"] = 0.0
    world.say(case.transformation)
    propagate(world)


def end_happy(world: World, case: Case) -> None:
    sam = world.get("Sam")
    maxe = world.get("Max")
    bike = world.get("bike")

    world.para()
    world.say(
        f"In the end, {case.resolution}"
    )
    world.say(
        "Sam and Max pushed the bicycle together, laughing again, and the boardwalk felt warm and friendly."
    )
    world.say(
        f"The cockle shell stayed safely in Max's pocket as a keepsake, and the flat tire became a fixed tire."
    )
    world.say(
        "That evening ended with a happy ending: the friends rode home side by side, closer than before."
    )


def tell(scene: Scene, case: Case, name: str = "Sam", friend: str = "Max") -> World:
    world = World(scene)
    sam = world.add(Entity(id=name, kind="character", type="boy", label=name))
    maxe = world.add(Entity(id=friend, kind="character", type="boy", label=friend))
    bike = world.add(Entity(id="bike", type="bike", label="bike", phrase="a little red bicycle"))
    cockle = world.add(Entity(id="cockle", type="shell", label="cockle shell", phrase="a cockle shell"))

    bike.located_at = scene.place
    cockle.located_at = "pocket"
    world.facts.update(hero=sam, friend=maxe, bike=bike, cockle=cockle)

    introduce(world)
    world.para()
    set_case(world, case)
    discover(world)
    explain(world, case)
    end_happy(world, case)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short detective story for children about a flat bicycle tire and a cockle shell clue.",
        "Tell a gentle mystery story where a small detective solves a case through truth, apology, and friendship.",
        "Write a happy-ending story in which a clue near the sand leads to reconciliation and a transformed afternoon.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = _safe_fact(world, world.facts, "case")
    return [
        QAItem(
            question="What mystery did Sam try to solve?",
            answer=f"Sam tried to solve why {case.mystery}.",
        ),
        QAItem(
            question="What clue did Sam notice near the path?",
            answer=f"He noticed {case.clue}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {case.resolution}, after the misunderstanding was cleared up.",
        ),
        QAItem(
            question="What changed in the story?",
            answer="The tired, worried feeling changed into forgiveness, and the broken plan transformed into a happy ride home.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a detective?",
        answer="A detective is a person who looks for clues to solve a mystery.",
    ),
    QAItem(
        question="What is a cockle?",
        answer="A cockle is a small shell from a sea creature, often found on a beach or near water.",
    ),
    QAItem(
        question="What does reconciliation mean?",
        answer="Reconciliation means people stop being upset and become friendly again.",
    ),
    QAItem(
        question="What does transformation mean?",
        answer="Transformation means something changes into a new state or form.",
    ),
    QAItem(
        question="What is a happy ending?",
        answer="A happy ending is when the story finishes in a hopeful and good way.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.located_at:
            bits.append(f"located_at={e.located_at}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "the boardwalk"
    name: str = "Sam"
    friend: str = "Max"
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


SCENE_REGISTRY = {
    "boardwalk": Scene(place="the boardwalk", clue_place="the sand", fair_weather=True),
    "pier": Scene(place="the pier", clue_place="the planks", fair_weather=True),
}

CASE_REGISTRY = {
    "flat-cockle": Case(
        mystery="the bicycle tire was flat",
        cause="a cockle shell had been stuck under the tire until the wheel rolled over it",
        clue="a cockle shell near the path",
        transformation="The mystery turned into a small lesson about looking where you step.",
        resolution="the friends fixed the bike, talked honestly, and rolled away smiling",
    )
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: flat tire, cockle clue, happy ending.")
    ap.add_argument("--place", choices=SCENE_REGISTRY.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    place = getattr(args, "place", None) or rng.choice(list(SCENE_REGISTRY.keys()))
    name = getattr(args, "name", None) or rng.choice(["Sam", "Nina", "Ivy"])
    friend = getattr(args, "friend", None) or rng.choice(["Max", "Leo", "Mina"])
    if name == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(seed=None, place=place, name=name, friend=friend)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "flat-cockle", "boardwalk") for place in SCENE_REGISTRY.keys()]


ASP_RULES = r"""
place(boardwalk).
place(pier).

case(flat_cockle).

flat_mystery(boardwalk) :- place(boardwalk), case(flat_cockle).
flat_mystery(pier) :- place(pier), case(flat_cockle).

#show flat_mystery/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SCENE_REGISTRY:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("case", "flat_cockle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show flat_mystery/1."))
    return sorted(set(asp.atoms(model, "flat_mystery")))


def asp_verify() -> int:
    python_set = set((p,) for p, _, _ in valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(python_set))
    print("asp:", sorted(asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    scene = SCENE_REGISTRY[params.place]
    case = CASE_REGISTRY["flat-cockle"]
    world = tell(scene, case, params.name, params.friend)
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
    StoryParams(place="the boardwalk", name="Sam", friend="Max"),
    StoryParams(place="the pier", name="Nina", friend="Leo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show flat_mystery/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show flat_mystery/1."))
        combos = sorted(set(asp.atoms(model, "flat_mystery")))
        print(f"{len(combos)} compatible settings:")
        for (place,) in combos:
            print(f"  {place}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} and {p.friend} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
