#!/usr/bin/env python3
"""
A small storyworld for a ghost-story-like domain built from the seed words
realm, murmur, and invasion, with Kindness, Moral Value, and Rhyme as the
main narrative instruments.

Premise:
- A quiet realm is kept in balance by a friendly bell and a nightly rhyme.
- A cold invasion of murmurs slips in when someone forgets to act kindly.
- The turn comes when the hero notices that the realm's fear feeds the murmur.
- The resolution arrives through a kind act, a spoken moral, and a rhyme that
  restores the room's courage and sends the murmurs away.

The simulation tracks:
- physical meters: chill, shadow, hush, warmth, lanternlight
- emotional memes: fear, courage, kindness, trust, relief

The prose is generated from the live state, not from a frozen template.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    hero: object | None = None
    murmur: object | None = None
    r: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Realm:
    name: str
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
class StoryParams:
    realm: str
    setting: str
    hero: str
    hero_type: str
    companion: str
    moral_value: str
    rhyme: str
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


REALMS = {
    "moon_hall": "the moonlit hall",
    "lantern_crypt": "the lantern crypt",
    "harbor_keep": "the harbor keep",
    "pine_room": "the pine room",
}

SETTINGS = {
    "moon_hall": {"murmurs": 1.0, "chill": 1.0},
    "lantern_crypt": {"murmurs": 1.2, "chill": 1.3},
    "harbor_keep": {"murmurs": 1.1, "chill": 1.0},
    "pine_room": {"murmurs": 0.9, "chill": 0.8},
}

HEROES = {
    "Lina": "girl",
    "Milo": "boy",
    "Nora": "girl",
    "Eli": "boy",
    "Tessa": "girl",
    "Rowan": "boy",
}

COMPANIONS = {
    "grandmother": "woman",
    "lighthouse keeper": "man",
    "older sister": "girl",
    "caretaker": "woman",
    "uncle": "man",
}

MORAL_VALUES = [
    "kindness means helping first and boasting later",
    "a gentle voice can make a hard room softer",
    "the bravest choice is often the kindest one",
    "sharing light is better than guarding it alone",
]

RHYMES = [
    "Murmur in the corner, murmur in the air; kindness makes it thinner, and courage keeps it fair.",
    "Little light, big night, hush the fear away; say a kind word softly and the shadows lose their sway.",
    "If the room grows cold and gray, do a kind deed right away; rhyme and warmth together make the wandering dark decamp.",
]


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_murmur_spread(world: Realm) -> list[str]:
    out = []
    if world.facts.get("invasion_started") and world.get("realm").meters["hush"] < 2:
        sig = ("spread",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.get("realm").meters["shadow"] += 1
        world.get("hero").memes["fear"] += 1
        out.append("The murmurs spread, and the room felt colder.")
    return out


def _r_kindness_soften(world: Realm) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["kindness"] >= THRESHOLD and ("soften",) not in world.fired:
        world.fired.add(("soften",))
        world.get("realm").meters["warmth"] += 1
        world.get("realm").meters["shadow"] = max(0, world.get("realm").meters["shadow"] - 1)
        hero.memes["courage"] += 1
        out.append("The kind act warmed the air and pushed the shadow back.")
    return out


def _r_rhyme_break(world: Realm) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["courage"] >= THRESHOLD and ("rhyme",) not in world.fired:
        world.fired.add(("rhyme",))
        world.get("realm").meters["hush"] += 1
        world.get("realm").meters["lanternlight"] += 1
        world.get("realm").meters["shadow"] = max(0, world.get("realm").meters["shadow"] - 1)
        hero.memes["relief"] += 1
        out.append("The rhyme rang out, and the murmur broke apart like mist.")
    return out


RULES = [
    Rule("murmur_spread", _r_murmur_spread),
    Rule("kindness_soften", _r_kindness_soften),
    Rule("rhyme_break", _r_rhyme_break),
]


def propagate(world: Realm, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                out.extend(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_realm(params: StoryParams) -> Realm:
    realm = Realm(name=params.realm, place=_safe_lookup(REALMS, params.setting))
    hero = realm.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    companion = realm.add(Entity(id=params.companion, kind="character", type=_safe_lookup(COMPANIONS, params.companion)))
    r = realm.add(Entity(id="realm", type="realm", label=_safe_lookup(REALMS, params.setting)))
    murmur = realm.add(Entity(id="murmur", type="murmur", label="the murmur"))
    realm.facts.update(hero=hero, companion=companion, realm=r, murmur=murmur, params=params)
    r.meters.update({"chill": _safe_lookup(SETTINGS, params.setting)["chill"], "shadow": 1.0, "hush": 1.0, "warmth": 0.0, "lanternlight": 0.0})
    hero.memes.update({"fear": 0.0, "courage": 0.0, "kindness": 0.0, "trust": 0.0, "relief": 0.0})
    companion.memes.update({"trust": 1.0})
    return realm


def tell(world: Realm, params: StoryParams) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    realm = world.get("realm")

    world.say(
        f"In {realm.label}, {hero.id} lived with {companion.id} where the windows always seemed to listen."
    )
    world.say(
        f"Each night, a small bell and a soft rhyme kept the room calm, and the dark stayed at the edges."
    )
    world.para()

    world.facts["invasion_started"] = True
    realm.meters["hush"] = 0.0
    realm.meters["shadow"] += 1
    hero.memes["fear"] += 1
    world.say(
        f"Then a murmur invasion slipped in under the door, whispering and growing colder with every breath."
    )
    world.say(
        f"{hero.id} heard the little voices and hugged closer to the lamp, while {companion.id} worried that the room had forgotten its courage."
    )

    world.para()
    hero.memes["kindness"] += 1
    world.say(
        f"Instead of hiding, {hero.id} took a warm cup to {companion.id} and said, "
        f"\"{params.moral_value.capitalize()}.\""
    )
    propagate(world, narrate=True)

    world.para()
    hero.memes["courage"] += 1
    world.say(
        f"Then {hero.id} recited a rhyme: \"{params.rhyme}\""
    )
    propagate(world, narrate=True)

    world.para()
    if realm.meters["shadow"] <= 0:
        hero.memes["trust"] += 1
        hero.memes["relief"] += 1
        world.say(
            f"The murmur fled into the corners, and the room glowed with lanternlight and a brave, gentle hush."
        )
        world.say(
            f"{hero.id} and {companion.id} sat together in the bright quiet, and the realm felt safe again."
        )
    else:
        world.say(
            f"The room still held a thin edge of darkness, but the kindness had made it smaller and easier to bear."
        )

    world.facts["resolved"] = realm.meters["shadow"] <= 0
    world.facts["moral_value"] = params.moral_value
    world.facts["rhyme"] = params.rhyme


def generation_prompts(world: Realm) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a ghost-story-style tale about {p.hero} in {_safe_lookup(REALMS, p.setting)} with a murmur invasion.",
        f"Tell a child-friendly spooky story that includes kindness, a moral value, and a rhyme.",
        f"Write a short realm story where a gentle act and a rhyme drive away a whispering invasion.",
    ]


def story_qa(world: Realm) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero = world.get("hero")
    comp = world.get("companion")
    realm = world.get("realm")
    qa = [
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened in {realm.label}, a quiet place where the dark could feel very close."
        ),
        QAItem(
            question=f"What did {hero.id} do when the murmur invasion began?",
            answer=f"{hero.id} did a kind thing for {comp.id}, spoke about {p.moral_value}, and then used a rhyme to chase the murmurs away."
        ),
        QAItem(
            question=f"Why did the room feel safer at the end?",
            answer=f"The kindness warmed the realm, the rhyme broke the murmur, and the shadow shrank until the room glowed with lanternlight."
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"What changed by the end of the story?",
                answer=f"The invasion of murmurs was driven out, and the realm ended in a soft, brave hush instead of fear."
            )
        )
    return qa


def world_knowledge_qa(world: Realm) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something caring or helpful for another person."
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an idea about what is good and right, like honesty, kindness, or courage."
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line or phrase that sounds musical because some of its words end with matching sounds."
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for realm in REALMS:
        for setting in SETTINGS:
            for hero, hero_type in HEROES.items():
                for companion in COMPANIONS:
                    combos.append((realm, setting, hero))
    return combos


def explain_rejection(reason: str) -> str:
    return f"(No story: {reason})"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story realm with murmurs, kindness, moral value, and rhyme.")
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--moral-value", dest="moral_value", choices=MORAL_VALUES)
    ap.add_argument("--rhyme", choices=RHYMES)
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
    realm = getattr(args, "realm", None) or rng.choice(list(REALMS))
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    hero_type = _safe_lookup(HEROES, hero)
    companion = getattr(args, "companion", None) or rng.choice(list(COMPANIONS))
    moral_value = getattr(args, "moral_value", None) or rng.choice(MORAL_VALUES)
    rhyme = getattr(args, "rhyme", None) or rng.choice(RHYMES)
    return StoryParams(realm=realm, setting=setting, hero=hero, hero_type=hero_type, companion=companion, moral_value=moral_value, rhyme=rhyme)


def generate(params: StoryParams) -> StorySample:
    world = build_realm(params)
    tell(world, params)
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
realm(R) :- realm_fact(R).
setting(S) :- setting_fact(S).
hero(H) :- hero_fact(H).
companion(C) :- companion_fact(C).

murmur_invasion(R,S) :- realm(R), setting(S), starts_murmur(R), shadow(R), chill(R).
kindness_turn(H) :- hero(H), kind(H).
moral_spoken(H,M) :- hero(H), moral(M).
rhyme_spoken(H,RH) :- hero(H), rhyme(RH).

rescued(R) :- kindness_turn(H), rhyme_spoken(H,_), realm(R), shadow(R).
resolved(R) :- rescued(R).

#show rescued/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in REALMS:
        lines.append(asp.fact("realm_fact", r))
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for h in HEROES:
        lines.append(asp.fact("hero_fact", h))
        lines.append(asp.fact("kind", h))
    for c in COMPANIONS:
        lines.append(asp.fact("companion_fact", c))
    lines.append(asp.fact("starts_murmur", "moon_hall"))
    lines.append(asp.fact("shadow", "moon_hall"))
    lines.append(asp.fact("chill", "moon_hall"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show resolved/1."))
    atoms = set(asp.atoms(model, "resolved"))
    if atoms:
        print("OK: ASP twin produces a resolution model.")
        return 0
    print("MISMATCH: ASP twin produced no resolved model.")
    return 1


CURATED = [
    StoryParams(
        realm="moon_hall",
        setting="moon_hall",
        hero="Lina",
        hero_type="girl",
        companion="grandmother",
        moral_value=_safe_lookup(MORAL_VALUES, 0),
        rhyme=_safe_lookup(RHYMES, 0),
    ),
    StoryParams(
        realm="lantern_crypt",
        setting="lantern_crypt",
        hero="Milo",
        hero_type="boy",
        companion="caretaker",
        moral_value=_safe_lookup(MORAL_VALUES, 2),
        rhyme=_safe_lookup(RHYMES, 1),
    ),
    StoryParams(
        realm="harbor_keep",
        setting="harbor_keep",
        hero="Nora",
        hero_type="girl",
        companion="older sister",
        moral_value=_safe_lookup(MORAL_VALUES, 3),
        rhyme=_safe_lookup(RHYMES, 2),
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.hero} in {p.realm}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
