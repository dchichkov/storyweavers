#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_worlds = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))
if not os.path.exists(os.path.join(_worlds, "results.py")):
    _worlds = os.path.dirname(os.path.dirname(_here))
sys.path.insert(0, _worlds)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Tale:
    id: str
    omen: str
    danger: str
    gift: str
    magic: str
    action: str
    image: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    cracker: str
    name: str
    companion: str
    seed: Optional[int] = None


PLACES = {
    "moonlit_hill": "the moonlit hill",
    "whispering_marsh": "the whispering marsh",
    "star_bridge": "the old bridge of stars",
}

CRACKERS = {
    "honey": "a honey cracker",
    "salt": "a salt cracker",
    "cinnamon": "a cinnamon cracker",
}

NAMES = ["Luna", "Ari", "Robin", "Sage", "Mica", "Rowan"]
COMPANIONS = ["Mira", "Sol", "Tavi", "Jules", "River", "Ember"]

TALES = {
    "empty_basket": Tale(
        "empty_basket",
        "the moon forgot one of its silver lights",
        "the night would lose its gentle path",
        "a small cracker",
        "the cracker glowed whenever it was shared",
        "break the cracker into equal pieces and offer them to the dark",
        "the moon returned its silver light, reflected in every crumb",
        "a gift grows brighter when no one keeps it alone",
    ),
    "sleeping_river": Tale(
        "sleeping_river",
        "the river had stopped singing",
        "the villages would forget how to find one another",
        "a warm cracker",
        "each shared bite became a bright note",
        "share the cracker while singing one true note together",
        "the river sang beneath a bridge woven from moonlight",
        "teamwork can awaken what one voice cannot",
    ),
    "thorn_gate": Tale(
        "thorn_gate",
        "the gate of thorns had closed before dawn",
        "the wandering stars would remain outside the sky",
        "a cinnamon cracker",
        "it softened every thorn touched by a generous hand",
        "hold the cracker between them and pass it from hand to hand",
        "the stars crossed the open gate and scattered blue fire",
        "sharing courage makes a narrow way wide enough for all",
    ),
    "stone_giant": Tale(
        "stone_giant",
        "a stone giant had forgotten its name",
        "the giant might wake frightened and shake the valley",
        "a salt cracker",
        "its white grains carried memories when friends shared them",
        "tell the giant their names and divide the cracker among them",
        "kind voices help lost hearts remember who they are",
    ),
    "cloud_lantern": Tale(
        "cloud_lantern",
        "the cloud lantern had gone dark",
        "the dawn would arrive without a welcome",
        "a honey cracker",
        "its sweetness became light when held by two willing hands",
        "lift the cracker together and speak a promise of welcome",
        "a shared promise can turn a little light into a dawn",
    ),
    "fox_comet": Tale(
        "fox_comet",
        "a fox-shaped comet had fallen into the forest",
        "its burning tail might scorch every nest",
        "a cinnamon cracker",
        "the spice made the comet remember cool winter stars",
        "share the cracker and guide the comet with a circle of joined hands",
        "gentle teamwork can guide even a blazing thing home",
    ),
}


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, cracker) for place in PLACES for cracker in CRACKERS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None)
    cracker = getattr(args, "cracker", None)
    if place is not None and place not in PLACES:
        raise StoryError(f"unknown place: {place}")
    if cracker is not None and cracker not in CRACKERS:
        raise StoryError(f"unknown cracker: {cracker}")
    choices = [
        pair for pair in valid_combos()
        if place is None or pair[0] == place
        if cracker is None or pair[1] == cracker
    ]
    if not choices:
        raise StoryError("no compatible place and cracker choice")
    selected_place, selected_cracker = rng.choice(choices)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    if name == companion:
        raise StoryError("the two travelers must have different names")
    return StoryParams(selected_place, selected_cracker, name, companion)


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity("hero", "character", params.name))
    companion = world.add(Entity("companion", "character", params.companion))
    cracker = world.add(Entity("cracker", "object", CRACKERS[params.cracker]))
    hero.memes.update(curiosity=1.0, trust=0.0)
    companion.memes.update(courage=1.0, trust=0.0)
    cracker.meters.update(whole=1.0, shared=0.0, glowing=0.0)
    world.facts.update(hero=hero, companion=companion, cracker=cracker)
    return world


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else sum(map(ord, params.name + params.companion)))
    world = build_world(params)
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    cracker: Entity = world.facts["cracker"]  # type: ignore[assignment]
    tale = rng.choice(list(TALES.values()))
    world.facts["tale"] = tale

    world.say(
        f"Long ago, {hero.label} and {companion.label}, two androgynous travelers beneath "
        f"the same wide sky, reached {world.place}."
    )
    world.say(f"There they found {tale.omen}, and the old magic began to stir.")
    world.para()

    world.say(
        f"In {hero.label}'s hand rested {cracker.label}, a humble cracker, but the crumbs "
        f"shone like tiny stars."
    )
    world.say(f"{hero.label} whispered, \"Perhaps this cracker can help.\"")
    world.say(f"{companion.label} answered, \"Then we must discover its magic together.\"")
    world.para()

    hero.memes["trust"] = 1.0
    companion.memes["trust"] = 1.0
    world.say(f"The danger was clear: {tale.danger}.")
    world.say(
        f"{hero.label} wanted to rush ahead, but {companion.label} noticed that the magic "
        f"answered only when both travelers worked as one."
    )
    world.say(f"\"Do we each take half?\" asked {hero.label}.")
    world.say(f"\"We share it, and we share the work,\" said {companion.label}.")
    world.para()

    cracker.meters["whole"] = 0.0
    cracker.meters["shared"] = 1.0
    cracker.meters["glowing"] = 1.0
    hero.memes["teamwork"] = 1.0
    companion.memes["teamwork"] = 1.0
    world.say(f"Together they {tale.action}.")
    world.say(
        f"When the last piece of {cracker.label} passed from one hand to the other, "
        f"{tale.magic.capitalize()}."
    )
    world.say(f"The spell lifted, and {tale.image}.")
    world.para()

    world.say(
        f"{hero.label} smiled at {companion.label}. \"A small share made a mighty change.\""
    )
    world.say(
        f"{companion.label} nodded. \"That is the oldest magic: {tale.lesson}.\""
    )
    world.say(f"And so the two travelers continued beneath the kinder sky.")

    story = world.render()
    prompts = [
        "Write a myth about a cracker whose magic appears when friends share it.",
        f"Tell a gentle tale in which {params.name} and {params.companion} use teamwork to save a magical place.",
        "Write a child-facing story with cracker, share, and androgynous travelers.",
    ]
    story_qa = [
        QAItem("Who found the magical cracker?", f"{params.name} and {params.companion} found {cracker.label}."),
        QAItem("What danger did the travelers face?", f"They faced a danger because {tale.danger}."),
        QAItem("How did the magic work?", f"The magic worked when the travelers shared the cracker and worked together: {tale.magic}."),
        QAItem("What did the travelers learn?", f"They learned that {tale.lesson}."),
    ]
    world_qa = [
        QAItem("What is teamwork?", "Teamwork is when people cooperate and combine their efforts to solve a problem."),
        QAItem("What does it mean to share?", "To share means to give part of what you have so another person can enjoy or use it too."),
        QAItem("What is magic in a myth?", "Magic in a myth is a wondrous power that changes events in a way ordinary tools cannot."),
        QAItem("Why can dialogue matter in a story?", "Dialogue lets characters exchange ideas, change their choices, and solve problems together."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


ASP_RULES = r"""
valid(Place, Cracker) :- setting(Place), cracker(Cracker).
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [*(asp.fact("setting", key) for key in PLACES),
         *(asp.fact("cracker", key) for key in CRACKERS)]
    )


def asp_program(show: str = "#show valid/2.") -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(asp_valid_combos())
    if expected != actual:
        print("ASP/Python mismatch")
        print("only in Python:", sorted(expected - actual))
        print("only in ASP:", sorted(actual - expected))
        return 1
    for place, cracker in valid_combos():
        sample = generate(StoryParams(place, cracker, "Luna", "Sol", 17))
        if not sample.story or "cracker" not in sample.story:
            print("generated-story verification failed")
            return 1
    print(f"OK: ASP matches Python ({len(expected)} combinations); stories exercised.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A myth about a shared magical cracker.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--cracker", choices=CRACKERS)
    parser.add_argument("--name")
    parser.add_argument("--companion")
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
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for index, (place, cracker) in enumerate(valid_combos()):
            samples.append(generate(StoryParams(place, cracker, "Luna", "Sol", base_seed + index)))
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        print(
            samples[0].to_json() if len(samples) == 1
            else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)
        )
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
