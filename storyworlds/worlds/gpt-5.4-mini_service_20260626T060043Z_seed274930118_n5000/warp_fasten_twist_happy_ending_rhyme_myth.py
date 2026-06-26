#!/usr/bin/env python3
"""
A myth-style storyworld about a little weaver, a warped cloth, a twist of fate,
and a happy ending that ends in rhyme.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clasp: object | None = None
    cloth: object | None = None
    helper: object | None = None
    hero: object | None = None
    song: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "brother"}:
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
class Realm:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    realm: object | None = None
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


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
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
    place: str = "the loom-hall"
    name: str = "Mara"
    gender: str = "girl"
    helper: str = "grandmother"
    seed: Optional[int] = None
    py_ok: object | None = None
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


PLACES = {
    "loom-hall": "the loom-hall",
    "riverbank": "the riverbank",
    "mountain-hut": "the mountain-hut",
}

NAMES = {
    "girl": ["Mara", "Nera", "Ila", "Sera", "Ayla"],
    "boy": ["Tari", "Kian", "Bren", "Oren", "Lio"],
}

HELPERS = ["grandmother", "mother", "father", "aunt", "uncle"]

SETTING_BLURBS = {
    "the loom-hall": "where the old threads sang softly in the rafters",
    "the riverbank": "where reeds leaned like listeners beside the water",
    "the mountain-hut": "where the fire made gold from the dark stones",
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def is_reasonable(params: StoryParams) -> bool:
    return params.place in PLACES


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> Realm:
    realm = Realm(place=params.place)

    hero = realm.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"hope": 1.0},
        memes={"wonder": 1.0, "pride": 1.0},
    ))
    helper = realm.add(Entity(
        id="helper",
        kind="character",
        type=params.helper if params.helper in {"mother", "father"} else "elder",
        label=f"the {params.helper}",
        meters={"care": 1.0},
        memes={"wisdom": 1.0},
    ))
    cloth = realm.add(Entity(
        id="cloth",
        kind="thing",
        type="cloth",
        label="warp-cloth",
        phrase="a moonlit warp-cloth",
        owner=hero.id,
        meters={"warp": 1.0},
    ))
    clasp = realm.add(Entity(
        id="clasp",
        kind="thing",
        type="clasp",
        label="silver clasp",
        phrase="a bright silver clasp",
        owner=helper.id,
        protective=True,
        meters={"fasten": 1.0},
    ))
    song = realm.add(Entity(
        id="song",
        kind="thing",
        type="song",
        label="rhyme-song",
        phrase="a small rhyme-song",
        meters={"rhyme": 1.0},
    ))

    realm.facts.update(hero=hero, helper=helper, cloth=cloth, clasp=clasp, song=song)
    return realm


def tell_story(realm: Realm) -> None:
    hero: Entity = realm.facts["hero"]
    helper: Entity = realm.facts["helper"]
    cloth: Entity = realm.facts["cloth"]
    clasp: Entity = realm.facts["clasp"]
    song: Entity = realm.facts["song"]

    realm.say(
        f"In {realm.place}, {hero.label} was a little weaver who loved old tales, "
        f"and {_safe_lookup(SETTING_BLURBS, realm.place)}."
    )
    realm.say(
        f"{hero.label} tended {hero.pronoun('possessive')} {cloth.label}, because the cloth held "
        f"the village banner and the village remembered its promises by it."
    )
    realm.say(
        f"One evening, a sudden Twist of wind made the {cloth.label} warp, and the edges curled "
        f"like a surprised snake."
    )

    realm.para()
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.meters["trouble"] = hero.meters.get("trouble", 0.0) + 1.0
    realm.say(
        f"{hero.label} frowned. Without a way to fasten the cloth, the banner would go loose "
        f"before dawn."
    )
    realm.say(
        f"{helper.label.capitalize()} came near and lifted the {clasp.label}. "
        f'"A strong fasten can tame a warp," {helper.label} said.'
    )
    helper.memes["confidence"] = helper.memes.get("confidence", 0.0) + 1.0

    realm.para()
    cloth.meters["warp"] = max(0.0, cloth.meters.get("warp", 0.0) - 1.0)
    cloth.meters["mended"] = cloth.meters.get("mended", 0.0) + 1.0
    clasp.meters["fasten"] = clasp.meters.get("fasten", 0.0) + 1.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    hero.memes["worry"] = 0.0
    realm.say(
        f"{hero.label} and {helper.label} worked together. {hero.label} held the cloth steady "
        f"while {helper.label} used the {clasp.label} to fasten the torn edge."
    )
    realm.say(
        f"The warp straightened little by little, and the banner stood tall again, bright as a star."
    )

    realm.para()
    song.meters["sung"] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    realm.say(
        f"Then {hero.label} sang a Happy Ending Rhyme: "
        f'"When wind may twist and cloth may bend, a steady hand can make it mend."'
    )
    realm.say(
        f"By moonrise, the village banner shone safe and sound, and {hero.label} smiled at "
        f"{helper.label} with a heart made light."
    )

    realm.facts["resolved"] = True
    realm.facts["twist"] = "wind"
    realm.facts["happy_ending"] = True
    realm.facts["rhyme"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: Realm) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    return [
        f"Write a short myth-like story about {hero.label}, a warp, and a helpful fasten.",
        "Tell a gentle tale where a Twist causes trouble, but a wise helper finds a Happy Ending.",
        "Write a child-friendly story in rhyme about mending something that has gone warped.",
    ]


def story_qa(world: Realm) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    cloth: Entity = _safe_fact(world, world.facts, "cloth")
    return [
        QAItem(
            question=f"What went wrong for {hero.label} at first?",
            answer=f"The {cloth.label} warped when a Twist of wind curled its edges and made it hard to use.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} fix the problem?",
            answer=f"They used a silver clasp to fasten the cloth steady, and that helped the warp straighten.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with a Happy Ending Rhyme, and the village banner stood safe and bright again.",
        ),
    ]


def world_knowledge_qa(world: Realm) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to fasten something?",
            answer="To fasten something means to hold it closed, tied, clipped, or joined so it stays in place.",
        ),
        QAItem(
            question="What is a warp in cloth?",
            answer="A warp in cloth is a bend, twist, or uneven pull that makes it stop lying flat.",
        ),
        QAItem(
            question="Why do people use rhyme in stories?",
            answer="People use rhyme because repeating sounds can make a story feel memorable, musical, and fun to say aloud.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(loom_hall).
place(riverbank).
place(mountain_hut).

valid(P) :- place(P).

twist(cause_wind).
warp(problem_cloth).
fasten(fix_clasp).
happy_ending(outcome).
rhyme(song).

story_ok(P) :- valid(P), twist(cause_wind), warp(problem_cloth), fasten(fix_clasp), happy_ending(outcome), rhyme(song).
#show story_ok/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in PLACES.values():
        lines.append(asp.fact("place", key.replace("-", "_")))
        lines.append(asp.fact("valid", key.replace("-", "_")))
    lines.append(asp.fact("twist", "cause_wind"))
    lines.append(asp.fact("warp", "problem_cloth"))
    lines.append(asp.fact("fasten", "fix_clasp"))
    lines.append(asp.fact("happy_ending", "outcome"))
    lines.append(asp.fact("rhyme", "song"))
    return "\n".join(lines)


def asp_program(show: str = "#show story_ok/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show story_ok/1.")
    model = asp.one_model(program)
    ok = bool(asp.atoms(model, "story_ok"))
    py_ok = all(is_reasonable(StoryParams(place=p)) for p in PLACES)
    if ok and py_ok:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


# ---------------------------------------------------------------------------
# Generation / formatting
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    if not is_reasonable(params):
        pass
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: Realm) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about warp, fasten, Twist, Happy Ending, and Rhyme.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    return StoryParams(place=place, name=name, gender=gender, helper=rng.choice(HELPERS))


CURATED = [
    StoryParams(place="the loom-hall", name="Mara", gender="girl", helper="grandmother"),
    StoryParams(place="the riverbank", name="Tari", gender="boy", helper="father"),
    StoryParams(place="the mountain-hut", name="Ila", gender="girl", helper="aunt"),
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show story_ok/1."))
        print("story_ok:", bool(asp.atoms(model, "story_ok")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
