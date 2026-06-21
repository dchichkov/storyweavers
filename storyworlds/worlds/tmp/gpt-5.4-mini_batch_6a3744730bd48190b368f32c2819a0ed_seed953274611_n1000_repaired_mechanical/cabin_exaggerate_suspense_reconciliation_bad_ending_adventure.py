#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cabin_exaggerate_suspense_reconciliation_bad_ending_adventure.py
================================================================================================

A small Storyweavers world: two kids on an adventure at a cabin, a frightened
misunderstanding grows into suspense, someone exaggerates what they saw, the
group tries to reconcile, and sometimes the ending turns bad anyway.

Seed words:
- cabin
- exaggerate

Style:
- Adventure

Features:
- Suspense
- Reconciliation
- Bad Ending

This script is self-contained and uses only the Python stdlib plus the shared
``storyworlds/results.py`` containers.  The ASP helper is imported lazily only
for ASP modes.

The world is intentionally small:
- a cabin in the woods
- a trail, a lantern, a radio, a door, and a storm
- a ranger-like adult helper
- a rumor/exaggeration beat that raises tension
- a reconciliation beat that may calm feelings
- a bad-ending branch where the storm, lost light, and delay win anyway

The story model is state-driven: meters and memes accumulate and determine the
rendered prose, the QA, and the ending.
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
FEAR_LIMIT = 2.0
STORM_LIMIT = 2.0


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
    openable: bool = False
    opened: bool = False
    light_source: bool = False
    safe_light: bool = False
    stormproof: bool = False

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
        return {"mother": "mom", "father": "dad", "ranger": "ranger"}.get(self.type, self.type)
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
    dark: bool = False
    outdoors: bool = False
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
class Trouble:
    id: str
    label: str
    cause: str
    exaggeration: str
    risk: int
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
class Rescue:
    id: str
    label: str
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
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_storm(world: World) -> list[str]:
    out: list[str] = []
    cabin = world.entities.get("cabin")
    if not cabin:
        return out
    if cabin.meters["storm"] < THRESHOLD:
        return out
    sig = ("storm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["fear"] += 1
    out.append("__storm__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.get("speaker").memes["exaggeration"] < THRESHOLD:
        return out
    if world.get("listener").memes["worry"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("speaker").memes["guilt"] += 1
    world.get("listener").memes["hurt"] += 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("storm", _r_storm), Rule("conflict", _r_conflict)]


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


def cabin_at_risk(trouble: Trouble) -> bool:
    return trouble.risk >= 1


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for tr_id, tr in TROUBLES.items():
            for rs_id, rs in RESCUES.items():
                if cabin_at_risk(tr) and rs.sense >= 2:
                    combos.append((place_id, tr_id, rs_id))
    return combos


def storm_level(delay: int, place: Place, trouble: Trouble) -> int:
    return trouble.risk + delay + (1 if place.dark else 0)


def contains(rescue: Rescue, delay: int, place: Place, trouble: Trouble) -> bool:
    return rescue.power >= storm_level(delay, place, trouble)


def predict_suspense(world: World, trouble: Trouble) -> dict:
    sim = world.copy()
    sim.get("cabin").meters["storm"] += trouble.risk
    propagate(sim, narrate=False)
    return {
        "fear": sum(e.memes["fear"] for e in sim.characters()),
        "storm": sim.get("cabin").meters["storm"],
    }


def setup(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"At {place.label}, {hero.id} and {friend.id} began an adventure in the woods. "
        f"The little cabin looked warm from outside, but the trees around it made the trail feel far away."
    )


def suspense_beat(world: World, hero: Entity, friend: Entity, trouble: Trouble) -> None:
    world.say(
        f"Inside the cabin, a shadow slipped across the wall, and {friend.id} whispered, "
        f'"Did you hear that?" The room went still, and even the lantern seemed to hold its breath.'
    )
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.get("cabin").meters["storm"] += trouble.risk


def exaggerate(world: World, speaker: Entity, listener: Entity, trouble: Trouble) -> None:
    speaker.memes["exaggeration"] += 1
    world.say(
        f'{speaker.id} pointed toward the window. "I saw something huge," {speaker.pronoun()} said, '
        f'and {speaker.pronoun("possessive")} voice made it sound even bigger than it was. '
        f'"Maybe a giant wolf," {speaker.id} added, even though the sound had only been the wind.'
    )
    listener.memes["worry"] += 1


def reconcile(world: World, helper: Entity, speaker: Entity, listener: Entity, trouble: Trouble) -> None:
    helper.memes["calm"] += 1
    speaker.memes["guilt"] += 1
    listener.memes["hope"] += 1
    world.say(
        f"Then {helper.id} knelt beside them and said, "
        f'"Let’s slow down. Wind can make scary noises, and people can exaggerate when they are frightened." '
        f'{speaker.id} looked at {listener.id} and took a breath.'
    )
    world.say(
        f'{speaker.id} swallowed {speaker.pronoun("possessive")} worry. "I was scared," {speaker.id} admitted. '
        f'"I made it sound worse than it was." {listener.id} nodded, still tense, but listening.'
    )


def bad_turn(world: World, helper: Entity, rescue: Rescue, trouble: Trouble, delay: int, place: Place) -> None:
    severity = storm_level(delay, place, trouble)
    if contains(rescue, delay, place, trouble):
        helper.meters["helped"] += 1
        world.say(
            f"{helper.id} opened the cabin door, steadied the lantern, and {rescue.text.replace('{trouble}', trouble.label)}."
        )
        world.say(
            "The sound outside faded, and the children could breathe again."
        )
    else:
        world.say(
            f"{helper.id} tried to help, but {rescue.fail.replace('{trouble}', trouble.label)}."
        )
        world.get("cabin").meters["storm"] += severity
        for kid in world.characters():
            kid.memes["fear"] += 1
        world.say(
            "The storm grew louder, the lantern wobbled, and the cabin felt smaller every moment."
        )
        world.get("cabin").meters["lost"] += 1


def ending(world: World, hero: Entity, friend: Entity) -> None:
    if world.get("cabin").meters["lost"] >= THRESHOLD:
        world.say(
            f"By morning, the trail marker was gone and the cabin door was stuck shut by wet, twisting wood. "
            f"{hero.id} and {friend.id} were safe, but their adventure had turned into a hard, quiet bad ending."
        )
        world.say(
            "They walked home with muddy shoes and a heavy silence, wishing they had told the truth sooner."
        )
    else:
        world.say(
            f"The next morning, {hero.id} and {friend.id} stepped onto the porch together, the cabin behind them calm and bright."
        )


def tell(place: Place, trouble: Trouble, rescue: Rescue, hero_name: str = "Ari",
         hero_gender: str = "boy", friend_name: str = "Mina",
         friend_gender: str = "girl", helper_type: str = "ranger", delay: int = 1) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    helper = world.add(Entity(id="Ranger", kind="character", type=helper_type, label="the ranger", role="helper"))
    cabin = world.add(Entity(id="cabin", type="cabin", label="the cabin", openable=True))
    lantern = world.add(Entity(id="lantern", type="lantern", label="the lantern", light_source=True, safe_light=True))

    setup(world, hero, friend, place)
    world.para()
    suspense_beat(world, hero, friend, trouble)
    exaggerate(world, hero, friend, trouble)
    world.para()
    reconcile(world, helper, hero, friend, trouble)
    bad_turn(world, helper, rescue, trouble, delay, place)
    world.para()
    ending(world, hero, friend)

    outcome = "bad" if world.get("cabin").meters["lost"] >= THRESHOLD else "reconciled"
    world.facts.update(
        hero=hero, friend=friend, helper=helper, cabin=cabin, lantern=lantern,
        place=place, trouble=trouble, rescue=rescue, delay=delay, outcome=outcome
    )
    return world


PLACES = {
    "cabin": Place(id="cabin", label="the cabin", dark=True, outdoors=False, tags={"cabin", "adventure"}),
    "woods": Place(id="woods", label="the cabin in the woods", dark=True, outdoors=True, tags={"cabin", "woods"}),
}

TROUBLES = {
    "owl": Trouble(id="owl", label="an owl on the roof", cause="wind", exaggeration="a giant wolf", risk=1, tags={"owl", "suspense"}),
    "storm": Trouble(id="storm", label="the storm outside", cause="rain", exaggeration="a breaking tree", risk=2, tags={"storm", "suspense"}),
    "creak": Trouble(id="creak", label="a creaking beam", cause="wood", exaggeration="the cabin was collapsing", risk=2, tags={"creak", "suspense"}),
}

RESCUES = {
    "talk": Rescue(id="talk", label="calm talk", sense=3, power=1,
                   text="shut the shutters, listened to the rain, and explained that it was only the storm",
                   fail="closed the shutters too late and could not calm the storm", tags={"reconciliation"}),
    "lantern": Rescue(id="lantern", label="lantern steadiness", sense=2, power=2,
                      text="held the lantern steady while speaking softly and pointing out the safe corners of the room",
                      fail="held the lantern, but the light kept shaking in the dark", tags={"reconciliation"}),
    "door": Rescue(id="door", label="the cabin door", sense=2, power=3,
                   text="opened the door so fresh air could come in and the children could hear the woods clearly",
                   fail="opened the door, but the wind slammed it back", tags={"reconciliation"}),
    "radio": Rescue(id="radio", label="the radio", sense=1, power=1,
                    text="turned on the radio and told a joke to the children",
                    fail="fiddled with the radio, but it only crackled", tags={"bad"}),
}

HERO_NAMES = ["Ari", "Mina", "Jules", "Tia", "Noah", "Nina"]
TRAITS = ["brave", "curious", "careful", "quick-thinking", "impatient"]


@dataclass
class StoryParams:
    place: str
    trouble: str
    rescue: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    helper_type: str
    delay: int = 1
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


def explain_rejection(trouble: Trouble, rescue: Rescue) -> str:
    if rescue.sense < 2:
        return f"(No story: the chosen help is too weak for a tense cabin scene.)"
    return "(No story: this combination is not reasonable for the adventure world.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("risk", tid, t.risk))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T, R) :- place(P), trouble(T), rescue(R), risk(T, K), K >= 1, sense(R, S), S >= 2.
bad_outcome(T, R) :- trouble(T), rescue(R), power(R, P), risk(T, K), P < K.
good_outcome(T, R) :- trouble(T), rescue(R), power(R, P), risk(T, K), P >= K.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    return 0 if set(asp_valid_combos()) == set(valid_combos()) else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cabin adventure with suspense, reconciliation, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (args.trouble is None or c[1] == args.trouble)
              and (args.rescue is None or c[2] == args.rescue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, rescue = rng.choice(sorted(combos))
    hero_gender = rng.choice(["boy", "girl"])
    friend_gender = "girl" if hero_gender == "boy" else "boy"
    hero = rng.choice(HERO_NAMES)
    friend = rng.choice([n for n in HERO_NAMES if n != hero])
    return StoryParams(
        place=place, trouble=trouble, rescue=rescue, hero=hero, hero_gender=hero_gender,
        friend=friend, friend_gender=friend_gender, helper_type="ranger", delay=rng.randint(1, 3)
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.trouble not in TROUBLES or params.rescue not in RESCUES:
        raise StoryError("Invalid parameters.")
    world = tell(PLACES[params.place], TROUBLES[params.trouble], RESCUES[params.rescue],
                 hero_name=params.hero, hero_gender=params.hero_gender,
                 friend_name=params.friend, friend_gender=params.friend_gender,
                 helper_type=params.helper_type, delay=params.delay)
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
        f'Write an adventure story for a young child that includes the words "cabin" and "exaggerate".',
        f"Tell a suspenseful cabin story where {f['hero'].id} gets scared, then admits that {f['hero'].id} exaggerated what was seen.",
        "Write a small adventure with a tense misunderstanding, a calm reconciliation, and a bad ending that still feels child-facing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, helper = f["hero"], f["friend"], f["helper"]
    place, trouble, rescue = f["place"], f["trouble"], f["rescue"]
    qa = [
        ("Where were the children?",
         f"They were at {place.label}, in a little cabin adventure in the woods."),
        ("What scared them?",
         f"They heard {trouble.label}, and the quiet made it feel larger than it was."),
        ("What did {0} do wrong?".format(hero.id),
         f"{hero.id} exaggerated what {hero.pronoun()} thought {hero.pronoun('subject')} saw, making the danger sound bigger."),
        ("How did the helper respond?",
         f"{helper.id} tried to reconcile everyone by calming the room and explaining that the danger was not as huge as it seemed."),
    ]
    if f["outcome"] == "bad":
        qa.append(("How did the story end?",
                   f"It ended badly even after the reconciliation beat: the storm won, the cabin stayed trapped in fear, and the children had to face a hard morning."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a cabin?",
         "A cabin is a small house, often made of wood, sometimes found near trees or water."),
        ("What does exaggerate mean?",
         "To exaggerate means to make something sound bigger, worse, or more exciting than it really is."),
        ("Why can storms be scary at night?",
         "Storms can be scary at night because the wind, rain, and noises make it hard to tell what is safe outside."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="cabin", trouble="owl", rescue="lantern", hero="Ari", hero_gender="boy", friend="Mina", friend_gender="girl", helper_type="ranger", delay=1),
    StoryParams(place="woods", trouble="storm", rescue="door", hero="Tia", hero_gender="girl", friend="Noah", friend_gender="boy", helper_type="ranger", delay=3),
    StoryParams(place="cabin", trouble="creak", rescue="talk", hero="Jules", hero_gender="boy", friend="Nina", friend_gender="girl", helper_type="ranger", delay=2),
]


def write_story(sample: StorySample) -> None:
    print(sample.story)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    write_story(sample)
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
        try:
            sample = generate(CURATED[0])
            _ = sample.story
        except Exception as exc:
            print(f"VERIFY FAILED: {exc}")
            sys.exit(1)
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
