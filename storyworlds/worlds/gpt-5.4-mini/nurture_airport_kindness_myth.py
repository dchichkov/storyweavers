#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nurture_airport_kindness_myth.py
===============================================================

A standalone storyworld for a small airport myth: a child with a worried heart
discovers that kindness can be a kind of nurture. In the airport, a missed plan
turns into a gentle rescue, and the ending proves that care can calm a storm.

The domain is intentionally tiny:
- one airport setting
- one child in a small myth-like situation
- one worry that needs nurturing
- one kindness turn that changes the world state
- one warm resolution image

The story is simulation-driven: emotional meters and physical meters change the
prose, and the QA sets are generated from world state rather than from rendered
English.
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class MythFrame:
    id: str
    title: str
    opening: str
    mood_image: str
    ending_image: str
    traits: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class AirportPlace:
    id: str
    label: str
    image: str
    allows_nurture: bool = True
    traits: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Need:
    id: str
    label: str
    source: str
    remedy: str
    strain: int
    traits: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Kindness:
    id: str
    label: str
    action: str
    gift: str
    comfort: str
    strength: int
    sense: int
    traits: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    need = world.entities.get("need")
    if not child or not helper or not need:
        return out
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("kindness", child.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["hope"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    helper.memes["kindness"] += 1
    out.append("__kindness__")
    return out


def _r_nurture(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["hope"] < THRESHOLD:
        return out
    sig = ("nurture", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    world.get("airport").meters["brightness"] += 1
    out.append("__nurture__")
    return out


CAUSAL_RULES = [
    Rule("kindness", "social", _r_kindness),
    Rule("nurture", "emotional", _r_nurture),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def nurture_at_airport(place: AirportPlace, frame: MythFrame) -> bool:
    return place.id == "airport" and place.allows_nurture and "myth" in frame.traits


def kindness_gate(kindness: Kindness) -> bool:
    return kindness.sense >= SENSE_MIN


def expected_calm(need: Need, kindness: Kindness) -> bool:
    return kindness.strength >= need.strain


def predict_turn(world: World, kindness: Kindness) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["worry"] += 0.0
    apply_kindness(sim, kindness, narrate=False)
    return {
        "hope": sim.get("child").memes["hope"],
        "calm": sim.get("child").memes["calm"],
        "brightness": sim.get("airport").meters["brightness"],
    }


def apply_kindness(world: World, kindness: Kindness, narrate: bool = True) -> None:
    child = world.get("child")
    helper = world.get("helper")
    child.memes["worry"] += 1
    if narrate:
        world.say(
            f"In the airport hall, {child.id} watched the departures board shimmer "
            f"like a warning star. The crowd moved like a tide, and {child.id}'s "
            f"heart felt too small for the wide place."
        )
    child.memes["worry"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"Then {helper.id} came near with {kindness.action}. {helper.id} "
        f"{kindness.gift}, and the simple kindness felt like a lantern in fog."
    )
    propagate(world, narrate=narrate)


def setup(world: World, frame: MythFrame, place: AirportPlace, child: Entity,
          helper: Entity, need: Need) -> None:
    child.memes["worry"] = 0.0
    child.memes["joy"] = 1.0
    helper.memes["kindness"] = 0.0
    world.say(
        f"{frame.opening} {child.id} traveled through {place.label}, where "
        f"{place.image}."
    )
    world.say(
        f"{child.id} carried {need.label}, because {need.source} had left a little "
        f"strain in {child.pronoun('possessive')} chest."
    )


def tension(world: World, need: Need) -> None:
    child = world.get("child")
    child.memes["worry"] += 2.0
    world.say(
        f"{child.id} tried to be brave, but the waiting made {child.pronoun('possessive')} "
        f"worry climb higher. The need for {need.remedy} felt like a small ache in a "
        f"big, bright kingdom."
    )


def resolve(world: World, kindness: Kindness, frame: MythFrame, need: Need) -> None:
    child = world.get("child")
    helper = world.get("helper")
    world.say(
        f"When {helper.id} offered {kindness.comfort}, {child.id} breathed easier. "
        f"The kindness was not grand, but it was enough to nurture the frightened part "
        f"of {child.pronoun('object')}."
    )
    world.say(
        f"By the time the announcement echoed again, {child.id} stood straighter. "
        f"{child.pronoun().capitalize()} had {need.remedy}, {helper.id} had given care, "
        f"and the airport no longer felt like a storm."
    )
    world.say(frame.ending_image)


def tell(frame: MythFrame, place: AirportPlace, need: Need, kindness: Kindness,
         child_name: str = "Ari", child_gender: str = "girl",
         helper_name: str = "Mara", helper_gender: str = "woman") -> World:
    if not nurture_at_airport(place, frame):
        raise StoryError("This storyworld only makes sense as a myth of kindness in an airport.")
    if not kindness_gate(kindness):
        raise StoryError(f"(Refusing kindness '{kindness.id}': it is too slight for this myth.)")
    if not expected_calm(need, kindness):
        raise StoryError("This kindness is too small to soothe the need in this story.")

    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="airport", type="place", label=place.label))
    world.facts.update(frame=frame, place=place, need=need, kindness=kindness)

    setup(world, frame, place, child, helper, need)
    world.para()
    tension(world, need)
    world.para()
    apply_kindness(world, kindness)
    resolve(world, kindness, frame, need)

    child.memes["joy"] += 1.0
    child.memes["hope"] += 1.0
    child.memes["calm"] += 1.0
    world.get("airport").meters["brightness"] += 1.0
    world.facts.update(
        child=child,
        helper=helper,
        outcome="kindly_settled",
        soothed=child.memes["calm"] >= THRESHOLD,
        helped=helper.memes["kindness"] >= THRESHOLD,
    )
    return world


THEMES = {
    "myth": MythFrame(
        "myth",
        "The Kindness of the Bright Terminal",
        "Long ago, in the bright terminal where rolling bags sang on stone,",
        "The airport shimmered like a silver shell under the lamps.",
        "At the end, the airport looked warmer, as if the lamps had learned to smile.",
        traits={"myth", "kindness"},
    ),
}

PLACES = {
    "airport": AirportPlace(
        "airport",
        "the airport",
        "The halls glowed with departure boards, echoing shoes, and little voices calling home.",
        allows_nurture=True,
        traits={"airport"},
    )
}

NEEDS = {
    "lost_ticket": Need(
        "lost_ticket",
        "a lost ticket",
        "the paper had slipped away in the crowd",
        "find the ticket again",
        strain=2,
        traits={"loss", "worry"},
    ),
    "rain_delay": Need(
        "rain_delay",
        "a delayed flight",
        "the rain had slowed the sky-ride",
        "wait with patience",
        strain=2,
        traits={"waiting", "worry"},
    ),
    "homesick": Need(
        "homesick",
        "a homesick feeling",
        "the long hall had made home seem far away",
        "remember home kindly",
        strain=2,
        traits={"homesick", "worry"},
    ),
}

KINDNESSES = {
    "lantern_story": Kindness(
        "lantern_story",
        "a gentle story",
        "with a cup of tea and a low voice",
        "told a story about a lantern that found its way through fog",
        "let the child hold the warm cup",
        strength=3,
        sense=3,
        traits={"kindness", "nurture"},
    ),
    "seat_share": Kindness(
        "seat_share",
        "a shared seat",
        "by sliding over on the bench",
        "made room on the quiet bench",
        "gave the child a calm place to rest",
        strength=2,
        sense=2,
        traits={"kindness", "nurture"},
    ),
    "map_note": Kindness(
        "map_note",
        "a folded note",
        "by drawing a tiny map with a pencil",
        "drew a map that showed the path from worry to waiting",
        "helped the child see the next step",
        strength=3,
        sense=2,
        traits={"kindness", "nurture"},
    ),
}



@dataclass
class StoryParams:
    theme: str
    place: str
    need: str
    kindness: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    StoryParams("myth", "airport", "homesick", "lantern_story", "Ari", "girl", "Mara", "woman"),
    StoryParams("myth", "airport", "lost_ticket", "seat_share", "Noah", "boy", "Iris", "woman"),
    StoryParams("myth", "airport", "rain_delay", "map_note", "Mina", "girl", "Sana", "woman"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES.values():
        for p in PLACES.values():
            if not nurture_at_airport(p, t):
                continue
            for n in NEEDS.values():
                for k in KINDNESSES.values():
                    if kindness_gate(k) and expected_calm(n, k):
                        combos.append((t.id, p.id, n.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small airport myth about nurture and kindness.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man", "girl", "boy"])
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
    if args.kindness and not kindness_gate(KINDNESSES[args.kindness]):
        raise StoryError("That kindness is too slight for the story.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.place is None or c[1] == args.place)
              and (args.need is None or c[2] == args.need)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, place, need = rng.choice(sorted(combos))
    kindness = args.kindness or rng.choice(sorted(KINDNESSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(["Ari", "Mina", "Noah", "Tali", "Ivo", "Lina"])
    helper = args.helper or rng.choice(["Mara", "Iris", "Sana", "Dara", "Luca"])
    return StoryParams(theme, place, need, kindness, child, child_gender, helper, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    need = f["need"]
    kind = f["kindness"]
    return [
        f'Write a myth-like airport story that includes the word "nurture" and shows kindness calming {need.label}.',
        f"Tell a child-sized myth at the airport where {f['child'].id} is worried, and {f['helper'].id} uses {kind.label} to nurture the feeling.",
        f'Write a gentle airport legend with a beginning, a turn, and an ending image proving kindness changed the day.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    need = f["need"]
    kind = f["kindness"]
    frame = f["frame"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {helper.id} in the airport. {helper.id} helps {child.id} with a kind, nurturing act."
        ),
        QAItem(
            question=f"Why did {child.id} feel worried?",
            answer=f"{child.id} felt worried because {need.source}. The airport was busy, so the worry felt even larger until kindness helped."
        ),
        QAItem(
            question=f"What did {helper.id} do to help?",
            answer=f"{helper.id} used {kind.label} and gave {kind.comfort}. That was a nurturing kindness, so {child.id} could calm down."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the airport feeling warmer and brighter. {child.id} felt calm, and the final image showed that kindness had changed the whole day."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an airport?",
            answer="An airport is a place where people wait for airplanes, carry bags, and listen for departures."
        ),
        QAItem(
            question="What does nurture mean?",
            answer="To nurture something means to care for it gently so it can feel safe, grow, or heal."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses to help, comfort, or be gentle with another person."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
kindness_ok(K) :- kindness(K), sense(K,S), sense_min(M), S >= M.
nurture_story(T,P,N) :- theme(T), place(P), need(N), kindness_ok(_), airport(P).
calm(N,K) :- need(N), kindness(K), strength(K,S), strain(N,R), S >= R.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES.values():
        lines.append(asp.fact("theme", t.id))
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.allows_nurture:
            lines.append(asp.fact("airport", p.id))
    for n in NEEDS.values():
        lines.append(asp.fact("need", n.id))
        lines.append(asp.fact("strain", n.id, n.strain))
    for k in KINDNESSES.values():
        lines.append(asp.fact("kindness", k.id))
        lines.append(asp.fact("strength", k.id, k.strength))
        lines.append(asp.fact("sense", k.id, k.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show nurture_story/3."))
    return sorted(set(asp.atoms(model, "nurture_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection(kindness: Kindness) -> str:
    return f"(Refusing kindness '{kindness.id}': it is too slight to carry this myth.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        THEMES[params.theme],
        PLACES[params.place],
        NEEDS[params.need],
        KINDNESSES[params.kindness],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
    )
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
        print(asp_program(show="#show nurture_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible nurture-story combos.")
        for t, p, n in asp_valid_combos():
            print(f"  {t:8} {p:8} {n}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} at the airport, guided by kindness"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
