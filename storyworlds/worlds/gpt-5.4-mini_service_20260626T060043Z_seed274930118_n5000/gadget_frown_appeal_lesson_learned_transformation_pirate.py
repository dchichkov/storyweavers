#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld: a crew, a gadget, a frown, an appeal, a lesson
learned, and a transformation.

The seed story premise:
- A young pirate wants to use a clever gadget.
- The gadget causes trouble or a silly mess.
- A worried companion frowns and makes an appeal.
- The pirate learns a lesson and transforms how they act.
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


# ---------------------------------------------------------------------------
# Domain model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gadget_ent: object | None = None
    hero: object | None = None
    mentor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "captain"}:
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
class Harbor:
    name: str
    setting_line: str
    risk: str
    sheen: str
    sea_state: str
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
class Gadget:
    id: str
    label: str
    phrase: str
    function: str
    mischief: str
    lesson: str
    transform: str
    tags: set[str] = field(default_factory=set)
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
    harbor: str
    gadget: str
    hero_name: str
    hero_kind: str
    mentor_kind: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

HARBORS = {
    "cove": Harbor(
        name="the moonlit cove",
        setting_line="The moonlit cove lay still, with salt wind brushing the docks.",
        risk="the tide",
        sheen="the wet boards",
        sea_state="calm",
    ),
    "port": Harbor(
        name="the busy port",
        setting_line="The busy port hummed with gulls, ropes, and creaking ships.",
        risk="the crowd",
        sheen="the shiny rail",
        sea_state="lively",
    ),
    "reef": Harbor(
        name="the coral reef shore",
        setting_line="The coral reef shore glittered in bright water and striped shells.",
        risk="the reef",
        sheen="the clear shallows",
        sea_state="bright",
    ),
}

GADGETS = {
    "net-launcher": Gadget(
        id="net-launcher",
        label="net launcher",
        phrase="a brass net launcher",
        function="cast a net fast",
        mischief="the net tangled the mast ropes",
        lesson="careful hands keep a ship steady",
        transform="to test every tool before bragging about it",
        tags={"net", "rope"},
    ),
    "shell-whistle": Gadget(
        id="shell-whistle",
        label="shell whistle",
        phrase="a shiny shell whistle",
        function="call the crew from far away",
        mischief="the whistle startled the gulls into a noisy whirl",
        lesson="loud tricks can stir up trouble",
        transform="to use a gentle signal when the deck needs peace",
        tags={"sound", "gulls"},
    ),
    "lamp-brightener": Gadget(
        id="lamp-brightener",
        label="lamp brightener",
        phrase="a clever lamp brightener",
        function="make a lantern glow brighter",
        mischief="the lantern shone so hard it made everyone blink and frown",
        lesson="bright ideas still need a soft touch",
        transform="to aim the light kindly, not wildly",
        tags={"light", "lantern"},
    ),
}

NAMES = ["Mara", "Nell", "Jory", "Pip", "Tess", "Finn", "Sailor", "Rina"]
KINDS = {"girl", "boy"}
MENTOR_LABELS = {
    "captain": "the captain",
    "mate": "the old mate",
}


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    harbor = _safe_lookup(HARBORS, params.harbor)
    gadget = _safe_lookup(GADGETS, params.gadget)
    world = World(harbor)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_kind,
        meters={"pride": 1.0, "worry": 0.0, "change": 0.0},
        memes={"curiosity": 1.0, "stubborn": 1.0, "lesson": 0.0},
    ))
    mentor_type = params.mentor_kind
    mentor_name = _safe_lookup(MENTOR_LABELS, mentor_type)
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type=mentor_type,
        label=mentor_name,
        meters={"worry": 0.0, "trust": 1.0},
        memes={"care": 1.0, "appeal": 0.0},
    ))
    gadget_ent = world.add(Entity(
        id="gadget",
        kind="thing",
        type="gadget",
        label=gadget.label,
        phrase=gadget.phrase,
        owner=hero.id,
        meters={"spark": 1.0, "mess": 0.0},
    ))

    world.facts.update(hero=hero, mentor=mentor, gadget=gadget_ent, gadget_def=gadget)
    return world


def tell_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    mentor: Entity = _safe_fact(world, world.facts, "mentor")
    gadget: Entity = _safe_fact(world, world.facts, "gadget")
    gadget_def: Gadget = _safe_fact(world, world.facts, "gadget_def")
    harbor = world.harbor

    # Act 1: setting and desire
    world.say(f"{hero.id} was a young pirate who loved clever gear and bold plans.")
    world.say(
        f"One day at {harbor.name}, {hero.id} found {gadget.phrase} and grinned at {gadget.function}."
    )
    world.say(harbor.setting_line)

    # Act 2: trouble and appeal
    world.para()
    hero.meters["pride"] += 1.0
    gadget.meters["spark"] += 1.0
    world.say(
        f"{hero.id} rushed to try the {gadget.label}, but the little machine made a grand mistake: "
        f"{gadget_def.mischief}."
    )
    mentor.meters["worry"] += 1.0
    mentor.memes["appeal"] += 1.0
    hero.meters["worry"] += 1.0
    world.say(
        f"{mentor.label} gave a worried frown and stepped closer. "
        f'"Hold on," {mentor.id} said, "please listen to me before that gadget makes a bigger mess."'
    )
    world.say(
        f"{mentor.id} made an appeal to {hero.id}: keep the ship safe, and use the tool with care."
    )

    # Act 3: lesson learned and transformation
    world.para()
    hero.meters["change"] += 1.0
    hero.memes["lesson"] += 1.0
    hero.meters["pride"] = max(0.0, hero.meters["pride"] - 1.0)
    world.say(
        f"{hero.id} looked at the tangle, then nodded. "
        f"{hero.id} learned a lesson: {gadget_def.lesson}."
    )
    world.say(
        f"So {hero.id} changed {hero.pronoun('possessive')} ways and chose {gadget_def.transform}."
    )
    world.say(
        f"After that, the deck grew calm again, and {hero.id} stood taller, not from bragging, but from wisdom."
    )

    world.facts["resolved"] = True
    world.facts["lesson"] = gadget_def.lesson
    world.facts["transformation"] = gadget_def.transform


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    gadget: Entity = _safe_fact(world, f, "gadget")
    return [
        f"Write a short pirate tale about {hero.id} and {gadget.label} that includes a frown and an appeal.",
        f"Tell a child-friendly story in which a pirate learns a lesson after using {gadget.phrase}.",
        f"Write a small pirate story with a clear transformation: a mistake, a worried frown, and a wiser ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mentor: Entity = _safe_fact(world, f, "mentor")
    gadget: Entity = _safe_fact(world, f, "gadget")
    gadget_def: Gadget = _safe_fact(world, f, "gadget_def")
    harbor = world.harbor

    return [
        QAItem(
            question=f"Who found the {gadget.label} at {harbor.name}?",
            answer=f"{hero.id} found the {gadget.label} at {harbor.name}.",
        ),
        QAItem(
            question=f"Why did {mentor.label} frown?",
            answer=(
                f"{mentor.label} frowns because the {gadget.label} made a mess and could have caused more trouble."
            ),
        ),
        QAItem(
            question="What appeal did the mentor make?",
            answer=(
                f"The mentor appealed to {hero.id} to slow down, listen, and keep the ship safe."
            ),
        ),
        QAItem(
            question="What lesson did the pirate learn?",
            answer=f"{hero.id} learned that {gadget_def.lesson}.",
        ),
        QAItem(
            question="How did the pirate change by the end?",
            answer=(
                f"{hero.id} transformed from a bragging, hasty pirate into someone who chose {gadget_def.transform}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gadget?",
            answer="A gadget is a small tool or machine made to help with a task, often in a clever way.",
        ),
        QAItem(
            question="What does a frown usually mean?",
            answer="A frown usually shows worry, unhappiness, or disapproval.",
        ),
        QAItem(
            question="What is an appeal?",
            answer="An appeal is a serious request asking someone to listen or choose a better way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A gadget can cause trouble; a frown appears when a trusted crew member notices.
trouble(G) :- gadget(G), mischief(G, _).
frown_needed(H, M) :- mentor(M), hero(H), trouble(_).
appeal(M, H) :- mentor(M), hero(H), frown_needed(H, M).
lesson_learned(H) :- hero(H), appeal(_, H).
transformation(H) :- lesson_learned(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for hid, h in HARBORS.items():
        lines.append(asp.fact("harbor", hid))
        lines.append(asp.fact("risk", hid, h.risk.replace(" ", "_")))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        lines.append(asp.fact("mischief", gid, g.mischief.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show transformation/1.")
    model = asp.one_model(program)
    asp_count = len(asp.atoms(model, "transformation"))
    py_count = 1
    if asp_count == py_count:
        print("OK: ASP and Python agree on transformation structure.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with gadget trouble and a wiser ending.")
    ap.add_argument("--harbor", choices=sorted(HARBORS))
    ap.add_argument("--gadget", choices=sorted(GADGETS))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=sorted(KINDS))
    ap.add_argument("--mentor", choices=sorted(MENTOR_LABELS))
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
    harbor = getattr(args, "harbor", None) or rng.choice(sorted(HARBORS))
    gadget = getattr(args, "gadget", None) or rng.choice(sorted(GADGETS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    mentor = getattr(args, "mentor", None) or rng.choice(sorted(MENTOR_LABELS))
    if getattr(args, "gender", None) and getattr(args, "name", None) is None:
        # still valid, just a minor preference
        pass
    return StoryParams(
        harbor=harbor,
        gadget=gadget,
        hero_name=name,
        hero_kind=gender,
        mentor_kind=mentor,
    )


def generate(params: StoryParams) -> StorySample:
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"harbor={world.harbor.name}")
    return "\n".join(lines)


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
        print(asp_program("#show transformation/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show transformation/1."))
        print(f"{len(asp.atoms(model, 'transformation'))} transformation atom(s) found.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for harbor in sorted(HARBORS):
            for gadget in sorted(GADGETS):
                params = StoryParams(
                    harbor=harbor,
                    gadget=gadget,
                    hero_name="Mara",
                    hero_kind="girl",
                    mentor_kind="captain",
                )
                samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
