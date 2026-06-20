#!/usr/bin/env python3
"""A splash-pad mystery about a meadow path, a crystal door, and patient problem solving.

Internal source tale:
At a meadow-themed splash pad, two children love opening a crystal door that
slides aside when the water path is balanced. One afternoon the door stays shut.
A repeating clue in the water pattern makes the children suspect magic, but a
careful helper teaches them to test the clue instead of guessing. They find one
small physical fault, fix it with the right tool, and prove the mystery is
solved when the whole meadow path lights and the crystal door opens.
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
class SplashPad:
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
class Fault:
    key: str
    place: str
    kind: str
    motion: str
    discovery: str
    result: str


@dataclass(frozen=True)
class Fix:
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
    splash_pad: str
    clue: str
    fault: str
    fix: str
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
class MysteryWorld:
    params: StoryParams
    splash_pad: SplashPad
    clue: Clue
    fault: Fault
    fix: Fix
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | float] = field(default_factory=dict)

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


SPLASH_PADS: dict[str, SplashPad] = {
    "daisy_drift": SplashPad(
        key="daisy_drift",
        name="Daisy Drift",
        opening="At Daisy Drift, the splash pad floor curved through a painted meadow of white petals, and slim water lines skipped from stone to stone like silver grasshoppers.",
        reward="the silver lily ring",
        ending_image="the silver lily ring sprayed a bright round crown while the open crystal door cast clean blue squares onto the wet meadow tiles",
        sites=("plate", "sensor"),
    ),
    "fern_loop": SplashPad(
        key="fern_loop",
        name="Fern Loop",
        opening="At Fern Loop, green frond tiles wound around the splash pad in a cool meadow spiral, and a soft mist kept brushing everyone's ankles.",
        reward="the moonflower tunnel",
        ending_image="the moonflower tunnel arched over them in sparkling loops while the crystal door stood open beside the fern wall",
        sites=("valve", "sensor"),
    ),
    "thistle_turn": SplashPad(
        key="thistle_turn",
        name="Thistle Turn",
        opening="At Thistle Turn, purple seed tiles made the splash pad look like a windy meadow, and the little jets clicked in a neat circle before every big burst.",
        reward="the tall reed fan",
        ending_image="the tall reed fan rose in a shining sheet while the crystal door flashed like morning ice at the edge of the pad",
        sites=("plate", "valve"),
    ),
}

CLUES: dict[str, Clue] = {
    "crooked_star": Clue(
        key="crooked_star",
        place="plate",
        text="One star-shaped stepping plate stayed dull while the rest of the meadow path flashed bright under the water.",
        hint="Each new cycle made the same star lag behind, as if the path kept pointing to one quiet stone.",
        false_guess="For a moment the children wondered whether the crystal door was refusing them on purpose, but the same quiet star kept giving the same answer.",
    ),
    "silver_blink": Clue(
        key="silver_blink",
        place="sensor",
        text="A tiny silver blink kept sliding across one clear sensor eye beside the crystal door frame.",
        hint="The blink returned whenever mist touched that corner, so it felt less like magic and more like a message from the same place.",
        false_guess="The shining blink looked like a secret spell at first, yet it kept landing on one real piece of hardware instead of floating anywhere it liked.",
    ),
    "humming_bend": Clue(
        key="humming_bend",
        place="valve",
        text="A low humming note kept starting under one meadow bench and then cutting off before the water path finished waking up.",
        hint="The hum always bent toward the same service nook, as if the pipes were trying to point with sound.",
        false_guess="The children first thought someone must be hiding and making the noise, but the hum returned even when the whole nook was empty.",
    ),
}

FAULTS: dict[str, Fault] = {
    "pebble_jam": Fault(
        key="pebble_jam",
        place="plate",
        kind="jam",
        motion="A smooth pebble was wedged beneath the stepping plate, so the water path could not feel the last press it needed to wake the crystal door.",
        discovery="When they lifted the edge a little, they saw a trapped pebble holding the star plate up like a tiny hard tooth.",
        result="Once the pebble was out, the star plate settled flat and the next water pulse completed the whole meadow path.",
    ),
    "sunscreen_glaze": Fault(
        key="sunscreen_glaze",
        place="sensor",
        kind="film",
        motion="A pale sunscreen glaze had dried across the sensor eye, so the crystal door kept missing the clean water signal it was waiting for.",
        discovery="In the clear panel light, a cloudy smear sat over the sensor eye like a thumbprint that had turned to chalk.",
        result="As soon as the cloudy glaze was wiped away, the sensor flashed blue and the door finally trusted the signal.",
    ),
    "kinked_feed": Fault(
        key="kinked_feed",
        place="valve",
        kind="kink",
        motion="A bent feed hose behind the service nook was pinching the flow, so the last meadow jets never gathered enough push to trigger the crystal door.",
        discovery="Behind the bench, the helper showed them a hose folded into a hard bend where the humming line should have run smooth.",
        result="When the bend was eased out, the hum opened into a steady rush and the final jets rose together.",
    ),
}

FIXES: dict[str, Fix] = {
    "foam_key": Fix(
        key="foam_key",
        solves="jam",
        tool="the foam service key",
        action="{first} held the edge of the star plate steady while {second} slid the foam service key under the lip and nudged the pebble into {helper_possessive} waiting hand.",
        proof="The plate settled with one clean click instead of a wobble, and the dark star immediately brightened with running water.",
        lesson="They solved the mystery by fixing the tiny part that kept the whole path from finishing its pattern.",
    ),
    "mist_cloth": Fix(
        key="mist_cloth",
        solves="film",
        tool="a mist bottle and a soft cloth",
        action="{helper} passed them {tool}. {second} sprayed a light rinse while {first} wiped the sensor eye in slow careful circles until the cloudy patch disappeared.",
        proof="The silver blink vanished, and the little eye answered with a true blue flash instead of a dull shine.",
        lesson="They solved the mystery by cleaning the exact place the clue kept naming.",
    ),
    "hose_cradle": Fix(
        key="hose_cradle",
        solves="kink",
        tool="the yellow hose cradle",
        action="{first} lifted the bent hose while {second} slipped the yellow hose cradle beneath it, and {helper} checked that the line lay in one long smooth curve.",
        proof="The cut-off hum stretched into one steady note, and the far meadow jets stopped sputtering and stood up straight.",
        lesson="They solved the mystery by giving the water line the shape it needed to do its job.",
    ),
}

TEAMS: dict[str, TeamChoice] = {
    "aya_miles": TeamChoice("aya_miles", "Aya", "girl", "Miles", "boy"),
    "nia_ben": TeamChoice("nia_ben", "Nia", "girl", "Ben", "boy"),
    "suri_jude": TeamChoice("suri_jude", "Suri", "girl", "Jude", "boy"),
    "zoe_cal": TeamChoice("zoe_cal", "Zoe", "girl", "Cal", "boy"),
}

HELPERS: dict[str, HelperChoice] = {
    "marisol": HelperChoice("marisol", "Marisol", "woman", "splash-pad mechanic", "patient"),
    "mr_lane": HelperChoice("mr_lane", "Mr. Lane", "man", "grounds keeper", "careful"),
    "coach_rey": HelperChoice("coach_rey", "Coach Rey", "woman", "water-play coach", "calm"),
}

PLACE_LABELS = {
    "plate": "the quiet star plate in the meadow path",
    "sensor": "the clear sensor eye beside the crystal door frame",
    "valve": "the humming service nook under the meadow bench",
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for splash_pad_key, splash_pad in sorted(SPLASH_PADS.items()):
        for clue_key, clue in sorted(CLUES.items()):
            for fault_key, fault in sorted(FAULTS.items()):
                for fix_key, fix in sorted(FIXES.items()):
                    if clue.place not in splash_pad.sites:
                        continue
                    if fault.place != clue.place:
                        continue
                    if fix.solves != fault.kind:
                        continue
                    combos.append((splash_pad_key, clue_key, fault_key, fix_key))
    return combos


def _unknown_reason(kind: str, value: str, options: Iterable[str]) -> str:
    opts = ", ".join(sorted(options))
    return f"No story: unknown {kind} {value!r}. Try one of: {opts}."


def explain_rejection(splash_pad_key: str, clue_key: str, fault_key: str, fix_key: str) -> str:
    if splash_pad_key not in SPLASH_PADS:
        return _unknown_reason("splash pad", splash_pad_key, SPLASH_PADS)
    if clue_key not in CLUES:
        return _unknown_reason("clue", clue_key, CLUES)
    if fault_key not in FAULTS:
        return _unknown_reason("fault", fault_key, FAULTS)
    if fix_key not in FIXES:
        return _unknown_reason("fix", fix_key, FIXES)

    splash_pad = SPLASH_PADS[splash_pad_key]
    clue = CLUES[clue_key]
    fault = FAULTS[fault_key]
    fix = FIXES[fix_key]

    if clue.place not in splash_pad.sites:
        sites = ", ".join(splash_pad.sites)
        return (
            f"No story: {splash_pad.name} cannot host a clue at {clue.place}. "
            f"That splash pad only exposes these mystery sites: {sites}."
        )
    if fault.place != clue.place:
        return (
            f"No story: clue {clue_key!r} points to {clue.place}, but fault {fault_key!r} lives at {fault.place}. "
            "The repeating clue and the real fault must happen at the same place."
        )
    if fix.solves != fault.kind:
        return (
            f"No story: fix {fix_key!r} solves {fix.solves}, but fault {fault_key!r} is a {fault.kind} problem. "
            "Use the tool that actually fits the physical fault."
        )
    return "No story: invalid splash-pad mystery."


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.team not in TEAMS:
        return False, _unknown_reason("team", params.team, TEAMS)
    if params.helper not in HELPERS:
        return False, _unknown_reason("helper", params.helper, HELPERS)
    reason = explain_rejection(params.splash_pad, params.clue, params.fault, params.fix)
    if reason == "No story: invalid splash-pad mystery.":
        return True, ""
    return False, reason


def _pick_team(seed: int) -> str:
    rng = random.Random(seed)
    return rng.choice(sorted(TEAMS))


def _pick_helper(seed: int) -> str:
    rng = random.Random(seed * 19 + 5)
    return rng.choice(sorted(HELPERS))


def params_from_combo(combo: tuple[str, str, str, str], seed: int) -> StoryParams:
    return StoryParams(
        splash_pad=combo[0],
        clue=combo[1],
        fault=combo[2],
        fix=combo[3],
        team=_pick_team(seed),
        helper=_pick_helper(seed),
        seed=seed,
    )


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    return [
        combo
        for combo in valid_combos()
        if (args.splash_pad is None or combo[0] == args.splash_pad)
        and (args.clue is None or combo[1] == args.clue)
        and (args.fault is None or combo[2] == args.fault)
        and (args.fix is None or combo[3] == args.fix)
    ]


def build_world(params: StoryParams) -> MysteryWorld:
    splash_pad = SPLASH_PADS[params.splash_pad]
    clue = CLUES[params.clue]
    fault = FAULTS[params.fault]
    fix = FIXES[params.fix]
    team_choice = TEAMS[params.team]
    helper_choice = HELPERS[params.helper]

    world = MysteryWorld(params=params, splash_pad=splash_pad, clue=clue, fault=fault, fix=fix)

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
        Entity("door", "object", "crystal_door", "the crystal door", role="door", traits=["clear", "glowing"])
    )
    path = world.add(
        Entity("path", "system", "water_path", "the meadow water path", role="path", traits=["patterned"])
    )
    site = world.add(
        Entity(fault.place, "mechanism", fault.place, PLACE_LABELS[fault.place], role="site", traits=["hidden"])
    )

    door.meters["open"] = 0.0
    door.meters["stuckness"] = 1.0
    path.meters["balance"] = 0.35
    site.meters["fault"] = 1.0
    team.memes["curiosity"] = 1.4
    team.memes["worry"] = 0.2
    helper.memes["patience"] = 1.0

    world.facts["pad_name"] = splash_pad.name
    world.facts["reward"] = splash_pad.reward
    world.facts["site"] = fault.place
    world.facts["site_label"] = PLACE_LABELS[fault.place]
    world.facts["fault_kind"] = fault.kind
    world.facts["tool"] = fix.tool
    world.facts["helper_role"] = helper_choice.role
    world.facts["mystery"] = "why the crystal door would not open"
    world.facts["solved"] = False
    world.facts["ending_image"] = splash_pad.ending_image
    world.facts["seed_words"] = "meadow, crystal door"
    return world


def tell(world: MysteryWorld) -> MysteryWorld:
    first = world.get("first")
    second = world.get("second")
    helper = world.get("helper")
    team = world.get("team")
    door = world.get("door")
    path = world.get("path")
    site = world.get("site")
    splash_pad = world.splash_pad
    clue = world.clue
    fault = world.fault
    fix = world.fix
    site_label = str(world.facts["site_label"])
    helper_role = str(world.facts["helper_role"])

    world.record(
        "opening",
        f"{splash_pad.opening} At the far edge of the splash pad waited the crystal door, and behind it shimmered {splash_pad.reward}.",
        actor="narrator",
        target="door",
    )
    world.record(
        "goal",
        f"{first.label} and {second.label} loved this meadow puzzle because the crystal door only opened after the water path finished its pattern all the way to the end.",
        actor="team",
        target="path",
    )
    team.memes["wonder"] += 0.9
    world.para()

    world.record(
        "problem",
        "This time the first sprays leaped up, the bright path almost connected, and then the crystal door gave a tiny shiver and stayed shut.",
        actor="door",
        target="door",
    )
    team.memes["worry"] += 0.7
    team.memes["curiosity"] += 0.6
    world.record("false_guess", clue.false_guess, actor="team", target="door")
    world.record("clue_spotted", f"{clue.text} {clue.hint}", actor="team", target=fault.place)
    world.record(
        "helper_arrives",
        f'{helper.label}, the {helper_role}, crouched beside them and said, "A good mystery becomes fair when the same clue keeps returning."',
        actor="helper",
        target=fault.place,
    )
    world.para()

    world.record(
        "test_cycle",
        f"The children let one more water cycle run and watched nothing but {site_label}. The same clue came back exactly where it had before.",
        actor="team",
        target=fault.place,
    )
    world.record("discovery", fault.discovery, actor="team", target=fault.place)
    world.record("diagnosis", fault.motion, actor="team", target=fault.place)
    team.memes["understanding"] += 1.1
    world.para()

    world.record(
        "solve",
        fix.action.format(
            first=first.label,
            second=second.label,
            helper=helper.label,
            helper_possessive=helper.pronoun("possessive"),
            tool=fix.tool,
        ),
        actor="team",
        target=fault.place,
    )
    site.meters["fault"] = 0.0
    path.meters["balance"] = 1.0
    door.meters["stuckness"] = 0.0
    door.meters["open"] = 1.0
    team.memes["pride"] += 1.3
    team.memes["worry"] = 0.0
    world.record("proof", f"{fix.proof} {fault.result}", actor="path", target="door")
    world.facts["solved"] = True
    world.para()

    world.record(
        "ending",
        f"The next pulse raced cleanly across the meadow tiles, and the crystal door slid aside. Then {splash_pad.ending_image}. {first.label} grinned at {second.label} because the answer had never been hidden by magic, only by one small stubborn part. {fix.lesson}",
        actor="team",
        target="door",
    )
    return world


def generation_prompts(world: MysteryWorld) -> list[str]:
    first = world.get("first").label
    second = world.get("second").label
    return [
        'Write a child-friendly mystery set at a splash pad that includes the words "meadow" and "crystal door."',
        f"Tell a problem-solving story where {first} and {second} follow one repeating clue instead of forcing a magical explanation.",
        "End with a concrete visual change that proves the water system and the crystal door are really working again.",
    ]


def story_grounded_qa(world: MysteryWorld) -> list[QAItem]:
    splash_pad = world.splash_pad
    clue = world.clue
    fault = world.fault
    fix = world.fix
    helper = world.get("helper").label
    site_label = str(world.facts["site_label"])
    return [
        QAItem(
            "What was the mystery in the story?",
            f"The mystery was why the crystal door at {splash_pad.name} stayed shut even when the splash pad woke up. That mattered because the children could only reach {splash_pad.reward} after the full water path worked correctly.",
        ),
        QAItem(
            "Which clue told the children where to look?",
            f"The repeating clue was that {clue.text.lower()} Because the same odd sign returned every cycle, it narrowed the mystery to {site_label} instead of making the children search everywhere.",
        ),
        QAItem(
            "What physical problem was actually stopping the crystal door?",
            f"The real problem was that {fault.motion.lower()} The children proved that when they inspected the site closely and found that {fault.discovery.lower()}",
        ),
        QAItem(
            "How did the children solve the problem?",
            f"They used {fix.tool} at the exact spot the clue kept naming. {fix.proof} That showed the fix matched the real fault instead of covering it up with a wild guess.",
        ),
        QAItem(
            "Why did the helper matter?",
            f"{helper} mattered because the helper taught the children how to test the repeated clue one more time before acting. That calm advice turned their worry into a clear plan.",
        ),
        QAItem(
            "What proved the mystery was solved at the end?",
            f"The solution was proven when the water path ran cleanly, the crystal door opened, and {splash_pad.ending_image}. That ending image could only happen after the hidden fault stopped interrupting the system.",
        ),
    ]


def world_knowledge_qa(world: MysteryWorld) -> list[QAItem]:
    return [
        QAItem(
            "Why must the clue place and the fault place match in this world?",
            "A fair mystery needs a clue that points toward the real trouble spot. If the clue happened in one place and the fault lived somewhere else, the children would be solving luck instead of evidence.",
        ),
        QAItem(
            "Why can each fix only solve one kind of fault?",
            "Each fix works on a specific material problem such as a jam, a film, or a kink. The world stays reasonable by requiring a tool and action that physically fit the fault instead of letting any busy motion count as a solution.",
        ),
        QAItem(
            "Why does the splash-pad setting matter to the story logic?",
            "The splash pad supplies the water path, the crystal door trigger, and the visible clue cycles that the children can observe. The setting limits which mystery sites exist, so the story stays grounded in real layout instead of floating anywhere.",
        ),
        QAItem(
            "Why is the ending image important in this kind of mystery?",
            "The ending image is proof, not decoration. When the final sprays and the crystal door change together, the children and the reader can see that the world state truly shifted from broken to solved.",
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
valid(S,C,F,X) :-
    splash_pad(S),
    clue(C),
    fault(F),
    fix(X),
    clue_place(C, P),
    fault_place(F, P),
    splash_pad_site(S, P),
    fault_kind(F, K),
    fix_solves(X, K).

ok :- chosen(S, C, F, X), valid(S, C, F, X).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    lines: list[str] = []
    for splash_pad_key, splash_pad in sorted(SPLASH_PADS.items()):
        lines.append(fact("splash_pad", splash_pad_key))
        for site in splash_pad.sites:
            lines.append(fact("splash_pad_site", splash_pad_key, site))
    for clue_key, clue in sorted(CLUES.items()):
        lines.append(fact("clue", clue_key))
        lines.append(fact("clue_place", clue_key, clue.place))
    for fault_key, fault in sorted(FAULTS.items()):
        lines.append(fact("fault", fault_key))
        lines.append(fact("fault_place", fault_key, fault.place))
        lines.append(fact("fault_kind", fault_key, fault.kind))
    for fix_key, fix in sorted(FIXES.items()):
        lines.append(fact("fix", fix_key))
        lines.append(fact("fix_solves", fix_key, fix.solves))
    if params is not None:
        lines.append(fact("chosen", params.splash_pad, params.clue, params.fault, params.fix))
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
    if world.get("site").meters.get("fault", 1) != 0:
        raise AssertionError("problem site stayed faulty")
    if world.get("path").meters.get("balance", 0) < 1:
        raise AssertionError("water path never recovered")
    if world.get("team").memes.get("pride", 0) < 1:
        raise AssertionError("team never reached a solved ending state")
    if not world.facts.get("solved"):
        raise AssertionError("story never marked itself solved")
    event_ids = {event.id for event in world.history}
    for required in ("clue_spotted", "discovery", "solve", "ending"):
        if required not in event_ids:
            raise AssertionError(f"missing event {required!r}")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 6 or len(sample.world_qa) < 4:
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
    print(f"OK: ASP parity matches Python gate ({len(py)} valid splash-pad mysteries).")
    for index, combo in enumerate(py):
        verify_sample(generate(params_from_combo(combo, 1000 + index)))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a meadow splash-pad mystery about a crystal door and problem solving."
    )
    parser.add_argument("--splash-pad", dest="splash_pad", choices=sorted(SPLASH_PADS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--fault", choices=sorted(FAULTS))
    parser.add_argument("--fix", choices=sorted(FIXES))
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
        splash_pad = args.splash_pad or next(iter(SPLASH_PADS))
        clue = args.clue or next(iter(CLUES))
        fault = args.fault or next(iter(FAULTS))
        fix = args.fix or next(iter(FIXES))
        raise StoryError(explain_rejection(splash_pad, clue, fault, fix))

    explicit = all(getattr(args, field) is not None for field in ("splash_pad", "clue", "fault", "fix"))
    if explicit:
        params = params_from_combo((args.splash_pad, args.clue, args.fault, args.fix), seed)
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
            splash_pad = args.splash_pad or next(iter(SPLASH_PADS))
            clue = args.clue or next(iter(CLUES))
            fault = args.fault or next(iter(FAULTS))
            fix = args.fix or next(iter(FIXES))
            raise StoryError(explain_rejection(splash_pad, clue, fault, fix))
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
            print("  " + " ".join(f"{part:16}" for part in combo))
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
            header = (
                f"=== meadow_crystal_door_splash_pad_problem_solving_4 "
                f"#{index} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
