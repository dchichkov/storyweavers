#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/majority_suspense_folk_tale.py
===============================================================

A small standalone storyworld for a folk-tale style suspense story about a
village majority, an uneasy choice, and a safer turn at the end.

Premise
-------
In a little riverside village, several townsfolk must choose what to do when
night falls and the bridge looks unsafe. Most people want one thing, but a
small, careful voice notices a better way. The story is built from simulated
state: a gathering grows tense, the danger rises, a majority leans one way, and
then the wiser choice changes the ending image.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes,
- a forward rule engine,
- a reasonableness gate,
- a Python/ASP twin,
- and grounded QA from the simulated state.

The featured seed word is "majority". The prose keeps a folk-tale rhythm and
uses suspense as the turning instrument.
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
DUSK_LIMIT = 1.0
RISK_LIMIT = 1.0


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
        female = {"woman", "girl", "mother", "grandmother", "elderwoman"}
        male = {"man", "boy", "father", "grandfather", "elderman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    foggy: bool = False
    dark: bool = False
    risky: bool = False
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
class Choice:
    id: str
    label: str
    action: str
    safe_action: str
    suspense_line: str
    consequence: str
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
    choice: str
    helper: str
    elder: str
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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    place = world.facts.get("place")
    if not place:
        return out
    plaza = world.get("place")
    if plaza.meters["dusk"] < DUSK_LIMIT:
        return out
    if plaza.meters["risk"] < RISK_LIMIT:
        return out
    sig = ("tension",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"majority", "minority", "helper", "elder"}:
            e.memes["worry"] += 1
    out.append("__tension__")
    return out


def _r_rise(world: World) -> list[str]:
    out: list[str] = []
    place = world.get("place")
    if place.meters["risk"] < 2:
        return out
    sig = ("rise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    place.meters["risk"] += 1
    out.append("The river rose a little higher, and the bridge creaked in the wind.")
    return out


CAUSAL_RULES = [Rule("tension", "social", _r_tension), Rule("rise", "physical", _r_rise)]


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


def could_besafe(place: Place, choice: Choice) -> bool:
    return place.risky and "safe" in choice.tags


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, choice in CHOICES.items():
            if could_besafe(place, choice):
                combos.append((pid, cid))
    return combos


def _do_risky(world: World, choice: Choice, narrate: bool = True) -> None:
    place = world.get("place")
    place.meters["risk"] += 1
    world.get("majority").memes["resolve"] += 1
    propagate(world, narrate=narrate)


def forecast(world: World, choice: Choice) -> dict:
    sim = world.copy()
    _do_risky(sim, choice, narrate=False)
    return {"risk": sim.get("place").meters["risk"], "worry": sim.get("minority").memes["worry"]}


def scene(world: World, place: Place, majority: Entity, minority: Entity, elder: Entity) -> None:
    world.say(
        f"At {place.label}, when the light was going and the geese were quiet, "
        f"{majority.id} and the others gathered by the river."
    )
    world.say(
        f"They were a small folk, but they had a big decision to make, and the "
        f"majority of the village would not agree at first."
    )


def suspense(world: World, choice: Choice, place: Place, minority: Entity) -> None:
    minority.memes["fear"] += 1
    world.say(choice.suspense_line)
    world.say(
        f"{minority.id} looked at the dark water and said, "
        f"\"Something here feels wrong.\""
    )


def warn(world: World, minority: Entity, elder: Entity, choice: Choice) -> bool:
    pred = forecast(world, choice)
    if pred["risk"] < 2:
        return False
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{minority.id} counted the boards, listened to the wind, and warned "
        f"that the bridge might not bear them. {elder.id} listened very still."
    )
    return True


def persuade(world: World, elder: Entity, majority: Entity) -> bool:
    if elder.memes["wisdom"] + elder.memes["calm"] >= 2:
        majority.memes["doubt"] += 1
        world.say(
            f"Then {elder.id} spoke like an old song: \"When the night is sharp, "
            f"the first path is not always the best path.\""
        )
        return True
    return False


def choose_safe(world: World, choice: Choice, place: Place, elder: Entity, majority: Entity) -> None:
    world.say(
        f"In the end, the village majority turned aside from {choice.label} and "
        f"followed {elder.id} to {choice.safe_action}."
    )
    world.say(
        f"They crossed by lantern light, and the bridge stayed behind them, "
        f"shaking in the dark but untouched."
    )
    majority.memes["relief"] += 1
    elder.memes["joy"] += 1
    place.meters["risk"] = 0.0


def choose_risky(world: World, choice: Choice, place: Place, majority: Entity) -> None:
    world.say(
        f"But if they would not listen, the majority chose {choice.action} anyway."
    )
    world.say(
        f"The boards groaned, the water leapt, and the night grew colder around "
        f"their lanterns."
    )
    majority.memes["fear"] += 1
    place.meters["risk"] += 1


def tell(place: Place, choice: Choice, helper_name: str, elder_name: str) -> World:
    world = World()
    majority = world.add(Entity(id="majority", kind="character", type="villager", role="majority"))
    minority = world.add(Entity(id=helper_name, kind="character", type="villager", role="minority"))
    elder = world.add(Entity(id=elder_name, kind="character", type="elderwoman", role="elder"))
    world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    world.facts["place"] = place.id
    majority.memes["resolve"] = 1.0
    minority.memes["calm"] = 1.0
    elder.memes["wisdom"] = 1.0
    elder.memes["calm"] = 1.0

    scene(world, place, majority, minority, elder)
    world.para()
    suspense(world, choice, place, minority)
    warn(world, minority, elder, choice)
    if persuade(world, elder, majority):
        choose_safe(world, choice, place, elder, majority)
    else:
        choose_risky(world, choice, place, majority)

    outcome = "safe"
    world.facts.update(
        majority=majority,
        minority=minority,
        elder=elder,
        choice=choice,
        place_cfg=place,
        outcome=outcome,
        warned=bool(world.facts.get("predicted_risk")),
    )
    return world


PLACES = {
    "bridge": Place(id="bridge", label="the old river bridge", foggy=True, dark=True, risky=True),
    "ford": Place(id="ford", label="the river ford", foggy=False, dark=False, risky=False),
    "hill": Place(id="hill", label="the misty hill road", foggy=True, dark=True, risky=True),
}

CHOICES = {
    "cross_bridge": Choice(
        id="cross_bridge",
        label="the bridge",
        action="cross the bridge in the fog",
        safe_action="wait for dawn by the mill",
        suspense_line="The bridge swayed, and every plank sounded like a whispered warning.",
        consequence="crossed the bridge",
        tags={"safe"},
    ),
    "take_ford": Choice(
        id="take_ford",
        label="the ford",
        action="take the shallow ford",
        safe_action="take the shallow ford",
        suspense_line="The water looked still, but the current hid under the silver skin.",
        consequence="took the ford",
        tags={"safe"},
    ),
    "hill_road": Choice(
        id="hill_road",
        label="the hill road",
        action="walk the hill road by lantern",
        safe_action="walk the hill road by lantern",
        suspense_line="The hill road vanished into the mist, and the crows would not sing.",
        consequence="walked the hill road",
        tags={"safe"},
    ),
}

CURATED = [
    StoryParams(place="bridge", choice="cross_bridge", helper="Mina", elder="Grandma"),
    StoryParams(place="hill", choice="hill_road", helper="Pip", elder="Nana"),
    StoryParams(place="bridge", choice="take_ford", helper="Wren", elder="Auntie"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place_cfg"]
    choice = f["choice"]
    return [
        f'Write a folk tale for a young child that uses the word "majority" and '
        f'builds suspense around a village decision at {place.label}.',
        f"Tell a suspenseful folk story where the village majority nearly chooses "
        f"{choice.action}, but a careful helper notices the danger first.",
        f"Write a small story about a majority, a warning, and a safer ending "
        f"beside {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place = f["place_cfg"]
    choice = f["choice"]
    majority = f["majority"]
    minority = f["minority"]
    elder = f["elder"]
    qa = [
        QAItem(
            question="Who was in the story?",
            answer=(
                f"The story is about {majority.id}, {minority.id}, and {elder.id}, "
                f"who stood together by {place.label} when the village had to decide what to do."
            ),
        ),
        QAItem(
            question="What made the story suspenseful?",
            answer=(
                f"The bridge and the fog made everyone uneasy, because it was not "
                f"clear whether the path was safe. That is why the warning mattered so much."
            ),
        ),
        QAItem(
            question="What did the majority want to do at first?",
            answer=(
                f"At first, the majority wanted to {choice.action}. The idea sounded brave, "
                f"but it also sounded risky in the dark."
            ),
        ),
    ]
    if f.get("warned"):
        qa.append(
            QAItem(
                question="Why did the helper warn the others?",
                answer=(
                    f"{minority.id} warned them because the boards, the wind, and the rising risk "
                    f"showed that the bridge could fail. {elder.id} listened, and that warning gave the village time to choose better."
                ),
            )
        )
    qa.append(
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended safely, with the village choosing {choice.safe_action}. "
                f"The dangerous bridge stayed behind in the dark, and the people reached safety with their lanterns still bright."
            ),
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a majority?",
            answer=(
                "A majority means more than half of a group. If the majority agrees, "
                "that choice has the most voices, even when a smaller voice is right."
            ),
        ),
        QAItem(
            question="Why is fog useful in a suspense story?",
            answer=(
                "Fog hides what is ahead, so people must guess and listen carefully. "
                "That uncertainty makes a story feel tense and full of wondering."
            ),
        ),
        QAItem(
            question="Why should people listen to a careful warning?",
            answer=(
                "A careful warning can stop people from stepping into danger. "
                "It is wise to slow down when the ground, water, or weather feels wrong."
            ),
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risky(place) :- place(place), foggy(place), dark(place).
tension :- place(place), risk(place, R), R >= 1.
safe_choice(cross_bridge).
safe_choice(take_ford).
safe_choice(hill_road).
majority_choice(C) :- choice(C), safe_choice(C).
outcome(safe) :- tension, majority_choice(C), choice(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.foggy:
            lines.append(asp.fact("foggy", pid))
        if place.dark:
            lines.append(asp.fact("dark", pid))
        if place.risky:
            lines.append(asp.fact("risk", pid, 1))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show outcome/1.\n#show majority_choice/1."))
    return sorted(set(asp.atoms(model, "majority_choice")))


def asp_verify() -> int:
    import asp
    rc = 0
    c = set(asp_valid_combos())
    p = set(x for x in (("cross_bridge",), ("take_ford",), ("hill_road",)))
    if c != p:
        rc = 1
        print("MISMATCH in ASP validity.")
    else:
        print("OK: ASP program loaded.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale suspense storyworld about a village majority.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
              and (args.choice is None or c[1] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, choice = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        choice=choice,
        helper=args.helper or rng.choice(["Mina", "Pip", "Wren", "Tia"]),
        elder=args.elder or rng.choice(["Grandma", "Nana", "Auntie"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.choice not in CHOICES:
        raise StoryError(f"Unknown choice: {params.choice}")
    world = tell(PLACES[params.place], CHOICES[params.choice], params.helper, params.elder)
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
        print(asp_program("#show majority_choice/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(c[0] for c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
