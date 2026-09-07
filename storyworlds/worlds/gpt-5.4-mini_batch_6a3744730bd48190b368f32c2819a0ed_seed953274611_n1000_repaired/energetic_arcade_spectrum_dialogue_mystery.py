#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/energetic_arcade_spectrum_dialogue_mystery.py
==============================================================================

A small storyworld about a curious mystery in an arcade: an energetic child,
a strange spectrum of colors, and a clue found through dialogue.

The story premise is simple:
- A machine at an arcade starts behaving strangely.
- The characters talk through the clues.
- The mystery is solved by tracing colored lights back to their source.
- The ending shows what changed: the arcade becomes bright, orderly, and safe.

The world is intentionally compact, child-facing, and state-driven.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    glow: str
    clues: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Mystery:
    id: str
    oddity: str
    dialogue_prompt: str
    resolution: str
    danger: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Answer:
    id: str
    text: str
    clue: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_fear(world: World) -> list[str]:
    signal = world.get("Signal")
    if signal.meters["oddity"] < THRESHOLD:
        return []
    sig = ("fear", "Child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("Child").memes["worry"] += 1
    return ["__worry__"]


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.get("Arcade").meters["signal"] < THRESHOLD:
        return out
    sig = ("clue", "arcade")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("Arcade").meters["order"] += 1
    out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("clue", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mystery(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get("Signal").meters["oddity"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("Child").memes["worry"],
        "order": sim.get("Arcade").meters["order"],
    }


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            for answer_id, answer in ANSWERS.items():
                if mystery.tags & answer.tags and place_id == "arcade":
                    combos.append((place_id, mystery_id, answer_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    answer: str
    child: str
    helper: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


PLACES = {
    "arcade": Place(
        id="arcade",
        label="the arcade",
        glow="bright screens and blinking buttons",
        clues=["a humming cabinet", "a stripe of color on the floor", "a soft chime"],
        tags={"arcade"},
    ),
    "hall": Place(
        id="hall",
        label="the hall",
        glow="long lamps and polished tiles",
        clues=["a quiet corner", "a mirrored wall", "a small humming panel"],
        tags={"hall"},
    ),
}

MYSTERIES = {
    "signal": Mystery(
        id="signal",
        oddity="a strange, energetic flicker",
        dialogue_prompt="Why is that machine flashing like a rainbow?",
        resolution="the loose color strip was plugged back in",
        danger="the floor became hard to see",
        tags={"signal"},
    ),
    "lights": Mystery(
        id="lights",
        oddity="a shifting spectrum of lights",
        dialogue_prompt="Why does the spectrum keep changing?",
        resolution="the lamp cover was cleaned and fixed",
        danger="the lights made everyone squint",
        tags={"spectrum"},
    ),
}

ANSWERS = {
    "plug": Answer(
        id="plug",
        text="plugged the cable in again and made the cabinet steady",
        clue="the broken link was near the back of the machine",
        tags={"signal"},
    ),
    "clean": Answer(
        id="clean",
        text="cleaned the lamp cover and set it straight",
        clue="dust had blurred the colored glass",
        tags={"spectrum"},
    ),
    "tape": Answer(
        id="tape",
        text="taped the loose strip down so it would not flicker",
        clue="the strip kept lifting and blinking",
        tags={"signal", "spectrum"},
    ),
}

NAMES = ["Mina", "Leo", "Ari", "Zoe", "Noah", "Luna", "Milo", "Ivy"]

OPENINGS = [
    "The after-school arcade challenge had just begun",
    "A birthday group was choosing its first game",
    "The arcade was about to award its hundredth prize ticket",
    "A rain shower had sent a crowd indoors to play",
    "The last round of the neighborhood game night was starting",
    "A younger player was learning the dance game for the first time",
    "The high-score board had drawn everyone to the center aisle",
    "The arcade attendant was testing the cabinets before opening",
]

CASES = {
    "plug": {
        "machine": "the Comet Racer cabinet",
        "interruptions": [
            "its steering lights blinked out halfway through every lap",
            "its score vanished whenever the blue band crossed the screen",
            "its start button chimed, but the race would not begin",
            "its rainbow track froze and sent players back to the starting line",
        ],
        "clues": [
            "a loose data cable shifted whenever the cabinet vibrated",
            "the blue light disappeared at the same moment the score reset",
            "a tiny amber connection lamp winked on and off behind the clear service panel",
            "the picture steadied when everyone stopped bumping the cabinet",
        ],
        "false_leads": [
            "a sticky steering wheel",
            "a scratched token",
            "the blinking prize counter",
            "a reflection from the snack sign",
        ],
        "diagnosis": "a loose data cable was breaking the cabinet's signal",
        "repair": "the attendant switched off the cabinet, secured the loose cable, and restarted it",
        "result": "the racer kept its score through a complete rainbow lap",
    },
    "clean": {
        "machine": "the Prism Puzzle projector",
        "interruptions": [
            "its colored clues melted into one cloudy patch",
            "its violet arrow pointed players toward the wrong door",
            "its rainbow map looked sharp at the top and fuzzy at the bottom",
            "its color-matching round rejected every correct answer",
        ],
        "clues": [
            "a gray crescent covered one edge of the lamp window",
            "fingerprints bent the projected colors into blurry halos",
            "the wall image cleared when a clean card briefly shaded the lamp",
            "dust sparkled in the projector beam but nowhere else",
        ],
        "false_leads": [
            "a faded picture on the wall",
            "the players' colored wristbands",
            "a purple bulb in the next cabinet",
            "the projector's cheerful warning tune",
        ],
        "diagnosis": "dust and fingerprints were blurring the projector's spectrum",
        "repair": "the attendant powered down the projector, cleaned its cover, and set it straight",
        "result": "each colored clue landed in its proper place on the puzzle wall",
    },
    "tape": {
        "machine": "the Spectrum Step dance game",
        "interruptions": [
            "a loose light strip flashed even when nobody stepped on it",
            "its green path flickered and made the next safe step unclear",
            "one edge of the glowing floor curled up after every song",
            "its colors raced in the opposite direction from the music",
        ],
        "clues": [
            "one corner of the light strip lifted whenever the floor thumped",
            "the false flash always began beside the same loose edge",
            "a narrow shadow appeared beneath the strip before each wrong color",
            "the color pattern behaved normally when the loose edge lay flat",
        ],
        "false_leads": [
            "a player's flashing shoelaces",
            "the energetic drumbeat",
            "a reflection in the prize-case glass",
            "the game's fastest difficulty setting",
        ],
        "diagnosis": "a lifting light strip was making false flashes and creating a tripping hazard",
        "repair": "the attendant closed the dance pad, fastened the strip beneath its clear guard, and tested every edge",
        "result": "the floor showed one steady path and stayed flat through the whole song",
    },
}

ENDING_IMAGES = [
    "A clean rainbow loop circled the cabinet while the next player cheered.",
    "On the polished floor, seven steady colors pointed all the way to the prize desk.",
    "The final blue light held still as a silver prize ticket curled into the tray.",
    "Across the quiet screen, the spectrum opened like a bright fan and did not flicker once.",
    "The younger players followed the clear colored path, one safe step at a time.",
    "A row of calm lights reflected in the two detectives' grinning faces.",
    "The high-score bell rang beneath a crisp rainbow that stayed exactly where it belonged.",
    "When the arcade doors opened, every color was bright, orderly, and ready for play.",
]


def _story_rng(params: StoryParams) -> random.Random:
    key = params.seed if params.seed is not None else (
        f"{params.place}|{params.mystery}|{params.answer}|{params.child}|{params.helper}"
    )
    return random.Random(key)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an energetic arcade mystery with dialogue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--answer", choices=ANSWERS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.answer and args.answer not in ANSWERS:
        raise StoryError("Unknown answer.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.answer is None or c[2] == args.answer)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, answer = rng.choice(sorted(combos))
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != child])
    return StoryParams(place=place, mystery=mystery, answer=answer, child=child, helper=helper)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="Child", kind="character", type="child", label=params.child, role="detective"))
    helper = world.add(Entity(id="Helper", kind="character", type="child", label=params.helper, role="clue keeper"))
    arcade = world.add(Entity(id="Arcade", kind="place", type="place", label=PLACES[params.place].label))
    signal = world.add(Entity(id="Signal", type="object", label=MYSTERIES[params.mystery].id))
    child.memes["energy"] = 1
    child.memes["curiosity"] = 1

    rng = _story_rng(params)
    case = CASES[params.answer]
    opening = rng.choice(OPENINGS)
    interruption = rng.choice(case["interruptions"])
    clue = rng.choice(case["clues"])
    false_lead = rng.choice(case["false_leads"])
    ending = rng.choice(ENDING_IMAGES)
    route = rng.randrange(6)
    investigation_method = [
        "comparing the first suspect's pattern with the flicker",
        "interviewing waiting players and watching another cycle",
        "mapping the changing colors on a prize slip",
        "listening between game sounds and matching cause to effect",
        "comparing the troubled game with a working neighbor",
        "clearing the area and observing the machine from farther away",
    ][route]

    world.say(
        f"{opening} when {child.label_word}, an energetic young detective, hurried inside. "
        f"The arcade shimmered with {PLACES[params.place].glow}, a lively spectrum of color, "
        f"but {case['machine']} showed {MYSTERIES[params.mystery].oddity}: {interruption}."
    )
    world.say(
        f'“{MYSTERIES[params.mystery].dialogue_prompt}” {child.label_word} asked. '
        f'“Let’s find evidence before anyone guesses,” {helper.label_word} replied.'
    )
    signal.meters["oddity"] += 1
    arcade.meters["signal"] += 1
    propagate(world, narrate=False)

    world.para()
    if route == 0:
        world.say(
            f"They first checked {false_lead}, but its pattern did not match the flicker. "
            f"Then {helper.label_word} crouched at a safe distance and spotted that {clue}."
        )
        world.say(
            f'“The same color vanishes each time,” said {child.label_word}. '
            f'“Our best explanation is that {case["diagnosis"]}.”'
        )
    elif route == 1:
        world.say(
            f"They asked two waiting players what they had seen. Both ruled out {false_lead} and pointed toward {case['machine']}. "
            f"Watching one more cycle revealed that {clue}."
        )
        world.say(
            f'“The stories agree with the spectrum,” {helper.label_word} said. '
            f'“Yes,” answered {child.label_word}, “{case["diagnosis"].capitalize()}.”'
        )
    elif route == 2:
        world.say(
            f"Instead of touching the machine, they drew the changing spectrum on a prize slip. "
            f"The repeated gap led them past {false_lead}, where they noticed that {clue}."
        )
        world.say(
            f'“Our color map repeats the mistake,” said {child.label_word}. '
            f'“So {case["diagnosis"]},” {helper.label_word} concluded.'
        )
    elif route == 3:
        world.say(
            f"They paused beside the cabinet and listened between its cheerful sounds. {false_lead.capitalize()} stayed unchanged, "
            f"but each faulty flash happened just as they observed this clue: {clue}."
        )
        world.say(
            f'“One event causes the next,” {helper.label_word} whispered. '
            f'“Then our answer is that {case["diagnosis"]},” said {child.label_word}.'
        )
    elif route == 4:
        world.say(
            f"They compared the troubled game with the cabinet beside it. They found {false_lead} nearby, yet the neighboring machine worked. "
            f"Only the troubled game showed that {clue}."
        )
        world.say(
            f'“We can cross out the reflection,” said {child.label_word}. '
            f'“The real cause is that {case["diagnosis"]},” {helper.label_word} replied.'
        )
    else:
        world.say(
            f"They warned the waiting players to give the machine room, then watched from the prize desk. "
            f"From there, {false_lead} stopped looking suspicious, and they could see that {clue}."
        )
        world.say(
            f'“Now the whole pattern makes sense,” said {helper.label_word}. '
            f'“It shows that {case["diagnosis"]},” {child.label_word} agreed.'
        )

    world.para()
    world.say(
        f"They told the arcade attendant what they had observed. After putting up a safety sign, {case['repair']}. "
        f"The detectives tested their conclusion by watching a full round: {case['result']}."
    )
    world.say(
        f'“Mystery solved by looking, listening, and talking,” {child.label_word} said. '
        f'“And by letting an adult handle the repair,” added {helper.label_word}. {ending}'
    )
    world.facts.update(
        child=child,
        helper=helper,
        arcade=arcade,
        signal=signal,
        mystery=MYSTERIES[params.mystery],
        answer=ANSWERS[params.answer],
        place=PLACES[params.place],
        opening=opening,
        machine=case["machine"],
        interruption=interruption,
        clue=clue,
        false_lead=false_lead,
        diagnosis=case["diagnosis"],
        repair=case["repair"],
        result=case["result"],
        ending=ending,
        investigation_route=route,
        investigation_method=investigation_method,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a young child that includes the words "energetic", "arcade", and "spectrum".',
        f"Tell a dialogue-driven story where {f['child'].label_word} and {f['helper'].label_word} use evidence to solve a mystery involving {f['machine']}.",
        f"Write a child-friendly arcade mystery in which the clue that {f['clue']} leads to a safe repair and a visible ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"When {f['opening'].lower()}, what problem did {child.label_word} and {helper.label_word} investigate at {f['machine']}?",
            answer=f"They investigated why {f['interruption']} while the machine showed {f['mystery'].oddity}. After ruling out {f['false_lead']}, they investigated by {f['investigation_method']} and discovered that {f['clue']}. The final proof was visible: {f['ending']}",
        ),
        QAItem(
            question=f"While {f['opening'].lower()}, the machine showed {f['mystery'].oddity} and {f['interruption']}. After ruling out {f['false_lead']}, what clue helped {child.label_word} and {helper.label_word} identify the cause?",
            answer=f"They investigated by {f['investigation_method']}. This let them observe that {f['clue']}, supporting their conclusion that {f['diagnosis']}. Their conclusion was confirmed when {f['ending'][0].lower() + f['ending'][1:]}",
        ),
        QAItem(
            question=f"When {f['opening'].lower()}, {f['machine']} had a problem: {f['interruption']}. How did {child.label_word} and {helper.label_word} safely solve the mystery of {f['mystery'].oddity}?",
            answer=f"After ruling out {f['false_lead']}, they investigated by {f['investigation_method']} and observed that {f['clue']}. They reported the evidence instead of repairing the machine themselves, so {f['repair']}. Afterward, {f['result']}. {f['ending']}",
        ),
        QAItem(
            question=f"While {f['opening'].lower()}, why did {child.label_word} and {helper.label_word} reject {f['false_lead']} as the cause of {f['mystery'].oddity}?",
            answer=f"It did not explain why {f['interruption']}. By the time they finished {f['investigation_method']}, the stronger clue was that {f['clue']}. The result was confirmed when {f['ending'][0].lower() + f['ending'][1:]}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    answer = f["answer"]
    mystery = f["mystery"]
    qa = [
        QAItem(
            question="What is an arcade?",
            answer="An arcade is a place with game machines and bright lights where people can play. It often makes cheerful sounds and colorful flashes.",
        ),
        QAItem(
            question="What does spectrum mean?",
            answer="A spectrum is a range of colors or lights, like the colors you might see spread across a rainbow. It can help someone notice a pattern or a clue.",
        ),
    ]
    if "signal" in mystery.tags:
        qa.append(
            QAItem(
                question="What should you do if a machine looks broken?",
                answer="You should tell a grown-up and look for the cause carefully instead of guessing. A slow, careful check can keep everyone safe.",
            )
        )
    if "spectrum" in answer.tags:
        qa.append(
            QAItem(
                question="Can colors be a clue?",
                answer="Yes. A strange color pattern can point to what is wrong, especially when something is flickering or out of place.",
            )
        )
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="arcade", mystery="signal", answer="plug", child="Mina", helper="Leo"),
    StoryParams(place="arcade", mystery="lights", answer="clean", child="Ari", helper="Zoe"),
    StoryParams(place="arcade", mystery="signal", answer="tape", child="Luna", helper="Milo"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    for aid, a in ANSWERS.items():
        lines.append(asp.fact("answer", aid))
        for tag in sorted(a.tags):
            lines.append(asp.fact("fits", aid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid("arcade", M, A) :- mystery(M), answer(A), fits(A, T), tag(M, T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset != pset:
        rc = 1
        print("MISMATCH in valid combos")
    else:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, answer=None, child=None, helper=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generated a story.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Arcade mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--answer", choices=ANSWERS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.answer is None or c[2] == args.answer)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, answer = rng.choice(sorted(combos))
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != child])
    return StoryParams(place=place, mystery=mystery, answer=answer, child=child, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.answer not in ANSWERS:
        raise StoryError("Invalid parameters.")
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
