#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/participant_equivalent_sound_effects_slice_of_life.py
======================================================================================

A small slice-of-life storyworld about a neighborhood music table where one child
worries about being a participant, learns an equivalent way to join in, and ends
the day with a calmer, brighter rhythm.

The world is intentionally tiny:
- typed entities with physical meters and emotional memes
- a causal model that drives the prose
- natural sound effects woven into the story
- grounded Q&A sets derived from world state, not from parsing rendered text
- a Python reasonableness gate plus an inline ASP twin
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
MEMO_RISE = 1.0


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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    ambience: str
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
class Activity:
    id: str
    verb: str
    sound: str
    method: str
    equivalent_of: str
    need: str
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
class Option:
    id: str
    label: str
    phrase: str
    sound: str
    fills: str
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
class Response:
    id: str
    sense: int
    help: int
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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


def _r_rhythm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["noise"] < THRESHOLD:
            continue
        if ("rhythm", e.id) in world.fired:
            continue
        world.fired.add(("rhythm", e.id))
        e.memes["confidence"] += 1
        out.append("__rhythm__")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("shared_equivalent") and ("comfort", "group") not in world.fired:
        world.fired.add(("comfort", "group"))
        for e in world.characters():
            e.memes["calm"] += 1
            e.memes["belonging"] += 1
        out.append("__comfort__")
    return out


CAUSAL_RULES = [Rule("rhythm", _r_rhythm), Rule("comfort", _r_comfort)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def helper_at_equivalent(activity: Activity, option: Option) -> bool:
    return option.id == activity.equivalent_of


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for act_id in ACTIVITIES:
            for opt_id in OPTIONS:
                if helper_at_equivalent(ACTIVITIES[act_id], OPTIONS[opt_id]):
                    combos.append((place, act_id, opt_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    option: str
    response: str
    participant: str
    participant_gender: str
    helper: str
    helper_gender: str
    adult: str
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


def predict(world: World, activity: Activity, option: Option) -> dict:
    sim = world.copy()
    sim.get("participant").meters["noise"] += 1
    propagate(sim, narrate=False)
    return {"calm": sim.get("participant").memes["calm"], "shared": option.id == activity.equivalent_of}


def do_activity(world: World, participant: Entity, activity: Activity) -> None:
    participant.meters["noise"] += 1
    participant.memes["spark"] += 1
    world.say(f"{participant.id} leaned over the table. {activity.sound} {activity.method}.")
    propagate(world, narrate=False)


def offer(world: World, helper: Entity, participant: Entity, activity: Activity, option: Option) -> None:
    world.say(
        f"{helper.id} noticed the worry and pointed to the {option.label}. "
        f'"{option.phrase}," {helper.pronoun()} said. "It is the equivalent way to do {activity.verb}."'
    )


def decide(world: World, participant: Entity, helper: Entity, activity: Activity, option: Option) -> None:
    participant.memes["worry"] += 1
    world.say(
        f'{participant.id} frowned. "Am I still a participant if I use {option.label}?" '
        f"{helper.id} smiled and nodded."
    )


def resolve(world: World, adult: Entity, participant: Entity, helper: Entity, activity: Activity, option: Option, response: Response) -> None:
    participant.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"{adult.label_word.capitalize()} came by at the right moment and {response.text.replace('{option}', option.label)}."
    )
    world.say(
        f"The room sounded gentle again: {option.sound}, {activity.sound}, and then a soft hush."
    )
    world.say(
        f"{participant.id} was still a participant, just using an equivalent way to join in."
    )


def fail(world: World, adult: Entity, participant: Entity, helper: Entity, activity: Activity, option: Option, response: Response) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came by, but {response.fail.replace('{option}', option.label)}."
    )
    world.say("The table went quiet, and the little practice had to stop for a while.")
    world.say(f"Even so, {participant.id} held on to the idea that an equivalent could still be found later.")


def tell(activity: Activity, option: Option, response: Response,
         participant: str = "Nina", participant_gender: str = "girl",
         helper: str = "Owen", helper_gender: str = "boy",
         adult: str = "mother") -> World:
    world = World(PLACES["community_room"])
    p = world.add(Entity(id=participant, kind="character", type=participant_gender, role="participant"))
    h = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    a = world.add(Entity(id="Adult", kind="character", type=adult, role="adult", label="the adult"))

    p.memes["worry"] = 1
    h.memes["calm"] = 1
    world.say(
        f"After school, {participant} and {helper} sat by the neighborhood table in {world.place.label}. "
        f"{world.place.ambience}"
    )
    world.say(
        f"{participant} wanted to {activity.verb}, and the plan went with a steady {activity.sound}."
    )
    world.para()
    decide(world, p, h, activity, option)
    if helper_at_equivalent(activity, option):
        world.facts["shared_equivalent"] = True
        offer(world, h, p, activity, option)
        world.para()
        do_activity(world, p, activity)
        resolve(world, a, p, h, activity, option, response)
    else:
        world.facts["shared_equivalent"] = False
        world.say(f"But {option.label} was not the equivalent thing they needed.")
        world.para()
        do_activity(world, p, activity)
        fail(world, a, p, h, activity, option, response)

    world.facts.update(
        participant=p, helper=h, adult=a, activity=activity, option=option,
        response=response, outcome="shared" if helper_at_equivalent(activity, option) else "mismatch",
    )
    return world


PLACES = {
    "community_room": Place(
        id="community_room",
        label="the community room",
        ambience="A row of chairs waited by the wall, and someone had left a jar of crayons on the sill.",
        tags={"slice_of_life"},
    ),
    "kitchen_table": Place(
        id="kitchen_table",
        label="the kitchen table",
        ambience="The kettle gave a quiet little hum, and a lunch plate still had one apple slice left.",
        tags={"slice_of_life"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        ambience="A warm breeze moved the curtain, and a bike bell rang somewhere down the block.",
        tags={"slice_of_life"},
    ),
}

ACTIVITIES = {
    "drums": Activity(
        id="drums",
        verb="practice the drum pattern",
        sound="bam-bam",
        method="tap the tabletop in a neat beat",
        equivalent_of="spoons",
        need="a steady beat",
        tags={"sound", "music"},
    ),
    "puzzle": Activity(
        id="puzzle",
        verb="sort the puzzle pieces",
        sound="flip-flip",
        method="spread the pieces in little stacks",
        equivalent_of="cards",
        need="matching edges",
        tags={"quiet", "sorting"},
    ),
    "snack": Activity(
        id="snack",
        verb="make the snack tray",
        sound="clink",
        method="arrange crackers and apple slices into rows",
        equivalent_of="cups",
        need="small containers",
        tags={"home", "routine"},
    ),
}

OPTIONS = {
    "spoons": Option(
        id="spoons",
        label="two wooden spoons",
        phrase="Those spoons are the equivalent of drumsticks here.",
        sound="tok-tok",
        fills="beat",
        tags={"sound", "music"},
    ),
    "cards": Option(
        id="cards",
        label="a stack of cards",
        phrase="The cards are the equivalent set for sorting pieces by color.",
        sound="shff",
        fills="sorting",
        tags={"quiet", "sorting"},
    ),
    "cups": Option(
        id="cups",
        label="small paper cups",
        phrase="The cups are the equivalent holders for a snack tray.",
        sound="tap",
        fills="holding",
        tags={"home", "routine"},
    ),
}

RESPONSES = {
    "approve": Response(
        id="approve",
        sense=3,
        help=3,
        text='smiled and said, "That works nicely."',
        fail='smiled politely but said nothing helpful.',
        qa_text="smiled and said that it worked nicely",
        tags={"kind"},
    ),
    "show": Response(
        id="show",
        sense=3,
        help=4,
        text='showed how to match the rhythm without making the room too loud',
        fail='showed an old example, but it did not fit the moment',
        qa_text="showed how to match the rhythm without making the room too loud",
        tags={"help"},
    ),
    "remind": Response(
        id="remind",
        sense=2,
        help=2,
        text='reminded them that being a participant mattered more than using the first tool they saw',
        fail='reminded them, but the reminder came too late',
        qa_text="reminded them that being a participant mattered more than using the first tool they saw",
        tags={"kind"},
    ),
    "shout": Response(
        id="shout",
        sense=1,
        help=1,
        text='shouted over the room',
        fail='shouted over the room, which only made things louder',
        qa_text="shouted over the room",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Nina", "Maya", "Lena", "Ivy", "Sana", "Tia"]
BOY_NAMES = ["Owen", "Eli", "Milo", "Noah", "Zeke", "Jude"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a child about a participant and an equivalent way to join in, and include the word "participant".',
        f'Write a warm everyday story where {f["participant"].id} worries about being a participant, then learns an equivalent way to take part.',
        f'Create a gentle story with sound effects about {f["activity"].verb} and the word "equivalent".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p = f["participant"]
    h = f["helper"]
    a = f["adult"]
    activity = f["activity"]
    option = f["option"]
    response = f["response"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {p.id} and {h.id}, two children at a neighborhood table, plus {a.label_word}.",
        ),
        (
            f"What did {p.id} want to do?",
            f"{p.id} wanted to {activity.verb}. The little table beat made the wish feel lively and close to home.",
        ),
        (
            f"What made {p.id} worry?",
            f"{p.id} worried about being a participant and not knowing the right tool to use. That is why the equivalent choice mattered so much.",
        ),
        (
            f"What was the equivalent thing they found?",
            f"They found {option.label}. It fit the same job in a gentler way, so {p.id} could still join in.",
        ),
    ]
    if f["outcome"] == "shared":
        qa.append((
            "How did the story end?",
            f"It ended calmly. {p.id} stayed a participant, used an equivalent way to help, and the room settled into a soft, happy rhythm.",
        ))
        qa.append((
            "How did the adult respond?",
            f"{a.label_word.capitalize()} {response.qa_text}. That kept the moment kind and helped the children finish together.",
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with a mismatch and a quiet pause. The children were not done, but they knew the right equivalent could be tried later.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["activity"].tags) | set(world.facts["option"].tags)
    out = []
    if "sound" in tags:
        out.append(("What are sound effects in a story?", "Sound effects are words like bam-bam or clink that help you hear the moment in your head."))
    if "music" in tags:
        out.append(("What is a beat?", "A beat is the steady pattern you hear when someone taps, claps, or drums in time."))
    if "sorting" in tags:
        out.append(("What does equivalent mean?", "Equivalent means something that is different on the outside but works the same way for the job you need."))
    if "routine" in tags or "home" in tags:
        out.append(("Why do people use little household helpers?", "They use them because the small tool is handy, easy to reach, and good for the task."))
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
    lines = [f"--- world model state ({world.place.label}) ---"]
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, option: Option) -> str:
    return f"(No story: {option.label} is not the equivalent choice for {activity.verb}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about participant/equivalent choices with sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--option", choices=OPTIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--participant")
    ap.add_argument("--participant-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.option and args.activity:
        if not helper_at_equivalent(ACTIVITIES[args.activity], OPTIONS[args.option]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], OPTIONS[args.option]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.option is None or c[2] == args.option)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, option = rng.choice(sorted(combos))
    participant_gender = args.participant_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if participant_gender == "girl" else "girl")
    participant = args.participant or rng.choice(GIRL_NAMES if participant_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != participant])
    adult = args.adult or rng.choice(["mother", "father"])
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(
        place=place,
        activity=activity,
        option=option,
        response=response,
        participant=participant,
        participant_gender=participant_gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {params.activity}")
    if params.option not in OPTIONS:
        raise StoryError(f"Unknown option: {params.option}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if RESPONSES[params.response].sense < 2:
        raise StoryError("Response is too weak for this storyworld.")
    activity = ACTIVITIES[params.activity]
    option = OPTIONS[params.option]
    if not helper_at_equivalent(activity, option):
        raise StoryError(explain_rejection(activity, option))
    world = tell(
        activity=activity,
        option=option,
        response=RESPONSES[params.response],
        participant=params.participant,
        participant_gender=params.participant_gender,
        helper=params.helper,
        helper_gender=params.helper_gender,
        adult=params.adult,
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


ASP_RULES = r"""
equivalent(A,O) :- activity(A), option(O), needs(A,N), fills(O,N).
valid(P,A,O) :- place(P), activity(A), option(O), equivalent(A,O).
shared(participant) :- valid(_,_,_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("needs", aid, a.need))
    for oid, o in OPTIONS.items():
        lines.append(asp.fact("option", oid))
        lines.append(asp.fact("fills", oid, o.fills))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    rc = 0
    if clingo_set != python_set:
        print("MISMATCH in valid combos:")
        print("  only in clingo:", sorted(clingo_set - python_set))
        print("  only in python:", sorted(python_set - clingo_set))
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, activity=None, option=None, response=None, participant=None, participant_gender=None, helper=None, helper_gender=None, adult=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams(place="community_room", activity="drums", option="spoons", response="show", participant="Nina", participant_gender="girl", helper="Owen", helper_gender="boy", adult="mother"),
    StoryParams(place="kitchen_table", activity="snack", option="cups", response="approve", participant="Milo", participant_gender="boy", helper="Ivy", helper_gender="girl", adult="father"),
    StoryParams(place="porch", activity="puzzle", option="cards", response="remind", participant="Lena", participant_gender="girl", helper="Jude", helper_gender="boy", adult="mother"),
]


def asp_show() -> str:
    return asp_program("", "#show valid/3.\n")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
