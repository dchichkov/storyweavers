#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a garland, a playground slide, and a
wobbly strut. The story turns on a gentle twist: a decoration that seems to
cause trouble points to a useful repair instead.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
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
    name: str
    helper: str
    place: str
    route: int = 0
    seed: Optional[int] = None


CASES = [
    {
        "place": "the sunny neighborhood playground",
        "garland": "a paper garland of red and yellow stars",
        "problem": "the slide gave a small wobble when the first child climbed the steps",
        "strut": "one wooden strut beneath the platform had loosened",
        "twist": "the garland's ribbon had brushed the loose bolt and made the wobble easy to notice",
        "repair": "tightened the bolt with the park keeper and moved the garland to the fence",
        "image": "the star garland fluttered safely while children took turns on the steady slide",
    },
    {
        "place": "the little apartment courtyard",
        "garland": "a green garland made from old grocery bags",
        "problem": "the slide squeaked and leaned a tiny bit to one side",
        "strut": "a metal strut had slipped from its bracket",
        "twist": "the garland was not the trouble at all; its trailing loop had shown exactly where the bracket moved",
        "repair": "asked the caretaker to secure the strut and tied the garland into shorter loops",
        "image": "the green garland curled neatly above the slide as neighbors laughed below",
    },
    {
        "place": "the school garden play corner",
        "garland": "a bright garland of painted leaves",
        "problem": "the slide stopped halfway down with a dull bump",
        "strut": "a strut under the landing had shifted against a board",
        "twist": "the painted garland had cast a leaf-shaped shadow that helped the children see the crooked board",
        "repair": "showed the teacher the shadow, then helped place the strut back with an adult",
        "image": "painted leaves shone over a smooth slide and a freshly straightened landing",
    },
    {
        "place": "the community center yard",
        "garland": "a blue-and-white welcome garland",
        "problem": "the slide made a tired creak during the afternoon game",
        "strut": "a small strut was rubbing against its wooden support",
        "twist": "the wind tugged the garland at the same moment, making everyone look toward the hidden rubbing point",
        "repair": "paused the game, found the rubbing strut, and let the center worker fasten it",
        "image": "the welcome garland waved above the quiet slide before play began again",
    },
]


def build_world(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if not params.helper.strip():
        raise StoryError("helper must not be empty")
    if not 0 <= params.route < 10:
        raise StoryError("route must be between 0 and 9")

    case = CASES[params.route % len(CASES)]
    world = World(Setting(case["place"], {"play", "notice", "repair"}))
    child = world.add(Entity(
        "child", "person", params.name,
        meters={"steps": 0.0, "careful_checks": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "confidence": 0.0},
    ))
    helper = world.add(Entity(
        "helper", "person", params.helper,
        meters={"tools": 1.0},
        memes={"patience": 1.0, "kindness": 1.0},
    ))
    slide = world.add(Entity(
        "slide", "playground equipment", "the slide",
        meters={"steadiness": 0.4},
        memes={"waiting": 1.0},
    ))
    world.add(Entity(
        "garland", "decoration", case["garland"],
        meters={"loops": 3.0},
        memes={"cheer": 1.0},
    ))
    world.add(Entity(
        "strut", "support", "the strut",
        meters={"tightness": 0.3},
        memes={"reliability": 0.0},
    ))
    world.facts.update(
        case=case,
        child=child,
        helper=helper,
        slide=slide,
        checked=False,
        repaired=False,
        twist_revealed=False,
        lesson="careful attention can protect everyone",
    )
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    case = world.facts["case"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    slide: Entity = world.facts["slide"]
    strut = world.entities["strut"]

    openings = [
        f"{child.label} arrived at {world.setting.place} just as {case['garland']} was being hung nearby.",
        f"After school, {child.label} carried a cheerful afternoon to {world.setting.place}, where {case['garland']} shone in the breeze.",
        f"The ordinary afternoon changed when {child.label} noticed {case['garland']} beside the playground slide.",
    ]
    world.say(openings[params.route % len(openings)])
    world.say(f"Then {case['problem']}.")
    child.memes["worry"] += 1.0
    world.para()

    world.say(f'"Maybe the garland pulled it loose," {child.label} said.')
    world.say(f'"Maybe," {helper.label} replied, "but let us look before we decide."')
    world.say(f"{child.label} held the slide still and examined the steps, the landing, and {case['strut']}.")
    child.meters["careful_checks"] += 1.0
    world.facts["checked"] = True
    world.say(f"The first clue was a faint scrape near the support. The second was a ribbon mark from {case['garland']}.")
    world.say(f"That was the twist: {case['twist']}.")
    world.facts["twist_revealed"] = True
    world.para()

    world.say(f'"So the garland did not break the slide," {child.label} said. "It helped us notice the real problem."')
    world.say(f'"Exactly," said {helper.label}. "A quick guess can blame the wrong thing."')
    world.say(f"Together, they {case['repair']}.")
    strut.meters["tightness"] = 1.0
    strut.memes["reliability"] = 1.0
    slide.meters["steadiness"] = 1.0
    child.memes["confidence"] += 1.0
    world.facts["repaired"] = True
    world.say(f"{child.label} tested the slide with one careful push before anyone climbed.")
    world.say(f"At last, {case['image']}.")
    world.say(
        f'"I learned to check the whole story before choosing someone to blame," {child.label} said.'
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a slice-of-life story at {world.setting.place} involving {case['garland']}, a slide, and a loose strut.",
        "Include a gentle twist showing that a decoration helped reveal a problem rather than causing it.",
        "End with a lesson about careful attention, shared responsibility, and not blaming too quickly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    return [
        QAItem(
            question=f"What did {child.label} notice about the slide?",
            answer=f"{child.label} noticed that {case['problem']}. A closer check showed that {case['strut']} was the real concern.",
        ),
        QAItem(
            question="What was the twist involving the garland?",
            answer=f"The garland was not the cause of the trouble. Instead, {case['twist']}.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} encouraged a careful check and helped ensure that {case['repair']}.",
        ),
        QAItem(
            question="What moral value did the child practice?",
            answer="The child practiced responsibility and fairness by checking the facts before blaming anyone.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson was that careful attention can reveal a problem, and patient teamwork can make a shared place safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garland?",
            answer="A garland is a string or chain of decorations, such as leaves, paper shapes, or flowers.",
        ),
        QAItem(
            question="What is a slide?",
            answer="A slide is playground equipment with a smooth sloping surface that children can travel down safely when it is sound.",
        ),
        QAItem(
            question="What is a strut?",
            answer="A strut is a support piece that helps hold part of a structure in place.",
        ),
        QAItem(
            question="Why should children tell an adult about unsafe playground equipment?",
            answer="Children should tell an adult so the equipment can be checked and repaired before someone gets hurt.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id:8} ({entity.kind:20}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_slide :- checked, repaired.
lesson_learned :- safe_slide, twist_revealed.
moral_value :- lesson_learned.
"""


def asp_facts(world: Optional[World] = None) -> str:
    import asp
    if world is not None:
        facts = world.facts
        return "\n".join(
            asp.fact(name)
            for name in ("checked", "repaired", "twist_revealed")
            if facts.get(name)
        )
    return "\n".join(asp.fact(name) for name in ("checked", "repaired", "twist_revealed"))


def asp_program(world: Optional[World] = None, show: str = "") -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life storyworld about a garland, slide, and strut."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--place")
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


NAMES = ["Luna", "Milo", "Nia", "Theo", "Suri", "Evan"]
HELPERS = ["Aunt Bea", "Uncle Ravi", "Ms. Chen", "Dad", "Grandma Jo"]
PLACES = [case["place"] for case in CASES]


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    if args.n < 1:
        raise StoryError("-n must be at least 1")
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or PLACES[index % len(PLACES)],
        route=rng.randrange(10),
    )


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


def asp_verify() -> int:
    import asp
    world = tell(StoryParams("Luna", "Aunt Bea", PLACES[0], route=0))
    model = asp.one_model(
        asp_program(world, "#show safe_slide/0.\n#show lesson_learned/0.\n#show moral_value/0.")
    )
    names = {symbol.name for symbol in model}
    expected = {"safe_slide", "lesson_learned", "moral_value"}
    if expected <= names and world.facts["repaired"] and world.facts["twist_revealed"]:
        print("OK: ASP twin matches the repaired Python story state.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected repaired state.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show safe_slide/0.\n#show lesson_learned/0.\n#show moral_value/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        world = tell(StoryParams("Luna", "Aunt Bea", PLACES[0], route=0))
        model = asp.one_model(
            asp_program(world, "#show safe_slide/0.\n#show lesson_learned/0.\n#show moral_value/0.")
        )
        print("ASP atoms:", " ".join(sorted(str(symbol) for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 5 if args.all else args.n
    samples: list[StorySample] = []
    for index in range(count):
        seed = base_seed + index
        rng = random.Random(seed)
        params = resolve_params(args, rng, index)
        params.seed = seed
        params.route = (seed + index) % 10
        if args.place:
            params.place = args.place
        samples.append(generate(params))

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
