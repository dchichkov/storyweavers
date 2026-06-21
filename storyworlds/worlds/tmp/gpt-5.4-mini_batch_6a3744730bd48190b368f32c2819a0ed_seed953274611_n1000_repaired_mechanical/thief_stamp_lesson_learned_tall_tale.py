#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thief_stamp_lesson_learned_tall_tale.py
=======================================================================

A tiny tall-tale storyworld about a stamp-obsessed thief, a missing seal, and a
lesson learned.  The world is built as a small causal simulation: a foolish theft
creates a wrinkle in the town's mail, a clever helper spots the trail, the thief
is caught by consequences rather than by brute force, and the ending proves the
change with a new rule about borrowing versus stealing.

Theme words from the seed: thief, stamp
Style: Tall Tale
Feature: Lesson Learned

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/thief_stamp_lesson_learned_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/thief_stamp_lesson_learned_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/thief_stamp_lesson_learned_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/thief_stamp_lesson_learned_tall_tale.py --verify
    python storyworlds/worlds/gpt-5.4-mini/thief_stamp_lesson_learned_tall_tale.py --json
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
BRAG_MIN = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    tall_tale_color: str
    mail_pile: str
    flourish: str
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


@dataclass
class Stamp:
    id: str
    label: str
    phrase: str
    power: int
    trail: str
    kind: str = "stamp"
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Consequence:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


@dataclass
class StoryParams:
    place: str
    stamp: str
    consequence: str
    thief_name: str
    thief_gender: str
    helper_name: str
    helper_gender: str
    adult_name: str
    adult_gender: str
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
        if e.meters["stolen"] < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("town").meters["trouble"] += 1
        world.get("helper").memes["suspicion"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def sensibleness(c: Consequence) -> bool:
    return c.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for stamp in STAMPS:
            for cons in CONSEQUENCES:
                if sensibleness(CONSEQUENCES[cons]):
                    combos.append((place, stamp, cons))
    return combos


def theft_risk(place: Place, stamp: Stamp) -> bool:
    return True


def outcome_of(params: StoryParams) -> str:
    cons = CONSEQUENCES[params.consequence]
    return "lesson" if cons.power >= 2 else "embarrassment"


def reasonableness_message() -> str:
    return "(No story: this world needs a sensible consequence with enough power to make a lesson.)"


def predict_world(world: World, stamp: Stamp) -> dict:
    sim = world.copy()
    sim.get("stamp").meters["stolen"] += 1
    propagate(sim, narrate=False)
    return {"trouble": sim.get("town").meters["trouble"], "suspicion": sim.get("helper").memes["suspicion"]}


def do_theft(world: World, thief: Entity, stamp: Entity, place: Place) -> None:
    thief.memes["greed"] += 1
    stamp.meters["stolen"] += 1
    stamp.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In the broad-brimmed dawn at {place.label}, {thief.id} the thief spotted "
        f"the town's grand stamp, red as a sunset and shining like a sheriff's star."
    )
    world.say(
        f"{thief.id} swiped it quick as a whip-crack and tucked it away, thinking "
        f"the whole town would never notice one little stamp."
    )


def alarm(world: World, helper: Entity, adult: Entity) -> None:
    world.say(
        f"But {helper.id} noticed the missing seal at once and hollered for {adult.id}, "
        f"because in a town like this a stamp is the tongue of every letter."
    )


def reveal(world: World, stamp: Entity, place: Place) -> None:
    world.say(
        f"The stolen stamp left a trail of {place.tall_tale_color} wax specks across the floor, "
        f"bright enough to follow with both eyes half-shut."
    )


def catch_and_lesson(world: World, adult: Entity, thief: Entity, stamp: Entity) -> None:
    thief.memes["shame"] += 1
    thief.memes["lesson"] += 1
    stamp.meters["stolen"] = 0
    stamp.meters["home"] = 1
    world.say(
        f"{adult.id} came in with a calm voice and a faster pair of boots, not to wrestle, "
        f"but to ask why a stamp had wandered off in the first place."
    )
    world.say(
        f"{thief.id} hung {thief.pronoun('possessive')} head and admitted that wanting a thing "
        f"was not the same as being allowed to take it."
    )
    world.say(
        f"Then {adult.id} put the stamp back where it belonged and said, "
        f'"Borrow with words, or the tall river of trouble will carry you farther than you mean to go."'
    )


def ending(world: World, place: Place) -> None:
    world.say(
        f"After that, the town's letters stamped out clean and proud, and even the wind "
        f"seemed to nod at the new rule: ask first, take never."
    )
    world.say(
        f"And {place.flourish}, as the story goes, the old stamp sat safely home while "
        f"the thief learned a lesson bigger than any postage mark."
    )


def tell(place: Place, stamp: Stamp, consequence: Consequence,
         thief_name: str = "Ned", thief_gender: str = "boy",
         helper_name: str = "Mira", helper_gender: str = "girl",
         adult_name: str = "Mayor June", adult_gender: str = "woman") -> World:
    world = World()
    thief = world.add(Entity(id=thief_name, kind="character", type=thief_gender, role="thief"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    world.add(Entity(id="town", type="town", label=place.label))
    stamp_ent = world.add(Entity(id="stamp", type="stamp", label=stamp.label))

    thief.memes["brag"] = BRAG_MIN
    helper.memes["watchful"] = 4
    world.facts["place"] = place
    world.facts["stamp_cfg"] = stamp
    world.facts["consequence"] = consequence

    world.say(
        f"{place.label} was a tall-tale town where the rooftops leaned like old hats, "
        f"and the post office smelled of ink, wood smoke, and midnight pie."
    )
    world.say(
        f"Everyone knew the grand stamp because it pressed every letter with a neat red star, "
        f"and everyone knew that a thief who loved shiny things might come sniffing round."
    )

    world.para()
    do_theft(world, thief, stamp_ent, place)
    world.para()
    alarm(world, helper, adult)
    reveal(world, stamp_ent, place)
    world.para()
    if consequence.power >= 2:
        catch_and_lesson(world, adult, thief, stamp_ent)
        world.para()
        ending(world, place)
        outcome = "lesson"
    else:
        world.say(
            f"The trouble was only half-solved, and the town had to mail its letters the slow way, "
            f"which made the thief blush harder than a hot coal."
        )
        ending(world, place)
        outcome = "embarrassment"

    world.facts.update(
        thief=thief, helper=helper, adult=adult, stamp=stamp_ent, outcome=outcome,
    )
    return world


PLACES = {
    "post_town": Place(
        id="post_town",
        label="Post Town",
        tall_tale_color="gold",
        mail_pile="the moon-high mail pile",
        flourish="on a day so big it could have had its own weather",
    ),
    "river_bend": Place(
        id="river_bend",
        label="River Bend",
        tall_tale_color="copper",
        mail_pile="the river-wet mail pile",
        flourish="where the river curled like a lazy lasso",
    ),
    "haymarket": Place(
        id="haymarket",
        label="Haymarket",
        tall_tale_color="red",
        mail_pile="the hay-bale mail pile",
        flourish="under a sky wide enough for ten wagons to race",
    ),
}

STAMPS = {
    "star": Stamp(id="star", label="the grand star stamp", phrase="a red star stamp", power=3, trail="red"),
    "crown": Stamp(id="crown", label="the crown stamp", phrase="a gold crown stamp", power=3, trail="gold"),
    "sun": Stamp(id="sun", label="the sun stamp", phrase="a bright sun stamp", power=3, trail="amber"),
}

CONSEQUENCES = {
    "lesson": Consequence(
        id="lesson", sense=3, power=3,
        text="put the stamp back in a blink and gave the thief a lesson",
        fail="put the stamp back, but the lesson never quite landed",
        qa_text="put the stamp back right away and made the thief admit that stealing was wrong",
    ),
    "warning": Consequence(
        id="warning", sense=1, power=1,
        text="warned the thief, but that was too soft to count as a lesson",
        fail="warned the thief, but it was too soft to matter",
        qa_text="warned the thief",
    ),
}

THIEF_NAMES = ["Ned", "Hank", "Rufus", "Otis", "Jeb"]
HELPER_NAMES = ["Mira", "Dot", "Luna", "Penny"]
ADULT_NAMES = ["Mayor June", "Sheriff Lou", "Aunt Bea"]


CURATED = [
    StoryParams(place="post_town", stamp="star", consequence="lesson",
                thief_name="Ned", thief_gender="boy", helper_name="Mira",
                helper_gender="girl", adult_name="Mayor June", adult_gender="woman"),
    StoryParams(place="river_bend", stamp="crown", consequence="lesson",
                thief_name="Otis", thief_gender="boy", helper_name="Dot",
                helper_gender="girl", adult_name="Sheriff Lou", adult_gender="man"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a thief and a stamp.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--stamp", choices=STAMPS)
    ap.add_argument("--consequence", choices=CONSEQUENCES)
    ap.add_argument("--thief-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--adult-name")
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
              and (args.stamp is None or c[1] == args.stamp)
              and (args.consequence is None or c[2] == args.consequence)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, stamp, consequence = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        stamp=stamp,
        consequence=consequence,
        thief_name=args.thief_name or rng.choice(THIEF_NAMES),
        thief_gender="boy",
        helper_name=args.helper_name or rng.choice(HELPER_NAMES),
        helper_gender="girl",
        adult_name=args.adult_name or rng.choice(ADULT_NAMES),
        adult_gender="woman" if "June" in (args.adult_name or "") else "man",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story that includes the words "thief" and "stamp" and ends with a lesson learned.',
        f"Tell a big-feeling story set in {f['place'].label} where {f['thief'].id} the thief steals the stamp and then learns why that was wrong.",
        f"Write a child-friendly tall tale about a missing stamp, a clever helper, and a lesson about asking first.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    thief: Entity = f["thief"]
    helper: Entity = f["helper"]
    adult: Entity = f["adult"]
    stamp: Entity = f["stamp"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {thief.id}, a thief, and {helper.id}, who noticed the missing stamp. {adult.id} also helped set things right."
        ),
        QAItem(
            question="Why did the trouble start?",
            answer=f"The trouble started when {thief.id} stole the stamp from {place.label}. That made the town's mail go wrong until the stamp was found again."
        ),
        QAItem(
            question="What lesson did the thief learn?",
            answer=f"{thief.id} learned that wanting something is not the same as being allowed to take it. The better choice is to ask first instead of stealing."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stamp for?",
            answer="A stamp helps mail go out correctly because it marks the letter as ready to travel. Post offices use stamps on envelopes and packages."
        ),
        QAItem(
            question="What should you do if you want something that belongs to someone else?",
            answer="You should ask first or wait for permission. Taking it without permission is stealing, and stealing hurts trust."
        ),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
stolen(S) :- stamp(S), stolen_fact(S).
trouble(town) :- stolen(S).
lesson_learned(T) :- character(T), shame(T), stolen_fact(_).
valid(P, S, C) :- place(P), stamp(S), consequence(C), sensible(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in STAMPS:
        lines.append(asp.fact("stamp", s))
    for c, cons in CONSEQUENCES.items():
        lines.append(asp.fact("consequence", c))
        lines.append(asp.fact("sense", c, cons.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
        print("MISMATCH: ASP and Python combo gates differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"FAIL: smoke test crashed: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.stamp not in STAMPS or params.consequence not in CONSEQUENCES:
        raise StoryError("(Invalid StoryParams choice.)")
    world = tell(
        PLACES[params.place],
        STAMPS[params.stamp],
        CONSEQUENCES[params.consequence],
        thief_name=params.thief_name,
        thief_gender=params.thief_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_name=params.adult_name,
        adult_gender=params.adult_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for p, s, c in asp_valid_combos():
            print(p, s, c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
