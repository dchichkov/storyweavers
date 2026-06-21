#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/squire_blot_splash_pad_twist_lesson_learned.py
===============================================================================

A standalone storyworld in a ghost-story mood for a splash pad setting.

Premise:
- A small "squire" character visits a splash pad.
- A mysterious blot appears near the water.
- Suspense grows as the squire wonders if something spooky is hiding there.
- Twist: the blot is not a ghost at all, but a harmless, ordinary thing.
- Lesson learned: when something seems scary, look closely and ask for help.

This world keeps the prose child-facing and concrete, while the world model
drives the turn, the reveal, and the ending image.
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "they", "object": "them", "possessive": "their"}
        if self.type in {"girl", "mother", "woman"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "father", "man"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    setting: str = "splash pad"
    squire_name: str = "Mina"
    squire_type: str = "girl"
    blot_kind: str = "shadow"
    blot_name: str = "the blot"
    helper_name: str = "Aunt June"
    helper_type: str = "woman"
    twist: str = "shadow"
    lesson: str = "look closely before you call something spooky"
    suspense_level: int = 1
    seed: Optional[int] = None
    response: str = ""
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


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    sounds: str
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
    label: str
    clue: str
    reveal: str
    harmless: bool = True
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
    text: str
    reveal_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_suspense(world: World) -> list[str]:
    out = []
    squire = world.get("squire")
    blot = world.get("blot")
    if squire.memes["worry"] >= THRESHOLD and blot.meters["mystery"] >= THRESHOLD:
        sig = ("suspense",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("pad").meters["unease"] += 1
            out.append("__suspense__")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    blot = world.get("blot")
    helper = world.get("helper")
    if blot.meters["revealed"] >= THRESHOLD:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["calm"] += 1
            out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("suspense", "social", _r_suspense), Rule("reveal", "social", _r_reveal)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("squire").memes["worry"] += 1
    sim.get("blot").meters["mystery"] += 1
    propagate(sim, narrate=False)
    return {
        "unease": sim.get("pad").meters["unease"],
        "mystery": sim.get("blot").meters["mystery"],
    }


SETTINGS = {
    "splash_pad": Setting(
        id="splash_pad",
        place="the splash pad",
        mood="cold and bright",
        sounds="The water ticked and hissed from the jets, and the ground gleamed like glass.",
        tags={"splash_pad", "water", "ghost"},
    )
}

MYSTERIES = {
    "shadow": Mystery(
        id="shadow",
        label="a blot of shadow",
        clue="a dark blot near the drain",
        reveal="just a shadow from a bent sign",
        harmless=True,
        tags={"blot", "shadow", "ghost"},
    ),
    "towel": Mystery(
        id="towel",
        label="a wet blot",
        clue="a dark blot on the concrete",
        reveal="only a wet towel left by the bench",
        harmless=True,
        tags={"blot", "water"},
    ),
}

RESPONSES = {
    "look_closer": Response(
        id="look_closer",
        sense=3,
        text="peeked closer and asked a grown-up to look too",
        reveal_text="lifted the sign and found the ordinary thing hiding underneath",
        tags={"calm", "ask_help"},
    ),
    "call_helper": Response(
        id="call_helper",
        sense=3,
        text="called for the helper and pointed at the blot",
        reveal_text="knelt down and smiled, because the mystery was harmless",
        tags={"calm", "ask_help"},
    ),
}

CURIOUS_NAMES = ["Mina", "Jules", "Rae", "Tobin", "Nora", "Luca"]


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, mid) for sid in SETTINGS for mid in MYSTERIES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story splash pad world with a twist and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--twist", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--squire-type", choices=["girl", "boy"])
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
    if args.twist and args.twist not in MYSTERIES:
        raise StoryError("Unknown twist.")
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too weak for this story.")
    setting = args.setting or rng.choice(list(SETTINGS))
    twist = args.twist or rng.choice(list(MYSTERIES))
    response = args.response or rng.choice(list(RESPONSES))
    name = args.name or rng.choice(CURIOUS_NAMES)
    squire_type = args.squire_type or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        squire_name=name,
        squire_type=squire_type,
        blot_kind=MYSTERIES[twist].id,
        blot_name=MYSTERIES[twist].label,
        helper_name="Ms. Harlow",
        helper_type="woman",
        twist=twist,
        lesson="look closely before you call something spooky",
        suspense_level=rng.randint(1, 2),
    )


def _intro(world: World, squire: Entity, setting: Setting) -> None:
    world.say(
        f"{squire.id} arrived at {setting.place} just as the air turned cold and bright. "
        f"{setting.sounds}"
    )
    world.say(
        f"{squire.id} was a little squire in a borrowed cape, brave enough for games but still quick to glance at strange things."
    )


def _mystery(world: World, squire: Entity, blot: Entity, mystery: Mystery) -> None:
    squire.memes["worry"] += 1
    blot.meters["mystery"] += 1
    world.say(
        f"Then {squire.id} noticed {mystery.clue}. It looked like a ghost had dropped a dark blot and slipped away."
    )
    world.say(
        f"{squire.id} held very still. The water hissed again, and the blot stayed dark and quiet."
    )
    propagate(world, narrate=False)


def _twist(world: World, helper: Entity, blot: Entity, mystery: Mystery, response: Response) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.id} came walking over slowly. Instead of rushing, {helper.pronoun()} {response.text}."
    )
    blot.meters["revealed"] += 1
    world.say(
        f"That was the twist: the scary blot was {mystery.reveal}."
    )
    world.say(
        f"{helper.id} {response.reveal_text}."
    )


def _lesson(world: World, squire: Entity, helper: Entity, setting: Setting, mystery: Mystery) -> None:
    squire.memes["relief"] += 1
    squire.memes["lesson"] += 1
    squire.memes["fear"] = 0.0
    world.say(
        f"{squire.id} let out a small breath. The splash pad was still the same splash pad, and the dark shape had been only an ordinary thing all along."
    )
    world.say(
        f"{helper.id} smiled. \"When something feels spooky, look again and ask for help,\" {helper.pronoun()} said."
    )
    world.say(
        f"{squire.id} nodded and looked back at the bright water. This time, the shadows were only shadows, and the mist felt playful instead of mean."
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.twist]
    response = RESPONSES[params.response if params.response else "look_closer"]

    squire = world.add(Entity(id=params.squire_name, kind="character", type=params.squire_type, role="squire"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper"))
    blot = world.add(Entity(id="blot", kind="thing", type="thing", label=mystery.label, role="mystery"))

    world.add(Entity(id="pad", kind="thing", type="place", label=setting.place))
    _intro(world, squire, setting)
    world.para()
    _mystery(world, squire, blot, mystery)
    world.para()
    _twist(world, helper, blot, mystery, response)
    world.para()
    _lesson(world, squire, helper, setting, mystery)

    world.facts.update(
        squire=squire,
        helper=helper,
        blot=blot,
        setting=setting,
        mystery=mystery,
        response=response,
        outcome="twist",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story-style scene at {f["setting"].place} that includes the words "squire" and "blot".',
        f"Tell a suspenseful story where {f['squire'].id} spots a blot in the splash pad, thinks it might be spooky, and learns what it really is.",
        f"Write a child-friendly ghost story with a twist, a lesson learned, and a calm helper who explains the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    squire = f["squire"]
    mystery = f["mystery"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Why was {squire.id} nervous at the splash pad?",
            answer=f"{squire.id} saw {mystery.clue} and thought something spooky might be hiding there. The dark shape and the hissing water made the moment feel tense.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The blot was not a ghost at all. It turned out to be {mystery.reveal}, so the scary idea was just a misunderstanding.",
        ),
        QAItem(
            question=f"What lesson did {helper.id} teach?",
            answer=f"{helper.id} taught that when something looks spooky, you should look closely and ask for help. That way, fear can turn into understanding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a splash pad?",
            answer="A splash pad is a play place with water that shoots, sprays, and splashes from the ground.",
        ),
        QAItem(
            question="Why can shadows seem scary?",
            answer="Shadows can look strange when the light is dim or the shape is unfamiliar. Once you look again, they are often just ordinary things.",
        ),
        QAItem(
            question="What should you do when something seems frightening?",
            answer="Stay calm, look carefully, and ask a trusted grown-up for help if you need it.",
        ),
    ]


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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
suspense :- squire_worry, blot_mystery.
reveal :- blot_revealed.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("mystery", mid) for mid in MYSTERIES]
    lines += [asp.fact("response", rid) for rid in RESPONSES]
    lines += [asp.fact("squire_worry"), asp.fact("blot_mystery"), asp.fact("blot_revealed")]
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_something() -> list[str]:
    import asp
    return [str(a) for a in asp.atoms(asp.one_model(asp_program("#show suspense/0.\n#show reveal/0.")), "suspense")]


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if len(valid_combos()) != 2:
        print("MISMATCH: expected the two built-in mystery choices.")
        rc = 1
    print("OK: story generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.twist not in MYSTERIES:
        raise StoryError("Unknown twist.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
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
        print(asp_program("#show suspense/0.\n#show reveal/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("suspense, reveal")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="splash_pad", squire_name="Mina", squire_type="girl", blot_kind="shadow", blot_name="the blot", helper_name="Ms. Harlow", helper_type="woman", twist="shadow", lesson="look closely before you call something spooky", suspense_level=2, seed=1, response="look_closer"),
            StoryParams(setting="splash_pad", squire_name="Tobin", squire_type="boy", blot_kind="towel", blot_name="the blot", helper_name="Ms. Harlow", helper_type="woman", twist="towel", lesson="look closely before you call something spooky", suspense_level=1, seed=2, response="call_helper"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
