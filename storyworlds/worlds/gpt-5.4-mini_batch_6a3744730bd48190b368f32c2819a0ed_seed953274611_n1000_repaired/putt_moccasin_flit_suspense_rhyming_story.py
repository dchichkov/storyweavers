#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/putt_moccasin_flit_suspense_rhyming_story.py
=============================================================================

A small standalone storyworld for a rhyming, suspenseful TinyStories-style tale.

Seed words:
- putt
- moccasin
- flit

Premise:
A child is playing a dusk-time putting game in the garden. A loose moccasin, a
flitting moth, and a narrow path create suspense: will the ball roll into the
dark drain, or will the child choose a careful putt and finish the game safely?

The world uses typed entities with physical meters and emotional memes, a tiny
forward rule engine, a reasonableness gate, QA generation from world state, and
an inline ASP twin for parity checks.
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
BRAVE_MIN = 4.0


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
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandfather": "grandpa", "grandmother": "grandma"}.get(self.type, self.type)
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
    twilight: bool = False
    has_drain: bool = False
    has_path: bool = False
    has_garden_light: bool = False
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
class ToyBall:
    id: str
    label: str
    phrase: str
    rolls_fast: bool = True
    fits_hole: bool = True
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
class Shoe:
    id: str
    label: str
    phrase: str
    is_moccasin: bool = False
    loose: bool = False
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
class Helper:
    id: str
    label: str
    phrase: str
    light: bool = False
    watches: bool = False
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
class StoryParams:
    place: str
    ball: str
    shoe: str
    helper: str
    child: str
    child_gender: str
    adult: str
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


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]
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


PLACES = {
    "garden": Place(id="garden", label="the garden", twilight=True, has_drain=True, has_path=True, has_garden_light=True),
    "courtyard": Place(id="courtyard", label="the courtyard", twilight=True, has_drain=True, has_path=True, has_garden_light=False),
    "porch": Place(id="porch", label="the porch", twilight=True, has_drain=False, has_path=True, has_garden_light=True),
}

BALLS = {
    "red": ToyBall(id="red", label="red ball", phrase="a red ball", rolls_fast=True, fits_hole=True),
    "striped": ToyBall(id="striped", label="striped ball", phrase="a striped ball", rolls_fast=False, fits_hole=True),
}

SHOES = {
    "moccasin": Shoe(id="moccasin", label="moccasin", phrase="a soft moccasin", is_moccasin=True, loose=True),
    "boot": Shoe(id="boot", label="boot", phrase="a little boot", is_moccasin=False, loose=False),
}

HELPERS = {
    "moth": Helper(id="moth", label="moth", phrase="a pale moth", light=False, watches=False),
    "lantern": Helper(id="lantern", label="lantern", phrase="a lantern", light=True, watches=True),
    "firefly": Helper(id="firefly", label="firefly", phrase="a firefly", light=False, watches=True),
}

GIRL_NAMES = ["Lily", "Mina", "Zoe", "Ava", "Mia"]
BOY_NAMES = ["Tom", "Finn", "Leo", "Noah", "Max"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        if not place.has_path:
            continue
        for bid, ball in BALLS.items():
            for sid, shoe in SHOES.items():
                for hid, helper in HELPERS.items():
                    if place.has_drain and ball.fits_hole and shoe.loose:
                        out.append((pid, bid, sid, hid))
    return out


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming suspense storyworld about a putt, a moccasin, and a flit.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ball", choices=BALLS)
    ap.add_argument("--shoe", choices=SHOES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather"])
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
              and (args.ball is None or c[1] == args.ball)
              and (args.shoe is None or c[2] == args.shoe)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.shoe == "moccasin" and args.place == "porch":
        raise StoryError("(No story: a porch without a drain removes the suspenseful risk this world needs.)")
    place, ball, shoe, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(list({"mother", "father", "grandmother", "grandfather"}))
    return StoryParams(place=place, ball=ball, shoe=shoe, helper=helper, child=name, child_gender=gender, adult=adult, adult_gender="woman" if adult in {"mother", "grandmother"} else "man")


def _do_putt(world: World, child: Entity, ball: Entity, place: Place, narrate: bool = True) -> None:
    child.memes["hope"] += 1
    ball.meters["roll"] += 1
    if place.has_drain:
        ball.meters["danger"] += 1
    if narrate:
        world.say(f"{child.id} took a careful putt in the fading light.")


def _r_danger(world: World) -> list[str]:
    out = []
    ball = world.get("ball")
    place = world.get("place")
    if ball.meters["roll"] >= THRESHOLD and place.meters["near_drain"] >= THRESHOLD:
        sig = ("danger",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["suspense"] += 1
            out.append("__suspense__")
    return out


CAUSAL_RULES = [Rule("danger", _r_danger)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def predict(world: World) -> dict:
    sim = world.copy()
    _do_putt(sim, sim.get("child"), sim.get("ball"), PLACES[sim.facts["place"]], narrate=False)
    return {"danger": sim.get("child").memes["suspense"]}


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.ball not in BALLS or params.shoe not in SHOES or params.helper not in HELPERS:
        raise StoryError("Invalid parameters for this storyworld.")
    place = PLACES[params.place]
    ball = BALLS[params.ball]
    shoe = SHOES[params.shoe]
    helper = HELPERS[params.helper]

    w = World()
    child = w.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", traits=["careful"], attrs={"shoe": shoe.id}))
    adult = w.add(Entity(id="Adult", kind="character", type=params.adult_gender, role="adult", label="the adult"))
    pl = w.add(Entity(id="place", type="place", label=place.label))
    bl = w.add(Entity(id="ball", type="ball", label=ball.label))
    sh = w.add(Entity(id="shoe", type="shoe", label=shoe.label))
    hl = w.add(Entity(id="helper", type="helper", label=helper.label))

    child.memes["curious"] += 1
    child.memes["joy"] += 1
    pl.meters["near_drain"] = 1.0 if place.has_drain else 0.0
    w.say(f"{params.child} went out at dusk to play a little putt, with {shoe.phrase} on one foot.")
    w.say(f"By the hedge, {helper.phrase} seemed to flit and blink, and the garden grew quiet and soft.")

    w.para()
    child.memes["worry"] += 1
    w.say(f"The ball looked small, the path looked long, and the drain looked dark as a midnight song.")
    w.say(f"{params.child} wanted one clean putt to make the ball roll light, but a loose moccasin could spoil the night.")

    w.para()
    _do_putt(w, child, bl, place)
    if place.has_drain:
        propagate(w, narrate=False)
        child.memes["suspense"] += 1
        w.say(f"The ball began to flit and skim, and everyone watched with breath held in.")
        if shoe.loose:
            w.say(f"The moccasin slipped with a little tap; the child paused, then steadied the strap.")
        if helper.light:
            w.say(f"{helper.phrase.capitalize()} glowed near the grass, showing the rim so the ball could pass.")
        else:
            w.say(f"{helper.phrase.capitalize()} drifted by, a tiny blink, and made the shadows seem to wink.")

    w.para()
    child.memes["courage"] += 1
    if place.has_drain and shoe.loose:
        w.say(f"The adult said, “Slow feet, small sweep, and watch the rim.”")
        w.say(f"So {params.child} made a gentler putt, and the ball slid safe instead of grim.")
    else:
        w.say(f"The adult smiled wide and kept watch near, and the last little putt rang bright and clear.")

    if place.has_drain:
        w.say(f"It rolled by the drain and into the cup, and the child gave a cheer as the moon came up.")
    else:
        w.say(f"It rolled straight home with a merry spin, and the game ended happy with a sleepy grin.")

    w.facts.update(place=params.place, ball=params.ball, shoe=params.shoe, helper=params.helper, child=child, adult=adult, outcome="safe", suspense=child.memes["suspense"] >= THRESHOLD)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming suspense story for a young child that includes the words "putt", "moccasin", and "flit".',
        f"Tell a gentle dusk-time story where {f['child'].id} makes a putt, a moccasin slips, and a flitting little helper adds suspense.",
        "Write a tiny rhyming story that feels a little tense but ends safely after a careful putt.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {child.id}, who is out in the garden with {adult.label_word if adult.label_word else 'an adult'}. The child is trying a careful game and watching the dark path closely."),
        QAItem(question="Why was there suspense?", answer="The path was near a drain, so the ball could roll into the dark spot if the putt was not careful. The loose moccasin and the flitting helper made everyone pause and watch."),
        QAItem(question="How did the story end?", answer="It ended safely, with the ball rolling into the cup instead of the drain. The child stayed steady, and the final image is a calm garden under the evening sky."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a putt?", answer="A putt is a gentle hit that sends a ball rolling toward a target. People use careful putting when they want the ball to go just a little way."),
        QAItem(question="What is a moccasin?", answer="A moccasin is a soft shoe or slipper. It can feel cozy, but if it is loose it may slip on a busy path."),
        QAItem(question="What does it mean when something flits?", answer="When something flits, it moves quickly and lightly from place to place. A moth or firefly can flit in the dark like a tiny blink."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,B,S,H) :- place(P), ball(B), shoe(S), helper(H), drain_place(P), moccasin(S), flit_helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].has_drain:
            lines.append(asp.fact("drain_place", p))
    for b in BALLS:
        lines.append(asp.fact("ball", b))
    for s in SHOES:
        lines.append(asp.fact("shoe", s))
        if SHOES[s].is_moccasin:
            lines.append(asp.fact("moccasin", s))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
        if h in {"moth", "firefly"}:
            lines.append(asp.fact("flit_helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos().")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, ball=None, shoe=None, helper=None, name=None, gender=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {e}")
    return rc


CURATED = [
    StoryParams(place="garden", ball="red", shoe="moccasin", helper="moth", child="Lily", child_gender="girl", adult="mother", adult_gender="woman"),
    StoryParams(place="courtyard", ball="striped", shoe="moccasin", helper="firefly", child="Tom", child_gender="boy", adult="grandfather", adult_gender="man"),
    StoryParams(place="porch", ball="red", shoe="boot", helper="lantern", child="Mia", child_gender="girl", adult="father", adult_gender="man"),
]


def generate(params: StoryParams) -> StorySample:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
