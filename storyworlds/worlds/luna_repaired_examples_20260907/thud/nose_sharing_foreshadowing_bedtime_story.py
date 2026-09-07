#!/usr/bin/env python3
"""
A tiny bedtime storyworld about sharing and a little nose.
"""

from __future__ import annotations

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    @property
    def phrase(self) -> str:
        return self.label or self.id.replace("_", " ")


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
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


@dataclass(frozen=True)
class StoryArc:
    key: str
    object_name: str
    object_phrase: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    sharing: tuple[str, str]
    ending: tuple[str, str]
    problem: str
    action: str
    result: str


ARCS = (
    StoryArc(
        "blue_blanket",
        "blue blanket",
        "a soft blue blanket",
        (
            "In the quiet room, {hero} curled beneath a soft blue blanket.",
            "{helper} sat beside the bed, listening to the little house grow still.",
        ),
        (
            "Then the blanket slipped toward {hero}, leaving {helper}'s toes in the cool.",
            "A tiny painted moon on the blanket pointed toward the empty side, as if it knew.",
        ),
        (
            "{hero} lifted the blanket and made room. \"Come close,\" {hero} whispered.",
            "They shared its warmth, shoulder to shoulder, while the night breeze faded away.",
        ),
        (
            "Soon both children were snug beneath the blue moon blanket.",
            "Their peaceful breathing sounded like two small waves under the stars.",
        ),
        "the blanket covered only one child",
        "one child lifted the blanket and invited the other close",
        "both children stayed warm together",
    ),
    StoryArc(
        "honey_milk",
        "cup of warm milk",
        "one small cup of warm milk",
        (
            "At bedtime, {hero} found one small cup of warm milk on the table.",
            "{helper} came in slowly, rubbing a sleepy nose after the long day.",
        ),
        (
            "{hero} held the cup, but {helper}'s nose drooped when the sweet smell floated by.",
            "The spoon made one quiet circle, as though it were waiting for two friends.",
        ),
        (
            "{hero} took a sip, then passed the cup to {helper}.",
            "They shared the warm milk, passing it gently until the cup was empty.",
        ),
        (
            "The warm sweetness settled their tummies, and their sleepy noses pointed toward bed.",
            "Under the covers, they smiled at the moon and drifted into a peaceful dream.",
        ),
        "there was one cup of warm milk for two sleepy children",
        "the children passed the cup and shared every sip",
        "both children felt comforted before bed",
    ),
    StoryArc(
        "star_lamp",
        "star lamp",
        "a little star lamp",
        (
            "By the bed stood a little star lamp, glowing softly beside {hero}.",
            "{helper} watched its golden light while a cool shadow rested near the door.",
        ),
        (
            "The lamp shone mostly on {hero}, leaving {helper}'s nose in the dark.",
            "A paper star on the wall trembled once, as if it hoped the light would travel.",
        ),
        (
            "{hero} moved the lamp between them. \"There is room for both,\" {hero} said.",
            "The children shared the golden circle and read one last page together.",
        ),
        (
            "The star lamp warmed both faces, and neither nose hid in the shadows.",
            "When the light went out, their dream seemed bright enough to guide them.",
        ),
        "the lamp lit only one side of the bed",
        "the lamp was moved so both children could share its light",
        "both children could read and rest in the gentle glow",
    ),
    StoryArc(
        "moon_cookie",
        "moon-shaped cookie",
        "one moon-shaped cookie",
        (
            "On the bedside plate lay one moon-shaped cookie for {hero}.",
            "{helper} peeked at it, and a small hopeful smile appeared beneath a twitching nose.",
        ),
        (
            "{hero} held the cookie close, but {helper}'s nose followed its cinnamon scent.",
            "The cookie's two little points looked almost like it was asking for a friend.",
        ),
        (
            "{hero} broke the cookie carefully down the middle.",
            "One half went to each child, and they thanked the moon-shaped treat together.",
        ),
        (
            "Their crumbs made two tiny moons on the plate as their eyelids grew heavy.",
            "They fell asleep happy, with the sweet smell tucked inside their dreams.",
        ),
        "there was one cookie for two children",
        "the cookie was broken into two equal pieces",
        "each child received a fair share",
    ),
)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    hero_gender: str = "boy"
    helper_gender: str = "girl"
    seed: Optional[int] = None


PLACES = {
    "bedroom": Place("bedroom", "the cozy bedroom", {"room", "night"}),
    "attic": Place("attic", "the quiet attic room", {"room", "night"}),
    "cottage": Place("cottage", "the little cottage bedroom", {"room", "night"}),
}

NAMES = {
    "boy": ["Ben", "Leo", "Noah", "Sam", "Toby"],
    "girl": ["Mia", "Lily", "Nora", "Zoe", "Ava"],
}


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown bedtime setting.")
    if params.hero_name == params.helper_name:
        raise StoryError("The two children must have different names.")
    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = ARCS[rng.randrange(len(ARCS))]
    world = World(PLACES[params.place])
    hero = world.add(Entity(params.hero_name, "character", params.hero_gender, params.hero_name))
    helper = world.add(Entity(params.helper_name, "character", params.helper_gender, params.helper_name))
    shared = world.add(Entity(arc.key, "bedtime_object", "comfort", arc.object_phrase))
    hero.memes["kindness"] = 1.0
    helper.memes["trust"] = 1.0
    shared.meters["shared"] = 1.0

    values = {"hero": hero.phrase, "helper": helper.phrase}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()
    hero.memes["generosity"] = 1.0
    helper.memes["belonging"] = 1.0
    shared.meters["fair"] = 1.0
    for line in arc.sharing:
        world.say(line.format(**values))
    world.para()
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=hero,
        helper=helper,
        object=shared,
        arc=arc.key,
        object_name=arc.object_name,
        problem=arc.problem,
        action=arc.action,
        result=arc.result,
        ending=arc.ending[-1],
        place=world.place,
        shared=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    f = world.facts
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            'Write a gentle bedtime story that includes the word "nose" and shows sharing.',
            f"Tell a sleepy story in {f['place'].label} where {f['hero'].phrase} shares {f['object_name']} with {f['helper'].phrase}.",
            "Use a small early clue to foreshadow a kind choice at bedtime.",
        ],
        story_qa=[
            QAItem(
                "What problem did the children face?",
                f"They faced a sharing problem: {f['problem']}.",
            ),
            QAItem(
                "How did the children solve it?",
                f"They solved it by sharing: {f['action']}. As a result, {f['result']}.",
            ),
            QAItem(
                "What showed that the sharing worked?",
                f"The ending showed the change when {f['ending']}",
            ),
        ],
        world_qa=[
            QAItem(
                "What does sharing mean?",
                "Sharing means letting another person use or enjoy something too, so everyone can have a fair part.",
            ),
            QAItem(
                "Why might a story foreshadow an event?",
                "Foreshadowing gives a small early clue about something important that may happen later.",
            ),
        ],
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or ("girl" if hero_gender == "boy" else "boy")
    hero_name = args.hero or rng.choice(NAMES[hero_gender])
    helper_choices = [n for n in NAMES[helper_gender] if n != hero_name]
    helper_name = args.helper or rng.choice(helper_choices)
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        hero_name=hero_name,
        helper_name=helper_name,
        hero_gender=hero_gender,
        helper_gender=helper_gender,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
comfort_object(O) :- object(O).
shared(O) :- comfort_object(O), shared_meter(O, 1).
peaceful_bedtime :- shared(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("object", "bedtime_object"))
    lines.append(asp.fact("shared_meter", "bedtime_object", 1))
    return "\n".join(lines)


def asp_program(show: str = "#show peaceful_bedtime/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if not asp.atoms(model, "peaceful_bedtime"):
            raise RuntimeError("ASP model did not derive peaceful bedtime.")
        sample = generate(
            StoryParams("bedroom", "Ben", "Mia", "boy", "girl", seed=2)
        )
        if "nose" not in sample.story.lower() or not sample.story.strip():
            raise RuntimeError("Generated story failed the nose check.")
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A sharing bedtime story about a nose.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--hero-gender", choices=["boy", "girl"])
    parser.add_argument("--helper-gender", choices=["boy", "girl"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "peaceful_bedtime"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        for i, arc in enumerate(ARCS):
            params = StoryParams(
                "bedroom",
                "Ben",
                "Mia",
                "boy",
                "girl",
                base_seed + i,
            )
            samples.append(generate(params))
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### bedtime story {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
