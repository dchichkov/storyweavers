#!/usr/bin/env python3
"""
A small forest-trail superhero storyworld about Frog-Dim, a missing lantern,
and a proud puzzle-maker whose funny mystery is solved through careful
observation and sharing.

Seed image:
---
On a forest trail, a superhero frog and a friend investigate a strange
lantern puzzle. Frog-Dim's power can soften bright light, but pride makes the
first attempt worse. Clues lead to a raccoon inventor, a silly badge, and a
happy solution built by working together.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_repo_root = None
for _parent in Path(__file__).resolve().parents:
    if _parent.name == "storyworlds":
        _repo_root = _parent.parent
        break
if _repo_root is not None:
    sys.path.insert(0, str(_repo_root))

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part for part in para if part) for para in self.paragraphs if para)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    partner_name: str = "Pip"
    trail: str = "Fernloop Trail"
    mystery_id: str = "backward_sign"


PARTNER_NAMES = ["Pip", "Moss", "Tansy", "Juniper", "Bramble", "Wren"]
TRAILS = ["Fernloop Trail", "Mossbell Trail", "Bracken Bend Trail"]


MYSTERIES = {
    "backward_sign": {
        "title": "the backward arrow",
        "setting": "forest_trail",
        "symptom": (
            "the arrow at the fork seemed to point toward a bramble patch, "
            "and the welcome lantern had vanished"
        ),
        "mistake": (
            "{hero} dimmed the junction lamp and nearly followed the arrow's "
            "bright reflection into the brambles"
        ),
        "clue": (
            "a silver arrow flashed on the back of the sign when Frog-Dim "
            "softened only the lamp's glare"
        ),
        "explanation": (
            "A little mirror behind the sign had flipped the arrow's reflection. "
            "Rollo's dotted acorn trail led from the mirror to the lantern hidden "
            "in a hollow stump."
        ),
        "repair": (
            "Frog-Dim softened the mirror's glare while Rollo removed it, and "
            "{partner} turned the arrow toward the safe white stones"
        ),
        "final_image": (
            "Warm lantern light washed over the corrected arrow while a squirrel "
            "in a berry crown bowed to the sign."
        ),
        "has_superhero": True,
        "has_clue": True,
        "has_sharing": True,
        "has_humor": True,
        "has_repair": True,
    },
    "acorn_signal": {
        "title": "the acorn signal",
        "setting": "forest_trail",
        "symptom": (
            "the trail lamps blinked three times, paused, then blinked twice, "
            "and the welcome lantern had vanished"
        ),
        "mistake": (
            "{hero} dimmed every lamp to see if the strange blinking would stop, "
            "leaving the junction darker than before"
        ),
        "clue": (
            "a tiny acorn pendulum tapped one loose lamp switch in a steady rhythm"
        ),
        "explanation": (
            "Rollo had hung the acorn pendulum as a puzzle signal, but it had "
            "bumped a switch. Its blue string led to the hollow stump where he "
            "had tucked the welcome lantern."
        ),
        "repair": (
            "Rollo untied the pendulum from the switch, {partner} steadied the "
            "lamp, and Frog-Dim used just a little power to soften the glare"
        ),
        "final_image": (
            "The lantern glowed steadily again, and the acorn pendulum swung "
            "harmlessly like a tiny conductor above the giggling hikers."
        ),
        "has_superhero": True,
        "has_clue": True,
        "has_sharing": True,
        "has_humor": True,
        "has_repair": True,
    },
    "rolling_lantern": {
        "title": "the runaway lantern",
        "setting": "forest_trail",
        "symptom": (
            "the welcome lantern rolled uphill along the trail, even though the "
            "path sloped gently the other way"
        ),
        "mistake": (
            "{hero} dashed after the rolling light, cape-first, and almost missed "
            "the white stones marking the safe path"
        ),
        "clue": (
            "in the glowberry light, a blue cord appeared looped around the "
            "lantern cart's wheel and trailing beneath a hollow stump"
        ),
        "explanation": (
            "Rollo had rigged a pulley to pull the lantern cart toward the stump "
            "for his puzzle. The cord had caught on a root and sent the cart "
            "rolling along the trail."
        ),
        "repair": (
            "Rollo loosened the pulley cord, {partner} held the cart steady, and "
            "Frog-Dim softened the lantern's glare so they could guide it safely"
        ),
        "final_image": (
            "The lantern shone from its post again while Rollo's empty cart "
            "rolled gently into a pile of soft leaves."
        ),
        "has_superhero": True,
        "has_clue": True,
        "has_sharing": True,
        "has_humor": True,
        "has_repair": True,
    },
}


OPENINGS = [
    "The forest was busy getting ready for its evening lantern walk.",
    "A chorus of crickets welcomed the day's last sunlight to the woods.",
    "The forest trail smelled of pine needles, wet leaves, and berry muffins.",
    "On the forest trail, even the squirrels seemed to be getting ready for a show.",
]


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(
        Entity(
            id="frog_dim",
            kind="character",
            type="superhero_frog",
            label="Frog-Dim",
            meters={"light_control": 1.0, "courage": 1.0},
            memes={"pride": 0.85, "curiosity": 0.55, "teamwork": 0.15},
        )
    )
    partner = world.add(
        Entity(
            id="partner",
            kind="character",
            type="friend",
            label=params.partner_name,
            meters={"glowberries": 1.0, "observation": 0.9},
            memes={"patience": 0.9, "trust": 0.55},
        )
    )
    raccoon = world.add(
        Entity(
            id="rollo",
            kind="character",
            type="raccoon_inventor",
            label="Rollo",
            meters={"riddle_skill": 0.9, "lantern_knowledge": 0.9},
            memes={"pride": 0.9, "willingness_to_help": 0.35},
        )
    )
    lamp = world.add(
        Entity(
            id="junction_lamp",
            kind="thing",
            type="trail_lamp",
            label="junction lamp",
            meters={"brightness": 1.0},
            memes={},
        )
    )
    welcome_lantern = world.add(
        Entity(
            id="welcome_lantern",
            kind="thing",
            type="lantern",
            label="welcome lantern",
            meters={"brightness": 1.0, "at_post": 0.0},
            memes={},
        )
    )
    sign = world.add(
        Entity(
            id="arrow_sign",
            kind="thing",
            type="trail_sign",
            label="arrow sign",
            meters={"alignment": 0.5},
            memes={},
        )
    )
    stump = world.add(
        Entity(
            id="hollow_stump",
            kind="place",
            type="hollow_stump",
            label="hollow stump",
            meters={"lantern_inside": 1.0},
            memes={},
        )
    )
    berries = world.add(
        Entity(
            id="glowberries",
            kind="thing",
            type="glowberry_jar",
            label="glowberries",
            owner=partner.id,
            meters={"light": 0.7, "portions": 4.0},
            memes={"shared": 0.0},
        )
    )

    world.facts.update(
        hero=hero,
        partner=partner,
        raccoon=raccoon,
        lamp=lamp,
        welcome_lantern=welcome_lantern,
        sign=sign,
        stump=stump,
        berries=berries,
        params=params,
        mystery=MYSTERIES[params.mystery_id],
    )


def _selection_token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.partner_name}|{params.trail}|{params.mystery_id}"
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)

    hero = world.facts["hero"]
    partner = world.facts["partner"]
    raccoon = world.facts["raccoon"]
    lamp = world.facts["lamp"]
    lantern = world.facts["welcome_lantern"]
    sign = world.facts["sign"]
    stump = world.facts["stump"]
    berries = world.facts["berries"]
    mystery = world.facts["mystery"]

    token = _selection_token(params)
    opening = OPENINGS[token % len(OPENINGS)]

    world.say(
        f"{opening} Frog-Dim, the bright-eyed superhero frog, bounded onto "
        f"{params.trail} with {partner.label}."
    )
    world.say(
        "Frog-Dim could soften a bright glare with a wave of his hand, but he "
        "could not make a dark trail brighter. His silver cape had a tiny "
        "lily-pad badge that flashed whenever he felt especially heroic."
    )

    world.para()
    world.say(
        f"Then {mystery['symptom']}. The white stepping stones still marked the "
        "safe route, but the hikers stopped and wondered what had happened."
    )
    mistake = mystery["mistake"].format(hero=hero.label)
    world.say(
        f"Frog-Dim was so proud of his power that {mistake}. Nobody was hurt, "
        "but the junction was harder to see."
    )
    world.say(
        f'"Wait," {partner.label} said. "We still have the white stones. '
        "I’m sharing my glowberries, so let’s look for one clue before we "
        'touch another lamp."'
    )
    world.say(
        f'"You’re right," Frog-Dim replied. "I was trying to solve it alone. '
        "I’ll keep the safe markers bright and use my power more carefully.\""
    )

    hero.meters["teamwork"] = 0.8
    hero.memes["pride"] = 0.45
    hero.memes["teamwork"] = 0.9
    partner.memes["trust"] = 0.8
    lamp.meters["brightness"] = 0.35
    berries.memes["shared"] = 1.0
    berries.meters["portions"] = 2.0
    world.fired.add(("shared_glowberries", "partner", "hikers"))
    world.fired.add(("hero_changed_plan", "frog_dim"))
    world.trace.append("The partner shared glowberries; Frog-Dim stopped dimming the trail markers.")

    world.para()
    world.say(
        f"While {partner.label} shared the berries, Frog-Dim softened only the "
        f"glare. {mystery['clue'].capitalize()}."
    )
    world.say(
        "A dotted trail of acorns led to a hollow stump. Rollo the raccoon "
        "popped out beside the missing welcome lantern, wearing his inventor's "
        "hat sideways; an acorn rolled off its brim and plinked into a fern."
    )
    world.say(
        f'"Behold, M.O.R.O.N.—Master Of Riddles, Owls, and Nightlights!" '
        f"Rollo announced proudly."
    )
    world.say(
        f'"That spells " + "'moron,'" + f" {partner.label} said gently, "
        '"and that word can hurt someone’s feelings."'
    )
    world.say(
        '"Oh! I wanted a silly badge, not a hurtful one," Rollo said. '
        '"I’ll choose kinder initials. I hid the lantern because I was proud '
        "of my puzzle and wanted everyone to solve it. I forgot this trail "
        'belongs to everyone."'
    )
    world.say(
        f'"Then help us put the lantern back," Frog-Dim said. "We can solve '
        'the rest together."'
    )

    raccoon.memes["pride"] = 0.55
    raccoon.memes["willingness_to_help"] = 1.0
    partner.memes["trust"] = 1.0
    stump.meters["lantern_inside"] = 0.0
    world.fired.add(("mystery_explained", "rollo"))
    world.trace.append("Rollo admitted he hid the lantern and agreed to help repair his puzzle.")

    world.para()
    world.say(
        f'"I can use my power gently," Frog-Dim said. "Rollo, you know the '
        f"puzzle rig. {partner.label}, can you help me steady the lantern?"'
    )
    world.say(
        f'"Ready," {partner.label} replied. "We can share the work, too."'
    )
    repair = mystery["repair"].format(partner=partner.label)
    world.say(f"Together they {repair}. They restored the welcome lantern to its post.")
    world.say(
        f'"And next time I’ll ask before turning the trail into a puzzle," Rollo '
        'promised. His new badge, made from a leaf, read "Helpful Raccoon."'
    )

    hero.memes["pride"] = 0.3
    hero.memes["teamwork"] = 1.0
    lamp.meters["brightness"] = 1.0
    lantern.meters["brightness"] = 1.0
    lantern.meters["at_post"] = 1.0
    sign.meters["alignment"] = 1.0
    berries.memes["shared"] = 1.0
    berries.meters["portions"] = 0.0
    world.fired.add(("lantern_restored", "welcome_lantern"))
    world.fired.add(("trail_safe", params.trail))
    world.fired.add(("puzzle_repaired", params.mystery_id))
    world.trace.append("The lantern returned to its post; the trail markers were bright and clear.")

    world.para()
    world.say(
        f"With the welcome lantern shining again, the hikers set off along the "
        f"safe stones. {partner.label} passed the last glowberries around, and "
        f"Rollo walked beside Frog-Dim, sharing how the puzzle worked."
    )
    world.say(mystery["final_image"])
    world.say(
        "Frog-Dim had learned that a hero’s power works best when the whole "
        "team gets to share the light."
    )

    world.facts.update(
        params=params,
        mystery=mystery,
        token=token,
        opening_index=token % len(OPENINGS),
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def _case_is_reasonable(case: dict) -> bool:
    required_text = (
        "title",
        "setting",
        "symptom",
        "mistake",
        "clue",
        "explanation",
        "repair",
        "final_image",
    )
    return (
        case.get("setting") == "forest_trail"
        and all(isinstance(case.get(key), str) and case[key].strip() for key in required_text)
        and case.get("has_superhero") is True
        and case.get("has_clue") is True
        and case.get("has_sharing") is True
        and case.get("has_humor") is True
        and case.get("has_repair") is True
    )


def valid_story(params: Optional[StoryParams | str] = None) -> bool:
    """Return whether one requested mystery, or the complete registry, is sound."""
    if params is None:
        return all(_case_is_reasonable(case) for case in MYSTERIES.values())
    mystery_id = params.mystery_id if isinstance(params, StoryParams) else params
    return mystery_id in MYSTERIES and _case_is_reasonable(MYSTERIES[mystery_id])


def _validate_params(params: StoryParams) -> None:
    if params.mystery_id not in MYSTERIES:
        raise StoryError(
            f"Unknown mystery {params.mystery_id!r}; choose one of {', '.join(MYSTERIES)}."
        )
    if params.partner_name not in PARTNER_NAMES:
        raise StoryError(
            f"Unknown partner name {params.partner_name!r}; choose one of {', '.join(PARTNER_NAMES)}."
        )
    if params.trail not in TRAILS:
        raise StoryError(
            f"Unknown trail {params.trail!r}; choose one of {', '.join(TRAILS)}."
        )
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("The seed must be an integer.")
    if not valid_story(params):
        raise StoryError(f"The mystery {params.mystery_id!r} does not make a reasonable story.")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    mystery = world.facts["mystery"]
    return [
        f"Write a child-friendly superhero story on {params.trail} about Frog-Dim and {mystery['title']}.",
        f"Show how Frog-Dim and {params.partner_name} share clues and glowberries to solve a funny forest mystery.",
        "Tell a complete story about a proud hero learning to share the work, with spoken dialogue and a clear happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    mystery = world.facts["mystery"]

    return [
        QAItem(
            question="What strange mystery did Frog-Dim and the friend find on the trail?",
            answer=(
                f"On {params.trail}, {mystery['symptom']}. The white stepping stones "
                "kept the hikers safe while Frog-Dim and the friend investigated."
            ),
        ),
        QAItem(
            question="What did Frog-Dim do wrong at first?",
            answer=(
                f"Frog-Dim was so proud of his power that {mystery['mistake'].format(hero='he')}. "
                "His friend helped him see that dimming the trail was making the problem worse."
            ),
        ),
        QAItem(
            question=f"How did {params.partner_name} help Frog-Dim?",
            answer=(
                f"{params.partner_name} shared glowberries and reminded Frog-Dim to follow "
                "the white stones and look for one clue at a time. That advice changed "
                "Frog-Dim's plan before anyone was hurt."
            ),
        ),
        QAItem(
            question="What clue helped them solve the mystery?",
            answer=(
                f"They noticed that {mystery['clue']}. The clue pointed them toward "
                "Rollo and the hidden welcome lantern."
            ),
        ),
        QAItem(
            question="Who had hidden the welcome lantern, and why?",
            answer=(
                f"Rollo the raccoon had hidden the lantern because he was proud of his "
                "puzzle and wanted hikers to solve it. He realized that the trail "
                "belonged to everyone and agreed to help put things right."
            ),
        ),
        QAItem(
            question="What did M.O.R.O.N. mean on Rollo's badge?",
            answer=(
                "Rollo said it meant “Master Of Riddles, Owls, and Nightlights.” "
                "When his friend explained that the letters spelled an unkind word, "
                "Rollo decided to choose kinder initials."
            ),
        ),
        QAItem(
            question="How did the team fix the trail?",
            answer=(
                f"Frog-Dim, {params.partner_name}, and Rollo worked together: "
                f"{mystery['repair'].format(partner=params.partner_name)}. "
                "They returned the welcome lantern to its post."
            ),
        ),
        QAItem(
            question="What final image showed that the mystery had a happy ending?",
            answer=f"{mystery['final_image']} The hikers could follow the safe trail again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a forest trail?",
            answer=(
                "A forest trail is a path through the woods. Signs, lamps, and clear "
                "markers help people follow it safely."
            ),
        ),
        QAItem(
            question="What does a superhero do?",
            answer=(
                "A superhero uses special abilities to help others. Good heroes also "
                "listen, think carefully, and work with their friends."
            ),
        ),
        QAItem(
            question="Why can sharing help solve a mystery?",
            answer=(
                "Sharing lets people combine what they notice and what they can do. "
                "One person may spot a clue while another knows how to use it."
            ),
        ),
        QAItem(
            question="What is a clue?",
            answer=(
                "A clue is a detail that helps someone understand what happened. "
                "Following clues carefully can lead to an answer."
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A reasonable story includes a forest-trail superhero mystery, a clue,
% sharing, humor, and a repaired lantern.
valid_story(C) :-
    forest_trail(C),
    superhero(C),
    mystery(C),
    clue_found(C),
    sharing(C),
    humor(C),
    lantern_restored(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for mystery_id, case in MYSTERIES.items():
        lines.append(asp.fact("mystery_case", mystery_id))
        if case.get("setting") == "forest_trail":
            lines.append(asp.fact("forest_trail", mystery_id))
        if case.get("has_superhero"):
            lines.append(asp.fact("superhero", mystery_id))
        if case.get("title"):
            lines.append(asp.fact("mystery", mystery_id))
        if case.get("has_clue"):
            lines.append(asp.fact("clue_found", mystery_id))
        if case.get("has_sharing"):
            lines.append(asp.fact("sharing", mystery_id))
        if case.get("has_humor"):
            lines.append(asp.fact("humor", mystery_id))
        if case.get("has_repair"):
            lines.append(asp.fact("lantern_restored", mystery_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_cases = set(asp.atoms(model, "valid_story"))
    python_cases = {
        (mystery_id,)
        for mystery_id in MYSTERIES
        if valid_story(mystery_id)
    }
    if asp_cases != python_cases:
        print("MISMATCH between ASP and Python reasonableness gate.")
        print("ASP:", sorted(asp_cases))
        print("Python:", sorted(python_cases))
        return 1

    print("OK: clingo parity matches the Python reasonableness gate.")
    return 0


def verify_generated_stories() -> int:
    for index, mystery_id in enumerate(MYSTERIES):
        params = StoryParams(
            seed=9100 + index,
            partner_name=PARTNER_NAMES[index],
            trail=TRAILS[index],
            mystery_id=mystery_id,
        )
        sample = generate(params)
        required_phrases = (
            "Frog-Dim",
            "M.O.R.O.N.",
            "glowberries",
            mystery_case_text(MYSTERIES[mystery_id]["final_image"]),
        )
        if any(phrase not in sample.story for phrase in required_phrases):
            print(f"Generated-story check failed for {mystery_id}: required story detail missing.")
            return 1
        if not any("said" in sentence for sentence in sample.story.split()):
            print(f"Generated-story check failed for {mystery_id}: spoken dialogue missing.")
            return 1
        if not sample.story.strip().endswith("light."):
            print(f"Generated-story check failed for {mystery_id}: complete ending missing.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print(f"Generated-story check failed for {mystery_id}: Q&A missing.")
            return 1
        if not valid_story(params):
            print(f"Generated-story check failed for {mystery_id}: Python gate rejected it.")
            return 1

    print("OK: generated stories include clues, dialogue, Q&A, and complete endings.")
    return 0


def mystery_case_text(text: str) -> str:
    """Keep generated-story checks explicit and readable."""
    return text


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "A forest-trail superhero storyworld about Frog-Dim, a funny mystery, "
            "and the power of sharing."
        )
    )
    parser.add_argument("--partner-name", choices=PARTNER_NAMES)
    parser.add_argument("--trail", choices=TRAILS)
    parser.add_argument("--mystery", dest="mystery_id", choices=list(MYSTERIES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    partner = args.partner_name or rng.choice(PARTNER_NAMES)
    trail = args.trail or rng.choice(TRAILS)
    mystery_id = args.mystery_id or rng.choice(list(MYSTERIES))
    return StoryParams(
        seed=None,
        partner_name=partner,
        trail=trail,
        mystery_id=mystery_id,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        state = []
        if meters:
            state.append(f"meters={meters}")
        if memes:
            state.append(f"memes={memes}")
        lines.append(f"  {entity.id:16} ({entity.kind:10}) {' '.join(state)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append("  events:")
    lines.extend(f"    - {event}" for event in world.trace[-6:])
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    out.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.extend(["", "== (3) World knowledge =="])
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(out)


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


CURATED = [
    StoryParams(
        partner_name="Pip",
        trail="Fernloop Trail",
        mystery_id="backward_sign",
    ),
    StoryParams(
        partner_name="Tansy",
        trail="Mossbell Trail",
        mystery_id="acorn_signal",
    ),
    StoryParams(
        partner_name="Wren",
        trail="Bracken Bend Trail",
        mystery_id="rolling_lantern",
    ),
]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        try:
            status = asp_verify()
        except Exception as exc:
            print(f"ASP verification could not run: {exc}")
            sys.exit(1)
        if status == 0:
            status = verify_generated_stories()
        sys.exit(status)
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return
    if args.n < 1 and not args.all:
        parser.error("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            samples.append(generate(params))
    else:
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


if __name__ == "__main__":
    main()
