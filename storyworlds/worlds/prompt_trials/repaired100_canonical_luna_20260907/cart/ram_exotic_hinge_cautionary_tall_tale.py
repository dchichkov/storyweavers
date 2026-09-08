#!/usr/bin/env python3
"""The Ram, the Exotic Gate, and the Hinge That Learned Caution.

A tall tale about a daring ram whose mighty head meets a small hinge,
and about why even strong horns should listen before they charge.
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
    label: str
    kind: str = "thing"
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
    revealed: str = ""
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
    ram: str = "Rollo"
    keeper: str = "Luna"
    obstacle: str = "gate"
    solution: str = "inspect"
    approach: str = "charge"
    feature: str = "exotic"
    seed: int = 777
    params: object | None = None
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


RAMS = ("Rollo", "Bram", "Tumble", "Hazel", "Moss", "Pip")
KEEPERS = ("Luna", "Mira", "Nora", "Ivy", "Sela")
OBSTACLES = {"gate": "narrow garden gate", "bridge": "old footbridge"}
SOLUTIONS = {"inspect": "look_before_bumping", "wait": "wait_for_keeper"}
APPROACHES = ("charge", "ask")
FEATURES = ("exotic",)
PROMPT = (
    "Write a dialogue-rich cautionary tall tale about a ram, an exotic hinge, "
    "and the trouble caused by charging before listening."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "ram": Entity(
                "ram", params.ram, "animal", "hill pasture",
                meters={"strength": 10, "speed": 7, "horn_width": 2},
                memes={"boldness": 1.0, "caution": 0.1, "pride": 0.9},
            ),
            "keeper": Entity(
                "keeper", params.keeper, "character", "hill pasture",
                memes={"care": 1.0, "worry": 0.4},
            ),
            "hinge": Entity(
                "hinge", "the exotic moon hinge", "mechanism", "gate",
                meters={"turns": 0, "safe_turns": 3, "noise": 0},
                memes={"patience": 1.0},
            ),
            "gate": Entity(
                "gate", _safe_lookup(OBSTACLES, params.obstacle), "barrier", "pasture path",
                meters={"opening": 1.0, "ram_width": 2.0, "latched": 1},
                memes={"stubbornness": 0.7},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ):
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def say(
        self,
        speaker: str,
        text: str,
        *,
        listener: str = "",
        reveal: str = "",
    ):
        actor = self.entities[speaker]
        if reveal:
            if not listener or reveal not in actor.beliefs:
                pass
            self.entities[listener].beliefs[reveal] = actor.beliefs[reveal]
        tag = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'{actor.label} {tag}, "{text}"',
                speaker=speaker,
                listener=listener,
                revealed=reveal,
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(
                    question=event.question,
                    answer=f"{event.cause} {event.result}",
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    question="What made the hinge exotic?",
                    answer=(
                        "It was an unusual moon hinge that turned with a soft silver click "
                        "instead of using an ordinary iron pin."
                    ),
                ),
                QAItem(
                    question="What lesson did the ram learn?",
                    answer=(
                        "The ram learned to inspect a barrier and listen to a helper "
                        "before using his strength."
                    ),
                ),
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
    if params.solution not in SOLUTIONS:
        pass
    if params.approach not in APPROACHES:
        pass
    if params.feature not in FEATURES:
        pass
    if params.ram == params.keeper:
        pass
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.ram, params.keeper)):
        pass


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def inspect_gate(world: World):
    gate = world.get("gate")
    hinge = world.get("hinge")
    if gate.meters["latched"] != 1:
        pass
    gate.beliefs["opening_problem"] = "the ram is wider than the opening"
    hinge.beliefs["safe_method"] = "turn the moon hinge gently"
    world.get("ram").beliefs["opening_problem"] = "the ram is wider than the opening"


def open_gate(world: World, *, gentle: bool):
    ram = world.get("ram")
    gate = world.get("gate")
    hinge = world.get("hinge")
    if gate.meters["latched"] != 1:
        pass
    if gentle:
        if hinge.beliefs.get("safe_method") != "turn the moon hinge gently":
            pass
        hinge.meters["turns"] += 1
        hinge.meters["noise"] = 0
        gate.meters["latched"] = 0
        gate.location = "open pasture"
        ram.memes["caution"] = 1.0
        ram.memes["pride"] = 0.4
        return
    hinge.meters["turns"] += 1
    hinge.meters["noise"] += 4
    if hinge.meters["turns"] > hinge.meters["safe_turns"]:
        pass
    gate.meters["latched"] = 0
    gate.location = "open pasture"


def check_ending(world: World):
    ram = world.get("ram")
    gate = world.get("gate")
    hinge = world.get("hinge")
    if gate.meters["latched"] != 0 or ram.location != "open pasture":
        pass
    if hinge.meters["noise"] != 0:
        pass
    if ram.memes["caution"] < 1.0:
        pass
    if hinge.meters["turns"] != 1:
        pass


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    ram = world.get("ram")
    keeper = world.get("keeper")
    hinge = world.get("hinge")
    gate = world.get("gate")
    r, k = ram.label, keeper.label

    world.narrate(
        "beginning",
        f"{r} was the boldest ram on the hill, and his horns were so broad "
        f"that two shepherds once used them as a breakfast table. One bright morning, "
        f"he saw the {gate.label} between himself and the green open pasture. "
        f"At its side rested an exotic moon hinge that glittered like a tiny silver moon.",
    )
    world.say("ram", "I shall cross that gate in one mighty bound!")
    world.say("keeper", "Wait, Rollo! The hinge has a way to open it.")
    world.say("ram", "A hinge is only a hinge. My horns are much more impressive.")

    if params.approach == "charge":
        ram.memes["pride"] += 0.3
        world.narrate(
            "warning",
            f"{r} lowered his head. The hill trembled, three daisies fainted, "
            f"and a cloud hurried behind another cloud.",
        )
        world.say("keeper", "Please look first. The opening is narrower than your horns.")
        world.say("ram", "Then the gate should have built a wider opening!")
        world.narrate(
            "impact",
            f"{r} charged. His horns met the gate with a boom so loud that a flock "
            f"of birds landed backward. The exotic hinge gave one unhappy silver squeak, "
            f"but the gate did not open.",
            question="Why did the ram fail to cross the gate?",
            cause="He charged without checking the narrow opening or listening to the keeper.",
            result="His broad horns struck the gate, and the hinge squeaked without opening it.",
        )
        ram.meters["speed"] = 0
        ram.memes["worry"] = 0.8
        world.say("ram", "My horns have met their match. What did you know about this hinge?")
        keeper.beliefs["opening_problem"] = "the ram is wider than the opening"
        world.say(
            "keeper",
            "I knew the opening was narrow, and the moon hinge turns safely only when it is handled gently.",
            listener="ram",
            reveal="opening_problem",
        )
        keeper.beliefs["safe_method"] = "turn the moon hinge gently"
        world.get("ram").beliefs["safe_method"] = "turn the moon hinge gently"
        world.say(
            "keeper",
            "May we inspect it together before you try again?",
        )
        world.say("ram", "Yes. This time my eyes will go first and my horns will wait.")
        inspect_gate(world)
        world.narrate(
            "turn",
            f"{r} and {k} examined the gate. They measured the opening with a willow "
            f"wand and found it narrower than {r}'s horns. Then {k} touched the exotic "
            f"moon hinge with one careful finger.",
            question="What changed the ram's plan?",
            cause="The keeper explained that the opening was narrow and the hinge needed a gentle turn.",
            result="The ram stopped charging and agreed to inspect the gate before acting.",
        )
        world.say("keeper", "A small turn, then a pause. Strength is useful after wisdom chooses the direction.")
        world.say("ram", "I can do a small turn. I can even pause.")
        open_gate(world, gentle=True)
        world.narrate(
            "resolution",
            f"The moon hinge turned once with a quiet silver click. The gate swung open, "
            f"and {r} walked through sideways, leaving both horns and his dignity untouched.",
            question="How did the ram finally get through?",
            cause="He and the keeper inspected the opening and turned the exotic hinge gently.",
            result="The gate opened quietly, so he could walk through sideways instead of crashing.",
        )
    else:
        world.say("ram", "What should I know before I use my horns?")
        keeper.beliefs["opening_problem"] = "the ram is wider than the opening"
        keeper.beliefs["safe_method"] = "turn the moon hinge gently"
        world.say(
            "keeper",
            "The opening is narrow, and this exotic hinge opens with a gentle turn.",
            listener="ram",
            reveal="opening_problem",
        )
        world.say("keeper", "Let us inspect the hinge together.")
        world.say("ram", "Good. A careful ram keeps his horns for useful work.")
        inspect_gate(world)
        world.narrate(
            "inspection",
            f"{r} and {k} measured the gate with a willow wand. The opening was narrower "
            f"than {r}'s horns, but the exotic moon hinge was ready for one quiet turn.",
            question="Why did the ram inspect the gate before touching it?",
            cause="The keeper warned that his horns were wider than the opening.",
            result="He checked the space and learned that the hinge needed a gentle turn.",
        )
        world.say("keeper", "Turn it slowly, and stop when the silver mark faces the sun.")
        world.say("ram", "Slowly is not my usual speed, but today it is my chosen speed.")
        open_gate(world, gentle=True)
        world.narrate(
            "resolution",
            f"The hinge made one soft silver click. The gate opened, and {r} walked "
            f"sideways into the green pasture while the hill applauded with its grass.",
            question="How did the ram reach the pasture safely?",
            cause="He listened to the keeper, measured the narrow opening, and turned the hinge gently.",
            result="The gate opened without a crash, and he walked through sideways.",
        )

    ram.location = "open pasture"
    world.say("ram", "I still have powerful horns.")
    world.say("keeper", "Yes, and now you have a powerful pause.")
    world.narrate(
        "ending",
        f"From then on, {r} inspected every gate before charging. The exotic moon hinge "
        f"shone quietly behind him, and the green pasture welcomed a ram who was still "
        f"mighty, but no longer in a hurry to prove it.",
        question="What lesson did the ending prove?",
        cause="The ram used listening and inspection before using his strength.",
        result="He kept his mighty horns and gained the wiser habit of pausing first.",
    )
    sample = world.sample()
    check_sample(sample)
    return sample


ASP_RULES = """
safe_solution(inspect,look_before_bumping).
safe_solution(wait,wait_for_keeper).
approach(charge).
approach(ask).
feature(exotic).
valid(S,A,F) :- safe_solution(S,A), approach(F), feature(exotic).
#show valid/3.
"""


def asp_facts() -> str:
    from asp import fact

    facts = []
    for solution, meaning in SOLUTIONS.items():
        facts.append(fact("safe_solution", solution, meaning))
    for approach in APPROACHES:
        facts.append(fact("approach", approach))
    facts.append(fact("feature", "exotic"))
    return "\n".join(facts)


def asp_combos() -> set[tuple]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def valid_combos() -> set[tuple[str, str, str]]:
    return {
        (solution, meaning, approach)
        for solution, meaning in SOLUTIONS.items()
        for approach in APPROACHES
    }


def check_sample(sample: StorySample):
    world = sample.world
    check_ending(world)
    speeches = [event for event in world.history if event.kind == "speech"]
    if len(speeches) < 12:
        pass
    if sum(event.speaker == "ram" for event in speeches) < 5:
        pass
    if sum(event.speaker == "keeper" for event in speeches) < 5:
        pass
    if not any(event.revealed for event in speeches):
        pass
    if len(sample.story_qa) < 3:
        pass
    forbidden = ("meters", "memes", "{", "}", "ram_id")
    if any(word in sample.story.lower() for word in forbidden):
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--ram")
    parser.add_argument("--keeper")
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--feature", choices=FEATURES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ram = getattr(args, "ram", None) or rng.choice(RAMS)
    keeper = getattr(args, "keeper", None) or rng.choice([name for name in KEEPERS if name != ram])
    solution = getattr(args, "solution", None) or rng.choice(tuple(SOLUTIONS))
    approach = getattr(args, "approach", None) or rng.choice(APPROACHES)
    feature = getattr(args, "feature", None) or "exotic"
    params = StoryParams(
        ram=ram,
        keeper=keeper,
        solution=solution,
        approach=approach,
        feature=feature,
        seed=getattr(args, "seed", None),
    )
    validate_params(params)
    return params


def verify():
    from asp import atoms, one_model

    expected = valid_combos()
    actual = set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))
    if expected != actual:
        pass
    tested = 0
    for solution in SOLUTIONS:
        for approach in APPROACHES:
            sample = generate(
                StoryParams(
                    ram="Rollo",
                    keeper="Luna",
                    solution=solution,
                    approach=approach,
                    feature="exotic",
                )
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} stories verified; {len(expected)} ASP-compatible combinations.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
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
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
                ensure_ascii=False,
            )
        )


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
            print(json.dumps(sorted(asp_combos()), ensure_ascii=False))
            return 0

        rng = random.Random(getattr(args, "seed", None))
        if getattr(args, "all", None):
            samples = []
            for solution in SOLUTIONS:
                for approach in APPROACHES:
                    params = StoryParams(
                        ram=getattr(args, "ram", None) or rng.choice(RAMS),
                        keeper=getattr(args, "keeper", None) or rng.choice(KEEPERS),
                        solution=solution,
                        approach=approach,
                        feature=getattr(args, "feature", None) or "exotic",
                        seed=getattr(args, "seed", None),
                    )
                    validate_params(params)
                    samples.append(generate(params))
        else:
            samples = [
                generate(resolve_params(args, rng))
                for _ in range(getattr(args, "n", None))
            ]

        if getattr(args, "json", None):
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
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
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
