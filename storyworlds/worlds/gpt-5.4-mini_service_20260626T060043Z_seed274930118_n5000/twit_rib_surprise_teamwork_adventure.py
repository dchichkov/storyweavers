#!/usr/bin/env python3
"""
storyworlds/worlds/twit_rib_surprise_teamwork_adventure.py
==========================================================

A small adventure storyworld about a surprise on the trail and the teamwork
needed to get through it.

Seed tale shape:
- Two little travelers head out with a plan.
- A surprise blocks the way.
- They share a job, solve the problem together, and find something new at the
  end of the path.

This world keeps the prose child-facing and concrete, while the simulated state
tracks both physical meters and emotional memes.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carrier: Optional[str] = None
    supportive: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    rib: object | None = None
    tool: object | None = None
    twit: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    outdoor: bool = True
    trail: str = "trail"
    SETTING: object | None = None
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
class Challenge:
    id: str
    verb: str
    gerund: str
    surprise: str
    obstacle: str
    method: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
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
class Aid:
    id: str
    label: str
    phrase: str
    solves: set[str]
    help_line: str
    tail: str
    plural: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.surprise_seen: bool = False
        self.helper_used: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.surprise_seen = self.surprise_seen
        clone.helper_used = self.helper_used
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _score(e: Entity, key: str) -> float:
    return float(e.meters.get(key, 0.0))


def _mem(e: Entity, key: str) -> float:
    return float(e.memes.get(key, 0.0))


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (rule_surprise, rule_teamwork, rule_ending):
            sents = fn(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def rule_surprise(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if _mem(hero, "alert") < 1:
            continue
        if world.surprise_seen:
            continue
        world.surprise_seen = True
        hero.memes["wonder"] = _mem(hero, "wonder") + 1
        hero.memes["worry"] = _mem(hero, "worry") + 1
        out.append(f"Something unexpected popped up on the trail.")
    return out


def rule_teamwork(world: World) -> list[str]:
    out: list[str] = []
    twit = world.get("Twit")
    rib = world.get("Rib")
    if _score(twit, "stuck") >= 1 and _score(rib, "support") >= 1 and not world.helper_used:
        world.helper_used = True
        twit.memes["worry"] = max(0.0, _mem(twit, "worry") - 1)
        twit.memes["trust"] = _mem(twit, "trust") + 1
        rib.memes["pride"] = _mem(rib, "pride") + 1
        out.append("Twit and Rib worked together and the problem began to give way.")
    return out


def rule_ending(world: World) -> list[str]:
    out: list[str] = []
    twit = world.get("Twit")
    if _score(twit, "reached") >= 1 and world.helper_used and ("final",) not in world.fired:
        world.fired.add(("final",))
        out.append("At the end, the trail opened onto a bright new place.")
    return out


SETTING = Setting(place="the winding hill trail", outdoor=True, trail="hill trail")

CHALLENGES = {
    "surprise_bridge": Challenge(
        id="surprise_bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        surprise="a tiny bridge was there, but it swayed in the wind",
        obstacle="the bridge was too wobbly to trust alone",
        method="one held the rope while the other stepped carefully",
        ending_image="the bridge stood still long enough for both travelers to cross",
        tags={"bridge", "surprise", "teamwork"},
    ),
    "surprise_stream": Challenge(
        id="surprise_stream",
        verb="reach the far bank",
        gerund="reaching the far bank",
        surprise="a stream glittered across the path where there had only been dry dirt before",
        obstacle="the stones were slippery and the water ran fast",
        method="one found stepping stones while the other watched each step",
        ending_image="the stepping stones made a safe line across the water",
        tags={"stream", "surprise", "teamwork"},
    ),
    "surprise_gate": Challenge(
        id="surprise_gate",
        verb="enter the grove",
        gerund="entering the grove",
        surprise="a small gate was stuck shut behind a tangle of vines",
        obstacle="the gate would not open by pulling alone",
        method="one cleared the vines while the other pushed the latch",
        ending_image="the gate swung open to a secret sunny grove",
        tags={"gate", "surprise", "teamwork"},
    ),
}

AIDS = {
    "rope": Aid(
        id="rope",
        label="a rope",
        phrase="a long rope with a red knot",
        solves={"surprise_bridge"},
        help_line="Rib tied the rope to a rock so the bridge would not sway so much.",
        tail="Then the rope kept the bridge steady.",
    ),
    "stones": Aid(
        id="stones",
        label="flat stones",
        phrase="a pouch of flat stones",
        solves={"surprise_stream"},
        help_line="Twit laid the stones across the water one by one.",
        tail="Then the stones made a safe path.",
    ),
    "stick": Aid(
        id="stick",
        label="a strong stick",
        phrase="a strong stick with a smooth handle",
        solves={"surprise_gate"},
        help_line="Rib used the stick to lift the vine and reach the latch.",
        tail="Then the gate opened with a soft creak.",
    ),
}


@dataclass
class StoryParams:
    challenge: str
    aid: str
    hero_name: str = "Twit"
    helper_name: str = "Rib"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about surprise and teamwork.")
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--aid", choices=AIDS)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for cid, c in CHALLENGES.items():
        for aid, a in AIDS.items():
            if cid in a.solves:
                combos.append((cid, aid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "challenge", None) is None or c[0] == getattr(args, "challenge", None))
              and (getattr(args, "aid", None) is None or c[1] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    challenge, aid = rng.choice(list(combos))
    return StoryParams(challenge=challenge, aid=aid)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    chal = _safe_lookup(CHALLENGES, params.challenge)
    aid = _safe_lookup(AIDS, params.aid)

    twit = world.add(Entity(
        id="Twit", kind="character", type="small scout",
        label="Twit", meters={"alert": 1, "stuck": 0, "reached": 0},
        memes={"curiosity": 1, "worry": 0, "wonder": 0, "trust": 0},
    ))
    rib = world.add(Entity(
        id="Rib", kind="character", type="helper",
        label="Rib", meters={"support": 1},
        memes={"calm": 1, "pride": 0},
    ))
    tool = world.add(Entity(
        id=aid.id, type="tool", label=aid.label, phrase=aid.phrase,
        owner="Twit", carrier="Twit", plural=aid.plural,
    ))
    world.facts.update(challenge=chal, aid=aid, twit=twit, rib=rib, tool=tool)

    world.say(f"Twit and Rib set off on the {world.setting.trail} with a small plan and a brave step.")
    world.say(f"They carried {aid.phrase}, because adventure goes better when you are ready.")

    world.para()
    twit.memes["curiosity"] += 1
    world.say(f"Twit wanted to {chal.verb}, but then {chal.surprise}.")
    twit.memes["alert"] += 1
    twit.memes["worry"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"That made Twit pause. {chal.obstacle}.")
    world.say(aid.help_line)
    twit.meters["stuck"] += 1
    rib.meters["support"] += 1
    world.say(f"Rib stayed close and nodded, and together they chose a better way.")
    world.say(f"They decided to use {aid.label} and try again.")

    propagate(world, narrate=True)

    world.para()
    twit.meters["reached"] += 1
    twit.memes["trust"] += 1
    twit.memes["worry"] = max(0.0, twit.memes.get("worry", 0.0) - 1)
    rib.memes["pride"] += 1
    world.say(f"They did it by teamwork. {aid.tail}")
    world.say(f"{chal.ending_image.capitalize()}.")
    world.say("Twit smiled at Rib, and the bright new place felt like a prize they had found together.")

    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    chal: Challenge = _safe_fact(world, f, "challenge")
    return [
        f'Write a short adventure story for a young child that includes "{chal.surprise}" and the word "teamwork".',
        f"Tell a gentle trail story about Twit and Rib where they face {chal.obstacle} and solve it together.",
        f"Write a simple adventure with a surprise, a helper, and a happy ending on the {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    chal: Challenge = _safe_fact(world, world.facts, "challenge")
    aid: Aid = _safe_fact(world, world.facts, "aid")
    qa = [
        QAItem(
            question="Who went on the trail adventure together?",
            answer="Twit and Rib went on the trail adventure together.",
        ),
        QAItem(
            question=f"What surprise did they find while trying to {chal.verb}?",
            answer=f"They found that {chal.surprise}.",
        ),
        QAItem(
            question=f"How did {aid.label} help them?",
            answer=f"{aid.help_line} {aid.tail}",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The problem became manageable, the path opened up, and Twit felt more trust and less worry.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share the job and help each other reach the goal.",
        ),
        QAItem(
            question="What does a surprise do in a story?",
            answer="A surprise is something unexpected that changes what the characters planned to do.",
        ),
        QAItem(
            question="Why is a trail adventure exciting?",
            answer="A trail adventure is exciting because the path can bring new places, new problems, and new discoveries.",
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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  surprise_seen={world.surprise_seen} helper_used={world.helper_used}")
    return "\n".join(lines)


CURATED = [
    StoryParams(challenge="surprise_bridge", aid="rope"),
    StoryParams(challenge="surprise_stream", aid="stones"),
    StoryParams(challenge="surprise_gate", aid="stick"),
]


ASP_RULES = r"""
valid(C, A) :- challenge(C), aid(A), solves(A, C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for c in sorted(a.solves):
            lines.append(asp.fact("solves", aid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser_args() -> argparse.ArgumentParser:
    return build_parser()


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible challenge/aid pairs:\n")
        for c, a in triples:
            print(f"  {c:16} {a}")
        return

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
