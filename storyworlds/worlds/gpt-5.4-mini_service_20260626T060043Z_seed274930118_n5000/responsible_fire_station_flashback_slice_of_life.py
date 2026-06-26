#!/usr/bin/env python3
"""
responsible_fire_station_flashback_slice_of_life.py
===================================================

A tiny storyworld about a fire station, where a responsible rookie remembers a
small past mistake and uses that flashback to do the right thing now.

Premise:
- A young helper at the station wants to keep the trucks, hoses, and lunch area
  ready for an ordinary day.

Tension:
- A past flashback reminds the helper what happened when a small job was rushed.

Turn:
- The helper slows down, checks the gear, and fixes the routine before anybody
  needs to ask.

Resolution:
- The station ends the day tidy, ready, and calm, with responsibility proving
  its worth in a quiet slice-of-life way.
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

FLASHBACK_TRIGGER = 1.0
ROUTINE_TRIGGER = 1.0



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
    role: str = ""
    owner: Optional[str] = None
    uses: int = 0
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    partner: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Station:
    place: str = "the fire station"
    station_name: str = "Station 7"
    shift: str = "morning"
    affords: set[str] = field(default_factory=lambda: {"gear_check", "tea_break", "truck_wipe_down", "logbook"})
    quiet: bool = True
    STATION: object | None = None
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
    name: str
    role: str
    partner_role: str
    task: str
    flashback_task: str
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
    def __init__(self, station: Station) -> None:
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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
        import copy as _copy

        w = World(self.station)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _flashback(world: World, hero: Entity, task: str, old_task: str) -> None:
    if hero.memes.get("memory", 0.0) < FLASHBACK_TRIGGER:
        return
    sig = ("flashback", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.say(
        f"As {hero.id} reached for the checklist, a flashback drifted in: last week, "
        f"they had rushed the {old_task}, and the little mistake had made extra work for everyone."
    )
    hero.memes["careful"] = hero.memes.get("careful", 0.0) + 1


def _routine(world: World, hero: Entity, partner: Entity, task: str) -> None:
    if hero.memes.get("careful", 0.0) < ROUTINE_TRIGGER:
        return
    sig = ("routine", hero.id, task)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.meters["order"] = hero.meters.get("order", 0.0) + 1
    partner.meters["calm"] = partner.meters.get("calm", 0.0) + 1
    world.say(
        f"{hero.id} slowed down, checked the {task}, and set everything back in its proper place."
    )


def _tidy(world: World, hero: Entity, partner: Entity) -> None:
    sig = ("tidy", hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.say(
        f"By the end of the shift, the floor gleamed, the mugs were stacked, and the trucks were ready."
    )
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    partner.memes["pride"] = partner.memes.get("pride", 0.0) + 1


def propagate(world: World) -> None:
    _flashback(world, world.get("hero"), world.facts["task"], world.facts["flashback_task"])
    _routine(world, world.get("hero"), world.get("partner"), world.facts["task"])
    _tidy(world, world.get("hero"), world.get("partner"))


STATION = Station()

HEROES = [
    ("Mina", "girl"),
    ("Eli", "boy"),
    ("Nora", "girl"),
    ("Leo", "boy"),
    ("Ari", "girl"),
]

PARTNERS = ["captain", "mentor", "crew chief"]
TASKS = {
    "gear check": "the gear check",
    "truck wipe-down": "the truck wipe-down",
    "logbook": "the logbook",
    "tea break": "the tea break table",
}
FLASHBACK_TASKS = {
    "gear check": "the gear check",
    "truck wipe-down": "the truck wipe-down",
    "logbook": "the logbook",
    "tea break": "the spilled tea cups",
}


def tell(params: StoryParams) -> World:
    world = World(STATION)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        role=params.role,
        meters={"order": 0.0},
        memes={"responsible": 1.0, "memory": 1.0},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=params.partner_role,
        role=params.partner_role,
        label=f"the {params.partner_role}",
        meters={"calm": 0.0},
        memes={"trust": 1.0},
    ))
    world.facts.update(hero=hero, partner=partner, task=params.task, flashback_task=params.flashback_task)

    world.say(
        f"{hero.id} was a responsible {hero.role} at {world.station.station_name}, and {hero.pronoun()} liked the steady rhythm of the morning shift."
    )
    world.say(
        f"{hero.id} and {partner.label} started with {_safe_lookup(TASKS, params.task)}, because a quiet station still had to stay ready."
    )
    world.para()
    world.say(
        f"While they worked, {hero.id} noticed a small scuff near the supply shelf."
    )
    propagate(world)
    world.para()
    world.say(
        f"{hero.id} put the last item away, wiped the counter once more, and smiled at how peaceful the station felt."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a slice-of-life story about {f['hero'].id}, a responsible {f['hero'].role}, at a fire station.",
        f"Tell a gentle fire-station story where a flashback helps a {f['hero'].role} remember to do {f['task']} carefully.",
        f"Write a short story that includes a flashback, a quiet routine, and a responsible choice at {world.station.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    partner = _safe_fact(world, f, "partner")
    task = _safe_fact(world, f, "task")
    old = _safe_fact(world, f, "flashback_task")
    return [
        QAItem(
            question=f"Where does {hero.id} work in the story?",
            answer=f"{hero.id} works at {world.station.station_name}, which is a fire station."
        ),
        QAItem(
            question=f"What task was {hero.id} doing when the flashback came back?",
            answer=f"{hero.id} was doing {task} when the memory of rushing the {old} came back."
        ),
        QAItem(
            question=f"How did the flashback change what {hero.id} did next?",
            answer=(
                f"The flashback made {hero.id} slow down, check the work carefully, and finish the job in a responsible way."
            ),
        ),
        QAItem(
            question=f"Who worked with {hero.id} during the quiet shift?",
            answer=f"{hero.id} worked with {partner.label} during the shift."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fire station?",
            answer="A fire station is a place where firefighters keep their trucks, gear, and supplies ready."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory scene that shows something from earlier in the past."
        ),
        QAItem(
            question="What does responsible mean?",
            answer="Responsible means doing what needs to be done carefully and reliably."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    lines.append(f"  fired={sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small responsible fire-station slice-of-life storyworld with flashback.")
    ap.add_argument("--name", choices=[n for n, _ in HEROES])
    ap.add_argument("--role", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=PARTNERS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--flashback-task", choices=FLASHBACK_TASKS)
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
    name, role = getattr(args, "name", None), getattr(args, "role", None)
    if name is None or role is None:
        name, role = rng.choice(HEROES)
    partner = getattr(args, "partner", None) or rng.choice(PARTNERS)
    task = getattr(args, "task", None) or rng.choice(list(TASKS))
    flash = getattr(args, "flashback_task", None) or task
    if getattr(args, "flashback_task", None) and getattr(args, "flashback_task", None) not in FLASHBACK_TASKS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, role=role, partner_role=partner, task=task, flashback_task=flash)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
% A responsible helper notices a memory and then does the task carefully.
memory(hero) :- responsible(hero), flashback(hero).
careful(hero) :- memory(hero).
ready(hero) :- careful(hero), task(hero).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for name, role in HEROES:
        lines.append(asp.fact("hero", name))
        lines.append(asp.fact("role", name, role))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for t in FLASHBACK_TASKS:
        lines.append(asp.fact("flashback_task", t))
    lines.append(asp.fact("responsible", "hero"))
    lines.append(asp.fact("flashback", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show ready/1."))
    atoms = set(asp.atoms(model, "ready"))
    if atoms == {("hero",)}:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH: ASP reasoner did not derive readiness as expected.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show ready/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show ready/1."))
        print(asp.atoms(model, "ready"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        presets = [
            StoryParams("Mina", "girl", "mentor", "gear check", "truck wipe-down"),
            StoryParams("Eli", "boy", "captain", "truck wipe-down", "logbook"),
            StoryParams("Nora", "girl", "crew chief", "logbook", "tea break"),
        ]
        samples = [generate(p) for p in presets]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1 and not getattr(args, "all", None):
            print(f"### variant {idx + 1}")
        elif getattr(args, "all", None):
            p = sample.params
            print(f"### {p.name}: {p.task} with a flashback")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
