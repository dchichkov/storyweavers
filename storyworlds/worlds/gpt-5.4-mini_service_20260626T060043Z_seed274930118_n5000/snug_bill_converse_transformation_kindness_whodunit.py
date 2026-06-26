#!/usr/bin/env python3
"""
storyworlds/worlds/snug_bill_converse_transformation_kindness_whodunit.py
========================================================================

A small whodunit-style storyworld about a missing bill, a snug little place,
quiet conversation, and a kindness that transforms the whole case.

Seed idea:
- Something in a snug room goes missing.
- Characters converse like a mystery crew.
- A bill is at the center of the puzzle.
- A transformation and a kind act resolve the tension.

The domain is intentionally small and constraint-checked:
- one detective
- one household or shop setting
- a short list of suspects
- one missing bill
- one transformation that changes an item or character state
- one kindness that reveals the truth and resolves suspicion
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    placed_in: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bill: object | None = None
    detective: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "lady"}
        male = {"boy", "man", "father", "uncle", "gentleman"}
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
class Setting:
    place: str
    snug: bool
    surfaces: list[str]
    lighting: str
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
class Suspect:
    id: str
    type: str
    label: str
    habit: str
    kindness: str
    clue: str
    innocent_reason: str
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


@dataclass
class StoryParams:
    setting: str
    suspect: str
    detective_name: str
    detective_type: str
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


SETTINGS = {
    "tea_room": Setting(
        place="the snug tea room",
        snug=True,
        surfaces=["counter", "bench", "shelf"],
        lighting="warm",
    ),
    "bookshop": Setting(
        place="the snug bookshop",
        snug=True,
        surfaces=["ladder", "table", "register"],
        lighting="golden",
    ),
    "hall": Setting(
        place="the little front hall",
        snug=False,
        surfaces=["hook", "rug", "shoe tray"],
        lighting="soft",
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        type="cat",
        label="the cat",
        habit="curling up in the warmest corner",
        kindness="purring beside a worried friend",
        clue="a few silver hairs on the bench",
        innocent_reason="the cat only slept near the bill and never touched it",
    ),
    "neighbor": Suspect(
        id="neighbor",
        type="woman",
        label="the neighbor",
        habit="borrowing sugar and leaving careful notes",
        kindness="holding the door and carrying heavy bags",
        clue="a neat ribbon from a gift parcel",
        innocent_reason="the neighbor had only come to help, not to hide anything",
    ),
    "helper": Suspect(
        id="helper",
        type="boy",
        label="the helper",
        habit="moving chairs and arranging books",
        kindness="straightening broken things with a gentle hand",
        clue="a pencil mark on the receipt pad",
        innocent_reason="the helper was busy mending the shelf, not taking the bill",
    ),
}

TRANSFORMS = {
    "stiff_to_snug": ("stiff", "snug", "a stiff coat became snug after a kind repair"),
    "cold_to_warm": ("cold", "warm", "the room felt warm after the lamp was lit"),
    "tense_to_calm": ("tense", "calm", "the mood turned calm after kind words were spoken"),
}

BILL = {
    "label": "bill",
    "phrase": "a small paper bill",
    "kind": "bill",
}


GENTLE_NAMES = ["Mina", "Lena", "Noah", "Iris", "Theo", "Mara", "Eli", "June"]
TRAITS = ["careful", "quiet", "kind", "curious", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, k) for s in SETTINGS for k in SUSPECTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Whodunit storyworld: a snug place, a missing bill, quiet conversation, and a kind transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
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
    if getattr(args, "gender", None) and getattr(args, "name", None) is None and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    choices = valid_combos()
    if getattr(args, "setting", None):
        choices = [c for c in choices if c[0] == getattr(args, "setting", None)]
    if getattr(args, "suspect", None):
        choices = [c for c in choices if c[1] == getattr(args, "suspect", None)]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, suspect = rng.choice(sorted(choices))
    name = getattr(args, "name", None) or rng.choice(GENTLE_NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    detective_type = gender
    return StoryParams(setting=setting, suspect=suspect, detective_name=name, detective_type=detective_type)


def propagate(world: World) -> None:
    # One simple reasoner: kindness reduces suspicion, transformation changes mood.
    suspect = _safe_fact(world, world.facts, "suspect_entity")
    detective = _safe_fact(world, world.facts, "detective")
    if suspect.memes.get("kindness_seen", 0.0) >= THRESHOLD and suspect.memes.get("suspicion", 0.0) >= THRESHOLD:
        key = ("calm", suspect.id)
        if key not in world.fired:
            world.fired.add(key)
            suspect.memes["suspicion"] = 0.0
            suspect.memes["relief"] = 1.0


def tell(setting: Setting, suspect_cfg: Suspect, detective_name: str, detective_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, traits=["careful", "curious"]))
    suspect = world.add(Entity(id=suspect_cfg.id, kind="character", type=suspect_cfg.type, label=suspect_cfg.label, traits=["quiet"]))
    bill = world.add(Entity(id="bill", kind="thing", type="bill", label="bill", phrase=BILL["phrase"], owner=detective.id))
    bill.placed_in = "receipt tray"

    detective.memes["unease"] = 1.0
    suspect.memes["suspicion"] = 1.0

    world.say(
        f"{detective.id} was a careful little detective who liked to converse softly and notice tiny things."
    )
    world.say(
        f"One evening in {world.setting.place}, {detective.id} found that {BILL['label']} was missing from the receipt tray."
    )
    world.say(
        f"{suspect.label} had been there too, doing {suspect_cfg.habit}, and the room felt strangely snug and quiet."
    )

    world.para()
    world.say(
        f"{detective.id} and {suspect.label} began to converse in low voices. "
        f'"Did you see the bill?" asked {detective.id}. '
        f'"Only this clue," said {suspect.label}, and showed {suspect_cfg.clue}.'
    )

    # Whodunit turn: suspicion rises, then a kindness and a transformation reveal the truth.
    suspect.memes["kindness_seen"] = 1.0
    world.say(
        f"Then {suspect.label} did something kind: {suspect_cfg.kindness}. "
        f"That small kindness changed the whole feeling of the room."
    )
    propagate(world)

    world.para()
    world.say(
        f"{detective.id} looked again and found the bill tucked inside a snug envelope on the shelf."
    )
    world.say(
        f"It had not been stolen at all; it had been moved there to keep it safe from the tea spill by the counter."
    )
    world.say(
        f"The little mystery turned from tense to calm, and even the room seemed transformed by the truth."
    )
    world.say(
        f"{detective.id} thanked {suspect.label} for the kindness, and {suspect.label} smiled because no one was in trouble."
    )

    world.facts.update(
        detective=detective,
        suspect_entity=suspect,
        bill=bill,
        setting=setting,
        suspect_cfg=suspect_cfg,
        solved=True,
        transform="tense_to_calm",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a snug whodunit for a young child about a missing {BILL['label']} in {f['setting'].place}.",
        f"Tell a small mystery where {f['detective'].id} and {f['suspect_entity'].label} converse quietly and a kindness changes the ending.",
        f"Write a simple story with a hidden bill, a calm conversation, and a transformation from tense to calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    suspect = _safe_fact(world, f, "suspect_entity")
    setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"What mystery did {detective.id} solve in {setting.place}?",
            answer=f"{detective.id} solved the mystery of the missing bill in {setting.place}.",
        ),
        QAItem(
            question=f"Who did {detective.id} converse with about the missing bill?",
            answer=f"{detective.id} conversed with {suspect.label}, who had been nearby when the bill went missing.",
        ),
        QAItem(
            question="What kind act helped calm the mystery?",
            answer=f"{suspect.label} did something kind, and that kindness helped turn the tense mood calm.",
        ),
        QAItem(
            question="Where was the bill found in the end?",
            answer="The bill was found tucked inside a snug envelope on the shelf.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does snug mean?",
            answer="Snug means cozy, close-fitting, and comfortable.",
        ),
        QAItem(
            question="What is a bill?",
            answer="A bill is a paper that shows how much something costs or what must be paid.",
        ),
        QAItem(
            question="What does converse mean?",
            answer="Converse means to talk with someone.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form, feeling, or state into another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        if e.placed_in:
            bits.append(f"placed_in={e.placed_in}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="tea_room", suspect="cat", detective_name="Mina", detective_type="girl"),
    StoryParams(setting="bookshop", suspect="helper", detective_name="Theo", detective_type="boy"),
    StoryParams(setting="hall", suspect="neighbor", detective_name="Iris", detective_type="girl"),
]


def explain_rejection() -> str:
    return "(No story: this little mystery only has the curated setting-suspect combinations.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SUSPECTS, params.suspect), params.detective_name, params.detective_type)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.snug:
            lines.append(asp.fact("snug", sid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("kindness", sid))
    lines.append(asp.fact("keyword", "snug"))
    lines.append(asp.fact("keyword", "bill"))
    lines.append(asp.fact("keyword", "converse"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, X) :- setting(S), suspect(X).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("compatible setting/suspect pairs:")
        for setting, suspect in asp_valid_combos():
            print(setting, suspect)
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
            header = f"### {p.name}: {p.setting} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
