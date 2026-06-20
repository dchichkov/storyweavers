#!/usr/bin/env python3
"""A mystery-leaning fire-station storyworld about a shiny cat, inner thoughts, and rescue magic.

Internal source tale:
Tess waits in a small fire station while Captain Imani checks the gear for a
children's safety night. The silver station whistle that starts the safety walk
goes missing, and a shiny cat appears under the red lamps as if it has carried
moonlight indoors. Tess first wonders whether the cat stole the whistle, but
the cat's magic keeps revealing careful clues in one part of the station. By
trusting those clues, using the right recovery tool, and reading the room
closely, Tess finds the whistle, learns the cat was guarding it from harm, and
ends the night with the station ready and peaceful again.
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
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)


ROOMS: dict[str, StationRoom] = {
    "engine_bay": StationRoom(
        id="engine_bay",
        name="the engine bay",
        opening=(
            "Rain stroked the wide doors of the fire station while Tess stood near the red truck and watched Captain Imani set out lanterns for the children's safety night."
        ),
        hush="Even the metal ladders seemed to hold their breath between one drip and the next.",
        ending_image="Around them, the engine bay glowed gently, with the truck windows holding still pools of light.",
    ),
    "bunk_hall": StationRoom(
        id="bunk_hall",
        name="the bunk hall",
        opening=(
            "The fire station was quiet except for the soft hum of drying coats as Tess followed Captain Imani past the bunk hall before the children's safety night."
        ),
        hush="The row of bunks looked like a line of careful secrets under the dim red night lamp.",
        ending_image="Around them, the bunk hall rested softly, with every blanket smooth and every boot paired again.",
    ),
    "radio_desk": StationRoom(
        id="radio_desk",
        name="the radio desk",
        opening=(
            "At the radio desk inside the fire station, Tess listened to the sleepy crackle of the speaker while Captain Imani arranged little safety maps for the evening visitors."
        ),
        hush="The message cubbies and pencils sat so neatly that one wrong shadow looked important.",
        ending_image="Around them, the radio desk shone warm, with the map edges flat and the speaker finally quiet.",
    ),
}


CLUES: dict[str, MagicClue] = {
    "ladder_sparks": MagicClue(
        id="ladder_sparks",
        place="engine_bay",
        sign="The shiny cat stepped onto the truck bumper, and its paws left bright silver sparks that climbed toward one ladder bracket instead of the floor.",
        thought='"A thief would run from the truck," Tess thought. "This cat keeps pointing me back to the same place."',
        reading="The sparks made Tess search above eye level, where something slim and silver could have caught instead of falling away.",
    ),
    "window_reflection": MagicClue(
        id="window_reflection",
        place="engine_bay",
        sign="A stripe of moony light slid off the cat's fur and flashed in the truck window until one narrow gap glinted back at Tess.",
        thought='"That flash answered the cat like a secret answer," Tess thought. "Magic is showing me the hiding place, not the culprit."',
        reading="The returning glint told Tess that the missing whistle was stuck in a slot near the truck and not lost somewhere outside.",
    ),
    "cot_moons": MagicClue(
        id="cot_moons",
        place="bunk_hall",
        sign="The shiny cat padded along the bunk rail, and little moons of light appeared under one bed before fading into the shadows.",
        thought='"If the cat wanted me scared, it would vanish," Tess thought. "Instead it keeps lighting the floor like a helper."',
        reading="Those soft moons showed Tess that the mystery was hiding low, where a quick glance would miss it.",
    ),
    "boot_whisper": MagicClue(
        id="boot_whisper",
        place="bunk_hall",
        sign="The cat brushed its tail across the boot rack, and one hanging charm of dust twirled toward the far bunk frame as if a whisper had tugged it there.",
        thought='"Dust does not choose a direction by itself," Tess thought. "Something under that bunk wants to be found."',
        reading="The twirling dust pointed toward the end of the bunk hall where the whistle had slid beyond easy reach.",
    ),
    "blue_whiskers": MagicClue(
        id="blue_whiskers",
        place="radio_desk",
        sign="The cat sat on the radio desk, and its whiskers glowed blue like tiny wires until they all aimed at the narrow side gap of a message cubby.",
        thought='"Those whiskers look like arrows," Tess thought. "Maybe the cat is speaking in magic because it cannot use words."',
        reading="The glowing whiskers narrowed the whole desk down to one cubby gap that looked too thin for a hand.",
    ),
    "paper_star": MagicClue(
        id="paper_star",
        place="radio_desk",
        sign="When the cat purred, a paper star from the map stack shivered across the desk and stopped beside one dark crack in the cubbies.",
        thought='"The purr moved the paper like a pointer," Tess thought. "The magic wants me to notice that crack."',
        reading="The paper star marked the exact corner where the missing whistle had slipped out of sight.",
    ),
}


HIDINGS: dict[str, HidingSpot] = {
    "ladder_slot": HidingSpot(
        id="ladder_slot",
        place="engine_bay",
        obstacle="high_slot",
        cause="When the truck rolled back after practice, a loose training rope brushed the whistle from its hook and flipped it into a narrow ladder slot above the bumper.",
        evidence="a thin silver scrape beside the bracket and one clean pawprint on the bumper dust",
        discovery="The silver station whistle was wedged in the ladder slot, shining whenever the cat's magic touched the metal edge.",
        truth="The cat had kept watch by the truck because one hard door slam could have shaken the whistle into the engine pit where it would have been much harder to reach.",
    ),
    "under_bunk": HidingSpot(
        id="under_bunk",
        place="bunk_hall",
        obstacle="low_gap",
        cause="A swinging coat hem had knocked the whistle from its peg, and it skidded under the far bunk until the frame trapped it in the low gap.",
        evidence="a silver half-circle in the dust and a line of paw taps stopping at the bunk leg",
        discovery="The silver station whistle was lying just beyond the bunk rail, bright and still under the low frame.",
        truth="The cat had stayed near the bunk hall because boots would have kicked the whistle farther back if it had not guarded the place first.",
    ),
    "cubby_crack": HidingSpot(
        id="cubby_crack",
        place="radio_desk",
        obstacle="narrow_crack",
        cause="A draft from the side door had pushed the whistle off the radio desk and down the side of the message cubbies, where it stood hidden in a narrow crack.",
        evidence="a silver edge below the paper stack and a tiny trail where a paw kept tapping the same wood seam",
        discovery="The silver station whistle was standing on edge in the cubby crack, almost invisible until the magic glow found it.",
        truth="The cat had guarded the radio desk because one more bump from the speaker cord would have dropped the whistle all the way behind the cabinet.",
    ),
}


TOOLS: dict[str, RecoveryTool] = {
    "step_stool": RecoveryTool(
        id="step_stool",
        solves="high_slot",
        label="a blue step stool",
        action="Captain Imani opened a blue step stool, and Tess climbed high enough to guide a careful hand into the ladder slot until the whistle slid free.",
        proof="The step stool turned a dangerous reach into a steady rescue, so the whistle came down without anyone bumping the truck gear.",
    ),
    "boot_hook": RecoveryTool(
        id="boot_hook",
        solves="low_gap",
        label="a boot hook",
        action="Captain Imani lay flat with a boot hook while Tess held the lamp low, and together they drew the whistle gently out from under the bunk.",
        proof="The hook could reach the low gap without shoving the whistle deeper, which mattered because hands alone could not fit under the frame.",
    ),
    "ribbon_loop": RecoveryTool(
        id="ribbon_loop",
        solves="narrow_crack",
        label="a ribbon loop",
        action="Captain Imani tied a soft ribbon loop to a ruler, and Tess lowered it into the crack until the whistle caught and rose into the light.",
        proof="The ribbon loop fit the crack more safely than fingers could, so the whistle came out cleanly instead of slipping farther down.",
    ),
}


ENDINGS: dict[str, EndingStyle] = {
    "soft_bell": EndingStyle(
        id="soft_bell",
        closing="When Tess hung the whistle back on its peg, the station bell gave one soft note as if the building itself felt relieved.",
        image="The shiny cat blinked at the sound and sat very still, looking more like a guardian than a mystery.",
    ),
    "helmet_nest": EndingStyle(
        id="helmet_nest",
        closing="After the whistle was safe again, the shiny cat curled inside a spare helmet and let its silver glow dim to a sleepy ember.",
        image="The helmet looked like a small nest, and the whole station seemed ready to exhale.",
    ),
    "rain_clear": EndingStyle(
        id="rain_clear",
        closing="Tess rehung the whistle just as the rain thinned to a silver lace across the station windows.",
        image="In the calmer light, the shiny cat looked almost ordinary, which made the solved mystery feel even stranger and better.",
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
        return False, "the magic clue must belong to the chosen fire-station room"
    if hiding.place != params.room:
        return False, "the whistle must be hidden in the chosen room"
    if tool.solves != hiding.obstacle:
        return False, "the recovery tool does not fit the whistle's hiding obstacle"
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
            id="tess",
            kind="character",
            type="girl",
            label="Tess",
            role="child",
            meters=defaultdict(float, {"confidence": 0.3, "care": 0.5}),
            memes=defaultdict(float, {"curiosity": 1.8, "worry": 0.8, "trust": 0.4}),
        )
    )
    world.add(
        Entity(
            id="captain",
            kind="character",
            type="woman",
            label="Captain Imani",
            role="captain",
            meters=defaultdict(float, {"readiness": 0.7}),
            memes=defaultdict(float, {"calm": 1.7}),
        )
    )
    world.add(
        Entity(
            id="cat",
            kind="animal",
            type="cat",
            label="the shiny cat",
            role="cat",
            attrs={"location": room.name},
            meters=defaultdict(float, {"glow": 1.2, "guide": 0.0}),
            memes=defaultdict(float, {"magic": 2.1, "guarding": 1.4}),
        )
    )
    world.add(
        Entity(
            id="whistle",
            kind="physical",
            type="whistle",
            label="the silver station whistle",
            role="whistle",
            owner="captain",
            attrs={"location": "missing"},
            meters=defaultdict(float, {"hidden": 1.0, "found": 0.0, "present": 0.0}),
            memes=defaultdict(float, {"importance": 1.7}),
        )
    )
    world.add(
        Entity(
            id="station",
            kind="place",
            type="fire_station",
            label="the fire station",
            role="station",
            meters=defaultdict(float, {"calm": 0.4, "event_ready": 0.0}),
            memes=defaultdict(float, {"mystery": 1.6, "relief": 0.0}),
        )
    )
    world.add(
        Entity(
            id="room",
            kind="place",
            type="room",
            label=room.name,
            role="room",
            attrs={"id": room.id},
            meters=defaultdict(float, {"quiet": 1.0}),
            memes=defaultdict(float, {"shadow": 0.8}),
        )
    )
    world.facts["room_name"] = room.name
    world.facts["missing_object"] = "the silver station whistle"
    world.facts["inner_monologue"] = False
    world.facts["magic_used"] = False
    world.facts["cat_cleared"] = False
    world.facts["station_restored"] = False
    world.facts["tool_label"] = TOOLS[params.tool].label
    world.facts["clue_text"] = ""
    return world


def opening_scene(world: FireStationWorld) -> None:
    room = ROOMS[world.params.room]
    world.record(
        "opening",
        f"{room.opening} The silver station whistle that began the safety walk should have been hanging by Captain Imani's hand, but its hook was empty.",
        "captain",
        "whistle",
    )
    world.record(
        "arrival",
        f"A shiny cat sat nearby with fur bright enough to look polished by moonlight. {room.hush}",
        "cat",
        "room",
    )
    world.get("station").memes["mystery"] += 0.4
    world.get("tess").memes["worry"] += 0.2


def name_the_problem(world: FireStationWorld) -> None:
    world.para()
    world.record(
        "loss",
        "Captain Imani said the children listened for that whistle before every safety walk, so the fire station could not feel truly ready without it. Tess looked from the empty hook to the cat and felt the quiet become a puzzle.",
        "captain",
        "station",
    )
    world.record(
        "thought_begin",
        '"Did the shiny cat take it, or is it trying to tell me something?" Tess thought. "A real thief would hide from me, not wait under the lamp."',
        "tess",
        "cat",
    )
    world.facts["inner_monologue"] = True
    world.get("tess").memes["worry"] += 0.4
    world.get("tess").memes["curiosity"] += 0.3


def follow_magic(world: FireStationWorld) -> None:
    clue = CLUES[world.params.clue]
    world.para()
    world.record(
        "magic_clue",
        f"The shiny cat trotted toward {world.facts['room_name']} and then let its magic do the talking. {clue.sign}",
        "cat",
        "room",
    )
    world.record(
        "thought_turn",
        clue.thought,
        "tess",
        "cat",
    )
    world.record(
        "reading",
        clue.reading,
        "tess",
        "whistle",
    )
    world.facts["magic_used"] = True
    world.facts["clue_text"] = clue.sign
    world.get("cat").meters["guide"] += 1.0
    world.get("tess").memes["trust"] += 0.8
    world.get("tess").meters["confidence"] += 0.4


def recover_whistle(world: FireStationWorld) -> None:
    hiding = HIDINGS[world.params.hiding]
    tool = TOOLS[world.params.tool]
    whistle = world.get("whistle")
    station = world.get("station")
    world.para()
    world.record(
        "cause",
        hiding.cause,
        "station",
        "whistle",
    )
    world.record(
        "evidence",
        f"Tess crouched close and found {hiding.evidence}. The mystery stopped feeling huge once the room finally gave her a true direction.",
        "tess",
        "whistle",
    )
    world.record(
        "recovery",
        f"{tool.action} {hiding.discovery}",
        "captain",
        "whistle",
    )
    world.record(
        "proof",
        tool.proof,
        "captain",
        "tess",
    )
    whistle.meters["hidden"] = 0.0
    whistle.meters["found"] = 1.0
    whistle.meters["present"] = 1.0
    whistle.attrs["location"] = "peg"
    station.meters["event_ready"] = 1.0
    station.meters["calm"] = 1.0
    world.get("station").memes["relief"] += 1.2
    world.get("station").memes["mystery"] = max(0.0, world.get("station").memes["mystery"] - 1.0)
    world.get("tess").memes["worry"] = max(0.0, world.get("tess").memes["worry"] - 0.8)
    world.get("tess").memes["trust"] += 0.5
    world.get("tess").meters["confidence"] += 0.5


def resolve_story(world: FireStationWorld) -> None:
    hiding = HIDINGS[world.params.hiding]
    ending = ENDINGS[world.params.ending]
    cat = world.get("cat")
    room = ROOMS[world.params.room]
    world.para()
    world.record(
        "truth",
        hiding.truth,
        "tess",
        "cat",
    )
    world.record(
        "acceptance",
        '"You were guarding it the whole time," Tess whispered. The shiny cat gave a slow blink, and the room no longer felt full of suspicion.',
        "tess",
        "cat",
    )
    world.record(
        "ending",
        f"{ending.closing} {ending.image} {room.ending_image} The fire station felt ready for children again.",
        "station",
        "whistle",
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
        f"Include a shiny cat whose magic reveals clues in {room.name}.",
        "Use inner monologue so the child moves from suspicion to trust before the ending image.",
    ]


def story_qa_for(world: FireStationWorld) -> list[QAItem]:
    room = ROOMS[world.params.room]
    clue = CLUES[world.params.clue]
    hiding = HIDINGS[world.params.hiding]
    tool = TOOLS[world.params.tool]
    return [
        QAItem(
            question="Why did Tess stop thinking the shiny cat was the thief?",
            answer=(
                "Tess stopped blaming the shiny cat because it stayed beside the mystery and kept making careful clues instead of running away. "
                f"When the magic clue appeared in {room.name}, she understood that the cat was guiding her toward the whistle."
            ),
        ),
        QAItem(
            question="What magic clue helped Tess search in the right place?",
            answer=(
                f"The key clue was this: {clue.sign} "
                "That sign narrowed the search from the whole station to one exact part of the room."
            ),
        ),
        QAItem(
            question="How did Tess and Captain Imani get the whistle back?",
            answer=(
                f"They used {tool.label} to reach the whistle where it was trapped. "
                f"{tool.proof}"
            ),
        ),
        QAItem(
            question="Where had the whistle really gone, and why was the cat guarding it?",
            answer=(
                f"The whistle had ended up in {room.name}. "
                f"{hiding.truth}"
            ),
        ),
    ]


def world_qa_for(world: FireStationWorld) -> list[QAItem]:
    hiding = HIDINGS[world.params.hiding]
    ending = ENDINGS[world.params.ending]
    return [
        QAItem(
            question="Why did the silver station whistle matter so much?",
            answer=(
                "The silver station whistle mattered because Captain Imani used it to begin the children's safety walk. "
                "Without it, the station did not feel fully ready for the evening visitors."
            ),
        ),
        QAItem(
            question="What caused the whistle to go missing in the first place?",
            answer=(
                "The whistle went missing because station motion knocked or pushed it out of its usual place. "
                f"{hiding.cause}"
            ),
        ),
        QAItem(
            question="How do we know the mystery is over by the end?",
            answer=(
                "We know the mystery is over because the whistle is back on its peg and the station is calm again. "
                f"{ending.closing}"
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    opening_scene(world)
    name_the_problem(world)
    follow_magic(world)
    recover_whistle(world)
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
            raise StoryError(f"station was not restored by the end for params={params}")
        if world.get("whistle").meters["found"] < 1.0:
            raise StoryError(f"whistle was not recovered for params={params}")
        if world.get("station").meters["event_ready"] < 1.0:
            raise StoryError(f"station was not ready for visitors for params={params}")
        if "  " in story or "{}" in story or "Trace:" in story:
            raise StoryError(f"story leaked scaffolding for params={params}")
    return (
        f"OK: Python and ASP agree on {len(python_combos)} valid shiny-cat fire-station mysteries, "
        "and every generated story restores the silver station whistle through grounded magical clues."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--room", choices=sorted(ROOMS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--hiding", choices=sorted(HIDINGS))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--ending", choices=sorted(ENDINGS))
    parser.add_argument("--seed", type=int, default=23)
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
    chosen = rng.choice(all_params())
    return StoryParams(
        room=chosen.room,
        clue=chosen.clue,
        hiding=chosen.hiding,
        tool=chosen.tool,
        ending=chosen.ending,
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
    tess = world.get("tess")
    cat = world.get("cat")
    whistle = world.get("whistle")
    station = world.get("station")
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("State:")
    lines.append(
        "  whistle_location={location} hidden={hidden:.1f} found={found:.1f} present={present:.1f}".format(
            location=whistle.attrs.get("location", "unknown"),
            hidden=whistle.meters["hidden"],
            found=whistle.meters["found"],
            present=whistle.meters["present"],
        )
    )
    lines.append(
        "  tess_curiosity={curiosity:.2f} tess_worry={worry:.2f} tess_trust={trust:.2f} confidence={confidence:.2f}".format(
            curiosity=tess.memes["curiosity"],
            worry=tess.memes["worry"],
            trust=tess.memes["trust"],
            confidence=tess.meters["confidence"],
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
