#!/usr/bin/env python3
"""
storyworlds/worlds/wondrous_bush_whispering_tower_fire_station_surprise.py
==========================================================================

Standalone storyworld for a seed prompt:

    Words: wondrous bush, whispering tower
    Setting: fire station
    Features: Surprise, Reconciliation
    Style: Pirate Tale

Internal source tale
--------------------
Two children help at a fire station that feels, to them, like a ship in harbor.
In the yard stands a wondrous bush covered with old thank-you ribbons, and over
the station rises a whispering tower whose brass tube hums in the wind. One
child finds a clue from a secret surprise the other child is preparing and
mistakes it for proof of mischief. While hurt feelings spread, the children
search together, discover the real physical trouble in the station gear, fix it,
and then reveal the hidden surprise. The ending image must prove both the station
and the friendship have been set right.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
STATION_NAME = "Harbor Bell Fire Station"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    location: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Clue:
    id: str
    mark: str
    clue_text: str
    accusation: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Cause:
    id: str
    need: str
    hint_text: str
    discovery: str
    risk_text: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Fix:
    id: str
    need: str
    action_text: str
    qa_text: str
    result_text: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class SurprisePlan:
    id: str
    mark: str
    hidden_work: str
    recipient: str
    reveal_text: str
    final_image: str
    tags: tuple[str, ...]


@dataclass
class StoryParams:
    clue: str
    cause: str
    fix: str
    surprise: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    captain: str
    captain_gender: str
    hero_trait: str
    seed: int | None = None


@dataclass
class Rule:
    name: str
    apply: callable


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[dict[str, str]] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def note(self, event: str, **fields: str) -> None:
        row = {"event": event}
        row.update({k: str(v) for k, v in fields.items()})
        self.history.append(row)

    def render(self) -> str:
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for ent in self.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            lines.append(
                f"  {ent.id:16} ({ent.type:10}) role={ent.role or '-':10} "
                f"location={ent.location or '-':18} meters={meters} memes={memes}"
            )
        lines.append(f"  facts={self.facts}")
        lines.append(f"  fired={sorted(self.fired)}")
        lines.append("  history:")
        for row in self.history:
            lines.append(f"    {row}")
        return "\n".join(lines)


CLUES: dict[str, Clue] = {
    "red_ribbon": Clue(
        "red_ribbon",
        "red_ribbon",
        "a curl of red rescue ribbon caught low on the wondrous bush",
        "You took station ribbon for some secret game and left the tower to croak.",
        ("ribbon", "clue"),
    ),
    "brass_hook": Clue(
        "brass_hook",
        "brass_hook",
        "a tiny brass hook glinting under the tower stairs",
        "You borrowed a bell hook without asking and muddled the gear.",
        ("brass", "clue"),
    ),
    "blue_chalk": Clue(
        "blue_chalk",
        "blue_chalk",
        "a blue chalk star on the step beside the hose rack",
        "You marked the yard for mischief and forgot the station job.",
        ("chalk", "clue"),
    ),
}


CAUSES: dict[str, Cause] = {
    "leaf_in_tube": Cause(
        "leaf_in_tube",
        "clear_tube",
        "When the noon breeze turned, the whispering tower wheezed instead of singing its bright harbor note.",
        "a glossy leaf from the wondrous bush had sailed into the brass speaking tube and folded there like a wet green sail",
        "the crew might miss a clear call across the yard if the tube stayed choked",
        ("tower", "bush", "wind"),
    ),
    "snagged_line": Cause(
        "snagged_line",
        "untangle_line",
        "The signal pennant jerked halfway up the tower and hung there crooked as a tired mast rope.",
        "the practice halyard had looped around a hose nozzle on the tower rail and would not run free",
        "the station could not raise a clean drill signal while the line was snagged",
        ("tower", "line", "gear"),
    ),
    "sooty_clapper": Cause(
        "sooty_clapper",
        "polish_bell",
        "The yard bell gave only a dull clonk, as if it had a blanket wrapped around its voice.",
        "the bell clapper wore a soft coat of soot left by yesterday's smoky ladder drill",
        "the crew might miss a practice call if the bell stayed muffled",
        ("bell", "soot", "gear"),
    ),
}


FIXES: dict[str, Fix] = {
    "clear_tube": Fix(
        "clear_tube",
        "clear_tube",
        "Together they slid the swab rod through the brass tube, eased the leaf free, and blew one clean test note across the yard.",
        "cleared the leaf from the brass speaking tube",
        "The next breeze ran through the tower in one smooth whistle.",
        ("tower", "repair"),
    ),
    "untangle_line": Fix(
        "untangle_line",
        "untangle_line",
        "They lowered the halyard, slipped it loose from the hose nozzle, and hauled it straight again hand over hand.",
        "untangled the practice halyard from the tower rail",
        "The pennant rose neat and true, with no jerking at all.",
        ("tower", "repair"),
    ),
    "polish_bell": Fix(
        "polish_bell",
        "polish_bell",
        "They rubbed the clapper with an oiled rag until the brass shone and the bell answered with a brave, bright ring.",
        "polished the soot from the bell clapper",
        "The bell spoke out clear enough for every corner of the yard.",
        ("bell", "repair"),
    ),
}


SURPRISES: dict[str, SurprisePlan] = {
    "crew_banner": SurprisePlan(
        "crew_banner",
        "red_ribbon",
        "stringing a thank-you banner from the whispering tower rail down to the wondrous bush",
        "the tired night crew",
        "the red ribbon was not stolen at all; it belonged to a secret thank-you banner for the tired night crew",
        "The banner fluttered between the tower and the wondrous bush like a happy signal flag while the night crew laughed and waved.",
        ("surprise", "ribbon", "crew"),
    ),
    "bell_chimes": SurprisePlan(
        "bell_chimes",
        "brass_hook",
        "hanging tiny brass chimes in the wondrous bush",
        "Captain Roan after a hard rescue shift",
        "the brass hook was only part of a row of tiny wind chimes meant to welcome Captain Roan home from a hard rescue shift",
        "The wondrous bush sang with bright brass tink-tinks while Captain Roan stood smiling beneath it.",
        ("surprise", "brass", "captain"),
    ),
    "chalk_map": SurprisePlan(
        "chalk_map",
        "blue_chalk",
        "drawing a treasure path of blue stars from the engine bay to the wondrous bush and up toward the whispering tower",
        "the station's new rescue pup, Spark",
        "the blue chalk star was the first mark in a treasure path for Spark, the station's new rescue pup",
        "Blue chalk stars curled around the yard, and Spark bounded from one to the next until the whole crew clapped.",
        ("surprise", "chalk", "pup"),
    ),
}


GIRL_NAMES = ["Mira", "Nell", "Tess", "Lina", "June", "Poppy"]
BOY_NAMES = ["Finn", "Jory", "Theo", "Pip", "Bram", "Nico"]
TRAITS = ["eager", "bold", "quick", "proud", "curious", "steady"]


def clue_matches_surprise(clue: Clue, surprise: SurprisePlan) -> bool:
    return clue.mark == surprise.mark


def fix_matches_cause(cause: Cause, fix: Fix) -> bool:
    return cause.need == fix.need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for clue_id, clue in CLUES.items():
        for cause_id, cause in CAUSES.items():
            for fix_id, fix in FIXES.items():
                for surprise_id, surprise in SURPRISES.items():
                    if clue_matches_surprise(clue, surprise) and fix_matches_cause(cause, fix):
                        combos.append((clue_id, cause_id, fix_id, surprise_id))
    return sorted(combos)


def explain_rejection(clue: Clue, cause: Cause, fix: Fix, surprise: SurprisePlan) -> str:
    if not clue_matches_surprise(clue, surprise):
        return (
            f"(No story: {clue.id} leaves the mark '{clue.mark}', but {surprise.id} uses "
            f"'{surprise.mark}'. The clue must come from the hidden surprise.)"
        )
    return (
        f"(No story: {cause.id} needs '{cause.need}', but {fix.id} provides "
        f"'{fix.need}'. The children must fix the real physical trouble.)"
    )


def _rule_quarrel_hushes_yard(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    tower = world.get("tower")
    if hero.memes["accusing"] < THRESHOLD or friend.memes["hurt"] < THRESHOLD:
        return []
    if "quarrel_hushes_yard" in world.fired:
        return []
    world.fired.add("quarrel_hushes_yard")
    tower.meters["tense"] += 1
    hero.memes["distance"] += 1
    friend.memes["distance"] += 1
    world.note("quarrel_hushes_yard", hero=hero.id, friend=friend.id)
    return []


def _rule_repair_steadies_station(world: World) -> list[str]:
    tower = world.get("tower")
    bell = world.get("bell")
    if tower.meters["fixed"] < THRESHOLD:
        return []
    if "repair_steadies_station" in world.fired:
        return []
    world.fired.add("repair_steadies_station")
    tower.meters["troubled"] = 0.0
    tower.meters["ready"] += 1
    bell.meters["ready"] += 1
    world.note("repair_steadies_station")
    return []


def _rule_apology_restores_crew(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    bush = world.get("bush")
    if hero.memes["apology"] < THRESHOLD or bush.meters["surprise_revealed"] < THRESHOLD:
        return []
    if "apology_restores_crew" in world.fired:
        return []
    world.fired.add("apology_restores_crew")
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["distance"] = 0.0
    friend.memes["distance"] = 0.0
    bush.meters["celebration"] += 1
    world.note("apology_restores_crew", hero=hero.id, friend=friend.id)
    return []


RULES = [
    Rule("quarrel_hushes_yard", _rule_quarrel_hushes_yard),
    Rule("repair_steadies_station", _rule_repair_steadies_station),
    Rule("apology_restores_crew", _rule_apology_restores_crew),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            before = set(world.fired)
            rule.apply(world)
            if world.fired != before:
                changed = True


def introduce(world: World, hero: Entity, friend: Entity, captain: Entity, surprise: SurprisePlan) -> None:
    bush = world.get("bush")
    tower = world.get("tower")
    hero.memes["duty"] += 1
    friend.memes["secret_surprise"] += 1
    bush.meters["glitter"] += 1
    tower.meters["troubled"] += 1
    world.say(
        f"At {STATION_NAME}, {hero.id} liked to pretend the red engine bays were a harbor and the ladder truck was a proud rescue ship."
    )
    world.say(
        f"In the little yard stood the wondrous bush, shining with old thank-you ribbons, and above it rose the whispering tower where the wind talked through a brass tube."
    )
    world.say(
        f"{captain.id} called the children the station's smallest deck crew, so {hero.id} and {friend.id} swept the floor, coiled hose, and kept one eye on the yard."
    )
    world.note(
        "beginning",
        hero=hero.id,
        friend=friend.id,
        captain=captain.id,
        surprise=surprise.id,
    )


def trouble_appears(world: World, hero: Entity, friend: Entity, clue: Clue, cause: Cause) -> None:
    tower = world.get("tower")
    tower.meters["whispering"] += 1
    world.say(cause.hint_text)
    world.say(
        f"Then {hero.id} spotted {clue.clue_text}. {hero.pronoun().capitalize()} remembered that {friend.id} had been sneaking in and out of the yard all morning with a private look on {friend.pronoun('possessive')} face."
    )
    hero.memes["accusing"] += 1
    friend.memes["hurt"] += 1
    propagate(world)
    world.say(
        f'"{friend.id}," {hero.id} burst out, "{clue.accusation}"'
    )
    world.say(
        f"{friend.id} went still. \"I was not trying to spoil anything,\" {friend.pronoun()} said, and that answer, though true, sounded secretive enough to sting."
    )
    world.note("accusation", clue=clue.id, cause=cause.id, hero=hero.id, friend=friend.id)


def captain_warns(world: World, captain: Entity, cause: Cause) -> None:
    world.say(
        f'{captain.id} stepped from the engine bay and tapped the bell post once. "A good crew checks the whole deck before pointing a finger," {captain.pronoun()} said. "If we leave this as it is, {cause.risk_text}."'
    )
    world.note("warning", captain=captain.id, risk=cause.id)


def investigate_and_fix(world: World, hero: Entity, friend: Entity, cause: Cause, fix: Fix) -> None:
    tower = world.get("tower")
    bell = world.get("bell")
    hero.memes["curiosity"] += 1
    friend.memes["courage"] += 1
    world.say(
        f"So the two children searched together from the hose rack to the tower stairs, quiet now except for the gull-like wind and the station's sleepy creaks."
    )
    world.say(
        f"At last they found the real trouble: {cause.discovery}."
    )
    tower.meters["trouble_found"] += 1
    bell.meters["needs_help"] += 1
    world.note("discovery", cause=cause.id, discovery=cause.discovery)
    world.say(fix.action_text)
    tower.meters["fixed"] += 1
    bell.meters["repaired"] += 1
    propagate(world)
    world.say(fix.result_text)
    world.note("repair", fix=fix.id, result=fix.result_text)


def reveal_surprise(world: World, hero: Entity, friend: Entity, captain: Entity, surprise: SurprisePlan) -> None:
    bush = world.get("bush")
    bush.meters["surprise_revealed"] += 1
    world.say(
        f"That was when {hero.id} noticed the rest of the hidden things tucked behind the water barrel. {captain.id} smiled and let the secret out: {surprise.reveal_text}."
    )
    world.say(
        f"{friend.id} had been {surprise.hidden_work} as a surprise for {surprise.recipient}."
    )
    world.note("surprise_revealed", surprise=surprise.id, recipient=surprise.recipient)


def reconcile(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["apology"] += 1
    propagate(world)
    world.say(
        f'"I am sorry I blamed you before I knew the whole tale," {hero.id} said. "{friend.id}, will you let me help?"'
    )
    world.say(
        f"{friend.id}'s face softened. \"Aye,\" {friend.pronoun()} said. \"A crew works best side by side.\""
    )
    world.note("reconciliation", hero=hero.id, friend=friend.id)


def closing(world: World, hero: Entity, friend: Entity, surprise: SurprisePlan) -> None:
    bush = world.get("bush")
    tower = world.get("tower")
    if bush.meters["celebration"] >= THRESHOLD and tower.meters["ready"] >= THRESHOLD:
        world.say(
            f"By supper time the whispering tower had its clear voice back, the bell gear was true, and {hero.id} with {friend.id} finished the secret work together."
        )
        world.say(surprise.final_image)
        world.say(
            f"{hero.id} thought the station looked less like a quarrelsome dock and more like a brave little fleet again, all because the crew had fixed the real trouble and made peace."
        )
    world.facts["reconciled"] = bush.meters["celebration"] >= THRESHOLD
    world.facts["surprise_revealed"] = bush.meters["surprise_revealed"] >= THRESHOLD
    world.note("ending", reconciled=str(world.facts["reconciled"]), surprise=str(world.facts["surprise_revealed"]))


def tell(params: StoryParams) -> World:
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    fix = FIXES[params.fix]
    surprise = SURPRISES[params.surprise]
    world = World(params)
    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type=params.hero_gender,
            label=params.hero,
            role="hero",
            location="engine_bay",
            traits=[params.hero_trait],
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type=params.friend_gender,
            label=params.friend,
            role="friend",
            location="yard",
            traits=["kind"],
        )
    )
    captain = world.add(
        Entity(
            id=params.captain,
            kind="character",
            type=params.captain_gender,
            label=params.captain,
            role="captain",
            location="engine_bay",
            traits=["steady"],
        )
    )
    world.add(Entity("tower", type="tower", label="whispering tower", role="tower", location="yard"))
    world.add(Entity("bush", type="bush", label="wondrous bush", role="bush", location="yard"))
    world.add(Entity("bell", type="bell", label="yard bell", role="bell", location="yard"))

    introduce(world, hero, friend, captain, surprise)
    world.para()
    trouble_appears(world, hero, friend, clue, cause)
    captain_warns(world, captain, cause)
    world.para()
    investigate_and_fix(world, hero, friend, cause, fix)
    reveal_surprise(world, hero, friend, captain, surprise)
    reconcile(world, hero, friend)
    closing(world, hero, friend, surprise)

    world.facts.update(
        clue=clue.id,
        cause=cause.id,
        fix=fix.id,
        surprise=surprise.id,
        hero=hero.id,
        friend=friend.id,
        captain=captain.id,
        station=STATION_NAME,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    return [
        'Write a pirate tale for young children set in a fire station that includes the exact phrases "wondrous bush" and "whispering tower" and uses surprise plus reconciliation.',
        f"Tell a story in which {hero.id} wrongly blames {friend.id} after finding a clue near a wondrous bush, then the children fix the real station problem together and make peace.",
        "Write a gentle harbor-flavored station adventure where the drill tower whispers, a hidden surprise is revealed, and the ending image proves both the gear and the friendship are restored.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    clue = CLUES[str(world.facts["clue"])]
    cause = CAUSES[str(world.facts["cause"])]
    fix = FIXES[str(world.facts["fix"])]
    surprise = SURPRISES[str(world.facts["surprise"])]
    hero = world.get("hero")
    friend = world.get("friend")
    captain = world.get("captain")
    return [
        (
            "Where does the story happen?",
            f"It happens at {STATION_NAME}, in the yard with the wondrous bush and the whispering tower. The children treat the station like a little harbor ship while they work.",
        ),
        (
            f"Why did {hero.id} blame {friend.id}?",
            f"{hero.id} found {clue.clue_text} and thought it proved {friend.id} had been careless. {friend.id} was hiding a kind surprise, so the secret made the clue look worse than it really was.",
        ),
        (
            "What was the real physical trouble?",
            f"The real trouble was that {cause.discovery}. That is why the station gear sounded wrong before the surprise was ever revealed.",
        ),
        (
            "How did the children fix the station?",
            f"They {fix.qa_text}. After the repair, {fix.result_text.lower()}",
        ),
        (
            f"What was the surprise?",
            f"The surprise was that {friend.id} had been {surprise.hidden_work} as a surprise for {surprise.recipient}. The clue came from that secret work, not from mischief.",
        ),
        (
            "How did the story end?",
            f"{hero.id} apologized, and {friend.id} let the friendship mend. Then the repaired station and the revealed surprise made the yard feel bright and welcoming again.",
        ),
    ]


KNOWLEDGE = {
    "fire_station": (
        "What is a fire station?",
        "A fire station is the place where firefighters keep their trucks, tools, and gear. It is also where they rest, train, and get ready to help people fast.",
    ),
    "tower": (
        "Why might a fire station have a tower?",
        "A tower gives firefighters a place to train with ladders, ropes, or drying hose. In stories, it can also become a dramatic lookout or signal place.",
    ),
    "reconciliation": (
        "What does reconciliation mean?",
        "Reconciliation means people make peace after hurt feelings or a quarrel. They listen, tell the truth, and choose friendship again.",
    ),
    "surprise": (
        "What makes a surprise kind instead of mean?",
        "A kind surprise is meant to delight or comfort someone. It should not leave real harm behind for other people to clean up.",
    ),
    "bell": (
        "Why is a clear bell useful in a station yard?",
        "A clear bell can call people together quickly. Loud, simple signals matter when many people need to notice the same thing at once.",
    ),
    "clue": (
        "Can a clue be real and still be misunderstood?",
        "Yes. A clue can show that something happened nearby without proving the whole story. That is why people still need patience and careful checking.",
    ),
}


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags = {"fire_station", "tower", "reconciliation", "surprise", "clue"}
    if "bell" in CAUSES[str(world.facts["cause"])].tags:
        tags.add("bell")
    ordered = ["fire_station", "tower", "reconciliation", "surprise", "bell", "clue"]
    return [KNOWLEDGE[tag] for tag in ordered if tag in tags]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: wondrous bush, whispering tower, fire station surprise. Unspecified choices are randomized."
    )
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["woman", "man"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.surprise:
        clue = CLUES[args.clue]
        surprise = SURPRISES[args.surprise]
        if not clue_matches_surprise(clue, surprise):
            cause = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
            fix = FIXES[args.fix] if args.fix else FIXES[cause.need]
            raise StoryError(explain_rejection(clue, cause, fix, surprise))
    if args.cause and args.fix:
        cause = CAUSES[args.cause]
        fix = FIXES[args.fix]
        if not fix_matches_cause(cause, fix):
            clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
            surprise = SURPRISES[args.surprise] if args.surprise else SURPRISES["crew_banner"]
            raise StoryError(explain_rejection(clue, cause, fix, surprise))

    combos = [
        combo
        for combo in valid_combos()
        if (args.clue is None or combo[0] == args.clue)
        and (args.cause is None or combo[1] == args.cause)
        and (args.fix is None or combo[2] == args.fix)
        and (args.surprise is None or combo[3] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    clue_id, cause_id, fix_id, surprise_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    captain_gender = args.captain_gender or rng.choice(["woman", "man"])
    captain = args.captain or ("Captain Roan" if captain_gender == "man" else "Captain Nessa")
    return StoryParams(
        clue=clue_id,
        cause=cause_id,
        fix=fix_id,
        surprise=surprise_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        captain=captain,
        captain_gender=captain_gender,
        hero_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_pairs(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
clue_matches_surprise(Clue, Surprise) :-
    clue(Clue), surprise(Surprise),
    clue_mark(Clue, Mark), surprise_mark(Surprise, Mark).

fix_matches_cause(Cause, Fix) :-
    cause(Cause), fix(Fix),
    cause_need(Cause, Need), fix_need(Fix, Need).

valid(Clue, Cause, Fix, Surprise) :-
    clue_matches_surprise(Clue, Surprise),
    fix_matches_cause(Cause, Fix).
"""


def asp_facts() -> str:
    from storyworlds import asp

    lines: list[str] = []
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_mark", clue_id, clue.mark))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_need", cause_id, cause.need))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_need", fix_id, fix.need))
    for surprise_id, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", surprise_id))
        lines.append(asp.fact("surprise_mark", surprise_id, surprise.mark))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams("red_ribbon", "leaf_in_tube", "clear_tube", "crew_banner", "Tess", "girl", "Finn", "boy", "Captain Nessa", "woman", "eager"),
    StoryParams("brass_hook", "snagged_line", "untangle_line", "bell_chimes", "Jory", "boy", "Mira", "girl", "Captain Roan", "man", "curious"),
    StoryParams("blue_chalk", "sooty_clapper", "polish_bell", "chalk_map", "June", "girl", "Theo", "boy", "Captain Nessa", "woman", "bold"),
]


def verify_story(sample: StorySample) -> None:
    if "wondrous bush" not in sample.story:
        raise StoryError("verify: story is missing 'wondrous bush'")
    if "whispering tower" not in sample.story:
        raise StoryError("verify: story is missing 'whispering tower'")
    if "fire station" not in sample.story.lower():
        raise StoryError("verify: story is missing the fire station setting")
    if not sample.prompts or not sample.story_qa or not sample.world_qa:
        raise StoryError("verify: story did not produce all QA sets")
    if sample.world is None:
        raise StoryError("verify: world object missing")
    if not sample.world.facts.get("reconciled"):
        raise StoryError("verify: reconciliation did not land")
    if not sample.world.facts.get("surprise_revealed"):
        raise StoryError("verify: surprise was not revealed")


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set != clingo_set:
        print("MISMATCH between Python gate and ASP gate:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in asp:", sorted(clingo_set - python_set))
        return 1

    try:
        for params in CURATED:
            sample = generate(params)
            verify_story(sample)
    except StoryError as err:
        print(err)
        return 1

    print(f"OK: ASP parity matches Python gate ({len(python_set)} combos).")
    print(f"OK: exercised {len(CURATED)} curated stories successfully.")
    return 0


def all_params() -> list[StoryParams]:
    samples: list[StoryParams] = []
    fixed_names = [
        ("Tess", "girl", "Finn", "boy", "Captain Nessa", "woman", "eager"),
        ("Jory", "boy", "Mira", "girl", "Captain Roan", "man", "curious"),
        ("June", "girl", "Theo", "boy", "Captain Nessa", "woman", "bold"),
    ]
    for i, combo in enumerate(valid_combos()):
        names = fixed_names[i % len(fixed_names)]
        samples.append(
            StoryParams(
                clue=combo[0],
                cause=combo[1],
                fix=combo[2],
                surprise=combo[3],
                hero=names[0],
                hero_gender=names[1],
                friend=names[2],
                friend_gender=names[3],
                captain=names[4],
                captain_gender=names[5],
                hero_trait=names[6],
                seed=i,
            )
        )
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (clue, cause, fix, surprise) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in all_params()]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend}: {p.clue} / {p.cause} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
