#!/usr/bin/env python3
"""A fairy-tale art-room storyworld about fixing a twinkling gate beside a dusty pond.

Internal source tale:
In a bright art room, two children paint a fairy mural with a twinkling gate
and a dusty pond. When the gate suddenly stops sparkling, they first blame the
stars on the gate itself. But the same clue appears three times in the pond's
surface, so they stop guessing, find the physical trouble, and mend the pond
with the right tool. Once the pond is clear, the gate shines again and the
whole mural proves the change.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class ArtRoom:
    id: str
    name: str
    opening: str
    helper: str
    tools: tuple[str, ...]
    ending: str


@dataclass(frozen=True)
class Pair:
    id: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    duo_label: str


@dataclass(frozen=True)
class Problem:
    id: str
    kind: str
    setup: str
    repeated_clue: str
    discovery: str
    theory: str
    result: str


@dataclass(frozen=True)
class Method:
    id: str
    solves: str
    needs: str
    tool_label: str
    action: str
    proof: str


@dataclass
class StoryParams:
    room: str
    pair: str
    problem: str
    method: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
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


@dataclass
class StoryWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        lines = [
            "TRACE",
            f"room: {self.facts['room_name']}",
            f"pair: {self.facts['duo_label']}",
            f"problem: {self.facts['problem_label']}",
            f"tool: {self.facts['tool_label']}",
        ]
        for event in self.history:
            lines.append(f"- {event.id}: {event.text}")
        lines.append("ENTITIES")
        for entity in self.entities.values():
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


ROOMS: dict[str, ArtRoom] = {
    "sun_easel": ArtRoom(
        id="sun_easel",
        name="Sun-Easel Art Room",
        opening=(
            "In the Sun-Easel art room, tall jars of brushes shone like a row of little towers, "
            "and paper banners curled from the ceiling as if a kind wind lived indoors."
        ),
        helper="Mistress Maren",
        tools=("sifter", "cloth"),
        ending="gold paint on the reeds glimmered, and the whole wall looked ready for a fairy queen to step through",
    ),
    "amber_window": ArtRoom(
        id="amber_window",
        name="Amber-Window Art Room",
        opening=(
            "In the Amber-Window art room, the late light spread over the tables like honey, "
            "and every paint cup looked as bright as a tiny jewel."
        ),
        helper="Teacher Elsi",
        tools=("cloth", "sponge"),
        ending="the amber window laid a warm ribbon over the water, and the mural looked deep enough for painted frogs to sing in it",
    ),
    "moon_paper": ArtRoom(
        id="moon_paper",
        name="Moon-Paper Art Room",
        opening=(
            "In the Moon-Paper art room, silver scraps and blue paper moons hung above the tables, "
            "so the room already felt like the first page of a fairy tale."
        ),
        helper="Master Ivo",
        tools=("sifter", "sponge"),
        ending="silver flecks floated over the paper cattails, and the pond caught the gate's light like a true little mirror",
    ),
}


PAIRS: dict[str, Pair] = {
    "lila_oren": Pair(
        id="lila_oren",
        hero_name="Lila",
        hero_type="girl",
        friend_name="Oren",
        friend_type="boy",
        duo_label="Lila and Oren",
    ),
    "anya_kip": Pair(
        id="anya_kip",
        hero_name="Anya",
        hero_type="girl",
        friend_name="Kip",
        friend_type="boy",
        duo_label="Anya and Kip",
    ),
}


PROBLEMS: dict[str, Problem] = {
    "chalk_haze": Problem(
        id="chalk_haze",
        kind="dust",
        setup=(
            "They had painted a twinkling gate at the edge of a dusty pond, but when the lamp was turned toward the mural, "
            "the tiny stars on the gate stayed dull instead of dancing."
        ),
        repeated_clue=(
            "Each time they tilted the mural, a pale blue ring drifted over the dusty pond again, "
            "as if the same sleepy ghost kept crossing the water."
        ),
        discovery=(
            "A veil of loose chalk dust lay on the pond glaze, muting the reflected light before it could reach the gate."
        ),
        theory=(
            "If chalk dust was sitting on the pond's shiny skin, the pond could not toss bright light back to the gate."
        ),
        result=(
            "When the haze was gone, the pond turned slick and deep-looking, and the gate stars woke up all at once."
        ),
    ),
    "glue_ridge": Problem(
        id="glue_ridge",
        kind="ripple",
        setup=(
            "They had painted a twinkling gate at the edge of a dusty pond, but when the lamp was turned toward the mural, "
            "the gate's silver points bent into crooked little lines."
        ),
        repeated_clue=(
            "Each time they tipped the board, one narrow crease crossed the dusty pond again, "
            "and the gate's reflection snagged on that same shining wrinkle."
        ),
        discovery=(
            "A hard glue ridge under the pond paper was pushing the surface upward like a tiny hidden dam."
        ),
        theory=(
            "If a ridge was buckling the pond paper, the water picture would keep breaking the gate's reflection."
        ),
        result=(
            "Once the ridge lay flat, the painted water looked smooth enough to carry a clean silver shimmer."
        ),
    ),
    "muddy_wash": Problem(
        id="muddy_wash",
        kind="muddy",
        setup=(
            "They had painted a twinkling gate at the edge of a dusty pond, but when the lamp was turned toward the mural, "
            "a brown shadow swallowed the place where the brightest stars should have gleamed."
        ),
        repeated_clue=(
            "Each time the board met the light, a dim brown crescent pooled over the dusty pond again, "
            "and the gate lost its prettiest spark behind it."
        ),
        discovery=(
            "Gray rinse water had seeped into the blue wash, leaving the pond cloudy and heavy instead of clear."
        ),
        theory=(
            "If muddy water had stained the pond wash, the pond would drink the light instead of returning it to the gate."
        ),
        result=(
            "After the murk lifted, the pond turned blue and glassy, and the gate could shine over it like moonlight."
        ),
    ),
}


METHODS: dict[str, Method] = {
    "sift_starlight": Method(
        id="sift_starlight",
        solves="dust",
        needs="sifter",
        tool_label="the little paint sifter",
        action=(
            "The children held the board steady together while one shook the little paint sifter over the pond and the other teased away the loose chalk with the gentlest brush strokes they knew."
        ),
        proof=(
            "The dull ring stopped coming back, which showed that the dust had truly been lifted instead of merely moved aside."
        ),
    ),
    "smooth_silver": Method(
        id="smooth_silver",
        solves="ripple",
        needs="cloth",
        tool_label="the velvet smoothing cloth",
        action=(
            "The children laid the velvet smoothing cloth over the pond paper and pressed the hidden ridge flat with slow thumb-wide circles."
        ),
        proof=(
            "When they tilted the mural again, the crease no longer caught the lamp, and the reflection ran straight across the water."
        ),
    ),
    "lift_and_layer": Method(
        id="lift_and_layer",
        solves="muddy",
        needs="sponge",
        tool_label="the rinsing sponge and a fresh blue wash",
        action=(
            "The children kissed the muddy patch with the rinsing sponge, then laid a fresh blue wash over the pond in two careful strokes."
        ),
        proof=(
            "The brown crescent vanished on the next check, proving that the dirty water had been lifted out of the picture."
        ),
    ),
}


TOOL_LABELS = {
    "sifter": "the little paint sifter",
    "cloth": "the velvet smoothing cloth",
    "sponge": "the rinsing sponge and a fresh blue wash",
}


PROBLEM_LABELS = {
    "dust": "a chalk haze over the pond",
    "ripple": "a glue ridge under the pond paper",
    "muddy": "muddy rinse water in the pond wash",
}


def explain_rejection(room_id: str, pair_id: str, problem_id: str, method_id: str) -> str:
    if room_id not in ROOMS:
        return f"unknown room: {room_id}"
    if pair_id not in PAIRS:
        return f"unknown pair: {pair_id}"
    if problem_id not in PROBLEMS:
        return f"unknown problem: {problem_id}"
    if method_id not in METHODS:
        return f"unknown method: {method_id}"
    room = ROOMS[room_id]
    problem = PROBLEMS[problem_id]
    method = METHODS[method_id]
    reasons: list[str] = []
    if method.solves != problem.kind:
        reasons.append("the repair method must match the physical problem in the pond")
    if method.needs not in room.tools:
        reasons.append(f"{room.name} does not have {TOOL_LABELS[method.needs]}")
    if not reasons:
        return "the requested story is valid"
    return "; ".join(reasons)


def valid_params(params: StoryParams) -> tuple[bool, str]:
    reason = explain_rejection(params.room, params.pair, params.problem, params.method)
    return (reason == "the requested story is valid", reason)


def all_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for room_id in ROOMS:
        for pair_id in PAIRS:
            for problem_id in PROBLEMS:
                for method_id in METHODS:
                    params = StoryParams(room_id, pair_id, problem_id, method_id)
                    if valid_params(params)[0]:
                        combos.append((room_id, pair_id, problem_id, method_id))
    return combos


def params_from_combo(combo: tuple[str, str, str, str], seed: int | None) -> StoryParams:
    return StoryParams(room=combo[0], pair=combo[1], problem=combo[2], method=combo[3], seed=seed)


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    combos = all_combos()
    if args.room:
        combos = [combo for combo in combos if combo[0] == args.room]
    if args.pair:
        combos = [combo for combo in combos if combo[1] == args.pair]
    if args.problem:
        combos = [combo for combo in combos if combo[2] == args.problem]
    if args.method:
        combos = [combo for combo in combos if combo[3] == args.method]
    return combos


def make_world(params: StoryParams) -> StoryWorld:
    room = ROOMS[params.room]
    pair = PAIRS[params.pair]
    problem = PROBLEMS[params.problem]
    method = METHODS[params.method]

    world = StoryWorld(params)
    world.add(Entity("hero", "character", pair.hero_type, pair.hero_name, role="hero"))
    world.add(Entity("friend", "character", pair.friend_type, pair.friend_name, role="friend"))
    world.add(Entity("helper", "character", "woman", room.helper, role="helper"))
    world.add(Entity("team", "group", "pair", pair.duo_label, role="team"))
    world.add(Entity("room", "place", "art_room", room.name))
    world.add(Entity("mural", "object", "mural", "the fairy mural"))
    world.add(Entity("gate", "object", "gate", "the twinkling gate"))
    world.add(Entity("pond", "object", "pond", "the dusty pond"))
    world.add(Entity("tool", "object", "tool", method.tool_label))

    world.get("gate").meters["sparkle"] = 0.4
    world.get("pond").meters["clarity"] = 0.4
    world.get("pond").meters["disturbance"] = 2.0
    world.get("mural").meters["finished"] = 0.0
    world.get("team").memes["wonder"] = 1.5
    world.get("team").memes["worry"] = 0.4
    world.get("team").memes["patience"] = 1.0
    world.get("helper").memes["steadiness"] = 2.0

    world.facts.update(
        room_name=room.name,
        duo_label=pair.duo_label,
        hero_name=pair.hero_name,
        friend_name=pair.friend_name,
        helper_name=room.helper,
        problem_label=PROBLEM_LABELS[problem.kind],
        repeated_phrase="Look low, look close, look again.",
        clue_text=problem.repeated_clue,
        theory=problem.theory,
        tool_label=method.tool_label,
        solved=False,
        checks=0,
    )
    return world


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def opening(world: StoryWorld) -> None:
    room = ROOMS[world.params.room]
    pair = PAIRS[world.params.pair]
    world.record(
        "opening",
        (
            f"{room.opening} On the longest table, {pair.duo_label} were painting a fairy mural for the wall: "
            "a twinkling gate beyond cattails, a dusty pond below it, and a ribbon path for moon-colored ducks."
        ),
        "team",
        "mural",
    )
    world.record(
        "wish",
        f'{pair.hero_name} said, "When the lamp reaches our twinkling gate, it should glitter like a pocket full of stars."',
        "hero",
        "gate",
    )


def problem_appears(world: StoryWorld) -> None:
    problem = PROBLEMS[world.params.problem]
    team = world.get("team")
    gate = world.get("gate")
    pond = world.get("pond")
    team.memes["worry"] += 1.0
    gate.meters["sparkle"] = 0.1
    pond.meters["disturbance"] += 1.0
    world.record("problem", problem.setup, "mural", "gate")
    world.record(
        "false_guess",
        (
            f'{world.facts["hero_name"]} almost blamed the silver stars painted on the gate itself, '
            'but the helper raised one calm finger and said, "Do not scold the gate before you listen to the pond."'
        ),
        "helper",
        "hero",
    )


def repeated_checks(world: StoryWorld) -> None:
    problem = PROBLEMS[world.params.problem]
    phrase = world.facts["repeated_phrase"]
    views = (
        "the floor tiles",
        "the little step stool",
        "the amber lamp by the drying rack",
    )
    for index, view in enumerate(views, 1):
        world.facts["checks"] = index
        world.get("team").memes["patience"] += 0.2
        world.record(
            f"check_{index}",
            f'{phrase} From {view}, {world.facts["duo_label"]} saw that {lower_first(problem.repeated_clue)}',
            "team",
            "pond",
        )


def turn_to_reasoning(world: StoryWorld) -> None:
    theory = world.facts["theory"]
    world.get("team").memes["wonder"] += 0.4
    world.get("team").memes["worry"] -= 0.3
    world.record(
        "turn",
        (
            f'{world.facts["helper_name"]} smiled and said, "A clue that returns three times is not a trick. '
            'It is the picture telling the truth." '
            f'Then {world.facts["hero_name"]} touched the edge of the pond and whispered, "{theory}"'
        ),
        "hero",
        "pond",
    )


def discover_problem(world: StoryWorld) -> None:
    problem = PROBLEMS[world.params.problem]
    pond = world.get("pond")
    pond.meters["disturbance"] = 2.0
    world.record(
        "discovery",
        (
            f"So the children stopped guessing about magic stars and studied the dusty pond itself. "
            f"Soon they found the real trouble: {problem.discovery}"
        ),
        "team",
        "pond",
    )


def solve_problem(world: StoryWorld) -> None:
    problem = PROBLEMS[world.params.problem]
    method = METHODS[world.params.method]
    gate = world.get("gate")
    pond = world.get("pond")
    mural = world.get("mural")
    team = world.get("team")

    world.record("solve", f"{method.action} {method.proof}", "team", "tool")
    pond.meters["disturbance"] = 0.0
    pond.meters["clarity"] = 2.5
    gate.meters["sparkle"] = 2.6
    mural.meters["finished"] = 1.0
    team.memes["worry"] = 0.0
    team.memes["pride"] += 1.5
    team.memes["relief"] += 1.0
    world.facts["solved"] = True
    world.record("result", problem.result, "pond", "gate")


def ending(world: StoryWorld) -> None:
    room = ROOMS[world.params.room]
    pair = PAIRS[world.params.pair]
    world.record(
        "ending",
        (
            f"When the lamp crossed the wall one more time, the twinkling gate scattered bright silver dots over the dusty pond, "
            f"and the dusty pond answered with a clean blue gleam. {pair.duo_label} clapped, {room.ending}, "
            "and even the drying brushes seemed to stand up straighter to watch."
        ),
        "team",
        "mural",
    )


def tell(params: StoryParams) -> StoryWorld:
    world = make_world(params)
    opening(world)
    world.para()
    problem_appears(world)
    repeated_checks(world)
    world.para()
    turn_to_reasoning(world)
    discover_problem(world)
    solve_problem(world)
    world.para()
    ending(world)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    return [
        'Write a child-facing fairy tale set in an art room that clearly includes the exact phrases "twinkling gate" and "dusty pond."',
        "Build the middle around problem solving and repetition, so the same clue appears three times before the children name the real cause.",
        "End with a vivid final image that proves the pond changed and the gate can sparkle again.",
    ]


def story_grounded_qa(world: StoryWorld) -> list[QAItem]:
    problem = PROBLEMS[world.params.problem]
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why did the twinkling gate stop sparkling in the art room?",
            answer=(
                f"The twinkling gate stopped sparkling because the real trouble was {world.facts['problem_label']}. "
                f"{problem.discovery} That kept the dusty pond from sending bright reflected light back to the gate."
            ),
        ),
        QAItem(
            question="What repeated clue helped the children stop guessing?",
            answer=(
                f"The repeated clue was that {problem.repeated_clue.lower()} "
                "Because the same sign returned from three different views, the children understood that one physical problem was still hiding in the pond."
            ),
        ),
        QAItem(
            question="How did the children solve the problem in the mural?",
            answer=(
                f"They used {method.tool_label} and worked directly on the dusty pond instead of fussing with the gate. "
                f"{method.proof} That careful test showed the repair truly matched the cause."
            ),
        ),
        QAItem(
            question="What proved at the end that the mural had changed?",
            answer=(
                "The gate scattered bright silver dots, and the pond answered with a clear blue gleam instead of a dull patch. "
                "That final image showed that the surface of the pond was healthy enough to carry the light again."
            ),
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    method = METHODS[world.params.method]
    return [
        QAItem(
            question="Why is a clue that repeats useful in problem solving?",
            answer=(
                "A repeating clue matters because it points to a cause that is still active in the world. "
                "When the same mark returns again and again, careful problem solvers know where to test their idea."
            ),
        ),
        QAItem(
            question="Why did the children need the right art-room tool instead of simply painting over the trouble?",
            answer=(
                f"They needed {method.tool_label} because the problem was physical, not just decorative. "
                "A real fix had to clear, flatten, or lift the damaged part before fresh beauty could stay in place."
            ),
        ),
        QAItem(
            question="How can a pond in a mural help a painted gate look bright?",
            answer=(
                "A shiny painted pond can bounce light toward other parts of the picture, much like a small mirror. "
                "If the pond grows dusty, wrinkled, or muddy, the reflected light turns weak and the nearby gate looks dull."
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
valid(R,P,Pr,M) :-
    room(R), pair(P), problem(Pr), method(M),
    problem_kind(Pr, K),
    method_solves(M, K),
    method_needs(M, T),
    room_tool(R, T).

ok :- chosen(R, P, Pr, M), valid(R, P, Pr, M).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from asp import fact

    lines: list[str] = []
    for room_id, room in sorted(ROOMS.items()):
        lines.append(fact("room", room_id))
        for tool in room.tools:
            lines.append(fact("room_tool", room_id, tool))
    for pair_id in sorted(PAIRS):
        lines.append(fact("pair", pair_id))
    for problem_id, problem in sorted(PROBLEMS.items()):
        lines.append(fact("problem", problem_id))
        lines.append(fact("problem_kind", problem_id, problem.kind))
    for method_id, method in sorted(METHODS.items()):
        lines.append(fact("method", method_id))
        lines.append(fact("method_solves", method_id, method.solves))
        lines.append(fact("method_needs", method_id, method.needs))
    if params is not None:
        lines.append(fact("chosen", params.room, params.pair, params.problem, params.method))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from asp import atoms, one_model

    return sorted(atoms(one_model(asp_program()), "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    for needle in ("art room", "twinkling gate", "dusty pond"):
        if needle not in story_lower:
            raise AssertionError(f"story is missing {needle!r}")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    if "meters=" in sample.story or "memes=" in sample.story:
        raise AssertionError("story leaked debug language")
    if world.get("gate").meters.get("sparkle", 0) < 2:
        raise AssertionError("gate never recovered its sparkle")
    if world.get("pond").meters.get("clarity", 0) < 2:
        raise AssertionError("pond never became clear enough")
    if world.get("pond").meters.get("disturbance", 1) != 0:
        raise AssertionError("pond problem stayed unresolved")
    if world.get("mural").meters.get("finished", 0) < 1:
        raise AssertionError("mural never reached a finished state")
    if world.get("team").memes.get("pride", 0) < 1:
        raise AssertionError("children never reached a solved emotional state")
    if world.facts.get("checks") != 3:
        raise AssertionError("story did not complete its three repeated checks")
    if not world.facts.get("solved"):
        raise AssertionError("story never marked itself solved")
    event_ids = {event.id for event in world.history}
    for required in ("problem", "check_3", "discovery", "solve", "ending"):
        if required not in event_ids:
            raise AssertionError(f"missing event {required!r}")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 12:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = sorted(all_combos())
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
    print(f"OK: ASP parity matches Python gate ({len(py)} valid fairy-tale art-room stories).")
    for index, combo in enumerate(py):
        verify_sample(generate(params_from_combo(combo, 1000 + index)))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a fairy-tale art-room story about a twinkling gate, a dusty pond, and problem solving."
    )
    parser.add_argument("--room", choices=sorted(ROOMS))
    parser.add_argument("--pair", choices=sorted(PAIRS))
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None, index: int = 0) -> StoryParams:
    seed = (args.seed if args.seed is not None else 13) + index
    combos = matching_combos(args)
    if not combos:
        room = args.room or next(iter(ROOMS))
        pair = args.pair or next(iter(PAIRS))
        problem = args.problem or next(iter(PROBLEMS))
        method = args.method or next(iter(METHODS))
        raise StoryError(explain_rejection(room, pair, problem, method))

    explicit = all(getattr(args, field) is not None for field in ("room", "pair", "problem", "method"))
    if explicit:
        params = params_from_combo((args.room, args.pair, args.problem, args.method), seed)
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
            room = args.room or next(iter(ROOMS))
            pair = args.pair or next(iter(PAIRS))
            problem = args.problem or next(iter(PROBLEMS))
            method = args.method or next(iter(METHODS))
            raise StoryError(explain_rejection(room, pair, problem, method))
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
        print(f"{len(combos)} valid fairy-tale art-room stories:\n")
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
                "=== twinkling_gate_dusty_pond_art_room_problem "
                f"#{index} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
