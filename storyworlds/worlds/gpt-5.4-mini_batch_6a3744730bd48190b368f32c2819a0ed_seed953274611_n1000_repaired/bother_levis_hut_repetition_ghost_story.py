#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bother_levis_hut_repetition_ghost_story.py
============================================================================

A tiny story world in a haunted-hut domain with repetition as a narrative
instrument. A child visits an old hut, hears a ghostly bother, learns to use a
calm repeated phrase, and ends with a safer, brighter image.

Seed words: bother, levis, hut
Style: Ghost Story
Feature: Repetition
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    damp: bool = True
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
class Bother:
    id: str
    phrase: str
    repeat: str
    effect: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Ghost:
    id: str
    label: str
    whisper: str
    repeat: str
    scared: int
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
class Response:
    id: str
    calm: str
    power: int
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
class StoryParams:
    setting: str
    bother: str
    ghost: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_bother(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    if child.memes.get("fear", 0.0) < THRESHOLD:
        return out
    sig = ("bother",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    ghost.memes["loud"] = ghost.memes.get("loud", 0.0) + 1
    out.append("")
    return out


def _r_calm(world: World) -> list[str]:
    child = world.get("child")
    if child.memes.get("calm", 0.0) < THRESHOLD:
        return []
    sig = ("calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["worry"] = 0.0
    return []


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_bother, _r_calm):
            if rule(world):
                changed = True


SETTINGS = {
    "hut": Setting(id="hut", label="the old hut", damp=True, tags={"hut"}),
    "shed": Setting(id="shed", label="the small shed", damp=False, tags={"shed"}),
}

BOTHERS = {
    "wind": Bother(id="wind", phrase="the wind kept tapping the wall", repeat="tap-tap, tap-tap", effect="the hut sounded busy", tags={"wind", "repeat"}),
    "floor": Bother(id="floor", phrase="the floorboard kept creaking", repeat="creak, creak", effect="the hut sounded awake", tags={"floor", "repeat"}),
    "drip": Bother(id="drip", phrase="a drop kept falling from the roof", repeat="drip, drip, drip", effect="the hut sounded patient", tags={"drip", "repeat"}),
}

GHOSTS = {
    "levis": Ghost(id="levis", label="Levis", whisper="bother, bother", repeat="again and again", scared=2, tags={"levis", "ghost"}),
    "pale": Ghost(id="pale", label="a pale ghost", whisper="hush, hush", repeat="soft and slow", scared=2, tags={"ghost"}),
}

RESPONSES = {
    "repeat": Response(id="repeat", calm="said the words again in a calm voice", power=2, tags={"repeat"}),
    "lantern": Response(id="lantern", calm="lit a lantern and held it up steady", power=3, tags={"light"}),
    "song": Response(id="song", calm="sang a small song until the room felt warmer", power=2, tags={"song"}),
}

GIRL_NAMES = ["Mina", "Nora", "Lina", "Ava", "Lily"]
BOY_NAMES = ["Theo", "Milo", "Ben", "Eli", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, b, g) for s in SETTINGS for b in BOTHERS for g in GHOSTS]


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for b, obj in BOTHERS.items():
        lines.append(asp.fact("bother", b))
        if "repeat" in obj.tags:
            lines.append(asp.fact("repetitive", b))
    for g in GHOSTS:
        lines.append(asp.fact("ghost", g))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B,G) :- setting(S), bother(B), ghost(G), repetitive(B).
gentle(R) :- response(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_gentle() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show gentle/1."))
    return sorted(r for (r,) in asp.atoms(model, "gentle"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos() differ.")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_gentle()) != set(RESPONSES):
        print("MISMATCH: ASP and Python response registry differ.")
        rc = 1
    else:
        print("OK: response registry matches.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, bother=None, ghost=None, response=None, child=None, child_gender=None, helper=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bother", choices=BOTHERS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.bother is None or c[1] == args.bother)
              and (args.ghost is None or c[2] == args.ghost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, bother, ghost = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, bother=bother, ghost=ghost, response=response,
                       child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper, role="helper"))
    hut = world.add(Entity(id="hut", kind="thing", type="place", label=SETTINGS[params.setting].label, tags={"hut"}))
    bother = world.add(Entity(id="bother", kind="thing", type="thing", label=BOTHERS[params.bother].phrase, tags={"repeat"}))
    ghost = world.add(Entity(id="ghost", kind="character", type="thing", label=GHOSTS[params.ghost].label, role="ghost"))
    child.memes["fear"] = 1.0
    ghost.memes["bother"] = 1.0

    world.say(f"On a cold night, {child.label} and {helper.label} went to {hut.label}.")
    world.say(f"Inside, {bother.label} -- {BOTHERS[params.bother].repeat} -- made the place feel strange.")
    world.say(f"Then {ghost.label} appeared and whispered, \"{GHOSTS[params.ghost].whisper}.\"")

    world.para()
    child.memes["fear"] += 1
    world.say(f"{child.label} felt a shiver and said it was a bother, a bother, a bother.")
    world.say(f"{helper.label} listened, and {helper.label} listened again, because the hut only grew louder.")

    world.para()
    if params.response == "repeat":
        child.memes["calm"] = 1.0
        world.say(f"So {child.label} chose to repeat the same calm words: \"{BOTHERS[params.bother].phrase}.\"")
        world.say(f"{child.label} said it once, then said it again, until the hush sounded bigger than the whisper.")
        world.say(f"{helper.label} smiled and held the lantern steady while the ghost drifted back into the dark.")
        world.say(f"At last the hut was still, and only the soft night wind answered the last little echo.")
    else:
        world.say(f"So {child.label} asked {helper.label} to {RESPONSES[params.response].calm}.")
        world.say(f"The glow grew warm, and the ghost's whisper slipped away.")
        world.say(f"The hut went quiet at last, and the two children could breathe again.")

    world.facts.update(params=params, child=child, helper=helper, hut=hut, bother=bother, ghost=ghost)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a ghost story for a young child that includes the words "bother", "levis", and "hut", and uses repetition.',
        f"Tell a spooky but gentle story where {p.child} and {p.helper} hear Levis in an old hut and repeat a calming phrase.",
        f"Write a short haunted-hut story with a repeated line that makes the ghost feel less scary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    qa = [
        QAItem(question="Where did the children go?", answer=f"They went to the old hut, where the air felt chilly and strange."),
        QAItem(question="What made the story spooky?", answer=f"Levis the ghost and the repeated bother sound made the hut feel haunted. The repeated words kept coming back, which made the scene feel eerie at first."),
        QAItem(question="How did the child calm the ghost story down?", answer=f"{p.child} repeated the same calm words again and again. That steady repetition made the hut feel quieter, and the ghost lost its power to scare them."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a hut?", answer="A hut is a small simple house or shelter. It can feel lonely or spooky if it sits in the dark."),
        QAItem(question="What does a ghost story usually do?", answer="A ghost story tries to make you feel a little scared in a safe way. It often uses shadows, whispers, and strange sounds."),
        QAItem(question="Why can repetition matter in a story?", answer="Repetition can make a line stick in your mind. In a spooky story, it can also make the feeling grow and then settle down again."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="hut", bother="wind", ghost="levis", response="repeat", child="Mina", child_gender="girl", helper="Owen", helper_gender="boy"),
    StoryParams(setting="hut", bother="floor", ghost="levis", response="lantern", child="Theo", child_gender="boy", helper="Nora", helper_gender="girl"),
    StoryParams(setting="shed", bother="drip", ghost="pale", response="song", child="Ava", child_gender="girl", helper="Eli", helper_gender="boy"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.bother not in BOTHERS or params.ghost not in GHOSTS or params.response not in RESPONSES:
        raise StoryError("Invalid world configuration.")
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
        print(asp_program("#show valid/3.\n#show gentle/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, b, g in combos:
            print(f"  {s:8} {b:8} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
