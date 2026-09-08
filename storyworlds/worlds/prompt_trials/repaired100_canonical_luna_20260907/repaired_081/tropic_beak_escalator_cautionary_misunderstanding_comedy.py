#!/usr/bin/env python3
"""
Story world: a comic escalator adventure about a tropic bird, a beak, and a
cautionary misunderstanding.

A child sees a colorful tropic bird near an escalator and misunderstands its
pointed beak as a signal to hurry. A helper notices the real clue, and the
child learns to pause, ask, and use the escalator safely.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Escalator:
    name: str
    place: str
    direction: str
    speed: str
    safety_rule: str


@dataclass
class StoryParams:
    escalator: str = "Palm Plaza escalator"
    hero_name: str = "Luna"
    helper_name: str = "Mika"
    bird_name: str = "Pico"
    incident: str = "beak_signal"
    telling_mode: str = "comedy"
    seed: Optional[int] = None


class World:
    def __init__(self, escalator: Escalator) -> None:
        self.escalator = escalator
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)


ESCALATOR_REGISTRY = {
    "Palm Plaza escalator": Escalator(
        name="Palm Plaza escalator",
        place="the bright shopping plaza",
        direction="up",
        speed="gentle",
        safety_rule="hold the handrail and keep clear of the edges",
    ),
    "Rainforest Gate escalator": Escalator(
        name="Rainforest Gate escalator",
        place="the tropical museum entrance",
        direction="down",
        speed="steady",
        safety_rule="stand still, face forward, and hold the rail",
    ),
    "Coral Market escalator": Escalator(
        name="Coral Market escalator",
        place="the busy coral market",
        direction="up",
        speed="slow",
        safety_rule="wait behind the yellow line and keep bags close",
    ),
}

HERO_NAMES = ["Luna", "Tavi", "Nia", "Bo", "Remy"]
HELPER_NAMES = ["Mika", "Zuri", "Pax", "Kiko", "Ari"]
BIRD_NAMES = ["Pico", "Sunny", "Beakley", "Mango", "Tiki"]

INCIDENTS = {
    "beak_signal": {
        "premise": "A bright tropic bird perched beside the escalator and pointed its long beak toward the moving steps.",
        "misunderstanding": "{hero} thought the bird was giving a hurry-up signal and lifted one foot before the next step arrived.",
        "clue": "{helper} noticed that the bird pointed at a fallen fruit sticker caught near the escalator entrance, not at the steps.",
        "change": "They stepped back, told a plaza worker, and waited until the entrance was clear before riding.",
        "result": "The worker removed the sticker, and the bird relaxed its beak while everyone boarded safely.",
        "lesson": "a strange signal should be checked before it becomes an action",
        "ending": "At the top, the tropic bird bowed so deeply that its beak nearly tickled its own toes.",
    },
    "fruit_confetti": {
        "premise": "A tropic bird shook a paper palm, sending fruit-shaped confetti around the escalator landing.",
        "misunderstanding": "{hero} mistook the confetti for a warning and tried to ride the escalator backward to escape it.",
        "clue": "{helper} saw that the paper pieces came from a celebration booth and that the escalator itself was moving normally.",
        "change": "They stepped off at the landing, moved away from the confetti, and asked the booth keeper to gather it.",
        "result": "The path stayed clear, and the bird stopped flapping whenever a paper fruit drifted near the rail.",
        "lesson": "look for the source of a surprise before choosing a response",
        "ending": "One paper banana landed on {hero}'s head like a tiny tropical crown.",
    },
    "shadow_beak": {
        "premise": "The escalator lights made the bird's beak cast a giant shadow across the steps.",
        "misunderstanding": "{hero} believed a giant shadow-beak was chasing the riders and announced an emergency in a very small voice.",
        "clue": "{helper} waved near the bird and watched the huge shadow wave too.",
        "change": "They paused at the safe waiting line, tested the light with their hands, and explained the shadow to nearby riders.",
        "result": "The riders laughed, the bird chirped, and everyone used the escalator without rushing.",
        "lesson": "a frightening picture can be caused by an ordinary object and light",
        "ending": "The shadow-beak shrank when the lights changed, but {hero}'s serious announcement stayed enormous.",
    },
    "wrong_direction": {
        "premise": "The tropic bird flew toward a down escalator while a sign above it showed an arrow pointing up.",
        "misunderstanding": "{hero} assumed the bird was the official escalator guide and marched toward the wrong side.",
        "clue": "{helper} read the sign aloud and saw the bird was chasing a feather blown by the air.",
        "change": "They let the feather settle, checked the arrow, and chose the correct escalator entrance.",
        "result": "The bird caught its feather without blocking anyone, and the children followed the clear sign.",
        "lesson": "someone moving with confidence may still be following a different goal",
        "ending": "The bird carried its feather upward while {hero} saluted the sign.",
    },
    "beak_bump": {
        "premise": "The curious tropic bird tapped its beak against the escalator handrail with a cheerful clack.",
        "misunderstanding": "{hero} thought the clacking meant the handrail was broken and tried to stop the whole escalator by shouting, “Freeze!”",
        "clue": "{helper} saw that the bird tapped only when the rail moved past its perch, making a silly rhythm.",
        "change": "They moved behind the safety line and asked a worker to check the rail instead of touching it themselves.",
        "result": "The worker found the rail was fine, and the children learned that the bird had invented a one-beak song.",
        "lesson": "tell an adult about a possible danger without trying to fix machinery yourself",
        "ending": "The bird played its clack song, and {hero} conducted with two careful fingers from far away.",
    },
}

TELLING_MODES = ["comedy", "dialogue opening", "mystery opening", "problem first"]

ASP_RULES = r"""
escalator(E) :- escalator_name(E).
bird(B) :- bird_name(B).
safe_wait(H) :- person(H), waits_behind_line(H).
understood(H) :- person(H), checks_clue(H).
lesson_learned(H) :- person(H), learned(H).
comic_misunderstanding(H) :- person(H), misunderstands(H).
resolved(E) :- escalator(E), path_clear(E), safe_wait(hero).
"""

def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp

    p = params or StoryParams()
    lines = [
        asp.fact("escalator_name", p.escalator),
        asp.fact("bird_name", p.bird_name),
        asp.fact("person", "hero"),
        asp.fact("person", "helper"),
        asp.fact("waits_behind_line", "hero"),
        asp.fact("checks_clue", "helper"),
        asp.fact("learned", "hero"),
        asp.fact("misunderstands", "hero"),
        asp.fact("path_clear", p.escalator),
    ]
    return "\n".join(lines)


def asp_program(params: Optional[StoryParams] = None, show: str = "") -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    params = StoryParams()
    model = asp.one_model(
        asp_program(
            params,
            "#show resolved/1.\n#show lesson_learned/1.\n#show comic_misunderstanding/1.",
        )
    )
    found = set()
    for symbol in model:
        if symbol.name in {"resolved", "lesson_learned", "comic_misunderstanding"}:
            args = tuple(
                a.string
                if a.type == a.type.String
                else a.number
                if a.type == a.type.Number
                else a.name
                for a in symbol.arguments
            )
            found.add((symbol.name, args))
    wanted = {
        ("resolved", ("Palm Plaza escalator",)),
        ("lesson_learned", ("hero",)),
        ("comic_misunderstanding", ("hero",)),
    }
    if found == wanted:
        sample = generate(params)
        if "escalator" not in sample.story.lower() or "beak" not in sample.story.lower():
            print("MISMATCH: generated story lost required domain terms.")
            return 1
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(found))
    print("PY :", sorted(wanted))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A comic cautionary story about a tropic bird and an escalator misunderstanding."
    )
    parser.add_argument("--escalator", choices=sorted(ESCALATOR_REGISTRY))
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--bird")
    parser.add_argument("--incident", choices=sorted(INCIDENTS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    escalator = args.escalator or rng.choice(list(ESCALATOR_REGISTRY))
    hero = args.name or rng.choice(HERO_NAMES)
    helper_choices = [name for name in HELPER_NAMES if name != hero]
    helper = args.helper or rng.choice(helper_choices)
    bird = args.bird or rng.choice(BIRD_NAMES)
    if hero == helper:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(
        escalator=escalator,
        hero_name=hero,
        helper_name=helper,
        bird_name=bird,
        incident=args.incident or rng.choice(list(INCIDENTS)),
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    if params.escalator not in ESCALATOR_REGISTRY:
        raise StoryError(f"Unknown escalator: {params.escalator}")
    if params.incident not in INCIDENTS:
        raise StoryError(f"Unknown incident: {params.incident}")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must be different characters.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.escalator}:{params.hero_name}:{params.helper_name}:{params.bird_name}:{params.incident}"
    )
    escalator = ESCALATOR_REGISTRY[params.escalator]
    incident = INCIDENTS[params.incident]
    world = World(escalator)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero_name,
            phrase=f"{params.hero_name}, a curious child",
            meters={"balance": 1.0, "distance_from_edge": 0.2},
            memes={"curiosity": 1.0, "worry": 0.0, "confidence": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper_name,
            phrase=f"{params.helper_name}, a careful friend",
            meters={"balance": 1.0, "distance_from_edge": 0.5},
            memes={"attention": 1.0, "worry": 0.0, "confidence": 1.0},
        )
    )
    bird = world.add(
        Entity(
            id="bird",
            kind="animal",
            label=params.bird_name,
            phrase=rng.choice(
                [
                    "a brilliant tropic bird with a banana-yellow beak",
                    "a red-and-green tropic bird with a wonderfully pointy beak",
                    "a tiny tropic bird whose enormous beak looked like a painted canoe",
                ]
            ),
            meters={"perch": 1.0, "beak_pointing": 1.0, "distance_from_edge": 0.7},
            memes={"curiosity": 1.0, "mischief": 1.0, "calm": 0.0},
        )
    )

    openings = {
        "comedy": f"At {escalator.place}, {params.hero_name} met {bird.phrase} beside the {escalator.name}.",
        "dialogue opening": f'“That beak is pointing at me!” {params.hero_name} cried beside the {escalator.name}.',
        "mystery opening": f"Nobody could explain why {bird.label} kept pointing its beak at the {escalator.name}.",
        "problem first": incident["premise"].format(hero=params.hero_name, helper=params.helper_name),
    }
    world.say(openings[params.telling_mode])
    world.say(
        rng.choice(
            [
                "The escalator hummed, the palm leaves swayed, and the bird looked as serious as a tiny airport manager.",
                "It was a perfectly ordinary escalator, except for the bird, the beak, and the very unordinary expression on {hero}'s face.".format(hero=params.hero_name),
                "The whole scene had the ingredients of a comedy: moving steps, bright feathers, and one child ready to guess too quickly.",
            ]
        )
    )
    if params.telling_mode != "problem first":
        world.say(incident["premise"].format(hero=params.hero_name, helper=params.helper_name))

    hero.memes["worry"] += 1.0
    hero.meters["distance_from_edge"] = 0.1
    world.say(incident["misunderstanding"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f'“Wait,” {params.helper_name} said. “Is the beak telling us about the escalator, or is it pointing at something else?”'
    )
    world.say(
        f'“It looks very official,” {params.hero_name} replied. “It has a beak-shaped pointer!”'
    )
    world.say(incident["clue"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"{params.helper_name} pointed to the yellow waiting line. “We can check the clue without stepping onto the escalator yet.”"
    )
    helper.memes["worry"] = 0.0
    hero.memes["worry"] = 0.2
    hero.meters["distance_from_edge"] = 0.8
    world.say(incident["change"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(
        f"{params.hero_name} followed the safety rule: {escalator.safety_rule}. The beak was still pointed, but nobody hurried."
    )
    world.say(incident["result"].format(hero=params.hero_name, helper=params.helper_name))
    hero.memes["confidence"] = 1.0
    hero.memes["lesson"] = 1.0
    bird.memes["calm"] = 1.0
    world.say(
        f"{params.hero_name} learned the cautionary lesson: {incident['lesson']}."
    )
    world.say(
        f'“Next time,” {params.hero_name} said, “I will ask what the beak means before I make my feet do anything funny.”'
    )
    world.say(
        f'“That is a wise plan,” {params.helper_name} said. “Your feet are already funny enough on a moving escalator.”'
    )
    world.say(incident["ending"].format(hero=params.hero_name, helper=params.helper_name))

    world.facts.update(
        hero=hero,
        helper=helper,
        bird=bird,
        escalator=escalator,
        transformed=True,
        safe=True,
        misunderstanding=True,
        clue=incident["clue"].format(hero=params.hero_name, helper=params.helper_name),
        lesson=incident["lesson"],
        resolution=incident["result"].format(hero=params.hero_name, helper=params.helper_name),
    )

    prompts = [
        f"Write a child-friendly Comedy story about {params.hero_name}, a tropic bird, and a beak beside an escalator.",
        f"Include a Cautionary Misunderstanding in which {params.hero_name} checks a strange signal before acting.",
        f"Show how {params.helper_name} uses a clue to make the escalator situation safe and funny.",
    ]
    story_qa = [
        QAItem(
            question="What happened at the escalator?",
            answer=incident["premise"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question=f"What did {params.hero_name} misunderstand?",
            answer=incident["misunderstanding"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question="What clue revealed the truth?",
            answer=incident["clue"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question="How was the situation made safe?",
            answer=incident["change"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question="What cautionary lesson did the child learn?",
            answer=f"{params.hero_name} learned that {incident['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is an escalator?",
            answer="An escalator is a set of moving steps that carries people between different levels of a building.",
        ),
        QAItem(
            question="Why should people hold an escalator handrail?",
            answer="People should hold the handrail to help keep their balance while the steps move.",
        ),
        QAItem(
            question="Why can a beak be misleading?",
            answer="A bird's beak may point toward food, a feather, or another object, so people should not assume it is giving them instructions.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone interprets a word, sign, or action incorrectly.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


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
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(
                f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        params = StoryParams(escalator=args.escalator or "Palm Plaza escalator")
        print(
            asp_program(
                params,
                "#show resolved/1.\n#show lesson_learned/1.\n#show comic_misunderstanding/1.",
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        params = StoryParams(escalator=args.escalator or "Palm Plaza escalator")
        model = asp.one_model(
            asp_program(
                params,
                "#show resolved/1.\n#show lesson_learned/1.\n#show comic_misunderstanding/1.",
            )
        )
        print("ASP model:")
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, incident in enumerate(INCIDENTS):
            params = StoryParams(
                escalator=list(ESCALATOR_REGISTRY)[index % len(ESCALATOR_REGISTRY)],
                hero_name=HERO_NAMES[index % len(HERO_NAMES)],
                helper_name=HELPER_NAMES[index % len(HELPER_NAMES)],
                bird_name=BIRD_NAMES[index % len(BIRD_NAMES)],
                incident=incident,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(0, args.n) and attempt < max(50, args.n * 30):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

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
    main()
