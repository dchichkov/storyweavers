#!/usr/bin/env python3
"""
A child-safe mystery storyworld about a hammock, a luau, and sharing.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Case:
    id: str
    opening: str
    clue: str
    danger: str
    first_idea: str
    discovery: str
    warning: str
    safe_action: str
    sharing_turn: str
    proof: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    setting: str
    feature: str
    object: str
    name: str
    animal: str
    trait: str
    case: str = ""
    telling: str = ""
    seed: Optional[int] = None


SETTINGS = {
    "palm_grove": "the palm grove",
    "moonlit_cove": "the moonlit cove",
    "garden_patio": "the garden patio",
}

FEATURES = {"sharing"}
OBJECTS = {"hammock"}

ANIMALS = [
    ("Luna", "lemur"),
    ("Milo", "monkey"),
    ("Tia", "toucan"),
    ("Pip", "parrot"),
    ("Nori", "otter"),
]

TRAITS = ["curious", "patient", "cheerful", "careful", "brave"]
TELLINGS = ["clue_first", "question_turn", "quiet_build", "friend_view", "action_turn"]

CASES = {
    "missing_shell": Case(
        id="missing_shell",
        opening="The luau was almost ready, but the smooth white shell that marked the hammock's sharing turn had vanished.",
        clue="Luna noticed three damp dots leading from the hammock toward the snack table.",
        danger="Without the shell, everyone might crowd the hammock at once and make its ropes strain.",
        first_idea="Luna wanted to search under every leaf immediately.",
        discovery="A tiny smear of coconut cream on one leaf showed that someone had carried the shell while helping with the food.",
        warning='"One at a time, please. Let us share the hammock safely," Luna called.',
        safe_action="The grown-up host tied a bright ribbon to the hammock and checked its knots before anyone climbed in.",
        sharing_turn="Luna asked each friend what they had seen, and the answers made a trail: Tia had moved the shell beside the fruit bowl so nobody would trip on it.",
        proof="The shell was found beside the fruit bowl, clean and safe.",
        ending="Friends took turns in the hammock while others shared fruit, songs, and cool shade below.",
        lesson="Sharing works best when everyone knows the turn and listens to the clues.",
    ),
    "cut_rope": Case(
        id="cut_rope",
        opening="At the luau, the hammock hung between two palms like a quiet boat, but one rope looked shorter than the others.",
        clue="A fringe of fresh fiber lay beneath the left palm, exactly where the rope rubbed against the bark.",
        danger="If someone climbed in before the rope was repaired, the hammock could tip and spill its friends.",
        first_idea="Luna thought about tying the loose rope with a strip of party ribbon.",
        discovery="When the ribbon slipped on the smooth fibers, Luna understood that a quick hack would not make the hammock safe.",
        warning='"Pause the hammock turn! Please stay on the sand," Luna said.',
        safe_action="The host closed the hammock, replaced the damaged rope with a strong one, and tested both sides with careful pulls.",
        sharing_turn="While they waited, the friends shared the shell marker and invented a song about taking turns.",
        proof="The new rope held steady when the host tested the hammock twice.",
        ending="Soon Luna and two friends rocked gently together, then climbed out so the next group could share the shade.",
        lesson="A clever-looking hack is not enough when safety matters; ask for skilled help.",
    ),
    "hidden_note": Case(
        id="hidden_note",
        opening="A paper palm leaf announced the luau's hammock turns, but the last three names had been rubbed away.",
        clue="Luna found tiny pencil flakes caught in the hammock's lower knot.",
        danger="The missing names could make friends argue over who should go first.",
        first_idea="Luna planned to guess the order from memory.",
        discovery="The knot held a folded scrap with three half-written names, so guessing could leave someone out.",
        warning='"Let us pause and ask everyone. Every friend deserves a turn," Luna said.',
        safe_action="The host laid out fresh cards, read each name aloud, and checked the hammock before reopening the turn list.",
        sharing_turn="Milo admitted he had erased the names while trying to hack a decoration, and the friends helped rewrite the list instead of blaming him.",
        proof="Every name appeared on a clear card, with a star beside the next turn.",
        ending="The hammock swayed beneath the lanterns as each friend waited, shared, and cheered for the others.",
        lesson="When a mistake hides a turn, honest sharing can repair trust.",
    ),
    "vanished_lantern": Case(
        id="vanished_lantern",
        opening="As the luau lights came on, the little lantern beside the hammock disappeared.",
        clue="A warm circle on the sand showed where it had stood, while a trail of flower petals led toward the music table.",
        danger="Without the lantern, someone might miss the hammock's rope after sunset.",
        first_idea="Luna wanted to follow the petals alone through the dim grove.",
        discovery="A cracked glow stick near the path showed that the petals marked a shortcut, not a safe search route.",
        warning='"Stay with a buddy and keep the hammock closed until we find its light," Luna said.',
        safe_action="The host brought a torch, checked the path, and found the lantern resting behind a basket.",
        sharing_turn="Tia explained that she had moved it to share light with the musicians, and everyone agreed on a safer place between both groups.",
        proof="The lantern shone from a hook where the hammock and music table could both be seen.",
        ending="Friends shared the hammock's gentle swing while the luau music glowed around them.",
        lesson="Sharing a useful thing means placing it where everyone can use it safely.",
    ),
}

PROMPTS = [
    "Write a child-friendly mystery about a hammock at a luau.",
    "Tell a story where Luna solves a small hammock mystery by sharing clues and turns.",
    "Show why a quick hack is not always a safe repair, and end with friends sharing fairly.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hammock, luau, hack, and sharing mystery world.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--feature", choices=FEATURES)
    parser.add_argument("--object", choices=OBJECTS)
    parser.add_argument("--name")
    parser.add_argument("--animal", choices=[a for _, a in ANIMALS])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--telling", choices=TELLINGS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.feature and args.feature != "sharing":
        raise StoryError("This mystery uses sharing as its central feature.")
    if args.object and args.object != "hammock":
        raise StoryError("This mystery centers on a hammock.")
    name = args.name or rng.choice(ANIMALS)[0]
    animal = args.animal or next((a for n, a in ANIMALS if n == name), rng.choice(ANIMALS)[1])
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        feature="sharing",
        object="hammock",
        name=name,
        animal=animal,
        trait=args.trait or rng.choice(TRAITS),
        case=args.case or rng.choice(sorted(CASES)),
        telling=args.telling or rng.choice(TELLINGS),
    )


def tell(params: StoryParams, rng: random.Random) -> World:
    world = World()
    hero = world.add(Entity(params.name, "character", params.animal, params.name))
    hammock = world.add(Entity("hammock", "thing", "hammock", "the hammock"))
    luau = world.add(Entity("luau", "thing", "luau", "the luau"))
    hero.memes.update(curiosity=1.0, sharing=1.0)
    hammock.meters.update(safety=1.0, turns=0.0)
    luau.meters["friendliness"] = 1.0
    case = CASES[params.case]

    openings = [
        f"Lanterns bobbed in {SETTINGS[params.setting]} as {hero.id}, a {params.trait} {params.animal}, helped prepare the luau.",
        f"The luau smelled of fruit and toasted coconut in {SETTINGS[params.setting]}. {hero.id}, a {params.trait} {params.animal}, watched the hammock carefully.",
        f"In {SETTINGS[params.setting]}, music began before the stars appeared. {hero.id}, a {params.trait} {params.animal}, was in charge of the hammock's turn marker.",
    ]
    world.say(rng.choice(openings))
    world.say(case.opening)
    world.para()

    if params.telling == "question_turn":
        world.say(f'"What changed?" asked {hero.id}.')
        world.say(case.clue)
        world.say(case.danger)
    elif params.telling == "friend_view":
        world.say(case.danger)
        world.say(case.clue)
    else:
        world.say(case.clue)
        world.say(f"That clue mattered because {case.danger[0].lower() + case.danger[1:]}")
    world.facts.update(clue=case.clue, danger=case.danger)
    world.para()

    world.say(case.first_idea)
    world.say(case.discovery)
    world.say(f'"{case.warning.split(chr(34))[1]}"')
    world.say("The friends stepped back and shared what they knew instead of rushing.")
    world.para()

    world.say(case.sharing_turn)
    world.say(case.safe_action)
    hammock.meters["safety"] = 2.0
    hammock.meters["turns"] = 1.0
    world.facts["resolved"] = True
    world.para()

    world.say(f"At last, {case.proof}")
    world.say(case.ending)
    world.say(f"{hero.id} remembered: {case.lesson}")
    world.facts.update(hero=hero, hammock=hammock, luau=luau, case=case, setting=SETTINGS[params.setting])
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        PROMPTS[0],
        PROMPTS[1],
        f"Write a mystery in which this clue matters: {case.clue}",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    case: Case = world.facts["case"]  # type: ignore[assignment]
    return [
        QAItem("Who solved the hammock mystery?", f"{hero.label}, a careful {hero.type}, solved the mystery."),
        QAItem("What clue helped solve the mystery?", case.clue),
        QAItem("What danger did the friends avoid?", case.danger),
        QAItem("How did the friends use sharing?", case.sharing_turn),
        QAItem("How did the story end?", case.ending),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a hammock?", "A hammock is a hanging bed or seat made from fabric or rope."),
        QAItem("What is a luau?", "A luau is a festive gathering with food, music, and friendly celebration."),
        QAItem("What is a hack?", "A hack is a quick trick or makeshift solution, but it may not be safe for every problem."),
        QAItem("Why is sharing important?", "Sharing gives everyone a fair chance to use things and helps people work together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_hammock :- checked_hammock, turn_marker.
shared_event :- safe_hammock, fair_turns.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "palm_grove"),
            asp.fact("object", "hammock"),
            asp.fact("event", "luau"),
            asp.fact("feature", "sharing"),
            asp.fact("checked_hammock"),
            asp.fact("turn_marker"),
            asp.fact("fair_turns"),
        ]
    )


def asp_program(show: str = "#show shared_event/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if ("shared_event",) in asp.atoms(model, "shared_event"):
        print("OK: ASP confirms a safe shared hammock event.")
        return 0
    print("MISMATCH: ASP did not confirm the safe shared hammock event.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.feature != "sharing":
        raise StoryError("The story requires the Sharing feature.")
    if params.object != "hammock":
        raise StoryError("The story requires a hammock.")
    if params.case not in CASES:
        raise StoryError("Unknown mystery case.")
    seed = params.seed if params.seed is not None else sum(ord(c) for c in params.name + params.case)
    world = tell(params, random.Random(seed ^ 0x51A7))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("palm_grove", "sharing", "hammock", "Luna", "lemur", "curious", "missing_shell", "clue_first", 101),
    StoryParams("moonlit_cove", "sharing", "hammock", "Milo", "monkey", "careful", "cut_rope", "question_turn", 202),
    StoryParams("garden_patio", "sharing", "hammock", "Tia", "toucan", "patient", "hidden_note", "friend_view", 303),
    StoryParams("palm_grove", "sharing", "hammock", "Pip", "parrot", "brave", "vanished_lantern", "action_turn", 404),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", ", ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 30):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
