#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/faith_humor_ghost_story.py
===========================================================

A tiny story world for a humorous ghost-story premise about faith, a spooky
house, and a child discovering that the "ghost" is funny rather than frightful.

The engine is intentionally small but still state-driven:
- characters carry physical meters and emotional memes,
- the house has places that can be spooky,
- a mystery grows, gets a comic reveal, and ends with a changed feeling,
- the word "faith" is woven into the narrative as trust, hope, or belief.

This world aims for a kid-facing ghost-story mood with a light, comic ending.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
FEAR_TO_SPIKE = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    room: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    house: str
    spooky_room: str
    sound: str
    hiding_place: str
    ending_image: str
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
    clue: str
    odd_sound: str
    fake_scary_line: str
    reveal_line: str
    cause: str
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
    sense: int
    calm: int
    action: str
    reveal: str
    ending: str
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["mystery"] < THRESHOLD:
            continue
        sig = ("spook", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["unease"] += 1
        out.append("__spook__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("revealed") and not world.facts.get("laughed"):
        world.facts["laughed"] = True
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["joy"] += 1
                ch.memes["fear"] = max(0.0, ch.memes["fear"] - 1.0)
        out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("spook", "mood", _r_spook), Rule("laugh", "mood", _r_laugh)]


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


def mystery_risky(setting: Setting, mystery: Mystery) -> bool:
    return mystery.id in setting.tags or True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_comic(response: Response) -> bool:
    return response.calm >= 2


def tell(setting: Setting, mystery: Mystery, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Grandma", helper_gender: str = "grandmother",
         pet_name: str = "Muffin") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["brave"], room="hall"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", traits=["faithful", "calm"], room="hall"))
    ghost = world.add(Entity(id="ghost", kind="thing", type="ghost", label="the ghost",
                             room=setting.spooky_room, attrs={"cause": mystery.cause}))
    pet = world.add(Entity(id=pet_name, kind="character", type="pet", label=pet_name,
                           room="hall", traits=["nosy"]))
    child.memes["faith"] = 1.0
    helper.memes["faith"] = 2.0
    child.memes["curiosity"] = 1.0
    child.meters["courage"] = 0.5
    ghost.meters["mystery"] = 1.0
    world.facts["pet"] = pet_name

    world.say(
        f"On a windy night, {child.id} and {helper.id} stayed in {setting.house}, "
        f"where {setting.spooky_room} always seemed to sigh."
    )
    world.say(
        f"{child.id} heard {setting.sound} from deep in the house and frowned. "
        f"Even {pet_name} stopped wagging and listened."
    )

    world.para()
    child.memes["fear"] += 1.0
    world.say(
        f'{"\""}Do you think it is a ghost?{"\""} {child.id} asked. '
        f'{helper.id} smiled and said, '
        f'"Sometimes spooky sounds are just house sounds, and sometimes faith means '
        f'waiting to see."'
    )
    world.say(
        f"{mystery.fake_scary_line} {child.id} held {helper.id}'s hand anyway, "
        f"because {child.id} wanted to believe the house would answer kindly."
    )

    world.para()
    ghost.meters["mystery"] += 1.0
    child.memes["faith"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f'The floorboard groaned from {mystery.odd_sound}, and a sheet-shaped shadow '
        f"wobbled in {setting.spooky_room}. {child.id} swallowed hard, but {child.id} "
        f"kept faith and followed the clue."
    )
    world.say(
        f"{helper.id} held up a flashlight and called, "
        f'"Hello? If you are a ghost, please do not eat the cookie jar."'
    )

    world.para()
    if is_comic(response):
        child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
        world.facts["revealed"] = True
        world.say(
            f"At last, {response.action}, and the mystery stopped being spooky."
        )
        world.say(
            f"It was not a ghost at all -- just {mystery.cause}. "
            f"{mystery.reveal_line}"
        )
        propagate(world, narrate=False)
        world.say(
            f"{helper.id} laughed so hard they had to lean on the doorway, and "
            f"{child.id} laughed too, because the ghost was only trying to be dramatic."
        )
        world.para()
        world.say(
            f"By the end, {child.id}'s faith had changed into a cheerful kind of bravery."
        )
        world.say(
            f"{setting.ending_image} {response.ending} {child.id} tucked the flashlight under "
            f"one arm and smiled at the now-funny house."
        )
    else:
        world.facts["revealed"] = False
        world.say(
            f"{response.action}, but the mystery only got sillier and never quite settled."
        )
        world.say(
            f"{child.id} and {helper.id} decided to call it a night and leave the clue for morning."
        )
        world.say(
            f"{setting.ending_image} The house still creaked, but faith kept {child.id} from running."
        )

    world.facts.update(
        child=child, helper=helper, ghost=ghost, setting=setting, mystery=mystery,
        response=response, outcome="comic" if world.facts.get("revealed") else "quiet",
    )
    return world


SETTINGS = {
    "old_house": Setting(
        id="old_house",
        house="the old house on Maple Lane",
        spooky_room="the attic",
        sound="a thump-thump above the stairs",
        hiding_place="behind the curtains",
        ending_image="The attic window glowed like a sleepy moon.",
        tags={"ghost", "house", "attic"},
    ),
    "grandma_house": Setting(
        id="grandma_house",
        house="Grandma's crooked cottage",
        spooky_room="the hallway closet",
        sound="a rattle in the cupboard",
        hiding_place="under a blanket pile",
        ending_image="The porch light blinked over the sleepy yard.",
        tags={"ghost", "house", "closet"},
    ),
}

MYSTERIES = {
    "sheet_ghost": Mystery(
        id="sheet_ghost",
        clue="a white sheet with a hole in it",
        odd_sound="the wind pushing through a cracked vent",
        fake_scary_line="The sheet puffed up like a round balloon and looked very haunted.",
        reveal_line="The 'ghost' was only a laundry sheet stuck on a fan and doing its best to look important.",
        cause="a laundry sheet on a fan",
        tags={"ghost", "humor"},
    ),
    "pipes": Mystery(
        id="pipes",
        clue="a silver pipe that knocked in the wall",
        odd_sound="steam tapping the pipes",
        fake_scary_line="The wall went tick-tick-tick as if a tiny ghost drummer lived inside.",
        reveal_line="It was only the heater making silly music through the pipes.",
        cause="the heater pipes",
        tags={"ghost", "humor"},
    ),
}

RESPONSES = {
    "flashlight_joke": Response(
        id="flashlight_joke",
        sense=3,
        calm=3,
        action="They shone the flashlight on the clue and joked that even ghosts need a stage light",
        reveal="The beam showed the silly trick at once.",
        ending="The little light turned the dark corner into a joke instead of a fright.",
        tags={"light", "humor"},
    ),
    "sing_back": Response(
        id="sing_back",
        sense=2,
        calm=2,
        action="They sang a tiny brave song to the creaking house, and the creaking seemed to sing back",
        reveal="The song made everyone laugh and listen more carefully.",
        ending="The song filled the room with courage and giggles.",
        tags={"song", "humor"},
    ),
    "ignore": Response(
        id="ignore",
        sense=1,
        calm=1,
        action="They tried to ignore it",
        reveal="The sound stayed spooky and confusing.",
        ending="The house stayed mysterious and nobody felt much better.",
        tags={"low"},
    ),
}

SENSE_MIN = 2

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Luna", "Pia"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Max", "Eli"]
HELPERS = [("grandmother", "Grandma"), ("grandfather", "Grandpa")]

@dataclass
class StoryParams:
    setting: str
    mystery: str
    response: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    helper_name: str = "Grandma"
    helper_gender: str = "grandmother"
    pet_name: str = "Muffin"
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


CURATED = [
    StoryParams(setting="old_house", mystery="sheet_ghost", response="flashlight_joke",
                child_name="Mina", child_gender="girl", helper_name="Grandma",
                helper_gender="grandmother", pet_name="Muffin"),
    StoryParams(setting="grandma_house", mystery="pipes", response="sing_back",
                child_name="Owen", child_gender="boy", helper_name="Grandpa",
                helper_gender="grandfather", pet_name="Pip"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid in MYSTERIES:
            if mystery_risky(setting, MYSTERIES[mid]):
                for rid, resp in RESPONSES.items():
                    if resp.sense >= SENSE_MIN:
                        combos.append((sid, mid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with humor and faith.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too wobbly for a ghost story ending.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, response = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender, helper_name = rng.choice(HELPERS)
    return StoryParams(setting=setting, mystery=mystery, response=response,
                       child_name=child_name, child_gender=child_gender,
                       helper_name=helper_name, helper_gender=helper_gender,
                       pet_name=rng.choice(["Muffin", "Pip", "Bean"]))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a humorous ghost story for a 3-to-5-year-old that includes the word "faith" and ends with a funny reveal.',
        f"Tell a spooky-but-silly story where {f['child'].id} hears a strange sound in {f['setting'].house} and keeps faith until the mystery is solved.",
        f"Write a child-friendly ghost story with jokes, a brave helper, and a reveal that turns the scary thing into something ordinary.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    mystery = f["mystery"]
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id} in {setting.house}. They spend the night trying to understand a spooky sound."),
        ("What did the child hear?",
         f"{child.id} heard {setting.sound}. That noise made the house feel like it might be haunted."),
        ("What helped the child stay calm?",
         f"{helper.id} kept {child.id} calm with jokes and a steady voice. The child also kept faith that the mystery would make sense."),
    ]
    if f.get("revealed"):
        qa.append((
            "What was the ghost really?",
            f"It was {mystery.cause}, not a real ghost. The scary-looking clue only seemed haunted until they looked closely."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily and a little sillily. {child.id} laughed, because the ghost turned out to be funny instead of frightening."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended quietly, with the mystery still a little spooky. Even then, {child.id} kept faith and stayed brave."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is faith?",
         "Faith is a strong trust or belief, even when you cannot see everything clearly yet. It can help someone stay calm and brave."),
        ("Why can old houses feel spooky?",
         "Old houses can creak, rattle, and make odd sounds when the wind or pipes move. Those sounds can feel spooky, even when nothing is wrong."),
        ("Why are jokes useful in a scary moment?",
         "Jokes can make people smile and feel less tense. A funny moment can shrink a big scary feeling."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
ok_response(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S, M, R) :- setting(S), mystery(M), response(R), ok_response(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in clingo gate.")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, response=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        print(f"Smoke test failed: {e}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.response not in RESPONSES:
        raise StoryError("Invalid parameters for this story world.")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError("That response is too low-sense for a satisfying story.")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], RESPONSES[params.response],
                 child_name=params.child_name, child_gender=params.child_gender,
                 helper_name=params.helper_name, helper_gender=params.helper_gender,
                 pet_name=params.pet_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
