#!/usr/bin/env python3
"""A folk-tale puddle story about a misty ship, a crystal door, teamwork, and curiosity.

Internal source tale:
After a night of rain, two children find a deep puddle that holds a crystal
door at its far edge. They want to send a little misty ship through the door,
but the ship cannot reach it because the water path is wrong. Instead of
blaming magic, the children follow a repeating clue, reason about the puddle's
physical shape, and fix the real obstruction together. Their teamwork lets the
misty ship glide true at last, and the opened crystal door gives a final image
that proves the world has changed.
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
    door_play: str
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
class Cause:
    id: str
    place: str
    kind: str
    motion: str
    discovery: str
    result: str


@dataclass(frozen=True)
class Method:
    id: str
    solves: str
    tool: str
    action: str
    proof: str


@dataclass
class StoryParams:
    puddle: str
    clue: str
    cause: str
    method: str
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
class PuddleWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str | bool | int | float] = field(default_factory=dict)

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
    "lane_hollow": Puddle(
        id="lane_hollow",
        name="Lane Hollow",
        opening=(
            "At Lane Hollow, last night's rain had gathered into a deep puddle so dark and round "
            "that the village children called it the road's small mirror."
        ),
        door_play=(
            "At the far bank, between two roots, stood a crystal door that opened only when the water "
            "carried a tiny boat to it in one clean glide."
        ),
        ending=(
            "the deep puddle sent the misty ship straight as a promise, and the crystal door shone blue "
            "between the roots"
        ),
        sites=("runnel", "latch_bowl"),
    ),
    "willow_step": Puddle(
        id="willow_step",
        name="Willow Step",
        opening=(
            "Behind the willow step, a deep puddle slept in a bowl of clay, and pale morning mist lay "
            "on its face like carded wool."
        ),
        door_play=(
            "Under a bent root rested a crystal door, waiting for the right ribbon of water to lift it "
            "and welcome a little traveler through."
        ),
        ending=(
            "little curls of mist rose from the deep puddle while the misty ship slipped through the crystal "
            "door and circled back beneath the willow shade"
        ),
        sites=("runnel", "sill_groove"),
    ),
    "mill_stone": Puddle(
        id="mill_stone",
        name="Mill Stone Cup",
        opening=(
            "Beside the old mill stone, rain filled a deep puddle in the cracked granite, and dawn light "
            "shivered on it like coins at the bottom of a well."
        ),
        door_play=(
            "There in the stone rim stood a crystal door, and the oldest children said it opened only for "
            "careful hands and honest water."
        ),
        ending=(
            "rings of light ran across the deep puddle while the crystal door stood wide and the misty ship "
            "rocked beyond it"
        ),
        sites=("latch_bowl", "sill_groove"),
    ),
}

CLUES: dict[str, Clue] = {
    "foam_wheel": Clue(
        id="foam_wheel",
        place="runnel",
        text="A white wheel of foam kept spinning where the little runnel met the deep puddle.",
        hint="It turned in the same tight place each time, as if the water were pointing with a patient finger.",
        doubt="For a blink, Toma wondered whether the crystal door had chosen to stay asleep that morning.",
    ),
    "tap_tap": Clue(
        id="tap_tap",
        place="latch_bowl",
        text="A patient tap-tap sounded from the small bowl below the crystal door whenever the misty ship drifted near.",
        hint="The sound was regular and trapped, not bright and free like a latch that wanted to rise.",
        doubt="Mira almost thought some hidden sprite was knocking from inside the clear panel.",
    ),
    "silver_streak": Clue(
        id="silver_streak",
        place="sill_groove",
        text="A narrow silver streak ran under the crystal door and stopped halfway, trembling as though it had lost its road.",
        hint="The same thin line broke in the same place again and again, which made Mira crouch lower to study it.",
        doubt="Toma muttered that perhaps the misty ship was too light and the door had no wish to greet it.",
    ),
}

CAUSES: dict[str, Cause] = {
    "reed_dam": Cause(
        id="reed_dam",
        place="runnel",
        kind="dam",
        motion=(
            "A braid of reeds and straw had dammed the runnel that should have guided the misty ship toward the door."
        ),
        discovery=(
            "Under the spinning foam, they found wet reeds hooked together like fingers across the narrow way."
        ),
        result=(
            "As soon as the runnel ran free, a straight little current caught the misty ship and drew it to the crystal door."
        ),
    ),
    "pebble_wedge": Cause(
        id="pebble_wedge",
        place="latch_bowl",
        kind="wedge",
        motion=(
            "A round pebble had dropped into the latch bowl and held the float down whenever the water tried to lift it."
        ),
        discovery=(
            "At the bottom of the bowl sat a smooth pebble, pinning the tiny float so it could only knock and never rise."
        ),
        result=(
            "When the pebble came out, the float bobbed up with a clear click, and the crystal door opened like morning ice."
        ),
    ),
    "silt_seal": Cause(
        id="silt_seal",
        place="sill_groove",
        kind="silt",
        motion=(
            "Packed silt had sealed the spill groove beneath the door, so the lifting water could not slide under the clear panel."
        ),
        discovery=(
            "Mira touched the silver line and felt gritty mud plugging the groove where the water ought to have whispered through."
        ),
        result=(
            "Once the groove cleared, a bright thread of water slipped beneath the panel and the crystal door lifted on its shining hinges."
        ),
    ),
}

METHODS: dict[str, Method] = {
    "forked_twig": Method(
        id="forked_twig",
        solves="dam",
        tool="a forked twig and steady hands",
        action=(
            "Mira held a forked twig low in the water while Toma pinched the reeds loose one by one, and together they drew the wet braid from the runnel."
        ),
        proof=(
            "The foam wheel broke apart at once, and a straight current reached for the misty ship."
        ),
    ),
    "shell_scoop": Method(
        id="shell_scoop",
        solves="wedge",
        tool="their cupped hands and a snail-shell scoop",
        action=(
            "Toma steadied the little bowl with both hands while Mira slipped a snail-shell scoop under the pebble and lifted it free."
        ),
        proof=(
            "The trapped float rose instead of knocking helplessly against the stone."
        ),
    ),
    "moss_brush": Method(
        id="moss_brush",
        solves="silt",
        tool="a leaf cup and a soft moss brush",
        action=(
            "Mira poured clear puddle water from a folded leaf cup while Toma brushed the groove with soft moss until the packed mud loosened."
        ),
        proof=(
            "A bright ribbon of water began to thread along the sill instead of stopping short."
        ),
    ),
}

PLACE_LABELS = {
    "runnel": "the little runnel at the puddle's edge",
    "latch_bowl": "the small latch bowl below the crystal door",
    "sill_groove": "the silver groove beneath the crystal door",
}

KIND_LABELS = {
    "dam": "a reed dam in the runnel",
    "wedge": "a pebble wedged in the latch bowl",
    "silt": "packed silt sealing the groove",
}


def sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def end_sentence(text: str) -> str:
    return text if text.endswith((".", "!", "?")) else f"{text}."


def explain_rejection(puddle_id: str, clue_id: str, cause_id: str, method_id: str) -> str:
    if puddle_id not in PUDDLES:
        return f"unknown puddle: {puddle_id}"
    if clue_id not in CLUES:
        return f"unknown clue: {clue_id}"
    if cause_id not in CAUSES:
        return f"unknown cause: {cause_id}"
    if method_id not in METHODS:
        return f"unknown method: {method_id}"
    puddle = PUDDLES[puddle_id]
    clue = CLUES[clue_id]
    cause = CAUSES[cause_id]
    method = METHODS[method_id]
    reasons: list[str] = []
    if clue.place != cause.place:
        reasons.append("the clue must point to the same place where the real obstruction lives")
    if method.solves != cause.kind:
        reasons.append("the repair method has to match the physical trouble in the puddle")
    if cause.place not in puddle.sites:
        reasons.append(f"{puddle.name} does not route this crystal door tale through {PLACE_LABELS[cause.place]}")
    if not reasons:
        return "the requested story is valid"
    return "; ".join(reasons)


def valid_params(params: StoryParams) -> tuple[bool, str]:
    reason = explain_rejection(params.puddle, params.clue, params.cause, params.method)
    return (reason == "the requested story is valid", reason)


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for puddle in PUDDLES:
        for clue in CLUES:
            for cause in CAUSES:
                for method in METHODS:
                    params = StoryParams(puddle=puddle, clue=clue, cause=cause, method=method)
                    if valid_params(params)[0]:
                        combos.append(params)
    return combos


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    combos = all_params()
    if args.puddle:
        combos = [combo for combo in combos if combo.puddle == args.puddle]
    if args.clue:
        combos = [combo for combo in combos if combo.clue == args.clue]
    if args.cause:
        combos = [combo for combo in combos if combo.cause == args.cause]
    if args.method:
        combos = [combo for combo in combos if combo.method == args.method]
    return combos


def make_world(params: StoryParams) -> PuddleWorld:
    puddle = PUDDLES[params.puddle]
    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]

    world = PuddleWorld(params)
    world.add(Entity("mira", "character", "girl", "Mira", role="hero", traits=["curious", "careful"]))
    world.add(Entity("toma", "character", "boy", "Toma", role="friend", traits=["steady", "kind"]))
    world.add(Entity("team", "group", "pair", "the two children", role="team"))
    world.add(Entity("puddle", "place", "puddle", "the deep puddle"))
    world.add(Entity("ship", "object", "boat", "the misty ship"))
    world.add(Entity("door", "object", "door", "the crystal door"))
    world.add(Entity("runnel", "mechanism", "runnel", PLACE_LABELS["runnel"]))
    world.add(Entity("latch_bowl", "mechanism", "bowl", PLACE_LABELS["latch_bowl"]))
    world.add(Entity("sill_groove", "mechanism", "groove", PLACE_LABELS["sill_groove"]))
    world.add(Entity("lamp", "object", "lamp", "the chestnut-shell lamp"))

    world.get("puddle").meters["depth"] = 3.0
    world.get("puddle").meters["current"] = 2.0
    world.get("puddle").meters["clarity"] = 2.0
    world.get("ship").meters["progress"] = 0.0
    world.get("ship").meters["drift"] = 1.0
    world.get("door").meters["stuckness"] = 2.0
    world.get("door").meters["open"] = 0.0
    world.get("door").meters["gleam"] = 1.0
    world.get("team").memes["teamwork"] = 1.5
    world.get("team").memes["worry"] = 0.0
    world.get("team").memes["relief"] = 0.0
    world.get("mira").memes["curiosity"] = 2.0
    world.get("toma").memes["trust"] = 1.5
    world.get(cause.place).meters["problem_here"] = 1.0

    world.facts.update(
        puddle_name=puddle.name,
        clue_text=clue.text,
        clue_hint=clue.hint,
        doubt=clue.doubt,
        place_label=PLACE_LABELS[cause.place],
        kind_label=KIND_LABELS[cause.kind],
        tool=method.tool,
        proverb="Still water reflects a wish, but moving water tells the truth.",
    )
    return world


def opening(world: PuddleWorld) -> None:
    puddle = PUDDLES[world.params.puddle]
    world.get("team").memes["wonder"] += 1.0
    world.get("mira").memes["curiosity"] += 0.5
    world.record(
        "opening",
        f"{puddle.opening} {puddle.door_play}",
        "puddle",
        "door",
        "puddle",
    )
    world.record(
        "setup",
        "Mira and Toma set a chestnut-shell lamp inside the misty ship, for they wished to see it pass through the crystal door before the sun drank the puddle away. Mira's curiosity burned bright, and Toma smiled because he liked any task they could do together.",
        "team",
        "ship",
        "puddle",
    )


def problem_appears(world: PuddleWorld) -> None:
    puddle = PUDDLES[world.params.puddle]
    world.get("team").memes["worry"] += 1.0
    world.get("puddle").meters["current"] -= 1.0
    world.get("ship").meters["drift"] -= 0.5
    world.get("door").meters["stuckness"] += 1.0
    world.record(
        "problem",
        f"But when they nudged the misty ship from the near shore, it wandered in a slow circle and never reached the crystal door. In {puddle.name}, the water gave only a tired pull, and the clear panel stayed shut.",
        "ship",
        "door",
        "puddle",
    )


def notice_clue(world: PuddleWorld) -> None:
    clue = CLUES[world.params.clue]
    world.get("mira").memes["curiosity"] += 1.0
    world.record(
        "clue",
        f"{clue.text} {end_sentence(sentence_start(clue.hint))}",
        "hero",
        clue.place,
        clue.place,
    )


def reject_wild_guess(world: PuddleWorld) -> None:
    clue = CLUES[world.params.clue]
    world.get("team").memes["worry"] += 0.4
    world.record(
        "guess",
        f"{clue.doubt} Yet Mira shook her head. \"A true mystery leaves a footprint,\" she said. \"Let us follow what the puddle keeps repeating.\"",
        "friend",
        "hero",
        clue.place,
    )


def turn_to_reasoning(world: PuddleWorld) -> None:
    cause = CAUSES[world.params.cause]
    if cause.kind == "dam":
        theory = "If the runnel was blocked, the ship would never find the straight pull it needed."
    elif cause.kind == "wedge":
        theory = "If something held the latch float down, the ship could knock all day and still leave the door asleep."
    else:
        theory = "If the groove could not carry water under the panel, the door would never feel the lift meant for it."
    world.facts["theory"] = theory
    world.get("team").memes["teamwork"] += 0.6
    world.record(
        "turn",
        f'Mira remembered an old saying from her grandmother: "{world.facts["proverb"]}" So the children knelt shoulder to shoulder, listened to the puddle again, and made a careful guess: {theory}',
        "hero",
        cause.place,
        cause.place,
    )


def inspect_problem(world: PuddleWorld) -> None:
    cause = CAUSES[world.params.cause]
    world.get("mira").memes["curiosity"] += 0.8
    world.get("toma").memes["trust"] += 0.5
    world.get("team").memes["teamwork"] += 1.0
    world.record(
        "inspect",
        f"So they searched {PLACE_LABELS[cause.place]} instead of blaming moon-fog or sleepy magic. {cause.motion} Soon they found the proof: {end_sentence(cause.discovery)}",
        "team",
        cause.place,
        cause.place,
    )


def solve_problem(world: PuddleWorld) -> None:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    world.get("puddle").meters["current"] += 2.0
    world.get("puddle").meters["clarity"] += 1.0
    world.get("ship").meters["progress"] = 1.0
    world.get("ship").meters["drift"] = 2.0
    world.get("door").meters["stuckness"] = 0.0
    world.get("door").meters["open"] = 1.0
    world.get("team").memes["relief"] += 1.0
    world.get("team").memes["teamwork"] += 1.0
    world.facts["solved"] = True
    world.record(
        "solve",
        f"{method.action} {method.proof} {cause.result}",
        "team",
        "door",
        cause.place,
    )


def ending(world: PuddleWorld) -> None:
    puddle = PUDDLES[world.params.puddle]
    world.get("team").memes["wonder"] += 1.0
    world.record(
        "ending",
        f"The children watched the chestnut-shell lamp sail in the misty ship until it kissed the threshold and slipped through the crystal door. They laughed softly, not because magic had done their work, but because curiosity had found the answer and teamwork had carried it through. By the time the sun climbed over the hedge, {puddle.ending}.",
        "team",
        "ship",
        "puddle",
    )


def tell(params: StoryParams) -> PuddleWorld:
    world = make_world(params)
    opening(world)
    world.para()
    problem_appears(world)
    notice_clue(world)
    reject_wild_guess(world)
    turn_to_reasoning(world)
    world.para()
    inspect_problem(world)
    solve_problem(world)
    world.para()
    ending(world)
    return world


def generation_prompts(world: PuddleWorld) -> list[str]:
    return [
        'Write a child-facing folk tale set at a deep puddle and include the exact phrases "misty ship" and "crystal door."',
        f"Build the turn around a repeating clue at {world.facts['place_label']} and let curiosity uncover the real physical problem.",
        "Resolve the story through teamwork, and end with a vivid image that proves the water path and the door truly changed.",
    ]


def story_grounded_qa(world: PuddleWorld) -> list[QAItem]:
    clue = CLUES[world.params.clue]
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why could the misty ship not reach the crystal door at first?",
            answer=(
                f"The misty ship could not reach the crystal door because of {KIND_LABELS[cause.kind]}. "
                f"{cause.motion} That changed the puddle's movement, so the ship drifted badly or the door could not respond."
            ),
        ),
        QAItem(
            question="What clue made Mira and Toma investigate the right place?",
            answer=(
                f"The clue was that {clue.text.lower()} "
                f"Because the same sign returned in the same spot, the children understood that the puddle was revealing a real cause instead of a random wonder."
            ),
        ),
        QAItem(
            question="How did teamwork help solve the problem?",
            answer=(
                f"Teamwork mattered because the children used {method.tool} together instead of fumbling alone. "
                f"{method.action} Their shared work let them test the right idea safely and finish the repair before the puddle changed again."
            ),
        ),
        QAItem(
            question="What proved that the world had changed by the end?",
            answer=(
                "The ending proved the change because the misty ship finally reached the threshold and passed through the crystal door. "
                "The straightened current, the moving panel, and the bright final image showed that the children had fixed the real trouble in the puddle."
            ),
        ),
    ]


def world_knowledge_qa(world: PuddleWorld) -> list[QAItem]:
    cause = CAUSES[world.params.cause]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why is curiosity useful in a small physical mystery?",
            answer=(
                "Curiosity helps because it makes a person stay with a strange sign long enough to compare it, test it, and ask what keeps repeating. "
                "Without that patient attention, a real cause can look like random magic."
            ),
        ),
        QAItem(
            question="Why was the correct tool important in this puddle story?",
            answer=(
                f"The correct tool mattered because the trouble was {KIND_LABELS[cause.kind]}, not a problem that force could solve. "
                f"Using {method.tool} matched the shape of the obstruction and let the children repair the water path instead of harming the door."
            ),
        ),
        QAItem(
            question="Why can a small change in water flow matter so much to a floating object?",
            answer=(
                "A floating object depends on direction as much as movement, so even a tiny blockage can bend its path or weaken a mechanism that expects steady flow. "
                "When the water finally runs true, the object and the system around it can behave very differently."
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
valid(P,C,A,M) :-
    puddle(P), clue(C), cause(A), method(M),
    clue_place(C, S), cause_place(A, S),
    cause_kind(A, K), method_solves(M, K),
    puddle_site(P, S).

ok :- chosen(P, C, A, M), valid(P, C, A, M).

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
    for cause_id, cause in CAUSES.items():
        lines.append(fact("cause", cause_id))
        lines.append(fact("cause_place", cause_id, cause.place))
        lines.append(fact("cause_kind", cause_id, cause.kind))
    for method_id, method in METHODS.items():
        lines.append(fact("method", method_id))
        lines.append(fact("method_solves", method_id, method.solves))
    if params is not None:
        lines.append(fact("chosen", params.puddle, params.clue, params.cause, params.method))
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
        raise AssertionError("crystal door never opened")
    if world.get("door").meters.get("stuckness", 1) != 0:
        raise AssertionError("door stayed stuck")
    if world.get("ship").meters.get("progress", 0) < 1:
        raise AssertionError("misty ship never completed its passage")
    if world.get("team").memes.get("teamwork", 0) < 3:
        raise AssertionError("teamwork never strengthened")
    if world.get("mira").memes.get("curiosity", 0) < 3:
        raise AssertionError("curiosity never drove the search")
    if not world.facts.get("solved"):
        raise AssertionError("story never marked itself solved")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 14:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = sorted((params.puddle, params.clue, params.cause, params.method) for params in all_params())
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
    parser.add_argument("--cause", choices=sorted(CAUSES))
    parser.add_argument("--method", choices=sorted(METHODS))
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
    explicit = all(getattr(args, field) is not None for field in ("puddle", "clue", "cause", "method"))
    if explicit:
        params = StoryParams(args.puddle, args.clue, args.cause, args.method, args.seed)
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    combos = matching_params(args)
    if not combos:
        puddle = args.puddle or next(iter(PUDDLES))
        clue = args.clue or next(iter(CLUES))
        cause = args.cause or next(iter(CAUSES))
        method = args.method or next(iter(METHODS))
        raise StoryError(explain_rejection(puddle, clue, cause, method))
    chosen = StoryParams(**vars(rng.choice(combos)))
    chosen.seed = args.seed
    return chosen


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_params(args)
        if not combos:
            puddle = args.puddle or next(iter(PUDDLES))
            clue = args.clue or next(iter(CLUES))
            cause = args.cause or next(iter(CAUSES))
            method = args.method or next(iter(METHODS))
            raise StoryError(explain_rejection(puddle, clue, cause, method))
        samples: list[StorySample] = []
        for index, params in enumerate(combos):
            chosen = StoryParams(**vars(params))
            chosen.seed = args.seed + index if args.seed is not None else None
            samples.append(generate(chosen))
        return samples

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    combos = matching_params(args)
    if not combos:
        puddle = args.puddle or next(iter(PUDDLES))
        clue = args.clue or next(iter(CLUES))
        cause = args.cause or next(iter(CAUSES))
        method = args.method or next(iter(METHODS))
        raise StoryError(explain_rejection(puddle, clue, cause, method))

    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = base_seed + index
        rng = random.Random(seed)
        chosen = StoryParams(**vars(rng.choice(combos)))
        chosen.seed = seed
        samples.append(generate(chosen))
    return samples


def dump_trace(world: PuddleWorld) -> str:
    lines = ["TRACE", f"puddle: {world.facts['puddle_name']}"]
    for event in world.history:
        where = f" @ {event.place}" if event.place else ""
        lines.append(f"- {event.id}{where}: {event.text}")
    lines.append("ENTITIES")
    for entity in world.entities.values():
        if entity.role and entity.role != entity.id:
            continue
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
            print("  " + " ".join(f"{part:14}" for part in combo))
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
            header = f"=== misty_ship_crystal_door_deep_puddle_teamwork #{index} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
