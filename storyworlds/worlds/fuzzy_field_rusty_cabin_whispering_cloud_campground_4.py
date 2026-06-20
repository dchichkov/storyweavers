#!/usr/bin/env python3
"""
Standalone StoryWorld for the seed:

    Words: fuzzy field, rusty cabin, whispering cloud
    Setting: campground
    Features: Surprise, Humor
    Style: Heartwarming

Internal source tale:
    Two campers are decorating a campground welcome corner beside a fuzzy field
    and a rusty cabin. A whispering cloud slides over the roof while wind slips
    through one loose cabin part, making a voice-like sound that startles them.
    They search the fuzzy field for the missing piece, a silly fluff mishap
    turns the scare into laughter, and then they repair the cabin together.
    The fix reveals a tiny hidden prize, so the campground ends warmer and more
    cheerful than it began.
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
    "step_stool": "a step stool",
    "pocket_mallet": "a tiny pocket mallet",
    "camp_twine": "camp twine",
    "sunny_ribbon": "a sunny yellow ribbon",
    "tool_tin": "the camp tool tin",
    "spare_pin": "a spare brass pin",
}


@dataclass(frozen=True)
class CampgroundProfile:
    key: str
    name: str
    field_detail: str
    cabin_detail: str
    cloud_detail: str
    evening_job: str
    treat: str
    closing_sound: str
    supplies: tuple[str, ...]


@dataclass(frozen=True)
class CamperTeam:
    key: str
    lead_name: str
    lead_kind: str
    pal_name: str
    pal_kind: str
    shared_habit: str
    joke_line: str
    comfort_line: str


@dataclass(frozen=True)
class WhisperTrouble:
    key: str
    loose_part: str
    missing_piece: str
    whisper_words: str
    clue_place: str
    cause: str
    risk: str
    surprise_item: str
    surprise_effect: str
    ending_image: str
    need: str


@dataclass(frozen=True)
class FixPlan:
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
    team: str
    trouble: str
    fix: str
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
    team: CamperTeam
    trouble: WhisperTrouble
    fix: FixPlan
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    whisper_heard: bool = False
    clue_found: bool = False
    repair_complete: bool = False
    surprise_shown: bool = False

    def add(self, entity: Entity) -> None:
        self.entities[entity.role] = entity

    def note(self, event: str, summary: str, **details: str) -> None:
        row = {"event": event, "summary": summary}
        row.update(details)
        self.history.append(row)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  campground={self.campground.key}")
        rows.append(f"  team={self.team.key}")
        rows.append(f"  trouble={self.trouble.key}")
        rows.append(f"  fix={self.fix.key}")
        for role, entity in self.entities.items():
            rows.append(
                f"  {role}<{entity.kind}> name={entity.name} "
                f"meters={entity.meters} memes={entity.memes} tags={entity.tags}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append(
            "  flags="
            f"whisper_heard={self.whisper_heard}, "
            f"clue_found={self.clue_found}, "
            f"repair_complete={self.repair_complete}, "
            f"surprise_shown={self.surprise_shown}"
        )
        rows.append("  history=")
        for item in self.history:
            rows.append(f"    - {item}")
        return "\n".join(rows)


CAMPGROUNDS: dict[str, CampgroundProfile] = {
    "blueberry_loop": CampgroundProfile(
        key="blueberry_loop",
        name="Blueberry Loop Campground",
        field_detail="a fuzzy field where seed fluff rolled around the tent pegs like tiny sheep",
        cabin_detail="a rusty cabin with a porch table waiting for cups and napkins",
        cloud_detail="a whispering cloud that hung over the roof like a pale scarf",
        evening_job="the welcome corner for new campers",
        treat="warm berry cocoa",
        closing_sound="the soft ding of enamel cups touching",
        supplies=("step_stool", "pocket_mallet", "camp_twine", "sunny_ribbon"),
    ),
    "lantern_hollow": CampgroundProfile(
        key="lantern_hollow",
        name="Lantern Hollow Campground",
        field_detail="a fuzzy field that brushed every ankle with clover and floating white fuzz",
        cabin_detail="a rusty cabin near the camp sign and the firewood stack",
        cloud_detail="a whispering cloud that drifted low enough to blur the first stars",
        evening_job="the supper bell corner before story circle",
        treat="maple cocoa",
        closing_sound="the bright plink of the supper spoon in a mug",
        supplies=("camp_twine", "sunny_ribbon", "tool_tin", "spare_pin"),
    ),
    "mossy_pines": CampgroundProfile(
        key="mossy_pines",
        name="Mossy Pines Campground",
        field_detail="a fuzzy field where every breeze sent soft seeds scooting past the boots",
        cabin_detail="a rusty cabin with a narrow step and a lantern shelf by the door",
        cloud_detail="a whispering cloud curled above the chimney like a sleepy gray ribbon",
        evening_job="the lantern-and-cocoa welcome after sunset",
        treat="honey cocoa",
        closing_sound="the tiny tap of lantern glass settling on its hook",
        supplies=("step_stool", "pocket_mallet", "tool_tin", "spare_pin"),
    ),
}


TEAMS: dict[str, CamperTeam] = {
    "lena_milo": CamperTeam(
        key="lena_milo",
        lead_name="Lena",
        lead_kind="girl",
        pal_name="Milo",
        pal_kind="boy",
        shared_habit="liked making even simple camp chores look extra special",
        joke_line="A puff of fluff landed under Milo's nose like a proud old mustache, and he bowed to the cabin as if it were a queen.",
        comfort_line="Once they laughed together, the strange sound felt like a puzzle instead of a threat.",
    ),
    "ivy_noah": CamperTeam(
        key="ivy_noah",
        lead_name="Ivy",
        lead_kind="girl",
        pal_name="Noah",
        pal_kind="boy",
        shared_habit="always checked each other's work before calling a job finished",
        joke_line="Noah sneezed into the fuzz, then announced that the field was trying to knit him a beard before supper.",
        comfort_line="Their best ideas always arrived right after one honest giggle and one kind glance.",
    ),
    "tess_benji": CamperTeam(
        key="tess_benji",
        lead_name="Tess",
        lead_kind="girl",
        pal_name="Benji",
        pal_kind="boy",
        shared_habit="turned cleanup into a quiet game of who could notice the smallest detail",
        joke_line="A seed puff stuck to Benji's eyebrow, and Tess told him he looked like a surprised owl in a blanket.",
        comfort_line="Sharing the worry made it lighter, and sharing the laugh made them brave again.",
    ),
}


TROUBLES: dict[str, WhisperTrouble] = {
    "chime_peg": WhisperTrouble(
        key="chime_peg",
        loose_part="wind-chime peg",
        missing_piece="round wooden peg",
        whisper_words="Hush my song",
        clue_place="resting in the fuzzy field under the porch bunting",
        cause="Wind kept rubbing the loose chime cup against the rusty cabin wall, so the scratchy little note sounded almost like words.",
        risk="Without the peg, the welcome corner would start with a lonely clack instead of a cheerful song.",
        surprise_item="a paper moon badge",
        surprise_effect="When the peg slid home, a paper moon badge slipped from inside the chime cup and landed softly on the porch rail.",
        ending_image="the chime rocking in one neat line beside the door",
        need="peg",
    ),
    "window_clasp": WhisperTrouble(
        key="window_clasp",
        loose_part="window flap clasp",
        missing_piece="curly tin clasp",
        whisper_words="Close my grin",
        clue_place="caught in the fuzzy field near the pancake table leg",
        cause="The loose window flap kept grinning open and shut, and the wind hissed through the gap until the cabin seemed to whisper.",
        risk="Without the clasp, the cocoa napkins and little welcome cards would keep fluttering away from the rusty cabin porch.",
        surprise_item="a cinnamon sticker star",
        surprise_effect="As soon as the flap clicked shut, a cinnamon sticker star fluttered from the sill and stuck to a sweater sleeve like a prize.",
        ending_image="the porch window resting still with a tidy, sleepy smile",
        need="clasp",
    ),
    "lantern_pin": WhisperTrouble(
        key="lantern_pin",
        loose_part="lantern hook pin",
        missing_piece="brass hook pin",
        whisper_words="Lift my light",
        clue_place="glinting in the fuzzy field beside the ring of campfire stones",
        cause="Each gust tipped the lantern hook sideways, and the thin metal rub made a whispery sound that curled up into the cloud.",
        risk="Without the pin, the lantern-and-cocoa welcome would begin in a dim wobble instead of a cozy glow.",
        surprise_item="a tiny painted acorn charm",
        surprise_effect="When the pin locked in place, a tiny painted acorn charm dropped from the hook and bounced once on the cabin step.",
        ending_image="the lantern hanging straight and golden beside the rusty cabin",
        need="pin",
    ),
}


FIXES: dict[str, FixPlan] = {
    "stool_peg": FixPlan(
        key="stool_peg",
        need="peg",
        gear_phrase="a step stool and a tiny pocket mallet",
        action_phrase="They climbed carefully, lined up the chime cup, and tapped the peg in with slow, patient hands.",
        proof_phrase="The next breeze made one sweet clink instead of a scratchy whisper.",
        result_phrase="The wind chime could greet the campground kindly again.",
        requires=("step_stool", "pocket_mallet"),
    ),
    "twine_clasp": FixPlan(
        key="twine_clasp",
        need="clasp",
        gear_phrase="camp twine and a sunny yellow ribbon",
        action_phrase="They looped the clasp back into place, tied the twine snug, and finished with the ribbon so the flap would stay put.",
        proof_phrase="When the wind returned, the window only gave a soft sigh and stayed still.",
        result_phrase="The welcome cards and cocoa napkins were safe on the porch again.",
        requires=("camp_twine", "sunny_ribbon"),
    ),
    "tin_pin": FixPlan(
        key="tin_pin",
        need="pin",
        gear_phrase="the camp tool tin and a spare brass pin",
        action_phrase="They lifted the hook, matched the little holes, and eased the brass pin through until the lantern sat straight.",
        proof_phrase="The next puff of air passed by with only a calm chimney hush.",
        result_phrase="The lantern could shine steadily for the evening welcome.",
        requires=("tool_tin", "spare_pin"),
    ),
}


def _supports(campground: CampgroundProfile, fix: FixPlan) -> bool:
    return set(fix.requires).issubset(set(campground.supplies))


def valid_combo(campground: str, trouble: str, fix: str) -> bool:
    if campground not in CAMPGROUNDS or trouble not in TROUBLES or fix not in FIXES:
        return False
    camp = CAMPGROUNDS[campground]
    issue = TROUBLES[trouble]
    plan = FIXES[fix]
    return issue.need == plan.need and _supports(camp, plan)


def invalid_reason(campground: str, trouble: str, fix: str) -> str:
    if campground not in CAMPGROUNDS:
        return f"No story: unknown campground {campground!r}."
    if trouble not in TROUBLES:
        return f"No story: unknown whisper trouble {trouble!r}."
    if fix not in FIXES:
        return f"No story: unknown fix plan {fix!r}."
    camp = CAMPGROUNDS[campground]
    issue = TROUBLES[trouble]
    plan = FIXES[fix]
    if issue.need != plan.need:
        return (
            f"No story: {plan.key} repairs a {plan.need}, but {issue.loose_part} needs a {issue.need}."
        )
    if not _supports(camp, plan):
        needed = ", ".join(SUPPLY_LABELS[item] for item in plan.requires)
        return f"No story: {camp.name} cannot support {plan.key}. It would need {needed}."
    return "No story: that campground setup is not reasonable."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for campground in sorted(CAMPGROUNDS):
        for trouble in sorted(TROUBLES):
            for fix in sorted(FIXES):
                if valid_combo(campground, trouble, fix):
                    combos.append((campground, trouble, fix))
    return combos


def _r_set_scene(world: World) -> bool:
    lead = world.entities["lead"]
    pal = world.entities["pal"]
    field_ent = world.entities["field"]
    cabin = world.entities["cabin"]
    cloud = world.entities["cloud"]
    camp = world.entities["camp"]
    lead.add_meter("steps_m", 18.0)
    lead.add_meme("care", 0.8)
    pal.add_meter("steps_m", 17.0)
    pal.add_meme("friendship", 0.8)
    field_ent.add_meter("width_m", 14.0)
    field_ent.add_meme("softness", 0.9)
    cabin.add_meter("rust_level", 0.8)
    cabin.add_meter("loose_level", 1.0)
    cabin.add_meme("history", 0.7)
    cloud.add_meter("breeze_level", 0.9)
    cloud.add_meme("mystery", 0.8)
    camp.add_meter("lantern_count", 4.0)
    camp.add_meme("welcome", 1.0)
    world.facts["job"] = world.campground.evening_job
    world.note(
        "premise",
        f"{world.team.lead_name} and {world.team.pal_name} were preparing {world.campground.evening_job}.",
        place=world.campground.name,
        habit=world.team.shared_habit,
    )
    return True


def _r_hear_whisper(world: World) -> bool:
    cabin = world.entities["cabin"]
    cloud = world.entities["cloud"]
    if cabin.meters.get("loose_level", 0.0) < 1.0 or cloud.meters.get("breeze_level", 0.0) < 0.5:
        return False
    lead = world.entities["lead"]
    pal = world.entities["pal"]
    lead.add_meme("surprise", 0.9)
    lead.add_meme("worry", 0.7)
    pal.add_meme("surprise", 0.8)
    pal.add_meme("worry", 0.5)
    world.whisper_heard = True
    world.facts["whisper_words"] = world.trouble.whisper_words
    world.facts["cause"] = world.trouble.cause
    world.facts["risk"] = world.trouble.risk
    world.note(
        "whisper",
        f"The {world.trouble.loose_part} seemed to say '{world.trouble.whisper_words}' under the whispering cloud.",
        cause=world.trouble.cause,
        risk=world.trouble.risk,
    )
    return True


def _r_laugh_in_field(world: World) -> bool:
    if not world.whisper_heard:
        return False
    lead = world.entities["lead"]
    pal = world.entities["pal"]
    field_ent = world.entities["field"]
    field_ent.add_meter("searched_m", 6.0)
    lead.add_meme("worry", -0.3)
    lead.add_meme("humor", 0.8)
    pal.add_meme("humor", 0.9)
    pal.add_meme("courage", 0.6)
    world.facts["joke_line"] = world.team.joke_line
    world.note(
        "humor",
        "The fuzzy field turned the scare into a laugh.",
        detail=world.team.joke_line,
    )
    return True


def _r_find_piece(world: World) -> bool:
    if world.entities["field"].meters.get("searched_m", 0.0) < 1.0:
        return False
    lead = world.entities["lead"]
    pal = world.entities["pal"]
    piece = world.entities["piece"]
    piece.tags["status"] = "found"
    piece.tags["location"] = world.trouble.clue_place
    piece.add_meter("shine", 0.7)
    lead.add_meme("curiosity", 0.8)
    pal.add_meme("helpfulness", 0.8)
    world.clue_found = True
    world.facts["clue_place"] = world.trouble.clue_place
    world.note(
        "discovery",
        f"They found the {world.trouble.missing_piece} {world.trouble.clue_place}.",
        reveal=world.trouble.cause,
    )
    return True


def _r_finish_repair(world: World) -> bool:
    if not world.clue_found:
        return False
    lead = world.entities["lead"]
    pal = world.entities["pal"]
    cabin = world.entities["cabin"]
    piece = world.entities["piece"]
    camp = world.entities["camp"]
    lead.add_meme("confidence", 0.9)
    pal.add_meme("trust", 0.9)
    cabin.meters["loose_level"] = 0.0
    cabin.add_meter("steady_level", 1.0)
    cabin.add_meme("relief", 1.0)
    camp.add_meme("coziness", 1.0)
    piece.tags["status"] = "installed"
    world.repair_complete = True
    world.facts["repair_result"] = world.fix.result_phrase
    world.note(
        "repair",
        f"They used {world.fix.gear_phrase} to fix the {world.trouble.loose_part}.",
        action=world.fix.action_phrase,
        proof=world.fix.proof_phrase,
    )
    return True


def _r_reveal_surprise(world: World) -> bool:
    if not world.repair_complete:
        return False
    lead = world.entities["lead"]
    pal = world.entities["pal"]
    cloud = world.entities["cloud"]
    lead.add_meme("joy", 1.0)
    pal.add_meme("joy", 1.0)
    cloud.add_meme("gentleness", 0.9)
    world.surprise_shown = True
    world.facts["surprise_effect"] = world.trouble.surprise_effect
    world.note(
        "surprise",
        f"The fix revealed {world.trouble.surprise_item}.",
        effect=world.trouble.surprise_effect,
        ending_image=world.trouble.ending_image,
    )
    return True


RULES = [
    Rule("set_scene", _r_set_scene),
    Rule("hear_whisper", _r_hear_whisper),
    Rule("laugh_in_field", _r_laugh_in_field),
    Rule("find_piece", _r_find_piece),
    Rule("finish_repair", _r_finish_repair),
    Rule("reveal_surprise", _r_reveal_surprise),
]


def build_world(params: StoryParams) -> World:
    if params.team not in TEAMS:
        raise StoryError(f"No story: unknown camper team {params.team!r}.")
    if not valid_combo(params.campground, params.trouble, params.fix):
        raise StoryError(invalid_reason(params.campground, params.trouble, params.fix))
    campground = CAMPGROUNDS[params.campground]
    team = TEAMS[params.team]
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    world = World(params=params, campground=campground, team=team, trouble=trouble, fix=fix)
    world.add(
        Entity(
            name=team.lead_name,
            kind=team.lead_kind,
            role="lead",
            meters={"height_cm": 129.0},
            memes={"kindness": 0.8},
            tags={"job": "lead camper"},
        )
    )
    world.add(
        Entity(
            name=team.pal_name,
            kind=team.pal_kind,
            role="pal",
            meters={"height_cm": 127.0},
            memes={"loyalty": 0.8},
            tags={"job": "helper camper"},
        )
    )
    world.add(
        Entity(
            name="fuzzy field",
            kind="place",
            role="field",
            meters={"span_m": 14.0},
            memes={"welcome": 0.7},
            tags={"texture": "fuzzy"},
        )
    )
    world.add(
        Entity(
            name="rusty cabin",
            kind="building",
            role="cabin",
            meters={"boards": 16.0},
            memes={"age": 0.8},
            tags={"look": "rusty"},
        )
    )
    world.add(
        Entity(
            name="whispering cloud",
            kind="weather",
            role="cloud",
            meters={"span_m": 21.0},
            memes={"hush": 0.8},
            tags={"voice": "whispering"},
        )
    )
    world.add(
        Entity(
            name=trouble.missing_piece,
            kind="part",
            role="piece",
            meters={"size_cm": 6.0},
            memes={"importance": 0.7},
            tags={"status": "lost"},
        )
    )
    world.add(
        Entity(
            name=campground.name,
            kind="campground",
            role="camp",
            meters={"tables": 2.0},
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
    pal = world.entities["pal"]
    opening = (
        f"At {world.campground.name}, {lead.name} and {pal.name} were setting out cups and cards for {world.campground.evening_job}. "
        f"Beside them stretched {world.campground.field_detail}, and just beyond it stood {world.campground.cabin_detail}. "
        f"Over the roof drifted {world.campground.cloud_detail}, so the whole campground felt soft and expectant."
    )

    tension = (
        f"Then a breeze touched the {world.trouble.loose_part}, and the sound seemed to say, "
        f'"{world.trouble.whisper_words}." {lead.name} froze with a cup in {lead.pronoun("possessive")} hand, because for one startled moment the whispering cloud and the rusty cabin sounded like they were talking to each other. '
        f"{world.trouble.risk}"
    )

    turn = (
        f"The two friends hurried into the fuzzy field. They {world.team.shared_habit}, even when their knees felt shaky. "
        f"{world.team.joke_line} {world.team.comfort_line} "
        f"Soon they spotted the {world.trouble.missing_piece} {world.trouble.clue_place}. {world.trouble.cause}"
    )

    repair = (
        f"Carrying the little piece back to the rusty cabin, they used {world.fix.gear_phrase}. "
        f"{world.fix.action_phrase} {world.fix.result_phrase} {world.fix.proof_phrase}"
    )

    ending = (
        f"{world.trouble.surprise_effect} {lead.name} and {pal.name} burst into warm, relieved laughter because the campground had saved one last tiny surprise for them. "
        f"Soon everyone could smell {world.campground.treat}, hear {world.campground.closing_sound}, and see {world.trouble.ending_image}. "
        f"The whispering cloud drifted higher, gentle now, as if it were pleased that two kind children had listened closely and helped."
    )

    return "\n\n".join([opening, tension, turn, repair, ending])


def _prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming campground story for children that includes the exact phrases "fuzzy field", "rusty cabin", and "whispering cloud".',
        f"Tell a funny surprise story where {world.team.lead_name} and {world.team.pal_name} solve a whispered campground problem before cocoa time.",
        f"Write a cozy tale set at {world.campground.name}, where a spooky-sounding mystery turns out to be a fixable cabin problem and ends with a tiny hidden prize.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    lead = world.team.lead_name
    pal = world.team.pal_name
    return [
        QAItem(
            "What first made the children think something odd was happening?",
            f"They heard the {world.trouble.loose_part} seem to say '{world.trouble.whisper_words}' under the whispering cloud. For a moment, the sound made the sky and the rusty cabin feel almost alive.",
        ),
        QAItem(
            "Why did they go into the fuzzy field?",
            f"They went into the fuzzy field to look for the missing {world.trouble.missing_piece}. They knew the cabin part could not be fixed until the right piece was back where it belonged.",
        ),
        QAItem(
            "What funny thing helped the children calm down?",
            f"{world.team.joke_line} That silly sight broke the tension, so {lead} and {pal} could treat the whisper like a puzzle instead of a danger.",
        ),
        QAItem(
            "What was really causing the whispering sound?",
            f"{world.trouble.cause} The whisper sounded magical, but it was really a small physical problem shaped by the wind.",
        ),
        QAItem(
            "How did they repair the problem?",
            f"They used {world.fix.gear_phrase} to work on the {world.trouble.loose_part}. {world.fix.action_phrase}",
        ),
        QAItem(
            "Why did the repair matter to the whole campground?",
            f"{world.trouble.risk} Fixing it meant the welcome corner could feel calm and cheerful for every camper who arrived.",
        ),
        QAItem(
            "What surprise came after the fix?",
            f"The repair revealed {world.trouble.surprise_item}. {world.trouble.surprise_effect}",
        ),
        QAItem(
            "How did the campground feel different at the end?",
            f"At first the campground felt jumpy because the whisper made the children stop and stare. By the end, everyone could enjoy {world.trouble.ending_image}, and the whole place felt warm, funny, and ready to welcome people.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why can wind around a loose object sound like a whisper?",
            f"Moving air can turn a gap, scrape, or wobble into a thin voice-like noise. In this world, the {world.trouble.loose_part} shaped the breeze until it seemed to say words.",
        ),
        QAItem(
            "Why might a tiny part be hard to find in a fuzzy field?",
            "Soft seed fluff, clover, and low grass can hide a small object very quickly. A lost piece often only shows itself when someone looks slowly from close by.",
        ),
        QAItem(
            "Why does laughing sometimes help children solve a problem?",
            "A gentle laugh can calm a frightened body and loosen a tight feeling in the chest. Once children feel safer, they usually notice clues and help each other better.",
        ),
        QAItem(
            "Why do little repairs matter in a shared campground?",
            "A campground works because many small things stay safe and steady for everyone. Fixing one loose part can change a place from fussy and confusing to warm and welcoming.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.campground not in CAMPGROUNDS:
        raise StoryError(f"No story: unknown campground {params.campground!r}.")
    if params.team not in TEAMS:
        raise StoryError(f"No story: unknown camper team {params.team!r}.")
    if params.trouble not in TROUBLES:
        raise StoryError(f"No story: unknown whisper trouble {params.trouble!r}.")
    if params.fix not in FIXES:
        raise StoryError(f"No story: unknown fix plan {params.fix!r}.")
    if not valid_combo(params.campground, params.trouble, params.fix):
        raise StoryError(invalid_reason(params.campground, params.trouble, params.fix))
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
supported(C,F) :-
    campground(C),
    fix(F),
    not missing_supply(C,F).

missing_supply(C,F) :-
    campground(C),
    fix(F),
    requires(F,S),
    not has_supply(C,S).

combo(C,T,F) :-
    campground(C),
    trouble(T),
    fix(F),
    needs(T,N),
    fixes(F,N),
    supported(C,F).

ok :-
    chosen(C,T,F),
    combo(C,T,F).

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
    for team in TEAMS:
        rows.append(fact("team", team))
    for trouble, issue in TROUBLES.items():
        rows.append(fact("trouble", trouble))
        rows.append(fact("needs", trouble, issue.need))
    for fix, plan in FIXES.items():
        rows.append(fact("fix", fix))
        rows.append(fact("fixes", fix, plan.need))
        for supply in plan.requires:
            rows.append(fact("requires", fix, supply))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.campground, params.trouble, params.fix) + "\n"
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

    teams = sorted(TEAMS)
    for index, combo in enumerate(sorted(py), 1):
        params = StoryParams(
            campground=combo[0],
            team=teams[(index - 1) % len(teams)],
            trouble=combo[1],
            fix=combo[2],
            seed=5000 + index,
        )
        if not asp_verify(params):
            raise StoryError(f"ASP verify failed for combo {combo}.")
        sample = generate(params)
        lowered = sample.story.lower()
        missing = [token for token in REQUIRED_TOKENS if token not in lowered]
        if missing:
            raise StoryError(f"Generated story for {combo} missed required seed terms: {missing}")
        if len(sample.prompts) < 3 or len(sample.story_qa) < 7 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated story for {combo} has incomplete prompt or QA coverage.")
        if sample.story.count("\n\n") < 4:
            raise StoryError(f"Generated story for {combo} did not form a full five-part tale.")
        if sample.world is None or not sample.world.repair_complete or not sample.world.surprise_shown:
            raise StoryError(f"Generated story for {combo} did not complete the repair arc.")
        multi_sentence = sum(answer.answer.count(".") >= 2 for answer in sample.story_qa)
        if multi_sentence < 6:
            raise StoryError(f"Generated story for {combo} regressed to shallow QA.")
        chosen_names = {TEAMS[params.team].lead_name, TEAMS[params.team].pal_name}
        other_names = {
            camper.lead_name for camper in TEAMS.values()
        } | {
            camper.pal_name for camper in TEAMS.values()
        }
        leaked_names = sorted(
            name for name in (other_names - chosen_names) if name in sample.story or any(
                name in qa.answer for qa in sample.story_qa
            )
        )
        if leaked_names:
            raise StoryError(f"Generated story for {combo} leaked unrelated names: {leaked_names}")
    return f"OK: clingo gate matches valid_combos() ({len(py)} combos) and all generated stories pass seed, arc, and QA checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate fuzzy field / rusty cabin / whispering cloud campground StoryWorld samples."
    )
    parser.add_argument("--campground", choices=sorted(CAMPGROUNDS))
    parser.add_argument("--team", choices=sorted(TEAMS))
    parser.add_argument("--trouble", choices=sorted(TROUBLES))
    parser.add_argument("--fix", choices=sorted(FIXES))
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
    team = args.team or rng.choice(sorted(TEAMS))
    return StoryParams(
        campground=combo[0],
        team=team,
        trouble=combo[1],
        fix=combo[2],
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
    if args.trouble:
        filtered = [combo for combo in filtered if combo[1] == args.trouble]
    if args.fix:
        filtered = [combo for combo in filtered if combo[2] == args.fix]
    if args.campground and args.trouble and args.fix and not valid_combo(
        args.campground, args.trouble, args.fix
    ):
        raise StoryError(invalid_reason(args.campground, args.trouble, args.fix))
    if not filtered:
        camp = args.campground or "<any campground>"
        trouble = args.trouble or "<any trouble>"
        fix = args.fix or "<any fix>"
        raise StoryError(
            f"No story: no valid combo matches campground={camp}, trouble={trouble}, fix={fix}."
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
    for campground, trouble, fix in sorted(asp_valid_combos()):
        print(f"{campground}\t{trouble}\t{fix}")


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
