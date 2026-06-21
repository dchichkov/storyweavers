#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/death_catalogue_bravery_bedtime_story.py
========================================================================

A tiny bedtime-story world about a child, a curious catalogue, and the brave
moment of asking about the word death.

The story stays gentle: a child finds a midnight catalogue in a quiet room, the
word death scares them, and bravery carries them through the worry so a grown-up
can explain the page and the child can rest peacefully.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/death_catalogue_bravery_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/death_catalogue_bravery_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/death_catalogue_bravery_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/death_catalogue_bravery_bedtime_story.py --verify
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
BRAVERY_INIT = 5.0
CALM_MIN = 2


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
class Room:
    id: str
    label: str
    dim: str
    quiet: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Catalogue:
    id: str
    label: str
    phrase: str
    title: str
    contains_word: str
    weight: int
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
class SourcePage:
    id: str
    label: str
    description: str
    worry_word: str
    gentle_meaning: str
    scary: bool = False
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
class Comfort:
    id: str
    label: str
    phrase: str
    glow: str
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
    effect: int
    text: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.room = Room(id="room", label="the nursery", dim="quiet and dim")

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
        clone.room = copy.deepcopy(self.room)
        clone.paragraphs = [[]]
        return clone


def _r_bury(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("bury",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["bravery"] += 1
    out.append("__tremble__")
    return out


CAUSAL_RULES = [("bury", _r_bury)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= CALM_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for cat in CATALOGUES:
            for page in PAGES:
                if cat.contains_word in page.worry_word or page.scary:
                    combos.append((room, cat.id, page.id))
    return combos


@dataclass
class StoryParams:
    room: str
    catalogue: str
    page: str
    comfort: str
    response: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    parent_name: str = "Mom"
    parent_gender: str = "mother"
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


ROOMS = {
    "nursery": Room(id="nursery", label="the nursery", dim="quiet and dim"),
    "reading_nook": Room(id="reading_nook", label="the reading nook", dim="soft and sleepy"),
}

CATALOGUES = {
    "moon_catalogue": Catalogue(
        id="moon_catalogue",
        label="a moon catalogue",
        phrase="a moon catalogue with silver tabs",
        title="Catalogue of Night Things",
        contains_word="death",
        weight=1,
        tags={"catalogue", "moon"},
    ),
    "garden_catalogue": Catalogue(
        id="garden_catalogue",
        label="a garden catalogue",
        phrase="a garden catalogue with pressed flowers",
        title="Catalogue of Lost Blooms",
        contains_word="death",
        weight=1,
        tags={"catalogue", "garden"},
    ),
}

PAGES = {
    "rose_page": SourcePage(
        id="rose_page",
        label="the rose page",
        description="a page about the death of a rose in winter",
        worry_word="death",
        gentle_meaning="the ending of a flower's bright season",
        scary=True,
        tags={"death", "flower"},
    ),
    "night_page": SourcePage(
        id="night_page",
        label="the night page",
        description="a page about the death of daylight at bedtime",
        worry_word="death",
        gentle_meaning="daylight ending so night can begin",
        scary=True,
        tags={"death", "night"},
    ),
}

COMFORTS = {
    "bear": Comfort(id="bear", label="teddy bear", phrase="a soft teddy bear", glow="warm and familiar", tags={"comfort"}),
    "lamp": Comfort(id="lamp", label="night lamp", phrase="a tiny night lamp", glow="golden and calm", tags={"light"}),
}

RESPONSES = {
    "ask": Response(
        id="ask",
        sense=3,
        effect=3,
        text="opened the catalogue on her lap and asked a grown-up what the word death meant",
        qa_text="opened the catalogue on her lap and asked a grown-up what the word death meant",
        tags={"ask", "bravery"},
    ),
    "close_book": Response(
        id="close_book",
        sense=1,
        effect=1,
        text="closed the catalogue and hid it under the pillow",
        qa_text="closed the catalogue and hid it under the pillow",
        tags={"avoid"},
    ),
    "read_aloud": Response(
        id="read_aloud",
        sense=2,
        effect=2,
        text="read the page out loud, very slowly, until the scary word sounded smaller",
        qa_text="read the page out loud, very slowly, until the scary word sounded smaller",
        tags={"bravery"},
    ),
}

GROWNUP_NAMES = ["Mom", "Dad", "Auntie", "Grandma"]
CHILD_NAMES = ["Mina", "Noa", "Toby", "Lia", "Jules"]


def cautious_choice(page: SourcePage, response: Response) -> bool:
    return page.scary and response.sense >= CALM_MIN


def explanation_for_rejection(page: SourcePage, response: Response) -> str:
    if response.sense < CALM_MIN:
        return "(No story: that response is too timid for this bedtime worry. Choose asking or reading aloud.)"
    return "(No story: this page does not create a bedtime-sized worry.)"


def tell_story(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_gender, role="parent", label=params.parent_name))
    room = world.add(Entity(id="room", kind="thing", type="room", label=ROOMS[params.room].label))
    cat = world.add(Entity(id="catalogue", kind="thing", type="catalogue", label=CATALOGUES[params.catalogue].label, tags=CATALOGUES[params.catalogue].tags))
    page = world.add(Entity(id="page", kind="thing", type="page", label=PAGES[params.page].label, tags=PAGES[params.page].tags))
    comfort = world.add(Entity(id="comfort", kind="thing", type="comfort", label=COMFORTS[params.comfort].label, tags=COMFORTS[params.comfort].tags))

    child.memes["bravery"] = BRAVERY_INIT
    child.memes["worry"] = 0.0
    child.memes["sleepy"] = 1.0

    world.say(
        f"At bedtime, {params.child_name} sat in {room.label} with {params.parent_name} and found {CATALOGUES[params.catalogue].phrase}."
    )
    world.say(
        f"The cover said {CATALOGUES[params.catalogue].title}, and when {params.child_name} turned a page, {PAGES[params.page].description} appeared."
    )
    world.para()
    world.say(
        f"{params.child_name} noticed the word death and felt a tiny shiver."
    )
    child.memes["worry"] += 1
    propagate(world, narrate=False)

    response = RESPONSES[params.response]
    world.say(
        f"Bravely, {params.child_name} {response.text}."
    )
    world.para()
    if params.response == "close_book":
        world.say(
            f"But the worry stayed tucked inside {params.child_name}'s chest, so {params.parent_name} opened the book again and used a softer voice."
        )
    else:
        world.say(
            f"{params.parent_name} smiled, and the room felt softer with the {comfort.label} nearby."
        )
    world.say(
        f"{params.parent_name} explained that death in the page meant {PAGES[params.page].gentle_meaning}, not a monster in the room."
    )
    child.memes["worry"] = 0.0
    child.memes["bravery"] += 1
    child.memes["sleepy"] += 1
    world.para()
    world.say(
        f"{params.child_name} hugged the {comfort.label}, listened to the end of the page, and drifted to sleep while the catalogue waited on the bedside table."
    )

    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        catalogue=cat,
        page=page,
        comfort=comfort,
        response=response,
        outcome="calm",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story about a child who finds a catalogue and feels brave enough to ask about the word death.',
        f"Tell a gentle bedtime story where {f['child'].id} sees {f['page'].label} in {f['catalogue'].label} and asks a grown-up what it means.",
        'Write a soft, child-facing story that includes the words catalogue and death and ends with a child feeling safe enough to sleep.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent = f["child"], f["parent"]
    page, cat, comfort = f["page"], f["catalogue"], f["comfort"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, who is trying to get ready for sleep. {parent.id} is there too, helping make the scary moment gentle."),
        ("What did {0} find?".format(child.id),
         f"{child.id} found {cat.label} and then noticed {page.description}. The catalogue made the page feel important, so the word death stood out right away."),
        ("How did {0} show bravery?".format(child.id),
         f"{child.id} showed bravery by staying with the page instead of hiding from it. {child.id} asked for help, and that was the brave choice because it turned a scary word into something calm."),
        ("How did the story end?",
         f"It ended with {child.id} hugging the {comfort.label} and falling asleep. {parent.id}'s explanation made the catalogue feel safe again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["catalogue"].tags) | set(f["page"].tags) | set(f["comfort"].tags) | {"bravery"}
    out = []
    if "catalogue" in tags:
        out.append(("What is a catalogue?", "A catalogue is a list or book of things organized so you can look through them one by one."))
    if "death" in tags:
        out.append(("What does the word death mean?", "Death means the end of life. In a bedtime story, a grown-up may explain it gently so a child does not feel alone."))
    if "bravery" in tags:
        out.append(("What is bravery?", "Bravery means staying with something a little scary and doing the helpful thing anyway."))
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return params.response in RESPONSES and cautious_choice(PAGES[params.page], RESPONSES[params.response])


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for cid in CATALOGUES:
        lines.append(asp.fact("catalogue", cid))
        lines.append(asp.fact("contains_word", cid, CATALOGUES[cid].contains_word))
    for pid in PAGES:
        lines.append(asp.fact("page", pid))
        if PAGES[pid].scary:
            lines.append(asp.fact("scary", pid))
        lines.append(asp.fact("worry_word", pid, PAGES[pid].worry_word))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, RESPONSES[rid].sense))
    lines.append(asp.fact("calm_min", CALM_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R, C, P) :- room(R), catalogue(C), page(P), scary(P), contains_word(C, W), worry_word(P, W).
calm_response(R) :- response(R), sense(R, S), calm_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generate() completed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if rc == 0:
        print("OK: ASP parity matches Python.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a catalogue, death, and bravery.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--catalogue", choices=CATALOGUES)
    ap.add_argument("--page", choices=PAGES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--response", choices=RESPONSES)
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
              if (args.room is None or c[0] == args.room)
              and (args.catalogue is None or c[1] == args.catalogue)
              and (args.page is None or c[2] == args.page)]
    if not combos:
        raise StoryError("(No valid bedtime-story combination matches the given options.)")
    room, catalogue, page = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    if RESPONSES[response].sense < CALM_MIN:
        raise StoryError("(That response is too timid for this story world.)")
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    return StoryParams(
        room=room,
        catalogue=catalogue,
        page=page,
        comfort=comfort,
        response=response,
        child_name=rng.choice(CHILD_NAMES),
        child_gender=rng.choice(["girl", "boy"]),
        parent_name=rng.choice(GROWNUP_NAMES),
        parent_gender=rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS or params.catalogue not in CATALOGUES or params.page not in PAGES:
        raise StoryError("Invalid params for this bedtime story world.")
    if params.comfort not in COMFORTS or params.response not in RESPONSES:
        raise StoryError("Invalid comfort or response selection.")
    if not valid_story(params):
        raise StoryError("This combination does not form a reasonable bedtime story.")
    world = tell_story(params)
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


CURATED = [
    StoryParams(room="nursery", catalogue="moon_catalogue", page="rose_page", comfort="bear", response="ask", child_name="Mina", child_gender="girl", parent_name="Mom", parent_gender="mother"),
    StoryParams(room="reading_nook", catalogue="garden_catalogue", page="night_page", comfort="lamp", response="read_aloud", child_name="Toby", child_gender="boy", parent_name="Dad", parent_gender="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show calm_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
