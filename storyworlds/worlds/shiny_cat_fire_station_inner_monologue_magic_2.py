#!/usr/bin/env python3
"""A mystery-leaning fire-station storyworld about a shiny cat, magic clues, and a missing brass star.

Internal source tale:
Mira spends a rainy evening at a small fire station while Captain Ro prepares for
the next day's school visit. The brass alarm star that hangs beside the old bell
goes missing, and a shiny cat appears as if it has stepped out of the bell's own
reflection. Mira first wonders whether the cat caused the trouble, but the cat's
magic turns into clues: glowing pawprints, lantern-bright whiskers, and purring
echoes that point toward the truth. By following the right clue into the right
corner of the station and using the proper recovery tool, Mira finds the star,
realizes the cat was guarding it rather than stealing it, and restores calm to
the fire station before dawn.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class StationRoom:
    id: str
    name: str
    opening: str
    hush: str
    ending_image: str


@dataclass(frozen=True)
class MagicClue:
    id: str
    place: str
    sign: str
    thought: str
    reading: str


@dataclass(frozen=True)
class HidingSpot:
    id: str
    place: str
    obstacle: str
    cause: str
    evidence: str
    discovery: str
    truth: str


@dataclass(frozen=True)
class RecoveryTool:
    id: str
    solves: str
    label: str
    action: str
    proof: str


@dataclass(frozen=True)
class EndingStyle:
    id: str
    closing: str
    image: str


@dataclass(frozen=True)
class StoryParams:
    room: str
    clue: str
    hiding: str
    tool: str
    ending: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    owner: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class FireStationWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | float] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


ROOMS: dict[str, StationRoom] = {
    "gear_room": StationRoom(
        id="gear_room",
        name="the gear room",
        opening=(
            "Rain tapped the high windows of the fire station while Mira waited beside the boot racks and watched Captain Ro polish the old alarm bell."
        ),
        hush="The coats hung so still that even their silver stripes seemed to be listening.",
        ending_image="the boot room shining softly, with every helmet back in place",
    ),
    "hose_tower": StationRoom(
        id="hose_tower",
        name="the hose tower",
        opening=(
            "The fire station smelled like rain and clean rope as Mira followed Captain Ro past the tall drying hoses and the old alarm bell."
        ),
        hush="Above her, the hanging hoses swayed like quiet red curtains waiting for a secret to fall out.",
        ending_image="the hose tower standing calm again, with the red loops resting in neat rows",
    ),
    "map_alcove": StationRoom(
        id="map_alcove",
        name="the map alcove",
        opening=(
            "Inside the fire station map alcove, Mira listened to the tick of the old alarm bell while Captain Ro straightened tomorrow's school-safety maps."
        ),
        hush="The glass map case held the room's lamplight so tightly that every reflection looked like half a clue.",
        ending_image="the map alcove glowing warm, with the glass case no longer keeping secrets",
    ),
}

CLUES: dict[str, MagicClue] = {
    "gold_paws": MagicClue(
        id="gold_paws",
        place="gear_room",
        sign="The shiny cat padded across the bench, and each pawprint briefly turned gold on the dusty shelf before fading away.",
        thought='"Those prints are too neat to be an accident," Mira thought. "Magic is showing me where to look, not where to blame."',
        reading="The glowing prints climbed toward the top helmet shelf instead of running for the door.",
    ),
    "helmet_glint": MagicClue(
        id="helmet_glint",
        place="gear_room",
        sign="The cat flicked its tail once, and a thin beam of light skipped from visor to visor until one dark corner flashed back.",
        thought='"If the shiny cat wanted to hide, it would choose shadow," Mira thought. "Instead it keeps lighting the same spot for me."',
        reading="That single hard flash told Mira that something brass was waiting above the helmets.",
    ),
    "echo_purr": MagicClue(
        id="echo_purr",
        place="hose_tower",
        sign="The cat purred at the foot of the hose tower, and the sound came back from one hanging loop brighter than a bell tap.",
        thought='"The purr is acting like a question and the hose is answering it," Mira thought. "That means the answer is up there."',
        reading="Only one hose answered the cat, so Mira knew the missing thing had been caught inside that loop.",
    ),
    "spark_tail": MagicClue(
        id="spark_tail",
        place="hose_tower",
        sign="The shiny cat leaped onto the rail, and its tail-tip sparked against the damp air until one hose loop gave a tiny golden wink.",
        thought='"That wink came from metal, not water," Mira thought. "The cat is tracing the real path for me."',
        reading="The golden wink came from the loop the cat kept watching, not from anywhere on the floor.",
    ),
    "whisker_compass": MagicClue(
        id="whisker_compass",
        place="map_alcove",
        sign="The cat stood on the map table, and its whiskers shone like compass needles toward the narrow cabinet gap.",
        thought='"A map tells you where to go," Mira thought. "This magic cat is turning itself into a map."',
        reading="The bright whiskers pointed straight to the gap behind the map cabinet and nowhere else.",
    ),
    "glass_moon": MagicClue(
        id="glass_moon",
        place="map_alcove",
        sign="Moony light slid off the cat's back and across the glass case until a tiny line of gold answered from behind the cabinet.",
        thought='"That little line answered the light," Mira thought. "So something shiny must be stuck where I cannot reach by hand."',
        reading="The reflected beam turned the hidden brass edge into a visible clue for just one second.",
    ),
}

HIDINGS: dict[str, HidingSpot] = {
    "helmet_ledge": HidingSpot(
        id="helmet_ledge",
        place="gear_room",
        obstacle="high_ledge",
        cause="During the evening drill, the station door banged and shook the brass alarm star off its bell hook onto the high helmet ledge.",
        evidence="a fresh brass scratch above the helmets and one stripe of dust brushed smooth by a careful paw",
        discovery="The brass alarm star was lying behind the top helmet, bright as a trapped drop of sunrise.",
        truth="The cat had not stolen the star at all. It had climbed up to guard the ledge and keep the charm from falling behind the lockers for the whole night.",
    ),
    "hose_loop": HidingSpot(
        id="hose_loop",
        place="hose_tower",
        obstacle="deep_loop",
        cause="When the hoses were rolled after practice, one bouncing hook knocked the brass alarm star into a hanging loop high in the tower.",
        evidence="one red loop swinging after the rest had gone still and a tiny ring of brass against dark canvas",
        discovery="The brass alarm star was tucked inside the hanging hose loop, glinting whenever the cat's magic touched it.",
        truth="The shiny cat had been pacing below the hose all evening because the star would have dropped deeper into the fold if anyone had yanked the line too fast.",
    ),
    "cabinet_gap": HidingSpot(
        id="cabinet_gap",
        place="map_alcove",
        obstacle="narrow_gap",
        cause="A draft from the side door had slid the brass alarm star off the map table and down behind the cabinet, where fingers could not quite reach.",
        evidence="a hair-thin line of gold in the gap and a little crescent of dust cleared by a paw that kept tapping the same place",
        discovery="The brass alarm star was standing on edge behind the cabinet, hidden except for one bright rim.",
        truth="The cat had been guarding the cabinet gap because one more bump would have dropped the star all the way into the wall space.",
    ),
}

TOOLS: dict[str, RecoveryTool] = {
    "stool": RecoveryTool(
        id="stool",
        solves="high_ledge",
        label="a folding stool",
        action="Captain Ro opened a folding stool while Mira climbed just high enough to reach behind the helmet row and lift the star free.",
        proof="The stool let Mira recover the charm without knocking the helmets down or losing sight of the clue.",
    ),
    "hook_pole": RecoveryTool(
        id="hook_pole",
        solves="deep_loop",
        label="a short hook pole",
        action="Mira steadied the hose with both hands while Captain Ro eased a short hook pole through the loop and drew the star down by its ribbon.",
        proof="The hook pole kept the hose from whipping and let the charm slide out without falling deeper into the canvas fold.",
    ),
    "magnet_ribbon": RecoveryTool(
        id="magnet_ribbon",
        solves="narrow_gap",
        label="a ribbon-tied magnet",
        action="Captain Ro tied a small magnet to a ribbon, and Mira lowered it into the gap until the brass star kissed it and rose into view.",
        proof="The ribbon magnet reached the narrow space that a hand could not safely enter, so the hidden edge became a full rescue instead of another guess.",
    ),
}

ENDINGS: dict[str, EndingStyle] = {
    "bell_ring": EndingStyle(
        id="bell_ring",
        closing="When Mira hooked the brass star back beside the old bell, the bell gave one clear note all by itself.",
        image="The shiny cat blinked at the sound as if it had been waiting for that one honest ring.",
    ),
    "helmet_nap": EndingStyle(
        id="helmet_nap",
        closing="When the brass star was back in its place, the cat curled into an empty spare helmet as if the whole mystery had only been a long errand.",
        image="Its silver fur dimmed to a soft glow, and the helmet looked more like a nest than station gear.",
    ),
    "dawn_window": EndingStyle(
        id="dawn_window",
        closing="Mira hung the brass star beside the bell just as the first pale strip of dawn touched the fire station window.",
        image="The shiny cat sat in the light and looked ordinary at last, which made the solved mystery feel even more magical.",
    ),
}


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.room not in ROOMS:
        return False, f"unknown room: {params.room}"
    if params.clue not in CLUES:
        return False, f"unknown clue: {params.clue}"
    if params.hiding not in HIDINGS:
        return False, f"unknown hiding: {params.hiding}"
    if params.tool not in TOOLS:
        return False, f"unknown tool: {params.tool}"
    if params.ending not in ENDINGS:
        return False, f"unknown ending: {params.ending}"
    clue = CLUES[params.clue]
    hiding = HIDINGS[params.hiding]
    tool = TOOLS[params.tool]
    if clue.place != params.room:
        return False, "the magical clue must happen in the same fire-station room the story is set to search"
    if hiding.place != params.room:
        return False, "the missing brass star must be hidden in the chosen fire-station room"
    if tool.solves != hiding.obstacle:
        return False, "the recovery tool does not fit the way the brass star is trapped"
    return True, ""


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for room in ROOMS:
        for clue_key, clue in CLUES.items():
            if clue.place != room:
                continue
            for hiding_key, hiding in HIDINGS.items():
                if hiding.place != room:
                    continue
                for tool_key, tool in TOOLS.items():
                    if tool.solves != hiding.obstacle:
                        continue
                    for ending in ENDINGS:
                        combos.append(
                            StoryParams(
                                room=room,
                                clue=clue_key,
                                hiding=hiding_key,
                                tool=tool_key,
                                ending=ending,
                            )
                        )
    return combos


def make_world(params: StoryParams) -> FireStationWorld:
    room = ROOMS[params.room]
    world = FireStationWorld(params=params)
    world.add(
        Entity(
            id="mira",
            kind="character",
            type="girl",
            label="Mira",
            role="child",
            meters=defaultdict(float, {"confidence": 0.3, "steps": 0.0}),
            memes=defaultdict(float, {"curiosity": 1.8, "worry": 0.9, "trust": 0.4}),
        )
    )
    world.add(
        Entity(
            id="captain",
            kind="character",
            type="woman",
            label="Captain Ro",
            role="captain",
            meters=defaultdict(float, {"readiness": 0.6}),
            memes=defaultdict(float, {"calm": 1.5}),
        )
    )
    world.add(
        Entity(
            id="cat",
            kind="animal",
            type="cat",
            label="the shiny cat",
            role="cat",
            meters=defaultdict(float, {"glow": 1.0, "guide": 0.0}),
            memes=defaultdict(float, {"magic": 2.0, "guarding": 1.5}),
            attrs={"location": room.name},
        )
    )
    world.add(
        Entity(
            id="star",
            kind="physical",
            type="charm",
            label="the brass alarm star",
            role="star",
            owner="captain",
            meters=defaultdict(float, {"present": 0.0, "hidden": 1.0, "found": 0.0}),
            memes=defaultdict(float, {"importance": 1.5}),
            attrs={"location": "missing"},
        )
    )
    world.add(
        Entity(
            id="station",
            kind="place",
            type="fire_station",
            label="the fire station",
            role="station",
            meters=defaultdict(float, {"calm": 0.3, "tour_ready": 0.0}),
            memes=defaultdict(float, {"mystery": 1.7, "relief": 0.0}),
        )
    )
    world.add(
        Entity(
            id="room",
            kind="place",
            type="room",
            label=room.name,
            role="room",
            meters=defaultdict(float, {"quiet": 1.0}),
            memes=defaultdict(float, {"shadow": 0.8}),
            attrs={"id": room.id},
        )
    )
    world.facts["room_name"] = room.name
    world.facts["missing_object"] = "the brass alarm star"
    world.facts["inner_monologue"] = False
    world.facts["cat_cleared"] = False
    world.facts["station_restored"] = False
    world.facts["magic_used"] = False
    world.facts["clue_text"] = ""
    world.facts["tool_label"] = TOOLS[params.tool].label
    return world


def opening_scene(world: FireStationWorld) -> None:
    room = ROOMS[world.params.room]
    world.record(
        "opening",
        f"{room.opening} On a hook beside it should have hung the brass alarm star that Captain Ro always showed visiting children, but tonight the hook was empty.",
        "captain",
        "star",
    )
    world.record(
        "arrival",
        f"A shiny cat sat near the bell and looked polished enough to have been brushed by moonlight itself. {room.hush}",
        "cat",
        "room",
    )
    world.get("mira").memes["worry"] += 0.2
    world.get("station").memes["mystery"] += 0.3


def notice_loss(world: FireStationWorld) -> None:
    world.para()
    world.record(
        "loss",
        "Captain Ro said the fire station needed the little brass star back before morning, because it was the first thing children touched during the safety tour. Mira felt the room become a puzzle all at once.",
        "captain",
        "station",
    )
    world.record(
        "thought_begin",
        '"If that shiny cat caused this, why is it still here watching me?" Mira thought. "And if it did not, then maybe it knows more than I do."',
        "mira",
        "cat",
    )
    world.facts["inner_monologue"] = True
    world.get("mira").memes["worry"] += 0.4
    world.get("mira").memes["curiosity"] += 0.3


def follow_magic(world: FireStationWorld) -> None:
    clue = CLUES[world.params.clue]
    world.para()
    world.record(
        "magic_clue",
        f"The shiny cat trotted toward {world.facts['room_name']}, then stopped and let its magic do the speaking. {clue.sign}",
        "cat",
        "room",
    )
    world.record(
        "thought_turn",
        clue.thought,
        "mira",
        "cat",
    )
    world.record(
        "reading",
        clue.reading,
        "mira",
        "star",
    )
    world.facts["magic_used"] = True
    world.facts["clue_text"] = clue.sign
    world.get("cat").meters["guide"] += 1.0
    world.get("mira").memes["trust"] += 0.9
    world.get("mira").meters["confidence"] += 0.4


def recover_star(world: FireStationWorld) -> None:
    hiding = HIDINGS[world.params.hiding]
    tool = TOOLS[world.params.tool]
    star = world.get("star")
    station = world.get("station")
    world.para()
    world.record(
        "cause",
        hiding.cause,
        "station",
        "star",
    )
    world.record(
        "evidence",
        f"Mira crouched and found {hiding.evidence}. That was enough to turn the mystery from a guess into a direction.",
        "mira",
        "star",
    )
    world.record(
        "recovery",
        f"{tool.action} {hiding.discovery}",
        "captain",
        "star",
    )
    world.record(
        "proof",
        tool.proof,
        "captain",
        "mira",
    )
    star.meters["hidden"] = 0.0
    star.meters["found"] = 1.0
    star.meters["present"] = 1.0
    star.attrs["location"] = "bell hook"
    station.meters["tour_ready"] = 1.0
    station.meters["calm"] = 1.0
    world.get("mira").memes["worry"] = max(0.0, world.get("mira").memes["worry"] - 0.8)
    world.get("mira").memes["trust"] += 0.5
    world.get("mira").meters["confidence"] += 0.5
    world.get("station").memes["relief"] += 1.2
    world.get("station").memes["mystery"] = max(0.0, world.get("station").memes["mystery"] - 1.0)


def resolve_story(world: FireStationWorld) -> None:
    hiding = HIDINGS[world.params.hiding]
    ending = ENDINGS[world.params.ending]
    cat = world.get("cat")
    world.para()
    world.record(
        "truth",
        hiding.truth,
        "mira",
        "cat",
    )
    world.record(
        "restore",
        f'Mira let out a breath she had been holding too long. "So you were guarding it," she whispered, and the shiny cat answered with one pleased blink.',
        "mira",
        "cat",
    )
    world.record(
        "ending",
        f"{ending.closing} {ending.image} The fire station no longer felt watchful. It felt ready.",
        "station",
        "star",
    )
    world.facts["cat_cleared"] = True
    world.facts["station_restored"] = True
    cat.meters["glow"] = 0.4
    cat.memes["guarding"] += 0.4
    world.get("station").memes["relief"] += 0.8


def prompts_for(world: FireStationWorld) -> list[str]:
    room = ROOMS[world.params.room]
    return [
        "Write a child-facing mystery set inside a fire station.",
        f"Include a shiny cat whose magic leaves clues in {room.name}.",
        "Use inner monologue to show the child detective changing from suspicion to trust.",
    ]


def story_qa_for(world: FireStationWorld) -> list[QAItem]:
    room = ROOMS[world.params.room]
    hiding = HIDINGS[world.params.hiding]
    tool = TOOLS[world.params.tool]
    clue = CLUES[world.params.clue]
    return [
        QAItem(
            question="Why did Mira decide to follow the shiny cat?",
            answer=(
                "Mira followed the shiny cat because it stayed near the mystery instead of running away from it. "
                f"When its magic created a clue in {room.name}, she understood that the cat was guiding her toward the missing star rather than hiding it."
            ),
        ),
        QAItem(
            question="What clue showed Mira where to search?",
            answer=(
                f"The key clue was this: {clue.sign} "
                f"That magic sign narrowed the search to {room.name}, so Mira could look for real evidence instead of making a wild guess."
            ),
        ),
        QAItem(
            question="How did Mira and Captain Ro get the brass alarm star back?",
            answer=(
                f"They used {tool.label} to reach the place where the star was trapped. "
                f"{tool.proof}"
            ),
        ),
        QAItem(
            question="Why was the cat not the thief after all?",
            answer=(
                "The cat was not the thief because the star had been knocked away by station movement, not by paws or mischief. "
                f"{hiding.truth}"
            ),
        ),
    ]


def world_qa_for(world: FireStationWorld) -> list[QAItem]:
    room = ROOMS[world.params.room]
    hiding = HIDINGS[world.params.hiding]
    ending = ENDINGS[world.params.ending]
    return [
        QAItem(
            question="What object mattered most in this fire-station mystery?",
            answer=(
                "The missing object was the brass alarm star that hung beside the old bell. "
                "It mattered because Captain Ro used it during the station's morning safety tour for children."
            ),
        ),
        QAItem(
            question="Where had the missing star really gone?",
            answer=(
                f"The star had ended up in {room.name}. "
                f"{hiding.cause}"
            ),
        ),
        QAItem(
            question="How do we know the mystery is truly over at the end?",
            answer=(
                f"We know the mystery is over because the star is restored and the station is ready again. {ending.closing}"
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    opening_scene(world)
    notice_loss(world)
    follow_magic(world)
    recover_star(world)
    resolve_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


ASP_RULES = r"""
valid(R, C, H, T, E) :-
    room(R), clue(C), hiding(H), tool(T), ending(E),
    clue_place(C, P), hiding_place(H, P), room_place(R, P),
    hiding_obstacle(H, O), tool_solves(T, O).

ok :- chosen(R, C, H, T, E), valid(R, C, H, T, E).

#show valid/5.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for room in ROOMS:
        rows.append(fact("room", room))
        rows.append(fact("room_place", room, room))
    for clue_key, clue in CLUES.items():
        rows.append(fact("clue", clue_key))
        rows.append(fact("clue_place", clue_key, clue.place))
    for hiding_key, hiding in HIDINGS.items():
        rows.append(fact("hiding", hiding_key))
        rows.append(fact("hiding_place", hiding_key, hiding.place))
        rows.append(fact("hiding_obstacle", hiding_key, hiding.obstacle))
    for tool_key, tool in TOOLS.items():
        rows.append(fact("tool", tool_key))
        rows.append(fact("tool_solves", tool_key, tool.solves))
    for ending in ENDINGS:
        rows.append(fact("ending", ending))
    if params is not None:
        rows.append(fact("chosen", params.room, params.clue, params.hiding, params.tool, params.ending))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str, str]]:
    from asp import atoms, one_model

    combos: set[tuple[str, str, str, str, str]] = set()
    for combo in atoms(one_model(asp_program()), "valid"):
        combos.add(tuple(str(part) for part in combo))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    python_combos = {
        (p.room, p.clue, p.hiding, p.tool, p.ending)
        for p in all_params()
    }
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(
            f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}"
        )
    for params in all_params():
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")
        sample = generate(params)
        story = sample.story
        world = sample.world
        if "shiny cat" not in story.lower():
            raise StoryError(f"required seed words missing from story for params={params}")
        if "fire station" not in story.lower():
            raise StoryError(f"required setting missing from story for params={params}")
        if "magic" not in story.lower():
            raise StoryError(f"magic feature missing from story for params={params}")
        if "thought" not in story.lower():
            raise StoryError(f"inner monologue missing from story for params={params}")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"QA too thin for params={params}")
        if not world.facts.get("cat_cleared"):
            raise StoryError(f"cat was not cleared by the end for params={params}")
        if not world.facts.get("station_restored"):
            raise StoryError(f"station was not restored for params={params}")
        if world.get("star").meters["found"] < 1.0:
            raise StoryError(f"star was not recovered for params={params}")
        if world.get("station").meters["tour_ready"] < 1.0:
            raise StoryError(f"fire station was not ready by the end for params={params}")
        if "  " in story or "{}" in story or "Trace:" in story:
            raise StoryError(f"story leaked scaffolding for params={params}")
    return (
        f"OK: Python and ASP agree on {len(python_combos)} valid shiny-cat fire-station mysteries, "
        "and every generated story restores the brass alarm star through grounded magical clues."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--room", choices=sorted(ROOMS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--hiding", choices=sorted(HIDINGS))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--ending", choices=sorted(ENDINGS))
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    explicit = any(
        getattr(args, key) is not None
        for key in ("room", "clue", "hiding", "tool", "ending")
    )
    if explicit:
        params = StoryParams(
            room=args.room or rng.choice(list(ROOMS)),
            clue=args.clue or rng.choice(list(CLUES)),
            hiding=args.hiding or rng.choice(list(HIDINGS)),
            tool=args.tool or rng.choice(list(TOOLS)),
            ending=args.ending or rng.choice(list(ENDINGS)),
            seed=args.seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params
    choice = rng.choice(all_params())
    return StoryParams(
        room=choice.room,
        clue=choice.clue,
        hiding=choice.hiding,
        tool=choice.tool,
        ending=choice.ending,
        seed=args.seed,
    )


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    explicit = any(
        getattr(args, key) is not None
        for key in ("room", "clue", "hiding", "tool", "ending")
    )
    if explicit:
        rng = random.Random(args.seed)
        for index in range(max(1, args.n)):
            params = resolve_params(args, rng)
            yield generate(
                StoryParams(
                    room=params.room,
                    clue=params.clue,
                    hiding=params.hiding,
                    tool=params.tool,
                    ending=params.ending,
                    seed=args.seed + index,
                )
            )
        return
    combos = all_params()
    rng = random.Random(args.seed)
    rng.shuffle(combos)
    count = max(1, args.n)
    for index in range(count):
        chosen = combos[index % len(combos)]
        yield generate(
            StoryParams(
                room=chosen.room,
                clue=chosen.clue,
                hiding=chosen.hiding,
                tool=chosen.tool,
                ending=chosen.ending,
                seed=args.seed + index,
            )
        )


def trace_lines(world: FireStationWorld) -> list[str]:
    mira = world.get("mira")
    cat = world.get("cat")
    star = world.get("star")
    station = world.get("station")
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(
        "  star_location={location} present={present:.1f} hidden={hidden:.1f} found={found:.1f}".format(
            location=star.attrs.get("location", "unknown"),
            present=star.meters["present"],
            hidden=star.meters["hidden"],
            found=star.meters["found"],
        )
    )
    lines.append(
        "  mira_curiosity={curiosity:.2f} mira_worry={worry:.2f} mira_trust={trust:.2f} confidence={confidence:.2f}".format(
            curiosity=mira.memes["curiosity"],
            worry=mira.memes["worry"],
            trust=mira.memes["trust"],
            confidence=mira.meters["confidence"],
        )
    )
    lines.append(
        "  cat_glow={glow:.2f} cat_guide={guide:.2f} station_mystery={mystery:.2f} station_relief={relief:.2f}".format(
            glow=cat.meters["glow"],
            guide=cat.meters["guide"],
            mystery=station.memes["mystery"],
            relief=station.memes["relief"],
        )
    )
    return lines


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        payload = sample.to_dict()
        if header:
            payload = {"header": header, **payload}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    if header:
        print(header)
    print(sample.story)
    if args.trace:
        print()
        print("\n".join(trace_lines(sample.world)))
    if args.qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nStory QA:")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\nWorld QA:")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        samples = list(iter_samples(args))
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = None
            if args.all:
                p = sample.params
                header = (
                    f"### room={p.room} clue={p.clue} hiding={p.hiding} "
                    f"tool={p.tool} ending={p.ending}"
                )
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, args, header=header)
            if index < len(samples) - 1:
                print("\n---\n")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
