#!/usr/bin/env python3
"""
A small forest-trail superhero storyworld about Frog-Dim, a funny mystery,
and the clues a team can find by sharing what they know.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    events: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    seed: Optional[int] = None
    helper_name: str = "Pip"
    trail: str = "Fernbutton Trail"
    mystery: str = "rattle"


HELPERS = {
    "Pip": "a squirrel trail scout",
    "Tavi": "a badger mapkeeper",
    "Mira": "a robin ranger",
    "Bram": "a hedgehog trail guide",
}

TRAILS = [
    "Fernbutton Trail",
    "Bramblecup Trail",
    "Moonmoss Trail",
]

MYSTERIES = {
    "rattle": {
        "title": "the bell that rang by itself",
        "oddity": "the old trail bell rang three times though nobody stood beside it",
        "first_guess": "A sneaky bell-ringer must be hiding down the side spur",
        "false_suspect": "a hidden bell-ringer",
        "wrong_action": "charged down the side spur after the supposed bell-ringer",
        "clue": "the bell rang only when a breeze shook a dry seedpod tied to its rope with a loop of vine",
        "cause": "the wind was swinging a seedpod against the bell",
        "tool": "a soft cloth strip",
        "helper_task": "hold the cloth while we clear the bell rope",
        "method": "Pip held the cloth strip while Frog-Dim freed the vine loop; together they moved the swinging seedpod away from the emergency bell.",
        "resolution": "The bell gave one clean ring when Pip tested it, and its rope swung freely instead of knocking against the seedpod.",
        "comic_beat": "A purple berry perched on the hero's nose like a tiny badge.",
        "ending": "the two hikers walked home beneath the trees while the bell rested quiet until someone truly needed it",
        "object_label": "the old trail bell",
        "tool_label": "a soft cloth strip",
        "has_clue": True,
        "safe_setback": True,
        "shares_solution": True,
        "ending_image": True,
    },
    "footprints": {
        "title": "the enormous muddy footprints",
        "oddity": "enormous muddy footprints appeared beside the trail and stopped at a patch of dry stones",
        "first_guess": "A forest giant must have crossed this trail",
        "false_suspect": "a forest giant",
        "wrong_action": "followed the huge prints off the main path to look for a forest giant",
        "clue": "each print had the comb-like lines of a fern's underside, and the marks appeared only where rain dripped",
        "cause": "a fallen fern frond had stamped its comb-like underside in rain-softened mud",
        "tool": "Pip's folded trail map",
        "helper_task": "hold the map while we choose firm stones",
        "method": "Pip marked the firm stones on the map while Frog-Dim moved a loose fern frond off the walking line and pointed out the muddy patch.",
        "resolution": "The strange prints stopped appearing once the loose frond was moved, and the hikers crossed on the firm stones.",
        "comic_beat": "A fern frond flopped over the hero's head like a leafy helmet.",
        "ending": "the hikers followed the dry stones as the leafy helmet waved a final farewell from Frog-Dim's hand",
        "object_label": "the rain-softened trail mud",
        "tool_label": "Pip's folded trail map",
        "has_clue": True,
        "safe_setback": True,
        "shares_solution": True,
        "ending_image": True,
    },
    "twinkle": {
        "title": "the blue lights that seemed to wander",
        "oddity": "little blue lights seemed to skip away from the trail markers toward the creek",
        "first_guess": "Someone must be carrying away the blue trail lights",
        "false_suspect": "a trail-light thief",
        "wrong_action": "chased the brightest glow down toward the creek",
        "clue": "the blue sparks wobbled on a puddle while tiny lights fluttered above it, but the painted blue arrows stayed still on the trees",
        "cause": "fireflies above a puddle were doubled into moving blue lights",
        "tool": "Pip's hooded lantern",
        "helper_task": "aim the lantern at the painted arrows",
        "method": "Pip held the hooded lantern low while Frog-Dim dimmed their suit-spots; the steady painted arrows appeared, and they guided the hikers away from the misleading puddle reflections.",
        "resolution": "The painted arrows stayed fixed when the puddle rippled, while the firefly reflections wavered and vanished.",
        "comic_beat": "The puddle showed Frog-Dim saluting an upside-down frog.",
        "ending": "fireflies bobbed above the creek while the hikers followed the steady blue arrows through the forest",
        "object_label": "the puddle beside the blue trail arrows",
        "tool_label": "Pip's hooded lantern",
        "has_clue": True,
        "safe_setback": True,
        "shares_solution": True,
        "ending_image": True,
    },
    "ribbons": {
        "title": "the missing orange trail ribbons",
        "oddity": "orange trail ribbons had vanished from several low branches",
        "first_guess": "A trail-marker thief must be hiding in those bushes",
        "false_suspect": "a trail-marker thief",
        "wrong_action": "hurried off the path toward the bushes to search for a marker thief",
        "clue": "from the trail, Pip spotted orange ribbon woven into a nearby jay's nest, while the lowest trail markers were missing",
        "cause": "a jay had carried loose, low ribbons to its nest",
        "tool": "Pip's spare orange trail ribbons",
        "helper_task": "pass up spare markers while we stay clear of the nest",
        "method": "Pip shared spare orange markers while Frog-Dim tied them higher along the trail; they left the jay's nest alone and told the ranger what had happened.",
        "resolution": "New ribbons showed the trail clearly, and the jay's nest stayed undisturbed.",
        "comic_beat": "Frog-Dim spun around to face a tree, which made a poor suspect.",
        "ending": "the orange trail markers glowed among the leaves while the jay settled quietly in its untouched nest",
        "object_label": "the low trail ribbons and the jay's nest",
        "tool_label": "Pip's spare orange trail ribbons",
        "has_clue": True,
        "safe_setback": True,
        "shares_solution": True,
        "ending_image": True,
    },
}

PARAMETER_REGISTRIES = {
    "helper_name": tuple(HELPERS),
    "trail": tuple(TRAILS),
    "mystery": tuple(MYSTERIES),
}


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def _setup(world: World, params: StoryParams, case: dict) -> None:
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="frog_superhero",
            label="Frog-Dim",
            meters={"energy": 1.0, "glow_charge": 1.0, "clue_count": 0.0, "cape_tangle": 0.0},
            memes={"confidence": 0.75, "worry": 0.1, "pride": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="trail_helper",
            label=params.helper_name,
            meters={"attention": 0.55},
            memes={"concern": 0.2, "trust": 0.65},
        )
    )
    trail = world.add(
        Entity(
            id="trail",
            kind="place",
            type="forest_trail",
            label=params.trail,
            meters={"markers_visible": 0.6, "safe_route": 0.6, "walkers_waiting": 0.0},
            memes={},
        )
    )
    walkers = world.add(
        Entity(
            id="walkers",
            kind="group",
            type="hikers",
            label="two evening hikers",
            meters={"together": 1.0, "on_safe_path": 1.0},
            memes={"uncertainty": 0.25, "relief": 0.0},
        )
    )
    clue = world.add(
        Entity(
            id="clue",
            kind="thing",
            type="trail_clue",
            label=case["object_label"],
            meters={"noticed": 0.0, "explained": 0.0},
            memes={},
        )
    )
    tool = world.add(
        Entity(
            id="shared_tool",
            kind="thing",
            type="trail_gear",
            label=case["tool_label"],
            owner=helper.id,
            holder=helper.id,
            meters={"available": 1.0, "shared": 0.0, "used": 0.0},
            memes={},
        )
    )
    world.facts.update(
        params=params,
        case=case,
        hero=hero,
        helper=helper,
        trail=trail,
        walkers=walkers,
        clue=clue,
        tool=tool,
        phase="patrol",
        resolved=False,
    )


def _simulate(params: StoryParams) -> World:
    case = MYSTERIES[params.mystery]
    world = World()
    _setup(world, params, case)

    hero = world.facts["hero"]
    helper = world.facts["helper"]
    trail = world.facts["trail"]
    walkers = world.facts["walkers"]
    clue = world.facts["clue"]
    tool = world.facts["tool"]

    world.say(
        f"At dusk, Frog-Dim patrolled {params.trail}, a winding forest trail, beside "
        f"{params.helper_name}, {HELPERS[params.helper_name]}. Frog-Dim was a forest superhero "
        "in a green cape, with suit-spots that could shine like lanterns or dim to reveal small clues."
    )
    world.say(
        f"Two hikers were making their way home when the puzzle began: {case['oddity']}."
    )

    world.para()
    world.say(
        f"“{case['first_guess']},” Frog-Dim said. “I'll keep the hikers at the safe fork and watch the trail,” "
        f"{params.helper_name} replied."
    )
    world.say(f"Frog-Dim {case['wrong_action']}.")
    hero.meters["energy"] = 0.78
    hero.meters["cape_tangle"] = 1.0
    hero.memes["worry"] = 0.72
    helper.meters["attention"] = 0.9
    trail.meters["walkers_waiting"] = 2.0
    walkers.memes["uncertainty"] = 0.65
    world.fired.add("wrong_guess_made")
    world.fired.add("walkers_kept_safe")
    world.facts["phase"] = "setback"
    world.event("The first guess led away from the clue; the hikers waited safely at the fork.")
    world.say(
        f"The cape caught on a low branch and deposited the hero gently in a pile of leaves. "
        f"{case['comic_beat']} Because {params.helper_name} stayed with the hikers, nobody followed "
        "the false lead."
    )

    world.para()
    world.say(
        "“I almost called myself a moron,” Frog-Dim admitted, picking leaves from the cape. "
        "“A wrong guess is not your name,” said "
        f"{params.helper_name}. “Let's check one clue at a time.” “Show me what you noticed,” Frog-Dim said."
    )
    clue.meters["noticed"] = 1.0
    hero.meters["clue_count"] = 1.0
    helper.meters["attention"] = 1.0
    hero.memes["worry"] = 0.32
    hero.memes["confidence"] = 0.82
    world.fired.add("clue_observed")
    world.facts["phase"] = "investigating"
    world.event("The helper shared an observation, and Frog-Dim replaced a guess with evidence.")
    world.say(
        f"“I noticed that {case['clue']},” {params.helper_name} said. "
        f"Frog-Dim dimmed the suit-spots and looked closely at {clue.label}. "
        f"The evidence pointed to {case['cause']}, not {case['false_suspect']}."
    )

    world.para()
    world.say(
        f"“Could we share your {case['tool']} while we test it?” Frog-Dim asked. "
        f"“Yes—and I'll {case['helper_task']},” {params.helper_name} replied."
    )
    tool.holder = "the team"
    tool.meters["shared"] = 1.0
    tool.meters["used"] = 1.0
    hero.meters["glow_charge"] = 0.72
    world.fired.add("gear_shared")
    world.say(case["method"])
    world.event("The helper shared useful gear, and both characters followed a clue-based plan.")

    trail.meters["markers_visible"] = 1.0
    trail.meters["safe_route"] = 1.0
    trail.meters["walkers_waiting"] = 0.0
    walkers.memes["uncertainty"] = 0.0
    walkers.memes["relief"] = 1.0
    clue.meters["explained"] = 1.0
    hero.meters["energy"] = 0.65
    hero.memes["worry"] = 0.0
    hero.memes["confidence"] = 1.0
    hero.memes["pride"] = 1.0
    helper.memes["concern"] = 0.0
    helper.memes["trust"] = 1.0
    world.fired.add("mystery_solved")
    world.facts["phase"] = "resolved"
    world.facts["resolved"] = True

    world.para()
    world.say(f"The shared plan worked: {case['resolution']}")
    world.say(
        f"The hikers thanked Frog-Dim and {params.helper_name} before following the safe trail. "
        "Frog-Dim felt proud—not because the first guess was perfect, but because the hero had listened, "
        "shared the work, and helped everyone get home."
    )
    world.say(f"At the end, {case['ending']}.")
    world.facts.update(
        params=params,
        case=case,
        case_id=params.mystery,
        trail_name=params.trail,
        resolved=True,
    )
    world.event("The mystery was explained, the route was safe, and the hikers continued home.")
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def _case_is_reasonable(case: dict) -> bool:
    required_text = (
        "title",
        "oddity",
        "first_guess",
        "false_suspect",
        "wrong_action",
        "clue",
        "cause",
        "tool",
        "helper_task",
        "method",
        "resolution",
        "comic_beat",
        "ending",
        "object_label",
        "tool_label",
    )
    return (
        all(isinstance(case.get(key), str) and case[key].strip() for key in required_text)
        and case.get("has_clue") is True
        and case.get("safe_setback") is True
        and case.get("shares_solution") is True
        and case.get("ending_image") is True
    )


def valid_story(params: Optional[StoryParams] = None) -> bool:
    """Python reasonableness gate mirrored by the inline ASP rules."""
    if params is None:
        return bool(MYSTERIES) and all(_case_is_reasonable(case) for case in MYSTERIES.values())
    if not isinstance(params, StoryParams):
        return False
    if params.helper_name not in HELPERS or params.trail not in TRAILS:
        return False
    case = MYSTERIES.get(params.mystery)
    return case is not None and _case_is_reasonable(case)


def _validate_params(params: StoryParams) -> None:
    if not isinstance(params, StoryParams):
        raise StoryError("Story parameters must be a StoryParams instance.")
    if params.helper_name not in HELPERS:
        raise StoryError(f"Unknown trail helper {params.helper_name!r}; choose a registered helper.")
    if params.trail not in TRAILS:
        raise StoryError(f"Unknown forest trail {params.trail!r}; choose a registered trail.")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery {params.mystery!r}; choose a registered mystery.")
    if params.seed is not None and (type(params.seed) is not int):
        raise StoryError("The seed must be an integer or None.")
    if not valid_story(params):
        raise StoryError("These choices do not make a reasonable, solvable forest-trail story.")


# ---------------------------------------------------------------------------
# Prompts and Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a funny superhero story about Frog-Dim solving {case['title']} on {params.trail}.",
        f"Show how Frog-Dim and {params.helper_name} use evidence and share their gear to help two hikers.",
        "Include a kind exchange after a mistaken guess, a clear mystery solution, and a final image showing that the forest trail is safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    case = world.facts["case"]
    return [
        QAItem(
            question="What mystery did Frog-Dim and the trail helper investigate?",
            answer=f"They investigated why {case['oddity']}. They solved it by discovering that {case['cause']}.",
        ),
        QAItem(
            question="What did Frog-Dim guess at first, and what happened?",
            answer=(
                f"Frog-Dim first guessed that {case['false_suspect']} was responsible and "
                f"{case['wrong_action']}. The cape snagged on a branch, but {params.helper_name} "
                "kept the hikers safely at the fork."
            ),
        ),
        QAItem(
            question="Which clue helped solve the mystery?",
            answer=(
                f"{params.helper_name} noticed that {case['clue']}. That evidence showed that "
                f"{case['cause']}, rather than the thing Frog-Dim had first suspected."
            ),
        ),
        QAItem(
            question=f"How did {params.helper_name} help the hikers?",
            answer=(
                f"{params.helper_name} stayed with the hikers at the safe fork while Frog-Dim "
                "checked the strange event. Later, the helper shared useful gear and helped put "
                "the evidence-based plan into action."
            ),
        ),
        QAItem(
            question="How did sharing help the superhero team?",
            answer=(
                f"Frog-Dim and {params.helper_name} shared {case['tool']} and combined their skills. "
                f"{case['method']} Their teamwork helped explain the clue and make the trail safe."
            ),
        ),
        QAItem(
            question="What did Frog-Dim learn after nearly using the word “moron” for themself?",
            answer=(
                "Frog-Dim learned that one mistaken guess is not a name to use for themself. "
                "The helper encouraged the hero to check the evidence, and listening helped them solve the mystery."
            ),
        ),
        QAItem(
            question="What showed that the story ended happily?",
            answer=(
                f"The hikers were able to continue along the safe trail. The final image was that "
                f"{case['ending']}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trail marker?",
            answer="A trail marker is a sign, ribbon, or painted mark that helps people stay on a path and find their way.",
        ),
        QAItem(
            question="Why might a puddle show a moving reflection?",
            answer="A puddle can reflect nearby lights, and ripples or moving objects can make those reflected lights seem to shift.",
        ),
        QAItem(
            question="How can a superhero help without using great strength?",
            answer="A superhero can observe carefully, share useful tools, and work with other people to solve a problem safely.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = _simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Trace and output
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- simulated forest-trail state ---"]
    for entity in world.entities.values():
        meters = {key: round(value, 3) for key, value in entity.meters.items() if value}
        memes = {key: round(value, 3) for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        if entity.owner:
            details.append(f"owner={entity.owner}")
        if entity.holder:
            details.append(f"holder={entity.holder}")
        lines.append(
            f"  {entity.id:12} ({entity.kind}/{entity.type}) {entity.label}: "
            + " ".join(details)
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append("  state changes:")
    lines.extend(f"    - {event}" for event in world.events)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        output.append(f"{index}. {prompt}")
    output.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.extend(["", "== (3) World knowledge =="])
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Every registered case must offer evidence, a safe setback, a shared solution,
% and a concrete ending image before it counts as a valid story.
valid_case(C) :-
    case(C),
    has_clue(C),
    safe_setback(C),
    shares_solution(C),
    ending_image(C).

% A selected mystery is valid only when it passes the same reasonableness gate.
valid_story(C) :-
    selected_case(C),
    valid_case(C).
"""


def asp_facts(selected: Optional[str] = None) -> str:
    from storyworlds import asp

    if selected is not None and selected not in MYSTERIES:
        raise StoryError(f"Unknown mystery {selected!r}; cannot build ASP facts.")

    lines: list[str] = []
    for case_id, case in MYSTERIES.items():
        lines.append(asp.fact("case", case_id))
        if case["has_clue"]:
            lines.append(asp.fact("has_clue", case_id))
        if case["safe_setback"]:
            lines.append(asp.fact("safe_setback", case_id))
        if case["shares_solution"]:
            lines.append(asp.fact("shares_solution", case_id))
        if case["ending_image"]:
            lines.append(asp.fact("ending_image", case_id))
    if selected is not None:
        lines.append(asp.fact("selected_case", selected))
    return "\n".join(lines)


def asp_program(show: str, selected: Optional[str] = None) -> str:
    return f"{asp_facts(selected)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp

    all_symbols = asp.one_model(asp_program("#show valid_case/1."))
    asp_cases = set(asp.atoms(all_symbols, "valid_case"))
    python_cases = {
        (case_id,)
        for case_id, case in MYSTERIES.items()
        if _case_is_reasonable(case)
    }
    if asp_cases != python_cases:
        print("MISMATCH between ASP and Python story reasonableness gates.")
        print("ASP:", sorted(asp_cases))
        print("Python:", sorted(python_cases))
        return 1

    for case_id, case in MYSTERIES.items():
        symbols = asp.one_model(asp_program("#show valid_story/1.", selected=case_id))
        asp_selected = set(asp.atoms(symbols, "valid_story"))
        params = StoryParams(
            seed=17,
            helper_name="Pip",
            trail="Fernbutton Trail",
            mystery=case_id,
        )
        expected_selected = {(case_id,)} if valid_story(params) else set()
        if asp_selected != expected_selected:
            print(f"MISMATCH for selected mystery {case['title']}.")
            print("ASP:", sorted(asp_selected))
            print("Python:", sorted(expected_selected))
            return 1

        sample = generate(params)
        if (
            sample.world is None
            or sample.world.facts.get("phase") != "resolved"
            or not sample.world.facts.get("resolved")
            or "mystery_solved" not in sample.world.fired
            or "“" not in sample.story
            or "moron" not in sample.story
        ):
            print(f"Generated-story exercise failed for {case['title']}.")
            return 1

    print("OK: ASP and Python gates match; every mystery generated a resolved story.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A forest-trail superhero storyworld about Frog-Dim, teamwork, and solving funny mysteries."
    )
    parser.add_argument("--helper", choices=tuple(HELPERS))
    parser.add_argument("--trail", choices=TRAILS)
    parser.add_argument("--mystery", choices=tuple(MYSTERIES))
    parser.add_argument("-n", type=int, default=1, help="number of stories to generate")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true", help="generate one story for every registered mystery")
    parser.add_argument("--trace", action="store_true", help="show the simulated world state")
    parser.add_argument("--qa", action="store_true", help="show prompts and question-answer sets")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of formatted prose")
    parser.add_argument("--asp", action="store_true", help="show the ASP result for the selected mystery")
    parser.add_argument("--verify", action="store_true", help="check ASP/Python parity and exercise generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print the inline ASP program and registry facts")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=None,
        helper_name=args.helper or rng.choice(tuple(HELPERS)),
        trail=args.trail or rng.choice(TRAILS),
        mystery=args.mystery or rng.choice(tuple(MYSTERIES)),
    )


CURATED = [
    StoryParams(seed=11, helper_name="Pip", trail="Fernbutton Trail", mystery="rattle"),
    StoryParams(seed=23, helper_name="Tavi", trail="Bramblecup Trail", mystery="footprints"),
    StoryParams(seed=37, helper_name="Mira", trail="Moonmoss Trail", mystery="twinkle"),
    StoryParams(seed=49, helper_name="Bram", trail="Fernbutton Trail", mystery="ribbons"),
]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.show_asp:
            print(asp_program("#show valid_case/1."))
            return
        if args.verify:
            raise SystemExit(asp_verify())

        base_seed = args.seed if args.seed is not None else random.randrange(2**31)

        if args.asp:
            params = resolve_params(args, random.Random(base_seed))
            params.seed = base_seed
            from storyworlds import asp

            model = asp.one_model(
                asp_program("#show valid_story/1.", selected=params.mystery)
            )
            print(sorted(set(asp.atoms(model, "valid_story"))))
            return

        if args.n <= 0 and not args.all:
            raise StoryError("The number of stories must be at least 1.")

        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            samples: list[StorySample] = []
            for index in range(args.n):
                params = resolve_params(args, random.Random(base_seed + index))
                params.seed = base_seed + index
                samples.append(generate(params))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return

        for index, sample in enumerate(samples):
            header = f"### variant {index + 1}" if len(samples) > 1 else ""
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
