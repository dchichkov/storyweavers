#!/usr/bin/env python3
"""A child-friendly living-room animal adventure about persuading a friend safely."""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = "living_room"


@dataclass(frozen=True)
class Challenge:
    key: str
    object_name: str
    problem: str
    tempting_plan: str
    reason_not_to: str
    questions: str
    safe_plan: str
    discovery: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    companion: str = "Pip"
    adult: str = "Grandma"
    challenge: str = "high_shelf"
    mood: str = "rainy"
    opening_mode: int = 0
    dialogue_mode: int = 0
    turn_mode: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CHALLENGES = {
    "high_shelf": Challenge(
        "high_shelf",
        "red adventure map",
        "the red adventure map slid behind a tall bookcase",
        "climb the bookcase or pull it away",
        "the bookcase could wobble and hurt someone, and the map might tear",
        "ask what could reach the map without making the furniture move",
        "ask Grandma to use a long-handled grabber while the animals wait on the rug",
        "a careful tug brings the map out from behind the bookcase",
        "they spread the map on the rug and planned a safe journey through its painted hills",
        "A good adventure needs brave ideas and a safe way to try them.",
    ),
    "under_sofa": Challenge(
        "under_sofa",
        "blue explorer badge",
        "the blue explorer badge rolled under the sofa",
        "send Pip underneath or poke it with a broom",
        "Pip could get stuck, and the broom might scratch the floor or push the badge farther",
        "ask how they could see and reach the badge while keeping paws and tools safe",
        "ask Grandma to shine a flashlight and slide a soft cardboard tube from the open side",
        "the badge rolls into the light and stops beside Luna's paw",
        "Pip wears the badge only after Grandma checks that its pin is closed",
        "Persuading a friend means offering a safer plan, not merely insisting.",
    ),
    "curtain_loop": Challenge(
        "curtain_loop",
        "green explorer scarf",
        "the green explorer scarf caught on a curtain loop",
        "jump and yank the curtain",
        "the loop might snap, and the curtain rod could fall",
        "ask which action would loosen the scarf without pulling the curtain",
        "ask Grandma to lower the curtain tie and free the scarf with both hands",
        "the scarf slips loose when the loop is gently opened",
        "the animals make a tiny bridge from cushions and wear the scarf only on the floor",
        "Stopping to inspect a problem can reveal a gentle solution.",
    ),
    "lamp_shadow": Challenge(
        "lamp_shadow",
        "paper cave picture",
        "a shadow made the paper cave picture look as if it had vanished",
        "move the lamp quickly or knock the papers together",
        "the lamp is hot and the papers could scatter",
        "ask what changed between the picture and the shadow",
        "persuade Pip to hold still while Grandma switches off the lamp and checks the table",
        "the picture is found safely beneath a clear folder",
        "they make animal shadows on the wall with the lamp kept on its stable table",
        "A strange appearance deserves calm questions before a hurried action.",
    ),
}


OPENINGS = (
    "Rain tapped the living-room window, and Luna announced that an adventure should begin indoors.",
    "The living room became a jungle, a mountain, and a sea when Luna found an old explorer kit.",
    "On a quiet afternoon, Luna and Pip discovered that one small object could start a very big adventure.",
    "The cushions were islands and the rug was a wide meadow until the explorer plan met a problem.",
)

DIALOGUES = (
    '"Let us solve it without making the living room less safe," Luna said.',
    '"I can persuade you with a plan, not a push," Luna told Pip.',
    '"Before we leap, what might happen next?" Luna asked.',
    '"A real explorer notices danger and chooses carefully," Luna said.',
)

TURNS = (
    "Pip stopped bouncing and looked at the problem from the rug.",
    "That question changed the adventure: they needed a method, not just more courage.",
    "Pip listened, and the first exciting idea became a safer experiment.",
    "The living room grew quiet enough for the useful clue to appear.",
)


ASP_RULES = r"""
item(X) :- item_fact(X).
challenge(C) :- challenge_fact(C).
safe_plan(C) :- challenge_fact(C), supervised(C).
persuasion(C) :- challenge_fact(C), asks_questions(C).
resolved(C) :- safe_plan(C), persuasion(C).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("item_fact", challenge.object_name.replace(" ", "_")) for challenge in CHALLENGES.values()]
    lines += [asp.fact("challenge_fact", key) for key in CHALLENGES]
    lines += [asp.fact("supervised", key) for key in CHALLENGES]
    lines += [asp.fact("asks_questions", key) for key in CHALLENGES]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal adventure and problem solving in a living room.")
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--adult")
    parser.add_argument("--challenge", choices=sorted(CHALLENGES))
    parser.add_argument("--mood")
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
    heroes = ["Luna", "Milo", "Bramble", "Nia"]
    companions = ["Pip", "Toby", "Clover", "Moss"]
    adults = ["Grandma", "Aunt May", "Uncle Jo", "Dad"]
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(heroes),
        companion=args.companion or rng.choice(companions),
        adult=args.adult or rng.choice(adults),
        challenge=args.challenge or rng.choice(list(CHALLENGES)),
        mood=args.mood or rng.choice(["rainy", "bright", "cloudy", "windy"]),
        opening_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        turn_mode=rng.randrange(len(TURNS)),
    )


def tell(params: StoryParams) -> World:
    if params.challenge not in CHALLENGES:
        raise StoryError(f"Unknown challenge: {params.challenge}")
    challenge = CHALLENGES[params.challenge]
    world = World()
    hero = world.add(Entity(params.hero, "animal", params.hero, {"height": 0.35}, {"curiosity": 2.0, "patience": 1.0}))
    companion = world.add(Entity(params.companion, "animal", params.companion, {"height": 0.28}, {"excitement": 2.0, "trust": 1.0}))
    adult = world.add(Entity(params.adult, "person", params.adult, {"reach": 1.7}, {"care": 2.0}))
    world.facts.update(hero=hero, companion=companion, adult=adult, challenge=challenge, resolved=False)

    world.say(OPENINGS[params.opening_mode])
    world.say(f"On a {params.mood} afternoon, {hero.label} and {companion.label} turned the rug into an expedition trail, while {adult.label} watched from the nearby chair.")
    world.say(f"Then they noticed that {challenge.problem}. The adventure stopped at once.")
    world.para()
    world.say(f'{companion.label} whispered, "I know what to do: {challenge.tempting_plan}."')
    world.say(DIALOGUES[params.dialogue_mode])
    world.say(f"{hero.label} explained, \"{challenge.reason_not_to.capitalize()}.\"")
    world.say(f'"What should we ask first?" {companion.label} said.')
    world.say(f"{hero.label} answered, \"{challenge.questions.capitalize()}.\"")
    world.say(TURNS[params.turn_mode])
    world.say(f'{adult.label} nodded. "That is a sensible question. We can {challenge.safe_plan}.\"')
    world.say(f"{companion.label} agreed, and the problem-solving plan began.")
    world.para()
    world.say(f"Together they discovered that {challenge.discovery}.")
    world.say(f'"You persuaded me with reasons," {companion.label} said. "I wanted an exciting shortcut, but your plan kept our adventure going."')
    world.say(f"{challenge.ending}.")
    world.say(challenge.lesson)
    world.say(f"The living room felt ready for another adventure, because {hero.label} and {companion.label} had learned how to be bold and careful at the same time.")

    hero.memes["confidence"] = 2.0
    companion.memes["trust"] = 2.0
    world.facts["resolved"] = True
    world.trace.extend([
        f"location:living_room",
        f"challenge:{challenge.key}",
        f"tempting_plan:{challenge.tempting_plan}",
        f"safe_plan:{challenge.safe_plan}",
        f"discovery:{challenge.discovery}",
        "persuasion:successful",
        "supervision:adult_present",
    ])
    return world


def generation_prompts(world: World) -> list[str]:
    challenge: Challenge = world.facts["challenge"]
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    return [
        f"Write an animal adventure in a living room starring {hero.label} and {companion.label}.",
        f"Include problem solving when {challenge.problem}.",
        f"Let {hero.label} persuade {companion.label} to choose this safe plan: {challenge.safe_plan}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    challenge: Challenge = world.facts["challenge"]
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    adult: Entity = world.facts["adult"]
    return [
        QAItem(
            f"What problem interrupted {hero.label} and {companion.label}'s adventure?",
            f"The adventure was interrupted because {challenge.problem}.",
        ),
        QAItem(
            f"What unsafe idea did {companion.label} suggest?",
            f"{companion.label} suggested that they should {challenge.tempting_plan}.",
        ),
        QAItem(
            f"How did {hero.label} persuade {companion.label}?",
            f"{hero.label} explained that {challenge.reason_not_to}, then asked {challenge.questions}.",
        ),
        QAItem(
            "What safe plan did the animals choose?",
            f"They chose to {challenge.safe_plan}.",
        ),
        QAItem(
            "How was the problem solved?",
            f"They discovered that {challenge.discovery}.",
        ),
        QAItem(
            "What did the friends learn?",
            answer=challenge.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should children ask an adult before moving furniture or using a tool?",
            "Furniture can wobble and tools can cause harm. An adult can check the danger and choose a safe method.",
        ),
        QAItem(
            "What is persuasion?",
            "Persuasion is giving clear reasons and listening so another person can make a thoughtful choice.",
        ),
        QAItem(
            "How does problem solving begin?",
            "It begins by noticing the problem, asking useful questions, considering consequences, and choosing a safe test.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.extend(f"  {item}" for item in world.trace)
    for entity in world.entities.values():
        lines.append(f"  {entity.label} ({entity.kind}) meters={entity.meters} memes={entity.memes}")
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(challenge="high_shelf"),
    StoryParams(
        hero="Milo",
        companion="Clover",
        adult="Aunt May",
        challenge="under_sofa",
        mood="bright",
        opening_mode=2,
        dialogue_mode=1,
        turn_mode=3,
    ),
    StoryParams(
        hero="Bramble",
        companion="Moss",
        adult="Uncle Jo",
        challenge="curtain_loop",
        mood="windy",
        opening_mode=3,
        dialogue_mode=2,
        turn_mode=1,
    ),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    show = "#show item/1.\n#show challenge/1.\n#show safe_plan/1.\n#show persuasion/1.\n#show resolved/1.\n"
    model = asp.one_model(asp_program(show))
    if not model:
        print("ASP produced no model.")
        return 1
    expected = {"high_shelf", "under_sofa", "curtain_loop", "lamp_shadow"}
    found = {args[0] for args in asp.atoms(model, "challenge")}
    if found != expected:
        print(f"ASP challenge parity failed: {found}")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print("OK: ASP and generated-story verification passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    show = "#show item/1.\n#show challenge/1.\n#show safe_plan/1.\n#show persuasion/1.\n#show resolved/1.\n"
    if args.show_asp:
        print(asp_program(show))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for offset in range(args.n):
            params = resolve_params(args, random.Random(base_seed + offset))
            params.seed = base_seed + offset
            samples.append(generate(params))

    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program(show))
            print(json.dumps({"asp_atoms": [str(atom) for atom in model]}, indent=2))
        except Exception as exc:
            raise StoryError(f"ASP mode failed: {exc}") from exc
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        raise SystemExit(2)
