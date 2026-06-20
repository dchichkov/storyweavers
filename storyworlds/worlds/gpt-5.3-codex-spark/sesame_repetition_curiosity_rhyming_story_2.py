#!/usr/bin/env python3
"""sesame_repetition_curiosity_rhyming_story_2.py
===================================================

A short source tale is used as the internal model seed:

Mila and Jun hear a short rhyme while baking with sesame seeds.
Each time they repeat it, the rhyme becomes clearer and points to a hidden jar.
They resist panic, test the line again and again, choose the tool that fits the
locked jar at its hiding spot, and end with a concrete image of the sesame jar
opened and ready for mixing.

Words: sesame
Features: Repetition, Curiosity
Style: Rhyming Story
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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class HidingSpot:
    key: str
    label: str
    lock: str
    start_line: str
    hidden_nook: str
    obstacle: str
    ending_image: str


@dataclass(frozen=True)
class SesameVerse:
    key: str
    line: str
    points_to: str
    misread: str


@dataclass(frozen=True)
class SesameTool:
    key: str
    label: str
    solves: str
    action: str
    why: str


@dataclass(frozen=True)
class StoryParams:
    spot: str
    verse: str
    tool: str
    seed: int | None = None


@dataclass
class Entity:
    key: str
    kind: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    location: str | None = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    facts: dict[str, str | int | float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class StoryWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.key] = ent
        return ent

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.events.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(parts) for parts in self.paragraphs if parts)


SPOTS: dict[str, HidingSpot] = {
    "attic_loop": HidingSpot(
        key="attic_loop",
        label="the attic window shelf",
        lock="twine_loop",
        start_line="the attic hummed low like a bell at night",
        hidden_nook="wedged on a beam knot behind a folded curtain",
        obstacle="A soft silk loop held the jar by the rim, patient and tight.",
        ending_image=(
            "the moonlit attic showed a clear sesame jar open on the beam shelf,"
            " with gold and white seeds glowing bright in a tiny silver stream"
        ),
    ),
    "pantry_panel": HidingSpot(
        key="pantry_panel",
        label="the pantry side panel",
        lock="wax_pinch",
        start_line="the pantry breathed warm and smelled sweet and light",
        hidden_nook="tucked inside a spice drawer behind a warm wax stripe",
        obstacle="A thin wax pinched the lid and refused a hard pull.",
        ending_image=(
            "the pantry side panel stood clear and cool while the sesame jar lay open"
            " on the counter, seeds spilling like tiny shining pebbles"
        ),
    ),
    "shed_wall": HidingSpot(
        key="shed_wall",
        label="the garden shed wall shelf",
        lock="mud_band",
        start_line="the shed kept its weathered rhythm through the light",
        hidden_nook="half buried against the wall where rain mud met a stone lip",
        obstacle="A ribbon of mud gripped the jar lip so no gentle hand could lift it.",
        ending_image=(
            "the shed wall shelf was clean and free, and the sesame jar sat open"
            " beside a blue cloth, every seed safe for baking and bright"
        ),
    ),
}

VERSES: dict[str, SesameVerse] = {
    "drum_verse": SesameVerse(
        key="drum_verse",
        line="Sesame, sesame, tap tap-tap, where did the little jar now go?",
        points_to="attic_loop",
        misread="The children first thought it asked for music, not a place.",
    ),
    "lamp_verse": SesameVerse(
        key="lamp_verse",
        line="Sesame, sesame, warm little glow, tell me which pantry holds your show?",
        points_to="pantry_panel",
        misread="At first it sounded like a bedtime rhyme and not a lead to follow.",
    ),
    "rain_verse": SesameVerse(
        key="rain_verse",
        line="Sesame, sesame, drip and track, point me where the bright seeds are at?",
        points_to="shed_wall",
        misread="Jun thought it might be a rain song made for grown-up jokes.",
    ),
}

TOOLS: dict[str, SesameTool] = {
    "loop_pin": SesameTool(
        key="loop_pin",
        label="a narrow loop pin",
        solves="twine_loop",
        action=(
            "Mila slipped the pin under the silk knot and loosened the knot first,"
            " then raised the jar from the beam without jerking."
        ),
        why="A loop knot can only open by prying the wrap off before lifting.",
    ),
    "wax_blower": SesameTool(
        key="wax_blower",
        label="a warm cloth blower",
        solves="wax_pinch",
        action=(
            "Jun warmed a clean cloth against the wax pinch and held it along the rim," \
            " then lifted the lid when the seal softened.") ,
        why="Wax loses its grip when gently warmed, so the jar opens safely.",
    ),
    "mud_flat": SesameTool(
        key="mud_flat",
        label="a small flat spatula",
        solves="mud_band",
        action=(
            "Mila scraped the mud edge away and lifted in a flat turn,"
            " giving the jar a clean path out of the seam."
        ),
        why="A flat edge breaks a mud band where a grip would drag and pinch.",
    ),
}


OPENING_IMAGES = (
    "A tiny spoon tap-tap sounded like a tiny drum through the kitchen tile.",
    "The morning smelled bright and sweet as if the day itself were ready to sing.",
)

TURN_IMAGES = (
    "Each repeat made the air feel less hurried and more bright.",
    "The same words fell into place and the room grew steadier by the line.",
)


def explain_invalid(spot: str | None, verse: str | None, tool: str | None) -> str:
    if spot is not None and spot not in SPOTS:
        return f"No story: unknown spot {spot!r}."
    if verse is not None and verse not in VERSES:
        return f"No story: unknown verse {verse!r}."
    if tool is not None and tool not in TOOLS:
        return f"No story: unknown tool {tool!r}."
    if spot and verse and (VERSES.get(verse) and VERSES[verse].points_to != spot):
        return "No story: selected verse points to a different spot."
    if spot and tool and (TOOLS.get(tool) and TOOLS[tool].solves != SPOTS[spot].lock):
        return "No story: selected tool cannot open this spot's lock."
    return "No story: invalid parameter mix."


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.spot not in SPOTS:
        return False, f"unknown spot: {params.spot}"
    if params.verse not in VERSES:
        return False, f"unknown verse: {params.verse}"
    if params.tool not in TOOLS:
        return False, f"unknown tool: {params.tool}"

    spot = SPOTS[params.spot]
    verse = VERSES[params.verse]
    tool = TOOLS[params.tool]

    if verse.points_to != params.spot:
        return False, "the verse points to a different spot"
    if tool.solves != spot.lock:
        return False, "the tool does not match the physical lock"

    return True, ""


def all_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    for spot in sorted(SPOTS):
        for verse in sorted(VERSES):
            for tool in sorted(TOOLS):
                params = StoryParams(spot=spot, verse=verse, tool=tool)
                if valid_params(params)[0]:
                    out.append(params)
    return out


def build_world(params: StoryParams) -> StoryWorld:
    spot = SPOTS[params.spot]
    verse = VERSES[params.verse]
    tool = TOOLS[params.tool]
    rng = random.Random(params.seed or 0)

    world = StoryWorld(params=params)

    world.add(Entity("mila", "character", "girl", "Mila", traits=["curious", "steady"]))
    world.add(Entity("jun", "character", "boy", "Jun", traits=["helpful", "careful"]))
    world.add(Entity("kitchen", "place", "kitchen", "the kitchen"))
    world.add(Entity("attic_loop", "place", "attic", SPOTS["attic_loop"].label))
    world.add(Entity("pantry_panel", "place", "pantry", SPOTS["pantry_panel"].label))
    world.add(Entity("shed_wall", "place", "shed", SPOTS["shed_wall"].label))
    world.add(Entity("jar", "object", "jar", "the sesame jar"))
    world.add(Entity("seeds", "object", "seed_bowl", "sesame seeds"))
    world.add(Entity("rhyme_note", "object", "note", "an old note"))

    kitchen = world.get("kitchen")
    jar = world.get("jar")
    seeds = world.get("seeds")
    mila = world.get("mila")
    jun = world.get("jun")

    kitchen.meters["order"] = 1.0
    jar.meters["present"] = 1.0
    jar.meters["hidden"] = 0.0
    jar.meters["open"] = 0.0
    jar.meters["obstructed"] = 1.0
    seeds.meters["stored"] = 1.0

    mila.location = "kitchen"
    jun.location = "kitchen"
    mila.memes["curiosity"] = 1.2
    mila.memes["joy"] = 1.0
    jun.memes["curiosity"] = 1.0
    mila.memes["focus"] = 1.1

    world.facts.update(
        source_spot=spot.key,
        source_verse=verse.key,
        source_tool=tool.key,
        selected_spot_label=spot.label,
        starting_rhyme=verse.line,
        chosen_tool_label=tool.label,
        opening_image=rng.choice(OPENING_IMAGES),
        turn_image=rng.choice(TURN_IMAGES),
        ending_image=spot.ending_image,
        obstacle=spot.obstacle,
        misread=verse.misread,
        verse_attempts=0,
    )

    return world


def opening_scene(world: StoryWorld) -> None:
    mila = world.get("mila")
    jun = world.get("jun")
    world.record(
        "opening",
        (
            "Mila and Jun tapped the jar three times with a wooden spoon, then sang, "
            f'"{world.facts["starting_rhyme"]}", while the room made room and held the light and song in balance. '
            f"{world.facts['opening_image']} {world.facts['selected_spot_label']} waited like a moonlit stage for a curious play."
        ),
        "mila",
    )
    mila.location = "kitchen"
    jun.location = "kitchen"
    world.record(
        "inventory",
        (
            f"They planned sesame biscuits for the morning market and placed the word"
            " 'sesame' at the top of their checklist, then promised to keep every step"
            " calm and exact."
        ),
        "jun",
    )
    mila.memes["confidence"] += 0.5
    jun.memes["confidence"] += 0.5


def hide_jar(world: StoryWorld) -> None:
    spot = SPOTS[world.params.spot]
    jar = world.get("jar")
    mila = world.get("mila")
    jun = world.get("jun")

    jar.meters["present"] = 0.0
    jar.meters["hidden"] = 1.0
    jar.facts["found_after"] = 0
    mila.location = "kitchen"
    jun.location = "kitchen"
    mila.memes["worry"] += 1.0
    jun.memes["worry"] += 0.8
    mila.memes["focus"] += 0.7

    world.record(
        "missing",
        f"A floor hush and a tiny bump later, the jar slid out from under a cloth and disappeared {spot.hidden_nook}. "
        "The first feeling was a blur and worry in a quick bright gust.",
        "jun",
        target="jar",
    )


def repeat_and_reason(world: StoryWorld) -> None:
    verse = VERSES[world.params.verse]
    mila = world.get("mila")
    jun = world.get("jun")
    jar = world.get("jar")
    spot = SPOTS[world.params.spot]

    for step in range(1, 4):
        if step == 1:
            world.record(
                "recur_1",
                f"Mila sang once: '{verse.line}'. It felt cheerful but unclear, and"
                f" {verse.misread} {world.facts['turn_image']}",
                "mila",
            )
            mila.memes["confusion"] += 0.6
            jun.memes["confusion"] += 0.4
        elif step == 2:
            world.record(
                "recur_2",
                "The line came back a second time, slower. Jun matched the rhythm"
                " with a two-step stamp, and the repeated rhyme stopped sounding like"
                " a joke and became a map in the room.",
                "jun",
            )
            jun.memes["focus"] += 0.9
            mila.memes["focus"] += 0.5
        else:
            world.record(
                "recur_3",
                f"On the third try they chanted together. The words now pointed straight to"
                f" {spot.label}. The obstacle was clear: {spot.obstacle}"
                f" They were also calm, because repetition had made the signal plain.",
                "mila",
            )
            mila.memes["clarity"] += 1.1
            mila.memes["curiosity"] += 0.4
            jun.memes["curiosity"] += 0.5
            jar.facts["found_after"] = 3

    world.facts["verse_attempts"] = 3
    world.facts["found_spot"] = world.params.spot
    mila.location = world.params.spot
    jun.location = world.params.spot


def open_jar(world: StoryWorld) -> None:
    tool = TOOLS[world.params.tool]
    mila = world.get("mila")
    jar = world.get("jar")
    seeds = world.get("seeds")
    spot = SPOTS[world.params.spot]

    jar.location = world.params.spot
    jar.meters["obstructed"] = 0.0
    jar.meters["present"] = 1.0
    jar.meters["hidden"] = 0.0
    jar.meters["open"] = 1.0
    seeds.meters["stored"] = 0.0
    seeds.meters["ready_for_mix"] = 1.0

    mila.memes["confidence"] += 1.2
    mila.memes["joy"] += 1.4
    world.record(
        "release",
        f"{tool.action} {tool.why} The sesame jar came free and opened in one steady breath,"
        f" revealing sesame seeds again where everyone could see them.",
        "mila",
        target="jar",
    )
    world.facts["opened_by"] = tool.key


def ending(world: StoryWorld) -> None:
    mila = world.get("mila")
    jun = world.get("jun")
    seeds = world.get("seeds")

    mila.memes["joy"] += 1.0
    jun.memes["joy"] += 1.0
    mila.memes["curiosity"] += 0.6
    jun.memes["focus"] += 0.5

    world.facts["resolved"] = True
    world.record(
        "ending",
        (
            f"The children ended with a bright final image: {world.facts['ending_image']}. "
            f"Curiosity had repeated, then verified, and the sesame kept its promise"
            " of sweetness."
        ),
        "jun",
        target="seeds",
    )
    seeds.facts["used_for"] = "biscuit dough"


def tell(params: StoryParams) -> StoryWorld:
    world = build_world(params)
    opening_scene(world)
    world.para()
    hide_jar(world)
    world.para()
    repeat_and_reason(world)
    world.para()
    open_jar(world)
    ending(world)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    spot = SPOTS[world.params.spot]
    verse = VERSES[world.params.verse]
    tool = TOOLS[world.params.tool]

    return [
        "Write a child-facing rhyming story that includes the exact repeated line 'sesame'.",
        "The story must include Sesame, repeated at least three times to narrow down the clue.",
        f"The line should point toward {spot.label} and not toward a wrong place.",
        f"Use the helper {tool.label} only after the rhyme indicates the right place.",
        "End with a concrete image showing the sesame jar open and the seeds ready to bake.",
        f"Show the children keep curiosity high through the middle turns: {verse.line}",
    ]


def story_grounded_qa(world: StoryWorld) -> list[QAItem]:
    spot = SPOTS[world.params.spot]
    verse = VERSES[world.params.verse]
    tool = TOOLS[world.params.tool]
    attempts = int(world.facts.get("verse_attempts", 0))
    return [
        QAItem(
            question="Why did Mila and Jun repeat the sesame line three times?",
            answer=(
                f"They repeated it {attempts} times to reduce noise and test what stayed stable."
                f" The first two tries sounded like a rhyme, but the third repetition matched the room and confirmed the true location."
            ),
        ),
        QAItem(
            question="Where did the sesame jar become hidden and why?",
            answer=(
                f"The jar ended hidden {spot.hidden_nook}, which is a physical location tied to {spot.label}. "
                f"That happened because the verse pointed to that spot and the narrative required them to follow the clue carefully."
            ),
        ),
        QAItem(
            question="What made the jar open safely in the end?",
            answer=(
                f"The children used {tool.label}, which is the only tool in this story that solves {spot.lock}. "
                f"They matched that physical tool to the obstacle so the jar could be lifted and opened without damage."
            ),
        ),
        QAItem(
            question="How did the ending prove the situation changed?",
            answer=(
                f"The ending includes this image: {world.facts['ending_image']}, which shows the jar no longer hidden and no longer closed. "
                f"The seed bowl state also changed to ready_for_mix, so the sesame became part of baking, not just words."
            ),
        ),
        QAItem(
            question="How did curiosity show up in the middle of the story?",
            answer=(
                f"Curiosity showed up as focused repetition, careful note-taking, and refusal to guess. "
                f"Mila and Jun kept checking clues against the room, then acted when the repeated verse confirmed the same location."
            ),
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    spot = SPOTS[world.params.spot]
    return [
        QAItem(
            question="Why is repetition useful when children are solving a small mystery?",
            answer=(
                "Repetition lets them filter accidental ideas by checking each attempt against the same line. "
                "The signal that stays consistent after several tries is stronger than a one-time hunch."
            ),
        ),
        QAItem(
            question="Why should a physical helper match the lock type in a world-state model?",
            answer=(
                f"Each lock type in the story ({spot.lock}) needs a compatible action. "
                f"If a different tool is used, the jar state would not transition from obstructed to open in the simulation."
            ),
        ),
        QAItem(
            question="What lesson about curiosity is carried by this story world?",
            answer=(
                "Curiosity is most helpful when it is structured, patient, and evidence-based. "
                "Here, repeated evidence changed beliefs, and action followed only when the evidence was stable."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)

    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(S,P,T) :-
    spot(S), verse(P), tool(T),
    verse_points(P, S),
    tool_solves(T, L),
    spot_lock(S, L).

ok :- chosen(S, P, T), valid(S, P, T).

#show valid/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    rows: list[str] = []
    for key, spot in SPOTS.items():
        rows.append(fact("spot", key))
        rows.append(fact("spot_label", key, spot.label))
        rows.append(fact("spot_lock", key, spot.lock))
    for key, verse in VERSES.items():
        rows.append(fact("verse", key))
        rows.append(fact("verse_points", key, verse.points_to))
    for key, tool in TOOLS.items():
        rows.append(fact("tool", key))
        rows.append(fact("tool_solves", key, tool.solves))

    if params is not None:
        rows.append(fact("chosen", params.spot, params.verse, params.tool))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None, show: str = "") -> str:
    return asp_facts(params) + "\n" + ASP_RULES + "\n" + show


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from asp import atoms, solve

    combos = set()
    for model in solve(asp_program(show=""), models=0):
        for item in atoms(model, "valid"):
            spot, verse, tool = item
            combos.add((str(spot), str(verse), str(tool)))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from asp import atoms, one_model

    facts = atoms(one_model(asp_program(params, "#show ok/0.")), "ok")
    return len(facts) > 0


def verify() -> str:
    python_combos = {(p.spot, p.verse, p.tool) for p in all_params()}
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
        text = sample.story.lower()
        world = sample.world
        if world is None:
            raise StoryError(f"story world missing for params={params}")
        if "sesame" not in text:
            raise StoryError(f"required word missing for params={params}")
        if world.facts.get("verse_attempts", 0) != 3:
            raise StoryError(f"repetition not recorded as 3 for params={params}")
        if len(world.events) < 7:
            raise StoryError(f"story timeline too short for params={params}")
        if world.facts.get("resolved") is not True:
            raise StoryError(f"story not marked resolved for params={params}")
        jar = world.get("jar")
        if jar.meters.get("open", 0.0) < 1.0:
            raise StoryError(f"jar never opened for params={params}")
        if jar.meters.get("present", 0.0) < 1.0:
            raise StoryError(f"jar was never returned for params={params}")
        if "ending_image" not in world.facts:
            raise StoryError(f"ending image not set for params={params}")
        if world.facts["ending_image"] not in text:
            raise StoryError(f"ending image not reflected in rendered story for params={params}")

    return (
        f"OK: ASP and Python agree on {len(python_combos)} sesame-valid stories "
        "and generated stories all resolve to opened, present jars with 3 repeats and full QA."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sesame repetition + curiosity rhyming world")
    parser.add_argument("--spot", choices=sorted(SPOTS))
    parser.add_argument("--verse", choices=sorted(VERSES))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--seed", type=int, default=24)
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
    candidates = [
        p
        for p in all_params()
        if (args.spot is None or p.spot == args.spot)
        and (args.verse is None or p.verse == args.verse)
        and (args.tool is None or p.tool == args.tool)
    ]
    if not candidates:
        raise StoryError(explain_invalid(args.spot, args.verse, args.tool))

    pick = candidates[rng.randrange(len(candidates))]
    return StoryParams(pick.spot, pick.verse, pick.tool, seed=args.seed)


def _trace_lines(world: StoryWorld) -> list[str]:
    jar = world.get("jar")
    mila = world.get("mila")
    jun = world.get("jun")
    seeds = world.get("seeds")
    return [
        "Trace:",
        f"  events={len(world.events)}",
        f"  jar_present={jar.meters['present']} open={jar.meters['open']} hidden={jar.meters['hidden']} obstructed={jar.meters['obstructed']}",
        f"  mila_curiosity={mila.memes['curiosity']} jun_curiosity={jun.memes['curiosity']}",
        f"  seeds_ready={seeds.meters['ready_for_mix']} attempts={world.facts.get('verse_attempts', 0)}",
    ]


def _format_qa(sample: StorySample) -> str:
    lines = ["Prompts:"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("Story-grounded QA:")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("World-knowledge QA:")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print("\n".join(_trace_lines(sample.world)))
    if args.qa:
        print()
        print(_format_qa(sample))


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    if args.n <= 0:
        raise StoryError("--n must be a positive integer")

    filtered = [p for p in all_params() if (args.spot is None or p.spot == args.spot)]
    filtered = [p for p in filtered if (args.verse is None or p.verse == args.verse)]
    if args.tool is not None:
        filtered = [p for p in filtered if p.tool == args.tool]

    if args.verse is not None:
        filtered = [p for p in filtered if p.verse == args.verse]

    if not filtered:
        raise StoryError(explain_invalid(args.spot, args.verse, args.tool))

    rng = random.Random(args.seed)
    out: list[StorySample] = []
    for i in range(args.n):
        base = filtered[i % len(filtered)]
        seed = (args.seed or 0) + i
        out.append(generate(StoryParams(base.spot, base.verse, base.tool, seed=seed)))
    return out


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    all_worlds = all_params()
    out: list[StorySample] = []
    base_seed = args.seed or 24
    for idx, base in enumerate(all_worlds):
        out.append(generate(StoryParams(base.spot, base.verse, base.tool, seed=base_seed + idx)))
    return out


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.show_asp:
            print(asp_program(show="#show valid/3."))
            return 0

        if args.verify:
            print(verify())
            return 0

        if args.asp:
            for triplet in sorted(asp_valid_combos()):
                print("\t".join(triplet))
            return 0

        samples = _sample_all(args) if args.all else _sample_n(args)

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = f"### sample {index + 1}" if len(samples) > 1 else None
            emit(sample, args, header=header)
            if index + 1 < len(samples):
                print("\n---\n")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
