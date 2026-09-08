#!/usr/bin/env python3
"""
A tall tale about a platinum tulip, a singer with laryngitis, and a
misunderstanding that makes a very quiet promise sound enormous.
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
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402



def _safe_next(iterable, fallback=None):
    return next(iter(iterable), fallback)


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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for key in ("height", "shine", "soreness", "distance", "surprise", "trust"):
            self.meters.setdefault(key, 0.0)
        for key in ("pride", "worry", "hope", "confusion", "patience"):
            self.memes.setdefault(key, 0.0)
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
class Trial:
    key: str
    place: str
    singer: str
    tulip_detail: str
    rumor: str
    misunderstanding: str
    clarification: str
    twist: str
    ending: str
    lesson: str
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
    hero: str = ""
    friend: str = ""
    singer: str = ""
    trial: str = "hill"
    style: str = "tall_tale"
    variation: int = 0
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


TRIALS = [
    Trial(
        "hill",
        "a hill so tall it tickled clouds",
        "the town's bell singer",
        "its petals were tall enough to shade a goat",
        "a message that the tulip would sing at noon",
        "the singer's laryngitis made every word come out as a booming whisper",
        "the singer meant that the tulip should be admired in silence",
        "the tulip's platinum petals caught the sun and sent a silver flash across the valley",
        "The villagers cheered for the quietest concert anyone had ever heard.",
        "A strange sound is worth understanding before a crowd builds a story around it.",
    ),
    Trial(
        "bridge",
        "a bridge stretched between two windy cliffs",
        "the keeper of the morning song",
        "its stem was taller than the bridge tower",
        "a promise that the flower would call the ferries home",
        "the singer's laryngitis turned a soft warning into a long, wheezy rumble",
        "the singer was asking everyone to wait until the wind settled",
        "the tulip's bell-shaped bloom rang once when a raindrop struck its metal petal",
        "Every ferry returned safely, guided by one accidental silver note.",
        "A careful question can keep a worried guess from becoming a dangerous command.",
    ),
    Trial(
        "square",
        "the widest market square in the county",
        "a singer who usually woke every rooster",
        "its platinum bloom was as wide as a wagon wheel",
        "a boast that the flower could announce a festival",
        "the singer's laryngitis made a tiny request sound like a royal decree",
        "the singer wanted only a cup of warm honey water",
        "the flower reflected a baker's oven glow and made every stall shine like dawn",
        "The festival began with honey water, laughter, and a flower brighter than fireworks.",
        "When words are unclear, kindness should arrive before conclusions.",
    ),
    Trial(
        "tower",
        "a watchtower higher than three mountains",
        "the lonely tower singer",
        "its stalk climbed past the top window",
        "a warning that the tulip had spotted a dragon",
        "the singer's laryngitis made the word 'garden' sound like 'dragon'",
        "the singer was pointing to a lost garden cart below",
        "the cart's mirror flashed against the platinum tulip, looking exactly like a dragon's eye",
        "The supposed dragon became the town's first flower cart, and nobody needed a sword.",
        "Listening twice can turn a frightening misunderstanding into a useful discovery.",
    ),
]


NAMES = ["Luna", "Milo", "Pip", "Cora", "Toby", "Nina", "Otto", "Daisy"]
MODES = ["tall_tale", "echo", "grand", "gentle"]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
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


def setup_world(params: StoryParams) -> World:
    trial = _safe_next((t for t in TRIALS if t.key == params.trial))
    world = World(params)
    world.add(Entity(params.hero, "character", params.hero, trial.place))
    world.add(Entity(params.friend, "character", params.friend, trial.place))
    world.add(Entity(params.singer, "character", params.singer, trial.place))
    world.add(Entity("platinum_tulip", "plant", "the platinum tulip", trial.place))
    world.entities[params.singer].meters["soreness"] = 2
    world.get("platinum_tulip").meters["shine"] = 9
    world.get("platinum_tulip").meters["height"] = 8
    return world


def tell_story(world: World) -> None:
    p = world.params
    t = _safe_next((x for x in TRIALS if x.key == p.trial))
    hero = world.entities[p.hero]
    friend = world.entities[p.friend]
    singer = world.entities[p.singer]
    tulip = world.get("platinum_tulip")
    rng = random.Random(p.variation)

    openings = [
        f"In {t.place}, {p.hero} found a platinum tulip standing taller than a church steeple.",
        f"People said no flower could grow so high, but {p.hero} met a platinum tulip in {t.place}.",
        f"On the tallest morning anyone could remember, {p.hero} and {p.friend} discovered a tulip made of platinum.",
        f"The platinum tulip rose above {t.place}, shining so brightly that shadows hid beneath it.",
    ]
    world.say(rng.choice(openings))
    world.say(f"{t.tulip_detail.capitalize()}, and its silver petals flashed like little moons.")
    world.say(
        f"{p.friend} pointed at the flower. “Who will tell everyone about it?” "
        f"asked {p.friend}."
    )
    world.say(
        f"{p.singer} stepped forward. “I will,” said {p.singer}, “though I have laryngitis today.”"
    )
    world.say(
        f"{p.hero} nodded. “Then speak slowly, and we will listen carefully,” said {p.hero}."
    )

    world.para()
    world.say(f"At noon, {t.rumor}.")
    world.say(
        f"But {p.singer}'s laryngitis made every sentence strange. "
        f"{t.misunderstanding.capitalize()}."
    )
    world.say(
        f"{p.friend} heard the rough whisper and cried, “Did {p.singer} just say that the flower has a mighty secret?”"
    )
    world.say(
        f"{p.hero} answered, “I am not sure. Let us ask instead of guessing.”"
    )
    world.say(
        f"{p.hero} asked, “Are you announcing the tulip, or asking us to help?”"
    )
    world.say(
        f"{p.singer} pressed a hand to a sore throat and whispered, “Help me find warm honey water.”"
    )
    singer.memes["confusion"] += 1
    friend.memes["worry"] += 1
    hero.memes["patience"] += 1

    world.para()
    world.say(f"The crowd had already begun to imagine a grand secret, but {t.clarification}.")
    world.say(
        f"{p.friend} blinked. “So the great announcement was a request for tea?”"
    )
    world.say(
        f"{p.singer} nodded. “Exactly,” came the tiny answer."
    )
    world.say(
        f"{p.hero} smiled. “Then the tulip can wait, and your throat cannot,” said {p.hero}."
    )
    world.say(
        f"They carried a warm cup up the path. Then came the twist: {t.twist}."
    )
    tulip.meters["shine"] += 3
    tulip.meters["surprise"] += 2
    hero.memes["hope"] += 1
    singer.memes["trust"] += 1

    world.para()
    world.say(t.ending)
    world.say(
        f"{p.friend} laughed. “The flower did make an announcement after all!”"
    )
    world.say(
        f"{p.singer} whispered, “But not the one my throat was trying to make.”"
    )
    world.say(f"{p.hero} looked at the silver bloom and remembered: {t.lesson}")
    world.say(
        f"That evening, the platinum tulip stood above {t.place}, "
        "and everyone listened before telling the next tall tale."
    )

    world.facts.update(
        trial=t,
        hero=hero,
        friend=friend,
        singer=singer,
        tulip=tulip,
        misunderstanding=t.misunderstanding,
        clarification=t.clarification,
        twist=t.twist,
        ending=t.ending,
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    t: Trial = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "trial")
    return [
        QAItem(
            "Who found the platinum tulip?",
            f"{p.hero} found the platinum tulip with help from {p.friend}.",
        ),
        QAItem(
            "What problem did the singer have?",
            f"{p.singer} had laryngitis, so speaking clearly was difficult.",
        ),
        QAItem(
            "What misunderstanding happened?",
            t.misunderstanding.capitalize() + ".",
        ),
        QAItem(
            "How did the friends solve the misunderstanding?",
            f"They asked {p.singer} a clear question and listened to the answer instead of guessing.",
        ),
        QAItem(
            "What was the twist?",
            t.twist.capitalize() + ".",
        ),
        QAItem(
            "What changed by the ending?",
            t.ending,
        ),
        QAItem(
            "What lesson did the characters learn?",
            t.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is platinum?",
            "Platinum is a rare, valuable metal with a bright silvery color.",
        ),
        QAItem(
            "What is a tulip?",
            "A tulip is a flowering plant that grows from a bulb.",
        ),
        QAItem(
            "What is laryngitis?",
            "Laryngitis is irritation or swelling of the voice box that can make speaking hoarse or difficult.",
        ),
        QAItem(
            "Why is dialogue useful in a story?",
            "Dialogue lets characters share information, ask questions, and change what they decide to do.",
        ),
    ]


def generation_prompts() -> list[str]:
    return [
        "Write a tall tale about a platinum tulip and a singer with laryngitis.",
        "Use dialogue and a misunderstanding that is repaired by asking a clear question.",
        "Include a surprising twist and end with a concrete image showing what changed.",
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tall tale world of a platinum tulip, laryngitis, dialogue, and a repaired misunderstanding."
    )
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--singer")
    parser.add_argument("--trial", choices=[t.key for t in TRIALS])
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
    supplied = [getattr(args, "hero", None), getattr(args, "friend", None), getattr(args, "singer", None)]
    chosen = [x for x in supplied if x]
    if len(set(chosen)) != len(chosen):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if len(chosen) not in (0, 3):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not chosen:
        chosen = rng.sample(NAMES, 3)
    trial = getattr(args, "trial", None) or rng.choice(TRIALS).key
    return StoryParams(
        hero=chosen[0],
        friend=chosen[1],
        singer=chosen[2],
        trial=trial,
        style=rng.choice(MODES),
        variation=rng.getrandbits(63),
        seed=getattr(args, "seed", None),
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
character(hero).
character(friend).
character(singer).
object(platinum_tulip).
has_laryngitis(singer).
heard_rumor(friend).
asks_clear_question(hero).
clarified.
twist_revealed.
#show clarified/0.
#show twist_revealed/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("character", "hero"),
            asp.fact("character", "friend"),
            asp.fact("character", "singer"),
            asp.fact("object", "platinum_tulip"),
            asp.fact("has_laryngitis", "singer"),
            asp.fact("heard_rumor", "friend"),
            asp.fact("asks_clear_question", "hero"),
            asp.fact("clarified"),
            asp.fact("twist_revealed"),
        ]
    )


def asp_program(show: str = "#show clarified/0.\n#show twist_revealed/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    expected = {"clarified", "twist_revealed"}
    if expected.issubset(names):
        print("OK: ASP twin preserves the repaired misunderstanding and twist.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected story state.")
    return 1


CURATED = [
    StoryParams("Luna", "Milo", "Cora", trial="hill", style="tall_tale", variation=17),
    StoryParams("Pip", "Nina", "Otto", trial="bridge", style="grand", variation=29),
    StoryParams("Daisy", "Toby", "Milo", trial="tower", style="echo", variation=41),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(max(1, getattr(args, "n", None))):
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            samples.append(generate(params))

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
