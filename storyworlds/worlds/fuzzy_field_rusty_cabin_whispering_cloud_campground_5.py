#!/usr/bin/env python3
"""
Standalone StoryWorld for the seed:

    Words: fuzzy field, rusty cabin, whispering cloud
    Setting: campground
    Features: Surprise, Humor
    Style: Heartwarming

Internal source tale:
    Two children help ready a campground welcome corner beside a fuzzy field and
    a rusty cabin. A whispering cloud passes over the cabin, wind slips through
    one loose part, and the children think the cabin is trying to talk. They
    search the fuzzy field for the missing piece, a silly fluff mishap turns the
    scare into laughter, and they fix the cabin together. The repair reveals a
    hidden welcome treat, so the whole campground ends softer, safer, and more
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


def oxford_join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def qa_clause(text: str) -> str:
    if text.startswith("A "):
        return "a " + text[2:]
    return text


@dataclass(frozen=True)
class CampgroundProfile:
    key: str
    name: str
    field_detail: str
    cabin_detail: str
    cloud_detail: str
    welcome_job: str
    treat: str
    ending_sound: str
    supplies: tuple[str, ...]


@dataclass(frozen=True)
class CamperTeam:
    key: str
    lead_name: str
    lead_kind: str
    pal_name: str
    pal_kind: str
    shared_habit: str
    gag_line: str
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
    need: str
    surprise_item: str
    surprise_effect: str
    ending_image: str


@dataclass(frozen=True)
class FixPlan:
    key: str
    need: str
    requires: tuple[str, ...]
    tool_phrase: str
    action_phrase: str
    proof_phrase: str
    result_phrase: str


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
    whisper_heard: bool = False
    clue_found: bool = False
    laugh_shared: bool = False
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
            f"laugh_shared={self.laugh_shared}, "
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
        cabin_detail="a rusty cabin beside the welcome stump and the stack of enamel mugs",
        cloud_detail="a whispering cloud that trailed over the roof like a gray ribbon",
        welcome_job="setting out the welcome cocoa corner",
        treat="warm berry cocoa",
        ending_sound="the small ding of two enamel cups touching",
        supplies=("hinge_pin", "patch_kit", "porch_stool", "camp_twine"),
    ),
    "lantern_hollow": CampgroundProfile(
        key="lantern_hollow",
        name="Lantern Hollow Campground",
        field_detail="a fuzzy field that brushed every ankle with clover and floating white fuzz",
        cabin_detail="a rusty cabin near the supper bell and the firewood pile",
        cloud_detail="a whispering cloud that floated low enough to soften the first stars",
        welcome_job="making the evening greeting corner look bright and neat",
        treat="maple cocoa",
        ending_sound="the plink of the cabin spoon resting in a cocoa mug",
        supplies=("patch_kit", "porch_stool", "berry_cloth"),
    ),
    "mossy_pines": CampgroundProfile(
        key="mossy_pines",
        name="Mossy Pines Campground",
        field_detail="a fuzzy field where every breeze sent soft seeds scooting past little boots",
        cabin_detail="a rusty cabin with a lantern hook and a narrow step by the door",
        cloud_detail="a whispering cloud curled above the chimney like a sleepy scarf",
        welcome_job="readying the late-arrival welcome table",
        treat="honey cocoa",
        ending_sound="the tiny tap of lantern glass settling on its hook",
        supplies=("hinge_pin", "camp_twine", "berry_cloth"),
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
        gag_line="A puff of fuzz landed under Milo's nose like a proud old mustache, and he bowed to the cabin as if it were a queen.",
        comfort_line="Once they laughed together, the strange sound felt like a puzzle instead of a threat.",
    ),
    "ivy_noah": CamperTeam(
        key="ivy_noah",
        lead_name="Ivy",
        lead_kind="girl",
        pal_name="Noah",
        pal_kind="boy",
        shared_habit="always checked each other's work before calling a job finished",
        gag_line="Noah sneezed into the fluff and announced that the field was trying to knit him a beard before supper.",
        comfort_line="Their best ideas always arrived right after one honest giggle and one kind glance.",
    ),
    "tess_benji": CamperTeam(
        key="tess_benji",
        lead_name="Tess",
        lead_kind="girl",
        pal_name="Benji",
        pal_kind="boy",
        shared_habit="turned cleanup into a quiet game of who could notice the smallest detail",
        gag_line="A seed puff stuck to Benji's eyebrow, and Tess said he looked like a surprised owl wrapped in a blanket.",
        comfort_line="Sharing the worry made it lighter, and sharing the laugh made them brave again.",
    ),
}


TROUBLES: dict[str, WhisperTrouble] = {
    "loose_shutter": WhisperTrouble(
        key="loose_shutter",
        loose_part="cabin shutter",
        missing_piece="a brass hinge pin",
        whisper_words="whoooo, close me",
        clue_place="by a flat stone in the fuzzy field",
        cause="Wind kept slipping through the half-hanging shutter and rubbing rusty metal against wood",
        risk="If the shutter kept flapping, it could scare new campers and bang the window all evening.",
        need="hinge_pin",
        surprise_item="a folded welcome note tucked in the shutter pocket",
        surprise_effect="Inside the note was a tiny row of cinnamon buttons left by last summer's campers for the next children who helped.",
        ending_image="the cabin window sitting straight while the children shared cinnamon buttons on the porch step",
    ),
    "vent_patch": WhisperTrouble(
        key="vent_patch",
        loose_part="roof vent flap",
        missing_piece="a square tin patch",
        whisper_words="hushhhh, mend me",
        clue_place="caught in thistles at the edge of the fuzzy field",
        cause="A loose flap on the cabin roof turned the breeze into a thin whistling voice",
        risk="If the flap stayed loose, night air could rattle the roof and make the welcome corner feel uneasy.",
        need="patch_kit",
        surprise_item="a hidden paper star garland under the vent shelf",
        surprise_effect="When the flap sat still again, the hidden stars slid out, and the children hung them by the welcome mugs.",
        ending_image="paper stars swaying under the porch roof while cocoa steam curled into the cool air",
    ),
    "bell_loop": WhisperTrouble(
        key="bell_loop",
        loose_part="welcome bell tongue",
        missing_piece="a twine loop",
        whisper_words="hellooo, tie me",
        clue_place="resting in the clover of the fuzzy field",
        cause="The bell tongue kept scraping the bell wall whenever the breeze nudged it",
        risk="If the bell stayed crooked, the cabin would keep muttering and the supper welcome would sound wrong.",
        need="camp_twine",
        surprise_item="a painted acorn charm hidden behind the bell hook",
        surprise_effect="The charm had a tiny smile on it, and the children tied it to the welcome table so everyone would see it first.",
        ending_image="the bell ringing cleanly while the painted acorn winked beside the mugs",
    ),
}


FIXES: dict[str, FixPlan] = {
    "pin_reset": FixPlan(
        key="pin_reset",
        need="hinge_pin",
        requires=("hinge_pin",),
        tool_phrase="the spare brass hinge pin from the tool tray",
        action_phrase="The children lifted the shutter together and slid the pin back through the sleepy hinge",
        proof_phrase="The shutter stopped wobbling and only gave one polite click",
        result_phrase="The window could rest quietly again, and the whole porch looked ready to smile at visitors.",
    ),
    "patch_press": FixPlan(
        key="patch_press",
        need="patch_kit",
        requires=("patch_kit", "porch_stool"),
        tool_phrase="the little patch kit and the porch stool",
        action_phrase="The children climbed carefully, pressed the tin patch flat, and smoothed each edge until the flap stopped curling",
        proof_phrase="The roof kept the wind outside instead of turning it into a whisper",
        result_phrase="The cabin sounded settled, like it had finally finished a long fussy complaint.",
    ),
    "twine_tie": FixPlan(
        key="twine_tie",
        need="camp_twine",
        requires=("camp_twine",),
        tool_phrase="a fresh loop of camp twine from the welcome basket",
        action_phrase="The children threaded the soft twine through the bell tongue and knotted it with careful little fingers",
        proof_phrase="The bell answered with one clear ring instead of a scratchy mumble",
        result_phrase="The welcome corner sounded bright and friendly again.",
    ),
}


def valid_combo(campground: str, trouble: str, fix: str) -> bool:
    profile = CAMPGROUNDS[campground]
    issue = TROUBLES[trouble]
    plan = FIXES[fix]
    if issue.need != plan.need:
        return False
    return all(supply in profile.supplies for supply in plan.requires)


def invalid_reason(campground: str, trouble: str, fix: str) -> str:
    profile = CAMPGROUNDS[campground]
    issue = TROUBLES[trouble]
    plan = FIXES[fix]
    if issue.need != plan.need:
        return (
            f"No story: {fix!r} repairs {plan.need}, but {trouble!r} needs {issue.need}. "
            f"The fix does not match the problem."
        )
    missing = [supply for supply in plan.requires if supply not in profile.supplies]
    if missing:
        return (
            f"No story: {profile.name} does not have {oxford_join(missing)} for {fix!r}. "
            f"That campground cannot support this repair."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for campground in sorted(CAMPGROUNDS):
        for trouble in sorted(TROUBLES):
            for fix in sorted(FIXES):
                if valid_combo(campground, trouble, fix):
                    combos.append((campground, trouble, fix))
    return combos


def build_world(params: StoryParams) -> World:
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

    world = World(
        params=params,
        campground=CAMPGROUNDS[params.campground],
        team=TEAMS[params.team],
        trouble=TROUBLES[params.trouble],
        fix=FIXES[params.fix],
    )

    lead = Entity(
        name=world.team.lead_name,
        kind=world.team.lead_kind,
        role="lead",
        meters={"courage": 0.5, "tiredness": 0.1},
        memes={"Care": 0.8, "Humor": 0.5, "Surprise": 0.2},
    )
    pal = Entity(
        name=world.team.pal_name,
        kind=world.team.pal_kind,
        role="pal",
        meters={"courage": 0.45, "tiredness": 0.1},
        memes={"Care": 0.8, "Humor": 0.6, "Surprise": 0.2},
    )
    cabin = Entity(
        name=world.campground.cabin_detail,
        kind="cabin",
        role="cabin",
        meters={"sturdiness": 0.45, "rust": 0.8},
        memes={"Warmth": 0.4},
        tags={"state": "wobbly"},
    )
    field = Entity(
        name="fuzzy field",
        kind="field",
        role="field",
        meters={"fuzz": 0.95},
        memes={"Playfulness": 0.6},
    )
    cloud = Entity(
        name="whispering cloud",
        kind="cloud",
        role="cloud",
        meters={"drift": 0.75},
        memes={"Surprise": 0.4},
    )
    camp = Entity(
        name=world.campground.name,
        kind="campground",
        role="campground",
        meters={"calm": 0.6},
        memes={"Warmth": 0.7, "Humor": 0.4},
    )

    world.add(lead)
    world.add(pal)
    world.add(cabin)
    world.add(field)
    world.add(cloud)
    world.add(camp)
    return world


def _play_story(world: World) -> None:
    lead = world.entities["lead"]
    pal = world.entities["pal"]
    cabin = world.entities["cabin"]
    camp = world.entities["campground"]

    world.facts["setting"] = world.campground.name
    world.facts["job"] = world.campground.welcome_job
    world.facts["needed_item"] = world.trouble.missing_piece
    world.facts["cause"] = world.trouble.cause

    world.note(
        "beginning",
        "The children begin a welcome job together.",
        place=world.campground.name,
        job=world.campground.welcome_job,
    )

    world.whisper_heard = True
    lead.add_meme("Surprise", 0.5)
    pal.add_meme("Surprise", 0.5)
    lead.add_meter("courage", -0.1)
    pal.add_meter("courage", -0.1)
    camp.add_meter("calm", -0.15)
    world.note(
        "whisper",
        "A whisper-like sound startles the children.",
        source=world.trouble.loose_part,
        words=world.trouble.whisper_words,
        cause=world.trouble.cause,
    )

    world.clue_found = True
    lead.add_meter("courage", 0.2)
    pal.add_meter("courage", 0.2)
    world.facts["clue_place"] = world.trouble.clue_place
    world.note(
        "search",
        "The children search the fuzzy field and find the missing piece.",
        place=world.trouble.clue_place,
        item=world.trouble.missing_piece,
    )

    world.laugh_shared = True
    lead.add_meme("Humor", 0.4)
    pal.add_meme("Humor", 0.4)
    lead.add_meme("Surprise", -0.2)
    pal.add_meme("Surprise", -0.2)
    camp.add_meme("Humor", 0.3)
    world.facts["gag"] = world.team.gag_line
    world.facts["comfort"] = world.team.comfort_line
    world.note(
        "laugh",
        "A fuzzy-field gag turns the scare into laughter.",
        gag=world.team.gag_line,
        comfort=world.team.comfort_line,
    )

    world.repair_complete = True
    cabin.add_meter("sturdiness", 0.45)
    cabin.tags["state"] = "steady"
    camp.add_meter("calm", 0.25)
    camp.add_meme("Warmth", 0.2)
    lead.add_meme("Care", 0.2)
    pal.add_meme("Care", 0.2)
    world.facts["tool_phrase"] = world.fix.tool_phrase
    world.note(
        "repair",
        "The children use the right supplies and complete the repair.",
        tools=world.fix.tool_phrase,
        proof=world.fix.proof_phrase,
    )

    world.surprise_shown = True
    lead.add_meme("Surprise", 0.3)
    pal.add_meme("Surprise", 0.3)
    camp.add_meme("Warmth", 0.2)
    world.facts["surprise_item"] = world.trouble.surprise_item
    world.facts["ending_image"] = world.trouble.ending_image
    world.note(
        "surprise",
        "The fix reveals a hidden gift for the welcome corner.",
        item=world.trouble.surprise_item,
        effect=world.trouble.surprise_effect,
    )


def _render_story(world: World) -> str:
    if not world.history:
        _play_story(world)

    lead = world.entities["lead"].name
    pal = world.entities["pal"].name

    opening = (
        f"{lead} and {pal} were at {world.campground.name}, busy {world.campground.welcome_job}. "
        f"Beside them lay a fuzzy field, and just past it stood a rusty cabin. "
        f"They {world.team.shared_habit}, so even lining up mugs for {world.campground.treat} felt important."
    )

    tension = (
        f"Then a whispering cloud slid over the cabin roof, and the children heard {world.trouble.whisper_words} "
        f"float out from the {world.trouble.loose_part}. {world.trouble.cause}. "
        f"For one long breath they stared at each other, because it truly sounded as if the cabin had decided to speak."
    )

    turn = (
        f"They looked carefully instead of running and guessed that something small had come loose. "
        f"In {world.campground.field_detail}, they found {world.trouble.missing_piece} {world.trouble.clue_place}. "
        f"{world.team.gag_line} {world.team.comfort_line}"
    )

    repair = (
        f"With {world.fix.tool_phrase}, they hurried back to the rusty cabin. {world.fix.action_phrase}. "
        f"{world.fix.proof_phrase}. {world.fix.result_phrase}"
    )

    ending = (
        f"When the cabin settled, the children discovered {world.trouble.surprise_item}. {world.trouble.surprise_effect} "
        f"Soon the campground felt different: safer, funnier, and full of welcome. "
        f"By the time evening came, everyone could enjoy {world.trouble.ending_image} and {world.campground.ending_sound}."
    )

    return "\n\n".join([opening, tension, turn, repair, ending])


def _prompts(world: World) -> list[str]:
    lead = world.entities["lead"].name
    pal = world.entities["pal"].name
    return [
        (
            f"Tell a heartwarming campground story about {lead} and {pal} preparing a welcome corner beside a fuzzy field and a rusty cabin."
        ),
        (
            f"Include a whispering cloud, a funny fluff mishap, and a surprise that appears only after the children repair the {world.trouble.loose_part}."
        ),
        (
            f"Keep the tone child-friendly and warm, and make sure the ending image includes {world.trouble.ending_image}."
        ),
    ]


def _story_qa(world: World) -> list[QAItem]:
    lead = world.entities["lead"].name
    pal = world.entities["pal"].name
    return [
        QAItem(
            "What were the children trying to do at the start of the story?",
            f"{lead} and {pal} were helping at {world.campground.name} by {world.campground.welcome_job}. They wanted the campground to feel kind and ready for new people.",
        ),
        QAItem(
            "Why did the cabin seem to be whispering?",
            f"It seemed to whisper because {world.trouble.cause.lower()}. The loose {world.trouble.loose_part} shaped the wind until it sounded like words.",
        ),
        QAItem(
            "Why did the children go into the fuzzy field?",
            f"They went into the fuzzy field because the repair could not happen without {world.trouble.missing_piece}. The children found it {world.trouble.clue_place}, where the breeze had carried it away.",
        ),
        QAItem(
            "What made the scary moment turn funny?",
            f"The scary moment turned funny when {qa_clause(world.team.gag_line)} That laugh helped both children feel steady enough to think clearly again.",
        ),
        QAItem(
            "How did the children fix the problem?",
            f"They used {world.fix.tool_phrase} to repair the {world.trouble.loose_part}. {world.fix.proof_phrase}, which showed the fix had worked.",
        ),
        QAItem(
            "Why did the repair matter to the whole campground?",
            f"{world.trouble.risk} Once the repair was done, the welcome corner could feel calm and cheerful for everyone who arrived.",
        ),
        QAItem(
            "What surprise came after the repair?",
            f"The repair revealed {world.trouble.surprise_item}. {world.trouble.surprise_effect}",
        ),
        QAItem(
            "How was the campground different at the end?",
            f"At first the campground felt jumpy because the children stopped and listened to the strange whisper. By the end, the place felt warm and playful because the fix worked and the hidden welcome gift was shared.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why can a loose part and wind sound like a whisper?",
            f"Wind can slip through a gap and scrape against something shaky until it makes a thin voice-like sound. In this world, the {world.trouble.loose_part} turned the breeze into a whisper.",
        ),
        QAItem(
            "Why might a tiny object be hard to spot in a fuzzy field?",
            "Soft seed fluff, clover, and low grass can hide a small object very quickly. Children often have to look slowly and close to the ground before a missing piece shows itself.",
        ),
        QAItem(
            "Why does laughing sometimes help children solve a problem?",
            "A gentle laugh can loosen fear and make the body feel safer. Once children calm down, they usually notice clues and work together better.",
        ),
        QAItem(
            "Why do little repairs matter in a campground?",
            "A campground feels welcoming when its shared places are steady and safe. Fixing one loose part can change a whole evening from uneasy to cozy.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = _render_story(world)
    return StorySample(
        params=params,
        story=story,
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
            seed=4000 + index,
        )
        if not asp_verify(params):
            raise StoryError(f"ASP verify failed for combo {combo}.")
        sample = generate(params)
        lowered = sample.story.lower()
        missing = [token for token in REQUIRED_TOKENS if token not in lowered]
        if missing:
            raise StoryError(f"Generated story for {combo} missed required seed terms: {missing}")
        if len(sample.prompts) < 3 or len(sample.story_qa) < 8 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated story for {combo} has incomplete prompt or QA coverage.")
        if sample.story.count("\n\n") < 4:
            raise StoryError(f"Generated story for {combo} did not form a full five-part tale.")
        if sample.world is None:
            raise StoryError(f"Generated story for {combo} lost its world model.")
        if not sample.world.whisper_heard or not sample.world.clue_found:
            raise StoryError(f"Generated story for {combo} skipped the middle turn.")
        if not sample.world.repair_complete or not sample.world.surprise_shown:
            raise StoryError(f"Generated story for {combo} did not complete the repair arc.")
        multi_sentence = sum(item.answer.count(".") >= 2 for item in sample.story_qa)
        if multi_sentence < 7:
            raise StoryError(f"Generated story for {combo} regressed to shallow QA.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Generated story for {combo} leaked template markers.")
    return (
        f"OK: clingo gate matches valid_combos() ({len(py)} combos) and all generated stories pass "
        "seed, arc, and QA checks."
    )


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
