#!/usr/bin/env python3
"""
storyworlds/worlds/shiny_tree_wondrous_path_crystal_bush_campground_2.py
=========================================================================

A standalone storyworld for a slice-of-life campground story built from:

    Words: shiny tree, wondrous path, crystal bush
    Setting: campground
    Features: Problem Solving, Reconciliation

Internal source tale:
    Two campers are preparing a gentle morning scavenger walk for younger kids.
    The shiny tree is their starting landmark, the wondrous path leads to a
    crystal bush by the creek, and a trail marker has gone wrong overnight.
    One camper blames the other too quickly because of a clue that seems to fit.
    They walk the path together, find the real cause, use the right camp tool to
    fix it, and reconcile before the younger campers arrive.
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

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Campground:
    key: str
    phrase: str
    tree_detail: str
    path_detail: str
    bush_detail: str
    host_place: str
    ending_sound: str
    available_repairs: tuple[str, ...]


@dataclass(frozen=True)
class Pairing:
    key: str
    accuser_name: str
    accuser_kind: str
    friend_name: str
    friend_kind: str
    host_name: str


@dataclass(frozen=True)
class Clue:
    key: str
    phrase: str
    scene_sentence: str
    accusation: str
    looks_like: str


@dataclass(frozen=True)
class Cause:
    key: str
    problem_phrase: str
    discovery: str
    risk: str
    need: str
    why_it_happened: str


@dataclass(frozen=True)
class Repair:
    key: str
    tool_phrase: str
    action: str
    solves: str
    qa_method: str
    ending_image: str


@dataclass
class StoryParams:
    campground: str
    clue: str
    cause: str
    repair: str
    pair: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "woman", "aunt"}:
            table = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.kind in {"boy", "father", "man", "uncle"}:
            table = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]


@dataclass
class Event:
    id: str
    text: str


@dataclass
class World:
    params: StoryParams
    campground: Campground
    pairing: Pairing
    clue: Clue
    cause: Cause
    repair: Repair
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, key: str) -> Entity:
        return self.entities[key]

    def note(self, event_id: str, text: str) -> None:
        self.history.append(Event(event_id, text))

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for name, ent in self.entities.items():
            if name != ent.id:
                continue
            traits = ", ".join(ent.traits) if ent.traits else "none"
            lines.append(
                f"  {name:<14} ({ent.kind:<10}) role={ent.role or '-':<12} "
                f"traits=[{traits}] meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        lines.append(
            "  choices: campground={camp} clue={clue} cause={cause} repair={repair} pair={pair}".format(
                camp=self.params.campground,
                clue=self.params.clue,
                cause=self.params.cause,
                repair=self.params.repair,
                pair=self.params.pair,
            )
        )
        lines.append(f"  facts: {self.facts}")
        lines.append("  history:")
        for event in self.history:
            lines.append(f"    - {event.id}: {event.text}")
        return "\n".join(lines)


CAMPGROUNDS: dict[str, Campground] = {
    "cedar_loop": Campground(
        key="cedar_loop",
        phrase="Cedar Loop Campground",
        tree_detail="its bark held little stripes of sap that flashed like coins in the first light",
        path_detail="small flat stones kept it neat between ferny tents and the creek bend",
        bush_detail="dew made every branch look dipped in clear sugar",
        host_place="the cocoa table by the ranger bench",
        ending_sound="mugs knocked together with a soft clink",
        available_repairs=("retie_marker", "tap_peg"),
    ),
    "creekside_ring": Campground(
        key="creekside_ring",
        phrase="Creekside Ring Campground",
        tree_detail="its branches leaned over the breakfast tables and caught the sun before any tent flap opened",
        path_detail="it curved around puddle-dark roots and pointed straight to the creek rail",
        bush_detail="it shone beside the water barrel with beads of dew on every twig",
        host_place="the pancake griddle beside the picnic shelter",
        ending_sound="spoons tapped against enamel bowls",
        available_repairs=("retie_marker", "wipe_arrow"),
    ),
    "maple_meadow": Campground(
        key="maple_meadow",
        phrase="Maple Meadow Campground",
        tree_detail="its leaves made a bright umbrella over the map board at the center of camp",
        path_detail="it crossed a dry patch of needles and then slipped into cooler shade",
        bush_detail="it stood at the meadow edge where the creek mist liked to rest",
        host_place="the supply stump near the song circle",
        ending_sound="children laughed over breakfast apples",
        available_repairs=("tap_peg", "wipe_arrow"),
    ),
}

PAIRS: dict[str, Pairing] = {
    "lina_omar": Pairing(
        key="lina_omar",
        accuser_name="Lina",
        accuser_kind="girl",
        friend_name="Omar",
        friend_kind="boy",
        host_name="Ranger Pia",
    ),
    "suri_jude": Pairing(
        key="suri_jude",
        accuser_name="Suri",
        accuser_kind="girl",
        friend_name="Jude",
        friend_kind="boy",
        host_name="Counselor Mae",
    ),
    "nia_teo": Pairing(
        key="nia_teo",
        accuser_name="Nia",
        accuser_kind="girl",
        friend_name="Teo",
        friend_kind="boy",
        host_name="Ranger Luis",
    ),
}

CLUES: dict[str, Clue] = {
    "damp_thread": Clue(
        key="damp_thread",
        phrase="a damp blue thread hanging from the trail marker",
        scene_sentence="A damp blue thread hung from the trail marker.",
        accusation="The thread looked like it came from a scarf, so the mistake seemed easy to pin on a camper who had walked ahead the night before.",
        looks_like="dew_loosened_knot",
    ),
    "crumb_patch": Clue(
        key="crumb_patch",
        phrase="cracker crumbs scattered near the marker peg",
        scene_sentence="Cracker crumbs were scattered near the marker peg.",
        accusation="The crumbs made it seem as if someone had snacked there and bumped the marker on the way back to the tents.",
        looks_like="raccoon_tugged_peg",
    ),
    "gray_smudge": Clue(
        key="gray_smudge",
        phrase="a gray smear across the chalk arrow",
        scene_sentence="A gray smear crossed the chalk arrow.",
        accusation="The smear looked like drawing charcoal, so it was tempting to blame the friend who liked to sketch in the morning.",
        looks_like="breakfast_smoke",
    ),
}

CAUSES: dict[str, Cause] = {
    "dew_loosened_knot": Cause(
        key="dew_loosened_knot",
        problem_phrase="the ribbon marker had sagged low across the wondrous path",
        discovery="cool drops had soaked the old knot until it slipped loose by itself",
        risk="little campers could miss the turn and wander past the crystal bush",
        need="retie_marker",
        why_it_happened="The air stayed wet all night, and the old string had already gone thin.",
    ),
    "raccoon_tugged_peg": Cause(
        key="raccoon_tugged_peg",
        problem_phrase="the marker stake leaned sideways and no longer pointed down the wondrous path",
        discovery="tiny paw prints showed that a raccoon had tugged the peg while sniffing for breakfast scraps",
        risk="the welcome walk would start with a crooked sign and confused feet",
        need="tap_peg",
        why_it_happened="The peg sat in soft dirt near the snack crate, and the night visitor loosened it.",
    ),
    "breakfast_smoke": Cause(
        key="breakfast_smoke",
        problem_phrase="the chalk arrow near the crystal bush had gone dull and hard to read",
        discovery="a light ribbon of griddle smoke had smeared soot across the sign face",
        risk="the youngest campers would not know where to stop for the creek story",
        need="wipe_arrow",
        why_it_happened="Breakfast started early, and the smoke drifted toward the sign before anyone noticed.",
    ),
}

REPAIRS: dict[str, Repair] = {
    "retie_marker": Repair(
        key="retie_marker",
        tool_phrase="the spare twine kit",
        action="They looped fresh twine through the ribbon and tied a careful square knot together.",
        solves="dew_loosened_knot",
        qa_method="Fresh twine and a new knot lifted the ribbon back where small campers could see it clearly.",
        ending_image="The ribbon sat high again, and it fluttered above the path like a tiny flag.",
    ),
    "tap_peg": Repair(
        key="tap_peg",
        tool_phrase="the small wooden mallet",
        action="They pressed the stake back into the ground and tapped it until the arrow faced the path again.",
        solves="raccoon_tugged_peg",
        qa_method="The mallet mattered because the peg needed steady force, not guesswork or bare hands.",
        ending_image="The arrow stood straight again, with the morning light resting on its painted edge.",
    ),
    "wipe_arrow": Repair(
        key="wipe_arrow",
        tool_phrase="a damp cloth and a piece of white chalk",
        action="They wiped the sign clean and drew the arrow back in a thick bright line.",
        solves="breakfast_smoke",
        qa_method="The cloth cleared the soot, and the chalk gave the sign a fresh mark that younger campers could read from far away.",
        ending_image="The sign looked bright again, and the white arrow almost glowed beside the crystal bush.",
    ),
}


def _campground_choices() -> list[str]:
    return sorted(CAMPGROUNDS)


def _clue_choices() -> list[str]:
    return sorted(CLUES)


def _cause_choices() -> list[str]:
    return sorted(CAUSES)


def _repair_choices() -> list[str]:
    return sorted(REPAIRS)


def _pair_choices() -> list[str]:
    return sorted(PAIRS)


def valid_combo(campground_key: str, clue_key: str, cause_key: str, repair_key: str) -> bool:
    if campground_key not in CAMPGROUNDS or clue_key not in CLUES or cause_key not in CAUSES or repair_key not in REPAIRS:
        return False
    campground = CAMPGROUNDS[campground_key]
    clue = CLUES[clue_key]
    cause = CAUSES[cause_key]
    repair = REPAIRS[repair_key]
    return (
        clue.looks_like == cause.key
        and repair.solves == cause.key
        and repair.key in campground.available_repairs
        and cause.need == repair.key
    )


def invalid_reason(campground_key: str, clue_key: str, cause_key: str, repair_key: str) -> str:
    if campground_key not in CAMPGROUNDS:
        return f"No story: unknown campground {campground_key!r}."
    if clue_key not in CLUES:
        return f"No story: unknown clue {clue_key!r}."
    if cause_key not in CAUSES:
        return f"No story: unknown cause {cause_key!r}."
    if repair_key not in REPAIRS:
        return f"No story: unknown repair {repair_key!r}."
    campground = CAMPGROUNDS[campground_key]
    clue = CLUES[clue_key]
    cause = CAUSES[cause_key]
    repair = REPAIRS[repair_key]
    if clue.looks_like != cause.key:
        return (
            f"No story: {clue.phrase} does not reasonably point to cause {cause.key!r}. "
            f"It only fits {clue.looks_like!r}."
        )
    if repair.solves != cause.key or cause.need != repair.key:
        return (
            f"No story: repair {repair.key!r} does not solve cause {cause.key!r}. "
            f"That cause needs {cause.need!r}."
        )
    if repair.key not in campground.available_repairs:
        return (
            f"No story: {campground.phrase} does not keep {repair.tool_phrase} at hand. "
            f"Available repairs: {', '.join(campground.available_repairs)}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for campground_key in _campground_choices():
        for clue_key in _clue_choices():
            for cause_key in _cause_choices():
                for repair_key in _repair_choices():
                    if valid_combo(campground_key, clue_key, cause_key, repair_key):
                        combos.append((campground_key, clue_key, cause_key, repair_key))
    return combos


def _choose_pair(args: argparse.Namespace, rng: random.Random) -> str:
    if args.pair:
        return args.pair
    return rng.choice(_pair_choices())


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str, str],
    index: int = 0,
) -> StoryParams:
    rng = random.Random(args.seed + index)
    pair_key = _choose_pair(args, rng)
    return StoryParams(
        campground=combo[0],
        clue=combo[1],
        cause=combo[2],
        repair=combo[3],
        pair=pair_key,
        seed=args.seed + index,
    )


def build_world(params: StoryParams) -> World:
    campground = CAMPGROUNDS[params.campground]
    pairing = PAIRS[params.pair]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    repair = REPAIRS[params.repair]
    world = World(
        params=params,
        campground=campground,
        pairing=pairing,
        clue=clue,
        cause=cause,
        repair=repair,
    )

    accuser = world.add(
        Entity(
            pairing.accuser_name,
            kind=pairing.accuser_kind,
            label=pairing.accuser_name,
            role="accuser",
            traits=["responsible", "quick to worry"],
        )
    )
    friend = world.add(
        Entity(
            pairing.friend_name,
            kind=pairing.friend_kind,
            label=pairing.friend_name,
            role="friend",
            traits=["steady", "helpful", "likes to sketch"],
        )
    )
    host = world.add(
        Entity(
            pairing.host_name,
            kind="adult",
            label=pairing.host_name,
            role="host",
            traits=["calm"],
        )
    )
    tree = world.add(Entity("shiny_tree", kind="landmark", label="shiny tree", role="tree"))
    path = world.add(Entity("wondrous_path", kind="trail", label="wondrous path", role="path"))
    bush = world.add(Entity("crystal_bush", kind="landmark", label="crystal bush", role="bush"))
    marker = world.add(Entity("trail_marker", kind="marker", label="trail marker", role="marker"))

    accuser.memes["trust"] = 1.0
    accuser.memes["care"] = 1.0
    friend.memes["trust"] = 1.0
    friend.memes["care"] = 1.0
    host.memes["calm"] = 1.0
    tree.meters["shine"] = 1.0
    path.meters["open"] = 1.0
    path.meters["ready"] = 0.0
    path.meters["delay"] = 1.0
    bush.meters["sparkle"] = 1.0
    marker.meters["upright"] = 0.0
    marker.meters["clear"] = 0.0
    marker.meters["problem"] = 1.0

    world.facts["problem_solved"] = "0"
    world.facts["reconciled"] = "0"
    world.facts["false_blame"] = "0"
    world.facts["ending_image"] = ""
    world.facts["host_place"] = campground.host_place
    world.note(
        "premise",
        f"{accuser.id} and {friend.id} are preparing the morning welcome walk at {campground.phrase}.",
    )
    return world


def simulate(world: World) -> None:
    accuser = world.get("accuser")
    friend = world.get("friend")
    path = world.get("path")
    marker = world.get("marker")

    accuser.memes["frustration"] = 1.0
    friend.memes["hurt"] = 1.0
    accuser.memes["patience"] = 0.0
    friend.memes["patience"] = 0.0
    world.facts["false_blame"] = "1"
    world.note(
        "misunderstanding",
        f"{accuser.id} sees {world.clue.phrase} and blames {friend.id} before checking the whole path.",
    )

    accuser.memes["patience"] = 1.0
    friend.memes["patience"] = 1.0
    world.note(
        "inspection",
        f"They walk the wondrous path together and discover that {world.cause.discovery}.",
    )

    marker.meters["problem"] = 0.0
    marker.meters["upright"] = 1.0
    marker.meters["clear"] = 1.0
    path.meters["ready"] = 1.0
    path.meters["delay"] = 0.0
    world.facts["problem_solved"] = "1"
    world.note(
        "repair",
        f"They use {world.repair.tool_phrase} to fix the marker because {world.cause.why_it_happened}",
    )

    accuser.memes["guilt"] = 1.0
    accuser.memes["trust"] = 1.6
    friend.memes["trust"] = 1.6
    friend.memes["hurt"] = 0.0
    accuser.memes["frustration"] = 0.0
    world.facts["reconciled"] = "1"
    world.note(
        "reconciliation",
        f"{accuser.id} apologizes, and {friend.id} accepts after the repair is finished.",
    )

    world.get("tree").meters["shine"] = 1.2
    world.get("bush").meters["sparkle"] = 1.2
    world.facts["ending_image"] = world.repair.ending_image
    world.note(
        "ending",
        "The younger campers arrive to follow the repaired route from the shiny tree to the crystal bush.",
    )


def render_story(world: World) -> str:
    camp = world.campground
    pair = world.pairing
    accuser = world.get("accuser")
    friend = world.get("friend")
    host = world.get("host")

    opening = (
        f"At {camp.phrase}, {pair.accuser_name} and {pair.friend_name} had one small morning job before breakfast. "
        f"They were setting up a welcome walk for the younger campers, starting at the shiny tree and ending at the crystal bush by the creek."
    )
    scene = (
        f"The shiny tree stood at the middle of camp, where {camp.tree_detail}. "
        f"From there, the wondrous path bent between tents and benches, and {camp.path_detail}. "
        f"Near the end of that path, the crystal bush waited in the cool air, and {camp.bush_detail}."
    )
    problem = (
        f"When {pair.accuser_name} reached the first turn, {world.cause.problem_phrase}. "
        f"{world.clue.scene_sentence} {world.clue.accusation}"
    )
    tension = (
        f'"{pair.friend_name}, did you do this when you walked back from {camp.host_place}?" '
        f"{pair.accuser_name} asked. {pair.friend_name} looked stung, but stayed beside the path instead of walking away."
    )
    turn = (
        f"The two of them checked the posts from the shiny tree to the crystal bush and finally saw the real trouble: {world.cause.discovery}. "
        f"{world.cause.risk.capitalize()}, so they stopped arguing and thought about what the path actually needed."
    )
    fix = (
        f"{host.id} opened the supply bin, and {pair.accuser_name} and {pair.friend_name} reached for {world.repair.tool_phrase}. "
        f"{world.repair.action} {world.cause.why_it_happened}"
    )
    reconciliation = (
        f'After the marker was steady again, {pair.accuser_name} let out a breath and said, "I was too quick to blame you." '
        f"{pair.friend_name} nodded and accepted the apology. Their faces softened, and the job felt shared again instead of sore."
    )
    ending = (
        f"Soon the younger campers came over from the tents and followed the wondrous path without stopping in confusion. "
        f"{world.repair.ending_image} By the time {camp.ending_sound}, the campground felt easy and whole again."
    )
    return "\n\n".join([opening + " " + scene, problem + " " + tension, turn + " " + fix, reconciliation + " " + ending])


def prompts_for(world: World) -> list[str]:
    return [
        'Write a slice-of-life campground story that uses the phrases "shiny tree", "wondrous path", and "crystal bush".',
        "Center the plot on one small practical problem, a mistaken accusation, and a calm repair.",
        "End with a concrete image that shows the friendship and the campground routine are both back in place.",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    pair = world.pairing
    camp = world.campground
    return [
        QAItem(
            "What problem interrupted the campers' morning job?",
            f"{pair.accuser_name} and {pair.friend_name} found that {world.cause.problem_phrase}. That mattered because {world.cause.risk}.",
        ),
        QAItem(
            f"Why did {pair.accuser_name} blame {pair.friend_name} at first?",
            f"{pair.accuser_name} saw {world.clue.phrase} and thought it pointed to {pair.friend_name}. The clue looked convincing in the moment, even though it only matched the surface of the problem and not the real cause.",
        ),
        QAItem(
            "How did they discover the true cause?",
            f"They walked the wondrous path together instead of staying at the first post and arguing. By checking the whole route, they learned that {world.cause.discovery}.",
        ),
        QAItem(
            "How was the problem solved?",
            f"They used {world.repair.tool_phrase}. {world.repair.qa_method}",
        ),
        QAItem(
            "What showed that the campers reconciled?",
            f"{pair.accuser_name} apologized after the repair, and {pair.friend_name} accepted instead of keeping the hurt alive. The welcome walk was ready on time, so their teamwork returned in a visible way.",
        ),
        QAItem(
            "What ending image proves the campground changed?",
            f"The younger campers could follow the route from the shiny tree to the crystal bush without getting lost. {world.repair.ending_image}",
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    camp = world.campground
    return [
        QAItem(
            "Why is every repair not valid in every campground?",
            f"Each campground keeps different supplies close at hand, so the story only allows repairs that the place can honestly support. At {camp.phrase}, that means using one of: {', '.join(camp.available_repairs)}.",
        ),
        QAItem(
            "Why are the shiny tree, wondrous path, and crystal bush important in this world?",
            "They are more than decorative words because they anchor how children move through camp. The shiny tree marks the beginning, the wondrous path carries the action, and the crystal bush gives the walk a clear stopping place.",
        ),
        QAItem(
            "Why does reconciliation matter to the practical outcome?",
            "The campers do not finish the job well until they stop protecting their pride and start sharing the inspection. In this world, social repair and physical repair are tied together because the route is prepared by people working side by side.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.pair not in PAIRS:
        raise StoryError(f"No story: unknown pair {params.pair!r}.")
    if not valid_combo(params.campground, params.clue, params.cause, params.repair):
        raise StoryError(invalid_reason(params.campground, params.clue, params.cause, params.repair))
    world = build_world(params)
    simulate(world)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


ASP_RULES = r"""
valid(Camp,Clue,Cause,Repair) :-
    campground(Camp),
    clue(Clue),
    cause(Cause),
    repair(Repair),
    clue_matches(Clue,Cause),
    solves(Repair,Cause),
    available(Camp,Repair),
    needs(Cause,Repair).

ok :- chosen(Camp,Clue,Cause,Repair), valid(Camp,Clue,Cause,Repair).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for campground_key, campground in CAMPGROUNDS.items():
        rows.append(fact("campground", campground_key))
        for repair_key in campground.available_repairs:
            rows.append(fact("available", campground_key, repair_key))
    for clue_key, clue in CLUES.items():
        rows.append(fact("clue", clue_key))
        rows.append(fact("clue_matches", clue_key, clue.looks_like))
    for cause_key, cause in CAUSES.items():
        rows.append(fact("cause", cause_key))
        rows.append(fact("needs", cause_key, cause.need))
    for repair_key, repair in REPAIRS.items():
        rows.append(fact("repair", repair_key))
        rows.append(fact("solves", repair_key, repair.solves))
    if params is not None:
        rows.append(fact("chosen", params.campground, params.clue, params.cause, params.repair))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        for combo in atoms(model, "valid"):
            combos.add(tuple(str(part) for part in combo))
    return combos


def asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    python_combos = set(valid_combos())
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    pair_keys = _pair_choices()
    for index, combo in enumerate(sorted(python_combos)):
        params = StoryParams(
            campground=combo[0],
            clue=combo[1],
            cause=combo[2],
            repair=combo[3],
            pair=pair_keys[index % len(pair_keys)],
            seed=index,
        )
        if not asp_accepts(params):
            raise StoryError(f"ASP rejected valid params: {params}")
        sample = generate(params)
        story = sample.story
        if "shiny tree" not in story or "wondrous path" not in story or "crystal bush" not in story:
            raise StoryError(f"Required seed language missing from story for params={params}")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
            raise StoryError(f"QA too thin for params={params}")
        if sample.world.facts["problem_solved"] != "1" or sample.world.facts["reconciled"] != "1":
            raise StoryError(f"World did not complete repair and reconciliation for params={params}")
    return f"OK: Python and ASP agree on {len(python_combos)} valid campground stories, and every sample solves the route problem and reconciles."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campground", choices=_campground_choices())
    parser.add_argument("--clue", choices=_clue_choices())
    parser.add_argument("--cause", choices=_cause_choices())
    parser.add_argument("--repair", choices=_repair_choices())
    parser.add_argument("--pair", choices=_pair_choices())
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    explicit = any(getattr(args, key) is not None for key in ("campground", "clue", "cause", "repair"))
    if explicit:
        filtered = [
            combo
            for combo in combos
            if (args.campground is None or combo[0] == args.campground)
            and (args.clue is None or combo[1] == args.clue)
            and (args.cause is None or combo[2] == args.cause)
            and (args.repair is None or combo[3] == args.repair)
        ]
        if not filtered:
            if all(getattr(args, key) is not None for key in ("campground", "clue", "cause", "repair")):
                raise StoryError(invalid_reason(args.campground, args.clue, args.cause, args.repair))
            raise StoryError("No story: the chosen filters do not overlap in a reasonable campground scenario.")
        combo = rng.choice(filtered)
    else:
        combo = rng.choice(combos)
    pair_key = args.pair or rng.choice(_pair_choices())
    return StoryParams(
        campground=combo[0],
        clue=combo[1],
        cause=combo[2],
        repair=combo[3],
        pair=pair_key,
        seed=args.seed,
    )


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        combos = valid_combos()
        for index, combo in enumerate(combos):
            yield generate(_params_from_combo(args, combo, index))
        return

    explicit = any(getattr(args, key) is not None for key in ("campground", "clue", "cause", "repair"))
    count = max(1, args.n)
    if explicit:
        for index in range(count):
            rng = random.Random(args.seed + index)
            params = resolve_params(args, rng)
            params.seed = args.seed + index
            yield generate(params)
        return

    combos = valid_combos()
    rng = random.Random(args.seed)
    rng.shuffle(combos)
    for index in range(count):
        combo = combos[index % len(combos)]
        yield generate(_params_from_combo(args, combo, index))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if qa:
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


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
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
            header = ""
            if args.all:
                params = sample.params
                header = (
                    f"### campground={params.campground} clue={params.clue} "
                    f"cause={params.cause} repair={params.repair} pair={params.pair}"
                )
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n---\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
