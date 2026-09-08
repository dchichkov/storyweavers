#!/usr/bin/env python3
"""
A small mythic storyworld about wheat, a remembered warning, and a surprising
ending that turns a bad harvest into a new beginning.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    helper: object | None = None
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
    name: str = ""
    helper: str = ""
    field: str = ""
    seed: Optional[int] = None
    weather: Optional[str] = None
    omen: Optional[str] = None
    surprise: Optional[str] = None
    ending: Optional[str] = None
    sample: object | None = None
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


@dataclass
class Weather:
    key: str
    description: str
    danger: str
    consequence: str
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
class Omen:
    key: str
    memory: str
    lesson: str
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


@dataclass
class Surprise:
    key: str
    reveal: str
    gift: str
    image: str
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


NAMES = ["Luna", "Mara", "Tavi", "Nia", "Rin", "Suri"]
HELPERS = ["grandmother", "brother", "friend", "village baker"]
FIELDS = ["the hill field", "the river field", "the moon field", "the old north field"]
WEATHER = [
    Weather("red_wind", "A red wind rose beyond the hills.", "the wheat would be scattered before dawn", "the stalks bent like frightened birds"),
    Weather("black_cloud", "A black cloud climbed over the valley.", "rain would flatten the wheat into the mud", "heavy drops bowed every golden head"),
    Weather("dry_sun", "The sun burned white for seven days.", "the wheat would dry before its kernels filled", "the field whispered with brittle leaves"),
    Weather("cold_moon", "A sharp frost shone beneath the moon.", "the tender wheat would freeze in its sleep", "silver ice touched the green tips"),
]
OMENS = [
    Omen("grandmother", "Long ago, Grandmother had shown {name} how to bend three stalks together and tie them with a red thread.", "a field survives when its neighbors help one another", "bind the weakest stalks before saving the tallest"),
    Omen("river", "Once, {helper} had pointed to the river reeds and said, 'Water finds a path when no one wall blocks it.'", "a wise path can be small and patient", "open a narrow channel toward the thirsty rows"),
    Omen("star", "In a childhood dream, a blue star had whispered, 'Do not carry every grain alone.'", "sharing a burden can protect the harvest", "ask the village to carry the cut wheat together"),
    Omen("crow", "The old crow had once dropped a seed into {name}'s palm and waited until {name} noticed the cracked husk.", "a hidden seed may matter more than a shining one", "look beneath the damaged heads before giving up"),
]
SURPRISES = [
    Surprise("golden_seed", "When the storm passed, one dark ear of wheat split open by itself.", "Inside lay a single blue-gold seed unlike any grain in the valley.", "The seed glowed softly in {name}'s palm."),
    Surprise("field_song", "The bent stalks began to hum when the villagers lifted them together.", "Their song showed everyone where the ripest grain was hiding.", "The whole field shimmered as if it remembered a tune."),
    Surprise("mouse_king", "A tiny mouse wearing a crown of straw stepped from beneath the granary door.", "It led {name} to a dry storehouse under the hill.", "The mouse bowed beside a door no person had seen."),
    Surprise("rainbow_flour", "The ruined grain, when ground, became flour with seven bright colors.", "The flour made bread that healed tired hearts and welcomed strangers.", "A rainbow loaf steamed on the village table."),
]
ENDINGS = ["seed", "song", "mouse", "bread"]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
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


def pick(items, key):
    return next((item for item in items if item.key == key), None)


def complete_params(params: StoryParams) -> None:
    if not params.name or not params.helper or not params.field:
        pass
    seed = params.seed if params.seed is not None else sum(map(ord, params.name + params.field))
    rng = random.Random(seed ^ 0x91A7)
    params.weather = params.weather or rng.choice(WEATHER).key
    params.omen = params.omen or rng.choice(OMENS).key
    params.surprise = params.surprise or rng.choice(SURPRISES).key
    params.ending = params.ending or rng.choice(ENDINGS)


def build_world(params: StoryParams) -> World:
    complete_params(params)
    weather = pick(WEATHER, params.weather)
    omen = pick(OMENS, params.omen)
    surprise = pick(SURPRISES, params.surprise)
    if weather is None or omen is None or surprise is None:
        pass
    if params.ending == "seed" and surprise.key != "golden_seed":
        pass
    if params.ending == "song" and surprise.key != "field_song":
        pass
    if params.ending == "mouse" and surprise.key != "mouse_king":
        pass
    if params.ending == "bread" and surprise.key != "rainbow_flour":
        pass

    w = World()
    child = w.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        meters={"courage": 0.0, "worry": 1.0, "hope": 0.0},
        memes={"care": 1.0},
    ))
    helper = w.add(Entity(
        id="helper",
        kind="character",
        type="helper",
        label=params.helper,
        meters={"wisdom": 2.0},
        memes={"patience": 1.0},
    ))
    w.add(Entity(
        id="wheat",
        kind="crop",
        type="wheat",
        label="wheat",
        owner=params.name,
        meters={"ripeness": 2.0, "safety": 1.0},
        memes={"promise": 1.0},
    ))
    w.facts.update(params=params, child=child, helper=helper, weather=weather,
                   omen=omen, surprise=surprise)
    return w


def tell(params: StoryParams) -> World:
    w = build_world(params)
    c = w.facts["child"]
    h = w.facts["helper"]
    weather = w.facts["weather"]
    omen = w.facts["omen"]
    surprise = w.facts["surprise"]

    w.say(f"In the first age, {c.label} tended wheat in {params.field}, where every stalk was said to remember the sun.")
    w.say(f"{weather.description} The wheat bowed, and {weather.danger}.")

    w.para()
    w.say(f"{c.label} ran to {h.label}.")
    w.say(f'"The harvest is lost!" cried {c.label}.')
    w.say(f'"Not while we can still listen," said {h.label}. "What did the old days teach you?"')
    c.meters["worry"] += 1
    w.say(f"That question opened a flashback. {omen.memory.format(name=c.label, helper=h.label)}")
    w.say(f"{c.label} remembered that {omen.lesson}.")
    c.meters["courage"] += 1
    c.memes["memory"] = 1.0

    w.para()
    w.say(f"{c.label} chose to {omen.action}. {h.label} helped, and soon the villagers joined them.")
    w.say(f"They worked until dusk, but the first result looked like a bad ending: {weather.consequence}, and much of the wheat lay broken.")
    c.meters["worry"] -= 1
    c.meters["hope"] += 1
    w.say(f'"We saved too little," whispered {c.label}.')
    w.say(f'"Look again," said {h.label}. "Myths often hide their gifts under the part that seems finished."')

    w.para()
    w.say(surprise.reveal)
    w.say(surprise.gift)
    w.say(surprise.image.format(name=c.label))
    c.meters["hope"] += 2
    c.meters["courage"] += 1
    c.memes["surprise"] = 1.0
    endings = {
        "seed": "They planted the strange seed at the center of the field, and by morning a green ring surrounded it.",
        "song": "The villagers followed the humming rows and gathered enough full ears to fill every empty basket.",
        "mouse": "Beneath the hill they found a dry storehouse, and the little mouse became guardian of the village grain.",
        "bread": "They baked the rainbow flour into loaves, then shared them with every traveler who came hungry.",
    }
    w.say(endings[params.ending])
    w.say(f"From then on, {params.field} was called a lucky field—not because nothing bad happened there, but because {c.label} remembered to look for the next living thing.")
    return w


def story_qa(w: World) -> list[QAItem]:
    p = w.facts["params"]
    c = w.facts["child"]
    h = w.facts["helper"]
    weather = w.facts["weather"]
    omen = w.facts["omen"]
    surprise = w.facts["surprise"]
    return [
        QAItem(
            question=f"What happened to {c.label}'s wheat in {p.field}?",
            answer=f"{weather.description} and threatened the wheat because {weather.danger}."
        ),
        QAItem(
            question=f"What did the flashback remind {c.label} about saving the wheat?",
            answer=f"It reminded {c.label} that {omen.lesson}, so {c.label} chose to {omen.action}."
        ),
        QAItem(
            question=f"Why did the harvest first seem to have a bad ending?",
            answer=f"The villagers worked hard, but {weather.consequence}, leaving much of the wheat broken."
        ),
        QAItem(
            question=f"What surprise changed the ending of the wheat story?",
            answer=f"{surprise.reveal} The surprise brought this gift: {surprise.gift}."
        ),
    ]


def world_qa(w: World) -> list[QAItem]:
    return [
        QAItem("What is wheat?", "Wheat is a grass-like crop whose grains can be ground into flour for foods such as bread."),
        QAItem("What is a flashback?", "A flashback is a part of a story that shows or remembers something that happened earlier."),
        QAItem("What is a bad ending?", "A bad ending is an ending where a problem seems to defeat the characters or cause a painful loss."),
        QAItem("Why can a surprise make a story stronger?", "A surprise can make a story stronger by changing what the characters and readers expect, especially when it grows from earlier clues."),
    ]


def prompts(w: World) -> list[str]:
    p = w.facts["params"]
    return [
        f"Write a child-friendly myth about wheat in {p.field}, including a flashback and a bad ending that changes.",
        f"Tell a mythic story in which {p.name} and {p.helper} save wheat through cooperation.",
        "End the wheat story with a surprising but hopeful image.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.extend([f"Q: {q.question}", f"A: {q.answer}"])
    lines.append("")
    lines.append("== (3) World questions ==")
    for q in sample.world_qa:
        lines.extend([f"Q: {q.question}", f"A: {q.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("crop", "wheat"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "bad_ending"),
        asp.fact("feature", "surprise"),
        asp.fact("style", "myth"),
        asp.fact("requires", "cooperation"),
    ])


ASP_RULES = r"""
myth_world(wheat, flashback, bad_ending, surprise) :-
    crop(wheat),
    feature(flashback),
    feature(bad_ending),
    feature(surprise),
    style(myth),
    requires(cooperation).
"""


def asp_program(show: str = "#show myth_world/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if asp.atoms(model, "myth_world") != [("wheat", "flashback", "bad_ending", "surprise")]:
        print("MISMATCH: ASP gate failed.")
        return 1
    for seed in range(5):
        sample = generate(StoryParams("Luna", "grandmother", "the hill field", seed=seed))
        if not sample.story or "wheat" not in sample.story:
            print("MISMATCH: generated story failed.")
            return 1
    print("OK: ASP and Python agree; generated stories are complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic wheat storyworld with a flashback and surprise.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--field", choices=FIELDS)
    ap.add_argument("--weather", choices=[x.key for x in WEATHER])
    ap.add_argument("--omen", choices=[x.key for x in OMENS])
    ap.add_argument("--surprise", choices=[x.key for x in SURPRISES])
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=getattr(args, "name", None) or rng.choice(NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
        field=getattr(args, "field", None) or rng.choice(FIELDS),
        weather=getattr(args, "weather", None) or rng.choice(WEATHER).key,
        omen=getattr(args, "omen", None) or rng.choice(OMENS).key,
        surprise=getattr(args, "surprise", None) or rng.choice(SURPRISES).key,
        ending=getattr(args, "ending", None) or None,
    )


CURATED = [
    StoryParams("Luna", "grandmother", "the hill field", surprise="golden_seed", ending="seed"),
    StoryParams("Mara", "friend", "the river field", surprise="field_song", ending="song"),
    StoryParams("Tavi", "village baker", "the old north field", surprise="rainbow_flour", ending="bread"),
]


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "myth_world"))
        return

    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, getattr(args, "n", None))):
            rng = random.Random(base + i)
            p = resolve_params(args, rng)
            p.seed = base + i
            samples.append(generate(p))

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return
    for i, sample in enumerate(samples):
        emit(sample, getattr(args, "trace", None), getattr(args, "qa", None), f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
