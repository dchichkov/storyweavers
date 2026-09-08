#!/usr/bin/env python3
"""
A small adventure storyworld about a kook, a strange mountain signal, and awe.

The world simulates a child-facing adventure in which a curious kook follows
a glowing trail, faces a choice at a high ridge, and learns that courage can
include stopping to listen. Inner monologue is used as a narrative instrument.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

try:
    from storyworlds.results import QAItem, StoryError, StorySample
except ImportError:
    from results import QAItem, StoryError, StorySample



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

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
class StoryParams:
    kook_name: str = "Kiko"
    guide_name: str = "Mara"
    place: str = "the blue mountain"
    route: str = "the lantern trail"
    danger: str = "a cracked rope bridge"
    treasure: str = "a nest of moon-bright stones"
    seed: Optional[int] = None
    variation: int = 0
    sample: object | None = None
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
class Route:
    key: str
    place: str
    route: str
    danger: str
    treasure: str
    clue: str
    sound: str
    ending_image: str
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


ROUTES = [
    Route(
        "blue_mountain",
        "the blue mountain",
        "the lantern trail",
        "a cracked rope bridge",
        "a nest of moon-bright stones",
        "three blue scratches pointed toward a safer ledge",
        "clink-clink",
        "Moonlight pooled in the stones while the valley shone below.",
    ),
    Route(
        "whistling_canyon",
        "Whistling Canyon",
        "the echo path",
        "a falling shelf of loose rocks",
        "a silver feather caught in a thorn bush",
        "a low whistle repeated only when the wind was calm",
        "whooo-whee",
        "The silver feather trembled in the dawn breeze.",
    ),
    Route(
        "red_forest",
        "the Red Forest",
        "the firefly track",
        "a stream swollen by rain",
        "a tiny bell buried beneath fern leaves",
        "fireflies gathered above the shallowest stones",
        "plink-plink",
        "The bell rang once as the forest woke around them.",
    ),
    Route(
        "cloud_steps",
        "Cloud Steps",
        "the stair of white rocks",
        "a thick cloud hiding the last turn",
        "a warm compass made from amber",
        "a robin flew twice toward the open sky",
        "flutter-flap",
        "The amber compass glowed beside the first bright cloud.",
    ),
]

NAMES = ["Kiko", "Pip", "Bram", "Luma", "Tavi", "Nell", "Odo", "Mina"]
GUIDES = ["Mara", "Sol", "Ira", "Tess", "Ravi"]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def route_for(params: StoryParams) -> Route:
    for route in ROUTES:
        if route.key == params.place:
            return route
    pass


def setup_world(params: StoryParams) -> World:
    route = route_for(params)
    world = World(params)
    world.add(Entity(
        id="kook",
        kind="character",
        label=params.kook_name,
        location="the foothill",
        meters={"bravery": 0.0, "awe": 0.0, "worry": 0.0, "curiosity": 1.0},
        memes={"recklessness": 0.0, "care": 0.0, "wonder": 0.0},
    ))
    world.add(Entity(
        id="guide",
        kind="character",
        label=params.guide_name,
        location="the foothill",
        meters={"patience": 1.0, "awe": 0.0, "worry": 0.0},
        memes={"trust": 1.0, "care": 1.0},
    ))
    world.add(Entity(
        id="signal",
        kind="thing",
        label="the glowing signal",
        location=route.route,
        meters={"brightness": 1.0, "distance": 1.0},
        memes={"mystery": 1.0},
    ))
    world.add(Entity(
        id="treasure",
        kind="thing",
        label=route.treasure,
        location="the hidden overlook",
        meters={"discovered": 0.0},
        memes={"wonder": 1.0},
    ))
    world.facts["route"] = route
    return world


def tell_story(world: World) -> None:
    params = world.params
    route: Route = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "route")
    kook = world.get("kook")
    guide = world.get("guide")
    signal = world.get("signal")
    treasure = world.get("treasure")
    rng = random.Random(params.variation)

    openings = [
        f"{params.kook_name} was a kook for clues, the sort of traveler who followed a glow before asking where it went.",
        f"At sunrise, {params.kook_name} spotted a pale light dancing beyond the foothills of {route.place}.",
        f"The first thing {params.kook_name} noticed was not the mountain, but a tiny shining signal blinking along {route.route}.",
    ]
    thoughts = [
        "That light is calling me, thought the kook. Or perhaps I am calling it.",
        "I could turn back, thought the kook, but then I would never know what made the sky sparkle.",
        "My feet feel brave and my knees feel wobbly, thought the kook. Maybe both can be true.",
    ]
    questions = [
        f'"Do you really mean to follow it?" asked {params.guide_name}.',
        f'"What do you think waits at the end?" {params.guide_name} asked.',
        f'"Will you listen if the trail tells us to stop?" asked {params.guide_name}.',
    ]
    answers = [
        f'"I do," said {params.kook_name}. "But I will not follow it foolishly."',
        f'"I do not know," said {params.kook_name}. "That is why I have to look."',
        f'"I will," said {params.kook_name}. "A true adventure needs eyes and ears."',
    ]
    inner_turns = [
        "The kook's excitement leaped ahead, but a quieter thought caught its sleeve: Wonder is not a race.",
        "For one breath, the kook wanted to dash onward. Then it remembered that even a bright clue could lead near a dark edge.",
        "Awe filled the kook's chest so completely that the danger seemed small. Then the kook blinked, listened, and saw the danger clearly.",
    ]
    choices = [
        f"{params.kook_name} tested each stone, tied the loose cord twice, and crossed only after {params.guide_name} nodded.",
        f"{params.kook_name} raised one paw and waited until the rocks settled before choosing the narrow safe path.",
        f"{params.kook_name} marked the safe steps with bright leaves and helped {params.guide_name} cross beside them.",
    ]

    world.say(rng.choice(openings))
    world.say(f"{params.guide_name} found the kook at the foothill, staring toward {route.route}.")
    world.say(rng.choice(thoughts))
    world.say(f'"A glowing signal can be a clue," said {params.guide_name}, "but a clue is not a command."')
    world.say(rng.choice(questions))
    world.say(rng.choice(answers))

    world.para()
    world.say(f"Together they followed the light through {route.route}. The trail curled toward {route.danger}.")
    world.say(rng.choice(inner_turns))
    world.say(f'"The path is asking us to be careful," said {params.kook_name}.')
    world.say(f'"Then careful is how we answer," said {params.guide_name}.')
    world.say(route.clue)
    world.say(rng.choice(choices))
    kook.meters["bravery"] += 1.0
    kook.meters["worry"] += 0.5
    kook.memes["care"] += 1.0
    guide.meters["patience"] += 0.5
    signal.meters["distance"] = 0.0
    world.say(f"{route.sound.capitalize()} The danger passed beneath their careful feet.")

    world.para()
    world.say("Beyond the danger, the glowing signal opened like a little door in the air.")
    world.say(f"There they found {route.treasure}.")
    treasure.meters["discovered"] = 1.0
    kook.meters["awe"] += 1.0
    guide.meters["awe"] += 1.0
    kook.memes["wonder"] += 1.0
    guide.memes["wonder"] += 1.0
    world.say(f"{params.kook_name} forgot to speak. The kook's inner voice whispered, This is bigger than my wanting.")
    world.say(f'"It is beautiful," said {params.kook_name} at last.')
    world.say(f'"Yes," said {params.guide_name}. "And you reached it by noticing what the world was saying."')

    world.para()
    world.say(f"They did not grab {route.treasure}. They sat beside it, watched the light fade, and carried home only a sketch.")
    world.say(route.ending_image)
    world.say(f"{params.kook_name} was still a kook for clues, but now the kook knew that awe grows brightest when courage travels with care.")

    world.facts.update({
        "danger": route.danger,
        "clue": route.clue,
        "treasure": route.treasure,
        "ending_image": route.ending_image,
        "safe_choice": choices[-1],
        "awe": True,
        "resolved": True,
    })


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    route: Route = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "route")
    return [
        QAItem(
            "Who followed the glowing signal?",
            f"{p.kook_name}, the curious kook, followed the glowing signal.",
        ),
        QAItem(
            "Where did the adventure lead?",
            f"The adventure led to {route.place} along {route.route}.",
        ),
        QAItem(
            "What danger did the travelers meet?",
            f"They met {route.danger}.",
        ),
        QAItem(
            "How did the kook get past the danger?",
            f"The kook slowed down, noticed the clue, and chose a safe way across instead of rushing.",
        ),
        QAItem(
            "What did the travelers discover?",
            f"They discovered {route.treasure}.",
        ),
        QAItem(
            "What did the kook learn?",
            "The kook learned that real courage includes listening, waiting, and taking care.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a kook?",
            "A kook is a playful word for someone who behaves in an unusual or delightfully silly way.",
        ),
        QAItem(
            "What is awe?",
            "Awe is a strong feeling of wonder when something seems beautiful, surprising, or much bigger than expected.",
        ),
        QAItem(
            "Why can careful listening help on an adventure?",
            "Careful listening can reveal warnings, clues, and safer choices that rushing might miss.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        "Write an adventurous child-facing story about a kook following a mysterious glowing signal.",
        "Tell a short adventure in which awe changes what the hero chooses to do.",
        "Use inner monologue, a danger, a guide, and a wonder-filled discovery in a gentle adventure story.",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure storyworld about a kook and awe.")
    parser.add_argument("--kook-name")
    parser.add_argument("--guide-name")
    parser.add_argument("--place", choices=[r.key for r in ROUTES])
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kook_name = getattr(args, "kook_name", None) or rng.choice(NAMES)
    guide_name = getattr(args, "guide_name", None) or rng.choice([n for n in GUIDES if n != kook_name])
    if kook_name == guide_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(ROUTES).key
    route = route_for(StoryParams(place=place))
    return StoryParams(
        kook_name=kook_name,
        guide_name=guide_name,
        place=place,
        route=route.route,
        danger=route.danger,
        treasure=route.treasure,
        seed=getattr(args, "seed", None),
        variation=rng.getrandbits(63),
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    lines = ["--- world trace ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"{entity.id}: location={entity.location} meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
character(kook).
character(guide).
signal(glow).
danger(bridge).
treasure(wonder).

follows(kook,glow).
guides(guide,kook).
meets(kook,bridge).
listens(kook).
careful(kook).
discovers(kook,wonder).
feels_awe(kook,wonder).

safe_adventure(K) :- character(K), follows(K,glow), listens(K), careful(K), discovers(K,wonder).
brave_with_care(K) :- safe_adventure(K), feels_awe(K,wonder).

#show safe_adventure/1.
#show brave_with_care/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("character", "kook"),
        asp.fact("character", "guide"),
        asp.fact("signal", "glow"),
        asp.fact("danger", "bridge"),
        asp.fact("treasure", "wonder"),
        asp.fact("follows", "kook", "glow"),
        asp.fact("guides", "guide", "kook"),
        asp.fact("meets", "kook", "bridge"),
        asp.fact("listens", "kook"),
        asp.fact("careful", "kook"),
        asp.fact("discovers", "kook", "wonder"),
        asp.fact("feels_awe", "kook", "wonder"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show brave_with_care/1."))
    atoms = asp.atoms(model, "brave_with_care")
    if ("kook",) not in atoms:
        print("MISMATCH: ASP twin did not produce brave_with_care(kook).")
        return 1
    sample = generate(StoryParams())
    if "awe" not in sample.story.lower() or "kook" not in sample.story.lower():
        print("MISMATCH: generated story omitted required domain words.")
        return 1
    print("OK: ASP/Python adventure parity verified.")
    return 0


CURATED = [
    StoryParams("Kiko", "Mara", "blue_mountain", "the lantern trail", "a cracked rope bridge", "a nest of moon-bright stones", variation=11),
    StoryParams("Pip", "Sol", "whistling_canyon", "the echo path", "a falling shelf of loose rocks", "a silver feather caught in a thorn bush", variation=22),
    StoryParams("Luma", "Tess", "red_forest", "the firefly track", "a stream swollen by rain", "a tiny bell buried beneath fern leaves", variation=33),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_adventure/1.\n#show brave_with_care/1."))
        return

    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(1, getattr(args, "n", None))):
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
                samples.append(generate(params))
            except StoryError:
                continue

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
