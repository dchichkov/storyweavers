#!/usr/bin/env python3
"""
storyworlds/worlds/astrology_invite_bank_misunderstanding_myth.py
=================================================================

A small myth-style story world about an astrology invite, a bank, and a
misunderstanding that turns on what the word "bank" means.

Seed tale:
---
In an old village under bright stars, a young listener named Mira loved
watching the sky with her grandmother. One evening, the royal astrologer sent
an invite to the bank for the moon reading. Mira read the word "bank" and
thought of the riverbank, where reeds bent in the wind and boats bumped softly
against the mud.

Mira hurried to the riverbank with a small basket and a cloak, but no one from
the palace was there. Her grandmother came after her and laughed kindly. "Not
that bank," she said. "The astrologer invited us to the stone bank, where the
village keeps its grain and counts the stars above it."

So Mira followed her grandmother to the stone bank. There, beneath the
constellations, the astrologer welcomed them inside. Mira learned that an invite
can be easy to misread when one word has two paths. By the end of the night,
she understood the stars, the bank, and the laugh of a mistake that had become
a lesson.

World model notes:
---
- The hero carries a social "confusion" meme when the invite is misread.
- The misunderstanding increases desire to act on the wrong meaning.
- A clarifying helper reduces confusion and resolves the invite.
- The final image must show both the corrected destination and the learned
  meaning in the world state.
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
    caregiver: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self):
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "queen", "priestess"}
        male = {"boy", "father", "grandfather", "man", "king", "priest"}
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
    sky: str
    places: set[str] = field(default_factory=set)
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
class Invite:
    id: str
    sender: str
    destination: str
    phrase: str
    keyword: str = "invite"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    invite: str
    bank: str
    hero_name: str
    hero_type: str
    helper_type: str
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
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "moon_village": Setting(
        place="the moonlit village",
        sky="the bright night sky",
        places={"river_bank", "stone_bank", "observatory"},
    )
}

INVITES = {
    "moon_reading": Invite(
        id="moon_reading",
        sender="the astrologer",
        destination="stone_bank",
        phrase="an invite to the bank for the moon reading",
    ),
    "star_counting": Invite(
        id="star_counting",
        sender="the village keeper",
        destination="observatory",
        phrase="an invite to the bank for the star counting",
    ),
}

BANKS = {
    "river_bank": {"label": "river bank", "kind": "river"},
    "stone_bank": {"label": "stone bank", "kind": "granary"},
}

GIRL_NAMES = ["Mira", "Nila", "Suri", "Asha", "Luna", "Tara"]
BOY_NAMES = ["Arun", "Kavi", "Niko", "Ravi", "Soren", "Timo"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, i, b) for s in SETTINGS for i in INVITES for b in BANKS]


def explain_rejection(invite_id: str, bank_id: str) -> str:
    inv = _safe_lookup(INVITES, invite_id)
    bank = _safe_lookup(BANKS, bank_id)["label"]
    return f"(No story: {inv.phrase} does not reasonably point to the {bank} in this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "invite", None) and getattr(args, "bank", None) and (getattr(args, "invite", None), getattr(args, "bank", None)) not in [(i, b) for _, i, b in valid_combos()]:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "invite", None) is None or c[1] == getattr(args, "invite", None))
              and (getattr(args, "bank", None) is None or c[2] == getattr(args, "bank", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, invite, bank = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = getattr(args, "helper", None) or "grandmother"
    hero_type = "girl" if gender == "girl" else "boy"
    return StoryParams(setting=setting, invite=invite, bank=bank, hero_name=hero_name, hero_type=hero_type, helper_type=helper_type)


def story_setup(world: World, hero: Entity, helper: Entity, inv: Invite, bank_id: str) -> None:
    world.say(
        f"In {world.setting.place}, under {world.setting.sky}, {hero.id} loved watching the stars with {helper.label}."
    )
    world.say(
        f"One evening, {inv.sender} sent {hero.id} {inv.phrase}."
    )
    world.say(
        f"{hero.id} read the word bank and thought of the {BANKS['river_bank']['label']}, where water licked the mud and reeds nodded."
    )
    hero.memes["curiosity"] += 1
    hero.memes["confusion"] += 1
    hero.memes["desire"] += 1
    world.facts["misread_bank"] = "river_bank"
    world.facts["true_bank"] = bank_id


def story_misunderstanding(world: World, hero: Entity, helper: Entity, inv: Invite, bank_id: str) -> None:
    wrong = BANKS["river_bank"]["label"]
    world.para()
    world.say(
        f"{hero.id} hurried to the {wrong} with a small basket and a cloak, sure the palace stars must be waiting there."
    )
    world.say(
        f"But no astrologer stood by the water. The only answer was the wind and a boat bumping softly against the shore."
    )
    hero.memes["confusion"] += 1
    hero.meters["distance"] = world.facts.get("distance_to_wrong_bank", 1) + 1
    helper.memes["concern"] += 1


def clarify(world: World, hero: Entity, helper: Entity, inv: Invite, bank_id: str) -> None:
    world.para()
    world.say(
        f"{helper.label} came after {hero.id} and laughed kindly. \"Not that bank,\" {helper.pronoun()} said. "
        f"\"The astrologer invited us to the {_safe_lookup(BANKS, bank_id)['label']}, where the village keeps its grain and reads the stars above it.\""
    )
    hero.memes["confusion"] -= 1
    hero.memes["understanding"] += 1
    world.facts["clarified"] = True


def attend(world: World, hero: Entity, helper: Entity, inv: Invite, bank_id: str) -> None:
    world.para()
    hero.location = bank_id
    helper.location = bank_id
    world.say(
        f"So {hero.id} followed {helper.label} to the {_safe_lookup(BANKS, bank_id)['label']}. Beneath the constellations, {inv.sender} welcomed them inside."
    )
    world.say(
        f"{hero.id} learned that one word can point to two places, and a careful question can find the right path."
    )
    world.say(
        f"By the end of the night, {hero.id} was smiling at the sky from the {_safe_lookup(BANKS, bank_id)['label']}, and the mistake had turned into wisdom."
    )
    hero.memes["joy"] += 1
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 1)
    world.facts["resolved"] = True


def tell(setting: Setting, invite: Invite, bank_id: str, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_type))
    world.add(Entity(id="invite", type="invite", label="invite", phrase=invite.phrase, owner=hero.id))
    world.add(Entity(id=bank_id, type="place", label=_safe_lookup(BANKS, bank_id)["label"]))

    story_setup(world, hero, helper, invite, bank_id)
    story_misunderstanding(world, hero, helper, invite, bank_id)
    clarify(world, hero, helper, invite, bank_id)
    attend(world, hero, helper, invite, bank_id)

    world.facts.update(hero=hero, helper=helper, invite=invite, bank_id=bank_id)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    invite = _safe_fact(world, f, "invite")
    bank_label = BANKS[f["bank_id"]]["label"]
    return [
        f'Write a short myth-like story for a young child about astrology, an invite, and a bank.',
        f"Tell a gentle story where {hero.id} misreads {invite.phrase} and thinks of the wrong {bank_label}.",
        f'Write a story about a misunderstanding that begins with the word "bank" and ends under the stars.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    bank_label = BANKS[f["bank_id"]]["label"]
    invite = _safe_fact(world, f, "invite")
    return [
        QAItem(
            question=f"Why did {hero.id} go to the {BANKS['river_bank']['label']} at first?",
            answer=f"{hero.id} thought the invite meant the {BANKS['river_bank']['label']}, because the word bank sounded like the riverbank.",
        ),
        QAItem(
            question=f"Who explained the misunderstanding to {hero.id}?",
            answer=f"{helper.label} explained that the invite was really for the {bank_label}.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end of the story?",
            answer=f"{hero.id} learned that {invite.phrase} meant a visit to the {bank_label}, not the riverbank.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is astrology?",
            answer="Astrology is the old practice of watching the stars and planets and giving them meanings for people on earth.",
        ),
        QAItem(
            question="What is an invite?",
            answer="An invite is a message that asks someone to come to an event or place.",
        ),
        QAItem(
            question="What is a bank?",
            answer="A bank can mean a place where people keep money, but it can also mean the side of a river.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.places):
            lines.append(asp.fact("place_in_setting", sid, p))
    for iid, inv in INVITES.items():
        lines.append(asp.fact("invite", iid))
        lines.append(asp.fact("invite_destination", iid, inv.destination))
    for bid, b in BANKS.items():
        lines.append(asp.fact("bank", bid))
        lines.append(asp.fact("bank_kind", bid, b["kind"]))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when an invite can point to a bank and the hero can
% misunderstand bank as the river bank before the helper clarifies it.
invite_targets(I, B) :- invite(I), invite_destination(I, B).
wrong_bank(B) :- bank(B), bank_kind(B, river).
right_bank(B) :- bank(B), bank_kind(B, granary).

misunderstanding(I) :- invite_targets(I, B), wrong_bank(W), B != W.
clarified(I) :- invite_targets(I, B), right_bank(B).
valid_story(S, I, B) :- setting(S), invite(I), bank(B), invite_targets(I, B), clarified(I), misunderstanding(I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth story world: astrology, invite, bank, and misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--invite", choices=INVITES)
    ap.add_argument("--bank", choices=BANKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(INVITES, params.invite), params.bank, params.hero_name, params.hero_type, params.helper_type)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = {(s, i, b) for s, i, b in valid_combos()}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(setting="moon_village", invite="moon_reading", bank="stone_bank", hero_name="Mira", hero_type="girl", helper_type="grandmother"),
    StoryParams(setting="moon_village", invite="moon_reading", bank="river_bank", hero_name="Arun", hero_type="boy", helper_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print("  ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
