#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hexagon_sound_effects_repetition_tall_tale.py
===============================================================================

A standalone story world for a tall-tale about a hexagon-shaped something that
makes big sound effects again and again, until the problem turns into a bright,
silly, triumphant ending.

Seed words:
- hexagon

Features:
- Sound Effects
- Repetition

Style:
- Tall Tale

This world models a small prairie-town tall tale: a child finds a giant
hexagon-shaped noisemaker hidden in an old shed, its booming echoes scare the
town animals, and a calm helper turns the noisy problem into a parade.

The story engine is state-driven. We model:
- physical meters: echo, wobble, crack, carry, and distance
- emotional memes: pride, worry, delight, and relief

The text is then rendered from state changes, not from a frozen paragraph with
swapped names.
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
REPETITION_MIN = 2
SOUND_MIN = 1

NAMES = ["Nell", "Milo", "June", "Bo", "Ivy", "Toby", "Pearl", "Clem"]
HELPERS = ["Grandma", "Grandpa", "Aunt Rose", "Uncle Finn"]
PLACES = {
    "prairie": "the wide prairie",
    "fair": "the county fair",
    "barn": "the red barn",
}
NOISES = {
    "boom": "BOOM!",
    "bang": "BANG!",
    "clang": "CLANG!",
    "whang": "WHANG!",
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    echo: int
    carries: int
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
class NoiseMaker:
    id: str
    label: str
    sound_words: list[str]
    repetition: int
    weight: int
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
class HelperMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
        self.facts: dict[str, object] = {}

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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    bell = world.get("noisemaker")
    place = world.get("place")
    if bell.meters["ringing"] < THRESHOLD:
        return out
    sig = ("echo",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["echo"] += place.attrs["echo_boost"]
    for kid in ("child", "helper"):
        world.get(kid).memes["worry"] += 1
    out.append("__echo__")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    bell = world.get("noisemaker")
    if bell.meters["ringing"] < THRESHOLD:
        return out
    if bell.meters["rings"] >= bell.attrs["target_rings"]:
        return out
    sig = ("repeat", int(bell.meters["rings"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bell.meters["rings"] += 1
    bell.memes["pride"] += 1
    out.append("__ring__")
    return out


RULES = [Rule("echo", _r_echo), Rule("repeat", _r_repeat)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable(place: Place, noise: NoiseMaker, move: HelperMove) -> bool:
    return place.echo >= SOUND_MIN and noise.repetition >= REPETITION_MIN and move.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES_REG.items():
        for nid, noise in NOISES_REG.items():
            for mid, move in MOVES.items():
                if reasonable(place, noise, move):
                    combos.append((pid, nid, mid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    move = MOVES[params.move]
    return "calmed" if move.power >= params.challenge else "rowdy"


def _make_noise_line(noise: NoiseMaker) -> str:
    return ", ".join(noise.sound_words)


def tell(place: Place, noise: NoiseMaker, move: HelperMove, child: Entity, helper: Entity) -> World:
    world = World()
    child = world.add(Entity(id=child.id, kind="character", type=child.type, role="child"))
    helper = world.add(Entity(id=helper.id, kind="character", type=helper.type, role="helper"))
    noise_ent = world.add(Entity(id="noisemaker", type="thing", label=noise.label,
                                 attrs={"target_rings": noise.repetition}))
    place_ent = world.add(Entity(id="place", type="place", label=place.label,
                                 attrs={"echo_boost": place.echo}))
    child.memes["pride"] = 1
    helper.memes["worry"] = 1

    world.say(
        f"Down on {place.label}, {child.id} found a giant hexagon-shaped noisemaker that "
        f"looked as big as a wagon wheel and as shiny as a pie pan."
    )
    world.say(
        f'"{_make_noise_line(noise)}," went the hexagon when {child.id} gave it a tap. '
        f'"{_make_noise_line(noise)}," it answered again, and again, and again.'
    )
    world.say(
        f"Each time it rang, it made a bigger tumble of sound, and the sound ran out over "
        f"{place.label} like a raccoon in a hurry."
    )

    world.para()
    child.meters["ringing"] = 1
    noise_ent.meters["ringing"] = 1
    propagate(world, narrate=False)
    world.say(
        f'"{_make_noise_line(noise)}!" shouted the hexagon, and every time it shouted, '
        f"the prairie seemed to shout back."
    )
    world.say(
        f"The {place.label_word if hasattr(place, 'label_word') else place.label} shook, the hens hopped, "
        f"and {helper.id} came hurrying up the lane with {helper.pronoun('possessive')} hat in both hands."
    )
    if world.get("place").meters["echo"] >= THRESHOLD:
        world.say(
            f'"Easy now," {helper.id} said. "That hexagon is making enough racket to wake '
            f"the moon twice."'
        )

    world.para()
    child.memes["defiance"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} wanted one more boom, and then one more after that, because a tall tale "
        f"always asks for one more."
    )
    world.say(
        f"But {helper.id} was already thinking. {helper.id} tied a bright rope to the hexagon, "
        f"and with a quick {NOISES[noise.id]}-like tug, {helper.pronoun()} turned the racket into a parade."
    )
    world.say(
        f"Now the hexagon went {NOISES[noise.id]}-boom, {NOISES[noise.id]}-boom, {NOISES[noise.id]}-boom "
        f"as it rolled slow and steady behind the wagon."
    )

    world.para()
    move_line = move.text.replace("{noise}", noise.label)
    if move.power >= 2:
        world.say(
            f"{helper.id} {move_line}, and the whole town started clapping in time: "
            f"boom, boom, boom, then clap, clap, clap."
        )
        world.say(
            f"{child.id} climbed onto the wagon seat and waved as the hexagon rolled along, "
            f"not wild anymore, but grand and merry and under control."
        )
        child.memes["relief"] += 2
        helper.memes["relief"] += 2
        world.say(
            f"By sunset the hexagon was singing softly instead of shouting, and the prairie held "
            f"the last echo like a bedtime story."
        )
    else:
        world.say(
            f"{helper.id} {move.fail.replace('{noise}', noise.label)}."
        )
        world.say(
            f"So the hexagon kept on booming until the cows ran three fences away and the barn swore "
            f"it had heard enough."
        )

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        noise=noise,
        move=move,
        outcome="calmed" if move.power >= 2 else "rowdy",
        rings=int(world.get("noisemaker").meters["rings"]),
        echo=world.get("place").meters["echo"],
        child_name=child.id,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a young child that includes the word "hexagon" and lots of repeated sound effects.',
        f"Tell a funny prairie story where {f['child_name']} finds a hexagon-shaped noisemaker, makes it go boom again and again, and then calms it down.",
        f'Write a story with repetition like "boom, boom, boom" and a giant hexagon that changes from noisy trouble into a parade.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    noise = f["noise"]
    qas = [
        QAItem(
            question="What did the child find?",
            answer=f"{child.id} found a giant hexagon-shaped noisemaker. It rang with repeated sound effects and filled {place.label} with echoing noise.",
        ),
        QAItem(
            question="Why did the helper come running?",
            answer=f"{helper.id} came running because the hexagon was making too much racket. The sound kept repeating, so the helper had to steady it before the whole place shook again.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the hexagon calm and rolling in a parade instead of shouting. The big noise changed into a cheerful rhythm, and everyone could smile again.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hexagon?",
            answer="A hexagon is a shape with six sides. People can use the shape for signs, wheels, or decorations.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying or doing something again and again. It can make a story feel musical, funny, or grand.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a word or phrase that makes you hear a noise in your mind, like BOOM or CLANG. It helps the reader imagine the action.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    noise: str
    move: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    challenge: int = 2
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


PLACES_REG = {
    "prairie": Place(id="prairie", label="the wide prairie", echo=2, carries=2, tags={"outdoor"}),
    "fair": Place(id="fair", label="the county fair", echo=3, carries=3, tags={"outdoor"}),
    "barn": Place(id="barn", label="the red barn", echo=1, carries=2, tags={"indoor"}),
}
NOISES_REG = {
    "boom": NoiseMaker(id="boom", label="a hexagon boom-box", sound_words=["BOOM", "BOOM"], repetition=3, weight=2, tags={"sound"}),
    "clang": NoiseMaker(id="clang", label="a hexagon dinner gong", sound_words=["CLANG", "CLANG"], repetition=2, weight=3, tags={"sound"}),
    "bang": NoiseMaker(id="bang", label="a hexagon drum", sound_words=["BANG", "BANG"], repetition=4, weight=3, tags={"sound"}),
}
MOVES = {
    "rope": HelperMove(id="rope", sense=3, power=3, text="tied a bright rope to the hexagon and led it into a parade", fail="tried to hush the {noise}, but it only got louder", tags={"calm"}),
    "cover": HelperMove(id="cover", sense=3, power=2, text="covered the hexagon with a quilt and tapped out a marching beat", fail="threw a quilt over it, but the hexagon shook it off", tags={"calm"}),
    "tap": HelperMove(id="tap", sense=2, power=1, text="tapped a steady beat on the wagon side", fail="tapped at the air and hoped for the best", tags={"weak"}),
}


def valid_story_keys() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a hexagon, sound effects, and repetition in a tall tale.")
    ap.add_argument("--place", choices=PLACES_REG)
    ap.add_argument("--noise", choices=NOISES_REG)
    ap.add_argument("--move", choices=MOVES)
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
              and (args.noise is None or c[1] == args.noise)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("No valid combo matches the requested options.")
    place, noise, move = rng.choice(sorted(combos))
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in HELPERS if n != child])
    return StoryParams(
        place=place,
        noise=noise,
        move=move,
        child=child,
        child_type="girl" if child in {"Nell", "June", "Ivy", "Pearl"} else "boy",
        helper=helper,
        helper_type="woman" if "Grandma" in helper or "Aunt" in helper else "man",
        challenge=2 if move != "tap" else 3,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES_REG or params.noise not in NOISES_REG or params.move not in MOVES:
        raise StoryError("Invalid params for this world.")
    world = tell(
        place=PLACES_REG[params.place],
        noise=NOISES_REG[params.noise],
        move=MOVES[params.move],
        child=Entity(id=params.child, kind="character", type=params.child_type, role="child"),
        helper=Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"),
    )
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


ASP_RULES = r"""
valid(P,N,M) :- place(P), noise(N), move(M), echo(P), repetition(N), sense(M,S), S >= 2.
outcome(calmed) :- chosen_move(M), power(M,P), challenge(C), P >= C.
outcome(rowdy) :- chosen_move(M), power(M,P), challenge(C), P < C.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES_REG.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("echo", pid, p.echo))
    for nid, n in NOISES_REG.items():
        lines.append(asp.fact("noise", nid))
        lines.append(asp.fact("repetition", nid, n.repetition))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        lines.append(asp.fact("power", mid, m.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, noise=None, move=None, child=None, helper=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams(place="prairie", noise="boom", move="rope", child="Nell", child_type="girl", helper="Grandma", helper_type="woman", challenge=2),
    StoryParams(place="fair", noise="bang", move="cover", child="Milo", child_type="boy", helper="Uncle Finn", helper_type="man", challenge=2),
    StoryParams(place="barn", noise="clang", move="tap", child="June", child_type="girl", helper="Aunt Rose", helper_type="woman", challenge=3),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        for i in range(max(args.n, 1) * 50):
            if len(samples) >= max(args.n, 1):
                break
            try:
                p = resolve_params(args, random.Random((args.seed or 0) + i))
            except StoryError as err:
                print(err)
                return
            if p in seen:
                continue
            seen.add(p)
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
