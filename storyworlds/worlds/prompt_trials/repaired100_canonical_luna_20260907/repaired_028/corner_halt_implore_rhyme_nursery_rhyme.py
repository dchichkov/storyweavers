#!/usr/bin/env python3
"""
A tiny nursery-rhyme world about a corner, a halt, and a plea for help.
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
    meters: dict[str, float] = field(default_factory=lambda: {"steps": 0.0, "distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"courage": 0.0, "worry": 0.0, "trust": 0.0})


@dataclass
class Object:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: {"position": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"importance": 0.0})
    blocked: bool = False


@dataclass
class World:
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
    helper_name: str = "Rhyme"
    cart_name: str = "moon cart"
    object_name: str = "silver bell"
    setting: str = "nursery lane"


NAMES = ["Luna", "Milo", "Nell", "Pip", "Tess"]
HELPERS = ["Rhyme", "Bramble", "Daisy", "Poe"]
CARTS = ["moon cart", "star cart", "red wagon", "cloud buggy"]
OBJECTS = ["silver bell", "blue bead", "golden thimble", "tiny drum"]

RHYME_ARCS = [
    {
        "key": "pebble_corner",
        "problem": "a round pebble wedged beneath one wheel at the lane's sharp corner",
        "halt": "the cart gave a clack and came to a halt",
        "mistake": "Luna tugged and shoved with all her might",
        "harm": "the cart tilted toward a puddle and scattered its blankets",
        "help": "Rhyme showed Luna how to lift the handle while Luna rolled the pebble free",
        "cause": "the pebble had jammed the wheel just where the path bent",
        "lesson": "a pause can make a tricky task plain",
        "ending": "the cart rolled round the corner, bell-bright and safe",
    },
    {
        "key": "thorny_turn",
        "problem": "a thorny vine curled across the cart's path at the garden corner",
        "halt": "the little cart stopped short with a squeaky halt",
        "mistake": "Luna pulled the vine without looking at its tangled end",
        "harm": "the vine caught the ribbon and tied a knot around the cart",
        "help": "Rhyme asked Luna to implore the gardener for snips, then they freed the ribbon together",
        "cause": "the vine had grown across the turning stones during the night",
        "lesson": "asking for safe help is braver than wrestling alone",
        "ending": "the ribbon waved beyond the corner like a flag in the dawn",
    },
    {
        "key": "rainy_rut",
        "problem": "rain filled a deep rut beside the nursery corner",
        "halt": "the cart rolled into it and made a sudden halt",
        "mistake": "Luna raced back and forth, trying to pull it straight",
        "harm": "mud splashed the blankets and hid the cart's small wheel",
        "help": "Rhyme told Luna to implore the baker for a board, and together they bridged the rut",
        "cause": "the rain had washed away the firm earth beneath the turning path",
        "lesson": "a good helper and a simple tool can mend a hard road",
        "ending": "the board made a bridge, and the cart crossed with a gentle song",
    },
]


def validate(params: StoryParams) -> None:
    if params.setting != "nursery lane":
        raise StoryError("This nursery-rhyme world only knows the nursery lane.")
    for label, value in (
        ("child name", params.child_name),
        ("helper name", params.helper_name),
        ("cart name", params.cart_name),
        ("object name", params.object_name),
    ):
        if not value or len(value.strip()) < 2:
            raise StoryError(f"The {label} must be a readable name.")
    if params.child_name == params.helper_name:
        raise StoryError("The child and helper must have different names.")
    if params.seed is not None and params.seed < 0:
        raise StoryError("The seed must not be negative.")


def build_world(params: StoryParams) -> World:
    validate(params)
    world = World()
    child = Character(params.child_name, "child")
    helper = Character(params.helper_name, "helper")
    cart = Object(params.cart_name, "cart")
    prize = Object(params.object_name, "keepsake")
    prize.memes["importance"] = 1.0
    world.characters[child.name] = child
    world.characters[helper.name] = helper
    world.objects[cart.name] = cart
    world.objects[prize.name] = prize
    world.facts.update(child=child, helper=helper, cart=cart, prize=prize)
    return world


def narrate(world: World, seed: int) -> None:
    rng = random.Random(seed ^ 0xC0A7)
    child: Character = world.facts["child"]
    helper: Character = world.facts["helper"]
    cart: Object = world.facts["cart"]
    prize: Object = world.facts["prize"]
    arc = rng.choice(RHYME_ARCS)

    child.meters["steps"] = 3.0
    child.meters["distance"] = 8.0
    child.memes["worry"] = 0.2
    cart.meters["position"] = 8.0
    cart.blocked = True
    world.facts["arc"] = arc

    world.say(f"At dawn in the nursery lane, Luna skipped with a tune;")
    world.say(f"She pushed the {cart.name} beneath a pale moon.")
    world.say(f"The {prize.name} rang with a bright little chime,")
    world.say(f"And the lane seemed to dance in its peppermint time.")
    world.say(f"But near the {arc['problem']},")
    world.say(f"{arc['halt'].capitalize()}—not a step, not a sway, not a roll.")

    world.para()
    world.say(f'"Pull, little cart!" cried {child.name}. "We must hurry along!"')
    world.say(f'"Wait," said {helper.name}. "What made it stop? Hear the song."')
    world.say(f'{child.name} {arc["mistake"]}.')
    world.say(f'{arc["harm"].capitalize()}.')
    child.memes["worry"] += 0.8
    world.say(f"The {prize.name} gave one worried ting, and the lane grew still.")

    world.para()
    world.say(f'"Rhyme, I implore you, please help me see!" {child.name} cried.')
    world.say(f'"First halt and breathe; then look by my side," {helper.name} replied.')
    child.memes["trust"] += 1.0
    child.memes["courage"] += 0.5
    world.say(f"Together they learned that {arc['cause']}.")
    world.say(f"{helper.name} and {child.name} {arc['help']}.")
    cart.blocked = False
    cart.meters["position"] = 12.0
    prize.meters["position"] = 12.0

    world.para()
    child.memes["courage"] += 0.5
    child.memes["worry"] = 0.0
    world.say(f"The {cart.name} moved with a hum, and the {prize.name} chimed clear.")
    world.say(f"{child.name} smiled. " + f'"A halt helped the answer appear."')
    world.say(f"{child.name} learned that {arc['lesson']}.")
    world.say(f"And {arc['ending']};")
    world.say("so the nursery lane sang softly, \"All is well!\"")


def generation_prompts(world: World) -> list[str]:
    child: Character = world.facts["child"]
    helper: Character = world.facts["helper"]
    return [
        f"Write a gentle Nursery Rhyme about {child.name}, a child whose cart stops at a corner.",
        f"Include {helper.name} as a helpful character whom {child.name} can implore.",
        "Use clear rhyme, a small problem, a halt, a safe solution, and a warm ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Character = world.facts["child"]
    helper: Character = world.facts["helper"]
    cart: Object = world.facts["cart"]
    prize: Object = world.facts["prize"]
    arc = world.facts["arc"]
    return [
        QAItem(
            question=f"Who was pushing the {cart.name}?",
            answer=f"{child.name} was pushing the {cart.name} along the nursery lane.",
        ),
        QAItem(
            question=f"Why did the {cart.name} come to a halt?",
            answer=f"It stopped because {arc['cause']}.",
        ),
        QAItem(
            question=f"Who did {child.name} implore for help?",
            answer=f"{child.name} implored {helper.name}, who helped inspect the problem and fix it safely.",
        ),
        QAItem(
            question=f"What happened to the {prize.name} at the end?",
            answer=f"The {prize.name} chimed clearly while the cart rolled safely onward.",
        ),
        QAItem(
            question=f"What lesson did {child.name} learn?",
            answer=f"{child.name} learned that {arc['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a corner?",
            answer="A corner is a place where two sides, paths, or walls meet and a traveler may need to turn.",
        ),
        QAItem(
            question="What does halt mean?",
            answer="Halt means to stop moving, often so someone can look, listen, or decide what to do next.",
        ),
        QAItem(
            question="What does implore mean?",
            answer="Implore means to ask earnestly and urgently for help or another important favor.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a poem or verse whose lines may repeat sounds, making it pleasant to hear and remember.",
        ),
    ]


ASP_RULES = r"""
setting(nursery_lane).
blocked(cart).
at_corner(cart).
needs_help(cart).
child(c).
helper(r).
halted(cart) :- blocked(cart), at_corner(cart).
implored(c,r) :- needs_help(cart), child(c), helper(r).
safe_solution :- halted(cart), implored(c,r).
resolved(cart) :- safe_solution.
#show halted/1.
#show implored/2.
#show safe_solution/0.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("child", "c"),
            asp.fact("helper", "r"),
            asp.fact("blocked", "cart"),
            asp.fact("at_corner", "cart"),
            asp.fact("needs_help", "cart"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program(
            "#show halted/1.\n#show implored/2.\n#show safe_solution/0.\n#show resolved/1."
        )
    )
    found = {(sym.name, tuple(str(arg) for arg in sym.arguments)) for sym in model}
    expected = {
        ("halted", ("cart",)),
        ("implored", ("c", "r")),
        ("safe_solution", ()),
        ("resolved", ("cart",)),
    }
    if found == expected:
        sample = generate(StoryParams(seed=7))
        if not sample.story or "halt" not in sample.story.lower() or "implore" not in sample.story.lower():
            print("Generated story failed the narrative gate.")
            return 1
        print("OK: ASP and Python parity verified.")
        return 0
    print("MISMATCH between ASP and expected world facts.")
    print("ASP atoms:", sorted(found))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming nursery-lane story about a helpful halt.")
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
    parser.add_argument("--object", dest="object_name", choices=OBJECTS)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        child_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        cart_name=args.cart or rng.choice(CARTS),
        object_name=args.object_name or rng.choice(OBJECTS),
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
    child: Character = world.facts["child"]
    cart: Object = world.facts["cart"]
    return (
        "--- world trace ---\n"
        f"{child.name}: meters={child.meters} memes={child.memes}\n"
        f"{cart.name}: meters={cart.meters} blocked={cart.blocked}"
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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
        print(asp_program("#show halted/1.\n#show implored/2.\n#show safe_solution/0.\n#show resolved/1."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(
            asp_program("#show halted/1.\n#show implored/2.\n#show safe_solution/0.\n#show resolved/1.")
        )
        for symbol in model:
            print(symbol)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams(seed=base_seed, child_name="Luna", helper_name="Rhyme", cart_name="moon cart", object_name="silver bell"),
            StoryParams(seed=base_seed + 1, child_name="Milo", helper_name="Daisy", cart_name="red wagon", object_name="blue bead"),
            StoryParams(seed=base_seed + 2, child_name="Nell", helper_name="Poe", cart_name="star cart", object_name="tiny drum"),
        ]
    else:
        params_list = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]
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
