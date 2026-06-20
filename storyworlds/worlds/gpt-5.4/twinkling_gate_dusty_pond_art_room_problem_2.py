#!/usr/bin/env python3
"""A fairy-tale art-room storyworld about mending a twinkling gate through the truth in a dusty pond.

Internal source tale:
In an art room dressed for a little school fair, two children paint a fairy
picture with a twinkling gate above a dusty pond. When the teacher's lamp shines
on the mural, the gate should glitter, but it does not. The children first
wonder whether the silver gate stars are wrong, yet the same clue appears three
times on the pond itself. By checking the picture again and again, they stop
guessing, name the real physical trouble, and use the right art-room tool to
repair the pond. The ending image proves the world changed: once the pond is
clear and true, the gate can shine at last.
"""

from __future__ import annotations

import argparse
import importlib
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class ArtRoom:
    id: str
    name: str
    opening: str
    helper: str
    tools: tuple[str, ...]
    ending_image: str


@dataclass(frozen=True)
class Pair:
    id: str
    hero_name: str
    hero_kind: str
    friend_name: str
    friend_kind: str
    duo_label: str


@dataclass(frozen=True)
class Trouble:
    id: str
    kind: str
    setup: str
    repeated_clue: str
    close_look: str
    theory: str
    result: str


@dataclass(frozen=True)
class Remedy:
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
    trouble: str
    remedy: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    facts: dict[str, Any] = field(default_factory=dict)

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
            f"trouble: {self.facts['trouble_label']}",
            f"remedy: {self.facts['tool_label']}",
            f"repeated_checks: {self.facts['repeated_checks']}",
            f"solved: {self.facts['solved']}",
        ]
        lines.append("EVENTS")
        for event in self.history:
            lines.append(f"- {event.id}: {event.text}")
        lines.append("ENTITIES")
        seen: set[str] = set()
        for key, entity in self.entities.items():
            if entity.id in seen or key != entity.id:
                continue
            seen.add(entity.id)
            lines.append(
                f"  {entity.id} | {entity.kind} | {entity.label} | "
                f"meters={entity.meters} memes={entity.memes}"
            )
        return "\n".join(lines)


ROOMS: dict[str, ArtRoom] = {
    "pearl_window": ArtRoom(
        id="pearl_window",
        name="Pearl-Window Art Room",
        opening=(
            "In the Pearl-Window art room, paper lilies hung from the rafters and a pale afternoon lamp "
            "made every jar of paint look like a row of little moons."
        ),
        helper="Teacher Sella",
        tools=("feather_brush", "pressing_cloth"),
        ending_image="the pearl window poured milk-white light over the reeds, and the mural looked ready for a fairy queen to step through",
    ),
    "candle_shelf": ArtRoom(
        id="candle_shelf",
        name="Candle-Shelf Art Room",
        opening=(
            "In the Candle-Shelf art room, warm light rested on the tables like honey, and the colored papers "
            "rose in neat towers as if a tiny castle had been folded out of card and glue."
        ),
        helper="Master Orin",
        tools=("feather_brush", "rinsing_sponge"),
        ending_image="golden light trembled across the water, and even the paper cattails seemed to bow toward the bright gate",
    ),
    "silver_ribbon": ArtRoom(
        id="silver_ribbon",
        name="Silver-Ribbon Art Room",
        opening=(
            "In the Silver-Ribbon art room, strips of foil twined above the drying rack, and every brush cup "
            "sparkled as if small stars had come indoors to watch the children work."
        ),
        helper="Mistress Vale",
        tools=("pressing_cloth", "rinsing_sponge"),
        ending_image="silver glints skipped from the gate to the pond, and the whole wall looked deep enough for moon ducks to land upon",
    ),
}


PAIRS: dict[str, Pair] = {
    "nella_ivo": Pair(
        id="nella_ivo",
        hero_name="Nella",
        hero_kind="girl",
        friend_name="Ivo",
        friend_kind="boy",
        duo_label="Nella and Ivo",
    ),
    "mira_tom": Pair(
        id="mira_tom",
        hero_name="Mira",
        hero_kind="girl",
        friend_name="Tom",
        friend_kind="boy",
        duo_label="Mira and Tom",
    ),
    "ada_finn": Pair(
        id="ada_finn",
        hero_name="Ada",
        hero_kind="girl",
        friend_name="Finn",
        friend_kind="boy",
        duo_label="Ada and Finn",
    ),
}


TROUBLES: dict[str, Trouble] = {
    "chalk_hush": Trouble(
        id="chalk_hush",
        kind="dust",
        setup=(
            "They had painted a twinkling gate above a dusty pond, but when the teacher turned the lamp toward the mural, "
            "the silver gate stars stayed sleepy instead of leaping into light."
        ),
        repeated_clue=(
            "the same pale halo drifted across the dusty pond again, soft as breath on glass"
        ),
        close_look=(
            "a thin skin of chalk dust had settled over the pond glaze, so the water picture could not throw clean light upward"
        ),
        theory=(
            "If chalk dust was dimming the pond, then the gate was only losing the bright answer that should have risen from the water."
        ),
        result=(
            "With the chalk hush lifted away, the pond turned glossy and deep-looking, and the gate's little stars woke all at once."
        ),
    ),
    "paper_ripple": Trouble(
        id="paper_ripple",
        kind="crease",
        setup=(
            "They had painted a twinkling gate above a dusty pond, but when the lamp crossed the board, "
            "the gate's silver shimmer broke into a bent and jagged line."
        ),
        repeated_clue=(
            "the same narrow wrinkle caught the light on the dusty pond again, like a tiny silver thorn"
        ),
        close_look=(
            "a damp buckle under the pond paper had lifted one strip of the picture, so the water scene kept snagging the reflection"
        ),
        theory=(
            "If the pond paper was buckled, then the water picture would keep breaking the gate's silver path every time the light crossed it."
        ),
        result=(
            "Once the paper lay smooth again, the painted pond held one long clean gleam, and the gate shone straight across it."
        ),
    ),
    "murky_moon": Trouble(
        id="murky_moon",
        kind="murk",
        setup=(
            "They had painted a twinkling gate above a dusty pond, but when the lamp brightened the board, "
            "a muddy crescent swallowed the place where the prettiest gleam should have lived."
        ),
        repeated_clue=(
            "the same brown moon pooled over the dusty pond again, hiding the gate's best sparkle"
        ),
        close_look=(
            "dirty rinse water had crept into the pond wash, clouding the blue with a brown film that drank the light"
        ),
        theory=(
            "If murky rinse water had clouded the pond, then the gate would shine only after the muddy veil was lifted away."
        ),
        result=(
            "When the murk was gone, the pond looked blue and clear as a storybook mirror, and the gate could glitter over it like moonlight."
        ),
    ),
}


REMEDIES: dict[str, Remedy] = {
    "soft_brush": Remedy(
        id="soft_brush",
        solves="dust",
        needs="feather_brush",
        tool_label="the feather-soft dusting brush",
        action=(
            "The children held the board steady together while one swept the feather-soft dusting brush over the pond in slow moon-shaped passes "
            "and the other watched for the pale halo to loosen and rise."
        ),
        proof=(
            "On the next lamp check, the floating halo did not come back, which showed that the dust had truly been lifted instead of merely pushed aside."
        ),
    ),
    "press_flat": Remedy(
        id="press_flat",
        solves="crease",
        needs="pressing_cloth",
        tool_label="the velvet pressing cloth",
        action=(
            "The children laid the velvet pressing cloth over the pond paper and pressed outward with warm fingertips, "
            "flattening the hidden buckle a little at a time."
        ),
        proof=(
            "When they tipped the mural again, the silver thorn no longer snatched at the light, and the reflection ran in one smooth thread."
        ),
    ),
    "lift_and_wash": Remedy(
        id="lift_and_wash",
        solves="murk",
        needs="rinsing_sponge",
        tool_label="the rinsing sponge and a fresh blue wash",
        action=(
            "The children kissed the cloudy patch with the rinsing sponge, then laid a fresh blue wash over the pond in two careful strokes while the helper counted softly beside them."
        ),
        proof=(
            "At the next check, the brown moon had vanished, proving that the dirty water had been lifted out of the picture instead of hidden under a brighter color."
        ),
    ),
}


TOOL_LABELS = {
    "feather_brush": "the feather-soft dusting brush",
    "pressing_cloth": "the velvet pressing cloth",
    "rinsing_sponge": "the rinsing sponge and a fresh blue wash",
}


TROUBLE_LABELS = {
    "dust": "chalk dust over the pond glaze",
    "crease": "a buckle under the pond paper",
    "murk": "murky rinse water in the pond wash",
}


VIEWPOINTS = (
    "from the window side of the easel",
    "from the little step stool by the mural",
    "from the drying rack beneath the lamp",
)


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text else text


def explain_rejection(room_id: str, pair_id: str, trouble_id: str, remedy_id: str) -> str:
    if room_id not in ROOMS:
        return f"unknown room: {room_id}"
    if pair_id not in PAIRS:
        return f"unknown pair: {pair_id}"
    if trouble_id not in TROUBLES:
        return f"unknown trouble: {trouble_id}"
    if remedy_id not in REMEDIES:
        return f"unknown remedy: {remedy_id}"
    room = ROOMS[room_id]
    trouble = TROUBLES[trouble_id]
    remedy = REMEDIES[remedy_id]
    reasons: list[str] = []
    if remedy.solves != trouble.kind:
        reasons.append("the remedy must match the physical trouble living in the pond")
    if remedy.needs not in room.tools:
        reasons.append(f"{room.name} does not have {TOOL_LABELS[remedy.needs]}")
    if not reasons:
        return "the requested story is valid"
    return "; ".join(reasons)


def valid_params(params: StoryParams) -> tuple[bool, str]:
    reason = explain_rejection(params.room, params.pair, params.trouble, params.remedy)
    return reason == "the requested story is valid", reason


def all_valid_params() -> list[StoryParams]:
    params_list: list[StoryParams] = []
    for room_id in sorted(ROOMS):
        for pair_id in sorted(PAIRS):
            for trouble_id in sorted(TROUBLES):
                for remedy_id in sorted(REMEDIES):
                    params = StoryParams(room_id, pair_id, trouble_id, remedy_id)
                    if valid_params(params)[0]:
                        params_list.append(params)
    return params_list


def matching_valid_params(args: argparse.Namespace) -> list[StoryParams]:
    params_list = all_valid_params()
    if args.room:
        params_list = [params for params in params_list if params.room == args.room]
    if args.pair:
        params_list = [params for params in params_list if params.pair == args.pair]
    if args.trouble:
        params_list = [params for params in params_list if params.trouble == args.trouble]
    if args.remedy:
        params_list = [params for params in params_list if params.remedy == args.remedy]
    return params_list


def make_world(params: StoryParams) -> StoryWorld:
    room = ROOMS[params.room]
    pair = PAIRS[params.pair]
    trouble = TROUBLES[params.trouble]
    remedy = REMEDIES[params.remedy]

    world = StoryWorld(params)
    world.add(Entity("hero", "character", pair.hero_kind, pair.hero_name, role="hero"))
    world.add(Entity("friend", "character", pair.friend_kind, pair.friend_name, role="friend"))
    world.add(Entity("helper", "character", "adult", room.helper, role="helper"))
    world.add(Entity("team", "group", "children", pair.duo_label, role="team"))
    world.add(Entity("room", "place", "art_room", room.name, role="room"))
    world.add(Entity("mural", "object", "mural", "the fairy mural", role="mural"))
    world.add(Entity("gate", "object", "gate", "the twinkling gate", role="gate"))
    world.add(Entity("pond", "object", "pond", "the dusty pond", role="pond"))
    world.add(Entity("tool", "object", "tool", remedy.tool_label, role="tool"))
    world.add(Entity("lamp", "object", "lamp", "the teacher's lamp", role="lamp"))

    world.get("gate").meters["sparkle"] = 0.5
    world.get("pond").meters["clarity"] = 0.6
    world.get("pond").meters["surface_trouble"] = 2.0
    world.get("mural").meters["finished"] = 0.4
    world.get("team").memes["wonder"] = 1.5
    world.get("team").memes["worry"] = 0.2
    world.get("team").memes["patience"] = 1.1
    world.get("team").memes["teamwork"] = 1.2
    world.get("helper").memes["steadiness"] = 2.0
    world.get("hero").memes["curiosity"] = 1.2
    world.get("friend").memes["care"] = 1.0

    world.facts.update(
        room_name=room.name,
        duo_label=pair.duo_label,
        hero_name=pair.hero_name,
        friend_name=pair.friend_name,
        helper_name=room.helper,
        trouble_label=TROUBLE_LABELS[trouble.kind],
        clue_line=trouble.repeated_clue,
        theory=trouble.theory,
        tool_label=remedy.tool_label,
        refrain="Low lamp, long look, little clue.",
        repeated_checks=0,
        solved=False,
    )
    return world


def opening(world: StoryWorld) -> None:
    room = ROOMS[world.params.room]
    pair = PAIRS[world.params.pair]
    world.record(
        "opening",
        (
            f"{room.opening} At the longest table, {pair.duo_label} were painting a fairy mural for the spring show: "
            "a twinkling gate among reeds, a dusty pond below it, and a path of pale stepping stones leading into the picture."
        ),
        "team",
        "mural",
    )
    world.record(
        "wish",
        (
            f'{pair.hero_name} smiled and said, "When the lamp finds our twinkling gate, it should glitter like a crown of tiny stars."'
        ),
        "hero",
        "gate",
    )


def problem_arrives(world: StoryWorld) -> None:
    trouble = TROUBLES[world.params.trouble]
    world.get("team").memes["worry"] += 0.9
    world.get("gate").meters["sparkle"] = 0.1
    world.get("pond").meters["surface_trouble"] += 0.8
    world.record("problem", trouble.setup, "lamp", "gate")
    world.record(
        "false_guess",
        (
            f'{world.facts["hero_name"]} almost blamed the silver stars on the gate itself, '
            f'but {world.facts["helper_name"]} said, "In a good picture, the water often tells the truth before the doorway does."'
        ),
        "helper",
        "hero",
    )


def repeated_checks(world: StoryWorld) -> None:
    trouble = TROUBLES[world.params.trouble]
    for index, viewpoint in enumerate(VIEWPOINTS, 1):
        world.facts["repeated_checks"] = index
        world.get("team").memes["patience"] += 0.2
        world.record(
            f"check_{index}",
            (
                f'{world.facts["refrain"]} {viewpoint.capitalize()}, {world.facts["duo_label"]} saw that '
                f"{lower_first(trouble.repeated_clue)}."
            ),
            "team",
            "pond",
        )


def turn_to_reasoning(world: StoryWorld) -> None:
    world.get("hero").memes["curiosity"] += 0.6
    world.get("team").memes["worry"] = max(0.0, world.get("team").memes["worry"] - 0.3)
    world.record(
        "theory",
        (
            f'After the third look, {world.facts["hero_name"]} whispered, "{world.facts["theory"]}" '
            f'{world.facts["friend_name"]} nodded, because a clue that returned three times no longer felt like a trick. '
            "It felt like a trail."
        ),
        "hero",
        "pond",
    )


def discover_trouble(world: StoryWorld) -> None:
    trouble = TROUBLES[world.params.trouble]
    world.record(
        "discovery",
        (
            "So the children stopped fussing with the painted stars and bent over the dusty pond itself. "
            f"At close range, they found the real trouble: {trouble.close_look}."
        ),
        "team",
        "pond",
    )


def solve_trouble(world: StoryWorld) -> None:
    trouble = TROUBLES[world.params.trouble]
    remedy = REMEDIES[world.params.remedy]
    world.record(
        "solve",
        f"{remedy.action} {remedy.proof}",
        "team",
        "tool",
    )
    world.get("pond").meters["surface_trouble"] = 0.0
    world.get("pond").meters["clarity"] = 2.5
    world.get("gate").meters["sparkle"] = 2.6
    world.get("mural").meters["finished"] = 1.0
    world.get("team").memes["worry"] = 0.0
    world.get("team").memes["pride"] = 1.4
    world.get("team").memes["relief"] = 1.1
    world.facts["solved"] = True
    world.record("result", trouble.result, "pond", "gate")


def ending(world: StoryWorld) -> None:
    room = ROOMS[world.params.room]
    world.record(
        "ending",
        (
            "When the lamp crossed the mural one last time, the twinkling gate scattered bright silver dots over the dusty pond, "
            f"the dusty pond answered with a clean blue gleam, {room.ending_image}, "
            "and the children laughed because the picture finally looked as if it knew its own happy ending."
        ),
        "team",
        "mural",
    )


def tell(params: StoryParams) -> StoryWorld:
    world = make_world(params)
    opening(world)
    world.para()
    problem_arrives(world)
    repeated_checks(world)
    world.para()
    turn_to_reasoning(world)
    discover_trouble(world)
    solve_trouble(world)
    world.para()
    ending(world)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    return [
        'Write a child-facing fairy tale set in an art room that clearly includes the exact phrases "twinkling gate" and "dusty pond."',
        "Build the middle around problem solving and repetition, so the same clue returns three times before the children name the real physical cause.",
        "End with a vivid final image that proves the pond changed and the gate can shine because of that change.",
    ]


def story_grounded_qa(world: StoryWorld) -> list[QAItem]:
    trouble = TROUBLES[world.params.trouble]
    remedy = REMEDIES[world.params.remedy]
    return [
        QAItem(
            question="Why did the twinkling gate fail to sparkle when the lamp touched the mural?",
            answer=(
                f"The gate failed to sparkle because the real trouble was {world.facts['trouble_label']}. "
                f"{trouble.close_look.capitalize()}. That kept the dusty pond from sending clean reflected light back toward the gate."
            ),
        ),
        QAItem(
            question="What repeated clue helped the children stop guessing?",
            answer=(
                f"The repeated clue was that {trouble.repeated_clue}. "
                "Because the same sign appeared from three different checks, the children understood that one steady physical problem was still hiding in the pond."
            ),
        ),
        QAItem(
            question="How did the children solve the problem in the art room?",
            answer=(
                f"They used {remedy.tool_label} and worked directly on the pond instead of repainting the gate. "
                f"{remedy.proof} That careful test proved the fix matched the cause."
            ),
        ),
        QAItem(
            question="What showed at the end that the mural had truly changed?",
            answer=(
                "The twinkling gate threw bright silver dots, and the dusty pond answered with a clean blue gleam instead of a dull mark. "
                "That ending image showed that the pond surface was healthy enough to carry the light again."
            ),
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="Why is repetition useful in this kind of problem-solving story?",
            answer=(
                "Repetition matters because a clue that returns again and again usually points to a cause that is still active in the world. "
                "Each repeated check helps the children trust evidence more than their first nervous guess."
            ),
        ),
        QAItem(
            question="Why does the pond matter so much to the look of the gate in this world?",
            answer=(
                "The painted pond matters because its surface carries and returns the lamp light, almost like a little mirror inside the mural. "
                "If the pond grows dusty, buckled, or muddy, the gate above it cannot borrow a bright shimmer."
            ),
        ),
        QAItem(
            question="Why must the children use the right art-room tool instead of simply painting over the trouble?",
            answer=(
                "They need the right tool because the trouble lives in the physical surface of the picture, not only in its color. "
                "A real repair has to lift, flatten, or clear the damaged part before the beauty can stay."
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
valid(R,P,T,M) :-
    room(R),
    pair(P),
    trouble(T),
    remedy(M),
    trouble_kind(T, K),
    remedy_solves(M, K),
    remedy_needs(M, Tool),
    room_tool(R, Tool).

ok :- chosen(R, P, T, M), valid(R, P, T, M).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    asp = importlib.import_module("storyworlds.asp")

    lines: list[str] = []
    for room_id, room in sorted(ROOMS.items()):
        lines.append(asp.fact("room", room_id))
        for tool in room.tools:
            lines.append(asp.fact("room_tool", room_id, tool))
    for pair_id in sorted(PAIRS):
        lines.append(asp.fact("pair", pair_id))
    for trouble_id, trouble in sorted(TROUBLES.items()):
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("trouble_kind", trouble_id, trouble.kind))
    for remedy_id, remedy in sorted(REMEDIES.items()):
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("remedy_solves", remedy_id, remedy.solves))
        lines.append(asp.fact("remedy_needs", remedy_id, remedy.needs))
    if params is not None:
        lines.append(asp.fact("chosen", params.room, params.pair, params.trouble, params.remedy))
    return "\n".join(lines) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    asp = importlib.import_module("storyworlds.asp")
    return sorted(asp.atoms(asp.one_model(asp_program()), "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    for needle in ("art room", "twinkling gate", "dusty pond"):
        if needle not in story_lower:
            raise AssertionError(f"story is missing {needle!r}")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should contain at least four paragraphs")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    if "meters=" in sample.story or "memes=" in sample.story or "trace" in story_lower:
        raise AssertionError("story leaked debug language")
    if world.get("gate").meters.get("sparkle", 0.0) < 2.0:
        raise AssertionError("gate never regained enough sparkle")
    if world.get("pond").meters.get("clarity", 0.0) < 2.0:
        raise AssertionError("pond never became clear enough")
    if world.get("pond").meters.get("surface_trouble", 1.0) != 0.0:
        raise AssertionError("pond trouble stayed unresolved")
    if world.get("mural").meters.get("finished", 0.0) < 1.0:
        raise AssertionError("mural never reached a finished state")
    if world.get("team").memes.get("pride", 0.0) < 1.0:
        raise AssertionError("team never reached a proud solved state")
    if world.facts.get("repeated_checks") != 3:
        raise AssertionError("story did not complete three repeated checks")
    if not world.facts.get("solved"):
        raise AssertionError("story never marked itself solved")
    event_ids = {event.id for event in world.history}
    for required in ("problem", "check_3", "theory", "discovery", "solve", "ending"):
        if required not in event_ids:
            raise AssertionError(f"missing event {required!r}")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
        raise AssertionError("QA sets are too thin")
    for item in [*sample.story_qa, *sample.world_qa]:
        if len(item.answer.split()) < 12:
            raise AssertionError(f"answer is too short: {item.question}")
        if "." not in item.answer:
            raise AssertionError(f"answer lacks sentence punctuation: {item.question}")


def verify_asp_parity() -> str:
    py = sorted((params.room, params.pair, params.trouble, params.remedy) for params in all_valid_params())
    lp = asp_valid_combos()
    if py != lp:
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        raise StoryError(f"ASP parity mismatch; only_py={only_py[:5]} only_lp={only_lp[:5]}")
    return f"ASP parity OK across {len(py)} valid parameter combinations."


def verify_worlds() -> str:
    params_list = all_valid_params()
    if not params_list:
        raise StoryError("no valid stories were generated")
    for params in params_list:
        verify_sample(generate(params))
    return f"Generated and checked {len(params_list)} complete fairy-tale art-room stories."


def verify() -> str:
    return f"{verify_asp_parity()} {verify_worlds()}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--room", choices=sorted(ROOMS))
    parser.add_argument("--pair", choices=sorted(PAIRS))
    parser.add_argument("--trouble", choices=sorted(TROUBLES))
    parser.add_argument("--remedy", choices=sorted(REMEDIES))
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    matches = matching_valid_params(args)
    if not matches:
        if args.room and args.pair and args.trouble and args.remedy:
            raise StoryError(explain_rejection(args.room, args.pair, args.trouble, args.remedy))
        raise StoryError("no valid stories match the requested filters")
    chosen = rng.choice(matches)
    return StoryParams(chosen.room, chosen.pair, chosen.trouble, chosen.remedy, args.seed)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        matches = matching_valid_params(args)
        if not matches:
            raise StoryError("no valid stories match the requested filters")
        for params in matches:
            yield generate(StoryParams(params.room, params.pair, params.trouble, params.remedy, args.seed))
        return
    rng = random.Random(args.seed)
    for _ in range(max(1, args.n)):
        yield generate(resolve_params(args, rng))


def emit(sample: StorySample, args: argparse.Namespace) -> None:
    if args.json:
        print(sample.to_json())
        return
    print(sample.story)
    if args.trace:
        print("\nTrace:")
        print(sample.world.trace())
    if args.qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nStory QA:")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\nWorld QA:")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main(argv: list[str] | None = None) -> int:
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
            asp = importlib.import_module("storyworlds.asp")
            print(asp.solve(asp_program()))
            return 0
        for index, sample in enumerate(iter_samples(args)):
            if index:
                print("\n---\n")
            emit(sample, args)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
