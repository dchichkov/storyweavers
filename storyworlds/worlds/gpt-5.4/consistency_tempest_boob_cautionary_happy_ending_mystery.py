#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/consistency_tempest_boob_cautionary_happy_ending_mystery.py
=======================================================================================

A standalone storyworld for a small cautionary mystery: during a seaside tempest,
a child hears a strange sound in an old building, imagines something spooky, and
wants to hurry toward the danger alone. A calm grown-up notices the consistency
of the sound, uses a safer method to investigate, and solves the mystery with a
happy ending.

The seed words are built into the world:
- consistency
- tempest
- boob

The word "boob" appears as the child's beloved stuffed bird, Boob, which is part
of the setup and emotional grounding of the mystery.
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

# Make shared result containers importable when run directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAREFUL_TRAITS = {"careful", "steady", "thoughtful", "patient"}


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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    room: str
    lookout: str
    ending_image: str
    affords: set[str] = field(default_factory=set)


@dataclass
class MysterySource:
    id: str
    label: str
    phrase: str
    place_text: str
    sound: str
    sound_line: str
    cause: str
    kind: str                 # outside_visible | inside_hidden
    danger: str
    fix_text: str
    clue_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    works_for: set[str]
    observe_text: str
    explain_text: str
    tags: set[str] = field(default_factory=set)


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


def _r_tempest_noise(world: World) -> list[str]:
    room = world.get("room")
    source = world.get("source")
    if room.meters["storm"] < THRESHOLD or source.meters["loose"] < THRESHOLD:
        return []
    sig = ("noise", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["rattling"] += 1
    room.meters["mystery"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "child":
            ent.memes["fear"] += 1
            ent.memes["curiosity"] += 1
    return ["__noise__"]


def _r_risk(world: World) -> list[str]:
    room = world.get("room")
    child = world.get("child")
    if room.meters["storm"] < THRESHOLD or child.meters["unsafe_step"] < THRESHOLD:
        return []
    sig = ("risk", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["slip_risk"] += 1
    child.memes["fear"] += 1
    room.meters["danger"] += 1
    return ["__risk__"]


def _r_clue(world: World) -> list[str]:
    source = world.get("source")
    helper = world.get("helper")
    if source.meters["pattern_seen"] < THRESHOLD or helper.meters["safe_check"] < THRESHOLD:
        return []
    sig = ("clue", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["explained"] += 1
    helper.memes["calm"] += 1
    child = world.get("child")
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    return ["__clue__"]


def _r_fixed(world: World) -> list[str]:
    source = world.get("source")
    if source.meters["secured"] < THRESHOLD:
        return []
    sig = ("fixed", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    source.meters["rattling"] = 0.0
    world.get("room").meters["mystery"] = 0.0
    child = world.get("child")
    helper = world.get("helper")
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    helper.memes["love"] += 1
    return ["__fixed__"]


CAUSAL_RULES = [
    Rule("tempest_noise", "physical", _r_tempest_noise),
    Rule("risk", "physical", _r_risk),
    Rule("clue", "epistemic", _r_clue),
    Rule("fixed", "physical", _r_fixed),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def method_matches(source: MysterySource, method: Method) -> bool:
    return source.kind in method.works_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for source_id in place.affords:
            source = SOURCES[source_id]
            for method_id, method in METHODS.items():
                if method_matches(source, method):
                    combos.append((place_id, source_id, method_id))
    return sorted(combos)


def close_call(trait: str, source: MysterySource) -> bool:
    return source.kind == "outside_visible" and trait not in CAREFUL_TRAITS


def explain_rejection(place: Place, source: MysterySource, method: Method) -> str:
    if source.id not in place.affords:
        return (
            f"(No story: {source.phrase} does not belong at {place.label}, so the mystery would not fit that place.)"
        )
    if not method_matches(source, method):
        return (
            f"(No story: {method.label} would not honestly reveal {source.phrase}. "
            f"Pick a method that fits a {source.kind.replace('_', ' ')} mystery.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_pattern(world: World, source_cfg: MysterySource, method_cfg: Method) -> dict:
    sim = world.copy()
    source = sim.get("source")
    helper = sim.get("helper")
    source.meters["pattern_seen"] += 1
    helper.meters["safe_check"] += 1
    propagate(sim, narrate=False)
    return {
        "explained": source.meters["explained"] >= THRESHOLD,
        "method": method_cfg.label,
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place, toy: Entity) -> None:
    world.say(
        f"{child.id} was spending the evening in {place.label} with {child.pronoun('possessive')} "
        f"{helper.label_word}. On the bed sat {toy.label}, {child.pronoun('possessive')} soft stuffed bird with one funny tilted beak."
    )
    world.say(
        f"{child.id} liked mysteries, but only the kind that ended with warm light and a clear answer."
    )


def storm_begins(world: World, place: Place) -> None:
    room = world.get("room")
    room.meters["storm"] += 1
    world.say(
        f"By nightfall a great tempest had wrapped itself around {place.label}. Rain tapped the panes, and the wind pressed at {place.lookout} as if it wanted to come in."
    )


def first_sound(world: World, source_cfg: MysterySource) -> None:
    source = world.get("source")
    source.meters["loose"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then it came: {source_cfg.sound_line}. The sound seemed to rise from {source_cfg.place_text}, and the whole room grew still."
    )


def fear_guess(world: World, child: Entity, toy: Entity) -> None:
    child.memes["imagination"] += 1
    world.say(
        f'{child.id} hugged {toy.label} tight. "What if it is a ghost?" {child.pronoun()} whispered.'
    )


def urge_to_dash(world: World, child: Entity, source_cfg: MysterySource) -> None:
    child.memes["bravery"] += 1
    if source_cfg.kind == "outside_visible":
        world.say(
            f"{child.id} took one quick step toward the outer door, ready to hurry into the storm and see for {child.pronoun('object')}self."
        )
    else:
        world.say(
            f"{child.id} looked toward the dark stair and almost started up alone, eager to solve the mystery before anyone else could."
        )


def warning(world: World, helper: Entity, child: Entity, source_cfg: MysterySource) -> None:
    helper.memes["calm"] += 1
    world.say(
        f'"Wait," said {helper.label_word.capitalize()} softly. "{source_cfg.danger}. A mystery is never worth getting hurt for."'
    )


def close_call_beat(world: World, child: Entity, helper: Entity, source_cfg: MysterySource) -> None:
    child.meters["unsafe_step"] += 1
    propagate(world, narrate=False)
    if source_cfg.kind == "outside_visible":
        world.say(
            f"The latch clicked under {child.pronoun('possessive')} hand, and a wet gust shoved the door hard enough to make {child.pronoun('object')} stumble back."
        )
    else:
        world.say(
            f"{child.id} put one foot on the dark stair, then froze when the old boards shivered under the storm."
        )
    world.say(
        f"{helper.label_word.capitalize()} drew {child.pronoun('object')} close, and {child.id} understood at once how quickly a brave idea could turn foolish."
    )


def safer_pause(world: World, child: Entity) -> None:
    child.memes["caution"] += 1
    world.say(
        f"{child.id} stopped where {child.pronoun()} was and took a slow breath instead."
    )


def observe(world: World, child: Entity, helper: Entity, source_cfg: MysterySource, method_cfg: Method) -> None:
    pred = predict_pattern(world, source_cfg, method_cfg)
    world.facts["predicted_explained"] = pred["explained"]
    world.facts["method_label"] = pred["method"]
    source = world.get("source")
    helper.meters["safe_check"] += 1
    source.meters["pattern_seen"] += 1
    propagate(world, narrate=False)
    world.say(method_cfg.observe_text.format(
        child=child.id,
        helper=helper.label_word,
        helper_cap=helper.label_word.capitalize(),
        sound=source_cfg.sound,
    ))
    world.say(
        f"After listening twice, then three times, they noticed the consistency of it. {source_cfg.clue_text}"
    )


def reveal(world: World, helper: Entity, source_cfg: MysterySource, method_cfg: Method) -> None:
    explanation = method_cfg.explain_text.format(cause=source_cfg.cause).rstrip(".") + "."
    world.say(
        f'"It is not a ghost," said {helper.label_word.capitalize()}. "{explanation}"'
    )


def fix(world: World, helper: Entity, source_cfg: MysterySource) -> None:
    source = world.get("source")
    source.meters["secured"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When the strongest gust had passed, {helper.label_word} {source_cfg.fix_text}."
    )
    world.say(
        f"The strange sound stopped so suddenly that the silence felt bright."
    )


def ending(world: World, child: Entity, helper: Entity, place: Place, toy: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f'{child.id} let out a little laugh and set {toy.label} on the windowsill. "So the mystery was only the storm being noisy in a clever way," {child.pronoun()} said.'
    )
    world.say(
        f'{helper.label_word.capitalize()} smiled. "And the clever part for us was staying safe long enough to understand it."'
    )
    world.say(
        f"Before bed, {place.ending_image}. The tempest was still roaming outside, but inside the room everything felt solved, warm, and brave."
    )


def tell(place: Place, source_cfg: MysterySource, method_cfg: Method,
         child_name: str = "Mira", child_type: str = "girl",
         helper_type: str = "aunt", trait: str = "careful") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child", traits=[trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    toy = world.add(Entity(id="toy", type="toy", label="Boob"))
    room = world.add(Entity(id="room", type="room", label=place.room))
    source = world.add(Entity(id="source", type="source", label=source_cfg.label, attrs={"kind": source_cfg.kind}))

    introduce(world, child, helper, place, toy)
    storm_begins(world, place)

    world.para()
    first_sound(world, source_cfg)
    fear_guess(world, child, toy)
    urge_to_dash(world, child, source_cfg)
    warning(world, helper, child, source_cfg)

    world.para()
    if close_call(trait, source_cfg):
        close_call_beat(world, child, helper, source_cfg)
    else:
        safer_pause(world, child)
    observe(world, child, helper, source_cfg, method_cfg)
    reveal(world, helper, source_cfg, method_cfg)

    world.para()
    fix(world, helper, source_cfg)
    ending(world, child, helper, place, toy)

    world.facts.update(
        place=place,
        source_cfg=source_cfg,
        method_cfg=method_cfg,
        child=child,
        helper=helper,
        toy=toy,
        source=source,
        close_call=close_call(trait, source_cfg),
        solved=source.meters["secured"] >= THRESHOLD,
    )
    return world


PLACES = {
    "lighthouse": Place(
        "lighthouse",
        "the old lighthouse cottage",
        "the lamp room",
        "the tall glass lookout",
        "the beacon lamp made a gold circle on the floor",
        affords={"shutter", "hook", "attic_hatch"},
    ),
    "inn": Place(
        "inn",
        "the little cliffside inn",
        "the upstairs hall",
        "the rainy front window",
        "the hallway lamp glowed on the polished banister",
        affords={"sign", "shutter"},
    ),
    "hill_house": Place(
        "hill_house",
        "the creaky house on the hill",
        "the front room",
        "the east window",
        "the fire made soft red shapes on the rug",
        affords={"attic_hatch", "sign"},
    ),
}

SOURCES = {
    "shutter": MysterySource(
        "shutter",
        "east shutter",
        "a loose shutter",
        "the outer wall by the window",
        "clack-clack",
        "Clack-clack went a shutter, then a pause, then clack-clack again",
        "the east shutter is knocking when each gust hits it",
        "outside_visible",
        "The stones are slick, and the wind is pushing hard outside",
        "waited a minute, then stepped out with a lantern and fastened the shutter hook tight",
        "Every harder gust was followed by the same double knock against the wall.",
        tags={"storm", "window", "safety"},
    ),
    "sign": MysterySource(
        "sign",
        "swinging inn sign",
        "a swinging sign",
        "the porch roof over the yard",
        "creak-thump",
        "Creak-thump came from outside, then came again after the next long gust",
        "the hanging sign is swinging on a loose chain",
        "outside_visible",
        "A storm porch is no place for a child alone in the dark",
        "went out under the porch when the gusts eased and wrapped the chain so the sign could not swing",
        "The sound returned whenever the wind curled around the porch corner.",
        tags={"storm", "porch", "safety"},
    ),
    "attic_hatch": MysterySource(
        "attic_hatch",
        "attic hatch",
        "an attic hatch",
        "the ceiling above the landing",
        "tap-scrape",
        "Tap-scrape whispered overhead, then stopped, then whispered again",
        "the attic hatch is lifting and settling in the draft",
        "inside_hidden",
        "Dark stairs and old ladders can trip you even before the storm does",
        "raised the lantern, climbed carefully, and tied the hatch latch snug",
        "The scrape came each time the draft slipped down the hall and under the hatch.",
        tags={"attic", "draft", "safety"},
    ),
    "hook": MysterySource(
        "hook",
        "lantern hook",
        "a loose lantern hook",
        "the beam above the gallery rail",
        "ting-ting",
        "Ting-ting rang above them like two tiny bells touching in the dark",
        "the loose lantern hook is tapping the beam in the wind",
        "outside_visible",
        "Wet steps around the gallery can send you sliding",
        "crossed out only after the gusts softened and tightened the hook with a wrench",
        "Each ring came when the wind found the same gap around the gallery rail.",
        tags={"storm", "metal", "safety"},
    ),
}

METHODS = {
    "window_watch": Method(
        "window_watch",
        "watching safely from the window",
        {"outside_visible"},
        "{helper_cap} drew {child} to the glass and watched without opening anything. Together they counted the gusts and listened for the {sound}.",
        "If we watch from here, we can learn that {cause}",
        tags={"window", "pattern"},
    ),
    "hall_listen": Method(
        "hall_listen",
        "listening from the hall with a lantern lit low",
        {"inside_hidden"},
        "{helper_cap} lit a small lantern and stood with {child} in the hall, well away from the stair edge. They listened for the {sound} and for the breath of moving air.",
        "If we listen from here, we can tell that {cause}",
        tags={"attic", "pattern"},
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Lily", "Eva", "June", "Clara", "Tessa", "Ruby"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Sam", "Finn", "Leo", "Max", "Eli"]
TRAITS = ["careful", "steady", "thoughtful", "patient", "curious", "bold"]
HELPERS = ["mother", "father", "aunt", "uncle"]


@dataclass
class StoryParams:
    place: str
    source: str
    method: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "storm": [(
        "What is a tempest?",
        "A tempest is a very strong storm with hard wind and rain. During a tempest, safe choices matter even more because things can be slippery and blow around."
    )],
    "window": [(
        "Why is it safer to watch a storm from inside?",
        "Inside, you are protected from slippery ground, strong wind, and flying rain. You can still learn what is happening without putting your body in danger."
    )],
    "attic": [(
        "Why can dark attic stairs be dangerous?",
        "Dark attic stairs can be steep, creaky, and hard to see on. If you hurry on them alone, you can trip or fall."
    )],
    "pattern": [(
        "What does consistency in a sound mean?",
        "Consistency means the sound keeps happening in the same way or at the same kind of moment. That can be a clue, because real causes often make the same pattern again and again."
    )],
    "safety": [(
        "What should a child do during a storm if something strange happens?",
        "Stay inside, tell a grown-up, and let the grown-up help check safely. Solving the mystery matters less than keeping everyone safe."
    )],
    "porch": [(
        "Why can a porch be unsafe during a storm?",
        "A storm can make porch boards wet and slippery, and swinging things can move suddenly. That is why children should not rush out alone."
    )],
    "draft": [(
        "What is a draft in a house?",
        "A draft is moving air that sneaks through gaps or under doors. It can make light things rattle or lift."
    )],
    "metal": [(
        "Why do loose metal parts make noise in wind?",
        "When wind shakes loose metal, the pieces tap or ring against something nearby. The same gust can make the same sound over and over."
    )],
}
KNOWLEDGE_ORDER = ["storm", "window", "attic", "pattern", "safety", "porch", "draft", "metal"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    source = f["source_cfg"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "consistency", "tempest", and "Boob".',
        f"Tell a cautionary mystery where {child.id} hears a strange sound in {place.label}, wants to investigate too fast, but {child.pronoun('possessive')} {helper.label_word} keeps {child.pronoun('object')} safe and solves the puzzle.",
        f"Write a gentle storm mystery where the strange noise turns out to come from {source.phrase}, and the ending feels warm, solved, and happy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    source = f["source_cfg"]
    method = f["method_cfg"]
    toy = f["toy"]
    hw = helper.label_word
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child staying in {place.label}, and {child.pronoun('possessive')} {hw}. {toy.label} the stuffed bird is there too, helping show how small and scared {child.id} felt at first."
        ),
        (
            "What made the mystery begin?",
            f"The mystery began when they heard {source.sound} coming from {source.place_text} during the tempest. The strange sound made the room feel spooky before they knew the real cause."
        ),
        (
            f"Why did {helper.label_word} tell {child.id} to wait?",
            f"{hw.capitalize()} told {child.id} to wait because {source.danger.lower()}. The warning mattered because solving a mystery is never as important as staying safe."
        ),
    ]
    if f["close_call"]:
        qa.append((
            f"What was the cautionary part of the story?",
            f"{child.id} almost rushed toward the danger alone and reached a risky first step. That showed how quickly fear and curiosity can push someone into an unsafe choice during a storm."
        ))
    else:
        qa.append((
            f"How did {child.id} make a safer choice?",
            f"{child.id} stopped instead of rushing forward. That pause gave {child.pronoun('object')} and {hw} time to think clearly and investigate in a safer way."
        ))
    qa.append((
        "How did they solve the mystery?",
        f"They used {method.label} and listened for the pattern instead of charging ahead. The consistency of the sound showed them that {source.cause}, so the mystery became a real clue instead of a scary guess."
    ))
    qa.append((
        "How did the story end?",
        f"{hw.capitalize()} fixed the real problem, and the strange noise stopped. The room felt warm and safe again, which proved the mystery had been solved without anyone getting hurt."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"pattern"}
    tags |= set(world.facts["source_cfg"].tags)
    tags |= set(world.facts["method_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lighthouse", "shutter", "window_watch", "Mira", "girl", "aunt", "curious"),
    StoryParams("inn", "sign", "window_watch", "Ben", "boy", "father", "bold"),
    StoryParams("hill_house", "attic_hatch", "hall_listen", "Nora", "girl", "mother", "careful"),
    StoryParams("lighthouse", "hook", "window_watch", "Theo", "boy", "uncle", "steady"),
]


def outcome_of(params: StoryParams) -> str:
    return "close_call" if close_call(params.trait, SOURCES[params.source]) else "careful_pause"


ASP_RULES = r"""
method_matches(S, M) :- source_kind(S, K), works_for(M, K).
valid(P, S, M) :- place(P), source(S), method(M), affords(P, S), method_matches(S, M).

close_call :- chosen_source(S), source_kind(S, outside_visible),
              chosen_trait(T), not careful_trait(T).
careful_pause :- not close_call.

outcome(close_call) :- close_call.
outcome(careful_pause) :- careful_pause.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.affords):
            lines.append(asp.fact("affords", pid, sid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("source_kind", sid, source.kind))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for kind in sorted(method.works_for):
            lines.append(asp.fact("works_for", mid, kind))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld: a storm sound, a risky guess, and a safe solution."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.source not in PLACES[args.place].affords:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        method = METHODS[args.method] if args.method else next(iter(METHODS.values()))
        raise StoryError(explain_rejection(place, source, method))
    if args.source and args.method and not method_matches(SOURCES[args.source], METHODS[args.method]):
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        raise StoryError(explain_rejection(place, SOURCES[args.source], METHODS[args.method]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.source is None or c[1] == args.source)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, source, method = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(place, source, method, name, gender, helper, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        SOURCES[params.source],
        METHODS[params.method],
        child_name=params.name,
        child_type=params.gender,
        helper_type=params.helper,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, method) combos:\n")
        for place, source, method in combos:
            print(f"  {place:10} {source:12} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.source} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
