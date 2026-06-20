#!/usr/bin/env python3
"""A folk-tale deep-puddle story about a misty ship, a crystal door, teamwork, and curiosity.

Internal source tale:
After rain, two children find a deep puddle with a crystal door resting at its
far rim. They want to send a tiny misty ship through the door, but the water
keeps failing in the same exact way. One child is tempted to blame the mood of
the door, yet the other stays curious and studies the repeating sign. Together
they discover a small physical trouble in the puddle's path, mend it with the
right shared action, and watch the ship pass through in a final image that
proves both the door and the water have changed.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Puddle:
    id: str
    name: str
    opening: str
    door_lore: str
    ending: str
    sites: tuple[str, ...]


@dataclass(frozen=True)
class Clue:
    id: str
    place: str
    text: str
    hint: str
    doubt: str


@dataclass(frozen=True)
class Obstruction:
    id: str
    place: str
    kind: str
    motion: str
    discovery: str
    result: str


@dataclass(frozen=True)
class Remedy:
    id: str
    solves: str
    tool: str
    action: str
    hero_work: str
    helper_work: str
    proof: str


@dataclass
class StoryParams:
    puddle: str
    clue: str
    obstruction: str
    remedy: str
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None
    place: str | None = None


@dataclass
class DoorPuddleWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    roles: dict[str, str] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | int | float] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        if entity.role:
            self.roles[entity.role] = entity.id
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[self.roles.get(entity_id, entity_id)]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(
        self,
        event_id: str,
        text: str,
        actor: str,
        target: str | None = None,
        place: str | None = None,
    ) -> None:
        self.history.append(Event(event_id, text, actor, target, place))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


PUDDLES: dict[str, Puddle] = {
    "fern_hollow": Puddle(
        id="fern_hollow",
        name="Fern Hollow",
        opening=(
            "In Fern Hollow, the night's rain had gathered into a deep puddle so still and dark that even the ferns leaned over to see their own faces in it."
        ),
        door_lore=(
            "At the far rim stood a crystal door no taller than a loaf of bread, and the old saying was that it opened only for a traveler carried by true water."
        ),
        ending=(
            "the deep puddle held a straight silver lane, and the crystal door stood open with fern-shadows trembling in its blue light"
        ),
        sites=("spill_ribbon", "hinge_cup"),
    ),
    "stone_heel": Puddle(
        id="stone_heel",
        name="Stone Heel",
        opening=(
            "At Stone Heel, rainwater slept in a deep puddle pressed into the road like a giant's footprint, with a thin shawl of mist lying over it."
        ),
        door_lore=(
            "By the far edge, a crystal door rested in the stone, and the village children whispered that it listened not to wishing, but to the honesty of moving water."
        ),
        ending=(
            "ripples ran clean across the deep puddle while the misty ship slipped through the crystal door and came back shining at the far side"
        ),
        sites=("spill_ribbon", "underlip_channel"),
    ),
    "briar_step": Puddle(
        id="briar_step",
        name="Briar Step",
        opening=(
            "Below the briar step, rain had pooled into a deep puddle ringed with roots, and dawn light floated on it as softly as milk."
        ),
        door_lore=(
            "Half-hidden under the roots was a crystal door, said to welcome only those who watched carefully before they acted."
        ),
        ending=(
            "mist lifted from the deep puddle in pale curls, and beyond the crystal door a bright little wake kept widening among the roots"
        ),
        sites=("hinge_cup", "underlip_channel"),
    ),
}

CLUES: dict[str, Clue] = {
    "leaf_whorl": Clue(
        id="leaf_whorl",
        place="spill_ribbon",
        text="A yellow leaf kept turning in one tight whorl where a thin ribbon of water should have guided the ship onward.",
        hint="Each time the children set the ship free, the leaf twirled in the very same place and would not drift an inch farther.",
        doubt="Oren whispered that perhaps the crystal door had woken in a stern mood and did not care to be visited.",
    ),
    "glass_hum": Clue(
        id="glass_hum",
        place="hinge_cup",
        text="A faint glassy hum came from the little cup beside the crystal door whenever the misty ship nudged close.",
        hint="The sound was trapped and regular, like something trying to rise but being kept from its work.",
        doubt="For a moment, Sela wondered whether a hidden spirit was singing inside the clear panel.",
    ),
    "silver_thread": Clue(
        id="silver_thread",
        place="underlip_channel",
        text="A silver thread of water slid under the crystal door and vanished halfway, as if its road had been swallowed.",
        hint="No matter how often they tried, that shining line broke at the same hidden place beneath the lip of the sill.",
        doubt="Oren said the misty ship might simply be too light for such a proud little door.",
    ),
}

OBSTRUCTIONS: dict[str, Obstruction] = {
    "rush_snarl": Obstruction(
        id="rush_snarl",
        place="spill_ribbon",
        kind="snarl",
        motion="A twist of rush roots and straw had snarled across the spill ribbon, bending the current away from the true lane.",
        discovery="Under the turning leaf, they found wet rush roots hooked together like a little claw across the narrow channel.",
        result="The freed ribbon ran true at once, and the misty ship caught the straight pull it had been seeking.",
    ),
    "acorn_stopper": Obstruction(
        id="acorn_stopper",
        place="hinge_cup",
        kind="stopper",
        motion="A fat acorn cap had slipped into the hinge cup and held the tiny float down whenever the water tried to lift it.",
        discovery="Inside the cup sat an acorn cap tight as a cork, pinning the float so it could only hum and never rise.",
        result="When the stopper came free, the float bobbed upward with a bright click, and the crystal door answered at once.",
    ),
    "clay_plug": Obstruction(
        id="clay_plug",
        place="underlip_channel",
        kind="plug",
        motion="Packed clay had plugged the underlip channel, so the lifting water could not slip beneath the crystal door.",
        discovery="Sela touched the silver thread and felt cool clay wedged in the hidden channel where the water should have whispered through.",
        result="Once the clay loosened, a clear line of water slid under the door and lifted it on its shining hinges.",
    ),
}

REMEDIES: dict[str, Remedy] = {
    "comb_and_lift": Remedy(
        id="comb_and_lift",
        solves="snarl",
        tool="a willow comb and both pairs of patient fingers",
        action="Sela held a willow comb low in the water to lift the roots while Oren teased the straw free, and together they drew the whole wet snarl out of the ribbon.",
        hero_work="Sela kept the channel open with the willow comb so the hidden tangle could rise.",
        helper_work="Oren loosened the straw and roots one by one until the current had room again.",
        proof="The leaf stopped spinning and glided forward as if it had been given a road.",
    ),
    "tilt_and_pinch": Remedy(
        id="tilt_and_pinch",
        solves="stopper",
        tool="a snail shell, two thumbs, and a steady breath",
        action="Oren tilted the little hinge cup with both thumbs while Sela slid a snail shell under the acorn cap and pinched it free.",
        hero_work="Sela used the shell to slip beneath the stopper without cracking the delicate cup.",
        helper_work="Oren steadied the cup so the trapped float would not wedge harder as she worked.",
        proof="The hum broke into a clear click, and the tiny float rose instead of trembling in place.",
    ),
    "rinse_and_feather": Remedy(
        id="rinse_and_feather",
        solves="plug",
        tool="a folded leaf cup and a robin feather",
        action="Sela poured clear puddle water from a folded leaf cup while Oren worked a robin feather through the hidden channel until the clay softened and slipped away.",
        hero_work="Sela kept sending clean water into the channel so the packed clay would loosen instead of hardening.",
        helper_work="Oren traced the narrow path with the feather until the plug gave way.",
        proof="The silver thread stopped breaking short and ran beneath the sill in one bright line.",
    ),
}

PLACE_LABELS = {
    "spill_ribbon": "the thin spill ribbon beside the puddle's rim",
    "hinge_cup": "the little hinge cup beside the crystal door",
    "underlip_channel": "the hidden underlip channel beneath the crystal door",
}

KIND_LABELS = {
    "snarl": "a rush-root snarl across the spill ribbon",
    "stopper": "an acorn cap wedged in the hinge cup",
    "plug": "packed clay plugging the underlip channel",
}


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def end_sentence(text: str) -> str:
    return text if text.endswith((".", "!", "?")) else f"{text}."


def explain_rejection(puddle_id: str, clue_id: str, obstruction_id: str, remedy_id: str) -> str:
    if puddle_id not in PUDDLES:
        return f"unknown puddle: {puddle_id}"
    if clue_id not in CLUES:
        return f"unknown clue: {clue_id}"
    if obstruction_id not in OBSTRUCTIONS:
        return f"unknown obstruction: {obstruction_id}"
    if remedy_id not in REMEDIES:
        return f"unknown remedy: {remedy_id}"
    puddle = PUDDLES[puddle_id]
    clue = CLUES[clue_id]
    obstruction = OBSTRUCTIONS[obstruction_id]
    remedy = REMEDIES[remedy_id]
    reasons: list[str] = []
    if clue.place != obstruction.place:
        reasons.append("the clue must point to the very place where the puddle's real trouble lives")
    if remedy.solves != obstruction.kind:
        reasons.append("the chosen remedy must fit the physical kind of obstruction")
    if obstruction.place not in puddle.sites:
        reasons.append(f"{puddle.name} does not route this tale through {PLACE_LABELS[obstruction.place]}")
    if not reasons:
        return "the requested story is valid"
    return "; ".join(reasons)


def valid_params(params: StoryParams) -> tuple[bool, str]:
    reason = explain_rejection(params.puddle, params.clue, params.obstruction, params.remedy)
    return (reason == "the requested story is valid", reason)


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for puddle in PUDDLES:
        for clue in CLUES:
            for obstruction in OBSTRUCTIONS:
                for remedy in REMEDIES:
                    params = StoryParams(
                        puddle=puddle,
                        clue=clue,
                        obstruction=obstruction,
                        remedy=remedy,
                    )
                    if valid_params(params)[0]:
                        combos.append(params)
    return combos


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    combos = all_params()
    if args.puddle:
        combos = [combo for combo in combos if combo.puddle == args.puddle]
    if args.clue:
        combos = [combo for combo in combos if combo.clue == args.clue]
    if args.obstruction:
        combos = [combo for combo in combos if combo.obstruction == args.obstruction]
    if args.remedy:
        combos = [combo for combo in combos if combo.remedy == args.remedy]
    return combos


def make_world(params: StoryParams) -> DoorPuddleWorld:
    puddle = PUDDLES[params.puddle]
    clue = CLUES[params.clue]
    obstruction = OBSTRUCTIONS[params.obstruction]
    remedy = REMEDIES[params.remedy]

    world = DoorPuddleWorld(params)
    world.add(Entity("sela", "character", "girl", "Sela", role="hero", traits=["curious", "patient"]))
    world.add(Entity("oren", "character", "boy", "Oren", role="helper", traits=["steady", "warm"]))
    world.add(Entity("pair", "group", "pair", "the two children", role="team"))
    world.add(Entity("puddle", "place", "puddle", "the deep puddle"))
    world.add(Entity("ship", "object", "boat", "the misty ship"))
    world.add(Entity("door", "object", "door", "the crystal door"))
    world.add(Entity("lantern", "object", "lamp", "the thimble lantern"))
    world.add(Entity("spill_ribbon", "mechanism", "water_lane", PLACE_LABELS["spill_ribbon"]))
    world.add(Entity("hinge_cup", "mechanism", "hinge", PLACE_LABELS["hinge_cup"]))
    world.add(Entity("underlip_channel", "mechanism", "channel", PLACE_LABELS["underlip_channel"]))

    world.get("puddle").meters["depth"] = 3.1
    world.get("puddle").meters["flow"] = 2.0
    world.get("puddle").meters["clarity"] = 2.0
    world.get("ship").meters["drift"] = 1.0
    world.get("ship").meters["passage"] = 0.0
    world.get("door").meters["open"] = 0.0
    world.get("door").meters["stuckness"] = 2.0
    world.get("door").meters["gleam"] = 1.0
    world.get("team").memes["teamwork"] = 1.8
    world.get("team").memes["worry"] = 0.0
    world.get("team").memes["relief"] = 0.0
    world.get("team").memes["wonder"] = 1.0
    world.get("hero").memes["curiosity"] = 2.1
    world.get("helper").memes["trust"] = 1.8
    world.get(obstruction.place).meters["blocked"] = 1.0

    world.facts.update(
        puddle_name=puddle.name,
        clue_text=clue.text,
        clue_hint=clue.hint,
        clue_place=PLACE_LABELS[clue.place],
        doubt=clue.doubt,
        obstruction_label=KIND_LABELS[obstruction.kind],
        remedy_tool=remedy.tool,
        proverb="When water repeats itself, it is trying to teach the watcher something.",
        solved=False,
    )
    return world


def opening(world: DoorPuddleWorld) -> None:
    puddle = PUDDLES[world.params.puddle]
    world.get("hero").memes["curiosity"] += 0.5
    world.get("team").memes["wonder"] += 0.8
    world.record(
        "opening",
        f"{puddle.opening} {puddle.door_lore}",
        "puddle",
        "door",
        "puddle",
    )
    world.record(
        "wish",
        "Sela and Oren set a tiny thimble lantern inside the misty ship, for they hoped to see it pass through the crystal door before the sun thinned the puddle. Sela loved puzzles that could be touched with the hands, and Oren loved any task that asked them to work side by side.",
        "team",
        "ship",
        "puddle",
    )


def failed_launch(world: DoorPuddleWorld) -> None:
    puddle = PUDDLES[world.params.puddle]
    world.get("puddle").meters["flow"] -= 1.0
    world.get("ship").meters["drift"] -= 0.4
    world.get("door").meters["stuckness"] += 1.0
    world.get("team").memes["worry"] += 1.1
    world.record(
        "problem",
        f"But when they set the misty ship free, it nosed aside and wandered without courage. In {puddle.name}, the water failed to carry it in a clean line, and the crystal door stayed clear, shut, and quiet.",
        "ship",
        "door",
        "puddle",
    )


def notice_clue(world: DoorPuddleWorld) -> None:
    clue = CLUES[world.params.clue]
    world.get("hero").memes["curiosity"] += 1.0
    world.record(
        "clue",
        f"{clue.text} {end_sentence(sentence_start(clue.hint))}",
        "hero",
        clue.place,
        clue.place,
    )


def reject_superstition(world: DoorPuddleWorld) -> None:
    clue = CLUES[world.params.clue]
    world.get("team").memes["worry"] += 0.2
    world.record(
        "doubt",
        f'{clue.doubt} Yet Sela crouched lower and said, "{world.facts["proverb"]}" So they chose to trust the sign instead of a frightened guess.',
        "helper",
        "hero",
        clue.place,
    )


def form_theory(world: DoorPuddleWorld) -> None:
    obstruction = OBSTRUCTIONS[world.params.obstruction]
    if obstruction.kind == "snarl":
        theory = "Something in the spill ribbon is twisting the current away from the ship's road."
    elif obstruction.kind == "stopper":
        theory = "Something in the hinge cup is holding the little lift down, so the door cannot answer the ship."
    else:
        theory = "Something under the door is stopping the water before it reaches the lifting place."
    world.facts["theory"] = theory
    world.get("team").memes["teamwork"] += 0.6
    world.record(
        "turn",
        f"Shoulder to shoulder, the children watched the puddle a second time and then made a careful plan. {theory}",
        "team",
        obstruction.place,
        obstruction.place,
    )


def inspect_obstruction(world: DoorPuddleWorld) -> None:
    obstruction = OBSTRUCTIONS[world.params.obstruction]
    world.get("hero").memes["curiosity"] += 0.8
    world.get("helper").memes["trust"] += 0.4
    world.get("team").memes["teamwork"] += 0.9
    world.record(
        "inspect",
        f"So they searched {PLACE_LABELS[obstruction.place]} instead of muttering at luck. {obstruction.motion} Soon the hidden proof gave itself up: {end_sentence(obstruction.discovery)}",
        "team",
        obstruction.place,
        obstruction.place,
    )


def repair(world: DoorPuddleWorld) -> None:
    obstruction = OBSTRUCTIONS[world.params.obstruction]
    remedy = REMEDIES[world.params.remedy]
    world.get("puddle").meters["flow"] += 2.2
    world.get("puddle").meters["clarity"] += 1.1
    world.get("ship").meters["drift"] = 2.0
    world.get("ship").meters["passage"] = 0.6
    world.get("door").meters["stuckness"] = 0.0
    world.get("door").meters["gleam"] += 1.0
    world.get("team").memes["teamwork"] += 1.1
    world.get("team").memes["relief"] += 1.0
    world.get(obstruction.place).meters["blocked"] = 0.0
    world.record(
        "repair",
        f"{remedy.action} {remedy.proof} {obstruction.result}",
        "team",
        obstruction.place,
        obstruction.place,
    )


def release_ship(world: DoorPuddleWorld) -> None:
    world.get("ship").meters["passage"] = 1.0
    world.get("door").meters["open"] = 1.0
    world.get("team").memes["wonder"] += 1.0
    world.facts["solved"] = True
    world.record(
        "release",
        "They set the misty ship free once more, and this time it traveled without wavering. The thimble lantern glowed at its heart as it touched the threshold and slipped through the crystal door.",
        "ship",
        "door",
        "puddle",
    )


def ending(world: DoorPuddleWorld) -> None:
    puddle = PUDDLES[world.params.puddle]
    world.record(
        "ending",
        f"Oren laughed first, and Sela laughed after him, for now they knew the puddle had not asked for grand magic at all. It had asked for curious eyes, gentle hands, and two children willing to help each other finish one careful thought. By full morning, {puddle.ending}.",
        "team",
        "ship",
        "puddle",
    )


def tell(params: StoryParams) -> DoorPuddleWorld:
    world = make_world(params)
    opening(world)
    world.para()
    failed_launch(world)
    notice_clue(world)
    reject_superstition(world)
    form_theory(world)
    world.para()
    inspect_obstruction(world)
    repair(world)
    world.para()
    release_ship(world)
    ending(world)
    return world


def generation_prompts(world: DoorPuddleWorld) -> list[str]:
    return [
        'Write a child-facing folk tale set at a deep puddle and include the exact phrases "misty ship" and "crystal door."',
        f"Make curiosity follow a repeating sign at {world.facts['clue_place']} until the children uncover a real physical obstruction.",
        "Resolve the problem through teamwork, and finish with an image that proves the water path and the door truly changed.",
    ]


def story_grounded_qa(world: DoorPuddleWorld) -> list[QAItem]:
    clue = CLUES[world.params.clue]
    obstruction = OBSTRUCTIONS[world.params.obstruction]
    remedy = REMEDIES[world.params.remedy]
    return [
        QAItem(
            question="Why did the misty ship fail to reach the crystal door at first?",
            answer=(
                f"The misty ship failed at first because of {KIND_LABELS[obstruction.kind]}. "
                f"{obstruction.motion} That changed how the water moved or how the door responded, so the ship could not complete its passage."
            ),
        ),
        QAItem(
            question="What clue helped Sela and Oren search in the right place?",
            answer=(
                f"The guiding clue was that {clue.text.lower()} "
                f"Because the same sign returned in the same spot, the children understood that the puddle was pointing toward a real cause instead of random wonder."
            ),
        ),
        QAItem(
            question="How did the two children divide the work when they fixed the puddle?",
            answer=(
                f"They solved it as a team by using {remedy.tool}. "
                f"{remedy.hero_work} {remedy.helper_work} That shared work let them repair the exact trouble without damaging the small crystal mechanism."
            ),
        ),
        QAItem(
            question="What final image showed that their work had truly changed the world?",
            answer=(
                "The change became clear when the misty ship finally traveled in a true line and passed through the crystal door. "
                "The opened door, the steady lantern, and the cleaned water path all showed that the puddle had been repaired rather than merely admired."
            ),
        ),
    ]


def world_knowledge_qa(world: DoorPuddleWorld) -> list[QAItem]:
    obstruction = OBSTRUCTIONS[world.params.obstruction]
    remedy = REMEDIES[world.params.remedy]
    return [
        QAItem(
            question="Why is curiosity useful when a small machine or water path behaves strangely?",
            answer=(
                "Curiosity keeps someone looking long enough to compare one try with the next and notice what repeats. "
                "That patience turns a confusing moment into a testable idea instead of a frightened guess."
            ),
        ),
        QAItem(
            question="Why did teamwork matter more than speed in this puddle story?",
            answer=(
                "Teamwork mattered because the problem needed one child to steady or guide the work while the other freed the obstruction. "
                "If they had rushed alone, they might have missed the cause or harmed the tiny path that needed careful handling."
            ),
        ),
        QAItem(
            question="Why can a small blockage change the behavior of a floating object so much?",
            answer=(
                f"A small blockage matters because floating objects depend on direction, not only on movement. "
                f"When {KIND_LABELS[obstruction.kind]} disturbs the path, even a light vessel can miss its lane until someone uses {remedy.tool} to restore the flow."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P,C,O,R) :-
    puddle(P), clue(C), obstruction(O), remedy(R),
    clue_place(C, S), obstruction_place(O, S),
    obstruction_kind(O, K), remedy_solves(R, K),
    puddle_site(P, S).

ok :- chosen(P, C, O, R), valid(P, C, O, R).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    lines: list[str] = []
    for puddle_id, puddle in PUDDLES.items():
        lines.append(fact("puddle", puddle_id))
        for site in puddle.sites:
            lines.append(fact("puddle_site", puddle_id, site))
    for clue_id, clue in CLUES.items():
        lines.append(fact("clue", clue_id))
        lines.append(fact("clue_place", clue_id, clue.place))
    for obstruction_id, obstruction in OBSTRUCTIONS.items():
        lines.append(fact("obstruction", obstruction_id))
        lines.append(fact("obstruction_place", obstruction_id, obstruction.place))
        lines.append(fact("obstruction_kind", obstruction_id, obstruction.kind))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(fact("remedy", remedy_id))
        lines.append(fact("remedy_solves", remedy_id, remedy.solves))
    if params is not None:
        lines.append(fact("chosen", params.puddle, params.clue, params.obstruction, params.remedy))
    return "\n".join(lines) + "\n"


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    if "deep puddle" not in story_lower:
        raise AssertionError("story is missing 'deep puddle'")
    if "misty ship" not in story_lower:
        raise AssertionError("story is missing 'misty ship'")
    if "crystal door" not in story_lower:
        raise AssertionError("story is missing 'crystal door'")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if world.get("door").meters.get("open", 0) < 1:
        raise AssertionError("the crystal door never opened")
    if world.get("ship").meters.get("passage", 0) < 1:
        raise AssertionError("the misty ship never completed its passage")
    if world.get("door").meters.get("stuckness", 1) != 0:
        raise AssertionError("the door remained stuck")
    if world.get("team").memes.get("teamwork", 0) < 3:
        raise AssertionError("teamwork did not strengthen enough")
    if world.get("hero").memes.get("curiosity", 0) < 3:
        raise AssertionError("curiosity did not drive the investigation")
    if not world.facts.get("solved"):
        raise AssertionError("story never marked itself solved")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    if len(world.history) < 8:
        raise AssertionError("story world history is too short")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    if "meters" in story_lower or "memes" in story_lower:
        raise AssertionError("story leaked internal state terms")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 14:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = sorted(
        (params.puddle, params.clue, params.obstruction, params.remedy)
        for params in all_params()
    )
    lp = sorted(asp_valid_combos())
    if py != lp:
        print("MISMATCH between Python and ASP gates:")
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        if only_py:
            print("  only in Python:", only_py)
        if only_lp:
            print("  only in ASP:", only_lp)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid deep-puddle stories).")
    for params in all_params():
        chosen = StoryParams(**vars(params))
        verify_sample(generate(chosen))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a folk-tale story about a misty ship, a crystal door, and teamwork in a deep puddle."
    )
    parser.add_argument("--puddle", choices=sorted(PUDDLES))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--obstruction", choices=sorted(OBSTRUCTIONS))
    parser.add_argument("--remedy", choices=sorted(REMEDIES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit = all(
        getattr(args, field) is not None
        for field in ("puddle", "clue", "obstruction", "remedy")
    )
    if explicit:
        params = StoryParams(
            args.puddle,
            args.clue,
            args.obstruction,
            args.remedy,
            args.seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    combos = matching_params(args)
    if not combos:
        puddle = args.puddle or next(iter(PUDDLES))
        clue = args.clue or next(iter(CLUES))
        obstruction = args.obstruction or next(iter(OBSTRUCTIONS))
        remedy = args.remedy or next(iter(REMEDIES))
        raise StoryError(explain_rejection(puddle, clue, obstruction, remedy))
    chosen = StoryParams(**vars(rng.choice(combos)))
    chosen.seed = args.seed
    return chosen


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_params(args)
        if not combos:
            puddle = args.puddle or next(iter(PUDDLES))
            clue = args.clue or next(iter(CLUES))
            obstruction = args.obstruction or next(iter(OBSTRUCTIONS))
            remedy = args.remedy or next(iter(REMEDIES))
            raise StoryError(explain_rejection(puddle, clue, obstruction, remedy))
        samples: list[StorySample] = []
        for index, params in enumerate(combos):
            chosen = StoryParams(**vars(params))
            chosen.seed = args.seed + index if args.seed is not None else None
            samples.append(generate(chosen))
        return samples

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = base_seed + index
        seeded_args = argparse.Namespace(**vars(args))
        seeded_args.seed = seed
        samples.append(generate(resolve_params(seeded_args, random.Random(seed))))
    return samples


def dump_trace(world: DoorPuddleWorld) -> str:
    lines = ["TRACE", f"puddle: {world.facts['puddle_name']}"]
    for event in world.history:
        where = f" @ {event.place}" if event.place else ""
        lines.append(f"- {event.id}{where}: {event.text}")
    lines.append("ENTITIES")
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id} | {entity.kind} | {entity.label}")
        if meters:
            lines.append(f"    meters={meters}")
        if memes:
            lines.append(f"    memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines: list[str] = ["PROMPTS"]
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
        print(dump_trace(sample.world))
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
        print(f"{len(combos)} valid deep-puddle misty-ship stories:\n")
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
            header = f"=== misty_ship_crystal_door_deep_puddle_teamwork_2 #{index} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
