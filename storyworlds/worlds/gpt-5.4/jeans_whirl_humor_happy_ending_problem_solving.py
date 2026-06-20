#!/usr/bin/env python3
"""A fairy-tale laundry storyworld about parade jeans, comic whirls, and careful repair.

Internal source tale:
In a fairy-tale laundry green, two children must ready a pair of parade jeans
for the Moonwhirl Fair. A silly physical fault makes the wet jeans whirl in a
funny, troublesome way, and at first the children almost blame sprites or
windy magic. But the same clue returns again and again, so they inspect the
right place, use the right tool, and fix the real problem. The story ends with
the jeans hanging true, the village laughing, and a happy image that proves
the trouble is over.
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

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


SOURCE_TALE = (
    "In a fairy-tale laundry green, two children must ready a pair of parade jeans "
    "for the Moonwhirl Fair. A comic physical fault makes the wet jeans whirl in the "
    "wrong way, but a repeating clue leads them to the true cause. With help, patience, "
    "and the right tool, they solve the trouble and end with laughter under clean blue cloth."
)


@dataclass(frozen=True)
class LaundryGround:
    key: str
    name: str
    opening: str
    comic_detail: str
    ending_image: str
    sites: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    key: str
    place: str
    kind: str
    crash_text: str
    clue_text: str
    discovery: str
    motion: str
    result: str


@dataclass(frozen=True)
class Remedy:
    key: str
    solves: str
    tool: str
    action: str
    proof: str
    lesson: str


@dataclass(frozen=True)
class DuoChoice:
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
    advice: str


@dataclass
class StoryParams:
    ground: str
    problem: str
    remedy: str
    duo: str
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
class LaundryWorld:
    params: StoryParams
    ground: LaundryGround
    problem: Problem
    remedy: Remedy
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

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

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


GROUNDS: dict[str, LaundryGround] = {
    "indigo_green": LaundryGround(
        key="indigo_green",
        name="Indigo Wash Green",
        opening=(
            "At Indigo Wash Green, a bright brook turned a washing wheel beside a ribbon fence, "
            "and the parade jeans for the Moonwhirl Fair hung over a willow rail like two sleepy blue giants."
        ),
        comic_detail=(
            "A striped goose kept bowing to the brass buttons because it had decided the pockets belonged to a very polite king."
        ),
        ending_image=(
            "the jeans hung straight as banners over the brook while the goose marched through one empty cuff as if it were a palace gate"
        ),
        sites=("wheel", "line"),
    ),
    "silver_trough": LaundryGround(
        key="silver_trough",
        name="Silver Trough Court",
        opening=(
            "In Silver Trough Court, moon-bright basins stood in a row under pearly trees, "
            "and the parade jeans waited for the Moonwhirl Fair on a cedar bench beside the rinsing water."
        ),
        comic_detail=(
            "A milk-white kitten kept diving into the back pocket and peeking out again as if the jeans were a soft blue cave."
        ),
        ending_image=(
            "the jeans shone blue and calm on the drying rail while the kitten peered from the pocket and made the whole court laugh"
        ),
        sites=("drain", "wheel"),
    ),
    "rosebridge_lawn": LaundryGround(
        key="rosebridge_lawn",
        name="Rosebridge Laundry Lawn",
        opening=(
            "Beyond Rosebridge Laundry Lawn, garlands of clothespins glittered above the grass, "
            "and the parade jeans for the Moonwhirl Fair waited by a rose-red post to catch the afternoon breeze."
        ),
        comic_detail=(
            "Three sparrows argued over whether the watch pocket was a window, a pantry, or a secret room for very small knights."
        ),
        ending_image=(
            "the jeans faced the breeze without a twist, and the sparrows sat along the hem like tiny heralds admiring a royal flag"
        ),
        sites=("line", "drain"),
    ),
}


PROBLEMS: dict[str, Problem] = {
    "bent_vane": Problem(
        key="bent_vane",
        place="wheel",
        kind="wobble",
        crash_text=(
            "The rinse wheel took one proud turn, then the tub bumped the rail with a comic bonk, "
            "and the wet jeans began to whirl so fast that one empty leg saluted the nearest bird."
        ),
        clue_text=(
            "Each time the children tried again, one side of the wheel dipped with the same wooden click, "
            "and the jeans slid into that same crooked whirl."
        ),
        discovery=(
            "Behind the spray, one willow vane on the wheel was bent inward like a crooked spoon."
        ),
        motion=(
            "The bent vane caught too much water on one side, so the wheel pulled unevenly and made the jeans whirl in a lopsided spin."
        ),
        result=(
            "Once the vane stood true again, the wheel turned round and the tub stopped shoving the jeans into wild circles."
        ),
    ),
    "soap_clog": Problem(
        key="soap_clog",
        place="drain",
        kind="clog",
        crash_text=(
            "Foam puffed, the basin gurgled, and the wet jeans began to whirl around the trough until a blue pocket slapped the bell rope with a wet plop."
        ),
        clue_text=(
            "The same bubble ring rose from the drain each time, and the water kept circling toward that one dark mouth."
        ),
        discovery=(
            "A pebble, two plum pits, and a clot of soap had lodged in the drain grate."
        ),
        motion=(
            "Because the drain could not sip the water evenly, the basin pulled the rinse into one stubborn whirl and dragged the jeans after it."
        ),
        result=(
            "When the drain ran clear, the water settled into a calm round shimmer and the jeans stopped circling like dancers who had missed the music."
        ),
    ),
    "sleepy_knot": Problem(
        key="sleepy_knot",
        place="line",
        kind="slip",
        crash_text=(
            "When the children tried to hang the wet jeans, the drying line snapped into a whirl, "
            "and the trousers spun so neatly that both legs pointed at the moon at once."
        ),
        clue_text=(
            "The same knot hopped loose at the left post every time the cloth tugged, and the line twisted back upon itself."
        ),
        discovery=(
            "The children found a polished knot that had gone slack where the drying line kissed the post ring."
        ),
        motion=(
            "That sleepy knot let the line twist under the wet weight, so the jeans kept turning instead of hanging straight."
        ),
        result=(
            "With the knot firm again, the line held steady and the jeans faced the breeze instead of chasing it."
        ),
    ),
}


REMEDIES: dict[str, Remedy] = {
    "moon_spanner": Remedy(
        key="moon_spanner",
        solves="wobble",
        tool="the cedar moon spanner",
        action=(
            "{helper} braced the tub while {first} held the wheel still and {second} turned {tool} with both hands until the crooked vane sat true beside its sisters."
        ),
        proof=(
            "When they tested the wheel again, the wooden click vanished and the jeans no longer lurched into a crooked spin."
        ),
        lesson=(
            "They solved the trouble by straightening the one part that kept tipping the whole rinse."
        ),
    ),
    "star_scoop": Remedy(
        key="star_scoop",
        solves="clog",
        tool="the tin star scoop",
        action=(
            "{first} lifted the drain grate with {tool} while {second} gathered the plum pits and soap clot in a little pan, and {helper} flushed the channel with a bright ribbon of clean water."
        ),
        proof=(
            "The next rinse flowed down in a quiet gulp, and the bubble ring never came back to call the jeans into a whirl."
        ),
        lesson=(
            "They solved the trouble by clearing the narrow throat that had been pulling the water the wrong way."
        ),
    ),
    "sun_clips": Remedy(
        key="sun_clips",
        solves="slip",
        tool="the brass sun clips",
        action=(
            "{second} retied the sleepy knot, {first} set {tool} at both cuffs, and {helper} pulled the line snug until it sang a small bright note."
        ),
        proof=(
            "At the next gust, the line stayed true and the jeans flapped like two proud flags instead of spinning around the post."
        ),
        lesson=(
            "They solved the trouble by giving the wet cloth a steadier hold than the twisting breeze could steal."
        ),
    ),
}


DUOS: dict[str, DuoChoice] = {
    "nella_pip": DuoChoice("nella_pip", "Nella", "girl", "Pip", "boy"),
    "iris_finn": DuoChoice("iris_finn", "Iris", "girl", "Finn", "boy"),
    "toma_bess": DuoChoice("toma_bess", "Toma", "boy", "Bess", "girl"),
}


HELPERS: dict[str, HelperChoice] = {
    "juniper": HelperChoice(
        key="juniper",
        name="Juniper",
        type="woman",
        role="tailor of festival cloth",
        trait="patient",
        advice='"When the same clue bows twice, bow back and follow it."',
    ),
    "bram": HelperChoice(
        key="bram",
        name="Bram",
        type="man",
        role="keeper of the rinse wheel",
        trait="steady",
        advice='"A whirl is only a riddle when you have not yet found what keeps turning it."',
    ),
    "clover": HelperChoice(
        key="clover",
        name="Auntie Clover",
        type="woman",
        role="mistress of the drying lawn",
        trait="observant",
        advice='"Do not scold the whole day when one small part is asking for help."',
    ),
}


PLACE_LABELS = {
    "wheel": "the rinsing wheel",
    "drain": "the silver drain grate",
    "line": "the drying line by the post ring",
}


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for ground_key, ground in sorted(GROUNDS.items()):
        for problem_key, problem in sorted(PROBLEMS.items()):
            for remedy_key, remedy in sorted(REMEDIES.items()):
                if problem.place not in ground.sites:
                    continue
                if remedy.solves != problem.kind:
                    continue
                for duo_key in sorted(DUOS):
                    for helper_key in sorted(HELPERS):
                        combos.append((ground_key, problem_key, remedy_key, duo_key, helper_key))
    return combos


def _unknown_reason(kind: str, value: str, options: dict[str, object]) -> str:
    opts = ", ".join(sorted(options))
    return f"No story: unknown {kind} {value!r}. Try one of: {opts}."


def explain_rejection(
    ground_key: str,
    problem_key: str,
    remedy_key: str,
    duo_key: str,
    helper_key: str,
) -> str:
    if ground_key not in GROUNDS:
        return _unknown_reason("ground", ground_key, GROUNDS)
    if problem_key not in PROBLEMS:
        return _unknown_reason("problem", problem_key, PROBLEMS)
    if remedy_key not in REMEDIES:
        return _unknown_reason("remedy", remedy_key, REMEDIES)
    if duo_key not in DUOS:
        return _unknown_reason("duo", duo_key, DUOS)
    if helper_key not in HELPERS:
        return _unknown_reason("helper", helper_key, HELPERS)
    ground = GROUNDS[ground_key]
    problem = PROBLEMS[problem_key]
    remedy = REMEDIES[remedy_key]
    if problem.place not in ground.sites:
        sites = ", ".join(ground.sites)
        return (
            f"No story: {ground.name} does not expose a {problem.place} fault. "
            f"That laundry ground only supports these repair sites: {sites}."
        )
    if remedy.solves != problem.kind:
        return (
            f"No story: remedy {remedy_key!r} solves {remedy.solves}, but problem {problem_key!r} is a {problem.kind} fault. "
            "Use the tool that fits the physical trouble."
        )
    return "No story: invalid laundry whirl."


def valid_params(params: StoryParams) -> tuple[bool, str]:
    reason = explain_rejection(
        params.ground,
        params.problem,
        params.remedy,
        params.duo,
        params.helper,
    )
    if reason == "No story: invalid laundry whirl.":
        return True, ""
    return False, reason


def params_from_combo(combo: tuple[str, str, str, str, str], seed: int) -> StoryParams:
    return StoryParams(
        ground=combo[0],
        problem=combo[1],
        remedy=combo[2],
        duo=combo[3],
        helper=combo[4],
        seed=seed,
    )


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str, str]]:
    combos = valid_combos()
    return [
        combo
        for combo in combos
        if (args.ground is None or combo[0] == args.ground)
        and (args.problem is None or combo[1] == args.problem)
        and (args.remedy is None or combo[2] == args.remedy)
        and (args.duo is None or combo[3] == args.duo)
        and (args.helper is None or combo[4] == args.helper)
    ]


def build_world(params: StoryParams) -> LaundryWorld:
    ground = GROUNDS[params.ground]
    problem = PROBLEMS[params.problem]
    remedy = REMEDIES[params.remedy]
    duo = DUOS[params.duo]
    helper_choice = HELPERS[params.helper]

    world = LaundryWorld(params=params, ground=ground, problem=problem, remedy=remedy)

    first = world.add(Entity("first", "character", duo.first_type, duo.first, role="first", traits=["curious"]))
    second = world.add(Entity("second", "character", duo.second_type, duo.second, role="second", traits=["careful"]))
    helper = world.add(
        Entity("helper", "character", helper_choice.type, helper_choice.name, role="helper", traits=[helper_choice.trait])
    )
    team = world.add(
        Entity(
            "team",
            "group",
            "children",
            f"{duo.first} and {duo.second}",
            role="team",
            traits=["playful", "steadfast"],
        )
    )
    jeans = world.add(
        Entity(
            "jeans",
            "object",
            "jeans",
            "the parade jeans",
            role="jeans",
            traits=["blue", "broad", "festival"],
        )
    )
    site = world.add(
        Entity(
            problem.place,
            "mechanism",
            problem.place,
            PLACE_LABELS[problem.place],
            role="site",
            traits=["small", "important"],
        )
    )
    world.add(Entity("ground", "place", "laundry_ground", ground.name, role="ground", traits=["storybook"]))

    jeans.meters["cleanliness"] = 1.2
    jeans.meters["dryness"] = 0.3
    jeans.meters["straightness"] = 0.2
    jeans.meters["twist"] = 1.0
    site.meters["fault"] = 1.0
    team.memes["wonder"] = 1.0
    team.memes["worry"] = 0.4
    team.memes["resolve"] = 0.2
    team.memes["glee"] = 0.8
    helper.memes["patience"] = 1.0

    world.facts["source_tale"] = SOURCE_TALE
    world.facts["seed_word_a"] = "jeans"
    world.facts["seed_word_b"] = "whirl"
    world.facts["festival"] = "Moonwhirl Fair"
    world.facts["site"] = problem.place
    world.facts["site_label"] = PLACE_LABELS[problem.place]
    world.facts["problem_kind"] = problem.kind
    world.facts["tool"] = remedy.tool
    world.facts["helper_role"] = helper_choice.role
    world.facts["solved"] = False
    world.facts["ending"] = "pending"
    return world


def build_false_guess(world: LaundryWorld) -> str:
    if world.problem.place == "wheel":
        return (
            "For one laughing breath, the children wondered whether a dance sprite had climbed into the pocket and ordered the whole wheel to jig. "
            "But the very same dip came back in the very same place, which sounded far more like a clue than a spell."
        )
    if world.problem.place == "drain":
        return (
            "They almost blamed a thirsty whirl sprite under the basin. "
            "Then the same bubble ring rose from the same mouth again, and the joke turned into evidence."
        )
    return (
        "For a blink, they suspected the evening breeze wanted to wear the jeans for itself. "
        "Then the same knot leaped loose again, and even the children had to laugh at such an honest clue."
    )


def upper_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def causal_clause(text: str) -> str:
    lowered = text.strip()
    if lowered.lower().startswith("because "):
        lowered = lowered[8:]
    return lower_first(lowered)


def tell(world: LaundryWorld) -> LaundryWorld:
    first = world.get("first")
    second = world.get("second")
    helper = world.get("helper")
    team = world.get("team")
    jeans = world.get("jeans")
    site = world.get("site")
    ground = world.ground
    problem = world.problem
    remedy = world.remedy
    helper_role = str(world.facts["helper_role"])
    site_label = str(world.facts["site_label"])

    world.record(
        "opening",
        f"{ground.opening} {ground.comic_detail}",
        actor="narrator",
        target="ground",
    )
    world.record(
        "goal",
        (
            f"That afternoon, {first.label} and {second.label} promised to ready the parade jeans before the Moonwhirl Fair, "
            "so the cloth could wave above the lane like a cheerful royal banner."
        ),
        actor="team",
        target="jeans",
    )
    world.para()

    world.record("crash", problem.crash_text, actor="jeans", target=problem.place)
    team.memes["worry"] += 0.7
    team.memes["wonder"] += 0.2
    world.record("false_guess", build_false_guess(world), actor="team", target="jeans")
    world.record("clue", problem.clue_text, actor="team", target=problem.place)
    world.record(
        "helper_hint",
        f'{helper.label}, the {helper_role}, tapped {site_label} and said, {HELPERS[world.params.helper].advice}',
        actor="helper",
        target=problem.place,
    )
    world.para()

    world.record(
        "inspect",
        f"So {first.label} and {second.label} stopped fussing at the whole pair of jeans and followed the clue to {site_label}.",
        actor="team",
        target=problem.place,
    )
    world.record("discovery", problem.discovery, actor="team", target=problem.place)
    world.record("diagnosis", problem.motion, actor="team", target=problem.place)
    team.memes["resolve"] += 1.0
    world.para()

    world.record(
        "solve",
        remedy.action.format(
            first=first.label,
            second=second.label,
            helper=helper.label,
            tool=remedy.tool,
        ),
        actor="team",
        target=problem.place,
    )
    site.meters["fault"] = 0.0
    jeans.meters["twist"] = 0.0
    jeans.meters["straightness"] = 2.3
    jeans.meters["dryness"] = 1.4
    team.memes["glee"] += 0.8
    team.memes["resolve"] += 0.4
    team.memes["worry"] = 0.0
    world.record("proof", f"{remedy.proof} {problem.result}", actor="jeans", target="jeans")
    world.facts["solved"] = True
    world.para()

    world.record(
        "ending",
        (
            f"By sunset, the parade jeans were ready at last. {upper_first(ground.ending_image)}. "
            f"Even {helper.label} laughed as {first.label} bowed to the trousers as if they were two sleepy blue giants. {remedy.lesson}"
        ),
        actor="team",
        target="jeans",
    )
    world.facts["ending"] = "happy"
    return world


def generation_prompts(world: LaundryWorld) -> list[str]:
    first = world.get("first").label
    second = world.get("second").label
    return [
        'Write a child-facing fairy tale that clearly includes the words "jeans" and "whirl."',
        f"Give {first} and {second} a funny physical problem to solve by following a repeating clue instead of blaming magic.",
        "End with a vivid happy image that proves the jeans are truly fixed and ready for the fair.",
    ]


def story_grounded_qa(world: LaundryWorld) -> list[QAItem]:
    first = world.get("first").label
    second = world.get("second").label
    helper = world.get("helper").label
    ground = world.ground
    problem = world.problem
    remedy = world.remedy
    site_label = str(world.facts["site_label"])
    return [
        QAItem(
            question="Why did the parade jeans begin to whirl the wrong way?",
            answer=(
                f"The parade jeans began to whirl the wrong way because {causal_clause(problem.motion)} "
                f"That physical trouble kept pulling the cloth off balance before {first} and {second} could finish readying it for the fair."
            ),
        ),
        QAItem(
            question="Which clue helped the children solve the problem?",
            answer=(
                f"The useful clue was this: {problem.clue_text.lower()} "
                f"Because the same sign returned in the same place, the children knew they should inspect {site_label} instead of guessing wildly."
            ),
        ),
        QAItem(
            question="How did the children fix the whirling jeans?",
            answer=(
                f"They used {remedy.tool} exactly where the clue pointed. {remedy.proof} "
                "That showed the repair matched the real cause instead of covering the trouble with hopeful talk."
            ),
        ),
        QAItem(
            question="What part did the helper play in the solution?",
            answer=(
                f"{helper} helped by slowing the children down and teaching them to trust the repeating clue. "
                "The helper did not solve the trouble alone, but turned laughter and surprise into careful problem solving."
            ),
        ),
        QAItem(
            question="Why is the story funny as well as happy?",
            answer=(
                f"The story is funny because the jeans behave almost like silly giants, and even the crash sends a cuff or pocket doing something ridiculous. "
                f"It is happy because the children repair the real fault and end with this image: {ground.ending_image}."
            ),
        ),
        QAItem(
            question="How does the ending prove that the trouble is really over?",
            answer=(
                f"The ending proves the trouble is over because {ground.ending_image}. "
                "That calm final picture could only happen after the jeans stopped twisting and the proper repair held."
            ),
        ),
    ]


def world_knowledge_qa(world: LaundryWorld) -> list[QAItem]:
    remedy = world.remedy
    return [
        QAItem(
            question="Why must the repair match the kind of laundry fault in this world?",
            answer=(
                "Each problem in this world is physical, such as a wobble, a clog, or a slipping line. "
                "The story stays reasonable only when the tool fits the material trouble instead of pretending that any cheerful motion can fix wet cloth."
            ),
        ),
        QAItem(
            question="Why is a repeating clue important in a problem-solving fairy tale?",
            answer=(
                "A repeating clue matters because it points to a cause that is still active in the world. "
                "When the same sign returns, careful children can test one place instead of blaming luck, mood, or magic."
            ),
        ),
        QAItem(
            question="Why do wet jeans need both balance and support while they dry?",
            answer=(
                "Wet jeans are heavy, so a small fault can twist them or pull a line out of shape. "
                "Good balance and support let the cloth hang straight, dry evenly, and show that the repair truly worked."
            ),
        ),
        QAItem(
            question="Why does the right tool matter more than quick guessing here?",
            answer=(
                f"The right tool matters because it acts on the exact place where the trouble lives, and in this story that tool is {remedy.tool}. "
                "Quick guessing may sound exciting, but it cannot straighten, clear, or secure the part that keeps the whirl going."
            ),
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
valid(G,P,R,D,H) :-
    ground(G),
    problem(P),
    remedy(R),
    duo(D),
    helper(H),
    problem_place(P, S),
    ground_site(G, S),
    problem_kind(P, K),
    remedy_solves(R, K).

ok :- chosen(G, P, R, D, H), valid(G, P, R, D, H).

#show valid/5.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    lines: list[str] = []
    for ground_key, ground in sorted(GROUNDS.items()):
        lines.append(fact("ground", ground_key))
        for site in ground.sites:
            lines.append(fact("ground_site", ground_key, site))
    for problem_key, problem in sorted(PROBLEMS.items()):
        lines.append(fact("problem", problem_key))
        lines.append(fact("problem_place", problem_key, problem.place))
        lines.append(fact("problem_kind", problem_key, problem.kind))
    for remedy_key, remedy in sorted(REMEDIES.items()):
        lines.append(fact("remedy", remedy_key))
        lines.append(fact("remedy_solves", remedy_key, remedy.solves))
    for duo_key in sorted(DUOS):
        lines.append(fact("duo", duo_key))
    for helper_key in sorted(HELPERS):
        lines.append(fact("helper", helper_key))
    if params is not None:
        lines.append(fact("chosen", params.ground, params.problem, params.remedy, params.duo, params.helper))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    from storyworlds.asp import atoms, one_model

    return sorted(atoms(one_model(asp_program()), "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    for needle in ("jeans", "whirl", "moonwhirl fair"):
        if needle not in story_lower:
            raise AssertionError(f"story is missing {needle!r}")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    if "meters=" in sample.story or "memes=" in sample.story:
        raise AssertionError("story leaked debug language")
    if world.get("jeans").meters.get("straightness", 0) < 2:
        raise AssertionError("jeans never recovered a straight hang")
    if world.get("jeans").meters.get("twist", 1) != 0:
        raise AssertionError("jeans still show a twisting problem")
    if world.get("jeans").meters.get("dryness", 0) < 1:
        raise AssertionError("jeans never reached a ready state")
    if world.get("site").meters.get("fault", 1) != 0:
        raise AssertionError("problem site stayed unresolved")
    if world.get("team").memes.get("resolve", 0) < 1:
        raise AssertionError("children never reached a problem-solving turn")
    if world.get("team").memes.get("worry", 1) != 0:
        raise AssertionError("worry never settled")
    if world.facts.get("ending") != "happy":
        raise AssertionError("story did not reach a happy ending")
    event_ids = {event.id for event in world.history}
    for required in ("crash", "clue", "discovery", "solve", "ending"):
        if required not in event_ids:
            raise AssertionError(f"missing event {required!r}")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 5 or len(sample.world_qa) < 4:
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
    print(f"OK: ASP parity matches Python gate ({len(py)} valid laundry fairy tales).")
    for index, combo in enumerate(py):
        verify_sample(generate(params_from_combo(combo, 2000 + index)))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a fairy-tale laundry story about jeans, a whirl, humor, and problem solving."
    )
    parser.add_argument("--ground", choices=sorted(GROUNDS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--remedy", choices=sorted(REMEDIES))
    parser.add_argument("--duo", choices=sorted(DUOS))
    parser.add_argument("--helper", choices=sorted(HELPERS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None, index: int = 0) -> StoryParams:
    seed = (args.seed if args.seed is not None else 13) + index
    combos = matching_combos(args)
    if not combos:
        ground = args.ground or next(iter(GROUNDS))
        problem = args.problem or next(iter(PROBLEMS))
        remedy = args.remedy or next(iter(REMEDIES))
        duo = args.duo or next(iter(DUOS))
        helper = args.helper or next(iter(HELPERS))
        raise StoryError(explain_rejection(ground, problem, remedy, duo, helper))

    explicit = all(getattr(args, field) is not None for field in ("ground", "problem", "remedy", "duo", "helper"))
    if explicit:
        params = params_from_combo((args.ground, args.problem, args.remedy, args.duo, args.helper), seed)
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
            ground = args.ground or next(iter(GROUNDS))
            problem = args.problem or next(iter(PROBLEMS))
            remedy = args.remedy or next(iter(REMEDIES))
            duo = args.duo or next(iter(DUOS))
            helper = args.helper or next(iter(HELPERS))
            raise StoryError(explain_rejection(ground, problem, remedy, duo, helper))
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


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid laundry fairy tales:\n")
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
            header = (
                "=== jeans_whirl_humor_happy_ending_problem_solving "
                f"#{index} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
