#!/usr/bin/env python3
"""
Standalone StoryWorld for the seed:

    Words: fuzzy field, rusty cabin, whispering cloud
    Setting: campground
    Features: Surprise, Humor
    Style: Heartwarming

Internal source tale:
    Two campers are getting a cocoa welcome ready at a campground. Beside the
    fuzzy field stands a rusty cabin, and over its roof drifts a whispering
    cloud. Wind slips through one loose cabin part and makes the cloud seem to
    talk. While the children search the fuzzy field for the missing piece, a
    silly fluff mishap makes them laugh and turns fear into teamwork. They fix
    the cabin, and the repair triggers a small happy surprise just in time for
    the evening cocoa.
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


REQUIRED_TOKENS = ("fuzzy field", "rusty cabin", "whispering cloud", "campground")


SUPPLY_LABELS: dict[str, str] = {
    "camp_twine": "camp twine",
    "stripe_ribbon": "a striped ribbon",
    "tool_tin": "the tiny tool tin",
    "spare_pin": "a spare brass pin",
    "step_stool": "a step stool",
    "pocket_hook": "a pocket hook",
}


@dataclass(frozen=True)
class CampgroundProfile:
    key: str
    name: str
    field_detail: str
    cabin_detail: str
    cloud_detail: str
    evening_job: str
    snack: str
    ending_sound: str
    supplies: tuple[str, ...]


@dataclass(frozen=True)
class CamperPair:
    key: str
    lead_name: str
    lead_kind: str
    friend_name: str
    friend_kind: str
    shared_habit: str
    comic_line: str
    teamwork_line: str


@dataclass(frozen=True)
class WhisperProblem:
    key: str
    loose_part: str
    missing_piece: str
    whisper_line: str
    field_clue: str
    cause: str
    risk: str
    surprise_item: str
    surprise_effect: str
    ending_image: str
    need: str


@dataclass(frozen=True)
class RepairPlan:
    key: str
    need: str
    gear_phrase: str
    action_phrase: str
    proof_phrase: str
    result_phrase: str
    requires: tuple[str, ...]


@dataclass
class StoryParams:
    campground: str
    pair: str
    problem: str
    repair: str
    seed: int = 1


@dataclass
class Entity:
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.kind in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Rule:
    name: str
    apply: callable


@dataclass
class World:
    params: StoryParams
    campground: CampgroundProfile
    pair: CamperPair
    problem: WhisperProblem
    repair: RepairPlan
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    whisper_started: bool = False
    piece_found: bool = False
    repair_done: bool = False
    surprise_revealed: bool = False

    def add(self, entity: Entity) -> None:
        self.entities[entity.role] = entity

    def note(self, event: str, summary: str, **details: str) -> None:
        row = {"event": event, "summary": summary}
        row.update(details)
        self.history.append(row)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  campground={self.campground.key}")
        rows.append(f"  pair={self.pair.key}")
        rows.append(f"  problem={self.problem.key}")
        rows.append(f"  repair={self.repair.key}")
        for role, entity in self.entities.items():
            rows.append(
                f"  {role}<{entity.kind}> name={entity.name} "
                f"meters={entity.meters} memes={entity.memes} tags={entity.tags}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append(
            "  flags="
            f"whisper_started={self.whisper_started}, "
            f"piece_found={self.piece_found}, "
            f"repair_done={self.repair_done}, "
            f"surprise_revealed={self.surprise_revealed}"
        )
        rows.append("  history=")
        for item in self.history:
            rows.append(f"    - {item}")
        return "\n".join(rows)


CAMPGROUNDS: dict[str, CampgroundProfile] = {
    "fern_lantern": CampgroundProfile(
        key="fern_lantern",
        name="Fern Lantern Campground",
        field_detail="a fuzzy field that looked as soft as chick fluff under the lantern light",
        cabin_detail="a rusty cabin with a porch shelf for mugs and napkins",
        cloud_detail="a whispering cloud stretched like a silver scarf above the roof",
        evening_job="the cocoa welcome for the smallest campers",
        snack="cinnamon cocoa",
        ending_sound="the small plink of tin mugs touching on the porch shelf",
        supplies=("camp_twine", "stripe_ribbon", "step_stool", "pocket_hook"),
    ),
    "pine_kettle": CampgroundProfile(
        key="pine_kettle",
        name="Pine Kettle Campground",
        field_detail="a fuzzy field where clover heads shook against the tent ropes",
        cabin_detail="a rusty cabin beside the supper circle and the stacked wood crate",
        cloud_detail="a whispering cloud that drifted low enough to blur the moon",
        evening_job="the welcome bell and cocoa tray before story time",
        snack="maple cocoa",
        ending_sound="the bright dink of the welcome bell over the picnic benches",
        supplies=("tool_tin", "spare_pin", "camp_twine"),
    ),
    "meadow_cinder": CampgroundProfile(
        key="meadow_cinder",
        name="Meadow Cinder Campground",
        field_detail="a fuzzy field that sent seed fluff scooting around every boot",
        cabin_detail="a rusty cabin with a little smoke ledge and a row of drying socks",
        cloud_detail="a whispering cloud curled like a sleepy cat over the chimney",
        evening_job="the after-supper cocoa line for homesick campers",
        snack="honey cocoa",
        ending_sound="the neat tap of spoons inside enamel cups",
        supplies=("tool_tin", "spare_pin", "step_stool", "pocket_hook"),
    ),
}


PAIRS: dict[str, CamperPair] = {
    "nia_joel": CamperPair(
        key="nia_joel",
        lead_name="Nia",
        lead_kind="girl",
        friend_name="Joel",
        friend_kind="boy",
        shared_habit="liked making every camp job look extra tidy",
        comic_line="A puff of field fluff stuck under Joel's nose like a grandpa mustache, and he bowed so seriously that Nia snorted.",
        teamwork_line="They always worked best once they stopped trying to look brave and simply helped each other.",
    ),
    "ruby_finn": CamperPair(
        key="ruby_finn",
        lead_name="Ruby",
        lead_kind="girl",
        friend_name="Finn",
        friend_kind="boy",
        shared_habit="raced to see who could finish a campground chore with fewer dropped things",
        comic_line="Finn sneezed three times into the fuzz and then claimed the field had tried to knit him a beard.",
        teamwork_line="They were the sort of friends who laughed first and untangled worries second.",
    ),
    "tess_omar": CamperPair(
        key="tess_omar",
        lead_name="Tess",
        lead_kind="girl",
        friend_name="Omar",
        friend_kind="boy",
        shared_habit="quietly checked each other's knots before any big camp event",
        comic_line="A soft puff landed on Omar's eyebrows, and Tess said he looked like a surprised owl in pajamas.",
        teamwork_line="Once they traded one honest grin, the problem always seemed smaller.",
    ),
}


PROBLEMS: dict[str, WhisperProblem] = {
    "porch_bell_hook": WhisperProblem(
        key="porch_bell_hook",
        loose_part="porch bell hook",
        missing_piece="crooked brass hook",
        whisper_line="Find my ring",
        field_clue="half buried in the fuzzy field near the mug crate",
        cause="Wind was dragging the bell string across the loose hook, so the breathy scrape sounded almost like words.",
        risk="Without the hook, the welcome bell would hang crooked and the littlest campers might miss the cocoa call.",
        surprise_item="a tiny painted acorn charm",
        surprise_effect="When the hook settled into place, a tiny painted acorn charm popped from behind the bell board and rang once inside the bucket of spoons.",
        ending_image="the bell swaying in one calm line over the porch shelf",
        need="hook",
    ),
    "shutter_latch": WhisperProblem(
        key="shutter_latch",
        loose_part="left shutter latch",
        missing_piece="star latch",
        whisper_line="Hold my grin",
        field_clue="caught in the fuzzy field beside the kindling basket",
        cause="Wind kept teasing the half-open shutter, and the gap hissed until the cabin seemed to be whispering through its teeth.",
        risk="Without the latch, the snack shelf window would keep clattering and make the cocoa corner feel spooky instead of welcoming.",
        surprise_item="a folded moon sticker",
        surprise_effect="As soon as the shutter clicked shut, a folded moon sticker slipped from the sill and fluttered onto the cocoa napkins like a silly little prize.",
        ending_image="the shutter resting still with a straight, sleepy smile",
        need="latch",
    ),
    "chimney_pin": WhisperProblem(
        key="chimney_pin",
        loose_part="chimney cap pin",
        missing_piece="round brass pin",
        whisper_line="Mind my hat",
        field_clue="glinting in the fuzzy field where the clover met the fire ring stones",
        cause="Each breeze nudged the chimney cap sideways, and the thin gap turned the moving air into a wheezy little voice.",
        risk="Without the pin, the supper smoke would puff crookedly and make the cabin seem worried while campers lined up for cocoa.",
        surprise_item="a tiny tin star",
        surprise_effect="When the cap sat straight again, a tiny tin star that had been tucked under the rim dropped onto the step stool with a bright ping.",
        ending_image="the chimney cap sitting proper above one soft ribbon of smoke",
        need="pin",
    ),
}


REPAIRS: dict[str, RepairPlan] = {
    "ribbon_hook": RepairPlan(
        key="ribbon_hook",
        need="hook",
        gear_phrase="a step stool and a pocket hook",
        action_phrase="They climbed carefully, slipped the hook back through the bell board, and steadied it with two patient turns.",
        proof_phrase="The next breeze only made the bell give one cheerful tap instead of a worried scrape.",
        result_phrase="The welcome bell hung straight again where even sleepy campers could see it.",
        requires=("step_stool", "pocket_hook"),
    ),
    "twine_latch": RepairPlan(
        key="twine_latch",
        need="latch",
        gear_phrase="camp twine and a striped ribbon",
        action_phrase="They looped the star latch back into place, tied the twine snug, and finished with the ribbon so the knot would not slip.",
        proof_phrase="When the wind returned, the shutter stayed quiet and the napkins on the sill hardly trembled.",
        result_phrase="The cocoa window looked cozy again instead of fussy and rattly.",
        requires=("camp_twine", "stripe_ribbon"),
    ),
    "tool_pin": RepairPlan(
        key="tool_pin",
        need="pin",
        gear_phrase="the tiny tool tin and a spare brass pin",
        action_phrase="They lifted the cap, lined up the holes, and eased the brass pin through until the metal sat straight.",
        proof_phrase="The next puff of air slid past with only a soft chimney sigh.",
        result_phrase="The smoke could rise in one tidy ribbon again.",
        requires=("tool_tin", "spare_pin"),
    ),
}


def _supports(campground: CampgroundProfile, repair: RepairPlan) -> bool:
    return set(repair.requires).issubset(set(campground.supplies))


def valid_combo(campground: str, problem: str, repair: str) -> bool:
    if campground not in CAMPGROUNDS or problem not in PROBLEMS or repair not in REPAIRS:
        return False
    camp = CAMPGROUNDS[campground]
    prob = PROBLEMS[problem]
    rep = REPAIRS[repair]
    return prob.need == rep.need and _supports(camp, rep)


def invalid_reason(campground: str, problem: str, repair: str) -> str:
    if campground not in CAMPGROUNDS:
        return f"No story: unknown campground {campground!r}."
    if problem not in PROBLEMS:
        return f"No story: unknown whisper problem {problem!r}."
    if repair not in REPAIRS:
        return f"No story: unknown repair plan {repair!r}."
    prob = PROBLEMS[problem]
    rep = REPAIRS[repair]
    camp = CAMPGROUNDS[campground]
    if prob.need != rep.need:
        return (
            f"No story: {rep.key} fixes a {rep.need}, but {prob.loose_part} needs a {prob.need}."
        )
    if not _supports(camp, rep):
        needed = ", ".join(SUPPLY_LABELS[item] for item in rep.requires)
        return (
            f"No story: {camp.name} cannot support {rep.key}. "
            f"It would need {needed}."
        )
    return "No story: that campground setup is not reasonable."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for campground in sorted(CAMPGROUNDS):
        for problem in sorted(PROBLEMS):
            for repair in sorted(REPAIRS):
                if valid_combo(campground, problem, repair):
                    combos.append((campground, problem, repair))
    return combos


def _r_set_premise(world: World) -> bool:
    lead = world.entities["lead"]
    friend = world.entities["friend"]
    field_ent = world.entities["field"]
    cabin = world.entities["cabin"]
    cloud = world.entities["cloud"]
    camp = world.entities["camp"]
    lead.add_meter("steps", 6.0)
    lead.add_meme("care", 0.8)
    friend.add_meter("steps", 5.0)
    friend.add_meme("playfulness", 0.6)
    field_ent.add_meter("fluff_depth", 0.9)
    field_ent.add_meme("softness", 0.8)
    cabin.add_meter("rust_level", 0.8)
    cabin.add_meter("loose_level", 1.0)
    cabin.add_meme("history", 0.7)
    cloud.add_meter("breeze", 0.9)
    cloud.add_meme("mystery", 0.8)
    camp.add_meme("welcome", 1.0)
    world.facts["job"] = world.campground.evening_job
    world.note(
        "premise",
        f"{world.pair.lead_name} and {world.pair.friend_name} were preparing {world.campground.evening_job}.",
        place=world.campground.name,
        habit=world.pair.shared_habit,
    )
    return True


def _r_whisper_begins(world: World) -> bool:
    lead = world.entities["lead"]
    friend = world.entities["friend"]
    cabin = world.entities["cabin"]
    cloud = world.entities["cloud"]
    if cabin.meters.get("loose_level", 0.0) < 1.0 or cloud.meters.get("breeze", 0.0) < 0.5:
        return False
    lead.add_meme("surprise", 0.9)
    lead.add_meme("worry", 0.7)
    friend.add_meme("surprise", 0.7)
    world.whisper_started = True
    world.facts["whisper_line"] = world.problem.whisper_line
    world.facts["risk"] = world.problem.risk
    world.note(
        "whisper",
        f"The {world.problem.loose_part} made the words '{world.problem.whisper_line}' under the whispering cloud.",
        cause=world.problem.cause,
        risk=world.problem.risk,
    )
    return True


def _r_fuzzy_laugh(world: World) -> bool:
    if not world.whisper_started:
        return False
    lead = world.entities["lead"]
    friend = world.entities["friend"]
    field_ent = world.entities["field"]
    field_ent.add_meter("searched", 1.0)
    lead.add_meme("worry", -0.3)
    lead.add_meme("humor", 0.8)
    friend.add_meme("humor", 0.9)
    friend.add_meme("courage", 0.5)
    world.facts["comic_turn"] = world.pair.comic_line
    world.note(
        "humor",
        "The fuzzy field turned the scary moment into a joke.",
        detail=world.pair.comic_line,
    )
    return True


def _r_find_piece(world: World) -> bool:
    if world.entities["field"].meters.get("searched", 0.0) < 1.0:
        return False
    lead = world.entities["lead"]
    friend = world.entities["friend"]
    part = world.entities["piece"]
    lead.add_meme("curiosity", 0.8)
    lead.add_meme("worry", -0.2)
    friend.add_meme("helpfulness", 0.8)
    part.tags["status"] = "found"
    part.tags["location"] = world.problem.field_clue
    part.add_meter("shine", 0.7)
    world.piece_found = True
    world.facts["reveal"] = world.problem.cause
    world.note(
        "discovery",
        f"They found the {world.problem.missing_piece} {world.problem.field_clue}.",
        reveal=world.problem.cause,
    )
    return True


def _r_make_repair(world: World) -> bool:
    if not world.piece_found:
        return False
    lead = world.entities["lead"]
    friend = world.entities["friend"]
    cabin = world.entities["cabin"]
    piece = world.entities["piece"]
    camp = world.entities["camp"]
    lead.add_meme("confidence", 0.9)
    friend.add_meme("trust", 0.8)
    cabin.meters["loose_level"] = 0.0
    cabin.add_meter("steady", 1.0)
    cabin.add_meme("relief", 1.0)
    piece.tags["status"] = "installed"
    camp.add_meme("coziness", 1.0)
    world.repair_done = True
    world.facts["repair_result"] = world.repair.result_phrase
    world.note(
        "repair",
        f"They used {world.repair.gear_phrase} to fix the {world.problem.loose_part}.",
        action=world.repair.action_phrase,
        proof=world.repair.proof_phrase,
    )
    return True


def _r_surprise_ending(world: World) -> bool:
    if not world.repair_done:
        return False
    lead = world.entities["lead"]
    friend = world.entities["friend"]
    cabin = world.entities["cabin"]
    cloud = world.entities["cloud"]
    lead.add_meme("joy", 1.0)
    friend.add_meme("joy", 1.0)
    cloud.add_meme("gentleness", 0.9)
    cabin.add_meme("welcome", 0.9)
    world.surprise_revealed = True
    world.facts["surprise"] = world.problem.surprise_effect
    world.note(
        "surprise",
        f"The repair revealed {world.problem.surprise_item}.",
        effect=world.problem.surprise_effect,
        ending_image=world.problem.ending_image,
    )
    return True


RULES = [
    Rule("set_premise", _r_set_premise),
    Rule("whisper_begins", _r_whisper_begins),
    Rule("fuzzy_laugh", _r_fuzzy_laugh),
    Rule("find_piece", _r_find_piece),
    Rule("make_repair", _r_make_repair),
    Rule("surprise_ending", _r_surprise_ending),
]


def build_world(params: StoryParams) -> World:
    if params.pair not in PAIRS:
        raise StoryError(f"No story: unknown camper pair {params.pair!r}.")
    if not valid_combo(params.campground, params.problem, params.repair):
        raise StoryError(invalid_reason(params.campground, params.problem, params.repair))
    campground = CAMPGROUNDS[params.campground]
    pair = PAIRS[params.pair]
    problem = PROBLEMS[params.problem]
    repair = REPAIRS[params.repair]
    world = World(params=params, campground=campground, pair=pair, problem=problem, repair=repair)
    world.add(
        Entity(
            name=pair.lead_name,
            kind=pair.lead_kind,
            role="lead",
            meters={"reach_cm": 128.0},
            memes={"kindness": 0.8},
            tags={"job": "lead camper"},
        )
    )
    world.add(
        Entity(
            name=pair.friend_name,
            kind=pair.friend_kind,
            role="friend",
            meters={"reach_cm": 126.0},
            memes={"loyalty": 0.8},
            tags={"job": "friend camper"},
        )
    )
    world.add(
        Entity(
            name="field",
            kind="place",
            role="field",
            meters={"width_m": 15.0},
            memes={"welcome": 0.6},
            tags={"texture": "fuzzy"},
        )
    )
    world.add(
        Entity(
            name="cabin",
            kind="building",
            role="cabin",
            meters={"boards": 14.0},
            memes={"age": 0.9},
            tags={"look": "rusty"},
        )
    )
    world.add(
        Entity(
            name="cloud",
            kind="weather",
            role="cloud",
            meters={"span_m": 20.0},
            memes={"hush": 0.8},
            tags={"voice": "whispering"},
        )
    )
    world.add(
        Entity(
            name=problem.missing_piece,
            kind="part",
            role="piece",
            meters={"size_cm": 7.0},
            memes={"importance": 0.7},
            tags={"status": "lost"},
        )
    )
    world.add(
        Entity(
            name=campground.name,
            kind="campground",
            role="camp",
            meters={"lanterns": 4.0},
            memes={"community": 0.9},
            tags={"setting": "campground"},
        )
    )
    for rule in RULES:
        if rule.apply(world):
            world.fired_rules.append(rule.name)
    return world


def _render_story(world: World) -> str:
    lead = world.entities["lead"]
    friend = world.entities["friend"]
    job = world.facts["job"]
    whisper_line = world.facts["whisper_line"]
    reveal = world.facts["reveal"]
    surprise = world.facts["surprise"]

    opening = (
        f"At {world.campground.name}, {lead.name} and {friend.name} were getting ready for {job}. "
        f"Beside them spread {world.campground.field_detail}, and just beyond it stood {world.campground.cabin_detail}. "
        f"Over the roof floated {world.campground.cloud_detail}, so the whole campground felt quiet and expectant."
    )

    tension = (
        f"Then the wind brushed the {world.problem.loose_part}, and the sound under the whispering cloud seemed to say, "
        f'"{whisper_line}." {lead.name} stopped with a mug in {lead.pronoun("possessive")} hand, because for one surprised second it felt as if the sky were talking to the rusty cabin. '
        f"{world.problem.risk}"
    )

    turn = (
        f"{friend.name} hurried into the fuzzy field first. The two friends {world.pair.shared_habit}, even during little campground chores. "
        f"{world.pair.comic_line} "
        f"The laugh loosened the fear in both children. Soon they spotted the {world.problem.missing_piece} "
        f"{world.problem.field_clue}. {reveal} {world.pair.teamwork_line}"
    )

    repair = (
        f"Using {world.repair.gear_phrase}, they worked beside the rusty cabin until the fix felt right. "
        f"{world.repair.action_phrase} {world.repair.result_phrase} {world.repair.proof_phrase}"
    )

    ending = (
        f"{surprise} {lead.name} and {friend.name} stared, then laughed again because the campground had been hiding one last tiny joke for them. "
        f"Soon the campers heard {world.campground.ending_sound}, smelled {world.campground.snack}, and saw {world.problem.ending_image}. "
        f"The whispering cloud drifted on, gentle now, as if it were pleased that the children had listened with brave and funny hearts."
    )

    return "\n\n".join([opening, tension, turn, repair, ending])


def _prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming campground story for children that includes the phrases "fuzzy field", "rusty cabin", and "whispering cloud".',
        f"Tell a funny surprise story where {world.pair.lead_name} and {world.pair.friend_name} solve a whispered mystery before cocoa time.",
        f"Write a cozy tale set at {world.campground.name}, where a child thinks the sky is speaking but discovers a small physical problem instead.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    lead = world.pair.lead_name
    friend = world.pair.friend_name
    return [
        QAItem(
            "What first made the children think something strange was happening?",
            f"They heard the {world.problem.loose_part} seem to say '{world.problem.whisper_line}' under the whispering cloud. The sound was surprising because it made the sky and the rusty cabin seem alive for a moment.",
        ),
        QAItem(
            "Why did they search the fuzzy field?",
            f"They needed to find the missing {world.problem.missing_piece} so they could fix the {world.problem.loose_part}. The cocoa area could not feel settled again until the right piece was back in place.",
        ),
        QAItem(
            "What funny thing happened during the search?",
            f"{world.pair.comic_line} That silly moment broke the tension, so the children could think clearly instead of staying scared.",
        ),
        QAItem(
            "What was the real cause of the whispering sound?",
            f"{world.problem.cause} The whisper was not magic at all; it was a physical problem that only sounded mysterious in the wind.",
        ),
        QAItem(
            "How did the children solve the problem?",
            f"They used {world.repair.gear_phrase} to repair the {world.problem.loose_part}. {world.repair.action_phrase}",
        ),
        QAItem(
            "What surprise came after the repair?",
            f"The repair revealed {world.problem.surprise_item}. {world.problem.surprise_effect}",
        ),
        QAItem(
            "How was the campground different at the end?",
            f"At first the cocoa area felt worried and interrupted by the whispering sound. By the end, the children could see {world.problem.ending_image}, and the campground felt warm, funny, and ready to welcome everyone.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why can a loose cabin part sound like a whisper?",
            f"Wind can turn a gap, scrape, or wobble into a thin voice-like sound. In this world, the loose {world.problem.loose_part} shaped the moving air until it seemed to say words.",
        ),
        QAItem(
            "Why might a small metal piece be hard to spot in a fuzzy field?",
            "Seed fluff, clover, and soft grass can hide small objects very quickly. A shiny piece may only show itself when someone looks slowly from close by.",
        ),
        QAItem(
            "Why does laughing sometimes help children solve a problem?",
            "A kind laugh can lower panic and make the body feel safer again. Once people are less tense, they usually notice clues and work together more carefully.",
        ),
        QAItem(
            "Why does fixing one small camp object matter to a whole campground?",
            f"Shared camp places depend on little parts working the way they should. Repairing the {world.problem.loose_part} helped the welcome area feel safe and clear for every camper who came for cocoa.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.campground not in CAMPGROUNDS:
        raise StoryError(f"No story: unknown campground {params.campground!r}.")
    if params.pair not in PAIRS:
        raise StoryError(f"No story: unknown camper pair {params.pair!r}.")
    if params.problem not in PROBLEMS:
        raise StoryError(f"No story: unknown whisper problem {params.problem!r}.")
    if params.repair not in REPAIRS:
        raise StoryError(f"No story: unknown repair plan {params.repair!r}.")
    if not valid_combo(params.campground, params.problem, params.repair):
        raise StoryError(invalid_reason(params.campground, params.problem, params.repair))
    world = build_world(params)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = """
supports(C,R) :-
    campground(C),
    repair(R),
    not missing_supply(C,R).

missing_supply(C,R) :-
    campground(C),
    repair(R),
    requires(R,S),
    not has_supply(C,S).

combo(C,P,R) :-
    campground(C),
    problem(P),
    repair(R),
    needs(P,N),
    fixes(R,N),
    supports(C,R).

ok :-
    chosen(C,P,R),
    combo(C,P,R).

#show combo/3.
#show ok/0.
"""


def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for campground, profile in CAMPGROUNDS.items():
        rows.append(fact("campground", campground))
        for supply in profile.supplies:
            rows.append(fact("has_supply", campground, supply))
    for pair in PAIRS:
        rows.append(fact("pair", pair))
    for problem, item in PROBLEMS.items():
        rows.append(fact("problem", problem))
        rows.append(fact("needs", problem, item.need))
    for repair, plan in REPAIRS.items():
        rows.append(fact("repair", repair))
        rows.append(fact("fixes", repair, plan.need))
        for supply in plan.requires:
            rows.append(fact("requires", repair, supply))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.campground, params.problem, params.repair) + "\n"
    return asp_facts() + chosen + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    py = set(valid_combos())
    asp = asp_valid_combos()
    if py != asp:
        only_py = sorted(py - asp)
        only_asp = sorted(asp - py)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_asp}")

    pairs = sorted(PAIRS)
    for index, combo in enumerate(sorted(py), 1):
        params = StoryParams(
            campground=combo[0],
            pair=pairs[(index - 1) % len(pairs)],
            problem=combo[1],
            repair=combo[2],
            seed=4000 + index,
        )
        if not asp_verify(params):
            raise StoryError(f"ASP verify failed for combo {combo}.")
        sample = generate(params)
        lowered = sample.story.lower()
        missing = [token for token in REQUIRED_TOKENS if token not in lowered]
        if missing:
            raise StoryError(f"Generated story for {combo} missed required seed terms: {missing}")
        if len(sample.prompts) < 3 or len(sample.story_qa) < 6 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated story for {combo} has incomplete prompt or QA coverage.")
        if sample.story.count("\n\n") < 4:
            raise StoryError(f"Generated story for {combo} did not form a full five-part tale.")
        if sample.world is None or not sample.world.repair_done or not sample.world.surprise_revealed:
            raise StoryError(f"Generated story for {combo} did not complete the repair/surprise arc.")
        multi_sentence = sum(answer.answer.count(".") >= 2 for answer in sample.story_qa)
        if multi_sentence < 5:
            raise StoryError(f"Generated story for {combo} regressed to shallow QA.")
    return f"OK: clingo gate matches valid_combos() ({len(py)} combos) and all generated stories pass seed, arc, and QA checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate fuzzy field / rusty cabin / whispering cloud StoryWorld samples."
    )
    parser.add_argument("--campground", choices=sorted(CAMPGROUNDS))
    parser.add_argument("--pair", choices=sorted(PAIRS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--repair", choices=sorted(REPAIRS))
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


def _params_from_combo(
    combo: tuple[str, str, str],
    args: argparse.Namespace,
    rng: random.Random,
    *,
    seed: int,
) -> StoryParams:
    pair = args.pair or rng.choice(sorted(PAIRS))
    return StoryParams(
        campground=combo[0],
        pair=pair,
        problem=combo[1],
        repair=combo[2],
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    del rng
    seed = args.seed + index
    local_rng = random.Random(seed)
    combos = valid_combos()

    filtered = combos
    if args.campground:
        filtered = [combo for combo in filtered if combo[0] == args.campground]
    if args.problem:
        filtered = [combo for combo in filtered if combo[1] == args.problem]
    if args.repair:
        filtered = [combo for combo in filtered if combo[2] == args.repair]

    if args.campground and args.problem and args.repair and not valid_combo(
        args.campground, args.problem, args.repair
    ):
        raise StoryError(invalid_reason(args.campground, args.problem, args.repair))
    if not filtered:
        camp = args.campground or "<any campground>"
        prob = args.problem or "<any problem>"
        rep = args.repair or "<any repair>"
        raise StoryError(
            f"No story: no valid combo matches campground={camp}, problem={prob}, repair={rep}."
        )
    combo = local_rng.choice(filtered)
    return _params_from_combo(combo, args, local_rng, seed=seed)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Generation prompts -- asks that would produce this story ==")
    for index, prompt in enumerate(sample.prompts, 1):
        print(f"{index}. {prompt}")
    print("\n== (2) Story questions -- answerable from the story ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    as_json: bool = False,
    header: str = "",
) -> None:
    if as_json:
        print(sample.to_json())
        return
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for campground, problem, repair in sorted(asp_valid_combos()):
        print(f"{campground}\t{problem}\t{repair}")


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
            for index, combo in enumerate(combos, 1):
                sample = generate(
                    _params_from_combo(
                        combo,
                        args,
                        random.Random(args.seed + index),
                        seed=args.seed + index,
                    )
                )
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    as_json=args.json,
                    header="" if args.json else f"### {combo[0]} / {combo[1]} / {combo[2]}",
                )
                if index != len(combos) and not args.json:
                    print("\n" + "=" * 70 + "\n")
            return 0

        count = max(1, args.n)
        rng = random.Random(args.seed)
        for index in range(count):
            sample = generate(resolve_params(args, rng, index))
            emit(
                sample,
                trace=args.trace,
                qa=args.qa,
                as_json=args.json,
                header="" if args.json or count == 1 else f"### variant {index + 1}",
            )
            if index != count - 1 and not args.json:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
