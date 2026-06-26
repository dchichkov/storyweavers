#!/usr/bin/env python3
"""
A standalone story world: a small mythic domain about a hopper, a corpus, and
the work of acclimating to strange sound effects after a misunderstanding.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    corpus: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
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
class Place:
    name: str
    atmosphere: str
    echoes: bool = False
    mythic: bool = True
    sound_likes: list[str] = field(default_factory=list)
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
class Sound:
    id: str
    label: str
    verb: str
    onomatopoeia: str
    source: str
    volume: int
    startle: float
    soothe: float
    tags: set[str] = field(default_factory=set)
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
    sound: str
    protagonist: str
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


PLACES = {
    "grove": Place(name="the moonlit grove", atmosphere="silver leaves and old roots", echoes=True, sound_likes=["whispers", "drums"]),
    "library": Place(name="the quiet archive", atmosphere="rows of tall shelves and dust-gold lamps", echoes=True, sound_likes=["pages", "footsteps"]),
    "shore": Place(name="the tide shore", atmosphere="salt air and black stones", echoes=True, sound_likes=["waves", "shells"]),
}

SOUNDS = {
    "bong": Sound(id="bong", label="a deep bong", verb="bong", onomatopoeia="BONG", source="bronze bell", volume=8, startle=0.7, soothe=0.2, tags={"sound_effect", "misunderstanding"}),
    "clatter": Sound(id="clatter", label="a bright clatter", verb="clatter", onomatopoeia="CLATTER", source="iron cups", volume=6, startle=0.5, soothe=0.4, tags={"sound_effect"}),
    "whirr": Sound(id="whirr", label="a soft whirr", verb="whirr", onomatopoeia="WHIRR", source="wind fan", volume=4, startle=0.3, soothe=0.6, tags={"sound_effect"}),
    "boom": Sound(id="boom", label="a far boom", verb="boom", onomatopoeia="BOOM", source="storm drum", volume=9, startle=0.8, soothe=0.1, tags={"sound_effect", "misunderstanding"}),
}

HEROES = ["hopper", "sprout", "ember", "wren"]
HERO_TRAITS = ["curious", "tender", "brave", "small", "patient", "dreamy"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def to_adj(name: str) -> str:
    return {"hopper": "hopper", "sprout": "sprightly", "ember": "ember-bright", "wren": "wren-small"}.get(name, name)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"In {world.place.name}, there lived {hero.phrase}, who was known as {hero.label}."
    )
    world.say(
        f"{hero.label.capitalize()} was a {world.facts['trait']} little hopper, and the old stones remembered its leaps."
    )


def myth_setup(world: World, hero: Entity, corpus: Entity) -> None:
    world.say(
        f"Below the shelves rested the corpus, a hush-filled treasury of songs, sayings, and little laws."
    )
    world.say(
        f"{hero.label.capitalize()} loved to listen, but it did not yet know how to dwell beside the corpus without fear."
    )


def misunderstanding(world: World, hero: Entity, sound: Sound, corpus: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + sound.startle
    corpus.memes["quiet"] = corpus.memes.get("quiet", 0) + 1
    world.say(
        f"Then the bronze source gave a sudden {sound.onomatopoeia}, and {hero.label} mistook the sound for an angry omen."
    )
    world.say(
        f"It thought the corpus had woken to judge it, because the shelves echoed like a giant throat."
    )


def acclimate(world: World, hero: Entity, sound: Sound, corpus: Entity) -> None:
    hero.memes["understanding"] = hero.memes.get("understanding", 0) + sound.soothe + 0.7
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0) - 0.6)
    hero.meters["near_corpus"] = hero.meters.get("near_corpus", 0) + 1
    world.say(
        f"An elder of the grove laughed softly and explained that the {sound.label} was only the {sound.source} speaking."
    )
    world.say(
        f"{hero.label.capitalize()} listened again and again until its breathing matched the rhythm of the room."
    )
    world.say(
        f"At last it had acclimated: the corpus no longer seemed like a wrathful giant, but like a patient keeper of stories."
    )


def ending(world: World, hero: Entity, sound: Sound, corpus: Entity) -> None:
    world.say(
        f"When the {sound.verb} came again, {hero.label} did not flee."
    )
    world.say(
        f"It sat beside the corpus in peace, and the myth of the alarm became a lesson about listening twice before fearing once."
    )


def predict_acclimate(sound: Sound) -> bool:
    return sound.soothe > 0.25


def tell(place: Place, sound: Sound, hero_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="hopper",
        label=hero_name,
        phrase=f"a small hopper named {hero_name}",
    ))
    corpus = world.add(Entity(
        id="corpus",
        kind="thing",
        type="corpus",
        label="the corpus",
        phrase="the corpus of old stories",
    ))
    world.facts.update(hero=hero, corpus=corpus, sound=sound, place=place, trait=random.choice(HERO_TRAITS))

    intro(world, hero)
    world.para()
    myth_setup(world, hero, corpus)
    world.para()
    misunderstanding(world, hero, sound, corpus)
    world.para()
    acclimate(world, hero, sound, corpus)
    ending(world, hero, sound, corpus)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a young child about a hopper, a corpus, and a sound effect like "{f["sound"].onomatopoeia}".',
        f"Tell a gentle mythic story in which {f['hero'].label} misunderstands a sound, then acclimates beside the corpus.",
        f"Write a small myth where a {f['place'].name} teaches a hopper how to listen after a strange {f['sound'].verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sound = _safe_fact(world, f, "sound")
    return [
        QAItem(
            question=f"Who is the story about in {f['place'].name}?",
            answer=f"It is about {hero.phrase}, a little hopper named {hero.label}.",
        ),
        QAItem(
            question="What did the hopper misunderstand?",
            answer=f"It misunderstood the {sound.label} and thought the corpus was angry.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The hopper calmed down, learned the sound was harmless, and acclimated to the corpus.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a corpus?",
            answer="A corpus is a collection of old texts or stories gathered together in one place.",
        ),
        QAItem(
            question="What does acclimate mean?",
            answer="To acclimate means to get used to a new place, feeling, or sound little by little.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a made or special sound that helps tell a story or create a mood.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = []
    parts.append("== (1) Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for sound in SOUNDS:
            combos.append((place, sound, "hopper"))
    return combos


ASP_RULES = r"""
place(P) :- place_fact(P).
sound(S) :- sound_fact(S).

misunderstanding(P,S,H) :- place(P), sound(S), hopper(H), startling(S).
acclimate(P,S,H) :- misunderstanding(P,S,H), soothing(S).

valid_story(P,S,H) :- place(P), sound(S), hopper(H), acclimate(P,S,H).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound_fact", sid))
        if s.startle >= 0.5:
            lines.append(asp.fact("startling", sid))
        if s.soothe >= 0.25:
            lines.append(asp.fact("soothing", sid))
    lines.append(asp.fact("hopper", "hopper"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if cl:
        cl = {(a, b, c) for (a, b, c) in cl}
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world of a hopper, a corpus, and acclimation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    sound = getattr(args, "sound", None) or rng.choice(list(SOUNDS))
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "sound", None) and getattr(args, "sound", None) not in SOUNDS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not predict_acclimate(_safe_lookup(SOUNDS, sound)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(HEROES).capitalize()
    return StoryParams(place=place, sound=sound, protagonist=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(SOUNDS, params.sound), params.protagonist)
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


CURATED = [
    StoryParams(place="grove", sound="boom", protagonist="Hopper"),
    StoryParams(place="library", sound="bong", protagonist="Sprout"),
    StoryParams(place="shore", sound="whirr", protagonist="Wren"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
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
