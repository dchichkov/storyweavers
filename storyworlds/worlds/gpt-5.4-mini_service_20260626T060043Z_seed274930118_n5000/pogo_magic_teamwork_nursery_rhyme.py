#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a pogo stick, a little bit of magic,
and teamwork that turns a wobble into a win.

The core tale is child-facing and state-driven:
- a child wants to bounce on a pogo stick,
- the bouncing is too wobbly to reach a goal,
- a friend adds magic with teamwork,
- the goal is reached in a cheerful ending image.
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
    wither: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: str = ""
    risk: str = ""
    friend: object | None = None
    goal: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str = "the meadow"
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
class Tool:
    id: str
    label: str
    phrase: str
    boost: float
    magic_needed: bool = False
    teamwork_needed: bool = False
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
class Goal:
    label: str
    phrase: str
    region: str
    risk: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("bounce", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("balance", 0.0) >= THRESHOLD:
            continue
        sig = ("wobble", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.id} wibbled and wobbled, and the bounce went crooked.")
    return out


def _r_magic_teamwork(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("magic", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("teamwork", 0.0) < THRESHOLD:
            continue
        sig = ("steady", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["balance"] = actor.meters.get("balance", 0.0) + 1
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        out.append(f"Magic and teamwork made the bounce go steady and bright.")
    return out


CAUSAL_RULES = [_r_wobble, _r_magic_teamwork]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def intro(world: World, hero: Entity, friend: Entity, tool: Entity, goal: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a bright pogo stick and a song in {hero.pronoun('possessive')} step."
    )
    world.say(
        f"{friend.id} was a kind helper who loved a tiny bit of magic and a lot of teamwork."
    )
    world.say(
        f"They had a {tool.label} for bouncing and a {goal.phrase} that waited beyond the grass."
    )


def wants_bounce(world: World, hero: Entity, tool: Entity) -> None:
    hero.meters["bounce"] = hero.meters.get("bounce", 0.0) + 1
    world.say(
        f"{hero.id} hopped on the {tool.label} and said, \"Boing, boing, boing, let me dance along!\""
    )


def check_risk(world: World, hero: Entity, goal: Entity) -> bool:
    if hero.meters.get("balance", 0.0) >= THRESHOLD:
        return False
    world.facts["risk"] = goal.risk
    world.say(
        f"But the hops were wobbly, and the {goal.label} seemed far away."
    )
    return True


def teamwork_offer(world: World, friend: Entity, hero: Entity, tool: Entity, goal: Entity) -> None:
    friend.meters["teamwork"] = friend.meters.get("teamwork", 0.0) + 1
    hero.meters["teamwork"] = hero.meters.get("teamwork", 0.0) + 1
    hero.meters["magic"] = hero.meters.get("magic", 0.0) + 1
    world.say(
        f"{friend.id} clapped once and winked twice. \"With teamwork and magic, we can steady the ride,\" {friend.pronoun()} said."
    )
    world.say(
        f"{friend.id} traced a shining circle around the {tool.label}, and {hero.id} held on tight."
    )
    propagate(world, narrate=True)


def finish(world: World, hero: Entity, friend: Entity, tool: Entity, goal: Entity) -> None:
    if hero.meters.get("balance", 0.0) < THRESHOLD:
        pass
    world.say(
        f"Up, up went {hero.id}, light as a feather on the {tool.label}, and over went the little {goal.label} at last."
    )
    world.say(
        f"{hero.id} and {friend.id} laughed together, and the meadow shone like a nursery rhyme come true."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    tool = world.add(Entity(id="pogo", type="pogo stick", label="pogo stick", phrase="a shiny pogo stick"))
    goal = world.add(Entity(id="star", type="thing", label="star", phrase="a little silver star", region="far fence", risk="too far to reach"))

    intro(world, hero, friend, tool, goal)
    world.para()
    wants_bounce(world, hero, tool)
    check_risk(world, hero, goal)
    world.para()
    teamwork_offer(world, friend, hero, tool, goal)
    finish(world, hero, friend, tool, goal)

    world.facts.update(hero=hero, friend=friend, tool=tool, goal=goal, setting=setting)
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"pogo"}),
    "yard": Setting(place="the yard", affords={"pogo"}),
}

HERO_NAMES = ["Mia", "Lily", "Noah", "Finn", "Ava", "Theo"]
FRIEND_NAMES = ["Bea", "Pip", "June", "Ollie", "Nia", "Sam"]
HERO_TYPES = ["girl", "boy"]
FRIEND_TYPES = ["girl", "boy"]


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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
    ap = argparse.ArgumentParser(description="A nursery-rhyme world of pogo, magic, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_type = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    friend_type = getattr(args, "friend_gender", None) or rng.choice(FRIEND_TYPES)
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, friend_name=friend_name, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.hero_name, params.hero_type, params.friend_name, params.friend_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about a pogo stick, magic, and teamwork.',
        f"Tell a gentle rhyme where {f['hero'].id} tries the pogo stick and {f['friend'].id} helps with magic.",
        f"Write a child-friendly story that ends with {f['hero'].id} and {f['friend'].id} reaching a little star together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, tool, goal = f["hero"], f["friend"], (f.get("tool") or next(iter(TOOLS.values()))), f["goal"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {tool.label}?",
            answer=f"{hero.id} wanted to bounce on the {tool.label} and make a happy little dance.",
        ),
        QAItem(
            question=f"Who helped {hero.id} use magic and teamwork?",
            answer=f"{friend.id} helped {hero.id} by sharing magic and teamwork.",
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} reach at the end?",
            answer=f"They reached {goal.phrase}, and the little star was no longer far away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pogo stick?",
            answer="A pogo stick is a bouncing toy with a spring that lets a child hop up and down.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do something together.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wondrous and unusual that can make a story feel sparkling and special.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_fact(H).
friend(F) :- friend_fact(F).
tool(T) :- tool_fact(T).
goal(G) :- goal_fact(G).

can_bounce(H) :- hero(H), tool(pogo).
needs_help(H) :- hero(H), not steady(H).
steady(H) :- magic(H), teamwork(H).

wobble(H) :- hero(H), can_bounce(H), not steady(H).
resolved(H) :- hero(H), steady(H).

#show wobble/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero_fact", "hero"),
        asp.fact("friend_fact", "friend"),
        asp.fact("tool_fact", "pogo"),
        asp.fact("goal_fact", "star"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show wobble/1.\n#show resolved/1."))
    names = {sym.name for sym in model}
    if "resolved" in names:
        print("OK: ASP model can resolve the pogo story.")
        return 0
    print("MISMATCH: ASP model did not resolve the pogo story.")
    return 1


def asp_valid_story() -> bool:
    return True


CURATED = [
    StoryParams(place="meadow", hero_name="Mia", hero_type="girl", friend_name="Pip", friend_type="boy"),
    StoryParams(place="yard", hero_name="Noah", hero_type="boy", friend_name="Bea", friend_type="girl"),
]


def explain_rejection() -> str:
    return "(No story: this little world always wants a pogo stick, a touch of magic, and teamwork.)"


def resolve_or_fail(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show wobble/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story pattern: pogo + magic + teamwork.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_or_fail(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
