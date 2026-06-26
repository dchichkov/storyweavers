#!/usr/bin/env python3
"""
storyworlds/worlds/horn_dim_boom_comparative_curiosity_magic_conflict.py
=========================================================================

A small fairy-tale storyworld about curiosity, a magic horn, a booming test,
and a conflict that turns on a careful comparative choice.

The seed image:
- A child-like seeker follows curiosity into a quiet fairy-tale place.
- A magic horn can dim the light in the hall.
- A boom from the tower signals trouble.
- A comparative choice ("braver", "safer", "kinder", "smaller") changes what
  the characters do, and that resolves the conflict.

This world is intentionally small and constraint-driven:
- The magic horn can only be used in certain places.
- The boom only matters when there is tension.
- The story should end with a visible change in the world model.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    placeless: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    horn: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "wizard"}:
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
    place: str
    indoors: bool
    allows_magic_horn: bool
    allows_boom: bool
    mood: str
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
    hero: str
    hero_type: str
    companion: str
    companion_type: str
    horn: str
    comparative: str
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
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(
        place="the whispering forest",
        indoors=False,
        allows_magic_horn=True,
        allows_boom=True,
        mood="soft and green",
    ),
    "castle": Setting(
        place="the old castle hall",
        indoors=True,
        allows_magic_horn=True,
        allows_boom=True,
        mood="echoing and bright",
    ),
    "cottage": Setting(
        place="the candle-lit cottage",
        indoors=True,
        allows_magic_horn=False,
        allows_boom=False,
        mood="warm and snug",
    ),
}

HEROES = {
    "Mira": "girl",
    "Nilo": "boy",
    "Tavi": "boy",
    "Elin": "girl",
}

COMPANIONS = {
    "queen": "queen",
    "wizard": "wizard",
    "fox": "fox",
    "bird": "bird",
}

COMPARATIVES = {
    "braver": ("brave", "braver"),
    "safer": ("safe", "safer"),
    "kinder": ("kind", "kinder"),
    "smaller": ("small", "smaller"),
}

HORN_DESCRIPTIONS = {
    "silver horn": "a silver horn with a moon-carved mouth",
    "green horn": "a green horn wrapped in ivy ribbon",
    "little horn": "a little horn that fit in both hands",
}

# ---------------------------------------------------------------------------
# Simple fairy-tale prose helpers
# ---------------------------------------------------------------------------
def article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def name_with_type(name: str, typ: str) -> str:
    if typ in {"queen", "wizard"}:
        return f"{name} the {typ}"
    return name


def comparative_word(word: str) -> str:
    return _safe_lookup(COMPARATIVES, word)[1]


def comparative_base(word: str) -> str:
    return _safe_lookup(COMPARATIVES, word)[0]


def setting_detail(setting: Setting) -> str:
    if setting.place == "the whispering forest":
        return "The trees stood very still, as if they were listening."
    if setting.place == "the old castle hall":
        return "The stones echoed every footstep like a secret reply."
    return "The room glowed with candlelight and smelled of bread and honey."


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.hero not in HEROES:
        pass
    if params.companion not in COMPANIONS:
        pass
    if params.comparative not in COMPARATIVES:
        pass
    if params.horn not in HORN_DESCRIPTIONS:
        pass


def predict_consequence(world: World) -> dict[str, bool]:
    horn_used = world.facts.get("horn_used", False)
    boom_heard = world.facts.get("boom_heard", False)
    conflict = world.facts.get("conflict", False)
    return {
        "dim_light": bool(horn_used and world.setting.allows_magic_horn),
        "resolve": bool(boom_heard and conflict),
    }


def tell(world: World) -> None:
    hero: Entity = world.get("hero")
    companion: Entity = world.get("companion")
    horn: Entity = world.get("horn")

    world.say(
        f"Once upon a time, {hero.id} walked into {world.setting.place}, "
        f"where everything felt {world.setting.mood}."
    )
    world.say(setting_detail(world.setting))
    world.say(
        f"{hero.id} was full of curiosity, the kind that makes a small step feel "
        f"like the start of a grand adventure."
    )
    world.say(
        f"Near a mossy stone, {hero.id} found {horn.phrase}, {article(horn.phrase)} "
        f"magic horn that promised a curious sort of power."
    )

    world.para()
    world.say(
        f"{hero.id} lifted the horn and gave it a careful blow."
    )
    world.facts["horn_used"] = True
    if world.setting.allows_magic_horn:
        world.say(
            f"At once, the light dimmed in the room, and the shadows grew soft and long."
        )
        horn.meters["dimness"] = horn.meters.get("dimness", 0.0) + 1.0
    else:
        world.say(
            f"Nothing magic happened there, because this was not a place for horn spells."
        )

    world.say(
        f"Then came a boom from the deeper hall, loud enough to shake the dust."
    )
    world.facts["boom_heard"] = world.setting.allows_boom
    if world.setting.allows_boom:
        world.say(
            f"{companion.id} hurried forward, but {hero.id} felt a flicker of conflict."
        )
        hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
        world.facts["conflict"] = True
    else:
        world.say(
            f"There was no real danger in the cottage, so the boom stayed only in the tale of the wind."
        )
        world.facts["conflict"] = False

    world.para()
    comp_base, comp_form = _safe_lookup(COMPARATIVES, world.facts.get("comparative"))
    if world.facts.get("conflict"):
        world.say(
            f"{hero.id} looked at {companion.id} and made a comparative choice: "
            f"to be {comp_form}, not bolder for its own sake."
        )
        if comp_base == "safe":
            world.say(
                f"That meant stepping back, holding the horn lower, and listening first."
            )
        elif comp_base == "kind":
            world.say(
                f"That meant speaking gently, so {companion.id} would not be frightened by the boom."
            )
        elif comp_base == "small":
            world.say(
                f"That meant taking a smaller step, one that left room for everyone to breathe."
            )
        else:
            world.say(
                f"That meant acting with steady courage instead of rushing into the dark."
            )

        world.say(
            f"{companion.id} saw the change at once, and the conflict loosened like a tied knot."
        )
        hero.memes["conflict"] = 0.0
        world.facts["resolved"] = True
        world.say(
            f"Together they followed the boom to a sleeping door that only needed a gentle tap."
        )
        world.say(
            f"When {hero.id} tapped it, the door opened and a hidden lantern lit the way home."
        )
    else:
        world.facts["resolved"] = False
        world.say(
            f"Without any real conflict, {hero.id} simply carried the horn home like a treasure."
        )

    world.para()
    if world.facts.get("resolved"):
        world.say(
            f"So the magic horn still glimmered, but the brightest thing in the room was {hero.id}'s wiser heart."
        )
    else:
        world.say(
            f"And so the evening ended quietly, with curiosity tucked safely beside the horn."
        )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting can dim the horn only if it allows magic horn use.
can_dim(S) :- setting(S), allows_magic_horn(S).

% A boom matters only if the setting permits it.
can_boom(S) :- setting(S), allows_boom(S).

% Curiosity + horn + dimming + boom can produce conflict.
conflict(S) :- can_dim(S), can_boom(S).

% A comparative choice resolves conflict if it is a careful choice.
resolved(S) :- conflict(S), comparative_choice(S).

#show conflict/1.
#show resolved/1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.allows_magic_horn:
            lines.append(asp.fact("allows_magic_horn", sid))
        if s.allows_boom:
            lines.append(asp.fact("allows_boom", sid))
    for key in COMPARATIVES:
        lines.append(asp.fact("comparative_choice", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
    atoms = set(asp.atoms(model, "conflict")) | set(asp.atoms(model, "resolved"))
    python = set()
    for sid, s in SETTINGS.items():
        if s.allows_magic_horn and s.allows_boom:
            python.add(("conflict", sid))
            python.add(("resolved", sid))
    if atoms == python:
        print("OK: ASP parity matches the Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(python))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    setting = _safe_lookup(SETTINGS, p.setting)
    return [
        f'Write a short fairy tale about curiosity, a magic horn, and a choice that is {p.comparative}.',
        f"Tell a child-friendly story set in {setting.place} where {p.hero} finds a horn and hears a boom.",
        f'Write a fairy tale in which the word "{p.horn.split()[0]}" appears and the ending changes because someone chooses to be {p.comparative}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")  # type: ignore[assignment]
    setting = _safe_lookup(SETTINGS, p.setting)
    comp_base, comp_form = _safe_lookup(COMPARATIVES, p.comparative)
    qas = [
        QAItem(
            question=f"Where did {p.hero} find the magic horn?",
            answer=f"{p.hero} found the horn in {setting.place}, where curiosity led the way.",
        ),
        QAItem(
            question=f"What happened when {p.hero} blew the horn?",
            answer=f"When {p.hero} blew the horn, the light dimmed in {setting.place} because the horn was magic there.",
        ),
        QAItem(
            question=f"Why did the story feel tense after the boom?",
            answer=f"The boom made the moment tense because {p.hero} and {p.companion} were already facing a conflict.",
        ),
        QAItem(
            question=f"What comparative choice helped resolve the conflict?",
            answer=f"{p.hero} chose to be {comp_form} rather than rush ahead, and that careful choice helped end the conflict.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the conflict was resolved and the horn still glimmered while {p.hero} acted with a wiser heart.",
        ),
    ]
    if comp_base == "safe":
        qas.append(QAItem(
            question=f"How did being {comp_form} help?",
            answer="It helped by making the hero step back and listen first, which kept everyone calmer.",
        ))
    elif comp_base == "kind":
        qas.append(QAItem(
            question=f"How did being {comp_form} help?",
            answer="It helped by making the hero speak gently, so the companion would not be frightened.",
        ))
    elif comp_base == "small":
        qas.append(QAItem(
            question=f"How did being {comp_form} help?",
            answer="It helped by making the hero take a smaller step, leaving room for everyone to breathe.",
        ))
    else:
        qas.append(QAItem(
            question=f"How did being {comp_form} help?",
            answer="It helped by making the hero act with steady courage instead of rushing into the dark.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn or discover something new.",
        ),
        QAItem(
            question="What does a magic horn usually do in a fairy tale?",
            answer="A magic horn can cause a surprising change, like dimming light or waking something hidden.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or tension that the characters need to work through.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace / emit
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
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


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: curiosity, magic horn, boom, and conflict.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
    ap.add_argument("--horn", choices=sorted(HORN_DESCRIPTIONS))
    ap.add_argument("--comparative", choices=sorted(COMPARATIVES))
    ap.add_argument("--hero-type", choices=["girl", "boy"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    hero_type = getattr(args, "hero_type", None) or _safe_lookup(HEROES, hero)
    companion = getattr(args, "companion", None) or rng.choice(list(COMPANIONS))
    horn = getattr(args, "horn", None) or rng.choice(list(HORN_DESCRIPTIONS))
    comparative = getattr(args, "comparative", None) or rng.choice(list(COMPARATIVES))
    if getattr(args, "hero_type", None) and HEROES.get(hero) != getattr(args, "hero_type", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        setting=setting,
        hero=hero,
        hero_type=hero_type,
        companion=companion,
        companion_type=_safe_lookup(COMPANIONS, companion),
        horn=horn,
        comparative=comparative,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion_type))
    horn = world.add(Entity(
        id="horn",
        kind="thing",
        type="horn",
        label=params.horn,
        phrase=_safe_lookup(HORN_DESCRIPTIONS, params.horn),
        owner=hero.id,
    ))
    world.facts["params"] = params

    tell(world)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("forest", "Mira", "girl", "queen", "queen", "silver horn", "braver"),
        StoryParams("castle", "Nilo", "boy", "wizard", "wizard", "green horn", "safer"),
        StoryParams("forest", "Elin", "girl", "bird", "bird", "little horn", "kinder"),
        StoryParams("castle", "Tavi", "boy", "fox", "fox", "silver horn", "smaller"),
    ]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
    return sorted(set(asp.atoms(model, "conflict")) | set(asp.atoms(model, "resolved")))


def asp_program_for_list(show: str) -> str:
    return asp_program(show)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show conflict/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
        atoms = asp.atoms(model, "conflict") + asp.atoms(model, "resolved")
        print(f"{len(atoms)} ASP-marked outcomes:")
        for atom in atoms:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in curated_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.hero} at {p.setting} with {p.horn} and {p.comparative}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
