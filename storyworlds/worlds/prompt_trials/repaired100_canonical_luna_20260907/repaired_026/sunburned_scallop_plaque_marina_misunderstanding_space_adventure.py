#!/usr/bin/env python3
"""
A small Space Adventure storyworld about a sunburned scallop, a missing plaque,
and a misunderstanding at a marina.
"""

from __future__ import annotations

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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Orbit"
    captain: str = "Captain Vega"
    place: str = "the marina"
    vessel: str = "the little star-skiff"


HERO_NAMES = ["Luna", "Nova", "Mira", "Tess", "Ari"]
HELPER_NAMES = ["Orbit", "Pip", "Comet", "Sol", "Echo"]
CAPTAIN_NAMES = ["Captain Vega", "Captain Noor", "Captain Halley", "Captain Mira"]
VESSELS = ["the little star-skiff", "the moonboat", "the comet tender", "the silver launch"]

SCENES = [
    {
        "title": "the red shell signal",
        "sun": "The noon sun had painted a hot red patch across the scallop's shell.",
        "plaque": "a brass plaque engraved with a tiny rocket",
        "clue": "three bright scratches beside Dock Seven",
        "solution": "the plaque belonged to the old rescue boat, not to the scallop",
        "ending": "the plaque shone again beneath the rescue boat's name while the scallop rested in cool seawater",
    },
    {
        "title": "the drifting welcome plate",
        "sun": "The scallop had been sunburned after floating too long beside the warm outer dock.",
        "plaque": "a silver welcome plaque with a picture of a star",
        "clue": "a trail of bubbles leading toward the harbor office",
        "solution": "the plaque had slipped from the marina's welcome buoy during a tide change",
        "ending": "the repaired welcome plaque greeted every returning boat as the scallop sheltered under a striped awning",
    },
    {
        "title": "the moon-marked pier",
        "sun": "A fierce beam of sunlight had left the scallop sunburned and tender.",
        "plaque": "a round plaque marked with a crescent moon",
        "clue": "a ribbon caught on a cleat near the launch ramp",
        "solution": "the plaque was a keepsake from the marina's night-sailing club",
        "ending": "the moon plaque hung above the club doorway while the scallop cooled in a shaded tide pool",
    },
    {
        "title": "the captain's lost label",
        "sun": "The scallop's shell looked sunburned after a bright morning on the floating pier.",
        "plaque": "a painted plaque naming a visiting research boat",
        "clue": "blue paint flecks on the deck of a nearby boat",
        "solution": "the plaque had blown loose from the research boat in a gust",
        "ending": "the research boat carried its plaque safely again, and the scallop wore a damp seaweed shade",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Space Adventure storyworld about a sunburned scallop and a marina misunderstanding."
    )
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--captain")
    parser.add_argument("--place")
    parser.add_argument("--vessel")
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
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in HELPER_NAMES if n != hero])
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    place = getattr(args, "place", None) or "the marina"
    vessel = getattr(args, "vessel", None) or rng.choice(VESSELS)

    if not place.strip():
        raise StoryError("place must not be empty")
    if hero == helper:
        raise StoryError("hero and helper must have different names")

    return StoryParams(
        seed=getattr(args, "seed", None),
        hero=hero,
        helper=helper,
        captain=captain,
        place=place,
        vessel=vessel,
    )


def make_world(params: StoryParams) -> World:
    world = World(params.place)
    world.add(Entity(
        "hero",
        "child astronaut",
        params.hero,
        meters={"heat": 0.8, "air": 1.0, "distance": 0.0},
        memes={"curiosity": 0.9, "worry": 0.3, "courage": 0.7},
    ))
    world.add(Entity(
        "helper",
        "robot helper",
        params.helper,
        meters={"battery": 0.9, "distance": 0.0},
        memes={"certainty": 0.5, "loyalty": 0.8},
    ))
    world.add(Entity(
        "captain",
        "marina captain",
        params.captain,
        meters={"distance": 1.0},
        memes={"trust": 0.5, "calm": 0.8},
    ))
    world.add(Entity(
        "scallop",
        "scallop",
        "the scallop",
        meters={"sunburn": 0.9, "water": 0.2, "safety": 0.4},
        memes={"fear": 0.6, "relief": 0.0},
    ))
    world.add(Entity(
        "plaque",
        "plaque",
        "the plaque",
        meters={"shine": 0.8, "distance": 1.0, "safety": 0.5},
        memes={"importance": 0.8},
    ))
    return world


def tell(params: StoryParams) -> World:
    rng = random.Random((params.seed or 0) ^ 0xA51C0P if False else (params.seed or 0) ^ 0xA51C0)
    world = make_world(params)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    captain = world.entities["captain"]
    scallop = world.entities["scallop"]
    plaque = world.entities["plaque"]
    scene = rng.choice(SCENES)

    world.facts.update(
        scene=scene["title"],
        sunburn=scene["sun"],
        plaque_description=scene["plaque"],
        clue=scene["clue"],
        solution=scene["solution"],
        ending=scene["ending"],
        hero=hero.label,
        helper=helper.label,
        captain=captain.label,
        place=params.place,
        vessel=params.vessel,
        misunderstanding=True,
        object="plaque",
        creature="scallop",
    )

    world.say(f"At {params.place}, {scene['sun']} {hero.label} was preparing {params.vessel} for a voyage among the stars.")
    world.say(f"Beside Dock Seven, {hero.label} found {scene['plaque']}. A shy scallop rested beneath it, blinking in the glare.")
    world.para()
    world.say(f"{helper.label} rolled over with a soft beep. \"Captain Vega said the plaque was a launch signal,\" they said. \"We should carry it to the rocket boat.\"")
    world.say(f"\"Wait,\" said {hero.label}. \"The scallop is touching it. Maybe the shell creature is giving us a message.\"")
    world.say(f"The two explorers misunderstood one another. {helper.label} thought the scallop was guarding the plaque, while {hero.label} thought the plaque had fallen onto the scallop's home.")
    world.say(f"Then the scallop made three tiny taps. Nearby, {scene['clue']} led toward the harbor office.")
    world.para()
    world.say(f"{hero.label} crouched beside the scallop. \"Are you hurt?\" {hero.label} asked.")
    world.say(f"\"I am sorry,\" {helper.label} said. \"I guessed before I checked.\"")
    world.say(f"The captain's voice crackled over the radio: \"A careful space crew checks both the signal and the creature.\"")
    world.say(f"{hero.label} shaded the scallop with a folded sail, carried fresh seawater from the tide tank, and followed the clue with {helper.label}.")
    world.say(f"At the harbor office, they learned that {scene['solution']}. The captain helped return the plaque instead of launching it into space.")
    world.para()
    world.say(f"\"The scallop was not sending a launch order,\" {helper.label} admitted. \"It was asking us to notice the heat.\"")
    world.say(f"\"And the plaque was not a treasure for us,\" said {hero.label}. \"It was a message from someone else.\"")
    world.say(f"The captain smiled. \"Misunderstandings shrink when friends ask questions.\"")
    world.say(f"{scene['ending']}.")
    world.say(f"{hero.label} logged the lesson in the ship's star journal: \"Before I blast off, I will listen twice.\"")

    scallop.meters["sunburn"] = 0.25
    scallop.meters["water"] = 1.0
    scallop.meters["safety"] = 1.0
    scallop.memes["fear"] = 0.1
    scallop.memes["relief"] = 0.9
    plaque.meters["distance"] = 0.0
    plaque.meters["safety"] = 1.0
    hero.memes["courage"] += 0.3
    helper.memes["certainty"] += 0.4
    captain.memes["trust"] += 0.3
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly Space Adventure at {f['place']} about {f['hero']} finding a sunburned scallop and a plaque.",
        f"Tell a story where a misunderstanding about a plaque is solved by checking clues and helping a scallop.",
        f"Write a marina adventure with dialogue, a careful astronaut, a robot helper, and the lesson that questions can repair a misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Where did {f['hero']} find the sunburned scallop and plaque?",
            answer=f"{f['hero']} found them at {f['place']}, near Dock Seven while preparing {f['vessel']}.",
        ),
        QAItem(
            question="What was the misunderstanding?",
            answer=f"{f['helper']} thought the plaque was a launch signal and that the scallop was guarding it, but the plaque had fallen near the scallop and the scallop needed shade and water.",
        ),
        QAItem(
            question="How did the explorers solve the misunderstanding?",
            answer=f"They listened to the scallop's three taps, followed {f['clue']}, asked questions, shaded the scallop, and returned the plaque to its proper place.",
        ),
        QAItem(
            question="What happened to the scallop at the end?",
            answer=f"The scallop was cooled with seawater and rested safely in shade while {f['ending'].split(' while ')[-1] if ' while ' in f['ending'] else 'the marina crew watched over it'}.",
        ),
        QAItem(
            question="What lesson did the space crew learn?",
            answer="They learned that misunderstandings become smaller when friends stop, listen, and ask questions before acting.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marina?",
            answer="A marina is a harbor where boats are kept, repaired, and prepared for trips.",
        ),
        QAItem(
            question="What is a scallop?",
            answer="A scallop is a sea animal with two fan-shaped shells.",
        ),
        QAItem(
            question="What is a plaque?",
            answer="A plaque is a flat plate with writing or pictures that remembers a person, place, or event.",
        ),
        QAItem(
            question="What does sunburned mean?",
            answer="Sunburned means skin or another exposed surface has been hurt or reddened by too much sunlight.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone understands a word, action, or situation incorrectly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items()}
        memes = {k: round(v, 3) for k, v in entity.memes.items()}
        lines.append(f"  {entity.id}: kind={entity.kind}, meters={meters}, memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
sunburned(scallop).
at_marina(scallop).
plaque_at_marina(plaque).
misunderstanding.
helped(scallop).
returned(plaque).

safe_scallop(S) :- sunburned(S), helped(S).
resolved(P) :- plaque_at_marina(P), returned(P), misunderstanding.
adventure_complete :- safe_scallop(scallop), resolved(plaque).
#show safe_scallop/1.
#show resolved/1.
#show adventure_complete/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("sunburned", "scallop"),
        asp.fact("at_marina", "scallop"),
        asp.fact("plaque_at_marina", "plaque"),
        asp.fact("misunderstanding"),
        asp.fact("helped", "scallop"),
        asp.fact("returned", "plaque"),
    ])


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    expected = {"safe_scallop", "resolved", "adventure_complete"}
    if expected.issubset(names):
        sample = generate(StoryParams(seed=17))
        if "misunderstanding" in sample.story.lower() and "scallop" in sample.story.lower():
            print("OK: ASP and Python story assumptions agree.")
            return 0
    print("MISMATCH between ASP and Python assumptions.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(seed=101, hero="Luna", helper="Orbit", captain="Captain Vega"),
    StoryParams(seed=202, hero="Nova", helper="Comet", captain="Captain Noor"),
    StoryParams(seed=303, hero="Mira", helper="Echo", captain="Captain Halley"),
    StoryParams(seed=404, hero="Tess", helper="Pip", captain="Captain Mira"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        print("ASP atoms:")
        for symbol in asp.one_model(asp_program()):
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1) * 100):
            if len(samples) >= max(args.n, 1):
                break
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
