#!/usr/bin/env python3
"""
storyworlds/worlds/beebee_exposure_casualty_quest_surprise_flashback_detective.py
=================================================================================

A small detective-story world about Beebee, a risky exposure, and one casualty
that turns a quiet quest into a surprising case with a flashback solution.

The seed tale behind this world:
---
Beebee was a careful little detective who loved quests. One wet morning, a note
about a missing brass button was left on her desk. The note said the button had
been seen near the fountain, where the wind and rain made everything slippery.

Beebee set out on her quest with her magnifying glass and a tidy notebook. But
when she left her clue card out in the rain, the card curled up and became a
casualty of exposure. Beebee frowned, then remembered a flashback from yesterday:
the gardener had tied a ribbon to the gate because the fountain pump had
splashed too far. That surprise mattered. The ribbon would lead her to the
button.

Beebee followed the ribbon, solved the case, and tucked the recovered button
safely into an envelope.
---

World model:
- Typed entities with physical meters and emotional memes.
- Exposure can damage an uncovered clue or token.
- Quest advances through places and clues.
- Surprise is a causal turn discovered in a flashback.
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    exposed: bool = False

    beebee: object | None = None
    clue: object | None = None
    envelope: object | None = None
    ribbon: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
    place: str = "the fountain square"
    afford_quest: bool = True
    afford_flashback: bool = True
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
class Case:
    title: str
    missing: str
    clue: str
    casualty: str
    exposure: str
    surprise: str
    flashback: str
    resolution: str
    case: object | None = None
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
    place: str
    case: str
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

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_exposure_damage(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if not e.exposed:
            continue
        if e.meters.get("protected", 0) >= THRESHOLD:
            continue
        if e.meters.get("damage", 0) >= THRESHOLD:
            continue
        sig = ("damage", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["damage"] = e.meters.get("damage", 0) + 1
        out.append(f"The {e.label} became a casualty of exposure.")
    return out


def _r_clue_found(world: World) -> list[str]:
    out: list[str] = []
    clue = world.entities.get("clue")
    if not clue or clue.meters.get("found", 0) >= THRESHOLD:
        return out
    if world.facts.get("followed_ribbon"):
        sig = ("found", clue.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        clue.meters["found"] = 1
        out.append("The clue had finally been found.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_exposure_damage, _r_clue_found):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_title(case: Case) -> str:
    return f"The Case of the {case.title}"


def build_world() -> tuple[World, Entity, Entity, Entity, Entity, Case]:
    setting = Setting()
    world = World(setting)
    beebee = world.add(Entity(id="Beebee", kind="character", type="girl", label="Beebee"))
    beebee.memes["curiosity"] = 1
    beebee.memes["duty"] = 1

    clue = world.add(Entity(
        id="clue",
        type="paper",
        label="clue card",
        phrase="a neat clue card",
        owner="Beebee",
    ))
    clue.meters["clean"] = 1

    envelope = world.add(Entity(
        id="envelope",
        type="envelope",
        label="envelope",
        phrase="a brown envelope",
        owner="Beebee",
    ))
    envelope.meters["safe"] = 1

    ribbon = world.add(Entity(
        id="ribbon",
        type="ribbon",
        label="ribbon",
        phrase="a red ribbon tied to the gate",
        owner="gardener",
    ))
    ribbon.meters["signal"] = 1

    case = Case(
        title="Brass Button",
        missing="brass button",
        clue="clue card",
        casualty="clue card",
        exposure="rain",
        surprise="the gardener had tied a ribbon to the gate",
        flashback="yesterday's splash by the fountain pump",
        resolution="the missing brass button was caught in the gate latch",
    )
    return world, beebee, clue, envelope, ribbon, case


def setup(world: World, beebee: Entity, clue: Entity, case: Case) -> None:
    world.say(f"Beebee was a careful little detective who loved a good quest.")
    world.say(f"One wet morning, a note about a missing {case.missing} waited on her desk.")
    world.say(f"She packed her magnifying glass, her notebook, and {clue.phrase}.")
    world.say(f"The case felt important, because a small clue could change everything.")


def begin_quest(world: World, beebee: Entity, clue: Entity, case: Case) -> None:
    world.para()
    world.say(f"Beebee went to {world.setting.place} to follow the first lead.")
    world.say(f"The air was damp, and the rain made the stones shine.")
    world.say(f"She wanted to solve the quest before the trail went cold.")


def exposure_turn(world: World, clue: Entity, case: Case) -> None:
    world.say(f"But Beebee set her {clue.label} on a ledge, and the rain reached it.")
    clue.exposed = True
    clue.meters["wet"] = clue.meters.get("wet", 0) + 1
    propagate(world, narrate=True)


def surprise_flashback(world: World, ribbon: Entity, case: Case) -> None:
    world.para()
    world.say("Then came a surprise.")
    world.say(f"Beebee paused and had a flashback to {case.flashback}.")
    world.say(f"In that memory, she saw that {case.surprise}.")
    world.facts["followed_ribbon"] = True
    ribbon.meters["noted"] = 1
    propagate(world, narrate=True)


def resolve_case(world: World, beebee: Entity, clue: Entity, envelope: Entity, case: Case) -> None:
    world.para()
    world.say(f"Beebee followed the ribbon and found that {case.resolution}.")
    clue.meters["found"] = 1
    clue.exposed = False
    envelope.meters["safe"] = 1
    envelope.carried_by = beebee.id
    beebee.memes["relief"] = beebee.memes.get("relief", 0) + 1
    beebee.memes["joy"] = beebee.memes.get("joy", 0) + 1
    world.say(f"She tucked the clue into the {envelope.label}, where it stayed dry and safe.")
    world.say("The mystery was solved, and the little detective smiled at the shiny gate.")


def tell(case: Case) -> World:
    world, beebee, clue, envelope, ribbon, _ = build_world()
    setup(world, beebee, clue, case)
    begin_quest(world, beebee, clue, case)
    exposure_turn(world, clue, case)
    surprise_flashback(world, ribbon, case)
    resolve_case(world, beebee, clue, envelope, case)
    world.facts.update(
        beebee=beebee,
        clue=clue,
        envelope=envelope,
        ribbon=ribbon,
        case=case,
        resolved=True,
    )
    return world


CASES = {
    "button": Case(
        title="Brass Button",
        missing="brass button",
        clue="clue card",
        casualty="clue card",
        exposure="rain",
        surprise="the gardener had tied a ribbon to the gate",
        flashback="yesterday's splash by the fountain pump",
        resolution="the missing brass button was caught in the gate latch",
    ),
    "toy": Case(
        title="Tiny Toy Train",
        missing="toy train",
        clue="note page",
        casualty="note page",
        exposure="spray",
        surprise="the baker had set a blue crate by the window",
        flashback="the morning delivery cart rolled past the bakery",
        resolution="the toy train was under the blue crate",
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    return [("the fountain square", "button"), ("the bakery lane", "toy")]


@dataclass
class WorldSampleData:
    world: World
    beebee: Entity
    clue: Entity
    envelope: Entity
    ribbon: Entity
    case: Case
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


def generation_prompts(world: World) -> list[str]:
    c = _safe_fact(world, world.facts, "case")
    return [
        f"Write a short detective story for a child about Beebee solving the case of the {c.missing}.",
        f"Tell a quest story where exposure hurts a clue, then a surprise and flashback help Beebee solve the mystery.",
        f"Write a gentle detective story with Beebee, a casualty of exposure, and a surprising clue at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "case")
    return [
        QAItem(
            question="Who was the little detective in the story?",
            answer="Beebee was the little detective, and she loved quests and careful clues.",
        ),
        QAItem(
            question=f"What happened to the {c.casualty} when the rain reached it?",
            answer=f"The {c.casualty} became a casualty of exposure and curled up from the wet weather.",
        ),
        QAItem(
            question="What surprise helped Beebee solve the case?",
            answer=f"The surprise was that {c.surprise}, and the flashback made that idea make sense.",
        ),
        QAItem(
            question="How did Beebee keep the clue safe at the end?",
            answer="She tucked the clue into an envelope so it could stay dry and neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is exposure?",
            answer="Exposure means something is left out where air, rain, or sun can reach it.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is someone who looks for clues and solves mysteries.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory of something that happened earlier.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is a new fact that changes what the hero understands.",
        ),
    ]


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
    lines.append("== World knowledge questions ==")
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
        if e.exposed:
            bits.append("exposed=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: Beebee, exposure, casualty, quest, surprise, flashback.")
    ap.add_argument("--place", choices=["the fountain square", "the bakery lane"], default=None)
    ap.add_argument("--case", choices=CASES.keys(), default=None)
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
    place = getattr(args, "place", None) or rng.choice(list({p for p, _ in valid_combos()}))
    case = getattr(args, "case", None) or rng.choice(list(CASES.keys()))
    if (place, case) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, case=case)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(CASES, params.case))
    world.setting.place = params.place
    world.facts["place"] = params.place
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
place(fountain_square).
place(bakery_lane).

case(button).
case(toy).

valid_story(P, C) :- place(P), case(C), combo(P, C).

combo(fountain_square, button).
combo(bakery_lane, toy).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("place", "fountain_square"))
    lines.append(asp.fact("place", "bakery_lane"))
    lines.append(asp.fact("case", "button"))
    lines.append(asp.fact("case", "toy"))
    lines.append(asp.fact("combo", "fountain_square", "button"))
    lines.append(asp.fact("combo", "bakery_lane", "toy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    cl = {(p.replace("_", " "), c) for (p, c) in cl}
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


CURATED = [
    StoryParams(place="the fountain square", case="button"),
    StoryParams(place="the bakery lane", case="toy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for p, c in stories:
            print(f"  {p.replace('_', ' '):18} {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.place} / {p.case}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
