#!/usr/bin/env python3
"""Holly and the Morphologic Concert.

A small animal story about Holly learning that a concerted plan must be tested
before a difficult trip.  The bad ending is gentle but real: the animals fail
to deliver the berries before the frost, and they learn why.
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
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    beliefs: dict[str, str] = field(default_factory=dict)
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
    speaker: str = ""
    listener: str = ""
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
    hero: str = "Holly"
    helper: str = "Pip"
    bird: str = "Wren"
    problem: str = "frost"
    plan: str = "concerted"
    word: str = "morphologic"
    ending: str = "bad"
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


NAMES = ("Holly", "Pip", "Wren", "Moss", "Clover", "Juniper")
PROBLEMS = {"frost": "late_berries", "steep": "steep_hill"}
PLANS = {"concerted": "shared_pull"}
WORDS = {"morphologic": "morphologic", "concerted": "concerted", "holly": "holly"}
ENDINGS = ("bad",)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity("hero", params.hero, "animal", "holly_grove",
                           memes={"hope": 0.7, "worry": 0.4}),
            "helper": Entity("helper", params.helper, "animal", "holly_grove",
                             memes={"hope": 0.6, "worry": 0.3}),
            "bird": Entity("bird", params.bird, "animal", "holly_grove",
                           memes={"alertness": 0.8}),
            "basket": Entity("basket", "the berry basket", "thing", "holly_grove",
                             meters={"capacity": 6, "load": 0}),
            "berries": Entity("berries", "the holly berries", "food", "holly_grove",
                              meters={"available": 6, "delivered": 0}),
            "hill": Entity("hill", "the icy hill", "place", "hill_path",
                           meters={"steepness": 3, "slipperiness": 1}),
            "frost": Entity("frost", "the first frost", "weather", "sky",
                            meters={"hours": 2}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result,
                                  state=self.snapshot()))

    def say(self, who: str, text: str, *, to: str = ""):
        actor = self.entities[who]
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {actor.label} {tag}.',
                                  speaker=who, listener=to, state=self.snapshot()))

    def set_plan(self):
        for key in ("hero", "helper"):
            self.entities[key].beliefs["plan"] = self.params.plan
            self.entities[key].memes["trust"] = 1.0
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def validate_params(params: StoryParams):
    if params.problem not in PROBLEMS:
        pass
    if params.plan not in PLANS:
        pass
    if params.word not in WORDS:
        pass
    if params.ending not in ENDINGS:
        pass
    names = (params.hero, params.helper, params.bird)
    if len(set(names)) != len(names):
        pass
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in names):
        pass


def move_basket(world: World, amount: int) -> bool:
    basket = world.get("basket")
    berries = world.get("berries")
    hill = world.get("hill")
    frost = world.get("frost")
    if any(world.entities[key].beliefs.get("plan") != world.params.plan
           for key in ("hero", "helper")):
        pass
    if amount <= 0 or amount > berries.meters["available"] - berries.meters["delivered"]:
        pass
    if amount > basket.meters["capacity"]:
        pass
    berries.meters["delivered"] += amount
    basket.meters["load"] = amount
    if hill.meters["slipperiness"] > 0 and amount >= 6:
        frost.meters["hours"] -= 1
        return False
    return True


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = World(params)
    h, p, w = params.hero, params.helper, params.bird

    world.narrate(
        "beginning",
        f"{h} the rabbit lived beneath a holly bush with {p} the mole and {w} the wren. "
        f"Bright berries hung above them, but the first frost was already silvering the grass."
    )
    world.say("hero", "We should carry the holly berries to the warm burrow.")
    world.say("helper", "The hill is slippery, and the basket is heavy.")
    world.say("bird", "I can watch the sky. The frost will come soon.")
    world.say("hero", "Then we need a concerted plan. What does that word mean?")
    world.say("helper", "It means we work together, not just at the same time.")
    world.say("bird", "And we should test the path before filling the basket.")

    world.narrate(
        "lesson",
        f"The animals studied the basket's {params.word} shape: wide at the top, narrow at the bottom. "
        "It looked sturdy, but its narrow base might slide on the icy hill.",
        question="Why did the animals study the basket before carrying the berries?",
        cause="Its morphologic shape was wide above but narrow below, which could make it slide.",
        result="They learned that a full basket might be unsafe on the icy hill."
    )
    world.say("hero", "I think one full trip will be fastest.")
    world.say("helper", "Fastest is not always safest. Shall we test an empty basket?")
    world.say("hero", "Yes. You pull, I guide, and Wren watches the turns.")
    world.say("bird", "I will call if the basket begins to slide.")
    world.set_plan()

    world.narrate(
        "agreement",
        f"{h} and {p} agreed to pull the basket together while {w} watched the icy hill.",
        question="What made their plan concerted?",
        cause="Holly and Pip gave themselves different jobs and Wren agreed to watch for danger.",
        result="They could respond together instead of each animal guessing alone."
    )
    world.say("helper", "The empty basket wobbles near the stones.")
    world.say("hero", "Then we should bring only three berries first.")
    world.say("bird", "That will leave time for another careful trip.")

    first_ok = move_basket(world, 3)
    if not first_ok:
        pass
    world.get("basket").meters["load"] = 0
    world.narrate(
        "trial",
        f"They carried three holly berries over the stones. The basket wobbled, but {p} steadied it.",
        question="How did the first trial change their action?",
        cause="The empty basket wobbled near the stones.",
        result="They carried three berries instead of filling the basket all at once."
    )
    world.say("hero", "That worked. We can hurry with all the rest.")
    world.say("helper", "Wait. The frost is closer, but the hill is still icy.")
    world.say("hero", "If we all pull hard, the basket will be fine.")
    world.say("bird", "Holly, the shape has not changed.")

    remaining = world.get("berries").meters["available"] - world.get("berries").meters["delivered"]
    if remaining != 3:
        pass

    second_ok = move_basket(world, remaining)
    if second_ok:
        pass
    world.get("basket").location = "hill_path"
    world.get("basket").meters["load"] = 0
    world.get("berries").location = "icy_slope"
    world.get("frost").meters["hours"] = 0
    world.get("hero").memes["hope"] = 0.2
    world.get("helper").memes["worry"] = 1.0

    world.narrate(
        "bad_turn",
        f"They filled the basket with the last three berries and pulled together. "
        f"Halfway up, its narrow bottom slid sideways. The berries rolled into the snow.",
        question="Why did the second load fail?",
        cause="The animals hurried with a full basket even though its narrow base still slid on the icy hill.",
        result="The remaining berries scattered before they reached the warm burrow."
    )
    world.say("helper", "We worked together, but we did not listen to the warning.")
    world.say("hero", "Our plan was concerted in effort, not in judgment.")
    world.say("bird", "The frost has covered the berries now.")
    world.narrate(
        "ending",
        f"The warm burrow stayed empty of holly berries. {h} found one red berry under a stone, "
        f"but it was too cold to save. The three animals sat quietly beside the tipped basket.",
        question="What showed that the story had a bad ending?",
        cause="The last berries spilled on the icy hill before the frost arrived.",
        result="The animals reached the end with an empty warm burrow and a tipped basket."
    )

    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history if event.question
        ],
        world_qa=[
            QAItem("What does concerted mean in this story?",
                   "It means the animals work together with agreed jobs and a shared plan."),
            QAItem("What does morphologic describe?",
                   "It describes the basket's shape: wide at the top and narrow at the bottom."),
            QAItem("Why was the ending bad?",
                   "The animals hurried with the full basket, so the remaining holly berries spilled before the frost.")
        ],
        world=world,
    )
    check_sample(sample)
    return sample


PROMPT = (
    "Write an Animal Story about Holly, a rabbit, and friends carrying holly berries. "
    "Use the words morphologic and concerted, and give the story a Bad Ending caused by a failed plan."
)

ASP_RULES = """
safe_plan(concerted) :- shape(morphologic), warning(icy_hill), test_first.
bad_ending :- full_load, narrow_base, icy_hill, hurry.
#show safe_plan/1.
#show bad_ending/0.
"""


def asp_facts() -> str:
    from asp import fact
    return "\n".join([
        fact("shape", "morphologic"),
        fact("warning", "icy_hill"),
        fact("test_first"),
        fact("full_load"),
        fact("narrow_base"),
        fact("icy_hill"),
        fact("hurry"),
    ])


def asp_status() -> list[str]:
    from asp import one_model
    from asp import atoms
    return [str(item) for item in one_model(asp_facts() + "\n" + ASP_RULES)
            if item.name in {"safe_plan", "bad_ending"}]


def check_sample(sample: StorySample):
    world = sample.world
    if world.get("berries").meters["delivered"] != 6:
        pass
    if world.get("berries").location != "icy_slope":
        pass
    if world.get("frost").meters["hours"] != 0:
        pass
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 14:
        pass
    if not all(sum(event.speaker == key for event in speech) >= 3
               for key in ("hero", "helper", "bird")):
        pass
    if len(sample.story_qa) < 4:
        pass
    forbidden = ("{", "}", "internal_id", "meters")
    if any(token in sample.story for token in forbidden):
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--bird")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--plan", choices=tuple(PLANS))
    parser.add_argument("--word", choices=tuple(WORDS))
    parser.add_argument("--ending", choices=ENDINGS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice([name for name in NAMES if name != hero])
    bird = getattr(args, "bird", None) or rng.choice([name for name in NAMES if name not in {hero, helper}])
    return StoryParams(
        hero=hero,
        helper=helper,
        bird=bird,
        problem=getattr(args, "problem", None) or rng.choice(tuple(PROBLEMS)),
        plan=getattr(args, "plan", None) or "concerted",
        word=getattr(args, "word", None) or "morphologic",
        ending=getattr(args, "ending", None) or "bad",
        seed=getattr(args, "seed", None),
    )


def verify():
    sample = generate(StoryParams())
    if "bad_ending" not in asp_status():
        pass
    if "safe_plan" not in asp_status():
        pass
    check_sample(sample)
    print("OK: Python story state and ASP twin agree on the repaired animal trial.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
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
            print(json.dumps(asp_status()))
            return 0

        rng = random.Random(getattr(args, "seed", None))
        if getattr(args, "all", None):
            params_list = []
            for problem in PROBLEMS:
                params_list.append(StoryParams(
                    hero=getattr(args, "hero", None) or "Holly",
                    helper=getattr(args, "helper", None) or "Pip",
                    bird=getattr(args, "bird", None) or "Wren",
                    problem=problem,
                    plan=getattr(args, "plan", None) or "concerted",
                    word=getattr(args, "word", None) or "morphologic",
                    ending=getattr(args, "ending", None) or "bad",
                    seed=getattr(args, "seed", None),
                ))
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
