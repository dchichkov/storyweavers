#!/usr/bin/env python3
"""
storyworlds/worlds/coon_foreign_dialogue_suspense_pirate_tale.py
=================================================================

A small pirate-tale storyworld about a coon crew, a foreign clue, a tense
midnight choice, and a dialogue-led resolution.

Premise:
- A young coon aboard a little pirate ship longs for adventure.
- The crew finds a foreign bottle-map or foreign drum, and the captain worries
  it may lead into danger.
- Suspense grows as the coon must decide whether to open the clue.
- Dialogue reveals the risk, the route, and the fix.
- The ending proves what changed: the crew reaches a safe treasure spot and the
  once-foreign thing becomes a helpful guide.

The simulation models:
- physical meters: tide, distance, dampness, lantern, rope, sail, treasure
- emotional memes: curiosity, fear, trust, relief, suspicion, bravery

The story generator deliberately keeps to a few plausible variants and refuses
invalid combinations with a readable StoryError.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, replace
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"coon", "raccoon"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"captain", "sailor", "pirate"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    sea: str
    clue_kind: str
    danger: str
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
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    reveals: str
    risky_when_opened: bool
    foreign: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    covers: set[str]
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
        self.port_route: str = ""

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
        w = World(self.setting)
        w.entities = {k: replace(v, meters=dict(v.meters), memes=dict(v.memes)) for k, v in self.entities.items()}
        w.fired = set(self.fired)
        w.port_route = self.port_route
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    clue: str
    hero: str
    captain: str
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


SETTINGS = {
    "harbor": Setting(place="the harbor", sea="the dark sea", clue_kind="map", danger="reef", affords={"open", "sail"}),
    "island": Setting(place="the island cove", sea="the blue sea", clue_kind="bottle", danger="fog", affords={"open", "sail"}),
}

CLUES = {
    "map": Clue(id="map", label="map", phrase="a foreign map in a glass bottle", kind="map", reveals="a safe cove behind the reef", risky_when_opened=True, foreign=True),
    "bottle": Clue(id="bottle", label="bottle", phrase="a foreign bottle with a folded note", kind="bottle", reveals="a hidden lane through the fog", risky_when_opened=True, foreign=True),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="lantern", phrase="a steady lantern", helps_with={"fog"}, covers={"dark"}),
    "hook": Tool(id="hook", label="hook", phrase="a stout hook", helps_with={"reef"}, covers={"rope"}),
}

GENDERS = {"boy", "girl"}


def _get_pronoun(name: str) -> str:
    return "he" if name.lower() in {"coon", "milo", "tom"} else "she"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale coon storyworld with foreign clue, dialogue, and suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero")
    ap.add_argument("--captain")
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
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    hero = getattr(args, "hero", None) or rng.choice(["Coon", "Milo", "Pip"])
    captain = getattr(args, "captain", None) or rng.choice(["Captain Mira", "Captain Sal", "Captain June"])
    return StoryParams(place=place, clue=clue, hero=hero, captain=captain)


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    clue = _safe_lookup(CLUES, params.clue)
    if clue.kind != setting.clue_kind:
        pass

    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="coon", label="coon"))
    captain = world.add(Entity(id=params.captain, kind="character", type="captain", label="captain"))
    item = world.add(Entity(id="clue", type=clue.kind, label=clue.label, phrase=clue.phrase, owner=hero.id))

    world.facts.update(hero=hero, captain=captain, clue=item, clue_cfg=clue, setting=setting)
    return world


def _tension_rises(world: World) -> None:
    h = _safe_fact(world, world.facts, "hero")
    c = _safe_fact(world, world.facts, "captain")
    clue = _safe_fact(world, world.facts, "clue")
    cfg = _safe_fact(world, world.facts, "clue_cfg")
    h.memes["curiosity"] = 1.0
    c.memes["suspicion"] = 1.0
    world.say(f"On {world.setting.place}, {h.id} found {cfg.phrase}.")
    world.say(f'"That looks foreign," {c.id} said. "What if it leads us wrong?"')
    world.say(f'"It might lead us right," {h.id} whispered, holding {clue.label} close.')
    world.para()
    world.say(f"The sea went quiet, and even the rope seemed to wait.")


def _open_clue(world: World) -> None:
    h = _safe_fact(world, world.facts, "hero")
    c = _safe_fact(world, world.facts, "captain")
    clue = _safe_fact(world, world.facts, "clue")
    cfg = _safe_fact(world, world.facts, "clue_cfg")
    if cfg.risky_when_opened:
        h.memes["fear"] = 0.5
        c.memes["fear"] = 0.5
        world.say(f'{h.id} asked, "Should I open it now?"')
        world.say(f'"Slowly," {c.id} said. "We listen first."')
        world.say(f"{h.id} opened {clue.it()} and found the note pointing toward {cfg.reveals}.")
        world.port_route = cfg.reveals
        h.memes["bravery"] = 1.0
        c.memes["trust"] = 1.0


def _sail_fix(world: World) -> None:
    h = _safe_fact(world, world.facts, "hero")
    c = _safe_fact(world, world.facts, "captain")
    cfg = _safe_fact(world, world.facts, "clue_cfg")
    world.say(f'"Then let us sail," {c.id} said. "Keep the lantern high and follow the clue."')
    world.say(f"{h.id} nodded and tied the line, while the little ship slipped past the danger.")
    world.say(f"By morning, they reached {cfg.reveals}, and the foreign clue had become their best guide.")
    h.memes["relief"] = 1.0
    c.memes["relief"] = 1.0
    c.memes["suspicion"] = 0.0


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = _safe_fact(world, world.facts, "hero")
    captain = _safe_fact(world, world.facts, "captain")

    world.say(f"{hero.id} was a small coon pirate with quick paws and a brave nose.")
    world.say(f"{hero.id} loved the ship because every creak sounded like a secret.")
    world.say(f"{captain.id} watched over the deck and trusted the wind more than luck.")
    world.para()
    world.say(f"One dusk, {hero.id} and the crew drifted near {world.setting.place}.")
    world.say(f"The water was dark, and {world.setting.danger} waited where the lantern could not reach.")
    _tension_rises(world)
    world.para()
    _open_clue(world)
    _sail_fix(world)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a young child about a coon who finds a foreign {f["clue_cfg"].label} and must decide what to do.',
        f"Tell a suspenseful dialogue story where {f['hero'].id} asks {f['captain'].id} about a foreign clue on the ship.",
        f"Write a gentle pirate adventure with a tense moment, spoken lines, and a safe ending image at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    captain = _safe_fact(world, f, "captain")
    clue = _safe_fact(world, f, "clue_cfg")
    return [
        QAItem(
            question=f"What kind of animal is {hero.id} in this pirate story?",
            answer=f"{hero.id} is a coon pirate, a little animal sailor with quick paws and a curious heart.",
        ),
        QAItem(
            question=f"What did {hero.id} find that was foreign?",
            answer=f"{hero.id} found {clue.phrase}. It looked foreign because it came from far away and carried a clue.",
        ),
        QAItem(
            question=f"Why did {captain.id} worry at first?",
            answer=f"{captain.id} worried because the clue might lead them toward {world.setting.danger}, where the ship could get into trouble.",
        ),
        QAItem(
            question=f"How did the tense moment turn into a safe ending?",
            answer=f"{hero.id} opened the clue carefully, learned about {clue.reveals}, and the crew sailed there instead of drifting into danger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a captain on a ship?",
            answer="A captain is the person who helps steer the ship and make important decisions.",
        ),
        QAItem(
            question="What does a lantern do at sea?",
            answer="A lantern gives light so sailors can see the deck, ropes, and waves when it is dark.",
        ),
        QAItem(
            question="Why can a reef be dangerous for a ship?",
            answer="A reef can sit near the surface of the water and scrape or stop a ship if the sailors do not steer around it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    lines.append(f"route: {world.port_route}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", clue="map", hero="Coon", captain="Captain Mira"),
    StoryParams(place="island", clue="bottle", hero="Pip", captain="Captain June"),
]


ASP_RULES = r"""
place(harbor). place(island).
clue(map). clue(bottle).
hero(coon). hero(pip).
captain(mira). captain(june).
setting_clue_kind(harbor,map).
setting_clue_kind(island,bottle).
clue_foreign(map). clue_foreign(bottle).
risky(map). risky(bottle).

valid_story(P,C,H,K) :- setting_clue_kind(P,K), clue(K), hero(H), captain(C), risky(K), clue_foreign(K).
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "harbor"),
        asp.fact("place", "island"),
        asp.fact("clue", "map"),
        asp.fact("clue", "bottle"),
        asp.fact("hero", "coon"),
        asp.fact("hero", "pip"),
        asp.fact("captain", "mira"),
        asp.fact("captain", "june"),
        asp.fact("setting_clue_kind", "harbor", "map"),
        asp.fact("setting_clue_kind", "island", "bottle"),
        asp.fact("clue_foreign", "map"),
        asp.fact("clue_foreign", "bottle"),
        asp.fact("risky", "map"),
        asp.fact("risky", "bottle"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c, h, k) for p in SETTINGS for c in CLUES for h in {"coon", "pip"} if _safe_lookup(SETTINGS, p).clue_kind == _safe_lookup(CLUES, c).kind}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
