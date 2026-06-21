#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cellophane_bob_situate_teamwork_quest_fable.py
========================================================================

A small fable-like story world about two animals on a quest. They must carry a
delicate message through a damp, breezy path and situate it on an old marker
before sunset. The world prefers a sensible fix: wrapping the message in
cellophane and carrying it together.

The seed words "cellophane", "bob", and "situate" are worked into the prose as
natural parts of the tale. The feature focus is Teamwork plus Quest, with a
gentle fable ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/cellophane_bob_situate_teamwork_quest_fable.py
    python storyworlds/worlds/gpt-5.4/cellophane_bob_situate_teamwork_quest_fable.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/cellophane_bob_situate_teamwork_quest_fable.py --all --qa
    python storyworlds/worlds/gpt-5.4/cellophane_bob_situate_teamwork_quest_fable.py --json
    python storyworlds/worlds/gpt-5.4/cellophane_bob_situate_teamwork_quest_fable.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "doe", "she"}
        male = {"boy", "stag", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def short_role(self) -> str:
        return self.attrs.get("species", self.type)


@dataclass
class Place:
    id: str
    phrase: str
    start_image: str
    path_text: str
    marker: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    picture: str
    purpose: str
    needs_dry: bool = True
    needs_still: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards_dry: bool = False
    guards_still: bool = False
    wrap_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Pair:
    id: str
    first_name: str
    first_kind: str
    first_species: str
    first_gift: str
    second_name: str
    second_kind: str
    second_species: str
    second_gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    tool: str
    pair: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


PLACES = {
    "brook": Place(
        id="brook",
        phrase="the silver brook path",
        start_image="Mist hung over the little brook like a scarf of breath.",
        path_text="A narrow stepping-stone path crossed the brook, where spray kissed everything and the evening breeze slipped between the reeds.",
        marker="the round moss stone beside the brook",
        tags={"water", "breeze"},
    ),
    "hill": Place(
        id="hill",
        phrase="the windy hill path",
        start_image="The hill wore a pale gold light, but the grass hissed in the wind.",
        path_text="The path climbed past open grass where damp clouds brushed low and every gust wanted to tug small things away.",
        marker="the flat sun-stone on the windy hill",
        tags={"wind", "hill"},
    ),
    "reeds": Place(
        id="reeds",
        phrase="the reed-marsh path",
        start_image="The marsh reeds bowed and whispered as if they knew an old secret.",
        path_text="The plank path ran over shallow water, and cool droplets and soft gusts drifted up together from the reeds.",
        marker="the old heron marker in the reeds",
        tags={"water", "wind", "marsh"},
    ),
}

ITEMS = {
    "map": QuestItem(
        id="map",
        label="map",
        phrase="a paper map painted with a moon-shaped trail",
        picture="a silver line curving toward the marker stone",
        purpose="so they could find the hidden berry gate before dusk",
        tags={"map", "paper"},
    ),
    "charter": QuestItem(
        id="charter",
        label="charter",
        phrase="a petal-thin charter with a red wax leaf at the corner",
        picture="a tiny picture of the stone where it belonged",
        purpose="so the garden birds would know the berry patch was open again",
        tags={"paper", "charter"},
    ),
    "song": QuestItem(
        id="song",
        label="song sheet",
        phrase="a song sheet written in soft blue ink",
        picture="small notes circling a star",
        purpose="so the dusk choir could sing at the marker before night fell",
        tags={"paper", "song"},
    ),
}

TOOLS = {
    "cellophane": Tool(
        id="cellophane",
        label="cellophane",
        phrase="a clear strip of cellophane",
        guards_dry=True,
        guards_still=True,
        wrap_text="They folded the message small and wrapped it in cellophane until it shone like a little window and held its shape.",
        qa_text="wrapped the message in cellophane so spray could not soak it and the wind could not flap it loose",
        tags={"cellophane", "wrap"},
    ),
    "leaf_pocket": Tool(
        id="leaf_pocket",
        label="leaf pocket",
        phrase="a curled dock leaf pocket",
        guards_dry=True,
        guards_still=False,
        wrap_text="They tucked the message into a curled leaf pocket.",
        qa_text="tucked the message into a curled leaf pocket",
        tags={"leaf", "wrap"},
    ),
    "reed_ring": Tool(
        id="reed_ring",
        label="reed ring",
        phrase="a tiny reed ring",
        guards_dry=False,
        guards_still=True,
        wrap_text="They slipped the message through a tiny reed ring to keep it snug.",
        qa_text="slipped the message through a reed ring to keep it from flapping",
        tags={"reed", "wrap"},
    ),
}

PAIRS = {
    "mouse_turtle": Pair(
        id="mouse_turtle",
        first_name="Miri",
        first_kind="girl",
        first_species="mouse",
        first_gift="quick paws",
        second_name="Tomo",
        second_kind="boy",
        second_species="turtle",
        second_gift="steady steps",
        tags={"teamwork"},
    ),
    "wren_mole": Pair(
        id="wren_mole",
        first_name="Pip",
        first_kind="boy",
        first_species="wren",
        first_gift="sharp eyes",
        second_name="Della",
        second_kind="girl",
        second_species="mole",
        second_gift="careful paws",
        tags={"teamwork"},
    ),
    "squirrel_hedgehog": Pair(
        id="squirrel_hedgehog",
        first_name="Nia",
        first_kind="girl",
        first_species="squirrel",
        first_gift="fast climbing",
        second_name="Bram",
        second_kind="boy",
        second_species="hedgehog",
        second_gift="patient balance",
        tags={"teamwork"},
    ),
}

MENTORS = [
    ("Owl", "owl"),
    ("Badger", "badger"),
    ("Heron", "heron"),
]

KNOWLEDGE = {
    "cellophane": [
        (
            "What is cellophane?",
            "Cellophane is a thin, clear wrapping. You can see through it, and it helps keep small things clean and dry.",
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map shows where things are and how to get somewhere. It helps travelers know which way to go.",
        )
    ],
    "paper": [
        (
            "Why can paper be harmed by water and wind?",
            "Paper can soak up water and turn soft. Wind can also flap or tear it if it is light and loose.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more friends help each other do one job. Each one brings a strength, and together they do better than alone.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a purpose. Someone sets out to do an important job and keeps going until it is done.",
        )
    ],
    "marker": [
        (
            "What does it mean to situate something?",
            "To situate something means to place it in the right spot. You put it where it belongs.",
        )
    ],
    "wind": [
        (
            "Why do light things move in the wind?",
            "Wind pushes on light things more easily than heavy things. That is why a leaf or paper can flutter away.",
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "teamwork", "cellophane", "paper", "map", "marker", "wind"]


def valid_tool_for_item(tool: Tool, item: QuestItem) -> bool:
    need_dry = item.needs_dry
    need_still = item.needs_still
    dry_ok = (not need_dry) or tool.guards_dry
    still_ok = (not need_still) or tool.guards_still
    return dry_ok and still_ok


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for item_id, item in ITEMS.items():
            for tool_id, tool in TOOLS.items():
                if valid_tool_for_item(tool, item):
                    combos.append((place_id, item_id, tool_id))
    return sorted(combos)


def explain_tool_rejection(tool: Tool, item: QuestItem) -> str:
    missing: list[str] = []
    if item.needs_dry and not tool.guards_dry:
        missing.append("keep it dry")
    if item.needs_still and not tool.guards_still:
        missing.append("keep it from flapping in the wind")
    need = " and ".join(missing)
    return (
        f"(No story: {tool.phrase} cannot {need}. This quest item is too delicate for that tool; try --tool cellophane.)"
    )


def outcome_of(params: StoryParams) -> str:
    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    return "delivered" if valid_tool_for_item(tool, item) else "spoiled"


def introduce_quest(world: World, a: Entity, b: Entity, mentor: Entity, place: Place, item: QuestItem) -> None:
    world.say(
        f"{place.start_image} In a small hollow nearby lived {a.id} the {a.attrs['species']} and {b.id} the {b.attrs['species']}, who liked to finish good work side by side."
    )
    world.say(
        f"That evening, {mentor.id} the {mentor.attrs['species']} called them close and showed them {item.phrase}. On it was {item.picture}."
    )
    world.say(
        f'"Take this to {place.marker}," said {mentor.id}. "You must situate it there before sunset, {item.purpose}."'
    )
    a.memes["purpose"] += 1
    b.memes["purpose"] += 1


def prepare(world: World, a: Entity, b: Entity, item_ent: Entity, tool: Tool) -> None:
    world.say(
        f"{a.id} wanted to hurry at once, but {b.id} looked at the thin paper and the damp air."
    )
    world.say(
        f'"A quest is not helped by rushing," {b.id} said. "Let us carry it wisely."'
    )
    item_ent.meters["wrapped"] += 1
    if tool.guards_dry:
        item_ent.meters["dry_guard"] += 1
    if tool.guards_still:
        item_ent.meters["still_guard"] += 1
    world.say(tool.wrap_text)
    world.say(
        f"{a.id} held the parcel high, and {b.id} tied a grass thread around it so they could carry it together."
    )
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1


def travel(world: World, a: Entity, b: Entity, place: Place, item_ent: Entity) -> None:
    world.para()
    world.say(place.path_text)
    world.say(
        f"{a.id} used {a.attrs['gift']} to watch the way ahead, while {b.id} used {b.attrs['gift']} to keep the parcel level between them."
    )
    item_ent.meters["risk"] += 1
    world.say(
        "At the worst bump, the tiny bundle gave a nervous bob, and both friends stopped at once instead of pretending nothing had happened."
    )
    if item_ent.meters["dry_guard"] >= THRESHOLD and item_ent.meters["still_guard"] >= THRESHOLD:
        item_ent.meters["safe"] += 1
        world.say(
            f'"Slower," said {b.id}. "One careful step is faster than starting over." So {a.id} shortened the stride, and the wrapped message stayed dry and neat.'
        )
    else:
        if item_ent.meters["dry_guard"] < THRESHOLD:
            item_ent.meters["wet"] += 1
        if item_ent.meters["still_guard"] < THRESHOLD:
            item_ent.meters["crumpled"] += 1
        world.say(
            "The little message shook and softened. By the time they reached the marker, its edges were spoiled."
        )


def finish_quest(world: World, a: Entity, b: Entity, item_ent: Entity, place: Place, item: QuestItem) -> None:
    world.para()
    if item_ent.meters["wet"] >= THRESHOLD or item_ent.meters["crumpled"] >= THRESHOLD:
        a.memes["sadness"] += 1
        b.memes["sadness"] += 1
        world.say(
            f"They reached {place.marker}, but the message was too spoiled to read well."
        )
        world.say(
            f"{a.id} drooped. {b.id} touched the damp paper and said, \"Next time we will prepare before we boast.\""
        )
        world.say(
            f"Even so, they carried the broken message back together, because a true friend stays for the hard walk as well as the bright one."
        )
        world.facts["outcome"] = "spoiled"
        return
    item_ent.meters["placed"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At last they came to {place.marker}. Together they set the little packet down, opened the clear wrap, and situate the {item.label} exactly where the picture said it belonged."
    )
    world.say(
        f"The evening light touched the marker, and the task was done. {a.id} laughed first, but {b.id} smiled widest."
    )
    world.say(
        f"From that day on, when the meadow folk spoke of brave errands, they also spoke of the two friends who shared one quest and carried it with four careful paws."
    )
    world.facts["outcome"] = "delivered"


def tell(place: Place, item: QuestItem, tool: Tool, pair: Pair, mentor_choice: tuple[str, str]) -> World:
    world = World()
    a = world.add(
        Entity(
            id=pair.first_name,
            kind="character",
            type=pair.first_kind,
            attrs={"species": pair.first_species, "gift": pair.first_gift},
            tags={"friend"},
        )
    )
    b = world.add(
        Entity(
            id=pair.second_name,
            kind="character",
            type=pair.second_kind,
            attrs={"species": pair.second_species, "gift": pair.second_gift},
            tags={"friend"},
        )
    )
    mentor = world.add(
        Entity(
            id=mentor_choice[0],
            kind="character",
            type="thing",
            attrs={"species": mentor_choice[1]},
            tags={"mentor"},
        )
    )
    item_ent = world.add(
        Entity(
            id="item",
            kind="thing",
            type="message",
            label=item.label,
            tags=set(item.tags),
        )
    )

    introduce_quest(world, a, b, mentor, place, item)
    prepare(world, a, b, item_ent, tool)
    travel(world, a, b, place, item_ent)
    finish_quest(world, a, b, item_ent, place, item)

    world.facts.update(
        place=place,
        item_cfg=item,
        tool=tool,
        pair=pair,
        mentor=mentor,
        first=a,
        second=b,
        item=item_ent,
        teamwork_used=a.memes["teamwork"] >= THRESHOLD and b.memes["teamwork"] >= THRESHOLD,
        delivered=item_ent.meters["placed"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pair = f["pair"]
    item = f["item_cfg"]
    place = f["place"]
    return [
        f'Write a short fable for a 3-to-5-year-old about teamwork and a quest, and include the words "cellophane", "bob", and "situate".',
        f"Tell a gentle animal story where {pair.first_name} the {pair.first_species} and {pair.second_name} the {pair.second_species} must carry {item.phrase} along {place.phrase} and place it carefully before sunset.",
        f'Write a child-facing fable in which two friends solve a problem by preparing wisely instead of hurrying, and end with a clear lesson about teamwork.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    pair = f["pair"]
    item = f["item_cfg"]
    tool = f["tool"]
    place = f["place"]
    a = f["first"]
    b = f["second"]
    mentor = f["mentor"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair.first_name} the {pair.first_species} and {pair.second_name} the {pair.second_species}. {mentor.id} the {mentor.attrs['species']} sends them on an important errand.",
        ),
        (
            "What was their quest?",
            f"They had to carry {item.phrase} to {place.marker} before sunset. They needed to situate it in the right place so the task could be finished properly.",
        ),
        (
            f"Why did {b.id} tell {a.id} not to rush?",
            f"{b.id} saw that the message was thin and easy to spoil. The path was damp and breezy, so hurrying could ruin it before they reached the marker.",
        ),
        (
            "How did they protect the message?",
            f"They {tool.qa_text}. That mattered because the path could splash the paper and toss it in the wind.",
        ),
        (
            "What happened when the bundle gave a little bob?",
            f"Both friends stopped at once and became more careful. Instead of pushing ahead, they changed how they walked, and that helped the quest succeed.",
        ),
    ]
    if f["delivered"]:
        qa.append(
            (
                "How did teamwork help them finish the quest?",
                f"{a.id} watched the way ahead with {a.attrs['gift']}, and {b.id} kept the parcel level with {b.attrs['gift']}. Each friend did a different part of the job, so the message stayed safe all the way to the marker.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They reached {place.marker} and placed the {item.label} exactly where it belonged. The ending shows that careful teamwork can carry a delicate job all the way home.",
            )
        )
    else:
        qa.append(
            (
                "Why did the quest fail?",
                f"The message was not protected well enough for the damp wind along the path. By the time they arrived, it was too spoiled to use.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"quest", "teamwork", "cellophane", "paper", "marker"}
    if f["item_cfg"].id == "map":
        tags.add("map")
    if "wind" in f["place"].tags or "breeze" in f["place"].tags:
        tags.add("wind")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="brook", item="map", tool="cellophane", pair="mouse_turtle"),
    StoryParams(place="hill", item="charter", tool="cellophane", pair="wren_mole"),
    StoryParams(place="reeds", item="song", tool="cellophane", pair="squirrel_hedgehog"),
]


ASP_RULES = r"""
needs(T, dry)   :- item(T), needs_dry(T).
needs(T, still) :- item(T), needs_still(T).

covers(K, dry)   :- tool(K), guards_dry(K).
covers(K, still) :- tool(K), guards_still(K).

valid(P, T, K) :- place(P), item(T), tool(K),
                  not missing_need(T, K).

missing_need(T, K) :- needs(T, dry), not covers(K, dry).
missing_need(T, K) :- needs(T, still), not covers(K, still).

outcome(delivered) :- chosen_item(T), chosen_tool(K), not missing_need(T, K).
outcome(spoiled)   :- chosen_item(T), chosen_tool(K), missing_need(T, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.needs_dry:
            lines.append(asp.fact("needs_dry", item_id))
        if item.needs_still:
            lines.append(asp.fact("needs_still", item_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.guards_dry:
            lines.append(asp.fact("guards_dry", tool_id))
        if tool.guards_still:
            lines.append(asp.fact("guards_still", tool_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    for item_id in ITEMS:
        for tool_id in TOOLS:
            params = StoryParams(place="brook", item=item_id, tool=tool_id, pair="mouse_turtle")
            py_outcome = outcome_of(params)
            asp_out = asp_outcome(params)
            if py_outcome != asp_out:
                rc = 1
                print(
                    f"MISMATCH outcome for item={item_id} tool={tool_id}: python={py_outcome} asp={asp_out}"
                )

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a fable quest where two animal friends protect a delicate message and carry it together."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.tool:
        item = ITEMS[args.item]
        tool = TOOLS[args.tool]
        if not valid_tool_for_item(tool, item):
            raise StoryError(explain_tool_rejection(tool, item))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, tool_id = rng.choice(sorted(combos))
    pair_id = args.pair or rng.choice(sorted(PAIRS))
    return StoryParams(place=place_id, item=item_id, tool=tool_id, pair=pair_id)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.pair not in PAIRS:
        raise StoryError(f"(Unknown pair: {params.pair})")

    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    if not valid_tool_for_item(tool, item):
        raise StoryError(explain_tool_rejection(tool, item))

    mentor_choice = MENTORS[(hash((params.place, params.item, params.pair)) % len(MENTORS))]
    world = tell(PLACES[params.place], item, tool, PAIRS[params.pair], mentor_choice)
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
        print(f"{len(combos)} compatible (place, item, tool) combos:\n")
        for place_id, item_id, tool_id in combos:
            print(f"  {place_id:8} {item_id:8} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.pair}: {p.item} via {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
