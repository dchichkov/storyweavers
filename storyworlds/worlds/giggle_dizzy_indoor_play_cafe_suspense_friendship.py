#!/usr/bin/env python3
"""
Indoor play cafe mystery world.

Internal source tale
--------------------
Two friends visit an indoor play cafe and wear matching friendship badges.
After one fast spin leaves the hero dizzy, the friends pause instead of rushing.
That is when a tiny hidden giggle sounds from a nearby play zone and the hero
realizes the badge is missing. The pair solve the mystery with a safe,
place-matched method and learn that the odd sound came from an ordinary cause.
The ending image proves the cafe has gone calm again.
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


CAFE_NAME = "Pudding Planet Indoor Play Cafe"


@dataclass(frozen=True)
class PlayZone:
    key: str
    phrase: str
    detail: str
    ending_image: str
    supported_methods: tuple[str, ...]
    mesh_spot: str = ""
    breeze_spot: str = ""
    pair_spot: str = ""


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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

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
    "moon_spinner": PlayZone(
        key="moon_spinner",
        phrase="the moon-spinner corner beside the sock cubbies",
        detail="silver rails curved around a soft spinning disc, and the cloud cubbies smelled like clean socks and warm foam",
        ending_image="The silver spinner stood perfectly still, and the cloud cubbies waited in a neat pale row.",
        supported_methods=("check_mesh_pocket", "ask_host_unzip"),
        mesh_spot="the side mesh pocket tucked under the spinner rail",
    ),
    "rainbow_tube": PlayZone(
        key="rainbow_tube",
        phrase="the rainbow crawl tube above the cocoa tables",
        detail="mesh sides glowed under little star lights, and cocoa steam floated up from the tables below",
        ending_image="The star lights shone on the empty tube while cocoa steam curled in one slow ribbon below.",
        supported_methods=("ask_host_unzip", "follow_breeze"),
        mesh_spot="the service pocket beside the tube exit",
        breeze_spot="the vent ledge near the tube mouth",
    ),
    "story_loft": PlayZone(
        key="story_loft",
        phrase="the story loft over the reading rug",
        detail="fat floor cushions leaned under a low fan, and picture books slept in wooden bins beneath them",
        ending_image="The picture books rested square in their bins, and the low fan only stirred the page corners once.",
        breeze_spot="the little fan shelf behind the book bin",
        pair_spot="the wide cushion stack by the reading rug",
        supported_methods=("follow_breeze", "lift_cushions_together"),
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "pocket_koala": Mystery(
        key="pocket_koala",
        label="the pocket giggle",
        sound_phrase="a tiny giggle, then hush, then the same tiny giggle again",
        clue="The sound seemed to puff out between pauses, as if cloth were squeezing something small.",
        need="mesh",
        truth="Their comet friendship badge had slipped beside a tiny squeeze-koala toy, and each sway of the pocket made the toy let out that odd giggle.",
        why_here="The badge had snagged while the friends were climbing, so it stayed hidden where no one could see it from above.",
        final_fix="The helper unfastened the badge and tucked the little koala back into the toy bin.",
        final_image="No more giggle came from the pocket after that, only the soft hum of the cafe lights.",
        zones=("moon_spinner", "rainbow_tube"),
    ),
    "cocoa_lid": Mystery(
        key="cocoa_lid",
        label="the breezy laugh",
        sound_phrase="a papery giggle that skipped each time the fan breathed across the play zone",
        clue="A paper napkin tip kept twitching toward the same corner, even when nobody walked by.",
        need="breeze",
        truth="A cocoa cup lid was wobbling against the vent, and the missing badge was tucked under its rim where the air had pushed it.",
        why_here="The small draft was strong enough to scoot light things, but gentle enough to hide them in plain sight.",
        final_fix="The lid was dropped into the recycle bin, and the badge was clipped back where it belonged.",
        final_image="The strange laugh disappeared, and the air moved quietly enough to turn only one loose page.",
        zones=("rainbow_tube", "story_loft"),
    ),
    "cushion_chime": Mystery(
        key="cushion_chime",
        label="the hidden chime",
        sound_phrase="a muffled giggle-clink from somewhere deep in the cushion pile",
        clue="One cushion corner sat higher than the others, as if something small were trapped under it.",
        need="pair",
        truth="The badge's tiny bell had slipped into the cushion seam and was tapping a spoon from the snack tray whenever the pile rocked.",
        why_here="The friends had dropped onto the loft cushions in a rush before stopping to rest.",
        final_fix="Together they set the spoon back on the tray and smoothed the cushions flat again.",
        final_image="The cushion pile looked broad and sleepy, with not one secret sound hiding inside it.",
        zones=("story_loft",),
    ),
}

METHODS: dict[str, SearchMethod] = {
    "check_mesh_pocket": SearchMethod(
        key="check_mesh_pocket",
        phrase="press the outer mesh gently and look for a hidden shape",
        action_text=(
            "{friend} held the rail steady while {hero} pressed the mesh with two careful fingers. "
            "{helper} watched the pocket line so nothing was tugged too hard."
        ),
        safe_reason="It checks the shape from the outside first, so nobody jerks the play gear or startles what is inside.",
        solves=("mesh",),
    ),
    "ask_host_unzip": SearchMethod(
        key="ask_host_unzip",
        phrase="ask a grown-up to open the service flap",
        action_text=(
            "{hero} pointed to the sound, and {helper} unzipped the small service flap while {friend} kept the ladder clear. "
            "They all moved slowly enough to hear the clue instead of losing it."
        ),
        safe_reason="Only the grown-up opens the panel, which keeps the play structure and the children safe.",
        solves=("mesh",),
    ),
    "follow_breeze": SearchMethod(
        key="follow_breeze",
        phrase="hold still and follow the little breeze",
        action_text=(
            "{friend} flattened a napkin in the air while {hero} watched which way its corner leaned. "
            "{helper} nodded when the napkin pointed to the same place twice."
        ),
        safe_reason="A moving draft can reveal light objects without any climbing or grabbing.",
        solves=("breeze",),
    ),
    "lift_cushions_together": SearchMethod(
        key="lift_cushions_together",
        phrase="lift the cushion stack together from both sides",
        action_text=(
            "{hero} and {friend} each took one side of the cushion stack while {helper} slid the tray away first. "
            "They lifted slowly so anything hidden could stay put long enough to be seen."
        ),
        safe_reason="Lifting together keeps the pile balanced and stops small things from bouncing deeper into the seam.",
        solves=("pair",),
    ),
    "dash_after_sound": SearchMethod(
        key="dash_after_sound",
        phrase="race toward the noise",
        action_text="",
        safe_reason="Rushing is not safe in a play structure full of ladders, mesh, and other children.",
        solves=("mesh", "breeze", "pair"),
        unsafe=True,
    ),
}

HELPERS: dict[str, Helper] = {
    "cora": Helper(
        key="cora",
        phrase="Miss Cora the play host",
        comfort_line="Miss Cora whispered that mysteries feel smaller when everyone moves carefully.",
    ),
    "jules": Helper(
        key="jules",
        phrase="Mr. Jules from the cafe floor",
        comfort_line="Mr. Jules said the best clue is the one that stays put long enough to be noticed.",
    ),
    "mina": Helper(
        key="mina",
        phrase="Auntie Mina from the snack counter",
        comfort_line="Auntie Mina reminded them that a calm body can hear what a worried body misses.",
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Lina", "Maya", "Tessa", "Nori"),
    "boy": ("Eli", "Ravi", "Noah", "Theo"),
}

FRIEND_NAMES: tuple[str, ...] = ("Jun", "Pip", "Skye", "Remy", "Ari", "Tomi")


def _spot_for(zone: PlayZone, need: str) -> str:
    if need == "mesh":
        return zone.mesh_spot
    if need == "breeze":
        return zone.breeze_spot
    if need == "pair":
        return zone.pair_spot
    return ""


def _hero_kind(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def helper_phrase(key: str) -> str:
    return HELPERS[key].phrase


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
        return "No story: rushing toward a sound is not reasonable in this indoor play cafe."
    if zone not in mystery_cfg.zones:
        return f"No story: {mystery_cfg.label} does not fit {zone_cfg.phrase}."
    if method not in zone_cfg.supported_methods:
        return f"No story: {method_cfg.phrase} is not a supported search for {zone_cfg.phrase}."
    if mystery_cfg.need not in method_cfg.solves:
        return f"No story: this method does not solve a {mystery_cfg.need} clue."
    if not _spot_for(zone_cfg, mystery_cfg.need):
        return f"No story: {zone_cfg.phrase} has no valid hiding place for a {mystery_cfg.need} mystery."
    return "No story: this play cafe setup is not reasonable."


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
    hero = world.add(Entity(params.hero, _hero_kind(params.gender), params.hero, location="cloud bench"))
    friend = world.add(Entity(params.friend, "child", params.friend, location="cloud bench"))
    helper = world.add(Entity(helper_cfg.phrase, "adult", helper_cfg.phrase, location=params.zone))
    badge = world.add(Entity("badge", "object", "the comet friendship badge", location="hero shirt"))
    cause = world.add(Entity(mystery_cfg.label, "object", mystery_cfg.label, location=_spot_for(zone_cfg, mystery_cfg.need)))
    zone = world.add(Entity("zone", "place", zone_cfg.phrase, location=params.zone))

    hero.memes["friendship"] += 1
    hero.memes["curiosity"] += 1
    friend.memes["friendship"] += 1
    friend.memes["care"] += 1
    helper.memes["calm"] += 1
    badge.meters["owned"] += 1
    badge.meters["visible"] += 1
    cause.meters["hidden"] += 1
    zone.meters["occupied"] += 1

    world.facts["cafe"] = CAFE_NAME
    world.facts["zone_phrase"] = zone_cfg.phrase
    world.facts["mystery_sound"] = mystery_cfg.sound_phrase
    world.facts["clue"] = mystery_cfg.clue
    world.facts["need"] = mystery_cfg.need
    world.facts["spot"] = _spot_for(zone_cfg, mystery_cfg.need)
    world.facts["helper_line"] = helper_cfg.comfort_line
    return world


def enact_premise(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    badge = world.get("badge")

    hero.meters["dizzy"] += 1
    hero.meters["resting"] += 1
    friend.meters["stayed_close"] += 1
    badge.meters["meaningful"] += 1
    world.event("premise", reason="spinner_dizzy")


def hear_mystery(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    badge = world.get("badge")
    cause = world.get(world.mystery_cfg.label)

    badge.location = world.facts["spot"]
    badge.meters["visible"] = 0
    badge.meters["missing"] += 1
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
    world.event("investigated", method=world.method_cfg.key)


def resolve_mystery(world: World) -> None:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    helper = world.get(world.helper_cfg.phrase)
    badge = world.get("badge")
    cause = world.get(world.mystery_cfg.label)

    hero.meters["dizzy"] = 0
    hero.meters["resting"] += 1
    hero.memes["relief"] += 1
    hero.memes["friendship"] += 1
    friend.memes["joy"] += 1
    friend.memes["friendship"] += 1
    helper.memes["relief"] += 1
    badge.location = "hero shirt"
    badge.meters["missing"] = 0
    badge.meters["visible"] += 1
    cause.meters["hidden"] = 0
    cause.meters["quiet"] += 1
    world.facts["resolved"] = "yes"
    world.facts["truth"] = world.mystery_cfg.truth
    world.event("resolved", truth=world.mystery_cfg.truth)


def story_text(world: World) -> str:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    helper = world.get(world.helper_cfg.phrase)
    badge = world.get("badge")
    sound = world.mystery_cfg.sound_phrase
    clue = world.mystery_cfg.clue
    spot = world.facts["spot"]
    action = world.method_cfg.action_text.format(
        hero=hero.name,
        friend=friend.name,
        helper=helper.name,
    )

    child_intro = "a girl" if world.params.gender == "girl" else "a boy"
    world.say(
        f"Once upon a time, there was {child_intro} named {hero.name} who loved visits to {CAFE_NAME} with {friend.name}."
    )
    world.say(
        f"The two friends wore matching comet badges, because they liked to say that good detectives stay kind to each other while they solve things."
    )
    world.say(
        f"After one quick spin on the moon disc, {hero.name} felt dizzy, so {friend.name} guided {hero.pronoun('object')} to a cloud bench instead of begging for another turn."
    )
    world.say(
        f"From there they could see {world.zone_cfg.phrase}, where {world.zone_cfg.detail}."
    )

    world.para()
    world.say(
        f"That was when they heard {sound} coming from {world.zone_cfg.phrase}, even though no child was there."
    )
    world.say(
        f"{hero.name} touched {hero.pronoun('possessive')} shirt and gasped. {badge.phrase.capitalize()} was missing."
    )
    world.say(
        f"{friend.name} did not laugh or run ahead. {friend.name} stayed close, squeezed {hero.pronoun('possessive')} hand, and listened."
    )
    world.say(clue)
    world.say(world.helper_cfg.comfort_line)

    world.para()
    world.say(
        f"So they decided to {world.method_cfg.phrase}. {action}"
    )
    world.say(
        f"In {spot}, they found the badge and learned the truth. {world.mystery_cfg.truth}"
    )
    world.say(world.mystery_cfg.why_here)
    world.say(world.mystery_cfg.final_fix)
    world.say(
        f"{hero.name} was not dizzy anymore, and the mystery no longer felt big enough to swallow the room. {world.zone_cfg.ending_image} {world.mystery_cfg.final_image}"
    )
    return world.render()


def prompts_for(sample_world: World) -> list[str]:
    return [
        'Write a mystery story set in an indoor play cafe that uses the words "giggle" and "dizzy".',
        "Give two friends a missing-badge mystery, a careful helper, and one clue-matched search method.",
        "End with an image that proves the play cafe is calm again after the mystery is solved.",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    hero = world.get(world.params.hero)
    friend = world.get(world.params.friend)
    return [
        QAItem(
            "Why did the search begin with a pause instead of a race?",
            f"The search began with a pause because {hero.name} felt dizzy after spinning and needed to sit still first. That pause also let {friend.name} hear the hidden giggle clearly instead of turning the mystery into a blur.",
        ),
        QAItem(
            "What was missing?",
            f"The missing object was the comet friendship badge that {hero.name} and {friend.name} liked to wear together. It mattered because the badge stood for their teamwork, so finding it meant protecting the friendship memory as well as the object.",
        ),
        QAItem(
            "Where did the strange giggle come from?",
            f"The strange giggle came from {world.facts['spot']} in {world.zone_cfg.phrase}. That hiding place matched the clue because the mystery needed a {world.facts['need']} kind of search.",
        ),
        QAItem(
            "How did they solve the mystery?",
            f"They solved it by choosing to {world.method_cfg.phrase}. That method fit the place, so the clue stayed readable and the badge could be found without rough grabbing.",
        ),
        QAItem(
            "What was the true cause of the sound?",
            f"The true cause was simple: {world.mystery_cfg.truth} The suspense ended as soon as the hidden cause was seen in the open.",
        ),
        QAItem(
            "How did friendship change the ending?",
            f"Friendship changed the ending because {friend.name} stayed calm and close when {hero.name} felt worried. That steady help turned the mystery into a shared puzzle instead of a lonely scare.",
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    extras = [
        QAItem(
            "Why should a child rest after feeling dizzy from spinning?",
            "Resting gives the body time to steady itself again. A calm body notices clues better and is less likely to trip or rush.",
        ),
        QAItem(
            "Why is a grown-up the right person to open a service flap in a play structure?",
            "A grown-up knows which panels are safe to open and how to close them again. That protects both the children and the play equipment.",
        ),
        QAItem(
            "How can friendship help during a mystery?",
            "A good friend can slow the moment down, notice details, and share courage. Working together keeps worry from becoming the loudest thing in the room.",
        ),
    ]
    if world.mystery_cfg.need == "breeze":
        extras.append(
            QAItem(
                "Why can a small breeze reveal a clue?",
                "A light draft moves paper and other tiny objects in a repeatable way. That makes the air itself act like a pointer toward the hidden spot.",
            )
        )
    elif world.mystery_cfg.need == "mesh":
        extras.append(
            QAItem(
                "Why check the outside shape of a mesh pocket first?",
                "The outside shape can show whether something is caught without yanking on the pocket. That keeps hidden objects from falling deeper or breaking loose in a rush.",
            )
        )
    else:
        extras.append(
            QAItem(
                "Why lift a cushion pile from both sides?",
                "Two-sided lifting keeps the pile balanced. Balance matters because small objects can slide farther away when one side jerks up too fast.",
            )
        )
    return extras


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
    parser = argparse.ArgumentParser(description="Indoor play cafe friendship mystery world.")
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
        combo for combo in valid_combos()
        if (args.zone is None or combo[0] == args.zone)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.zone or "moon_spinner",
                args.mystery or "pocket_koala",
                args.method or "check_mesh_pocket",
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
        if zone.mesh_spot:
            rows.append(asp.fact("zone_need", zone.key, "mesh"))
        if zone.breeze_spot:
            rows.append(asp.fact("zone_need", zone.key, "breeze"))
        if zone.pair_spot:
            rows.append(asp.fact("zone_need", zone.key, "pair"))
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
            hero="Lina",
            gender="girl",
            friend="Jun",
            helper="cora",
            seed=1000 + i,
        )
        sample = generate(params)
        story = sample.story
        if "giggle" not in story.lower():
            problems.append(f"{combo}: story is missing the seed word 'giggle'")
        if "dizzy" not in story.lower():
            problems.append(f"{combo}: story is missing the seed word 'dizzy'")
        if "indoor play cafe" not in story.lower():
            problems.append(f"{combo}: story does not name the indoor play cafe setting")
        if story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, turn, or ending paragraph")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world QA set is too small")
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
    base_seed = args.seed if args.seed is not None else 17
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            zone=combo[0],
            mystery=combo[1],
            method=combo[2],
            hero="Maya",
            gender="girl",
            friend="Jun",
            helper="cora",
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
