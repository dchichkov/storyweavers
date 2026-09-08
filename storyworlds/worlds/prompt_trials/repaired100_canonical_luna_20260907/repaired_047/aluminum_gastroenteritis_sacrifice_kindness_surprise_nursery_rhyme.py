#!/usr/bin/env python3
"""
A standalone nursery-rhyme storyworld about a careful kindness:
- seed words: aluminum, gastroenteritis, sacrifice
- features: kindness, surprise
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402

ASP_RULES = r"""
safe_story(S) :- setting(S), has_kindness(S), has_surprise(S), careful_choice(S).
healthy_choice(C) :- choice(C), protects_guest(C).
good_turn(S) :- safe_story(S), healthy_choice(C).
"""

PLACE = "the moonlit nursery"

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount

@dataclass
class StoryParams:
    child: str
    guest: str
    vessel: str
    treat: str
    seed: Optional[int] = None

@dataclass(frozen=True)
class Scenario:
    key: str
    trouble: str
    clue: str
    guest_line: str
    sacrifice: str
    repair: str
    result: str
    surprise: str
    ending: str

@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for entity in self.entities.values():
            parts = []
            if entity.meters:
                parts.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                parts.append(f"memes={dict(entity.memes)}")
            if entity.label:
                parts.append(f"label={entity.label!r}")
            lines.append(f"  {entity.id:10} ({entity.kind:10}) {' '.join(parts)}")
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)

NAMES = ["Luna", "Pip", "Mara", "Bram", "Nell", "Toby", "Wren", "Milo"]
GUESTS = ["a sleepy lamb", "a little fox", "a bluebird", "a shy mouse", "a small bear"]
VESSELS = ["aluminum cup", "aluminum bowl", "aluminum spoon", "aluminum lunch tin"]
TREATS = ["warm porridge", "apple mash", "rice pudding", "soft pear"]

SCENARIOS = [
    Scenario(
        "cup_of_care",
        "The guest grew pale and tired, and a worried whisper said gastroenteritis had made the little belly ache.",
        "The guest could keep down only tiny sips, while the nursery clock ticked softly.",
        '"No feast for me tonight," the guest said. "A sip and a quiet bed would be right."',
        "gave up the sweet supper and saved it for morning, choosing comfort over celebration",
        "washed the aluminum cup, cooled clean water, and carried it with slow, steady steps",
        "The guest rested safely, took small sips, and soon found a little strength.",
        "Behind the curtain, the nursery stars had made a paper moon with a bright silver tail.",
        "The moon swung low above the bed, and kindness hummed a gentle tune.",
    ),
    Scenario(
        "tinny_rain",
        "A tummy bug called gastroenteritis had left the guest too weak for the noisy rain game.",
        "The aluminum lunch tin made a clear ping whenever a drop struck its lid.",
        '"Could we make a quiet rain instead?" the guest asked.',
        "set aside the grand game and offered the best blanket, even though the night felt chilly",
        "turned the aluminum tin into a soft drum by wrapping it in cloth and placed water nearby",
        "The guest smiled at the gentle patter and rested without being startled.",
        "When the cloth came away, tiny painted raindrops appeared on the tin.",
        "The moonlit nursery tapped, tap-tap, while the brave little guest dreamed.",
    ),
    Scenario(
        "spoonful_song",
        "Gastroenteritis had stolen the guest's appetite just when everyone expected a birthday supper.",
        "One small spoonful stayed comfortable, while a large serving made the guest turn away.",
        '"Please do not hurry me," the guest said. "Small is kind tonight."',
        "let the birthday child miss the cake song and saved one candle for a gentler morning",
        "measured a tiny portion in the aluminum spoon and waited patiently between sips",
        "The guest managed a little food and fell asleep peacefully.",
        "The cake was hidden under a cloth, but its candlelight made a star-shaped shadow.",
        "The shadow danced on the wall until the guest laughed a quiet laugh.",
    ),
    Scenario(
        "bowl_of_stars",
        "The guest had gastroenteritis and could not join the nursery parade.",
        "A cool cloth and a few careful sips helped more than bright marching or loud bells.",
        '"I can watch from bed," the guest said. "Please make the parade soft."',
        "gave away the parade leader's shiny badge and stopped the marching band at the door",
        "filled an aluminum bowl with water and reflected a small lamp across its smooth rim",
        "The guest watched calm stars shimmer and felt less alone.",
        "The reflected lamp suddenly shaped a golden crown on the ceiling.",
        "No drum went boom, yet every star seemed to cheer the resting guest.",
    ),
]

OPENINGS = [
    "In the moonlit nursery, Luna heard a tiny cough before the first star blinked.",
    "Hush-a-bye, hush-a-bye, the nursery was bright when {child} opened the door.",
    "At bedtime, {child} found a little guest awake beneath the quilt.",
    "Round went the moon, and soft went the broom, as {child} tiptoed through the nursery.",
]

def reasonableness_gate(params: StoryParams) -> None:
    if not params.child.strip():
        raise StoryError("A nursery rhyme needs a named child.")
    if params.guest not in GUESTS:
        raise StoryError("The guest must be a gentle nursery visitor.")
    if params.vessel not in VESSELS:
        raise StoryError("The vessel must be a small aluminum nursery object.")
    if params.treat not in TREATS:
        raise StoryError("The treat must be a mild, child-friendly food.")

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "moonlit_nursery"),
        asp.fact("has_kindness", "moonlit_nursery"),
        asp.fact("has_surprise", "moonlit_nursery"),
        asp.fact("careful_choice", "moonlit_nursery"),
        asp.fact("choice", "small_sips"),
        asp.fact("choice", "quiet_rest"),
        asp.fact("choice", "gentle_food"),
        asp.fact("protects_guest", "small_sips"),
        asp.fact("protects_guest", "quiet_rest"),
        asp.fact("protects_guest", "gentle_food"),
    ])

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        child=rng.choice(NAMES),
        guest=rng.choice(GUESTS),
        vessel=rng.choice(VESSELS),
        treat=rng.choice(TREATS),
        seed=rng.randrange(2**31),
    )

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme kindness storyworld.")
    parser.add_argument("--child")
    parser.add_argument("--guest", choices=GUESTS)
    parser.add_argument("--vessel", choices=VESSELS)
    parser.add_argument("--treat", choices=TREATS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = valid_params(rng)
    for field_name in ("child", "guest", "vessel", "treat"):
        value = getattr(args, field_name)
        if value:
            setattr(params, field_name, value)
    reasonableness_gate(params)
    return params

def build_world(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", "character", params.child))
    guest = world.add(Entity("guest", "character", params.guest))
    vessel = world.add(Entity("vessel", "object", params.vessel))
    treat = world.add(Entity("treat", "food", params.treat))
    world.facts.update(
        child=child,
        guest=guest,
        vessel=vessel,
        treat=treat,
        place=PLACE,
        kindness=True,
        surprise=True,
        illness="gastroenteritis",
        material="aluminum",
    )
    return world

def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    child = world.get("child")
    guest = world.get("guest")
    vessel = world.get("vessel")
    treat = world.get("treat")

    child.bump_meme("kindness")
    guest.bump_meme("trust")

    world.say(rng.choice(OPENINGS).format(child=child.label))
    world.say(
        f"{child.label} found {guest.label} tucked in bed and brought the {treat.label}, "
        f"but the guest's tired face asked for care rather than a feast."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(scenario.clue)
    world.say(scenario.guest_line)
    world.para()

    child.bump_meme("patience")
    world.say(
        f"{child.label} listened. Instead of making a fuss, {child.label} chose a gentle sacrifice: "
        f"{scenario.sacrifice}."
    )
    world.say(f"Then {child.label} {scenario.repair}.")
    vessel.bump_meter("use", 1)
    world.para()

    world.say(scenario.result)
    guest.bump_meme("hope")
    world.say(f"{scenario.surprise} The surprise made the quiet room feel warm.")
    world.say(scenario.ending)
    world.say(
        f"By morning, the {vessel.label} stood clean beside the bed, and {child.label} remembered "
        "that kindness can be small, patient, and bright."
    )

    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        clue=scenario.clue,
        guest_line=scenario.guest_line,
        sacrifice=scenario.sacrifice,
        repair=scenario.repair,
        result=scenario.result,
        surprise=scenario.surprise,
        ending=scenario.ending,
        resolved=True,
    )

def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a nursery rhyme about {facts['child'].label} showing kindness to {facts['guest'].label}.",
        "Write a gentle child-facing story using aluminum, gastroenteritis, and sacrifice.",
        f"Tell a story in the moonlit nursery where a {facts['vessel'].label} helps reveal a surprise.",
    ]

def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    child = facts["child"].label
    guest = facts["guest"].label
    vessel = facts["vessel"].label
    return [
        QAItem(
            "What made the guest need quiet care?",
            f"The guest had gastroenteritis, which caused a sore, tired belly and made a large meal or noisy game unsuitable.",
        ),
        QAItem(
            f"What sacrifice did {child} make?",
            f"{child} gave up the grand celebration or sweet supper so {guest} could rest safely and comfortably.",
        ),
        QAItem(
            f"How did the {vessel} help?",
            f"The {vessel} was used gently to offer water, soft sounds, or a calm reflection while the guest rested.",
        ),
        QAItem(
            "What was the surprise?",
            facts["surprise"] + " It appeared after the careful kindness.",
        ),
        QAItem(
            "How did the story end?",
            facts["ending"] + " The guest was safe, comforted, and hopeful.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is aluminum?",
            "Aluminum is a light metal often used to make cups, bowls, spoons, and other useful objects.",
        ),
        QAItem(
            "What does gastroenteritis mean?",
            "Gastroenteritis is an illness that can upset the stomach and intestines, so a sick person may need rest and small sips of fluid.",
        ),
        QAItem(
            "What is a sacrifice?",
            "A sacrifice is giving up something one wants in order to help or protect someone else.",
        ),
        QAItem(
            "What is kindness?",
            "Kindness means noticing another person's needs and choosing to help with care.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)

def asp_verify() -> int:
    import asp
    program = asp_program(
        "#show safe_story/1.\n#show healthy_choice/1.\n#show good_turn/1."
    )
    model = asp.one_model(program)
    found = set()
    for symbol in model:
        if symbol.name in {"safe_story", "healthy_choice", "good_turn"}:
            found.add((symbol.name, tuple(
                arg.name if arg.type != 1 else arg.string
                for arg in symbol.arguments
            )))
    expected = {
        ("safe_story", ("moonlit_nursery",)),
        ("good_turn", ("moonlit_nursery",)),
        ("healthy_choice", ("small_sips",)),
        ("healthy_choice", ("quiet_rest",)),
        ("healthy_choice", ("gentle_food",)),
    }
    if found == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and expected story rules.")
    print("ASP:", sorted(found))
    print("PY :", sorted(expected))
    return 1

def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_turn/1."))
    return sorted(asp.atoms(model, "good_turn"))

def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))

CURATED = [
    StoryParams("Luna", "a sleepy lamb", "aluminum cup", "warm porridge", 11),
    StoryParams("Pip", "a little fox", "aluminum bowl", "apple mash", 29),
    StoryParams("Mara", "a bluebird", "aluminum spoon", "rice pudding", 47),
]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_turn/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible moonlit nursery stories:")
        for item in asp_list():
            print(item)
        return

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempts += 1

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
