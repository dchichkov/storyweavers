#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alarm_pinata_bugger_kindness_folk_tale.py
===========================================================================

A small folk-tale storyworld about a village fete, a hanging pinata, a noisy
alarm, and a little bugger who starts trouble until kindness wins the day.

Seed words: alarm, pinata, bugger
Feature: Kindness
Style: Folk Tale
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Place:
    id: str
    label: str
    atmosphere: str
    indoors: bool = False
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
class Mischief:
    id: str
    label: str
    makes_alarm: bool
    near: str
    trouble: str
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
class Pinata:
    id: str
    label: str
    phrase: str
    filled_with: str
    hanging: str
    fragile: bool = True
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
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
    place: str
    mischief: str
    pinata: str
    remedy: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    elder: str
    elder_gender: str
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


def _r_alarm(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["alarm"] < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.role in {"child", "helper"}:
                kid.memes["startle"] += 1
        out.append("__alarm__")
    return out


def _r_kindness(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "alarm" in world.entities:
            world.get("alarm").meters["calm"] += 1
        for kid in list(world.entities.values()):
            if kid.role in {"child", "helper"}:
                kid.memes["relief"] += 1
        out.append("__kindness__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("kindness", "social", _r_kindness)]


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


def sensible_responses() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for mis_id, mis in MISCHIEFS.items():
            for pin_id, pin in PINATAS.items():
                if place.indoors or mis.makes_alarm:
                    if pin.fragile:
                        out.append((place_id, mis_id, pin_id))
    return out


def is_reasonable_response(rid: str) -> bool:
    return REMEDIES[rid].sense >= SENSE_MIN


def outcome_of(params: StoryParams) -> str:
    if params.remedy == "gentle_words":
        return "kind"
    return "calm"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
    for mid, m in MISCHIEFS.items():
        lines.append(asp.fact("mischief", mid))
        if m.makes_alarm:
            lines.append(asp.fact("makes_alarm", mid))
    for pid in PINATAS:
        lines.append(asp.fact("pinata", pid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,Pi) :- place(P), mischief(M), pinata(Pi), indoors(P).
valid(P,M,Pi) :- place(P), mischief(M), pinata(Pi), makes_alarm(M), not indoors(P).
sensible(R) :- remedy(R), sense(R,S), sense_min(M), S >= M.
outcome(kind) :- remedy(gentle_words).
outcome(calm) :- remedy(R), sensible(R), R != gentle_words.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: alarm, pinata, bugger, kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mischief", choices=MISCHIEFS)
    ap.add_argument("--pinata", choices=PINATAS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, used: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != used] or pool
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and not is_reasonable_response(args.remedy):
        raise StoryError("That remedy is too small-minded for this story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mischief is None or c[1] == args.mischief)
              and (args.pinata is None or c[2] == args.pinata)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mischief, pinata = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["girl", "boy"])
    child = args.child or _pick_name(rng, child_gender)
    helper = args.helper or _pick_name(rng, helper_gender, used=child)
    elder = args.elder or _pick_name(rng, elder_gender, used=child)
    if elder == helper:
        elder = _pick_name(rng, elder_gender, used=child)
    return StoryParams(
        place=place, mischief=mischief, pinata=pinata, remedy=remedy,
        child=child, child_gender=child_gender,
        helper=helper, helper_gender=helper_gender,
        elder=elder, elder_gender=elder_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a young child that includes the words "alarm", "{f["pinata"].label}", and "bugger".',
        f"Tell a gentle village story where {f['child'].id} is startled by an alarm near the {f['pinata'].label}, but kindness quiets the trouble.",
        f"Write a simple story about a bugger who causes a fuss at the feast, then is met with kindness and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, elder = f["child"], f["helper"], f["elder"]
    pin = f["pinata"]
    rem = f["remedy"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {helper.id}, and {elder.id}, with a little {f['mischief'].label} bugger causing trouble near the feast.",
        ),
        QAItem(
            question="What happened near the pinata?",
            answer=f"The alarm rang and the bugger’s fuss made everyone look up at the pinata. That startled the children, but it also gave them a chance to choose kindness.",
        ),
        QAItem(
            question="How did they calm the trouble?",
            answer=f"{elder.id} used {rem.qa_text}. That gentle act softened the alarm and helped the children settle down.",
        ),
    ]
    if f["kindness_done"]:
        items.append(QAItem(
            question="What changed by the end?",
            answer=f"The alarm grew quiet, the pinata stayed safe, and the bugger was treated kindly instead of chased away. The whole village ended the tale with softer hearts.",
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an alarm?",
            answer="An alarm is a sound or signal that warns people something needs attention right away.",
        ),
        QAItem(
            question="What is a pinata?",
            answer="A pinata is a hanging decoration that people sometimes open at a party to find sweets inside.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing gentle, helpful actions that keep other people safe and feeling cared for.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder"))
    alarm = world.add(Entity(id="alarm", type="thing", label="alarm"))
    pin = world.add(Entity(id="pinata", type="thing", label=PINATAS[params.pinata].label))
    bug = world.add(Entity(id="bugger", type="thing", label=MISCHIEFS[params.mischief].label))

    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    elder.memes["kindness"] += 1
    world.say(
        f"Once in a bright village, {child.id} and {helper.id} went to the feast by the green, where {pin.label} hung over the crowd."
    )
    world.say(
        f"A little {bug.label} began to fuss, and then the {PINATAS[params.pinata].label} gave a wobble beneath the old alarm."
    )
    world.para()
    child.meters["alarm"] += 1
    bug.meters["trouble"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Bugger, bugger!" cried the folk, for the alarm had made a small fright.'
    )
    world.say(
        f"{helper.id} held {helper.pronoun('possessive')} hands together and said the bugger should not be chased with sticks."
    )
    world.para()
    elder.meters["kindness"] += 1
    if params.remedy == "gentle_words":
        world.say(
            f"{elder.id} knelt beside the bugger and spoke gentle words, as soft as bread from the oven."
        )
    else:
        world.say(
            f"{elder.id} brought out a calm song and a warm smile, which worked as well as a lantern in a dark lane."
        )
    if params.remedy == "gentle_words":
        world.say("The bugger blinked, then bowed its head, ashamed of its mischief.")
    else:
        world.say("The bugger quieted at once, and the alarm ceased its clatter.")
    propagate(world, narrate=False)
    world.say(
        f"The pinata stayed whole, and the village ended the day with sweet cakes, soft laughter, and kinder hearts."
    )
    world.facts.update(
        child=child, helper=helper, elder=elder,
        pinata=PINATAS[params.pinata], mischief=MISCHIEFS[params.mischief],
        remedy=REMEDIES[params.remedy], kindness_done=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mischief not in MISCHIEFS or params.pinata not in PINATAS or params.remedy not in REMEDIES:
        raise StoryError("Invalid story parameters.")
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


PLACES = {
    "green": Place(id="green", label="the green", atmosphere="bright", tags={"village"}),
    "hall": Place(id="hall", label="the hall", atmosphere="cozy", indoors=True, tags={"village"}),
}
MISCHIEFS = {
    "jostle": Mischief(id="jostle", label="jostling", makes_alarm=True, near="the crowd", trouble="jostled too hard", tags={"noise"}),
    "snatch": Mischief(id="snatch", label="snatching", makes_alarm=True, near="the sweets table", trouble="snatched at the ribbons", tags={"noise"}),
}
PINATAS = {
    "sun": Pinata(id="sun", label="sun-pinata", phrase="a bright sun-pinata", filled_with="sweets", hanging="from a beam", tags={"pinata"}),
    "moon": Pinata(id="moon", label="moon-pinata", phrase="a pale moon-pinata", filled_with="candies", hanging="from a branch", tags={"pinata"}),
}
REMEDIES = {
    "gentle_words": Remedy(id="gentle_words", sense=3, power=3, text="spoke gentle words to the bugger until the worry passed", fail="spoke gentle words, but the fuss kept spinning", qa_text="spoke gentle words to the bugger until the worry passed", tags={"kindness"}),
    "warm_song": Remedy(id="warm_song", sense=2, power=2, text="sang a warm song and steadied the whole ring of listeners", fail="sang a warm song, but the alarm still rattled", qa_text="sang a warm song and steadied the whole ring of listeners", tags={"kindness"}),
}
GIRL_NAMES = ["Mara", "Nina", "Iris", "Lena", "Cora", "Sana"]
BOY_NAMES = ["Pip", "Oren", "Jory", "Tomas", "Bram", "Eli"]


CURATED = [
    StoryParams(place="green", mischief="jostle", pinata="sun", remedy="gentle_words", child="Mara", child_gender="girl", helper="Pip", helper_gender="boy", elder="Nina", elder_gender="girl"),
    StoryParams(place="hall", mischief="snatch", pinata="moon", remedy="warm_song", child="Oren", child_gender="boy", helper="Lena", helper_gender="girl", elder="Bram", elder_gender="boy"),
]


def explain_rejection() -> str:
    return "(No story: the chosen parts do not make a proper folk-tale trouble and kindness pair.)"


def asp_verify_program() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses:", ", ".join(asp_sensible()))
        print()
        for row in asp_valid_combos():
            print(row)
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
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
