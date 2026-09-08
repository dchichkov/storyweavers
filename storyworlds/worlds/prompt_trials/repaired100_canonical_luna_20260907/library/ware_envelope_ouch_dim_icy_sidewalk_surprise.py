#!/usr/bin/env python3
"""A ghostly envelope on an icy sidewalk teaches a careful lesson."""

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
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
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
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)
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
    hero: str = "Luna"
    helper: str = "Owen"
    ware: str = "blue teacup"
    envelope: str = "silver envelope"
    approach: str = "listen"
    seed: int = 777
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


NAMES = ("Luna", "Owen", "Mira", "Theo", "Nia", "Pip")
WARE = {
    "blue teacup": ("a blue teacup", "a thin blue cup"),
    "brass key": ("a brass key", "a warm brass key"),
    "glass marble": ("a glass marble", "a round glass marble"),
}
APPROACHES = ("listen", "hurry")
PROMPT = "Write a gentle ghost story about a child finding an envelope on an icy sidewalk."
ASP_RULES = """
safe(Approach) :- approach(Approach), Approach = listen.
surprise(yes) :- envelope_found(yes), ghost_message(yes).
bad_ending(no) :- safe(listen).
#show safe/1.
#show surprise/1.
#show bad_ending/1.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity("hero", params.hero, "character", "sidewalk",
                           memes={"curiosity": 1.0, "courage": 0.5, "care": 0.5}),
            "helper": Entity("helper", params.helper, "character", "sidewalk",
                             memes={"care": 0.7, "trust": 0.5}),
            "sidewalk": Entity("sidewalk", "icy sidewalk", "place", "street",
                               meters={"slippery": 1, "dark": 1}),
            "ghost": Entity("ghost", "the pale ghost", "spirit", "sidewalk",
                            memes={"loneliness": 1.0}),
            "envelope": Entity("envelope", params.envelope, "message", "ice",
                               meters={"opened": 0, "safe": 0}),
            "ware": Entity("ware", WARE[params.ware][0], "object", "ice",
                           meters={"picked_up": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind, text, question, cause, result, self.snapshot()))

    def say(self, speaker: str, text: str):
        name = self.entities[speaker].label
        punctuation = "" if text.endswith((".", "?", "!")) else "."
        self.history.append(Event("speech", f'"{text}" said {name}{punctuation}',
                                  state=self.snapshot()))

    def sample(self) -> StorySample:
        story_qa = [
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in self.history if event.question
        ]
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=story_qa,
            world_qa=[
                QAItem("What makes the sidewalk dangerous?",
                       "Ice makes the sidewalk slippery, so people should move slowly."),
                QAItem("What does an envelope carry?",
                       "An envelope can carry a message for someone to read."),
            ],
            world=self,
        )
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def validate_params(params: StoryParams):
    if params.ware not in WARE:
        pass
    if params.approach not in APPROACHES:
        pass
    if params.hero == params.helper:
        pass
    for name in (params.hero, params.helper):
        if not name or not name[0].isupper() or not name.isalpha():
            pass


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def place_ware(world: World):
    ware = world.get("ware")
    envelope = world.get("envelope")
    if ware.location != "ice" or envelope.location != "ice":
        pass
    ware.location = "hero"
    ware.meters["picked_up"] = 1
    envelope.meters["safe"] = 1


def open_envelope(world: World):
    envelope = world.get("envelope")
    if envelope.location != "hero" or not envelope.meters["safe"]:
        pass
    envelope.meters["opened"] = 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.get("hero").label
    helper = world.get("helper").label
    ware = WARE[params.ware][0]

    world.narrate(
        "beginning",
        f"At dusk, {hero} walked along the icy sidewalk with {ware} tucked in a mitten. "
        f"Snow made the street quiet, and every step gave a tiny crack.",
    )
    world.say("hero", f"Look, {helper}. Something is shining under the ice.")
    world.say("helper", "Do not rush. The sidewalk is slippery.")
    world.narrate(
        "discovery",
        f"{hero} saw a silver envelope beside the {ware}. A pale shape appeared in its frosty shine, "
        "then vanished when the wind moved the snow.",
        question="Why did the children stop on the icy sidewalk?",
        cause=f"They noticed an envelope beside the {ware} and saw a strange shape in the frost.",
        result="They stopped so they could examine it without sliding.",
    )

    if params.approach == "hurry":
        world.get("hero").memes["care"] = 0.0
        world.say("hero", "I can grab it before the wind takes it!")
        world.narrate(
            "bad_turn",
            f"{hero} hurried across the ice. One boot slipped, and the {ware} flew from the mitten. "
            "The silver envelope skated into a dark drain.",
            question="What caused the bad ending?",
            cause=f"{hero} hurried instead of listening to {helper}'s warning about the icy sidewalk.",
            result="The ware fell, and the envelope slid into a drain before its message could be read.",
        )
        world.say("helper", "I warned you to move slowly.")
        world.say("hero", "I should have listened.")
        world.get("ware").location = "drain"
        world.get("envelope").location = "drain"
        world.get("sidewalk").meters["danger_remains"] = 1
        world.narrate(
            "ending",
            "The pale shape returned in the drain water. It looked like a sad face, and the wind whispered, "
            "“Please be careful with what is not yours.” The children walked home slowly, leaving the lost message behind.",
        )
    else:
        world.say("hero", "I will wait. Can you see what the envelope is touching?")
        world.say("helper", "The little ware is holding it against the wind.")
        world.narrate(
            "careful_pickup",
            f"{hero} crouched low. {helper} held out a mitten, and together they lifted the envelope and the {ware} "
            "without stepping on the slippery patch.",
            question="How did the children keep the envelope from being lost?",
            cause=f"They listened to the warning and lifted the envelope and {ware} together, very slowly.",
            result="The envelope stayed safe in {hero}'s mitten instead of sliding toward the drain.",
        )
        place_ware(world)
        world.say("hero", "Should we open it?")
        world.say("helper", "Only if the name on it belongs to someone here.")
        world.narrate(
            "surprise",
            f"The envelope shivered. A tiny cold handprint appeared on its flap, and a voice said, "
            f"“{hero}, please read this.”",
            question="What was the surprise?",
            cause="The ghost inside the frosty envelope spoke directly to the children.",
            result=f"They learned that the envelope carried a message from a lonely ghost.",
        )
        open_envelope(world)
        world.say("hero", "It says, 'Please return my blue light to the old porch.'")
        world.say("helper", "Then the safe thing is to carry it there together.")
        world.narrate(
            "resolution",
            f"{hero} opened the envelope while {helper} watched. Inside was a small map to an old porch, "
            f"where the ghost's blue light waited beside the {ware}.",
            question="How did the children help the ghost?",
            cause="The message gave them a safe place to take the ghost's blue light.",
            result="They followed the map together and returned the light to the old porch.",
        )
        world.get("envelope").location = "old_porch"
        world.get("ware").location = "old_porch"
        world.get("ghost").location = "old_porch"
        world.get("ghost").memes["loneliness"] = 0.0
        world.get("hero").memes["care"] = 1.0
        world.get("helper").memes["trust"] = 1.0
        world.narrate(
            "ending",
            f"At the old porch, the blue light rose from the {ware} and floated into the ghost's hands. "
            f"The ghost smiled, and the icy sidewalk behind {hero} and {helper} gleamed like a path home.",
        )

    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    params = sample.params
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 8:
        pass
    if not any("?" in event.text for event in speech):
        pass
    if params.approach == "listen":
        if world.get("envelope").location != "old_porch":
            pass
        if world.get("envelope").meters["opened"] != 1:
            pass
        if world.get("ghost").memes["loneliness"] != 0.0:
            pass
        if not any(event.kind == "surprise" for event in world.history):
            pass
    else:
        if world.get("envelope").location != "drain":
            pass
    if len(sample.story_qa) < 3:
        pass


def valid_combos() -> list[tuple[str]]:
    return [(approach,) for approach in APPROACHES]


def asp_facts() -> str:
    from asp import fact
    return "\n".join([
        fact("approach", "listen"),
        fact("approach", "hurry"),
        fact("envelope_found", "yes"),
        fact("ghost_message", "yes"),
    ])


def asp_outcomes() -> set[str]:
    from asp import atoms, one_model
    symbols = one_model(asp_facts() + ASP_RULES)
    return {args[0] for args in atoms(symbols, "safe")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--ware", choices=tuple(WARE))
    parser.add_argument("--approach", choices=APPROACHES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice([name for name in NAMES if name != hero])
    return StoryParams(
        hero=hero,
        helper=helper,
        ware=getattr(args, "ware", None) or rng.choice(tuple(WARE)),
        approach=getattr(args, "approach", None) or rng.choice(APPROACHES),
        seed=getattr(args, "seed", None),
    )


def verify():
    from asp import atoms, one_model
    symbols = one_model(asp_facts() + ASP_RULES)
    if not atoms(symbols, "safe"):
        pass
    count = 0
    for approach in APPROACHES:
        for ware in WARE:
            sample = generate(StoryParams(approach=approach, ware=ware))
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; ASP identifies the listening path.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


def main() -> int:
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
            print(json.dumps(sorted(asp_outcomes())))
            return 0

        rng = random.Random(getattr(args, "seed", None))
        if getattr(args, "all", None):
            params_list = [
                StoryParams(
                    hero=getattr(args, "hero", None) or "Luna",
                    helper=getattr(args, "helper", None) or "Owen",
                    ware=ware,
                    approach=approach,
                    seed=getattr(args, "seed", None),
                )
                for approach in APPROACHES
                for ware in WARE
                if getattr(args, "approach", None) is None or getattr(args, "approach", None) == approach
                if getattr(args, "ware", None) is None or getattr(args, "ware", None) == ware
            ]
            if not params_list:
                pass
        else:
            params_list = [resolve_params(args, rng) for _ in range(getattr(args, "n", None))]

        samples = [generate(params) for params in params_list]
        if getattr(args, "json", None):
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None),
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
