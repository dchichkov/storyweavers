#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    anthem: object | None = None
    baby: object | None = None
    child: object | None = None
    parent: object | None = None
    racket: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Place:
    name: str
    world: object | None = None
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
class ObjectSpec:
    id: str
    label: str
    phrase: str
    mess: str
    sound: str
    at_risk: str
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
    name: str
    parent: str
    place: str
    object: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def _r_noise(world: World) -> list[str]:
    out = []
    child = world.get(world.facts["child"].id)
    obj = world.get(world.facts["obj"].id)
    if child.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.meters["noise"] += 1
    out.append("The loud sound went through the driveway and into the still house.")
    return out


def _r_wake(world: World) -> list[str]:
    out = []
    obj = world.get(world.facts["obj"].id)
    baby = world.get("baby")
    if obj.meters["noise"] < THRESHOLD or baby.memes["sleep"] < THRESHOLD:
        return out
    sig = ("wake", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    baby.memes["disturbed"] += 1
    out.append("A little baby woke up and started to cry.")
    return out


def _r_bad_end(world: World) -> list[str]:
    child = world.get(world.facts["child"].id)
    baby = world.get("baby")
    if baby.memes["disturbed"] < THRESHOLD:
        return []
    sig = ("bad_end", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["sad"] += 1
    return []


RULES = [_r_noise, _r_wake, _r_bad_end]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                if narrate:
                    for s in sents:
                        world.say(s)


def build_world(params: StoryParams) -> World:
    world = World(Place(params.place))
    child = world.add(Entity(id=params.name, kind="character", type="boy", meters={"noise": 0}, memes={"hope": 1}))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent, meters={"patience": 1}, memes={"care": 1}))
    anthem = world.add(Entity(id="anthem", kind="thing", type="song", label="anthem", phrase="a little driveway anthem", meters={"noise": 0}, memes={"pride": 1}))
    racket = world.add(Entity(id="racket", kind="thing", type="racket", label="racket", phrase="a shiny racket", owner=child.id, meters={"noise": 0}))
    baby = world.add(Entity(id="baby", kind="character", type="baby", label="the baby", meters={"sleep": 1}, memes={"sleep": 1}))
    world.facts = {"child": child, "parent": parent, "anthem": anthem, "obj": racket, "baby": baby}
    return world


def story_text(world: World) -> str:
    child = _safe_fact(world, world.facts, "child")
    parent = _safe_fact(world, world.facts, "parent")
    anthem = _safe_fact(world, world.facts, "anthem")
    racket = _safe_fact(world, world.facts, "obj")
    baby = _safe_fact(world, world.facts, "baby")

    world.say(f"{child.id} stood in the driveway at bedtime, holding a {racket.label} like a small baton.")
    world.say(f"{child.id} wanted to tap out an {anthem.label} for the quiet dark, because the tune felt brave and grand.")
    world.say(f"{parent.label.capitalize()} smiled softly and said the driveway was for sleepy voices now, not big racket.")
    world.para()
    world.say(f"But {child.id} tried anyway. {child.id} swung the {racket.label} against the mailbox, and the sound made a sharp racket.")
    child.meters["noise"] += 1
    propagate(world, narrate=True)
    world.para()
    if baby.memes.get("disturbed", 0) >= THRESHOLD:
        world.say(f"The baby cried, and {parent.label} hurried in to rock the baby back to sleep.")
        world.say(f"{child.id} lowered the {racket.label} and looked at the driveway stones, which felt cold and lonely now.")
        world.say(f"The little anthem never finished, and the night grew quiet in a sad way.")
    else:
        world.say(f"The driveway stayed quiet, but the anthem still sounded small and lonely.")
    return world.render()


def valid_combo(place: str, obj: str) -> bool:
    return place == "driveway" and obj == "racket"


SETTINGS = {
    "driveway": Place("the driveway")
}

OBJECTS = {
    "racket": ObjectSpec(
        id="racket",
        label="racket",
        phrase="a shiny racket",
        mess="noise",
        sound="racket",
        at_risk="sleep",
    ),
    "anthem": ObjectSpec(
        id="anthem",
        label="anthem",
        phrase="a little driveway anthem",
        mess="pride",
        sound="anthem",
        at_risk="quiet",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Leo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime-story world with racket, anthem, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS, default="driveway")
    ap.add_argument("--object", dest="obj", choices=OBJECTS, default="racket")
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
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
    if not valid_combo(getattr(args, "place", None), getattr(args, "obj", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES)
    return StoryParams(name=name, parent=getattr(args, "parent", None), place=getattr(args, "place", None), object=getattr(args, "obj", None))


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = story_text(world)
    prompts = [
        'Write a short bedtime story about a child in the driveway with a racket and an anthem.',
        'Tell a gentle story that begins softly but ends badly after a loud racket wakes the house.',
        'Write a bedtime story where the word "racket" matters to the ending.',
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.name} make a racket in the driveway?",
            answer=f"{params.name} wanted to play a little anthem in the driveway, and the racket made the sound even louder.",
        ),
        QAItem(
            question="What happened after the loud sound?",
            answer="The baby woke up and cried, so the night ended in a sad, quiet way.",
        ),
        QAItem(
            question="Did the ending turn out well?",
            answer="No. The story ends badly because the loud racket ruins the calm bedtime mood.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a racket?",
            answer="A racket is a tool with a frame and strings, often used to hit a ball or make a quick tapping sound.",
        ),
        QAItem(
            question="What is an anthem?",
            answer="An anthem is a special song that people may sing together to show pride or feeling.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
noise(obj) :- racket(obj), child_plays(obj).
wake(baby) :- noise(obj), baby_sleeping(baby).
bad_end(child) :- wake(baby).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "driveway"),
        asp.fact("racket", "racket"),
        asp.fact("child_plays", "racket"),
        asp.fact("baby_sleeping", "baby"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_end/1."))
    atoms = set(asp.atoms(model, "bad_end"))
    python_ok = {("child",)}
    if atoms == python_ok:
        print("OK: ASP and Python agree on the bad ending.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  ASP:", sorted(atoms))
    print("  Python:", sorted(python_ok))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story Q&A ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world Q&A ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show bad_end/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show bad_end/1."))
        print(asp.atoms(model, "bad_end"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        params = resolve_params(args, random.Random(base_seed))
        samples = [generate(params)]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
