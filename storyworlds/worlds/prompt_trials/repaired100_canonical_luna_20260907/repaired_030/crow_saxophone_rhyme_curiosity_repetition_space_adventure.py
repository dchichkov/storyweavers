#!/usr/bin/env python3
"""
A small space-adventure storyworld about a curious crow, a saxophone, and a
repeating rhyme that helps a crew find its way home.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    beacon: object | None = None
    captain: object | None = None
    crow: object | None = None
    crystal: object | None = None
    musician: object | None = None
    sax: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class StoryParams:
    captain: str = ""
    crow_name: str = ""
    saxophonist: str = ""
    moon: str = ""
    rhyme: str = ""
    repetition: int = 0
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


@dataclass
class Moon:
    name: str
    landscape: str
    beacon: str
    treasure: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


MOONS = {
    "silver": Moon("Silver Moon", "a field of glittering craters", "a blue beacon", "a map crystal"),
    "echo": Moon("Echo Moon", "a canyon of ringing stones", "a green beacon", "a star compass"),
    "copper": Moon("Copper Moon", "a red plain dusted with sparks", "a gold beacon", "a moonstone key"),
    "cloud": Moon("Cloud Moon", "a floating garden above white clouds", "a violet beacon", "a feather-light engine part"),
}

RHYME_OPTIONS = {
    "light": "When the silver light is bright, play the tune and steer aright.",
    "star": "Find the star, hear the bar, then you will know where you are.",
    "glow": "Follow the glow, play soft and low, and homeward rockets go.",
    " tune": "Hear the tune, face the moon, and the lost path will come soon.",
}

CAPTAINS = ["Mara", "Jon", "Pia", "Sol", "Nia"]
CROWS = ["Cinder", "Pepper", "Ink", "Comet", "Rook"]
SAXOPHONISTS = ["Tavi", "Lulu", "Orin", "Bea", "Kito"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crow saxophone space-adventure storyworld.")
    parser.add_argument("--captain")
    parser.add_argument("--crow-name")
    parser.add_argument("--saxophonist")
    parser.add_argument("--moon", choices=MOONS)
    parser.add_argument("--rhyme", choices=("light", "star", "glow", "tune"))
    parser.add_argument("--repetition", type=int, choices=(2, 3, 4))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain = getattr(args, "captain", None) or rng.choice(CAPTAINS)
    crow_name = getattr(args, "crow_name", None) or rng.choice(CROWS)
    saxophonist = getattr(args, "saxophonist", None) or rng.choice(SAXOPHONISTS)
    if len({captain, saxophonist}) < 2:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        captain=captain,
        crow_name=crow_name,
        saxophonist=saxophonist,
        moon=getattr(args, "moon", None) or rng.choice(tuple(MOONS)),
        rhyme=getattr(args, "rhyme", None) or rng.choice(("light", "star", "glow", "tune")),
        repetition=getattr(args, "repetition", None) or rng.choice((2, 3, 4)),
    )


def tell(params: StoryParams) -> World:
    moon = _safe_lookup(MOONS, params.moon)
    rhyme = _safe_lookup(RHYME_OPTIONS, params.rhyme).strip()
    world = World()

    captain = world.add(Entity("captain", "character", params.captain, "rocket"))
    crow = world.add(Entity("crow", "animal", params.crow_name, "rocket"))
    musician = world.add(Entity("musician", "character", params.saxophonist, "rocket"))
    sax = world.add(Entity("saxophone", "instrument", "the silver saxophone", "rocket"))
    beacon = world.add(Entity("beacon", "object", moon.beacon, "moon"))
    crystal = world.add(Entity("treasure", "object", moon.treasure, "moon"))

    world.facts.update(
        captain=captain,
        crow=crow,
        musician=musician,
        sax=sax,
        beacon=beacon,
        treasure=crystal,
        moon=moon,
        rhyme=rhyme,
        repetition=params.repetition,
    )

    world.say(
        f"Captain {captain.label} flew the little rocket toward {moon.name}, "
        f"where {moon.landscape} shimmered below."
    )
    world.say(
        f"Beside {captain.label} sat {crow.label}, a curious crow, while "
        f"{musician.label} guarded a bright saxophone."
    )
    world.say(
        f"They had come to find {moon.treasure}, but a cloud of space dust swallowed "
        f"the stars and hid the route home."
    )

    world.para()
    crow.memes["curiosity"] = 1.0
    crow.meters["pecking"] = 1.0
    world.say(
        f"{crow.label} tilted its head and noticed that a tiny radio lamp blinked "
        f"whenever the saxophone was near the window."
    )
    world.say(
        f'"Maybe the lamp is showing us a path," said {captain.label}. '
        f'"Then let us listen carefully," replied {musician.label}.'
    )
    world.say(
        f"{musician.label} played the first line: {rhyme}"
    )

    world.para()
    world.facts["pattern_found"] = True
    world.say(
        f"The lamp flashed {params.repetition} times. Each flash matched one bright "
        f"note, and each note made {crow.label} flap toward a different window."
    )
    for i in range(params.repetition):
        world.say(f"Again the saxophone sang, \"{rhyme}\"")
    world.say(
        f"On the last repetition, {crow.label} tapped the correct window with its beak. "
        f"Beyond it, the hidden {moon.beacon} rose over the moon."
    )
    world.fired.add("rhyme-repeated")
    world.facts["route"] = "the beacon route"

    world.para()
    world.say(
        f"The crew landed safely on {moon.name}. {crow.label} led them across "
        f"{moon.landscape} while {musician.label} played the rhyme softly."
    )
    world.say(
        f"Near the {moon.beacon}, they found {moon.treasure} shining under a stone."
    )
    world.say(
        f'"You were curious enough to notice the blinking lamp," said {captain.label}. '
        f'"And you repeated the song until it made sense," added {musician.label}.'
    )
    world.say(
        f"{crow.label} gave a pleased caw. The crew placed {moon.treasure} in the "
        f"rocket, followed the repeated rhyme, and sailed home by the steady stars."
    )
    world.facts["resolved"] = True
    world.facts["lesson"] = "Curiosity notices clues, and repetition can turn a clue into a safe path."
    return world


def generation_prompts(world: World) -> list[str]:
    moon: Moon = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "moon")
    return [
        f"Write a space adventure about a curious crow and a saxophone near {moon.name}.",
        "Use a rhyme and repeat it until the travelers discover how to get home.",
        "Show how curiosity changes a dangerous journey into a successful rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    captain: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "captain")
    crow: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "crow")
    musician: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "musician")
    moon: Moon = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "moon")
    rhyme: str = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "rhyme")
    repetition: int = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "repetition")
    return [
        QAItem(
            question=f"Who traveled toward {moon.name}?",
            answer=f"Captain {captain.label}, the curious crow {crow.label}, and the saxophonist {musician.label} traveled there together.",
        ),
        QAItem(
            question="What clue did the crow notice?",
            answer=f"The crow noticed that a tiny radio lamp blinked whenever the saxophone was near the rocket window.",
        ),
        QAItem(
            question="Why did the crew repeat the rhyme?",
            answer=f"They repeated “{rhyme}” {repetition} times because the flashes, notes, and crow's movements revealed the safe route to the beacon.",
        ),
        QAItem(
            question="What changed by the end of the adventure?",
            answer="The crew found the moon treasure and used the repeated musical clue to return safely. They learned that curiosity notices clues, and repetition can turn a clue into a safe path.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crow?",
            answer="A crow is a clever black bird that can notice patterns, remember places, and use sounds to communicate.",
        ),
        QAItem(
            question="What is a saxophone?",
            answer="A saxophone is a wind instrument with a curved metal body and a reed that helps make its musical sound.",
        ),
        QAItem(
            question="Why can repetition help someone learn?",
            answer="Repetition can help someone learn because hearing or practicing something more than once makes its pattern easier to remember.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"  {entity.id:10} kind={entity.kind:10} "
            f"location={entity.location:8} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  facts: {sorted(world.facts)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(space).
feature(rhyme).
feature(curiosity).
feature(repetition).
object(crow).
object(saxophone).
valid(space,crow,saxophone).
valid(space,rhyme,curiosity).
valid(space,repetition,rhyme).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "space"),
            asp.fact("feature", "rhyme"),
            asp.fact("feature", "curiosity"),
            asp.fact("feature", "repetition"),
            asp.fact("object", "crow"),
            asp.fact("object", "saxophone"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("space", "crow", "saxophone"),
        ("space", "rhyme", "curiosity"),
        ("space", "repetition", "rhyme"),
    ]


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    print("only in python:", sorted(py - clingo))
    print("only in clingo:", sorted(clingo - py))
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


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"[Prompt {index}] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print()
            print(show_qa_item(item))


CURATED = [
    StoryParams("Mara", "Cinder", "Tavi", "silver", "light", 3),
    StoryParams("Jon", "Pepper", "Lulu", "echo", "star", 2),
    StoryParams("Pia", "Comet", "Orin", "copper", "glow", 4),
    StoryParams("Sol", "Rook", "Bea", "cloud", "tune", 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return

    if getattr(args, "verify", None):
        code = asp_verify()
        if code:
            sys.exit(code)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or "crow" not in sample.story.lower():
                print("Generated-story verification failed.")
                sys.exit(1)
        print("OK: generated stories passed.")
        return

    if getattr(args, "asp", None):
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(1, getattr(args, "n", None))):
            seed = base_seed + index
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
