#!/usr/bin/env python3
"""A child-facing pirate tale about a historic shutter, friendship, and repair."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    captain: object | None = None
    friend: object | None = None
    helper: object | None = None
    shutter: object | None = None
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
class Scene:
    place: str
    weather: str
    landmark: str
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
    place: str = ""
    shutter: str = ""
    captain: str = ""
    friend: str = ""
    helper: str = ""
    route: str = ""
    repair: str = ""
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
class ShutterProblem:
    missing: str
    danger: str
    first_idea: str
    failed_test: str
    clue: str
    truth: str
    repair: str
    lesson: str
    ending: str
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
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)
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


PLACES = {
    "harbor": Scene("the old harbor", "a brisk salt wind", "the bell tower"),
    "island": Scene("a green island cove", "a warm sea breeze", "the watchtower"),
    "lighthouse": Scene("the historic lighthouse hill", "a restless wind", "the lantern room"),
}

SHUTTERS = {
    "oak": "the heavy oak shutter",
    "blue": "the blue-painted shutter",
    "carved": "the carved shutter marked with a silver moon",
}

NAMES = {"Luna": "girl", "Mara": "girl", "Finn": "boy", "Pip": "boy"}
HELPERS = {"parrot": "parrot", "turtle": "turtle", "monkey": "monkey", "dolphin": "dolphin"}

ROUTES = (
    "map_first",
    "dialogue_first",
    "tide_first",
    "clue_first",
    "bell_first",
    "storm_first",
)

PROBLEMS = {
    "rope": ShutterProblem(
        missing="the historic shutter's bronze hinge pin",
        danger="the shutter swung wildly above the path",
        first_idea="pulling it closed with the longest rope",
        failed_test="the rope slipped on the smooth hinge and nearly tugged the shutter loose",
        clue="salt-dark rope fibers caught on a jagged nail below the window",
        truth="a coil of old rope had snagged the hinge pin and dragged it toward the cliff path",
        repair="tied a safety line, lowered the shutter gently, and replaced the hinge with a strong pin",
        lesson="a calm plan is stronger than a hurried pull",
        ending="the repaired shutter rested safely while the harbor bell rang over the blue water",
    ),
    "storm": ShutterProblem(
        missing="the historic shutter's iron latch",
        danger="rain could pour through the open window and ruin the captain's charts",
        first_idea="covering the opening with a sail",
        failed_test="the wet sail ballooned like a giant kite and blocked everyone's view",
        clue="a tiny line of sand led from the latch to a cracked roof tile",
        truth="the storm had shaken the roof tile down, and its fall had knocked the latch into a gutter",
        repair="secured the sail, lifted the tile with a pole, and retrieved the latch from the gutter",
        lesson="good helpers share observations before choosing a tool",
        ending="the historic shutter clicked shut as dry charts waited safely inside",
    ),
    "seagull": ShutterProblem(
        missing="the historic shutter's little copper knob",
        danger="without the knob, nobody could close the window before night",
        first_idea="chasing the gulls that cried on the roof",
        failed_test="the gulls flew away, but the knob was still nowhere to be seen",
        clue="a bright copper glint shone inside an empty rain barrel",
        truth="the knob had bounced into the barrel when a loose bucket struck the wall",
        repair="rolled the barrel away from the doorway and lifted the knob with a hooked stick",
        lesson="a loud suspect is not always the true cause",
        ending="the copper knob gleamed on the historic shutter beneath a pink evening sky",
    ),
    "map": ShutterProblem(
        missing="the historic shutter's painted sea-star",
        danger="the old landmark would lose an important piece of its story",
        first_idea="painting a new star over the bare wood",
        failed_test="the fresh paint hid the old mark instead of restoring it",
        clue="blue flakes appeared along a trail beneath the carpenter's bench",
        truth="the sea-star had fallen into a box of old blue boards during the morning repair",
        repair="washed the original piece, matched its screws, and placed it back on the shutter",
        lesson="restoring history means saving what is real, not covering it with a guess",
        ending="the old sea-star shone again while Luna and her friend told its story to the crew",
    ),
    "parrot": ShutterProblem(
        missing="the historic shutter's small brass key",
        danger="the window could not be locked before the tide rose",
        first_idea="following the parrot's repeated cry of 'key, key!'",
        failed_test="the parrot led them to a shiny spoon instead",
        clue="a brass scratch marked the edge of a wooden supply chest",
        truth="the key had slid under the chest when the deck tilted during a wave",
        repair="lifted the chest with a lever and returned the key to its hook",
        lesson="words can guide a search, but careful evidence finishes it",
        ending="the locked shutter kept the sea spray out as the parrot practiced a kinder song",
    ),
}

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A pirate tale about friendship and a historic shutter.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--shutter", choices=sorted(SHUTTERS))
    parser.add_argument("--captain")
    parser.add_argument("--friend", choices=sorted(NAMES))
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


ASP_RULES = """
valid(Place, Shutter, Problem) :- place(Place), shutter(Shutter), problem(Problem).
safe(Place, Shutter, Problem) :- valid(Place, Shutter, Problem).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    facts = []
    facts.extend(asp.fact("place", value) for value in PLACES)
    facts.extend(asp.fact("shutter", value) for value in SHUTTERS)
    facts.extend(asp.fact("problem", value) for value in PROBLEMS)
    return "\n".join(facts)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, shutter, problem) for place in sorted(PLACES)
            for shutter in sorted(SHUTTERS) for problem in sorted(PROBLEMS)]


def asp_valid_combos() -> list[tuple]:
    import asp
    symbols = asp.one_model(asp_program())
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    python_values = set(valid_combos())
    asp_values = set(asp_valid_combos())
    if python_values == asp_values:
        print(f"OK: clingo gate matches valid_combos() ({len(python_values)} combinations).")
        return 0
    print("MISMATCH:")
    print("Python only:", sorted(python_values - asp_values))
    print("ASP only:", sorted(asp_values - python_values))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo for combo in valid_combos()
        if not getattr(args, "place", None) or combo[0] == getattr(args, "place", None)
        if not getattr(args, "shutter", None) or combo[1] == getattr(args, "shutter", None)
        if not getattr(args, "problem", None) or combo[2] == getattr(args, "problem", None)
    ]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, shutter, problem = rng.choice(choices)
    captain = getattr(args, "captain", None) or "Luna"
    friend_choices = [name for name in sorted(NAMES) if name != captain]
    friend = getattr(args, "friend", None) or rng.choice(friend_choices)
    return StoryParams(
        place=place,
        shutter=shutter,
        captain=captain,
        friend=friend,
        helper=getattr(args, "helper", None) or rng.choice(sorted(HELPERS)),
        route=rng.choice(ROUTES),
        repair=problem,
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.place, params.shutter, params.captain,
        params.friend, params.helper, params.route, params.repair,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = _safe_lookup(PLACES, params.place)
    problem = _safe_lookup(PROBLEMS, params.repair)
    rng = story_rng(params)
    world = World(scene)

    captain = world.add(Entity(
        id=params.captain,
        kind="character",
        type=NAMES.get(params.captain, "child"),
        memes={"bravery": 1.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type=_safe_lookup(NAMES, params.friend),
        memes={"trust": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="animal",
        type=_safe_lookup(HELPERS, params.helper),
        memes={"helpfulness": 1.0},
    ))
    shutter = world.add(Entity(
        id="historic_shutter",
        kind="landmark",
        type="shutter",
        label=_safe_lookup(SHUTTERS, params.shutter),
        meters={"height": 3.0, "distance_to_path": 2.0},
        memes={"history": 1.0},
    ))

    openings = {
        "map_first": (
            f"Luna drew a map of {scene.place}: the pier, the {scene.landmark}, "
            f"and {shutter.label}. The old pirate crew had guarded that historic shutter for many years."
        ),
        "dialogue_first": (
            f'"Crew close by!" {captain.id} called at {scene.place}. '
            f'{shutter.label.capitalize()} had come loose, and {scene.weather} pushed against it.'
        ),
        "tide_first": (
            f"The tide was climbing beside {scene.place} when {captain.id} noticed "
            f'{shutter.label} shaking above the stones. The historic landmark needed help before sunset.'
        ),
        "clue_first": (
            f"Near {scene.landmark}, {captain.id} found a small clue beneath {shutter.label}. "
            f"The historic shutter was open, and {scene.weather} rushed through the room."
        ),
        "bell_first": (
            f"The bell at {scene.landmark} gave three worried clangs. At {scene.place}, "
            f"{captain.id} saw {shutter.label} swinging where it had been still for a century."
        ),
        "storm_first": (
            f"{scene.weather.capitalize()} swept across {scene.place}. "
            f'{captain.id} and {friend.id} hurried toward {shutter.label}, the historic window of the old lookout.'
        ),
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"{friend.id} grabbed the repair chest, while {captain.id} checked the path below.",
        f"{captain.id} and {friend.id} stood shoulder to shoulder, just as their pirate teachers had taught them.",
        f"The {helper.type} watched from a safe rail as the friends made a careful plan.",
    ]))
    world.para()

    world.say(f"The danger was clear: {problem.danger}.")
    world.say(rng.choice([
        f'"We must save the shutter and the old story together," {captain.id} said.',
        f'"No racing," {friend.id} warned. "We will solve one part at a time."',
        f'{captain.id} nodded. "Friends listen before they pull."',
    ]))
    world.say(f"Their first idea was {problem.first_idea}.")
    world.say(f"They tested it, but {problem.failed_test}.")
    captain.meters["tests_completed"] = 1.0
    friend.memes["confidence"] = 1.0
    world.say(rng.choice([
        f'"That did not work," {friend.id} said. "Good thing we tested it while we were together."',
        f'{captain.id} lowered the rope. "A failed try is a sign to think again, not to blame a friend."',
        f"The {helper.type} made a soft warning sound, and everyone looked more closely.",
    ]))
    world.para()

    world.say(f"Then {helper.type} helped them notice {problem.clue}.")
    world.say(f"{captain.id} and {friend.id} followed the clue instead of arguing about the first idea.")
    world.say(f"They discovered that {problem.truth}.")
    shutter.meters["danger"] = 0.0
    captain.memes["friendship"] = 1.0
    friend.memes["problem_solving"] = 1.0
    world.say(rng.choice([
        f'"Your careful looking found the answer," {captain.id} told {friend.id}.',
        f'"We solved it because we shared every clue," {friend.id} replied.',
        f'The friends grinned. Even the {helper.type} seemed pleased with their teamwork.',
    ]))
    world.para()

    world.say(f"Together they {problem.repair}.")
    world.say(f"The work was safe because {captain.id} held the line while {friend.id} chose the right tool.")
    world.say(f"{captain.id} wrote the lesson in the ship's log: {problem.lesson}.")
    world.say(rng.choice([
        f"At sunset, {problem.ending}.",
        f"When the tide turned, {problem.ending}.",
        f"That evening, {problem.ending}.",
    ]))

    world.facts.update(
        captain=captain,
        friend=friend,
        helper=helper,
        shutter=shutter,
        scene=scene,
        problem=problem,
        shutter_name=shutter.label,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    problem = facts["problem"]
    return [
        f"Write a gentle pirate tale about {facts['captain'].id}, {facts['friend'].id}, and {facts['shutter_name']} at {facts['scene'].place}.",
        f"Tell a friendship problem-solving story in which the children investigate why {problem.missing} is missing.",
        f"Write a child-facing adventure that ends with {problem.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    problem = facts["problem"]
    captain = facts["captain"].id
    friend = facts["friend"].id
    helper = facts["helper"].type
    place = facts["scene"].place
    return [
        QAItem(
            question=f"What historic object needed help at {place}?",
            answer=f"{facts['shutter_name'].capitalize()} needed help at {place}; it was part of the old landmark.",
        ),
        QAItem(
            question=f"What first idea did {captain} and {friend} test, and why did they change plans?",
            answer=f"They tested {problem.first_idea}, but {problem.failed_test}. They changed plans and searched for better evidence.",
        ),
        QAItem(
            question=f"How did the {helper} help solve the shutter problem?",
            answer=f"The {helper} helped them notice {problem.clue}, which led them to discover that {problem.truth}.",
        ),
        QAItem(
            question=f"How did friendship help {captain} and {friend} repair the historic shutter?",
            answer=f"They listened to one another, shared clues, and worked together: they {problem.repair}.",
        ),
        QAItem(
            question="What lesson did the pirate crew record?",
            answer=f"They recorded that {problem.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a movable cover for a window. It can protect the room from wind, rain, or bright sunlight.",
        ),
        QAItem(
            question="Why should friends test an idea carefully?",
            answer="A careful test shows whether an idea works and can prevent people from making a risky choice or blaming someone unfairly.",
        ),
        QAItem(
            question="How can friendship help during a problem?",
            answer="Friends can listen, share observations, divide safe tasks, and encourage one another when the first plan fails.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  location={world.scene.place}")
    lines.append(f"  truth={_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "problem").truth}")
    return "\n".join(lines)


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="harbor",
        shutter="oak",
        captain="Luna",
        friend="Mara",
        helper="parrot",
        route="map_first",
        repair="rope",
        seed=101,
    ),
    StoryParams(
        place="lighthouse",
        shutter="blue",
        captain="Luna",
        friend="Finn",
        helper="turtle",
        route="storm_first",
        repair="storm",
        seed=202,
    ),
    StoryParams(
        place="island",
        shutter="carved",
        captain="Luna",
        friend="Pip",
        helper="dolphin",
        route="clue_first",
        repair="map",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        combinations = asp_valid_combos()
        print(f"{len(combinations)} compatible combinations:\n")
        for place, shutter, problem in combinations:
            print(f"  {place:12} {shutter:8} {problem}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < getattr(args, "n", None) and attempts < max(getattr(args, "n", None) * 50, 50):
            current_seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(current_seed))
            except StoryError:
                continue
            params.seed = current_seed
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
        if getattr(args, "all", None):
            header = "### curated story"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
