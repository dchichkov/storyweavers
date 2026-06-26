#!/usr/bin/env python3
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    relic_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "witch", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "knight", "father"}:
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
    tone: str
    affords: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    kind: str
    region: str
    guards: set[str] = field(default_factory=set)
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
class Threat:
    id: str
    label: str
    kind: str
    mess: str
    zone: set[str]
    risk: str
    turns: int
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
    place: str
    threat: str
    relic: str
    hero_name: str
    hero_type: str
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
        self.repetition: int = 0

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
        w.facts = dict(self.facts)
        w.repetition = self.repetition
        return w


SETTINGS = {
    "wood": Setting("the wood", "old", {"crumbs", "mist", "spells"}),
    "castle": Setting("the castle garden", "grand", {"crumbs", "spells"}),
    "hollow": Setting("the mossy hollow", "quiet", {"mist", "crumbs"}),
}

THREATS = {
    "crumbs": Threat(
        id="crumbs", label="crumbs in the path", kind="crumbs",
        mess="crumbled", zone={"ground"}, risk="the road to the tower could be broken",
        turns=3,
    ),
    "mist": Threat(
        id="mist", label="mist at dusk", kind="mist",
        mess="fogged", zone={"air"}, risk="the lantern could vanish from sight",
        turns=2,
    ),
    "spells": Threat(
        id="spells", label="sleepy spells", kind="spells",
        mess="drowsed", zone={"heart"}, risk="the hero might give up too soon",
        turns=4,
    ),
}

RELICS = {
    "breast_fleck": Relic(
        id="breast_fleck", label="breast fleck", phrase="a tiny breast fleck",
        kind="breast fleck", region="breast", guards={"spells"},
    ),
    "nugget": Relic(
        id="nugget", label="gold nugget", phrase="a warm gold nugget",
        kind="nugget", region="pocket", guards={"crumbs", "mist"},
    ),
    "lantern_chip": Relic(
        id="lantern_chip", label="lantern chip", phrase="a bright lantern chip",
        kind="chip", region="hand", guards={"mist"},
    ),
}

HERO_TYPES = ["girl", "boy"]
NAMES = ["Mira", "Lenn", "Tessa", "Pip", "Rowan", "Elin"]
TRAITS = ["brave", "gentle", "small", "curious"]


def can_handle(threat: Threat, relic: Relic) -> bool:
    return threat.kind in relic.guards


ASP_RULES = r"""
threat(T) :- threat_id(T).
relic(R) :- relic_id(R).
guards(R,T) :- guards_id(R,T).
possible(T,R) :- threat(T), relic(R), guards(R,T).
#show possible/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat_id", tid))
        for z in sorted(t.zone):
            lines.append(asp.fact("zone", tid, z))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic_id", rid))
        lines.append(asp.fact("region", rid, r.region))
        for g in sorted(r.guards):
            lines.append(asp.fact("guards_id", rid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for t, threat in THREATS.items():
            for r, relic in RELICS.items():
                if threat.kind in relic.guards:
                    combos.append((p, t, r))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show possible/2."))
    return sorted(set(asp.atoms(model, "possible")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set((t, r) for _, t, r in valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} pairs).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world with bravery, repetition, and a bad ending that can be turned aside.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "threat", None) is None or c[1] == getattr(args, "threat", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, threat, relic = (list(rng.choice(combos)) + [None, None, None])[:3]
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, threat=threat, relic=relic, hero_name=name, hero_type=hero_type)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    threat = _safe_lookup(THREATS, params.threat)
    relic = _safe_lookup(RELICS, params.relic)
    relic_ent = world.add(Entity(id="relic", type=relic.kind, label=relic.label, phrase=relic.phrase))
    hero.memes["bravery"] = 0
    world.facts.update(hero=hero, threat=threat, relic=relic_ent, params=params)

    world.say(f"Once in {world.setting.place}, there lived a little {hero.type} named {hero.id}.")
    world.say(f"{hero.id} found {relic.phrase}, and the treasure glimmered like a promise.")
    world.para()
    world.say(f"Each night, {threat.label} came again and again, and again it came, and again.")
    world.say(f"The same bad ending waited for anyone who would not try: {threat.risk}.")
    world.para()
    hero.memes["bravery"] += 1
    if params.threat == "spells":
        world.say(f"But {hero.id} touched the tiny breast fleck to {hero.pronoun('possessive')} breast and held still.")
        world.say("The fleck warmed like a candle under cloth, and the sleepy spell thinned.")
    elif params.threat == "crumbs":
        world.say(f"But {hero.id} tucked the gold nugget into {hero.pronoun('possessive')} hand and marched on.")
        world.say("The nugget tapped like a drumbeat, and the broken path became a steady road.")
    else:
        world.say(f"But {hero.id} lifted the lantern chip and walked through the mist.")
        world.say("The bright chip cut a little road of light, and the fog moved aside.")
    world.say(f"{hero.id} kept going, even when the warning tried to return.")
    world.para()
    world.say(f"At last, the danger did not win.")
    if params.relic == "breast_fleck":
        ending = f"The small breast fleck rested on {hero.id}'s breast, shining softly like a brave star."
    elif params.relic == "nugget":
        ending = f"The gold nugget stayed warm in {hero.id}'s pocket, and the wood felt safe enough to sing."
    else:
        ending = f"The lantern chip gleamed in {hero.id}'s hand, and the path looked friendly at last."
    world.say(ending)
    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a fairy tale about a child named {params.name} who finds a {relic.label} in {world.setting.place}.",
            f"Tell a story with bravery, a repeating danger, and a turning point involving {relic.kind}.",
            f"Make the words breast, nugget, and fleck feel natural in a magical tale.",
        ],
        story_qa=[
            QAItem(question=f"What did {params.name} find?", answer=f"{params.name} found {relic.phrase}."),
            QAItem(question=f"What kept happening again and again?", answer=f"{threat.label} kept coming back, which made the tale repeat like a warning."),
            QAItem(question=f"What helped {params.name} be brave?", answer=f"{relic.phrase} helped {params.name} stand up to the danger."),
        ],
        world_qa=[
            QAItem(question="What does bravery mean in a fairy tale?", answer="Bravery means doing the hard thing even when you feel scared."),
            QAItem(question="Why can repetition matter in a story?", answer="Repetition can make a warning feel stronger and help the listener notice a pattern."),
            QAItem(question="What is a nugget?", answer="A nugget is a small lump of something valuable, often gold."),
            QAItem(question="What is a fleck?", answer="A fleck is a tiny little speck or spot."),
            QAItem(question="What is a breast on a bird?", answer="A breast is the front part of a bird's body, between the neck and the belly."),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"repetition={world.repetition}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="wood", threat="spells", relic="breast_fleck", hero_name="Mira", hero_type="girl"),
    StoryParams(place="castle", threat="crumbs", relic="nugget", hero_name="Pip", hero_type="boy"),
    StoryParams(place="hollow", threat="mist", relic="lantern_chip", hero_name="Tessa", hero_type="girl"),
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
        print(asp_program("#show possible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible pairs:\n")
        for t, r in pairs:
            print(f"  {t:8} {r:14}")
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            params.seed = base_seed + i
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
