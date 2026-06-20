#!/usr/bin/env python3
"""A meadow splash-pad mystery about a crystal door that opens only after a physical problem is solved.

Internal source tale:
At a meadow-themed splash pad, two children race toward a crystal door that
should open when the water system runs correctly. The door stays shut, which
feels mysterious at first. A repeating clue in the water leads them to the true
mechanical problem. With a patient helper and the right tool, they solve the
problem and watch the crystal door open into a bright final splash.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class MeadowPad:
    key: str
    name: str
    opening: str
    reward: str
    ending_image: str
    sites: tuple[str, ...]


@dataclass(frozen=True)
class Clue:
    key: str
    place: str
    text: str
    hint: str
    false_guess: str


@dataclass(frozen=True)
class Cause:
    key: str
    place: str
    kind: str
    motion: str
    discovery: str
    result: str


@dataclass(frozen=True)
class Solution:
    key: str
    solves: str
    tool: str
    action: str
    proof: str
    lesson: str


@dataclass(frozen=True)
class TeamChoice:
    key: str
    first: str
    first_type: str
    second: str
    second_type: str


@dataclass(frozen=True)
class HelperChoice:
    key: str
    name: str
    type: str
    role: str
    trait: str


@dataclass
class StoryParams:
    meadow: str
    clue: str
    cause: str
    solution: str
    team: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None


@dataclass
class SplashWorld:
    params: StoryParams
    meadow: MeadowPad
    clue: Clue
    cause: Cause
    solution: Solution
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | int | float] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        if entity.role:
            self.entities[entity.role] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

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

    def trace(self) -> str:
        lines = ["TRACE"]
        for event in self.history:
            target = f" -> {event.target}" if event.target else ""
            lines.append(f"- {event.id}: {event.actor}{target}: {event.text}")
        lines.append("ENTITIES")
        seen: set[str] = set()
        for entity in self.entities.values():
            if entity.id in seen:
                continue
            seen.add(entity.id)
            lines.append(f"  {entity.id} | {entity.kind} | {entity.label}")
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            if meters:
                lines.append(f"    meters={meters}")
            if memes:
                lines.append(f"    memes={memes}")
        lines.append("FACTS")
        for key in sorted(self.facts):
            lines.append(f"  {key}={self.facts[key]}")
        return "\n".join(lines)


MEADOWS: dict[str, MeadowPad] = {
    "clover_court": MeadowPad(
        key="clover_court",
        name="Clover Court",
        opening="At Clover Court, the splash pad floor curled into a bright meadow of green tiles, and cool loops of water skipped over the stone like tiny rabbits.",
        reward="a rainbow fan wheel",
        ending_image="green rings of water circled their ankles while the rainbow fan wheel bloomed under the open crystal door",
        sites=("drain", "latch"),
    ),
    "buttercup_basin": MeadowPad(
        key="buttercup_basin",
        name="Buttercup Basin",
        opening="At Buttercup Basin, yellow petal tiles glowed like a sunny meadow, and the splash pad hissed softly as the afternoon light slid across the wet ground.",
        reward="the high buttercup arch",
        ending_image="the buttercup arch sprayed a silver roof above them while the crystal door shone pale blue at its side",
        sites=("hinge", "latch"),
    ),
    "reed_run": MeadowPad(
        key="reed_run",
        name="Reed Run",
        opening="At Reed Run, painted reeds waved along the wall, turning the splash pad into a meadow marsh where thin ribbons of water whispered over the tiles.",
        reward="a tall mist curtain",
        ending_image="the mist curtain floated like silver grass while the crystal door stood open and sparkling in the reeds",
        sites=("drain", "hinge"),
    ),
}

CLUES: dict[str, Clue] = {
    "petal_whorl": Clue(
        key="petal_whorl",
        place="drain",
        text="A thin whorl of meadow petals kept spinning over one drain while the rest of the water ran past.",
        hint="The petals returned to the same spot every cycle, as if the water was pointing down with a tiny green finger.",
        false_guess="At first the children wondered whether someone had pressed the wrong button, but the water kept disagreeing in the same place.",
    ),
    "bubble_thread": Clue(
        key="bubble_thread",
        place="hinge",
        text="A thread of silver bubbles kept clinging to one hinge of the crystal door whenever the sprays restarted.",
        hint="The bubbles lined up beside a tiny sensor eye and never drifted anywhere else.",
        false_guess="For a breath, the children thought the crystal door was acting magical on purpose, yet the bubbles kept tracing a real edge.",
    ),
    "trapped_click": Clue(
        key="trapped_click",
        place="latch",
        text="A small trapped click sounded inside the latch cup each time water filled it and slipped away again.",
        hint="It was not the bright pop of an opening door. It was a caught little click that stopped too soon.",
        false_guess="The shut door looked so neat that the children almost guessed it had been locked for cleaning, but the click kept begging them to look closer.",
    ),
}

CAUSES: dict[str, Cause] = {
    "petal_clog": Cause(
        key="petal_clog",
        place="drain",
        kind="clog",
        motion="A felted mat of wet leaves and petals was muffling the drain, so the water could not pull with enough strength to wake the opening system.",
        discovery="When they knelt beside the drain, they could see flat green scraps sealing the slots like a soggy lid.",
        result="As soon as the slots were clear, the next rush of water pulled strong through the pipe and the crystal door gave a relieved shiver.",
    ),
    "sunscreen_film": Cause(
        key="sunscreen_film",
        place="hinge",
        kind="film",
        motion="A cloudy strip of dried sunscreen foam had glazed the hinge sensor, so the crystal door kept waiting for a clear signal that never came.",
        discovery="Sunlight through the clear panel showed a pale smear sitting right over the little sensor eye by the hinge.",
        result="Once the cloudy film washed away, the sensor blinked blue and the crystal door swung loose.",
    ),
    "pebble_wedge": Cause(
        key="pebble_wedge",
        place="latch",
        kind="wedge",
        motion="A smooth pebble had hopped into the latch cup and wedged the tiny lift before the water cycle could pop it free.",
        discovery="The caught click came from a pebble trapped in the shallow latch cup where the lift needed room to rise.",
        result="With the cup empty again, the latch sprang up and the crystal door opened like a bright secret.",
    ),
}

SOLUTIONS: dict[str, Solution] = {
    "drain_comb": Solution(
        key="drain_comb",
        solves="clog",
        tool="the long drain comb",
        action="{first} braced the grate with both hands while {second} slid {tool} under the leaf mat and lifted it away in one slippery sheet.",
        proof="The spinning petals vanished, and the nearby water hurried downward in one clean pull.",
        lesson="They solved the mystery by following the water instead of guessing at it.",
    ),
    "rinse_cloth": Solution(
        key="rinse_cloth",
        solves="film",
        tool="a rinse bucket and a soft cloth",
        action="{helper} handed them {tool}. {second} poured the clean rinse while {first} wiped the cloudy sensor eye in small careful circles.",
        proof="The silver bubble thread broke apart, and the little eye flashed blue before either child even stood up.",
        lesson="They solved the mystery by cleaning the exact place the clue kept naming.",
    ),
    "foam_hook": Solution(
        key="foam_hook",
        solves="wedge",
        tool="the foam hook",
        action="{first} held the latch cup steady while {second} slipped {tool} under the trapped pebble and teased it out onto the wet tile.",
        proof="The caught click changed into a bright pop, which meant the latch could finally move the way it was built to move.",
        lesson="They solved the mystery by matching the right tool to the tiny stuck part.",
    ),
}

TEAMS: dict[str, TeamChoice] = {
    "mira_noah": TeamChoice("mira_noah", "Mira", "girl", "Noah", "boy"),
    "tavi_jo": TeamChoice("tavi_jo", "Tavi", "girl", "Jo", "boy"),
    "lena_omar": TeamChoice("lena_omar", "Lena", "girl", "Omar", "boy"),
    "noor_eli": TeamChoice("noor_eli", "Noor", "girl", "Eli", "boy"),
}

HELPERS: dict[str, HelperChoice] = {
    "rosa": HelperChoice("rosa", "Rosa", "woman", "splash-pad guide", "patient"),
    "mr_hale": HelperChoice("mr_hale", "Mr. Hale", "man", "grounds helper", "calm"),
    "ivy": HelperChoice("ivy", "Coach Ivy", "woman", "water-play coach", "observant"),
}

PLACE_LABELS = {
    "drain": "the silver drain by the meadow stones",
    "hinge": "the clear hinge beside the crystal door frame",
    "latch": "the shallow latch cup under the crystal door handle",
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for meadow_key, meadow in sorted(MEADOWS.items()):
        for clue_key, clue in sorted(CLUES.items()):
            for cause_key, cause in sorted(CAUSES.items()):
                for solution_key, solution in sorted(SOLUTIONS.items()):
                    if clue.place not in meadow.sites:
                        continue
                    if cause.place != clue.place:
                        continue
                    if solution.solves != cause.kind:
                        continue
                    combos.append((meadow_key, clue_key, cause_key, solution_key))
    return combos


def _unknown_reason(kind: str, value: str, options: Iterable[str]) -> str:
    opts = ", ".join(sorted(options))
    return f"No story: unknown {kind} {value!r}. Try one of: {opts}."


def explain_rejection(meadow_key: str, clue_key: str, cause_key: str, solution_key: str) -> str:
    if meadow_key not in MEADOWS:
        return _unknown_reason("meadow", meadow_key, MEADOWS)
    if clue_key not in CLUES:
        return _unknown_reason("clue", clue_key, CLUES)
    if cause_key not in CAUSES:
        return _unknown_reason("cause", cause_key, CAUSES)
    if solution_key not in SOLUTIONS:
        return _unknown_reason("solution", solution_key, SOLUTIONS)
    meadow = MEADOWS[meadow_key]
    clue = CLUES[clue_key]
    cause = CAUSES[cause_key]
    solution = SOLUTIONS[solution_key]
    if clue.place not in meadow.sites:
        sites = ", ".join(meadow.sites)
        return (
            f"No story: {meadow.name} does not support a {clue.place} mystery. "
            f"That splash pad only exposes these clue sites: {sites}."
        )
    if cause.place != clue.place:
        return (
            f"No story: clue {clue_key!r} points to {clue.place}, but cause {cause_key!r} lives at {cause.place}. "
            "The repeating clue and the real fault must happen at the same place."
        )
    if solution.solves != cause.kind:
        return (
            f"No story: solution {solution_key!r} solves {solution.solves}, but cause {cause_key!r} is a {cause.kind} problem. "
            "Use a fix that matches the physical fault."
        )
    return "No story: invalid splash-pad mystery."


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.team not in TEAMS:
        return False, _unknown_reason("team", params.team, TEAMS)
    if params.helper not in HELPERS:
        return False, _unknown_reason("helper", params.helper, HELPERS)
    reason = explain_rejection(params.meadow, params.clue, params.cause, params.solution)
    if reason == "No story: invalid splash-pad mystery.":
        return True, ""
    return False, reason


def _pick_team(seed: int) -> str:
    rng = random.Random(seed)
    return rng.choice(sorted(TEAMS))


def _pick_helper(seed: int) -> str:
    rng = random.Random(seed * 17 + 3)
    return rng.choice(sorted(HELPERS))


def params_from_combo(combo: tuple[str, str, str, str], seed: int) -> StoryParams:
    return StoryParams(
        meadow=combo[0],
        clue=combo[1],
        cause=combo[2],
        solution=combo[3],
        team=_pick_team(seed),
        helper=_pick_helper(seed),
        seed=seed,
    )


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    combos = valid_combos()
    return [
        combo
        for combo in combos
        if (args.meadow is None or combo[0] == args.meadow)
        and (args.clue is None or combo[1] == args.clue)
        and (args.cause is None or combo[2] == args.cause)
        and (args.solution is None or combo[3] == args.solution)
    ]


def build_world(params: StoryParams) -> SplashWorld:
    meadow = MEADOWS[params.meadow]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    solution = SOLUTIONS[params.solution]
    team_choice = TEAMS[params.team]
    helper_choice = HELPERS[params.helper]

    world = SplashWorld(params=params, meadow=meadow, clue=clue, cause=cause, solution=solution)

    first = world.add(
        Entity("first", "character", team_choice.first_type, team_choice.first, role="first", traits=["curious"])
    )
    second = world.add(
        Entity("second", "character", team_choice.second_type, team_choice.second, role="second", traits=["steady"])
    )
    helper = world.add(
        Entity("helper", "character", helper_choice.type, helper_choice.name, role="helper", traits=[helper_choice.trait])
    )
    team = world.add(
        Entity(
            "team",
            "group",
            "children",
            f"{team_choice.first} and {team_choice.second}",
            role="team",
            traits=["observant", "brave"],
        )
    )
    door = world.add(
        Entity("door", "object", "crystal_door", "the crystal door", role="door", traits=["clear", "shining"])
    )
    water = world.add(Entity("water", "system", "water_line", "the water line", role="water", traits=["pressurized"]))
    site = world.add(
        Entity(cause.place, "mechanism", cause.place, PLACE_LABELS[cause.place], role="site", traits=["hidden"])
    )

    door.meters["open"] = 0.0
    door.meters["stuckness"] = 1.0
    water.meters["flow"] = 0.35
    site.meters["blocked"] = 1.0
    team.memes["curiosity"] = 1.3
    team.memes["worry"] = 0.2
    helper.memes["patience"] = 1.0

    world.facts["meadow_name"] = meadow.name
    world.facts["reward"] = meadow.reward
    world.facts["site"] = cause.place
    world.facts["site_label"] = PLACE_LABELS[cause.place]
    world.facts["problem_kind"] = cause.kind
    world.facts["tool"] = solution.tool
    world.facts["helper_role"] = helper_choice.role
    world.facts["solved"] = False
    world.facts["mystery"] = "why the crystal door stayed shut"
    world.facts["ending_image"] = meadow.ending_image
    return world


def tell(world: SplashWorld) -> SplashWorld:
    first = world.get("first")
    second = world.get("second")
    helper = world.get("helper")
    team = world.get("team")
    door = world.get("door")
    water = world.get("water")
    site = world.get("site")
    meadow = world.meadow
    clue = world.clue
    cause = world.cause
    solution = world.solution
    site_label = str(world.facts["site_label"])
    helper_role = str(world.facts["helper_role"])

    world.record(
        "opening",
        f"{meadow.opening} At the far side stood the crystal door, and behind it waited {meadow.reward}.",
        actor="narrator",
        target="door",
    )
    world.record(
        "goal",
        f"{first.label} and {second.label} hurried across the splash pad because opening the crystal door was the most exciting game there.",
        actor="team",
        target="door",
    )
    team.memes["wonder"] += 0.8
    world.para()

    world.record(
        "problem",
        "But when the next water cycle thumped through the pipes, the crystal door only trembled and stayed shut.",
        actor="door",
    )
    team.memes["worry"] += 0.7
    team.memes["curiosity"] += 0.5
    world.record("false_guess", clue.false_guess, actor="team", target="door")
    world.record("clue_spotted", f"{clue.text} {clue.hint}", actor="team", target=clue.place)
    world.record(
        "helper_arrives",
        f'{helper.label}, the {helper_role}, knelt beside them and said, "A mystery gets smaller when you follow the thing that repeats."',
        actor="helper",
        target=clue.place,
    )
    world.para()

    world.record(
        "inspect",
        f"The children watched the splash cycle one more time and followed the clue back to {site_label}.",
        actor="team",
        target=cause.place,
    )
    world.record("discovery", cause.discovery, actor="team", target=cause.place)
    world.record("diagnosis", cause.motion, actor="team", target=cause.place)
    team.memes["understanding"] += 1.0
    world.para()

    world.record(
        "solve",
        solution.action.format(
            first=first.label,
            second=second.label,
            helper=helper.label,
            tool=solution.tool,
            site_label=site_label,
        ),
        actor="team",
        target=cause.place,
    )
    site.meters["blocked"] = 0.0
    water.meters["flow"] = 1.0
    door.meters["stuckness"] = 0.0
    door.meters["open"] = 1.0
    team.memes["pride"] += 1.2
    team.memes["worry"] = 0.0
    world.record("proof", f"{solution.proof} {cause.result}", actor="door", target="door")
    world.facts["solved"] = True
    world.para()

    world.record(
        "ending",
        f"The crystal door swung open at last, and {meadow.ending_image}. {first.label} laughed at {second.label} because the answer had been hiding in plain water all along. {solution.lesson}",
        actor="team",
        target="door",
    )
    return world


def generation_prompts(world: SplashWorld) -> list[str]:
    first = world.get("first").label
    second = world.get("second").label
    return [
        'Write a child-friendly mystery set at a splash pad that includes the words "meadow" and "crystal door."',
        f"Tell a problem-solving story where {first} and {second} solve a repeating water clue instead of forcing the answer.",
        "End with a concrete image that proves the splash-pad mechanism changed after the right fix.",
    ]


def story_grounded_qa(world: SplashWorld) -> list[QAItem]:
    first = world.get("first").label
    second = world.get("second").label
    clue = world.clue
    cause = world.cause
    solution = world.solution
    meadow = world.meadow
    site_label = str(world.facts["site_label"])
    return [
        QAItem(
            "What was the mystery at the splash pad?",
            f"The mystery was why the crystal door at {meadow.name} stayed shut when the water cycle started. That mattered because the children could only reach {meadow.reward} after the door opened.",
        ),
        QAItem(
            "Which clue showed the children where to look?",
            f"The children trusted the repeating clue: {clue.text.lower()} That clue kept returning to {site_label}, so it narrowed the mystery to one physical spot instead of the whole splash pad.",
        ),
        QAItem(
            "What was really wrong with the crystal door system?",
            f"The real problem was {cause.motion.lower()} The children confirmed it when they inspected the spot closely and found that {cause.discovery.lower()}",
        ),
        QAItem(
            "How did the children solve the problem?",
            f"They used {solution.tool} at exactly the place the clue named. {solution.proof} That proved the fix matched the hidden fault instead of just making a noisy guess.",
        ),
        QAItem(
            "What changed at the end of the story?",
            f"By the end, the crystal door opened and the children reached the hidden splash feature behind it. The ending image changes because {meadow.ending_image}, which could only happen after the mechanism started working again.",
        ),
        QAItem(
            "Why did the helper matter?",
            f"The helper did not solve the mystery by magic. Instead, {world.get('helper').label} taught the children to watch what repeated, which turned their worry into a useful investigation.",
        ),
    ]


def world_knowledge_qa(world: SplashWorld) -> list[QAItem]:
    return [
        QAItem(
            "Why must the clue place and cause place match in this world?",
            "A repeating clue is only fair if it points toward the real fault. If the clue happened at one place and the cause lived somewhere else, the mystery would stop being grounded in the splash-pad system.",
        ),
        QAItem(
            "Why can only one kind of solution fix each problem?",
            "Each solution is tied to a physical fault such as a clog, a film, or a wedge. The world stays reasonable by requiring a tool and action that actually fit the material problem instead of pretending any helpful motion can fix everything.",
        ),
        QAItem(
            "Why is the crystal door not treated like pure magic?",
            "The crystal door looks mysterious, but it still depends on drains, sensors, latches, and water flow. That keeps the story in a child-scale mystery mode where careful observation reveals a real mechanism.",
        ),
        QAItem(
            "How does the meadow setting affect the mystery?",
            "Each meadow-themed splash pad exposes only certain clue sites, such as a drain, hinge, or latch cup. The setting matters because the children can only solve problems that the physical layout actually allows them to inspect.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(M,C,A,S) :-
    meadow(M),
    clue(C),
    cause(A),
    solution(S),
    clue_place(C, P),
    cause_place(A, P),
    meadow_site(M, P),
    cause_kind(A, K),
    solution_solves(S, K).

ok :- chosen(M, C, A, S), valid(M, C, A, S).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    lines: list[str] = []
    for meadow_key, meadow in sorted(MEADOWS.items()):
        lines.append(fact("meadow", meadow_key))
        for site in meadow.sites:
            lines.append(fact("meadow_site", meadow_key, site))
    for clue_key, clue in sorted(CLUES.items()):
        lines.append(fact("clue", clue_key))
        lines.append(fact("clue_place", clue_key, clue.place))
    for cause_key, cause in sorted(CAUSES.items()):
        lines.append(fact("cause", cause_key))
        lines.append(fact("cause_place", cause_key, cause.place))
        lines.append(fact("cause_kind", cause_key, cause.kind))
    for solution_key, solution in sorted(SOLUTIONS.items()):
        lines.append(fact("solution", solution_key))
        lines.append(fact("solution_solves", solution_key, solution.solves))
    if params is not None:
        lines.append(fact("chosen", params.meadow, params.clue, params.cause, params.solution))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds.asp import atoms, one_model

    return sorted(atoms(one_model(asp_program()), "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    for needle in ("meadow", "crystal door", "splash pad"):
        if needle not in story_lower:
            raise AssertionError(f"story is missing {needle!r}")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    if "meters=" in sample.story or "memes=" in sample.story:
        raise AssertionError("story leaked debug language")
    if world.get("door").meters.get("open", 0) < 1:
        raise AssertionError("crystal door never opened")
    if world.get("door").meters.get("stuckness", 1) != 0:
        raise AssertionError("crystal door stayed stuck")
    if world.get("site").meters.get("blocked", 1) != 0:
        raise AssertionError("problem site stayed blocked")
    if world.get("water").meters.get("flow", 0) < 1:
        raise AssertionError("water flow never recovered")
    if world.get("team").memes.get("pride", 0) < 1:
        raise AssertionError("children never reached a solved ending state")
    if not world.facts.get("solved"):
        raise AssertionError("story never marked itself solved")
    event_ids = {event.id for event in world.history}
    for required in ("clue_spotted", "discovery", "solve", "ending"):
        if required not in event_ids:
            raise AssertionError(f"missing event {required!r}")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 12:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = sorted(valid_combos())
    lp = asp_valid_combos()
    if py != lp:
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        print("MISMATCH between Python and ASP gates:", file=sys.stderr)
        if only_py:
            print(f"  only in Python: {only_py}", file=sys.stderr)
        if only_lp:
            print(f"  only in ASP: {only_lp}", file=sys.stderr)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid meadow splash-pad mysteries).")
    for index, combo in enumerate(py):
        verify_sample(generate(params_from_combo(combo, 1000 + index)))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a meadow splash-pad mystery about a crystal door and problem solving."
    )
    parser.add_argument("--meadow", choices=sorted(MEADOWS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--cause", choices=sorted(CAUSES))
    parser.add_argument("--solution", choices=sorted(SOLUTIONS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None, index: int = 0) -> StoryParams:
    seed = (args.seed if args.seed is not None else 1) + index
    combos = matching_combos(args)
    if not combos:
        meadow = args.meadow or next(iter(MEADOWS))
        clue = args.clue or next(iter(CLUES))
        cause = args.cause or next(iter(CAUSES))
        solution = args.solution or next(iter(SOLUTIONS))
        raise StoryError(explain_rejection(meadow, clue, cause, solution))

    explicit = all(getattr(args, field) is not None for field in ("meadow", "clue", "cause", "solution"))
    if explicit:
        params = params_from_combo((args.meadow, args.clue, args.cause, args.solution), seed)
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    chooser = rng or random.Random(seed)
    return params_from_combo(chooser.choice(combos), seed)


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_combos(args)
        if not combos:
            meadow = args.meadow or next(iter(MEADOWS))
            clue = args.clue or next(iter(CLUES))
            cause = args.cause or next(iter(CAUSES))
            solution = args.solution or next(iter(SOLUTIONS))
            raise StoryError(explain_rejection(meadow, clue, cause, solution))
        return [generate(params_from_combo(combo, args.seed + index)) for index, combo in enumerate(combos)]

    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = args.seed + index
        samples.append(generate(resolve_params(args, random.Random(seed), index)))
    return samples


def format_qa(sample: StorySample) -> str:
    lines = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid meadow crystal door splash-pad mysteries:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:15}" for part in combo))
        return 0

    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for index, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== meadow_crystal_door_splash_pad_problem_solving_3 #{index} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
