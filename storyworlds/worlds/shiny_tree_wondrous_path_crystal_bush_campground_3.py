#!/usr/bin/env python3
"""
Standalone storyworld for a campground slice-of-life story.

Seed words: shiny tree, wondrous path, crystal bush
Features: Problem Solving, Reconciliation
Setting: campground

Internal source tale:
    Two campers are setting up a morning welcome walk at a campground. The
    shiny tree marks the start, the wondrous path leads to cocoa by the
    crystal bush, and one trail marker goes wrong just before younger campers
    arrive. One child blames the other too quickly because of a misleading
    clue. They inspect the route together, find the real cause, use available
    camp gear to fix the marker, and reconcile before the walk begins.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


SUPPLY_LABELS: dict[str, str] = {
    "dry_cloth": "a dry cloth",
    "spare_twine": "spare twine",
    "wooden_stake": "a wooden stake",
    "rubber_mallet": "a rubber mallet",
    "spring_clip": "a spring clip",
    "step_stool": "a step stool",
}


@dataclass(frozen=True)
class CampgroundProfile:
    key: str
    name: str
    tree_detail: str
    path_detail: str
    bush_detail: str
    meeting_job: str
    cocoa_detail: str
    ending_sound: str
    supplies: tuple[str, ...]


@dataclass(frozen=True)
class CamperPair:
    key: str
    accuser_name: str
    accuser_kind: str
    suspect_name: str
    suspect_kind: str
    shared_habit: str


@dataclass(frozen=True)
class Trouble:
    key: str
    marker_phrase: str
    false_clue: str
    accusation_stub: str
    actual_cause: str
    risk: str
    compatible_repairs: tuple[str, ...]


@dataclass(frozen=True)
class Repair:
    key: str
    gear_phrase: str
    action_phrase: str
    result_phrase: str
    proof_phrase: str
    required_supplies: tuple[str, ...]


@dataclass
class StoryParams:
    campground: str
    pair: str
    trouble: str
    repair: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    role: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.kind in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    campground: CampgroundProfile
    pair: CamperPair
    trouble: Trouble
    repair: Repair
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)

    def add(self, entity: Entity) -> None:
        self.entities[entity.role] = entity

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  campground={self.campground.key}")
        rows.append(f"  pair={self.pair.key}")
        rows.append(f"  trouble={self.trouble.key}")
        rows.append(f"  repair={self.repair.key}")
        for role, entity in self.entities.items():
            rows.append(
                f"  {role}<{entity.kind}> name={entity.name} "
                f"traits={entity.traits} meters={entity.meters} memes={entity.memes}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append("  history=")
        for item in self.history:
            rows.append(f"    - {item}")
        return "\n".join(rows)

    def note(self, event: str, summary: str, **details: str) -> None:
        row = {"event": event, "summary": summary}
        row.update(details)
        self.history.append(row)


CAMPGROUNDS: dict[str, CampgroundProfile] = {
    "fern_hollow": CampgroundProfile(
        key="fern_hollow",
        name="Fern Hollow Campground",
        tree_detail="the shiny tree by the breakfast circle, where the silver bark caught the early light",
        path_detail="the wondrous path, a soft loop of pine needles and painted stones between the tents",
        bush_detail="the crystal bush beside the cocoa bench, its clear pods clicking like beads",
        meeting_job="the morning welcome walk for the younger campers",
        cocoa_detail="a dented cocoa pot warming on the picnic table",
        ending_sound="the clear clink of tin mugs near the cocoa bench",
        supplies=("dry_cloth", "spare_twine"),
    ),
    "creek_bend": CampgroundProfile(
        key="creek_bend",
        name="Creek Bend Campground",
        tree_detail="the shiny tree near the hand pump, still bright with dew",
        path_detail="the wondrous path curving past damp logs and a row of rain boots",
        bush_detail="the crystal bush beside the camp map, sparkling over the gravel",
        meeting_job="the welcome walk that led new campers from breakfast to the craft table",
        cocoa_detail="a red kettle resting on a camp stove",
        ending_sound="the tiny tap of the kettle lid as steam puffed out",
        supplies=("wooden_stake", "rubber_mallet", "spare_twine"),
    ),
    "meadow_ring": CampgroundProfile(
        key="meadow_ring",
        name="Meadow Ring Campground",
        tree_detail="the shiny tree at the edge of the field, where the bark looked polished after sunrise",
        path_detail="the wondrous path threading between clover patches and sleeping tents",
        bush_detail="the crystal bush beside a folding table of paper cups and napkins",
        meeting_job="the short welcome walk that brought sleepy campers to snack time",
        cocoa_detail="a tray of cups waiting under a checked cloth",
        ending_sound="the rustle of napkins and the little pop of the checked cloth in the breeze",
        supplies=("spring_clip", "step_stool"),
    ),
}


PAIRS: dict[str, CamperPair] = {
    "nora_eli": CamperPair(
        key="nora_eli",
        accuser_name="Nora",
        accuser_kind="girl",
        suspect_name="Eli",
        suspect_kind="boy",
        shared_habit="liked making neat little signs for camp jobs",
    ),
    "maya_owen": CamperPair(
        key="maya_owen",
        accuser_name="Maya",
        accuser_kind="girl",
        suspect_name="Owen",
        suspect_kind="boy",
        shared_habit="always compared whose knots looked straighter",
    ),
    "tess_luca": CamperPair(
        key="tess_luca",
        accuser_name="Tess",
        accuser_kind="girl",
        suspect_name="Luca",
        suspect_kind="boy",
        shared_habit="usually finished setup jobs before the bell rang",
    ),
}


TROUBLES: dict[str, Trouble] = {
    "dew_loosened_arrow": Trouble(
        key="dew_loosened_arrow",
        marker_phrase="the wooden arrow tied beside the shiny tree",
        false_clue="{suspect} had carried the ribbon spool back from craft hour the night before",
        accusation_stub="must have left the knot sloppy on purpose",
        actual_cause="the dawn dew had soaked the old knot until it slipped loose by itself",
        risk="the younger campers might wander toward the laundry line instead of following the wondrous path",
        compatible_repairs=("retie_marker",),
    ),
    "tipped_cocoa_sign": Trouble(
        key="tipped_cocoa_sign",
        marker_phrase="the little cocoa sign standing near the crystal bush",
        false_clue="{suspect} had been counting the border pebbles after supper",
        accusation_stub="must have bumped the sign and left it leaning in the grass",
        actual_cause="a squirrel hunting cracker crumbs had nosed the basket over during the night",
        risk="the end of the welcome walk would look muddled, and the smallest campers would not know where to stop",
        compatible_repairs=("reset_marker",),
    ),
    "wind_spun_tag": Trouble(
        key="wind_spun_tag",
        marker_phrase="the paper tag hanging halfway down the wondrous path",
        false_clue="{suspect} had practiced hanging the tags during quiet hour",
        accusation_stub="must have turned the arrow the wrong way and forgotten to fix it",
        actual_cause="an evening gust had spun the tag around the branch until the arrow faced back toward the tents",
        risk="the line of campers could loop in a circle instead of reaching the crystal bush",
        compatible_repairs=("clip_marker_low",),
    ),
}


REPAIRS: dict[str, Repair] = {
    "retie_marker": Repair(
        key="retie_marker",
        gear_phrase="a dry cloth and a coil of spare twine",
        action_phrase=(
            "They dried the ribbon, threaded fresh twine through the arrow, "
            "and tied a careful double knot before testing it twice."
        ),
        result_phrase="The arrow stopped drooping and pointed neatly into the start of the wondrous path.",
        proof_phrase="Even when a little breeze reached the breakfast circle, the knot held still.",
        required_supplies=("dry_cloth", "spare_twine"),
    ),
    "reset_marker": Repair(
        key="reset_marker",
        gear_phrase="a wooden stake, spare twine, and a rubber mallet",
        action_phrase=(
            "They stood the sign up again, tied it to the new stake, "
            "and tapped the stake into the dirt with slow, careful turns."
        ),
        result_phrase="The cocoa sign faced the trail again instead of leaning into the grass.",
        proof_phrase="From the start of the route, the stop by the crystal bush looked clear again.",
        required_supplies=("wooden_stake", "rubber_mallet"),
    ),
    "clip_marker_low": Repair(
        key="clip_marker_low",
        gear_phrase="a spring clip and a step stool",
        action_phrase=(
            "They climbed one step up, moved the tag to a lower branch, "
            "and fastened it where the wind could not spin it around."
        ),
        result_phrase="The tag stayed still and easy to read from the middle of the trail.",
        proof_phrase="From the crystal bush, the arrow still pointed back to the shiny tree without wobbling.",
        required_supplies=("spring_clip", "step_stool"),
    ),
}


def _supply_list(keys: tuple[str, ...]) -> str:
    return ", ".join(SUPPLY_LABELS[key] for key in keys)


def valid_combo(campground_key: str, pair_key: str, trouble_key: str, repair_key: str) -> bool:
    if campground_key not in CAMPGROUNDS:
        return False
    if pair_key not in PAIRS:
        return False
    if trouble_key not in TROUBLES:
        return False
    if repair_key not in REPAIRS:
        return False
    campground = CAMPGROUNDS[campground_key]
    trouble = TROUBLES[trouble_key]
    repair = REPAIRS[repair_key]
    if repair.key not in trouble.compatible_repairs:
        return False
    return all(req in campground.supplies for req in repair.required_supplies)


def invalid_reason(campground_key: str, pair_key: str, trouble_key: str, repair_key: str) -> str:
    if campground_key not in CAMPGROUNDS:
        return f"No story: unknown campground {campground_key!r}."
    if pair_key not in PAIRS:
        return f"No story: unknown camper pair {pair_key!r}."
    if trouble_key not in TROUBLES:
        return f"No story: unknown trouble {trouble_key!r}."
    if repair_key not in REPAIRS:
        return f"No story: unknown repair {repair_key!r}."

    campground = CAMPGROUNDS[campground_key]
    trouble = TROUBLES[trouble_key]
    repair = REPAIRS[repair_key]
    if repair.key not in trouble.compatible_repairs:
        options = ", ".join(trouble.compatible_repairs)
        return (
            f"No story: {repair.key!r} does not solve trouble {trouble.key!r}. "
            f"Try one of: {options}."
        )
    missing = [req for req in repair.required_supplies if req not in campground.supplies]
    if missing:
        readable = ", ".join(SUPPLY_LABELS[m] for m in missing)
        return (
            f"No story: {campground.name} does not have {readable} for repair {repair.key!r}. "
            f"Available supplies are: {_supply_list(campground.supplies)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for campground_key in sorted(CAMPGROUNDS):
        for pair_key in sorted(PAIRS):
            for trouble_key in sorted(TROUBLES):
                for repair_key in sorted(REPAIRS):
                    if valid_combo(campground_key, pair_key, trouble_key, repair_key):
                        combos.append((campground_key, pair_key, trouble_key, repair_key))
    return combos


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str, str],
    index: int = 0,
) -> StoryParams:
    campground_key, pair_key, trouble_key, repair_key = combo
    return StoryParams(
        campground=campground_key,
        pair=pair_key,
        trouble=trouble_key,
        repair=repair_key,
        seed=args.seed + index,
    )


def build_world(params: StoryParams) -> World:
    campground = CAMPGROUNDS[params.campground]
    pair = PAIRS[params.pair]
    trouble = TROUBLES[params.trouble]
    repair = REPAIRS[params.repair]

    world = World(
        params=params,
        campground=campground,
        pair=pair,
        trouble=trouble,
        repair=repair,
    )

    accuser = Entity(
        name=pair.accuser_name,
        kind=pair.accuser_kind,
        role="accuser",
        traits=["helpful", "quick to speak"],
        meters={"energy": 0.9, "hands_free": 1.0},
        memes={"trust": 0.8, "blame": 0.0, "apology": 0.0, "teamwork": 0.4, "relief": 0.0},
    )
    suspect = Entity(
        name=pair.suspect_name,
        kind=pair.suspect_kind,
        role="suspect",
        traits=["steady", "careful"],
        meters={"energy": 0.9, "hands_free": 1.0},
        memes={"trust": 0.8, "hurt": 0.0, "forgiveness": 0.0, "teamwork": 0.4, "relief": 0.0},
    )
    marker = Entity(
        name="trail marker",
        kind="marker",
        role="marker",
        traits=["small", "important"],
        meters={"stability": 0.9, "clarity": 1.0, "readiness": 0.9},
        memes={"welcome": 0.8},
    )
    path = Entity(
        name="wondrous path",
        kind="path",
        role="path",
        traits=["gentle", "camp-made"],
        meters={"clarity": 1.0, "flow": 1.0},
        memes={"comfort": 0.7},
    )
    tree = Entity(
        name="shiny tree",
        kind="tree",
        role="tree",
        traits=["bright", "familiar"],
        meters={"visibility": 1.0},
        memes={"gathering": 1.0},
    )
    bush = Entity(
        name="crystal bush",
        kind="bush",
        role="bush",
        traits=["sparkly", "welcoming"],
        meters={"visibility": 1.0},
        memes={"destination": 1.0},
    )

    for entity in (accuser, suspect, marker, path, tree, bush):
        world.add(entity)

    world.facts["job"] = campground.meeting_job
    world.facts["false_clue"] = trouble.false_clue.format(suspect=suspect.name)
    world.facts["required_supplies"] = _supply_list(repair.required_supplies)
    world.facts["available_supplies"] = _supply_list(campground.supplies)
    world.facts["cocoa_detail"] = campground.cocoa_detail
    world.facts["seed"] = str(params.seed)
    return world


def simulate(world: World) -> None:
    accuser = world.entities["accuser"]
    suspect = world.entities["suspect"]
    marker = world.entities["marker"]
    path = world.entities["path"]
    tree = world.entities["tree"]
    bush = world.entities["bush"]
    trouble = world.trouble
    repair = world.repair

    world.note(
        "premise",
        f"{accuser.name} and {suspect.name} started {world.campground.meeting_job} together.",
        location="campground",
        start=tree.name,
        end=bush.name,
    )

    marker.meters["stability"] = 0.25
    marker.meters["clarity"] = 0.4
    marker.meters["readiness"] = 0.2
    path.meters["clarity"] = 0.45
    path.meters["flow"] = 0.5
    accuser.memes["blame"] = 0.9
    suspect.memes["hurt"] = 0.8
    world.note(
        "misunderstanding",
        f"They found trouble at {trouble.marker_phrase}.",
        clue=world.facts["false_clue"],
        accusation=f"{accuser.name} thought {suspect.name} {trouble.accusation_stub}.",
        risk=trouble.risk,
    )

    accuser.memes["teamwork"] = 0.7
    suspect.memes["teamwork"] = 0.8
    world.note(
        "inspection",
        f"{accuser.name} and {suspect.name} checked the route together instead of arguing longer.",
        cause=trouble.actual_cause,
        supplies=world.facts["required_supplies"],
    )

    marker.meters["stability"] = 1.0
    marker.meters["clarity"] = 1.0
    marker.meters["readiness"] = 1.0
    path.meters["clarity"] = 1.0
    path.meters["flow"] = 1.0
    accuser.memes["relief"] = 0.9
    suspect.memes["relief"] = 0.9
    world.note(
        "repair",
        f"They used {repair.gear_phrase} to fix the problem.",
        action=repair.action_phrase,
        result=repair.result_phrase,
        proof=repair.proof_phrase,
    )

    accuser.memes["apology"] = 1.0
    accuser.memes["trust"] = 1.2
    suspect.memes["forgiveness"] = 1.0
    suspect.memes["trust"] = 1.2
    suspect.memes["hurt"] = 0.1
    world.note(
        "reconciliation",
        f"{accuser.name} apologized, and {suspect.name} accepted.",
        shared_work="They finished the route side by side.",
    )

    world.facts["ending_image"] = (
        f"Soon the first younger campers could start at the shiny tree, follow the wondrous path, "
        f"and smile when they reached the crystal bush beside {world.campground.cocoa_detail}."
    )
    world.facts["ending_sound"] = world.campground.ending_sound


def _render_story(world: World) -> str:
    accuser = world.entities["accuser"]
    suspect = world.entities["suspect"]
    marker = world.entities["marker"]
    path = world.entities["path"]
    trouble = world.trouble
    repair = world.repair
    camp = world.campground

    opening = (
        f"At {camp.name}, {accuser.name} and {suspect.name} were on {camp.meeting_job}. "
        f"The route started at {camp.tree_detail}. From there ran {camp.path_detail}. "
        f"At the far end stood {camp.bush_detail}. "
        f"They both {world.pair.shared_habit}, so the job usually felt easy."
    )

    conflict = (
        f"But that morning, they found trouble at {trouble.marker_phrase}. "
        f"Because {world.facts['false_clue']}, {accuser.name} blurted that {suspect.name} {trouble.accusation_stub}. "
        f"{suspect.name} went quiet right away, and there was no time to waste because {trouble.risk}."
    )

    if marker.meters["stability"] >= 1.0 and path.meters["clarity"] >= 1.0:
        turn = (
            f"Instead of staying upset, they checked the ground, the branch, and the trail together. "
            f"They discovered that {trouble.actual_cause}. "
            f"They used {repair.gear_phrase}. {repair.action_phrase} "
            f"{repair.result_phrase} {repair.proof_phrase}"
        )
    else:
        turn = "They kept studying the route, but the marker still needed a workable fix."

    if accuser.memes["apology"] >= 1.0 and suspect.memes["forgiveness"] >= 1.0:
        ending = (
            f"After the fix held, {accuser.name} admitted the blame came too fast and apologized. "
            f"{suspect.name} accepted because they had solved the problem together instead of leaving it crooked. "
            f"{world.facts['ending_image']} The morning ended with {world.facts['ending_sound']}."
        )
    else:
        ending = world.facts["ending_image"]

    return "\n\n".join([opening, conflict, turn, ending])


def _prompts(world: World) -> list[str]:
    return [
        "Write a slice-of-life campground story using the phrases shiny tree, wondrous path, and crystal bush.",
        "Center the plot on a small practical problem that children can solve with camp supplies.",
        "Include a mistaken blame that ends in a sincere apology and a repaired friendship.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    accuser = world.entities["accuser"]
    suspect = world.entities["suspect"]
    return [
        QAItem(
            "What job were the campers doing at the beginning?",
            f"They were setting up {world.campground.meeting_job} at {world.campground.name}. The route started at the shiny tree and ended by the crystal bush, so the markers had to be clear before the younger campers arrived.",
        ),
        QAItem(
            f"Why did {accuser.name} blame {suspect.name} at first?",
            f"{accuser.name} jumped to a conclusion because {world.facts['false_clue']}. After they inspected the route, they learned that the real cause was different and the blame had been unfair.",
        ),
        QAItem(
            "What was the real problem with the trail marker?",
            f"The real problem was that {world.trouble.actual_cause}. That mattered because {world.trouble.risk}.",
        ),
        QAItem(
            "How did they solve the campground problem?",
            f"They used {world.repair.gear_phrase} and worked side by side. {world.repair.action_phrase} {world.repair.result_phrase}",
        ),
        QAItem(
            "How did the reconciliation happen?",
            f"Once the marker held steady, {accuser.name} admitted the accusation was too quick and apologized. {suspect.name} accepted, because fixing the route together restored trust between them.",
        ),
        QAItem(
            "What image at the end proves the story changed for the better?",
            f"The ending image is a clear route from the shiny tree to the crystal bush for the younger campers. That picture shows the problem is solved and the friendship is warm again at the same time.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why is this repair reasonable in this campground?",
            f"It is reasonable because {world.campground.name} has {world.facts['required_supplies']} on hand. The repair fits the setting instead of inventing tools that are not there.",
        ),
        QAItem(
            "Why does the story use both problem solving and reconciliation?",
            f"The campers have to change the physical state of the route by fixing the marker. They also have to change the social state by correcting the unfair blame and rebuilding trust.",
        ),
        QAItem(
            "What physical state makes the wondrous path ready again?",
            f"The marker needs to stand firmly, point clearly, and stay readable in the morning breeze. Once the arrow is steady and the path is easy to follow, the younger campers can reach the crystal bush without confusion.",
        ),
        QAItem(
            "Why is checking evidence before blaming important in a small campground story?",
            f"A campground is full of ordinary causes like dew, wind, and animals, so a first guess can be wrong. Looking at the route together protects the friendship and leads to a better fix.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.campground, params.pair, params.trouble, params.repair):
        raise StoryError(
            invalid_reason(params.campground, params.pair, params.trouble, params.repair)
        )

    world = build_world(params)
    simulate(world)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
campground_supports(C, R) :-
    campground(C),
    repair(R),
    not missing_supply(C, R).

combo(C, P, T, R) :-
    campground_supports(C, R),
    camper_pair(P),
    trouble(T),
    repair(R),
    solves(T, R).

missing_supply(C, R) :-
    campground(C),
    repair(R),
    needs(R, Supply),
    not has_supply(C, Supply).

ok :- chosen(C, P, T, R), combo(C, P, T, R).

#show combo/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for campground in CAMPGROUNDS.values():
        rows.append(fact("campground", campground.key))
        for supply in campground.supplies:
            rows.append(fact("has_supply", campground.key, supply))
    for pair in PAIRS.values():
        rows.append(fact("camper_pair", pair.key))
    for trouble in TROUBLES.values():
        rows.append(fact("trouble", trouble.key))
        for repair_key in trouble.compatible_repairs:
            rows.append(fact("solves", trouble.key, repair_key))
    for repair in REPAIRS.values():
        rows.append(fact("repair", repair.key))
        for supply in repair.required_supplies:
            rows.append(fact("needs", repair.key, supply))
    if params is not None:
        rows.append(fact("chosen", params.campground, params.pair, params.trouble, params.repair))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program())
    return set(atoms(model, "combo"))


def verify() -> str:
    python_set = set(valid_combos())
    asp_set = asp_valid_combos()
    if python_set != asp_set:
        only_python = sorted(python_set - asp_set)
        only_asp = sorted(asp_set - python_set)
        raise StoryError(
            f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}"
        )

    required_phrases = ("shiny tree", "wondrous path", "crystal bush", "campground")
    for combo in sorted(python_set):
        params = StoryParams(
            campground=combo[0],
            pair=combo[1],
            trouble=combo[2],
            repair=combo[3],
            seed=1,
        )
        sample = generate(params)
        lower_story = sample.story.lower()
        for phrase in required_phrases:
            if phrase not in lower_story:
                raise StoryError(f"Generated story for {combo} is missing phrase {phrase!r}.")
        if "apologized" not in lower_story:
            raise StoryError(f"Generated story for {combo} does not include reconciliation.")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
            raise StoryError(f"Generated story for {combo} has incomplete QA sets.")
    return f"OK: clingo gate matches valid_combos() with {len(python_set)} combos."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate campground problem-solving and reconciliation story samples."
    )
    parser.add_argument("--campground", choices=sorted(CAMPGROUNDS), default=None)
    parser.add_argument("--pair", choices=sorted(PAIRS), default=None)
    parser.add_argument("--trouble", choices=sorted(TROUBLES), default=None)
    parser.add_argument("--repair", choices=sorted(REPAIRS), default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random | None = None,
    index: int = 0,
) -> StoryParams:
    combos = valid_combos()
    filtered = [
        combo for combo in combos
        if (args.campground is None or combo[0] == args.campground)
        and (args.pair is None or combo[1] == args.pair)
        and (args.trouble is None or combo[2] == args.trouble)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if (args.campground or args.pair or args.trouble or args.repair) and not filtered:
        if args.campground and args.trouble and args.repair:
            pair_key = args.pair or sorted(PAIRS)[0]
            raise StoryError(
                invalid_reason(args.campground, pair_key, args.trouble, args.repair)
            )
        raise StoryError("No story: no valid combination matches the selected filters.")
    if not filtered:
        filtered = combos
    pool = list(filtered)
    local_rng = rng or random.Random(args.seed)
    local_rng.shuffle(pool)
    combo = pool[index % len(pool)]
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for combo in sorted(asp_valid_combos()):
        print("\t".join(combo))


def main(argv: Iterable[str] | None = None) -> int:
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
            _emit_asp_listing()
            return 0
        if args.all:
            combos = valid_combos()
            for i, combo in enumerate(combos, 1):
                sample = generate(_params_from_combo(args, combo, i))
                emit(sample, args, f"### {' / '.join(combo)}")
                if i != len(combos) and not args.json:
                    print("\n" + "=" * 72 + "\n")
            return 0

        count = max(1, args.n)
        for i in range(count):
            sample = generate(resolve_params(args, index=i))
            header = f"### variant {i + 1}" if count > 1 and not args.json else None
            emit(sample, args, header)
            if i != count - 1 and not args.json:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
