#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/folder_diffuse_point_conflict_repetition_foreshadowing_superhero.py
====================================================================================================

A standalone storyworld for a small superhero-style tale built from the seed
words "folder", "diffuse", and "point". The domain is a kid-sized hero mission:
a young hero and a helper prepare a rescue, a smoky problem hides the way, a
villain creates conflict, repeated calls and repeated actions drive the middle,
and foreshadowing pays off in the end when a simple clue turns into a clean
save.

The world is deliberately tiny:
- a hero, a sidekick, a mentor, and a villain
- one room with meters for smoke and damage
- one folder holding a clue
- one pointy signal that can guide the rescue
- a diffuse cloud that can spread and then be broken apart

The prose is state-driven. It is not a frozen paragraph with swapped nouns:
meters and memes change through the story, and the ending image proves what
changed.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/folder_diffuse_point_conflict_repetition_foreshadowing_superhero.py
    python storyworlds/worlds/gpt-5.4-mini/folder_diffuse_point_conflict_repetition_foreshadowing_superhero.py --qa
    python storyworlds/worlds/gpt-5.4-mini/folder_diffuse_point_conflict_repetition_foreshadowing_superhero.py --verify
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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    room_word: str
    mood: str
    dark_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    source: str
    spread: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    hero: str
    sidekick: str
    mentor: str
    villain: str
    folder: str
    hazard: str
    response: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_diffuse(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["smoke"] < THRESHOLD:
        return out
    sig = ("diffuse",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for name in ("hero", "sidekick", "mentor"):
        world.get(name).memes["worry"] += 1
    room = world.get("room")
    room.meters["visibility"] = max(0.0, room.meters["visibility"] - 1.0)
    out.append("__diffuse__")
    return out


def _r_conflict(world: World) -> list[str]:
    if world.get("villain").meters["trouble"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["anger"] += 1
    world.get("sidekick").memes["fear"] += 1
    return ["__conflict__"]


CAUSAL_RULES = [Rule("diffuse", _r_diffuse), Rule("conflict", _r_conflict)]


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


def reasonableness_gate(setting: Setting, folder: Item, hazard: Hazard, response: Response) -> bool:
    return bool(setting and folder and hazard and response.sense >= SENSE_MIN)


def hazard_risk(setting: Setting, hazard: Hazard) -> bool:
    return "smoke" in hazard.tags and "room" in setting.tags


def response_can_handle(response: Response, hazard: Hazard) -> bool:
    return response.power >= hazard.spread


def predicted_outcome(params: StoryParams) -> str:
    hz = HAZARDS[params.hazard]
    rsp = RESPONSES[params.response]
    return "safe" if response_can_handle(rsp, hz) else "stuck"


def fold_diffuse_point_story(world: World, hero: Entity, sidekick: Entity, mentor: Entity,
                             villain: Entity, folder: Entity, clue: Item, hazard: Hazard,
                             response: Response) -> None:
    hero.memes["hope"] += 1
    sidekick.memes["hope"] += 1
    world.say(
        f"At {world.setting.place}, {hero.id} and {sidekick.id} were the tiny heroes "
        f"of {world.setting.room_word}. {mentor.id} had left a {folder.label_word} on the desk, "
        f"and inside it was a clue that pointed toward the safe door."
    )
    world.say(
        f"{hero.id} tapped the {folder.label} once, then tapped it again. "
        f"\"Keep the {folder.label} safe,\" {mentor.id} had said, and the words stuck."
    )
    world.say(
        f"That night the air was {world.setting.mood}, and a {hazard.label} began to "
        f"{hazard.source}. The {hazard.label} was ready to diffuse through the room."
    )

    world.para()
    hero.memes["resolve"] += 1
    sidekick.memes["resolve"] += 1
    world.say(
        f"Then {villain.id} burst in, laughing. \"If you want to stop me, point to the clue!\" "
        f"{villain.id} said. \"Point to the clue! Point to the clue!\""
    )
    world.say(
        f"{sidekick.id} pointed at the {folder.label} first. {hero.id} pointed at the floor, "
        f"where the smoke was starting to swirl. The old clue mattered now."
    )

    world.para()
    world.get("room").meters["smoke"] += 1
    propagate(world, narrate=False)

    if response_can_handle(response, hazard):
        world.say(
            f"{mentor.id} came in calm and quick. {response.text.replace('{hazard}', hazard.label)}."
        )
        world.get("room").meters["smoke"] = 0.0
        world.get("room").meters["visibility"] = 1.0
        world.get("villain").meters["trouble"] = 0.0
        hero.memes["joy"] += 1
        sidekick.memes["joy"] += 1
        world.say(
            f"The smoke faded, and the room felt bigger again. {hero.id} opened the "
            f"{folder.label} with steady hands, and the clue inside pointed them straight "
            f"to the safe exit."
        )
        world.say(
            f"{sidekick.id} smiled and pointed one last time, not at danger, but at the open door. "
            f"The little heroes walked out together, and the {folder.label} stayed tucked under {hero.id}'s arm."
        )
        world.facts["outcome"] = "safe"
    else:
        world.say(
            f"{mentor.id} rushed in and {response.fail.replace('{hazard}', hazard.label)}."
        )
        world.get("room").meters["smoke"] += 1
        world.get("room").meters["damage"] += 1
        hero.memes["worry"] += 1
        sidekick.memes["worry"] += 1
        world.say(
            f"The {hazard.label} kept spreading, and the room turned dim and gray. "
            f"The clue still pointed to the exit, but the heroes had to get out fast."
        )
        world.say(
            f"They did get out, clutching the {folder.label}, but the mission had changed into a rescue."
        )
        world.facts["outcome"] = "stuck"


SETTINGS = {
    "hideout": Setting(
        id="hideout",
        place="the rooftop hideout",
        room_word="hideout",
        mood="misty",
        dark_spot="the shadow near the stairs",
        tags={"room", "rooftop"},
    ),
    "museum": Setting(
        id="museum",
        place="the night museum",
        room_word="gallery",
        mood="smoky",
        dark_spot="the hall by the glass case",
        tags={"room", "museum"},
    ),
}

HEROES = {
    "spark": ("Spark Kid", "boy"),
    "beam": ("Beam Girl", "girl"),
    "mosaic": ("Mosaic", "girl"),
}

SIDEKICKS = {
    "zip": ("Zip", "boy"),
    "orbit": ("Orbit", "boy"),
    "nova": ("Nova", "girl"),
}

MENTORS = {
    "captain": ("Captain Lantern", "man"),
    "warden": ("Warden Bright", "woman"),
}

VILLAINS = {
    "smudge": ("Dr. Smudge", "man"),
    "hush": ("Hush Hood", "woman"),
}

FOLDERS = {
    "red": Item(
        id="red_folder",
        label="folder",
        phrase="a bright red folder",
        purpose="holds the clue",
        tags={"folder"},
    ),
    "blue": Item(
        id="blue_folder",
        label="folder",
        phrase="a blue folder with a silver sticker",
        purpose="holds the clue",
        tags={"folder"},
    ),
}

CLUES = {
    "point": Item(
        id="point_clue",
        label="point",
        phrase="a point-shaped clue",
        purpose="shows the way",
        tags={"point"},
    ),
    "arrow": Item(
        id="arrow_clue",
        label="point",
        phrase="a point that looked like an arrow",
        purpose="shows the way",
        tags={"point"},
    ),
}

HAZARDS = {
    "smoke": Hazard(
        id="smoke",
        label="smoke cloud",
        phrase="a smoke cloud",
        source="diffuse across the room",
        spread=2,
        tags={"smoke"},
    ),
}

RESPONSES = {
    "fan": Response(
        id="fan",
        sense=3,
        power=3,
        text="switched on the fan and pushed the smoke away in a fast, steady stream",
        fail="switched on the fan, but the smoke was too thick to clear",
        qa_text="switched on the fan and pushed the smoke away",
        tags={"fan"},
    ),
    "shield": Response(
        id="shield",
        sense=2,
        power=2,
        text="raised a clear shield and guided everyone under it until the air calmed down",
        fail="raised a shield, but the smoke slipped around it anyway",
        qa_text="raised a clear shield and guided everyone through",
        tags={"shield"},
    ),
    "spray": Response(
        id="spray",
        sense=1,
        power=1,
        text="sprayed water everywhere, hoping for the best",
        fail="sprayed water everywhere, but it only made the mess bigger",
        qa_text="sprayed water everywhere",
        tags={"water"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid in HAZARDS:
            for rid, response in RESPONSES.items():
                if hazard_risk(setting, HAZARDS[hid]) and response.sense >= SENSE_MIN:
                    combos.append((sid, "red", hid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with folder, diffuse, and point.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--mentor", choices=MENTORS)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--folder", choices=FOLDERS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--clue", choices=CLUES)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{args.response}': too weak for a superhero rescue.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard = args.hazard or "smoke"
    response = args.response or rng.choice([k for k, v in RESPONSES.items() if v.sense >= SENSE_MIN])
    if not hazard_risk(SETTINGS[setting], HAZARDS[hazard]):
        raise StoryError("(No story: this setting and hazard do not form a believable rescue.)")
    return StoryParams(
        setting=setting,
        hero=args.hero or rng.choice(list(HEROES)),
        sidekick=args.sidekick or rng.choice(list(SIDEKICKS)),
        mentor=args.mentor or rng.choice(list(MENTORS)),
        villain=args.villain or rng.choice(list(VILLAINS)),
        folder=args.folder or rng.choice(list(FOLDERS)),
        hazard=hazard,
        response=response,
        clue=args.clue or rng.choice(list(CLUES)),
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    hero_name, hero_gender = HEROES.get(params.hero, ("", ""))
    side_name, side_gender = SIDEKICKS.get(params.sidekick, ("", ""))
    mentor_name, mentor_gender = MENTORS.get(params.mentor, ("", ""))
    villain_name, villain_gender = VILLAINS.get(params.villain, ("", ""))
    folder = FOLDERS.get(params.folder)
    hazard = HAZARDS.get(params.hazard)
    response = RESPONSES.get(params.response)
    clue = CLUES.get(params.clue)
    if not all([setting, hero_name, side_name, mentor_name, villain_name, folder, hazard, response, clue]):
        raise StoryError("Invalid parameters for this storyworld.")

    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    sidekick = world.add(Entity(id=side_name, kind="character", type=side_gender, role="sidekick"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender, role="mentor"))
    villain = world.add(Entity(id=villain_name, kind="character", type=villain_gender, role="villain"))
    folder_ent = world.add(Entity(id="folder", type="thing", label="folder", tags={"folder"}))
    room = world.add(Entity(id="room", type="room", label=setting.room_word))
    clue_ent = world.add(Entity(id="clue", type="thing", label="point", tags={"point"}))

    folder_ent.meters["safe"] = 1.0
    clue_ent.meters["bright"] = 1.0
    world.facts.update(setting=setting, hero=hero, sidekick=sidekick, mentor=mentor,
                       villain=villain, folder=folder, hazard=hazard, response=response,
                       clue=clue, outcome="")

    world.say(
        f"In {setting.place}, {hero.id} and {sidekick.id} trained like tiny superheroes. "
        f"They kept a {folder.label} close because the best rescue plans began with a clue."
    )
    world.say(
        f"{mentor.id} pointed to the {clue.label} inside the {folder.label} and said, "
        f"\"Always point to the way out before the trouble gets loud.\""
    )
    world.say(
        f"{hero.id} repeated it once, then again: point to the way out, point to the way out. "
        f"It sounded like a promise."
    )

    world.para()
    world.get("room").meters["smoke"] += 1
    world.get("villain").meters["trouble"] += 1
    world.say(
        f"That evening, {villain.id} returned and tried to {hazard.source}. "
        f"The {hazard.label} began to diffuse through {setting.room_word}, and the windows went gray."
    )
    world.say(
        f"{sidekick.id} pointed at the floor. {hero.id} pointed at the folder. "
        f"The old clue came back like a light turned on twice."
    )

    world.para()
    fold_diffuse_point_story(world, hero, sidekick, mentor, villain, folder_ent, clue, hazard, response)

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
        f'Write a superhero story for a young child that includes the words "folder", "diffuse", and "point".',
        f"Tell a rescue story where {f['hero'].id} and {f['sidekick'].id} use a {f['folder'].label} clue to stop {f['villain'].id}'s smoky plan.",
        f"Write a story with conflict, repetition, and foreshadowing where a point-shaped clue in a folder helps the heroes escape a diffusing smoke cloud.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    mentor: Entity = f["mentor"]
    villain: Entity = f["villain"]
    folder: Item = f["folder"]
    hazard: Hazard = f["hazard"]
    response: Response = f["response"]
    qa = [
        ("Who are the story's heroes?",
         f"The story is about {hero.id} and {sidekick.id}, two tiny superheroes who stayed close to {mentor.id}'s plan."),
        ("What did the folder do in the story?",
         f"The folder held the clue, and that clue pointed to the safe way out. It mattered because the heroes had to keep track of the right direction when the room got smoky."),
        ("Why was there conflict?",
         f"{villain.id} tried to make {hazard.label} spread through the room, so the heroes had to stop the trouble quickly. That created a superhero-sized problem that needed a fast answer."),
    ]
    if f.get("outcome") == "safe":
        qa.append((
            "How did the heroes solve the problem?",
            f"{mentor.id} used a calm rescue and {response.qa_text}, which cleared the air. After that, {hero.id} and {sidekick.id} used the clue in the folder to point straight to the exit."
        ))
        qa.append((
            "How did repetition help?",
            f"{hero.id} kept repeating the same rescue words, and that helped everyone remember the plan. The repeated pointing also kept the clue important when the smoke made the room hard to read."
        ))
        qa.append((
            "What was foreshadowed earlier?",
            f"The clue in the folder pointed to the exit before the trouble really started, so the ending was prepared from the beginning. When the smoke diffused later, the old clue suddenly became useful."
        ))
    else:
        qa.append((
            "What happened when the rescue was not enough?",
            f"{response.fail.replace('{hazard}', hazard.label).capitalize()}. The room got dimmer, and the heroes had to leave fast even though they still held the folder."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a folder?",
         "A folder is something that holds papers or clues together so they do not get lost."),
        ("What does diffuse mean?",
         "Diffuse means to spread out through a space, like smoke moving into a room."),
        ("What does it mean to point?",
         "To point is to aim a finger or object toward something to show where it is."),
        ("Why can smoke be dangerous?",
         "Smoke makes it hard to see and breathe, so people should get away from it quickly and call for help."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
folder_item(fld).
hazard(smoke).
response(fan).
response(shield).
response(spray).
sensible(R) :- response(R), R != spray.
valid(setting, folder, hazard, response) :- folder_item(folder), hazard(hazard), sensible(response).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid in FOLDERS:
        lines.append(asp.fact("folder", fid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    return predicted_outcome(params)


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        _ = sample.to_json()
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: smoke test crashed: {e}")
        return 1
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        if py != cl:
            rc = 1
            print("MISMATCH: ASP and Python valid_combos differ.")
        else:
            print(f"OK: ASP and Python gate match ({len(py)} combos).")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: ASP verification crashed: {e}")
        return 1
    return rc


def build_sample_world(params: StoryParams) -> StorySample:
    return generate(params)


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
    StoryParams(
        setting="hideout",
        hero="spark",
        sidekick="zip",
        mentor="captain",
        villain="smudge",
        folder="red",
        hazard="smoke",
        response="fan",
        clue="point",
    ),
    StoryParams(
        setting="museum",
        hero="beam",
        sidekick="nova",
        mentor="warden",
        villain="hush",
        folder="blue",
        hazard="smoke",
        response="shield",
        clue="arrow",
    ),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{args.response}': too weak for a superhero rescue.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard = args.hazard or "smoke"
    response = args.response or rng.choice([k for k, v in RESPONSES.items() if v.sense >= SENSE_MIN])
    if not hazard_risk(SETTINGS[setting], HAZARDS[hazard]):
        raise StoryError("(No story: this setting and hazard do not form a believable rescue.)")
    return StoryParams(
        setting=setting,
        hero=args.hero or rng.choice(list(HEROES)),
        sidekick=args.sidekick or rng.choice(list(SIDEKICKS)),
        mentor=args.mentor or rng.choice(list(MENTORS)),
        villain=args.villain or rng.choice(list(VILLAINS)),
        folder=args.folder or rng.choice(list(FOLDERS)),
        hazard=hazard,
        response=response,
        clue=args.clue or rng.choice(list(CLUES)),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "folder", "diffuse", and "point".',
        f"Tell a rescue story where {f['hero'].id} and {f['sidekick'].id} use a {f['folder'].label} clue to stop {f['villain'].id}'s smoky plan.",
        f"Write a story with conflict, repetition, and foreshadowing where a point-shaped clue in a folder helps the heroes escape a diffusing smoke cloud.",
    ]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    hero_name, hero_gender = HEROES.get(params.hero, ("", ""))
    side_name, side_gender = SIDEKICKS.get(params.sidekick, ("", ""))
    mentor_name, mentor_gender = MENTORS.get(params.mentor, ("", ""))
    villain_name, villain_gender = VILLAINS.get(params.villain, ("", ""))
    folder = FOLDERS.get(params.folder)
    hazard = HAZARDS.get(params.hazard)
    response = RESPONSES.get(params.response)
    clue = CLUES.get(params.clue)
    if not all([setting, hero_name, side_name, mentor_name, villain_name, folder, hazard, response, clue]):
        raise StoryError("Invalid parameters for this storyworld.")
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    sidekick = world.add(Entity(id=side_name, kind="character", type=side_gender, role="sidekick"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_gender, role="mentor"))
    villain = world.add(Entity(id=villain_name, kind="character", type=villain_gender, role="villain"))
    folder_ent = world.add(Entity(id="folder", type="thing", label="folder", tags={"folder"}))
    world.add(Entity(id="room", type="room", label=setting.room_word))
    world.add(Entity(id="clue", type="thing", label="point", tags={"point"}))
    world.facts.update(hero=hero, sidekick=sidekick, mentor=mentor, villain=villain,
                       folder=folder, hazard=hazard, response=response, clue=clue)
    world.say(
        f"In {setting.place}, {hero.id} and {sidekick.id} trained like tiny superheroes. "
        f"They kept a {folder.label} close because the best rescue plans began with a clue."
    )
    world.say(
        f"{mentor.id} pointed to the {clue.label} inside the {folder.label} and said, "
        f"\"Always point to the way out before the trouble gets loud.\""
    )
    world.say(
        f"{hero.id} repeated it once, then again: point to the way out, point to the way out. "
        f"It sounded like a promise."
    )
    world.para()
    world.get("room").meters["smoke"] += 1
    world.get("villain").meters["trouble"] += 1
    world.say(
        f"That evening, {villain.id} returned and tried to {hazard.source}. "
        f"The {hazard.label} began to diffuse through {setting.room_word}, and the windows went gray."
    )
    world.say(
        f"{sidekick.id} pointed at the floor. {hero.id} pointed at the folder. "
        f"The old clue came back like a light turned on twice."
    )
    world.para()
    fold_diffuse_point_story(world, hero, sidekick, mentor, villain, folder_ent, clue, hazard, response)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        for row in asp_valid_combos():
            print(row)
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
            header = f"### {p.hero} & {p.sidekick} in {p.setting} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
