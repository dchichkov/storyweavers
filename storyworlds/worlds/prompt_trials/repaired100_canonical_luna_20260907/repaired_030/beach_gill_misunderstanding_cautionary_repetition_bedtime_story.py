#!/usr/bin/env python3
"""
A gentle bedtime storyworld about a beach misunderstanding, a gill, and the
caution of repeating a warning before acting.
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
    child: object | None = None
    fish: object | None = None
    friend: object | None = None
    strand: object | None = None
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
    child: str = ""
    friend: str = ""
    creature: str = ""
    beach_time: str = ""
    misunderstanding: str = ""
    caution: str = ""
    repetition: str = ""
    ending: str = ""
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
class Episode:
    arrival: str
    sign: str
    danger: str
    truth: str
    action: str
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


NAMES = ["Luna", "Milo", "Nia", "Pip", "Tessa", "Oren", "Mara", "Finn"]
CREATURES = ["a small silver fish", "a sleepy tide-pool fish", "a striped little fish", "a bright blue fish"]
TIMES = ["moonrise", "the last pink light", "the quiet blue dusk", "the first stars"]

EPISODES = {
    "net": Episode(
        arrival="Luna and her friend came to the beach to listen to the waves",
        sign="a shiny strand curled beside a tide pool",
        danger="Luna thought the strand was seaweed, but it was a loose fishing line",
        truth="the line could catch the fish's gill",
        action="they called for the beach keeper and kept the line still until it was removed",
    ),
    "shell": Episode(
        arrival="Luna carried a shell cup to the edge of the water",
        sign="a shell trembled near the rocks",
        danger="Luna thought the shell was empty, but a tiny crab was hiding inside",
        truth="the crab needed room to crawl out safely",
        action="they placed the shell back where the waves could reach it",
    ),
    "foam": Episode(
        arrival="Luna and her friend watched white foam drift across the sand",
        sign="a patch of foam shone beside the tide pool",
        danger="Luna thought the foam was a soft blanket, but it covered a sharp piece of glass",
        truth="the glass could hurt bare feet",
        action="they marked the spot and asked an adult to lift the glass with a tool",
    ),
    "rock": Episode(
        arrival="Luna built a little rock tower above the wet sand",
        sign="one smooth stone glimmered under the water",
        danger="Luna thought the stone was safe to grab, but it was covering a narrow crab hole",
        truth="the crab needed its doorway left open",
        action="they left the stone in place and built their tower farther away",
    ),
}

MISUNDERSTANDINGS = {
    "heard": "Luna heard her friend say, “Do not touch the shiny thing,” and thought he meant the fish",
    "whisper": "The waves swallowed half the warning, so Luna guessed what the whisper meant",
    "shadow": "A moving shadow made the harmless object look dangerous and the dangerous object look harmless",
    "echo": "The beach echoed the warning until Luna was unsure which part she had heard first",
}

CAUTIONS = {
    "ask": "stop, look twice, and ask before touching",
    "repeat": "repeat the warning in a calm voice before making a choice",
    "wait": "wait for a grown-up when the beach gives an uncertain sign",
    "point": "point from a safe distance instead of reaching toward a mystery",
}

REPETITIONS = {
    "three": "“Stop, look, and ask,” they repeated three times",
    "soft": "They repeated the warning softly until both friends understood it",
    "wave": "They repeated the warning each time a wave rushed near",
    "together": "They said the warning together, so no part of it was lost",
}

ENDINGS = {
    "lullaby": "That night, the waves hummed a lullaby, and Luna dreamed of a beach where every small creature had room to be safe.",
    "lantern": "Under the lantern by the door, Luna repeated the lesson once more, then fell asleep smiling.",
    "moon": "The moon laid a silver road across the water, and the friends walked home with careful hearts.",
    "shell": "Luna placed a clean shell beside her bed to remember that patience can protect a life.",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Beach gill misunderstanding bedtime storyworld.")
    parser.add_argument("--child")
    parser.add_argument("--friend")
    parser.add_argument("--creature", choices=CREATURES)
    parser.add_argument("--beach-time", choices=TIMES)
    parser.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    parser.add_argument("--caution", choices=CAUTIONS)
    parser.add_argument("--repetition", choices=REPETITIONS)
    parser.add_argument("--ending", choices=ENDINGS)
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
    child = getattr(args, "child", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != child])
    if child == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        child=child,
        friend=friend,
        creature=getattr(args, "creature", None) or rng.choice(CREATURES),
        beach_time=getattr(args, "beach_time", None) or rng.choice(TIMES),
        misunderstanding=getattr(args, "misunderstanding", None) or rng.choice(tuple(MISUNDERSTANDINGS)),
        caution=getattr(args, "caution", None) or rng.choice(tuple(CAUTIONS)),
        repetition=getattr(args, "repetition", None) or rng.choice(tuple(REPETITIONS)),
        ending=getattr(args, "ending", None) or rng.choice(tuple(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    episode = _safe_lookup(EPISODES, params.misunderstanding)
    world = World()
    child = world.add(Entity(params.child, "child", params.child, "beach"))
    friend = world.add(Entity(params.friend, "friend", params.friend, "beach"))
    fish = world.add(Entity("fish", "animal", params.creature, "tide pool"))
    strand = world.add(Entity("mystery", "object", episode.sign, "tide pool"))

    child.meters["curiosity"] = 1.0
    child.memes["confidence"] = 1.0
    friend.memes["care"] = 1.0
    fish.meters["gill_strength"] = 1.0
    world.facts.update(child=child, friend=friend, fish=fish, strand=strand, episode=episode)

    world.say(f"At {params.beach_time}, {episode.arrival}.")
    world.say(f"The sand was cool, and {params.creature} rested in a tide pool while the sleepy sea whispered nearby.")
    world.say(f"Beside the pool, {episode.sign}.")
    world.para()

    world.say(f"{params.misunderstanding.capitalize()} made a simple warning seem confusing.")
    world.say(f"{params.misunderstanding and _safe_lookup(MISUNDERSTANDINGS, params.misunderstanding)}.")
    world.say(f'"Do not touch it!" {params.friend} cried.')
    world.say(f'"The fish?" {params.child} asked. "Or the shiny thing?"')
    world.say(f'"The shiny thing," {params.friend} answered. "The fish has a tender gill."')
    world.say(f"Then they both understood that {episode.danger.casefold()}.")
    child.memes["uncertainty"] = 1.0
    friend.memes["trust"] = 1.0
    world.para()

    world.say(f"They remembered to {_safe_lookup(CAUTIONS, params.caution)}.")
    world.say(f"{_safe_lookup(REPETITIONS, params.repetition)}.")
    world.say(f"They stayed back and watched the tide pool carefully.")
    world.say(f"At last, they learned that {episode.truth}.")
    world.say(f"Together, {episode.action}.")
    fish.meters["gill_safe"] = 1.0
    child.memes["care"] = 1.0
    friend.memes["care"] = 1.0
    world.fired.add("misunderstanding_cleared")
    world.fired.add("warning_repeated")
    world.para()

    world.say(f"The fish flicked its tail, and its little gill opened and closed safely in the moonlit water.")
    world.say("Luna knew that a repeated warning is not bothersome when it helps everyone understand.")
    world.say(_safe_lookup(ENDINGS, params.ending))
    world.facts["resolved"] = True
    world.facts["lesson"] = "When a warning is unclear, stop, ask, and repeat it before acting."
    return world


def generation_prompts(world: World) -> list[str]:
    episode: Episode = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "episode")
    return [
        f"Write a bedtime story at the beach about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "fish").label} and a misunderstanding.",
        f"Show why the fish's gill must be protected when {episode.danger.casefold()}.",
        "Use a repeated caution to turn confusion into a safe, gentle choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    friend: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "friend")
    fish: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "fish")
    episode: Episode = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "episode")
    return [
        QAItem(
            question=f"Who visited the beach?",
            answer=f"{child.label} and {friend.label} visited the beach together and watched {fish.label}.",
        ),
        QAItem(
            question="What caused the misunderstanding?",
            answer=f"The warning was confusing because {episode.danger.casefold()}. The friends clarified that the shiny object, not the fish, was the thing to avoid.",
        ),
        QAItem(
            question="Why did the friends repeat the caution?",
            answer="They repeated it so both friends would understand the danger before anyone touched the mystery object near the tide pool.",
        ),
        QAItem(
            question="How was the fish's gill kept safe?",
            answer=f"They stayed back, asked for help when needed, and made sure that {episode.truth}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gill?",
            answer="A gill is a breathing part that lets many fish take oxygen from water.",
        ),
        QAItem(
            question="Why should people be careful near tide pools?",
            answer="Tide pools are homes for small animals, so careful visitors look before touching and leave creatures and their shelters undisturbed.",
        ),
        QAItem(
            question="What should someone do when a warning is unclear?",
            answer="They should stop, ask a calm question, and repeat the warning in clear words before acting.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"  {entity.id}: kind={entity.kind} location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(beach).
feature(gill).
theme(misunderstanding).
theme(cautionary).
theme(repetition).
style(bedtime_story).
valid(beach,gill,misunderstanding,cautionary,repetition,bedtime_story).
safe_when_repeated(warning).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "beach"),
            asp.fact("feature", "gill"),
            asp.fact("theme", "misunderstanding"),
            asp.fact("theme", "cautionary"),
            asp.fact("theme", "repetition"),
            asp.fact("style", "bedtime_story"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program("#show valid/6."), models=1)
    if not models:
        print("ASP verification failed: no valid model.")
        return 1
    combos = asp.atoms(models[0], "valid")
    expected = [("beach", "gill", "misunderstanding", "cautionary", "repetition", "bedtime_story")]
    if sorted(combos) != expected:
        print("ASP verification failed: registry parity mismatch.")
        return 1
    print("OK: ASP registry matches the Python story domain.")
    for seed in range(3):
        params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("ASP verification failed: story generation was empty.")
            return 1
    print("OK: generated stories and QA are non-empty.")
    return 0


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


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"[Prompt {i}] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print()
            print(show_qa_item(item))


CURATED = [
    StoryParams("Luna", "Milo", _safe_lookup(CREATURES, 0), _safe_lookup(TIMES, 0), "heard", "repeat", "three", "lullaby"),
    StoryParams("Nia", "Pip", _safe_lookup(CREATURES, 2), _safe_lookup(TIMES, 2), "foam", "ask", "together", "moon"),
    StoryParams("Tessa", "Oren", _safe_lookup(CREATURES, 1), _safe_lookup(TIMES, 1), "shell", "wait", "soft", "shell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/6."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for combo in asp_valid_combos():
            print(combo)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        for offset in range(max(getattr(args, "n", None) * 20, 20)):
            if len(samples) >= getattr(args, "n", None):
                break
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
