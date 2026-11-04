#!/usr/bin/env python3
"""
A tall-tale storyworld about a pail, a peculiar little spic, and a quest
that gets larger every time someone tells it.

Spic is the name of a tiny brass bird who points toward whatever is missing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, STORYWORLDS_ROOT)
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
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


QUESTS = {
    "moonwater": {
        "name": "the Moonwater Quest",
        "missing": "the moon's last silver drop",
        "clue": "Spic's beak pointed straight down into the empty pail",
        "method": "they lowered the pail into the well and listened for the echo",
        "result": "the pail came up full of moonlit water",
        "ending": "That night, the moon winked in the pail while the town's flowers drank.",
    },
    "thunder": {
        "name": "the Thunder Quest",
        "missing": "a thunderclap for the town's sleepy bell",
        "clue": "Spic pecked at the pail whenever a cloud rumbled overhead",
        "method": "they held the pail beneath a storm cloud and waited for a rumble",
        "result": "one cheerful thunderclap boomed into the pail",
        "ending": "The bell rang at last, and even the clouds seemed to chuckle.",
    },
    "giant_button": {
        "name": "the Giant Button Quest",
        "missing": "the giant's runaway coat button",
        "clue": "Spic kept pointing toward a round hill that had one shiny spot",
        "method": "they rolled the pail up the hill and asked the giant to check his coat",
        "result": "the button popped into the pail with a sound like a drum",
        "ending": "The giant waved in his mended coat, and the pail wore the button as a hat.",
    },
}

HUMOR = {
    "teapot": "a very serious teapot",
    "goose": "a goose who honked whenever anyone said 'quest'",
    "socks": "two enormous socks, though nobody could remember packing them",
}

NAMES = ("Mira", "Tavi", "Lumi", "Bram", "Niko")
TRAITS = ("bold", "patient", "curious", "cheerfully stubborn")
VALID_COMBOS = [(q, h) for q in QUESTS for h in HUMOR]


@dataclass
class StoryParams:
    quest: str
    humor: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A funny tall-tale quest featuring Spic and a pail."
    )
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--humor", choices=HUMOR)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--trait", choices=TRAITS)
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
    return StoryParams(
        quest=args.quest or rng.choice(tuple(QUESTS)),
        humor=args.humor or rng.choice(tuple(HUMOR)),
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {params.quest!r}.")
    if params.humor not in HUMOR:
        raise StoryError(f"Unknown humor companion: {params.humor!r}.")
    if params.name not in NAMES:
        raise StoryError(f"Choose a quester from: {', '.join(NAMES)}.")
    if params.trait not in TRAITS:
        raise StoryError(f"Choose a trait from: {', '.join(TRAITS)}.")


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    quest = QUESTS[params.quest]
    joke = HUMOR[params.humor]

    world = World()
    hero = world.add(Entity(params.name, "character", "child", params.name))
    spic = world.add(Entity("Spic", "character", "brass bird", "Spic"))
    pail = world.add(Entity("Pail", "thing", "pail", "the pail"))
    companion = world.add(Entity("Companion", "character", "comic companion", joke))

    hero.memes.update({"courage": 1.0, "worry": 1.0})
    spic.meters["needle_wobble"] = 1.0
    pail.meters["fullness"] = 0.0

    openings = [
        f"In a town so small that its mayor could shout across it without standing up, {params.name} began {quest['name']}.",
        f"Long ago, {params.name} set out on {quest['name']}, carrying an empty pail and enough courage to fill it twice.",
        f"The mountains were tall, the road was long, and {params.name}'s pail was so empty it echoed at passing thoughts.",
    ]
    world.say(openings[(params.seed or 0) % len(openings)])
    world.say(
        f"At {params.name}'s shoulder rode Spic, a tiny brass bird whose beak pointed toward whatever was missing. "
        f"Today, it pointed toward {quest['missing']}."
    )
    world.say(
        f"Along came {joke}, who joined the quest after mistaking the pail for a very small parade float."
    )
    world.para()

    world.say(
        f"The road crossed seven hills, each taller than the last because the story grew as they walked. "
        f"At the top of the seventh, the pail gave a hollow bonk."
    )
    world.say(f"{params.name} frowned. “How can an empty pail help us find {quest['missing']}?”")
    world.say(f"Spic chirped, “It can help us listen. And it can carry what we find.”")
    world.say(
        f"That changed {params.name}'s plan: instead of rushing ahead, the questers watched where Spic pointed."
    )
    world.say(f"The clue was plain once they looked: {quest['clue']}.")
    world.say(
        f"“I thought we needed a bigger plan,” said {params.name}. “Maybe we need a better look,” replied {joke}."
    )

    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    spic.meters["clue_found"] = 1.0
    world.para()

    world.say(
        f"Together, the three questers tried a careful plan: {quest['method']}. "
        f"The pail shook so hard that {joke} saluted it."
    )
    pail.meters["fullness"] = 1.0
    hero.meters["quest_complete"] = 1.0
    spic.meters["guidance_used"] = 1.0
    world.say(f"At once, {quest['result']}.")
    world.say(
        f"They had not conquered the world; they had paid attention to it, and that was enough."
    )
    world.para()

    world.say(
        f"On the way home, {params.name} thanked Spic for pointing out the clue and thanked {joke} for staying through the hard part."
    )
    world.say(
        f"“Next time,” said {params.name}, “we bring a pail with a lid.” "
        f"“Next time,” said {joke}, “I bring a smaller hat.”"
    )
    world.say(quest["ending"])

    world.facts.update(
        hero=hero,
        spic=spic,
        pail=pail,
        companion=companion,
        quest=quest,
        joke=joke,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly tall tale about {f['hero'].label}, Spic, a pail, and {f['quest']['name']}.",
        f"Tell a funny quest story where a clue changes {f['hero'].label}'s plan.",
        f"Write a complete tall tale that includes {f['joke']} and ends with a changed image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    quest = f["quest"]
    return [
        QAItem(
            question=f"What was {hero} trying to find?",
            answer=f"{hero} was trying to find {quest['missing']} on the quest.",
        ),
        QAItem(
            question="Who was Spic?",
            answer="Spic was a tiny brass bird whose beak pointed toward whatever was missing.",
        ),
        QAItem(
            question="What clue changed the questers' plan?",
            answer=f"They noticed that {quest['clue']}, so they stopped rushing and followed the clue.",
        ),
        QAItem(
            question="How did the pail help?",
            answer=f"The questers used the pail as part of their careful plan: {quest['method']}.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"The plan worked: {quest['result']}. {quest['ending']}",
        ),
    ]


def world_knowledge_qa() -> list[QAItem]:
    return [
        QAItem(
            question="What is a pail used for?",
            answer="A pail is a container that can carry things such as water, sand, or tools.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal, often involving challenges and discoveries along the way.",
        ),
        QAItem(
            question="Why can a clue be useful?",
            answer="A clue gives information that can help someone understand a problem and choose what to do next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== Story QA =="])
    for qa in sample.story_qa:
        lines.extend([f"Q: {qa.question}", f"A: {qa.answer}"])
    lines.extend(["", "== World QA =="])
    for qa in sample.world_qa:
        lines.extend([f"Q: {qa.question}", f"A: {qa.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: {entity.type}; meters={entity.meters}; memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(Q,H) :- quest(Q), humor(H).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    facts = []
    for quest, humor in VALID_COMBOS:
        facts.extend([asp.fact("quest", quest), asp.fact("humor", humor)])
    return "\n".join(facts)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        python_combos = set(VALID_COMBOS)
        answer_sets = __import__("asp").solve(asp_program(), models=0)
        asp_combos = {
            combo
            for model in answer_sets
            for combo in __import__("asp").atoms(model, "valid")
        }
        if python_combos != asp_combos:
            print(f"MISMATCH: Python={sorted(python_combos)} ASP={sorted(asp_combos)}")
            return 1
        for i, (quest, humor) in enumerate(VALID_COMBOS):
            params = StoryParams(quest, humor, NAMES[i % len(NAMES)], TRAITS[i % len(TRAITS)])
            sample = generate(params)
            if not sample.story.strip() or not sample.story.endswith("."):
                print(f"FAILED story exercise for {quest}/{humor}")
                return 1
            if "Spic" not in sample.story or "pail" not in sample.story.lower():
                print(f"FAILED required-story detail for {quest}/{humor}")
                return 1
    except ImportError as exc:
        print(f"ASP verification requires clingo: {exc}")
        return 1
    print(f"OK: ASP matches Python ({len(VALID_COMBOS)} combinations); stories exercised.")
    return 0


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


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1 and not args.all and not args.verify and not args.asp and not args.show_asp:
        raise SystemExit("-n must be at least 1.")

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for i, (quest, humor) in enumerate(VALID_COMBOS):
            samples.append(
                generate(
                    StoryParams(
                        quest,
                        humor,
                        NAMES[i % len(NAMES)],
                        TRAITS[i % len(TRAITS)],
                        base_seed + i,
                    )
                )
            )
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 30, 30)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) >= args.n:
                break

    if args.json:
        payload = samples[0].to_json() if len(samples) == 1 else json.dumps(
            [sample.to_dict() for sample in samples], indent=2, ensure_ascii=False
        )
        print(payload)
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.quest} / {sample.params.humor}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
