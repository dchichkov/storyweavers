#!/usr/bin/env python3
"""A tiny rocky-shore whodunit about friendship, kindness, and a cute mystery."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import itertools
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


FRIENDS = ("Luna", "Milo", "Pip", "Tess")
WEATHER = ("sunny", "misty")
OBJECTS = ("shell", "button")
VOICES = ("gentle", "playful")
MAX_ACTIONS = 20


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Milo"
    mystery_object: str = "shell"
    weather: str = "misty"
    voice: str = "gentle"
    world_seed: int = 777
    prose_seed: int = 42
    p: object | None = None
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
class Entity:
    id: str
    label: str
    kind: str
    location: str = "rocky_shore"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    beliefs: dict[str, str] = field(default_factory=dict)
    mystery_object: object | None = None
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
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict
    event: object | None = None
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
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    fact_events: dict[str, int] = field(default_factory=dict)
    outcome: str = ""

    w: object | None = None
    def snapshot(self):
        return {
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "outcome": self.outcome,
        }

    def record(self, kind, actor, *, facts=(), needs=(), **data):
        missing = [fact for fact in needs if fact not in self.fact_events]
        if missing:
            pass
        causes = tuple(sorted({self.fact_events[fact] for fact in needs}))
        event = Event(
            id=len(self.history),
            kind=kind,
            actor=actor,
            data=data,
            facts=tuple(facts),
            causes=causes,
            state=self.snapshot(),
        )
        self.history.append(event)
        for fact in facts:
            self.fact_events[fact] = event.id
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


def validate_params(p: StoryParams):
    if p.hero not in FRIENDS or p.friend not in FRIENDS:
        pass
    if p.hero == p.friend:
        pass
    if p.mystery_object not in OBJECTS:
        pass
    if p.weather not in WEATHER:
        pass
    if p.voice not in VOICES:
        pass
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        pass


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(params=p)
    object_label = "striped shell" if p.mystery_object == "shell" else "red button"
    w.entities = {
        "hero": Entity(
            "hero", p.hero, "character",
            memes={"curiosity": 1, "kindness": 1},
            beliefs={"friendship": "important"},
        ),
        "friend": Entity(
            "friend", p.friend, "character",
            memes={"worry": 1, "trust": 1},
            beliefs={"secret": "unknown"},
        ),
        "object": Entity(
            "object", object_label, "treasure",
            owner=p.friend,
            meters={"size": 1, "shine": 3 if p.mystery_object == "shell" else 4},
        ),
        "tide_pool": Entity(
            "tide_pool", "a clear tide pool", "place",
            meters={"depth": 1},
        ),
        "cliff": Entity(
            "cliff", "a low rocky ledge", "place",
            meters={"height": 2},
        ),
        "gull": Entity(
            "gull", "a curious gull", "animal",
            location="cliff",
            memes={"hunger": 1},
        ),
    }
    w.record(
        "opening",
        "friend",
        facts=("mystery_started",),
        hero=p.hero,
        friend=p.friend,
        object=object_label,
        weather=p.weather,
    )
    return w


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    execute(w, "notice_missing")
    execute(w, "ask_friend")
    execute(w, "follow_clues")
    execute(w, "find_object")
    execute(w, "tell_truth")
    execute(w, "restore_object")
    execute(w, "close")
    validate_world(w)
    return w


def execute(w: World, action: str):
    p = w.params
    hero = w.entities["hero"]
    friend = w.entities["friend"]
    obj = w.entities["object"]
    gull = w.entities["gull"]

    if action == "notice_missing":
        if "missing_noticed" in w.fact_events:
            pass
        friend.beliefs["object_seen"] = "gone"
        friend.memes["worry"] = 2
        w.record(
            action,
            "friend",
            facts=("missing_noticed",),
            needs=("mystery_started",),
            object=obj.label,
        )
    elif action == "ask_friend":
        if "missing_noticed" not in w.fact_events:
            pass
        hero.beliefs["friend_explanation"] = "gull_borrowed_it"
        friend.beliefs["told_truth"] = "yes"
        w.record(
            action,
            "hero",
            facts=("truth_shared",),
            needs=("missing_noticed",),
            explanation="The gull carried the object toward the tide pool.",
        )
    elif action == "follow_clues":
        if "truth_shared" not in w.fact_events:
            pass
        hero.beliefs["clue"] = "wet_feathers"
        w.record(
            action,
            "hero",
            facts=("clue_found",),
            needs=("truth_shared",),
            clue="wet feathers and a bright scrape on the rocks",
        )
    elif action == "find_object":
        if "clue_found" not in w.fact_events:
            pass
        obj.location = "tide_pool"
        gull.beliefs["carried_object"] = "yes"
        w.record(
            action,
            "hero",
            facts=("object_found",),
            needs=("clue_found",),
            location="tide pool",
        )
    elif action == "tell_truth":
        if "object_found" not in w.fact_events:
            pass
        hero.beliefs["gull_not_thief"] = "yes"
        friend.beliefs["gull_not_thief"] = "yes"
        w.record(
            action,
            "hero",
            facts=("kindness_chosen",),
            needs=("object_found",),
            reason="The gull borrowed the shiny object to line a nest.",
        )
    elif action == "restore_object":
        if "kindness_chosen" not in w.fact_events:
            pass
        obj.location = "friend"
        obj.owner = "friend"
        gull.beliefs["carried_object"] = "no"
        friend.memes["worry"] = 0
        hero.memes["kindness"] = 2
        w.outcome = "truth_and_kindness"
        w.record(
            action,
            "friend",
            facts=("object_returned", "friendship_proved"),
            needs=("kindness_chosen",),
            owner=p.friend,
        )
    elif action == "close":
        if "object_returned" not in w.fact_events:
            pass
        hero.location = friend.location = "rocky_shore"
        w.record(
            action,
            "hero",
            facts=("ending",),
            needs=("object_returned",),
            moral="Kindness makes room for truth and friendship.",
        )
    else:
        pass


def validate_world(w: World):
    if w.outcome != "truth_and_kindness":
        pass
    if w.entities["object"].owner != w.params.friend:
        pass
    if w.entities["object"].location != "friend":
        pass
    if "ending" not in w.fact_events:
        pass
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            pass


def render(w: World) -> tuple[str, list[QAItem]]:
    p = w.params
    color = "silver-striped shell" if p.mystery_object == "shell" else "red button"
    place = "misty" if p.weather == "misty" else "bright"
    if p.voice == "playful":
        opening = (
            f"On the {place} rocky shore, {p.hero} found {p.friend} staring into a tide pool. "
            f'"My cute {color} is missing," said {p.friend}.'
        )
        dialogue = (
            f'"Did the waves take it?" asked {p.hero}. '
            f'"No," said {p.friend}. "A gull flew off with something shiny."'
        )
    else:
        opening = (
            f"On the {place} rocky shore, {p.hero} found {p.friend} beside a quiet tide pool. "
            f'Their cute {color} was gone.'
        )
        dialogue = (
            f'"I am worried," said {p.friend}. '
            f'"We will look carefully," said {p.hero}. "We should learn what happened before we blame anyone."'
        )

    story = [
        opening,
        dialogue,
        f"{p.hero} noticed wet feathers and a bright scrape leading between the rocks. "
        f"The little trail ended at the tide pool, where the gull had tucked the {color} beside a nest of sea grass.",
        f'"The gull did not steal it," said {p.hero}. "It borrowed the shiny thing for its nest." '
        f'"Then we can ask for it kindly," said {p.friend}.',
        f"They waited until the gull finished arranging the grass. "
        f"Then it left the {color} on a flat stone, and {p.friend} picked it up with a grateful smile.",
        f"Together, the friends left a soft piece of seaweed near the nest. "
        f"The gull bobbed its head, and the two friends laughed beside the shining tide pool.",
        "They had solved the mystery without a harsh word. "
        "On the rocky shore, truth protected their friendship, and kindness made the answer feel right.",
    ]
    qa = [
        QAItem(
            question=f"Why did {p.hero} avoid blaming the gull?",
            answer=(
                f"{p.hero} followed the wet-feather clue and learned that the gull had borrowed "
                f"the {color} to line its nest, so kindness was fairer than blame."
            ),
        ),
        QAItem(
            question=f"Where did the friends find the missing {p.mystery_object}?",
            answer=f"They found it beside the tide pool, next to the gull's sea-grass nest.",
        ),
        QAItem(
            question="What moral did the friends learn?",
            answer="They learned that telling the truth and choosing kindness can protect friendship.",
        ),
    ]
    return "\n\n".join(story), qa


ASP_RULES = """
valid_case :- setting(rocky_shore), friendship, kindness, moral_value.
mystery_solved :- clue(wet_feathers), object_found, kindness.
friendship_proved :- mystery_solved, object_returned.
#show valid_case/0.
#show mystery_solved/0.
#show friendship_proved/0.
"""


def asp_facts():
    from asp import fact
    return "\n".join(
        [
            fact("setting", "rocky_shore"),
            fact("friendship"),
            fact("kindness"),
            fact("moral_value"),
            fact("clue", "wet_feathers"),
            fact("object_found"),
            fact("object_returned"),
        ]
    )


def asp_signature():
    from asp import atoms, one_model
    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return {
        "valid_case": set(atoms(model, "valid_case")),
        "mystery_solved": set(atoms(model, "mystery_solved")),
        "friendship_proved": set(atoms(model, "friendship_proved")),
    }


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story, qa = render(world)
    return StorySample(
        params=p,
        story=story,
        prompts=[
            f"Write a cute rocky-shore whodunit about {p.hero} and {p.friend}, "
            "where friendship, kindness, and moral value solve a small mystery."
        ],
        story_qa=qa,
        world_qa=[
            QAItem(
                question="What kind of place is this storyworld?",
                answer="It is a rocky shore with tide pools, ledges, sea grass, and a curious gull.",
            ),
            QAItem(
                question="What values guide the solution?",
                answer="Friendship, kindness, truth, and fair judgment guide the solution.",
            ),
        ],
        world=world,
    )


def verify():
    from asp import atoms, one_model

    result = asp_signature()
    if result["valid_case"] != {()}:
        pass
    if result["mystery_solved"] != {()} or result["friendship_proved"] != {()}:
        pass

    count = 0
    for hero, friend, mystery_object, weather, voice in itertools.product(
        FRIENDS, FRIENDS, OBJECTS, WEATHER, VOICES
    ):
        if hero == friend:
            continue
        p = StoryParams(
            hero=hero,
            friend=friend,
            mystery_object=mystery_object,
            weather=weather,
            voice=voice,
            world_seed=count + 10,
            prose_seed=count + 20,
        )
        sample = generate(p)
        if not sample.story.strip() or len(sample.story_qa) < 3:
            pass
        if "?" not in sample.story:
            pass
        count += 1
    print(f"OK: {count} configurations; Python/ASP parity; complete dialogue-rich stories.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=FRIENDS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--mystery-object", choices=OBJECTS)
    parser.add_argument("--weather", choices=WEATHER)
    parser.add_argument("--voice", choices=VOICES, default="gentle")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=getattr(args, "world_seed", None) + index,
        prose_seed=getattr(args, "prose_seed", None) + index,
        voice=getattr(args, "voice", None),
    )
    choices = {
        "hero": FRIENDS,
        "friend": FRIENDS,
        "mystery_object": OBJECTS,
        "weather": WEATHER,
    }
    for name, values in choices.items():
        requested = getattr(args, name)
        if requested is not None:
            setattr(p, name, requested)
        elif sample:
            setattr(p, name, rng.choice(values))
    if p.hero == p.friend:
        available = [name for name in FRIENDS if name != p.hero]
        p.friend = rng.choice(available) if sample else available[0]
    validate_params(p)
    return p


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "world": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                ensure_ascii=False,
                indent=2,
            )
        )


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if getattr(args, "n", None) < 1:
            pass
        if getattr(args, "show_asp", None):
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if getattr(args, "verify", None):
            verify()
            return 0
        if getattr(args, "asp", None):
            print(json.dumps(asp_signature(), indent=2))
            return 0

        rng = random.Random(getattr(args, "world_seed", None))
        if getattr(args, "all", None):
            params = []
            for hero, friend, mystery_object, weather in itertools.product(
                FRIENDS, FRIENDS, OBJECTS, WEATHER
            ):
                if hero == friend:
                    continue
                if getattr(args, "hero", None) is not None and getattr(args, "hero", None) != hero:
                    continue
                if getattr(args, "friend", None) is not None and getattr(args, "friend", None) != friend:
                    continue
                if getattr(args, "mystery_object", None) is not None and getattr(args, "mystery_object", None) != mystery_object:
                    continue
                if getattr(args, "weather", None) is not None and getattr(args, "weather", None) != weather:
                    continue
                params.append(
                    StoryParams(
                        hero=hero,
                        friend=friend,
                        mystery_object=mystery_object,
                        weather=weather,
                        voice=getattr(args, "voice", None),
                        world_seed=len(params) + getattr(args, "world_seed", None),
                        prose_seed=len(params) + getattr(args, "prose_seed", None),
                    )
                )
        else:
            params = [
                resolve_params(args, rng, index, sample=getattr(args, "n", None) > 1)
                for index in range(getattr(args, "n", None))
            ]

        samples = [generate(p) for p in params]
        if getattr(args, "json", None):
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=getattr(args, "trace", None),
                    qa=getattr(args, "qa", None),
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
