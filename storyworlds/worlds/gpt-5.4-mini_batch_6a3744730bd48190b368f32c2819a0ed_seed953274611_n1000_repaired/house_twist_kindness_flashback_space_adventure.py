#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/house_twist_kindness_flashback_space_adventure.py
=================================================================================

A standalone storyworld for a tiny space-adventure in and around a house:
a child plans a pretend mission, a twist changes the goal, kindness solves the
problem, and a flashback reveals why the ending matters.

The world is intentionally small and classical: typed entities, physical meters,
emotional memes, causal state changes, three QA sets, and an inline ASP twin for
reasonableness checks.
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

HOUSE_HUM = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    room: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class SpaceKit:
    id: str
    label: str
    verb: str
    mission: str
    shine: str
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
class TwistCard:
    id: str
    label: str
    reveal: str
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
class KindnessMove:
    id: str
    label: str
    action: str
    result: str
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
class FlashbackCard:
    id: str
    label: str
    memory: str
    reason: str
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
        c.facts = dict(self.facts)
        return c


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


def _r_spread(w: World) -> list[str]:
    out: list[str] = []
    if w.get("ship").meters["drift"] >= HOUSE_HUM and ("spread",) not in w.fired:
        w.fired.add(("spread",))
        w.get("room").meters["wonder"] += 1
        w.get("hero").memes["curiosity"] += 1
        out.append("The little ship felt even more real.")
    return out


def _r_kindness(w: World) -> list[str]:
    out: list[str] = []
    if w.get("helper").memes["kindness"] >= HOUSE_HUM and ("kindness",) not in w.fired:
        w.fired.add(("kindness",))
        w.get("hero").memes["warmth"] += 1
        w.get("helper").memes["pride"] += 1
        out.append("The room grew warm with help.")
    return out


RULES = [Rule("spread", _r_spread), Rule("kindness", _r_kindness)]


def propagate(w: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            s = rule.apply(w)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            w.say(s)
    return produced


def predict_twist(w: World) -> dict:
    sim = w.copy()
    sim.get("ship").meters["drift"] += 1
    propagate(sim, narrate=False)
    return {
        "wonder": sim.get("room").meters["wonder"],
        "warmth": sim.get("hero").memes["warmth"],
    }


def flashback(w: World, card: FlashbackCard) -> None:
    w.say(
        f"A flashback flickered through {w.get('hero').id}'s mind: {card.memory}. "
        f"It mattered now because {card.reason}."
    )


def tell(spacekit: SpaceKit, twist: TwistCard, kindness: KindnessMove, flashback_card: FlashbackCard) -> World:
    w = World()
    hero = w.add(Entity(id="Mina", kind="character", type="girl", role="hero", label="Mina"))
    helper = w.add(Entity(id="Dad", kind="character", type="father", role="helper", label="Dad"))
    ship = w.add(Entity(id="ship", type="thing", label="cardboard spaceship"))
    room = w.add(Entity(id="room", type="room", label="the living room"))
    beacon = w.add(Entity(id="beacon", type="thing", label=spacekit.label, tags=set(spacekit.tags)))

    hero.memes["hope"] += 1
    helper.memes["kindness"] = 0
    ship.meters["drift"] = 0

    w.say(
        f"Mina turned the house into a space station. The couch became a control seat, "
        f"the hallway became a moon tunnel, and a cardboard spaceship waited by the rug."
    )
    w.say(
        f'She wanted to {spacekit.verb} and reach "{spacekit.mission}". '
        f'The shiny {spacekit.label} {spacekit.shine}.'
    )

    w.para()
    pred = predict_twist(w)
    w.facts["pred"] = pred
    w.say(
        f"Then the twist arrived: {twist.reveal}. The mission changed in a blink."
    )
    ship.meters["drift"] += 1
    propagate(w, narrate=False)
    w.say(
        f"Mina paused, looking from the beacon to {helper.id}. She could keep chasing the old plan, "
        f"or use the new one."
    )

    w.para()
    helper.memes["kindness"] += 1
    w.say(
        f"Dad chose kindness. {kindness.action}, and {kindness.result}."
    )
    w.say(
        f"Mina nodded. Together they followed the new signal, and the cardboard ship slid across the rug "
        f"like it was really sailing a silver sea."
    )
    flashback(w, flashback_card)
    w.say(
        f"Years, or at least a whole bedtime, had passed since that memory: {flashback_card.memory}. "
        f"Now the house felt bigger because Mina knew how to change course and keep going."
    )

    w.facts.update(
        hero=hero,
        helper=helper,
        spacekit=spacekit,
        twist=twist,
        kindness=kindness,
        flashback=flashback_card,
        outcome="kind",
    )
    return w


SPACEKITS = {
    "beacon": SpaceKit(
        id="beacon",
        label="little star beacon",
        verb="follow the little star beacon",
        mission="the bright moon room",
        shine="blinked blue and gold",
        tags={"space", "light"},
    ),
    "scanner": SpaceKit(
        id="scanner",
        label="tiny moon scanner",
        verb="scan the house for moon rocks",
        mission="the secret crater under the table",
        shine="whirred softly and glowed green",
        tags={"space", "search"},
    ),
}

TWISTS = {
    "lost_cat": TwistCard(
        id="lost_cat",
        label="twist",
        reveal="the beacon was not a moon signal at all -- it was the family cat trapped behind the laundry basket",
        tags={"twist", "cat"},
    ),
    "rain_alarm": TwistCard(
        id="rain_alarm",
        label="twist",
        reveal="the blinking light was actually the rain alarm telling everyone the kitchen window was open",
        tags={"twist", "home"},
    ),
}

KINDNESSES = {
    "lift_basket": KindnessMove(
        id="lift_basket",
        label="kindness",
        action="Dad lifted the laundry basket with a careful grin",
        result="the cat leaped free and rubbed its head against Mina's hand",
        tags={"kindness", "cat"},
    ),
    "close_window": KindnessMove(
        id="close_window",
        label="kindness",
        action="Dad closed the open kitchen window and brought in a towel",
        result="the house grew calm again and the alarm blinked off",
        tags={"kindness", "home"},
    ),
}

FLASHBACKS = {
    "lost_paint": FlashbackCard(
        id="lost_paint",
        label="flashback",
        memory="Mina once lost her favorite rocket drawing in the same basket",
        reason="Dad had kindly helped her find it without laughing",
        tags={"flashback", "memory"},
    ),
    "night_light": FlashbackCard(
        id="night_light",
        label="flashback",
        memory="Dad had once given Mina a tiny night light for a dark hallway",
        reason="it showed her that a small light can make a scary room feel safe",
        tags={"flashback", "memory"},
    ),
}


@dataclass
class StoryParams:
    spacekit: str
    twist: str
    kindness: str
    flashback: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sk in SPACEKITS:
        for tw in TWISTS:
            for kd in KINDNESSES:
                for fb in FLASHBACKS:
                    combos.append((sk, tw, kd, fb))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny house-space-adventure storyworld.")
    ap.add_argument("--spacekit", choices=SPACEKITS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
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
    if args.spacekit and args.spacekit not in SPACEKITS:
        raise StoryError("Unknown spacekit.")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("Unknown twist.")
    if args.kindness and args.kindness not in KINDNESSES:
        raise StoryError("Unknown kindness.")
    if args.flashback and args.flashback not in FLASHBACKS:
        raise StoryError("Unknown flashback.")
    combos = [c for c in valid_combos()
              if (args.spacekit is None or c[0] == args.spacekit)
              and (args.twist is None or c[1] == args.twist)
              and (args.kindness is None or c[2] == args.kindness)
              and (args.flashback is None or c[3] == args.flashback)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sk, tw, kd, fb = rng.choice(combos)
    return StoryParams(spacekit=sk, twist=tw, kindness=kd, flashback=fb)


def generate(params: StoryParams) -> StorySample:
    if params.spacekit not in SPACEKITS or params.twist not in TWISTS or params.kindness not in KINDNESSES or params.flashback not in FLASHBACKS:
        raise StoryError("Invalid params.")
    world = tell(SPACEKITS[params.spacekit], TWISTS[params.twist], KINDNESSES[params.kindness], FLASHBACKS[params.flashback])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story set in a house that includes the word "house" and a twist.',
        f"Tell a child-friendly story where Mina uses {f['spacekit'].label} for a space mission, then learns a twist and responds with kindness.",
        f'Write a short bedtime space adventure with a flashback that explains why kindness matters.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    fb = f["flashback"]
    tw = f["twist"]
    kd = f["kindness"]
    return [
        ("What kind of place was the house in the story?",
         "It became a pretend space station. Mina made the rooms feel like part of a moon mission."),
        ("What was the twist?",
         f"{tw.reveal}. That changed the mission from chasing a signal to helping with a real problem."),
        ("How did Dad show kindness?",
         f"{kd.action.lower()}, and {kd.result}. He helped instead of scolding, so Mina could feel safe."),
        ("Why was the flashback important?",
         f"It showed that Dad had helped Mina kindly before. That memory made the new kindness feel even bigger."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a flashback in a story?",
         "A flashback is a memory from before the main moment of the story. Writers use it to explain why something matters now."),
        ("What is a twist in a story?",
         "A twist is a surprising turn that changes what the characters think is happening. It makes the story feel different and exciting."),
        ("What is kindness?",
         "Kindness means helping, caring, and being gentle with someone. Kindness can make a hard moment feel better."),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            m = {k: v for k, v in e.meters.items() if v}
            if m:
                bits.append(f"meters={m}")
        if e.memes:
            m = {k: v for k, v in e.memes.items() if v}
            if m:
                bits.append(f"memes={m}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(spacekit="beacon", twist="lost_cat", kindness="lift_basket", flashback="lost_paint"),
    StoryParams(spacekit="scanner", twist="rain_alarm", kindness="close_window", flashback="night_light"),
]


def explain_rejection() -> str:
    return "(No story: the chosen combination has no story-shaped twist/kindness/flashback path.)"


ASP_RULES = r"""
valid(S,T,K,F) :- spacekit(S), twist(T), kindness(K), flashback(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SPACEKITS:
        lines.append(asp.fact("spacekit", s))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    for k in KINDNESSES:
        lines.append(asp.fact("kindness", k))
    for f in FLASHBACKS:
        lines.append(asp.fact("flashback", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            sample = generate(CURATED[0])
            emit(sample)
        if not buf.getvalue().strip():
            print("MISMATCH: smoke test produced no output.")
            rc = 1
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


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
        print(f"{len(asp_valid_combos())} compatible combos.")
        for c in asp_valid_combos():
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = "### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
