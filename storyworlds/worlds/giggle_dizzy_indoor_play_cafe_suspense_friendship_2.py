#!/usr/bin/env python3
"""
Indoor play cafe mystery world.

Internal source tale
--------------------
At Lantern Loops Indoor Play Cafe, a child and a close friend wear a shared
detective lanyard with a silver compass charm. After a fast crossing leaves the
hero dizzy, the pair slow down on purpose instead of rushing for another turn.
That pause lets them hear a hidden giggle from an empty play zone, and the hero
realizes the compass charm is missing. With a calm helper and a clue-matched
search, the friends solve a small mystery safely. The ending image proves that
the play cafe is peaceful again.
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


CAFE_NAME = "Lantern Loops Indoor Play Cafe"


@dataclass(frozen=True)
class PlayZone:
    key: str
    phrase: str
    detail: str
    ending_image: str
    supported_methods: tuple[str, ...]
    window_spot: str = ""
    draft_spot: str = ""
    stack_spot: str = ""


@dataclass(frozen=True)
class Mystery:
    key: str
    label: str
    sound_phrase: str
    clue: str
    need: str
    truth: str
    why_here: str
    final_fix: str
    final_image: str
    zones: tuple[str, ...]


@dataclass(frozen=True)
class SearchMethod:
    key: str
    phrase: str
    action_text: str
    safe_reason: str
    solves: tuple[str, ...]
    unsafe: bool = False


@dataclass(frozen=True)
class Helper:
    key: str
    phrase: str
    comfort_line: str


@dataclass
class StoryParams:
    zone: str
    mystery: str
    method: str
    hero: str
    gender: str
    friend: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    phrase: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "woman"}:
            table = {"subject": "she", "object": "her", "possessive": "her"}
            return table[case]
        if self.kind in {"boy", "man"}:
            table = {"subject": "he", "object": "him", "possessive": "his"}
            return table[case]
        table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]


@dataclass
class World:
    params: StoryParams
    zone_cfg: PlayZone
    mystery_cfg: Mystery
    method_cfg: SearchMethod
    helper_cfg: Helper
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    fired: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, name: str, **data: str) -> None:
        self.history.append({"event": name, **data})
        self.fired.append(name)

    def render(self) -> str:
        return "\n\n".join(" ".join(bits) for bits in self.paragraphs if bits)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  zone={self.zone_cfg.key}")
        rows.append(f"  mystery={self.mystery_cfg.key}")
        rows.append(f"  method={self.method_cfg.key}")
        rows.append(f"  helper={self.helper_cfg.key}")
        for entity in self.entities.values():
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            rows.append(
                f"  {entity.name}<{entity.kind}> location={entity.location} "
                f"meters={meters} memes={memes}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append(f"  history={self.history}")
        rows.append(f"  fired={self.fired}")
        return "\n".join(rows)


ZONES: dict[str, PlayZone] = {
    "comet_tube": PlayZone(
        key="comet_tube",
        phrase="the comet crawl tube above the cocoa tables",
        detail=(
            "clear side windows caught the lamp glow, and a row of tiny boots "
            "waited below on the cubby shelf"
        ),
        ending_image=(
            "The tube shone empty above the cocoa tables, and the boots stayed "
            "paired heel to heel."
        ),
        supported_methods=("trace_shadow_window", "ask_helper_open_flap", "follow_streamer_draft"),
        window_spot="the clear service pocket under the tube bend",
        draft_spot="the warm vent lip beside the tube ladder",
    ),
    "pillow_cove": PlayZone(
        key="pillow_cove",
        phrase="the pillow cove behind the picture-book rug",
        detail=(
            "quilted hills leaned under sleepy lanterns, and ribbons on the "
            "story canopy barely moved at all"
        ),
        ending_image=(
            "The lanterns glowed on the tidy pillow cove, and the canopy ribbons "
            "rested in one soft line."
        ),
        supported_methods=("follow_streamer_draft", "lift_blankets_together"),
        draft_spot="the ribbon hook behind the canopy post",
        stack_spot="the folded blanket shelf by the rug",
    ),
    "waffle_bridge": PlayZone(
        key="waffle_bridge",
        phrase="the waffle bridge over the foam-ball bay",
        detail=(
            "soft yellow steps bounced above a sea of pale balls, and a clear "
            "guard bubble curved beside the last step"
        ),
        ending_image=(
            "The foam-ball bay lay smooth under the bridge, and the clear guard "
            "bubble held only lamp reflections."
        ),
        supported_methods=("trace_shadow_window", "ask_helper_open_flap"),
        window_spot="the clear guard pocket beside the last bridge step",
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "clear_pocket_giggle": Mystery(
        key="clear_pocket_giggle",
        label="the clear-pocket giggle",
        sound_phrase="a shut-in giggle that squeaked, stopped, and squeaked again",
        clue=(
            "A round shadow kept bumping the same clear seam whenever the play "
            "frame settled."
        ),
        need="window",
        truth=(
            "The silver compass charm had slipped beside a tiny squeeze-planet "
            "toy in the clear pocket, and each small nudge made the toy giggle."
        ),
        why_here=(
            "The charm had snagged while the friends were climbing, so it stayed "
            "trapped where only a careful look through the window could find it."
        ),
        final_fix=(
            "The helper opened the pocket, clipped the charm back onto the "
            "friendship lanyard, and returned the squeeze-planet to the lost-toy basket."
        ),
        final_image=(
            "Nothing tapped the clear panel now except a soft wash of cafe light."
        ),
        zones=("comet_tube", "waffle_bridge"),
    ),
    "ribbon_laugh": Mystery(
        key="ribbon_laugh",
        label="the ribbon laugh",
        sound_phrase="a papery giggle that skipped whenever the warm air breathed through the room",
        clue=(
            "One loose streamer kept leaning toward the same corner, even when "
            "no child moved nearby."
        ),
        need="draft",
        truth=(
            "A snack-cup lid was fluttering against the vent, and the missing "
            "compass charm was tucked under its rim where the draft had nudged it."
        ),
        why_here=(
            "The moving air was gentle, but it was steady enough to herd light "
            "things into one small hiding place."
        ),
        final_fix=(
            "The lid went into the recycle bin, and the charm was fastened back "
            "where it belonged."
        ),
        final_image=(
            "Only one ribbon stirred after that, and it moved as quietly as a yawn."
        ),
        zones=("comet_tube", "pillow_cove"),
    ),
    "blanket_bell_secret": Mystery(
        key="blanket_bell_secret",
        label="the blanket-bell secret",
        sound_phrase="a muffled giggle-clink from deep inside the folded blankets",
        clue=(
            "The top blanket sat crooked, as if something small were propping "
            "one edge higher than the rest."
        ),
        need="stack",
        truth=(
            "The compass charm had slipped into a blanket fold and was tapping a "
            "tiny bell clip from the tea-set basket whenever the pile shifted."
        ),
        why_here=(
            "The friends had tucked the blankets aside in a hurry before stopping "
            "to rest, so the fold became a perfect hiding place."
        ),
        final_fix=(
            "Together they smoothed the blankets flat, hung the bell clip back on "
            "the basket, and clipped the charm onto the lanyard again."
        ),
        final_image=(
            "The blanket shelf looked sleepy and square, with no secret sound left inside it."
        ),
        zones=("pillow_cove",),
    ),
}

METHODS: dict[str, SearchMethod] = {
    "trace_shadow_window": SearchMethod(
        key="trace_shadow_window",
        phrase="trace the shadow through the clear window before touching anything",
        action_text=(
            "{friend} steadied the rail while {hero} followed the shape with one "
            "careful finger on the outside. {helper} watched the seam so nothing "
            "would be tugged too hard."
        ),
        safe_reason=(
            "Looking first through the clear panel keeps the clue visible and "
            "prevents rough grabbing."
        ),
        solves=("window",),
    ),
    "ask_helper_open_flap": SearchMethod(
        key="ask_helper_open_flap",
        phrase="ask the helper to open the service flap",
        action_text=(
            "{hero} pointed to the sound, and {helper} opened the small service "
            "flap while {friend} kept the step clear. They moved slowly enough "
            "to hear the clue instead of losing it."
        ),
        safe_reason=(
            "Only the grown-up opens the flap, which keeps the play structure and "
            "the children safe."
        ),
        solves=("window",),
    ),
    "follow_streamer_draft": SearchMethod(
        key="follow_streamer_draft",
        phrase="hold still and watch which way the ribbon leans",
        action_text=(
            "{friend} lifted one loose streamer into the air while {hero} watched "
            "which way it tilted. {helper} nodded when the streamer pointed to the "
            "same place twice."
        ),
        safe_reason=(
            "A steady draft can reveal a light hiding place without any climbing, "
            "shoving, or guessing."
        ),
        solves=("draft",),
    ),
    "lift_blankets_together": SearchMethod(
        key="lift_blankets_together",
        phrase="lift the blanket stack together from both sides",
        action_text=(
            "{hero} and {friend} each took one side of the folded blankets while "
            "{helper} slid the tea basket away first. They lifted slowly so anything "
            "hidden could stay put long enough to be seen."
        ),
        safe_reason=(
            "Two-sided lifting keeps the stack balanced and stops small things from "
            "sliding deeper into the folds."
        ),
        solves=("stack",),
    ),
    "scramble_after_echo": SearchMethod(
        key="scramble_after_echo",
        phrase="scramble toward the sound before it can hide again",
        action_text="",
        safe_reason=(
            "Rushing through ladders, rails, and soft obstacles is not a safe way "
            "to solve a mystery in a busy play cafe."
        ),
        solves=("window", "draft", "stack"),
        unsafe=True,
    ),
}

HELPERS: dict[str, Helper] = {
    "nella": Helper(
        key="nella",
        phrase="Miss Nella the play host",
        comfort_line=(
            "Miss Nella whispered that the best mystery clue is the one that a calm body can still notice."
        ),
    ),
    "omar": Helper(
        key="omar",
        phrase="Mr. Omar from the cocoa counter",
        comfort_line=(
            "Mr. Omar said that good detectives do not chase every sound; they wait for the true one to repeat."
        ),
    ),
    "tia": Helper(
        key="tia",
        phrase="Auntie Tia from the sock gate",
        comfort_line=(
            "Auntie Tia reminded them that friendship makes a scared feeling smaller when the room feels strange."
        ),
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Mira", "Elsie", "Nina", "Tori"),
    "boy": ("Owen", "Rafi", "Leo", "Kian"),
}

FRIEND_NAMES: tuple[str, ...] = ("Pip", "Skye", "Jun", "Ari", "Tess", "Milo")


def _spot_for(zone: PlayZone, need: str) -> str:
    if need == "window":
        return zone.window_spot
    if need == "draft":
        return zone.draft_spot
    if need == "stack":
        return zone.stack_spot
    return ""


def _hero_kind(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def explain_rejection(zone: str, mystery: str, method: str) -> str:
    if zone not in ZONES:
        return f"No story: unknown zone {zone!r}."
    if mystery not in MYSTERIES:
        return f"No story: unknown mystery {mystery!r}."
    if method not in METHODS:
        return f"No story: unknown method {method!r}."
    zone_cfg = ZONES[zone]
    mystery_cfg = MYSTERIES[mystery]
    method_cfg = METHODS[method]
    if method_cfg.unsafe:
        return "No story: scrambling after a sound is not reasonable in an indoor play cafe."
    if zone not in mystery_cfg.zones:
        return f"No story: {mystery_cfg.label} does not fit {zone_cfg.phrase}."
    if method not in zone_cfg.supported_methods:
        return f"No story: {method_cfg.phrase} is not supported in {zone_cfg.phrase}."
    if mystery_cfg.need not in method_cfg.solves:
        return f"No story: this method does not solve a {mystery_cfg.need} clue."
    if not _spot_for(zone_cfg, mystery_cfg.need):
        return f"No story: {zone_cfg.phrase} has no valid hiding place for a {mystery_cfg.need} mystery."
    return "No story: this indoor play cafe setup is not reasonable."


def valid_combo(zone: str, mystery: str, method: str) -> bool:
    if zone not in ZONES or mystery not in MYSTERIES or method not in METHODS:
        return False
    zone_cfg = ZONES[zone]
    mystery_cfg = MYSTERIES[mystery]
    method_cfg = METHODS[method]
    if method_cfg.unsafe:
        return False
    if zone not in mystery_cfg.zones:
        return False
    if method not in zone_cfg.supported_methods:
        return False
    if mystery_cfg.need not in method_cfg.solves:
        return False
    if not _spot_for(zone_cfg, mystery_cfg.need):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for zone in ZONES:
        for mystery in MYSTERIES:
            for method in METHODS:
                if valid_combo(zone, mystery, method):
                    rows.append((zone, mystery, method))
    return rows


def build_world(params: StoryParams) -> World:
    if params.friend == params.hero:
        raise StoryError("No story: the friend must be a different child from the hero.")
    if not valid_combo(params.zone, params.mystery, params.method):
        raise StoryError(explain_rejection(params.zone, params.mystery, params.method))
    zone_cfg = ZONES[params.zone]
    mystery_cfg = MYSTERIES[params.mystery]
    method_cfg = METHODS[params.method]
    helper_cfg = HELPERS[params.helper]
    world = World(
        params=params,
        zone_cfg=zone_cfg,
        mystery_cfg=mystery_cfg,
        method_cfg=method_cfg,
        helper_cfg=helper_cfg,
    )
    hero = world.add(Entity(params.hero, _hero_kind(params.gender), params.hero, location="cocoa bench"))
    friend = world.add(Entity(params.friend, "child", params.friend, location="cocoa bench"))
    helper = world.add(Entity(helper_cfg.phrase, "adult", helper_cfg.phrase, location=params.zone))
    charm = world.add(
        Entity(
            "charm",
            "object",
            "the silver compass charm on their friendship lanyard",
            location="hero lanyard",
        )
    )
    cause = world.add(Entity(mystery_cfg.label, "object", mystery_cfg.label, location=_spot_for(zone_cfg, mystery_cfg.need)))
    zone = world.add(Entity("zone", "place", zone_cfg.phrase, location=params.zone))

    hero.meters["steady"] += 0
    hero.memes["friendship"] += 1
    hero.memes["curiosity"] += 1
    friend.memes["friendship"] += 1
    friend.memes["care"] += 1
    helper.memes["calm"] += 1
    charm.meters["owned"] += 1
    charm.meters["visible"] += 1
    cause.meters["hidden"] += 1
    zone.meters["occupied"] += 1

    world.facts["cafe"] = CAFE_NAME
    world.facts["zone_phrase"] = zone_cfg.phrase
    world.facts["mystery_sound"] = mystery_cfg.sound_phrase
    world.facts["clue"] = mystery_cfg.clue
    world.facts["need"] = mystery_cfg.need
    world.facts["spot"] = _spot_for(zone_cfg, mystery_cfg.need)
    world.facts["helper_line"] = helper_cfg.comfort_line
    world.facts["seat"] = "the cocoa bench"
    return world


def enact_premise(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    charm = world.get("charm")

    hero.meters["dizzy"] += 1
    hero.meters["resting"] += 1
    hero.memes["trust"] += 1
    friend.meters["stayed_close"] += 1
    friend.memes["protectiveness"] += 1
    charm.meters["meaningful"] += 1
    world.event("premise", reason="fast_crossing_left_hero_dizzy")


def hear_mystery(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    charm = world.get("charm")
    cause = world.get(world.mystery_cfg.label)

    charm.location = world.facts["spot"]
    charm.meters["visible"] = 0
    charm.meters["missing"] += 1
    cause.meters["hidden_sound"] += 1
    hero.memes["suspense"] += 1
    friend.memes["suspense"] += 1
    friend.memes["helpfulness"] += 1
    world.event("mystery_heard", sound=world.mystery_cfg.sound_phrase, spot=world.facts["spot"])


def investigate(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    helper = world.get(world.helper_cfg.phrase)

    hero.memes["caution"] += 1
    hero.memes["certainty"] += 1
    friend.memes["hope"] += 1
    helper.memes["helpfulness"] += 1
    world.event("investigated", method=world.method_cfg.key, reason=world.method_cfg.safe_reason)


def resolve_mystery(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    helper = world.get(world.helper_cfg.phrase)
    charm = world.get("charm")
    cause = world.get(world.mystery_cfg.label)

    hero.meters["dizzy"] = 0
    hero.meters["steady"] += 1
    hero.meters["resting"] += 1
    hero.memes["relief"] += 1
    hero.memes["friendship"] += 1
    friend.memes["joy"] += 1
    friend.memes["friendship"] += 1
    helper.memes["relief"] += 1
    charm.location = "hero lanyard"
    charm.meters["missing"] = 0
    charm.meters["visible"] += 1
    cause.meters["hidden"] = 0
    cause.meters["quiet"] += 1
    world.facts["resolved"] = "yes"
    world.facts["truth"] = world.mystery_cfg.truth
    world.event("resolved", truth=world.mystery_cfg.truth)


def story_text(world: World) -> str:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    helper = world.get(world.helper_cfg.phrase)
    charm = world.get("charm")
    sound = world.facts["mystery_sound"]
    clue = world.facts["clue"]
    spot = world.facts["spot"]
    action = world.method_cfg.action_text.format(hero=hero.name, friend=friend.name, helper=helper.name)

    child_intro = "a girl" if world.params.gender == "girl" else "a boy"
    dizziness_line = (
        f"After one fast crossing, {hero.name} felt dizzy, so {friend.name} guided "
        f"{hero.pronoun('object')} to {world.facts['seat']} instead of begging for another turn."
    )
    ending_feeling = (
        f"{hero.name} felt steady again"
        if hero.meters["steady"] > 0
        else f"{hero.name} was still learning to feel steady"
    )
    friendship_line = (
        f"{friend.name} stayed so close that the mystery never had to belong to {hero.name} alone."
        if friend.meters["stayed_close"] > 0
        else f"{friend.name} watched from nearby."
    )

    world.say(
        f"Once upon a time, there was {child_intro} named {hero.name} who loved visiting {CAFE_NAME} with {friend.name}."
    )
    world.say(
        "The two friends shared a detective lanyard with a silver compass charm, because they liked pretending that friendship was the best tool in any mystery."
    )
    world.say(dizziness_line)
    world.say(f"From there they could see {world.zone_cfg.phrase}, where {world.zone_cfg.detail}.")

    world.para()
    world.say(f"That was when they heard {sound} coming from {world.zone_cfg.phrase}, even though no child was there.")
    world.say(
        f"{hero.name} touched {hero.pronoun('possessive')} neck and gasped. {charm.phrase.capitalize()} was gone."
    )
    world.say(friendship_line)
    world.say(clue)
    world.say(world.facts["helper_line"])

    world.para()
    world.say(f"So they decided to {world.method_cfg.phrase}. {action}")
    world.say(f"In {spot}, they found the missing charm and learned the truth. {world.mystery_cfg.truth}")
    world.say(world.mystery_cfg.why_here)
    world.say(world.mystery_cfg.final_fix)
    world.say(
        f"{ending_feeling}, and the suspense could no longer make the whole indoor play cafe feel huge. "
        f"{world.zone_cfg.ending_image} {world.mystery_cfg.final_image}"
    )
    return world.render()


def prompts_for(world: World) -> list[str]:
    return [
        'Write a child-friendly mystery story set in an indoor play cafe that uses the words "giggle" and "dizzy".',
        "Give the hero one close friend, one safe helper, and a missing object that turns a strange sound into a small mystery to solve.",
        "End with a concrete calm image that proves the suspense is over and the friendship has held.",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    return [
        QAItem(
            "Why did the mystery begin with a pause instead of a chase?",
            f"The mystery began with a pause because {hero.name} felt dizzy after the fast crossing and needed a steady seat first. That quiet moment let {friend.name} hear the hidden giggle clearly instead of turning the clue into a blur.",
        ),
        QAItem(
            "What important object went missing?",
            f"The missing object was the silver compass charm on the friends' detective lanyard. It mattered because the charm stood for their shared mystery games, so losing it felt like losing part of their teamwork too.",
        ),
        QAItem(
            "Where did the strange giggle come from?",
            f"The strange giggle came from {world.facts['spot']} in {world.zone_cfg.phrase}. That place matched the clue because this mystery needed a {world.facts['need']} kind of search.",
        ),
        QAItem(
            "How did the children solve the mystery safely?",
            f"They solved it by choosing to {world.method_cfg.phrase}. That method fit both the clue and the play space, so they could find the charm without rough grabbing or panicked rushing.",
        ),
        QAItem(
            "What was the true cause of the sound?",
            f"The true cause was ordinary once they could see it: {world.mystery_cfg.truth} The scary feeling shrank as soon as the hidden cause became a visible thing in the world.",
        ),
        QAItem(
            "How did friendship change the ending of the story?",
            f"Friendship changed the ending because {friend.name} stayed close when {hero.name} felt worried and dizzy. That steady kindness turned suspense into a shared puzzle instead of a lonely fright.",
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    items = [
        QAItem(
            "Why should a child rest after feeling dizzy on play equipment?",
            "Resting gives the body time to steady itself again. A calm body notices details better and is less likely to trip or rush into a bad choice.",
        ),
        QAItem(
            "Why is slowing down useful in a mystery?",
            "Slowing down gives clues time to repeat in a clear way. It also keeps excitement from becoming the loudest thing in the room.",
        ),
        QAItem(
            "How can friendship help in a suspenseful moment?",
            "A good friend can stay close, share courage, and help sort real clues from scared guesses. That kind of company makes a tense moment feel smaller and safer.",
        ),
    ]
    if world.mystery_cfg.need == "window":
        items.append(
            QAItem(
                "Why look through a clear panel before opening anything?",
                "A clear panel lets a detective study the shape of the clue first. That protects both the object and the play equipment from rough tugging.",
            )
        )
    elif world.mystery_cfg.need == "draft":
        items.append(
            QAItem(
                "Why can a ribbon reveal a hiding place?",
                "A ribbon leans with the same moving air that can push paper-light objects around. When it points to one spot again and again, the draft becomes a useful clue.",
            )
        )
    else:
        items.append(
            QAItem(
                "Why lift a blanket stack from both sides?",
                "Two-sided lifting keeps the stack balanced. Balance matters because tiny objects can slide deeper into folds when one side jerks up too fast.",
            )
        )
    return items


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    enact_premise(world)
    hear_mystery(world)
    investigate(world)
    resolve_mystery(world)
    story = story_text(world)
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print("\n")
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Indoor play cafe suspense friendship mystery world.")
    parser.add_argument("--zone", choices=sorted(ZONES))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--friend")
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.zone is None or combo[0] == args.zone)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.zone or "comet_tube",
                args.mystery or "clear_pocket_giggle",
                args.method or "trace_shadow_window",
            )
        )
    zone, mystery, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    friend_choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        zone=zone,
        mystery=mystery,
        method=method,
        hero=hero,
        gender=gender,
        friend=friend,
        helper=helper,
    )


ASP_RULES = r"""
combo(Z,Y,M) :-
  zone(Z), mystery(Y), method(M),
  mystery_zone(Y,Z), zone_method(Z,M),
  mystery_need(Y,N), method_solves(M,N),
  zone_need(Z,N), not method_unsafe(M).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for zone in ZONES.values():
        rows.append(asp.fact("zone", zone.key))
        for method in zone.supported_methods:
            rows.append(asp.fact("zone_method", zone.key, method))
        if zone.window_spot:
            rows.append(asp.fact("zone_need", zone.key, "window"))
        if zone.draft_spot:
            rows.append(asp.fact("zone_need", zone.key, "draft"))
        if zone.stack_spot:
            rows.append(asp.fact("zone_need", zone.key, "stack"))
    for mystery in MYSTERIES.values():
        rows.append(asp.fact("mystery", mystery.key))
        rows.append(asp.fact("mystery_need", mystery.key, mystery.need))
        for zone in mystery.zones:
            rows.append(asp.fact("mystery_zone", mystery.key, zone))
    for method in METHODS.values():
        rows.append(asp.fact("method", method.key))
        if method.unsafe:
            rows.append(asp.fact("method_unsafe", method.key))
        for need in method.solves:
            rows.append(asp.fact("method_solves", method.key, need))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def exercise_generated_stories() -> list[str]:
    problems: list[str] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            zone=combo[0],
            mystery=combo[1],
            method=combo[2],
            hero="Mira",
            gender="girl",
            friend="Jun",
            helper="nella",
            seed=2000 + i,
        )
        sample = generate(params)
        story = sample.story
        if "giggle" not in story.lower():
            problems.append(f"{combo}: story is missing the seed word 'giggle'")
        if "dizzy" not in story.lower():
            problems.append(f"{combo}: story is missing the seed word 'dizzy'")
        if "indoor play cafe" not in story.lower():
            problems.append(f"{combo}: story does not name the indoor play cafe setting")
        if "mystery" not in story.lower():
            problems.append(f"{combo}: story never names the mystery")
        if story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, turn, or ending paragraph")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world QA set is too small")
        if any(answer.answer.count(".") < 2 for answer in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if sample.world is None or sample.world.facts.get("resolved") != "yes":
            problems.append(f"{combo}: world never reaches a resolved state")
    return problems


def asp_verify() -> int:
    py = set(valid_combos())
    logic = set(asp_valid_combos())
    status = 0
    if py == logic:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between Python and ASP gate")
        if py - logic:
            print(f"  only python: {sorted(py - logic)}")
        if logic - py:
            print(f"  only asp: {sorted(logic - py)}")
        status = 1

    problems = exercise_generated_stories()
    if problems:
        print("Story exercise failures:")
        for item in problems:
            print(f"  {item}")
        status = 1
    else:
        print("OK: generated stories pass seed, structure, QA, and resolution checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    attempts = 0
    while len(samples) < target and attempts < target * 30:
        seed = base_seed + attempts
        attempts += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Not enough unique stories from the current indoor play cafe constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 29
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            zone=combo[0],
            mystery=combo[1],
            method=combo[2],
            hero="Mira",
            gender="girl",
            friend="Jun",
            helper="nella",
            seed=base_seed + i,
        )
        rows.append(generate(params))
    return rows


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.show_asp:
        print(asp_program("#show combo/3."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    if args.all:
        samples = _sample_all(args)
    else:
        samples = _sample_n(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
