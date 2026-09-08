#!/usr/bin/env python3
"""
A small heartwarming storyworld about a loose rim, a slanting cart, and a
lesson learned through patient repair.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"place": 0.0})
    memes: dict[str, float] = field(
        default_factory=lambda: {"worry": 0.0, "patience": 0.0, "pride": 0.0}
    )


@dataclass
class Object:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {"tilt": 0.0, "strength": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"meaning": 0.0})
    repaired: bool = False


@dataclass
class World:
    setting: str
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
    child_name: str = "Luna"
    helper_name: str = "Nana"
    cart_name: str = "little red cart"
    rim_name: str = "brass rim"
    setting: str = "community garden"


@dataclass(frozen=True)
class RepairArc:
    name: str
    opening: str
    first_attempt: str
    consequence: str
    careful_step: str
    cause: str
    repair: str
    lesson: str
    ending: str


NAMES = ["Luna", "Mira", "Nia", "Tessa", "Ari", "Jo"]
HELPERS = ["Nana", "Grandpa", "Aunt May", "Uncle Theo", "Mrs. Rosa"]
CARTS = ["little red cart", "blue garden wagon", "green library trolley", "yellow tea cart"]
RIMS = ["brass rim", "silver rim", "copper rim", "painted rim"]

ARCS = [
    RepairArc(
        "loose wheel",
        "Luna had promised to carry warm rolls from the garden kitchen to the neighbors",
        "pulled the cart quickly, hoping speed would hide its wobbles",
        "the cart took a slant and sent two rolls tumbling into the soft grass",
        "set the cart still, placed one hand on its handle, and watched which wheel moved first",
        "the rim around one wheel had grown lax after many sunny afternoons of use",
        "tightened the rim with Nana and added a smooth wooden brace beneath the axle",
        "a small loose thing deserves careful attention before it becomes a large tumble",
        "the cart rolled straight, carrying a basket of rolls and a little bunch of daisies",
    ),
    RepairArc(
        "rain barrel path",
        "Luna wanted to bring cups of water to the thirsty seedlings",
        "filled the cart to its brim and hurried down the stone path",
        "the heavy load made the cart slant toward a puddle and water splashed everywhere",
        "emptied half the cups and tested the path with one gentle push",
        "a lax rim let the cart's front basket lean whenever the path dipped",
        "fastened the rim with cloth ties, then carried two light trips instead of one heavy trip",
        "helping well sometimes means changing the plan, not forcing it",
        "the seedlings drank from a steady row of cups while the cart rested beneath a mint plant",
    ),
    RepairArc(
        "painted sign",
        "Luna was taking a new welcome sign to the garden gate",
        "balanced the sign on the cart and crossed the yard without asking for help",
        "a slanting turn tipped the sign into a puddle, washing one painted letter away",
        "asked Nana to hold the cart while Luna checked the rim and the balance",
        "the rim was lax where the sign's corner had been rubbing against it",
        "repaired the rim, dried the sign, and painted the missing letter together",
        "asking for help can protect both the work and the heart behind it",
        "the restored sign welcomed everyone, with one bright letter painted by each helper",
    ),
    RepairArc(
        "seed basket",
        "Luna carried a basket of sunflower seeds toward the oldest garden bed",
        "gave the cart a proud shove before checking its load",
        "the basket slid toward the rim and seeds sprinkled across the path",
        "knelt beside the cart and gathered the seeds before moving another inch",
        "the basket leaned because the rim no longer held its round shape",
        "reshaped the rim with a wooden mallet and tied the basket down with a red ribbon",
        "a pause to notice trouble is also a brave kind of action",
        "sunflowers later nodded above the repaired cart, and the red ribbon fluttered like a tiny flag",
    ),
    RepairArc(
        "library books",
        "Luna was bringing storybooks from the porch shelf to children waiting under the tree",
        "stacked every book high and tried to steer around a patch of pebbles",
        "the stack slanting sideways made the cart stop with a soft bump",
        "lowered the books, counted them, and asked which path would be kindest to the cart",
        "a lax rim made one corner lower than the other",
        "balanced the books in two baskets and repaired the rim with Nana's small wrench",
        "good work grows stronger when we share its weight",
        "the children read beneath the tree while the cart held the books as neatly as a shelf",
    ),
]


def build_world(params: StoryParams) -> World:
    if params.setting != "community garden":
        raise StoryError("This storyworld takes place in the community garden.")
    if not params.child_name.strip() or not params.helper_name.strip():
        raise StoryError("The child and helper need names.")
    world = World(setting=params.setting)
    child = Character(params.child_name, "helpful child")
    helper = Character(params.helper_name, "patient helper")
    cart = Object(params.cart_name, "cart")
    rim = Object(params.rim_name, "rim")
    world.characters[child.name] = child
    world.characters[helper.name] = helper
    world.objects[cart.name] = cart
    world.objects[rim.name] = rim
    world.facts.update(child=child, helper=helper, cart=cart, rim=rim)
    return world


def narrate(world: World, seed: int) -> None:
    rng = random.Random(seed ^ 0xA19E28)
    params = world.facts
    child: Character = params["child"]
    helper: Character = params["helper"]
    cart: Object = params["cart"]
    rim: Object = params["rim"]
    arc = rng.choice(ARCS)
    opening_detail = rng.choice(
        [
            "Morning light rested on the tomato leaves",
            "A warm breeze moved through the bean poles",
            "After a gentle rain, the garden paths shone",
            "The garden woke to birdsong and the smell of fresh bread",
        ]
    )
    dialogue = rng.choice(
        [
            (
                f'"I can fix this by going faster," {child.name} said.',
                f'"Let us first learn what the cart is telling us," {helper.name} replied.',
            ),
            (
                f'"I thought I could manage everything alone," {child.name} whispered.',
                f'"You do not have to carry a problem alone," said {helper.name}.',
            ),
            (
                f'"The cart is leaning," {child.name} noticed.',
                f'"Then we will stop before the leaning becomes a tumble," {helper.name} said.',
            ),
        ]
    )

    child.memes["worry"] += 1
    cart.meters["tilt"] = 1.0
    rim.meters["strength"] = 0.2
    world.facts.update(arc=arc, dialogue=dialogue)

    world.say(f"{opening_detail}, and {child.name} was ready to help.")
    world.say(f"{arc.opening}.")
    world.say(
        f"The {cart.name} waited nearby, but its {rim.name} was lax, so one side rested a little lower than the other."
    )
    world.say(f"{child.name} noticed the slant and frowned, yet tried to continue.")

    world.para()
    world.say(dialogue[0])
    world.say(f"In a hurry, {child.name} {arc.first_attempt}.")
    world.say(f"That choice made the trouble worse: {arc.consequence}.")
    world.say(f"The work was safe, but the happy plan no longer felt easy.")

    world.para()
    world.say(f"{helper.name} came close and listened without scolding.")
    world.say(dialogue[1])
    world.say(f"Together, they {arc.careful_step}.")
    world.say(f"They discovered that {arc.cause}.")
    child.memes["patience"] += 1
    rim.repaired = True
    rim.meters["strength"] = 1.0
    cart.meters["tilt"] = 0.0
    world.say(
        f"Instead of hiding the mistake, {child.name} helped {helper.name} make a careful repair: {arc.repair}."
    )

    world.para()
    child.memes["pride"] += 1
    world.say(f"The {cart.name} stood level again.")
    world.say(f"{child.name} learned that {arc.lesson}.")
    world.say(f"They finished the task together, and {arc.ending}.")
    world.say(
        f"That evening, {child.name} touched the once-lax {rim.name} and smiled at the transformation from a wobbly worry into a shared success."
    )


def generation_prompts(world: World) -> list[str]:
    child: Character = world.facts["child"]
    cart: Object = world.facts["cart"]
    return [
        f"Write a heartwarming children's story about {child.name} repairing a slanting {cart.name}.",
        "Include a lax rim, a failed first attempt, kind dialogue, a lesson learned, and a visible transformation.",
        "End with a concrete image showing that careful help changed the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Character = world.facts["child"]
    helper: Character = world.facts["helper"]
    cart: Object = world.facts["cart"]
    rim: Object = world.facts["rim"]
    arc: RepairArc = world.facts["arc"]
    return [
        QAItem(
            f"What was wrong with the {cart.name}?",
            f"Its {rim.name} was lax, which made the cart slant and become unsafe to hurry.",
        ),
        QAItem(
            f"What did {child.name} do first?",
            f"{child.name} tried to continue quickly, but {arc.consequence}.",
        ),
        QAItem(
            f"How did {helper.name} help?",
            f"{helper.name} listened kindly and worked with {child.name} to {arc.repair}.",
        ),
        QAItem(
            "What lesson was learned?",
            f"The lesson was that {arc.lesson}.",
        ),
        QAItem(
            "What transformation happened by the ending?",
            f"The cart changed from a slanting, wobbly problem into a level, useful cart, and the work became a shared success.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does lax mean?",
            "Lax means loose, slack, or not held tightly enough.",
        ),
        QAItem(
            "What is a rim?",
            "A rim is the outer edge of something round, such as a wheel, basket, or bowl.",
        ),
        QAItem(
            "What does slant mean?",
            "To slant means to lean or slope instead of standing straight or level.",
        ),
        QAItem(
            "What is a transformation?",
            "A transformation is a meaningful change from one condition or shape into another.",
        ),
        QAItem(
            "Why can asking for help be wise?",
            "Asking for help can bring another person's care, knowledge, and strength to a difficult problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
setting(community_garden).
problem(cart_slants) :- rim_lax.
needs_help(cart_slants) :- cart_slants.
repaired(cart) :- careful_check, helper_present.
lesson_learned(child) :- repaired(cart), helper_present.
transformed(cart) :- repaired(cart), not rim_lax_after.
rim_lax_after :- repaired(cart), false_marker.

#show problem/1.
#show needs_help/1.
#show repaired/1.
#show lesson_learned/1.
#show transformed/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("rim_lax"),
            asp.fact("careful_check"),
            asp.fact("helper_present"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    show = "\n".join(
        [
            "#show problem/1.",
            "#show needs_help/1.",
            "#show repaired/1.",
            "#show lesson_learned/1.",
            "#show transformed/1.",
        ]
    )
    model = asp.one_model(asp_program(show))
    names = {(sym.name, tuple(str(a) for a in sym.arguments)) for sym in model}
    expected = {
        ("problem", ("cart_slants",)),
        ("needs_help", ("cart_slants",)),
        ("repaired", ("cart",)),
        ("lesson_learned", ("child",)),
        ("transformed", ("cart",)),
    }
    if names != expected:
        print("MISMATCH between ASP and Python parity gate.")
        print("ASP atoms:", sorted(names))
        print("Expected:", sorted(expected))
        return 1
    sample = generate(StoryParams(seed=17))
    if not sample.story or "learned" not in sample.story:
        print("Generated story exercise failed.")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming lax-rim slant story with a lesson learned."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--cart", choices=CARTS)
    parser.add_argument("--rim", choices=RIMS)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        child_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        cart_name=args.cart or rng.choice(CARTS),
        rim_name=args.rim or rng.choice(RIMS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world, params.seed if params.seed is not None else 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.name}: meters={character.meters} memes={character.memes}"
        )
    for obj in world.objects.values():
        lines.append(
            f"{obj.name}: meters={obj.meters} memes={obj.memes} repaired={obj.repaired}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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

    if args.show_asp:
        print(
            asp_program(
                "\n".join(
                    [
                        "#show problem/1.",
                        "#show needs_help/1.",
                        "#show repaired/1.",
                        "#show lesson_learned/1.",
                        "#show transformed/1.",
                    ]
                )
            )
        )
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "\n".join(
                    [
                        "#show problem/1.",
                        "#show needs_help/1.",
                        "#show repaired/1.",
                        "#show lesson_learned/1.",
                        "#show transformed/1.",
                    ]
                )
            )
        )
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                seed=base_seed,
                child_name="Luna",
                helper_name="Nana",
                cart_name="little red cart",
                rim_name="brass rim",
            ),
            StoryParams(
                seed=base_seed + 1,
                child_name="Mira",
                helper_name="Grandpa",
                cart_name="blue garden wagon",
                rim_name="silver rim",
            ),
            StoryParams(
                seed=base_seed + 2,
                child_name="Nia",
                helper_name="Aunt May",
                cart_name="green library trolley",
                rim_name="copper rim",
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < target * 30:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
