#!/usr/bin/env python3
"""Gingham Magic: a nursery-rhyme dialogue about mending a moonlit cart."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    child: str = "Pip"
    helper: str = "Mabel"
    charm: str = "moonbeam"
    cloth: str = "gingham"
    seed: int = 777


NAMES = ("Pip", "Mabel", "Nell", "Toby", "Daisy", "Robin")
CHARMS = {
    "moonbeam": ("moonbeam", "silver"),
    "stardust": ("stardust", "golden"),
    "raindrop": ("raindrop", "blue"),
}
CLOTHES = {
    "gingham": ("gingham", "red-and-white"),
    "calico": ("calico", "green-and-cream"),
    "ribbon": ("ribbon", "purple"),
}

PROMPT = (
    "Write a dialogue-rich nursery-rhyme story about two children using magic "
    "and gingham to repair a little cart."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "child": Entity(
                "child", params.child, "character", "nursery",
                memes={"worry": 1.0, "hope": 0.4},
            ),
            "helper": Entity(
                "helper", params.helper, "character", "nursery",
                memes={"calm": 0.8, "trust": 0.5},
            ),
            "cart": Entity(
                "cart", "the little cart", "vehicle", "nursery",
                meters={"wheels": 2, "sound_wheels": 1, "riders": 0},
                memes={"magic": 0.0},
            ),
            "cloth": Entity(
                "cloth", f"the {params.cloth} cloth", "material", "nursery",
                meters={"patches": 3, "used": 0},
            ),
            "moon": Entity(
                "moon", "the moon", "sky", "window",
                meters={"light": 1},
                memes={"watchful": 1.0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(
        self,
        kind: str,
        text: str,
        *,
        question: str = "",
        cause: str = "",
        result: str = "",
    ):
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def say(self, speaker: str, text: str):
        if speaker not in self.entities:
            raise StoryError("A missing speaker cannot join the conversation.")
        if not text or not text.endswith((".", "?", "!")):
            raise StoryError("Spoken lines need clear punctuation.")
        name = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(kind="speech", text=f'"{text}" {name} {verb}.', state=self.snapshot())
        )


def validate_params(params: StoryParams):
    if params.child == params.helper:
        raise StoryError("The two speakers must have different names.")
    if any(not name or not name[0].isupper() for name in (params.child, params.helper)):
        raise StoryError("Names must begin with capital letters.")
    if params.charm not in CHARMS:
        raise StoryError("Unknown magical charm.")
    if params.cloth not in CLOTHES:
        raise StoryError("Unknown cloth.")


def mend_cart(world: World):
    cart = world.entities["cart"]
    cloth = world.entities["cloth"]
    if cloth.meters["used"] >= cloth.meters["patches"]:
        raise StoryError("There is no gingham patch left for the cart.")
    if world.entities["child"].memes.get("plan") != "mend":
        raise StoryError("The children must agree on a mending plan first.")
    cloth.meters["used"] += 1
    cart.meters["wheels"] = 4
    cart.meters["sound_wheels"] = 0


def awaken_cart(world: World):
    cart = world.entities["cart"]
    if cart.meters["wheels"] != 4:
        raise StoryError("The cart needs its missing wheel repaired first.")
    if world.entities["helper"].memes.get("charm_ready") != world.params.charm:
        raise StoryError("The magical charm has not been prepared.")
    cart.meters["sound_wheels"] = 1
    cart.memes["magic"] = 1.0


def check_ending(world: World):
    cart = world.entities["cart"]
    child = world.entities["child"]
    helper = world.entities["helper"]
    if cart.meters["wheels"] != 4 or cart.meters["sound_wheels"] != 1:
        raise StoryError("The cart must finish mended and rolling quietly.")
    if cart.location != "moonlit garden":
        raise StoryError("The ending must place the cart in the moonlit garden.")
    if child.memes.get("brave") != 1.0 or helper.memes.get("proud") != 1.0:
        raise StoryError("The children's changed feelings must be shown in the world.")


def check_sample(sample: StorySample):
    world = sample.world
    check_ending(world)
    speech = [event for event in world.history if event.kind == "speech"]
    if len(speech) < 10:
        raise StoryError("The story needs a sustained exchange of dialogue.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs at least three grounded questions.")
    if not any("?" in event.text for event in speech):
        raise StoryError("The characters must ask one another a useful question.")
    if "gingham" not in sample.story.lower():
        raise StoryError("The story must name the gingham cloth.")
    if "magic" not in sample.story.lower() and "spell" not in sample.story.lower():
        raise StoryError("The story must make the magic visible.")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = World(params)
    child = world.entities["child"]
    helper = world.entities["helper"]
    cart = world.entities["cart"]
    cloth = world.entities["cloth"]
    charm_name, charm_color = CHARMS[params.charm]
    cloth_name, cloth_color = CLOTHES[params.cloth]
    c_name = child.label
    h_name = helper.label

    world.narrate(
        "beginning",
        f"At moonrise, {c_name} found a little cart by the nursery door. "
        f"Its wheel was gone, and its {cloth_name} seat flapped in the breeze. "
        f"Three silver bells chimed, but the cart could not roll.",
    )
    world.say("child", "Oh, little cart, why can you not go?")
    world.say("helper", "Your wheel is missing, and your seat needs a bright patch.")
    world.say("child", "Can a bit of cloth mend a cart?")
    world.say("helper", "Gingham can, if we sew it with care and wake it with a charm.")

    world.narrate(
        "problem",
        f"The cart leaned toward the dark garden path. Its loose {cloth_name} seat "
        "trembled whenever the night wind blew.",
        question="What was wrong with the little cart?",
        cause="One wheel was missing and the seat had a tear.",
        result="The children needed cloth and a careful plan before the cart could move.",
    )

    world.say("child", "I will pull the cart as fast as I can.")
    world.say("helper", "That may tear the seat farther. What should we do instead?")
    world.say("child", "We can stitch the tear and make a new wheel from moonlight.")
    world.say("helper", "Yes. You hold the gingham, and I will whisper the charm.")
    child.memes["plan"] = "mend"
    helper.memes["charm_ready"] = params.charm

    world.narrate(
        "agreement",
        f"{c_name} spread the {cloth_color} {cloth_name} cloth across the seat. "
        f"{h_name} placed one hand on the empty wheel peg.",
        question="Why did the children choose gingham instead of pulling the cart?",
        cause="Pulling could make the torn seat worse, while a careful patch could hold it firm.",
        result=f"{c_name} held the cloth steady so {h_name} could prepare the {charm_name} charm.",
    )

    mend_cart(world)
    world.narrate(
        "mending",
        f"Snip, stitch, pat! The {cloth_name} patch settled flat as a little red-and-white square. "
        "It shone like a picnic cloth under the moon.",
    )
    world.say("child", "The patch is snug. Is the cart ready?")
    world.say("helper", "Not yet. A spell needs a promise as well as a sparkle.")
    world.say("child", "I promise to carry the small bells gently.")
    world.say("helper", "Then I promise to guide the cart along the safe path.")

    world.narrate(
        "magic",
        f"{h_name} lifted a {charm_color} thread of {charm_name}. "
        f"Together they whispered, 'Wheel and cloth, be whole and soft!'",
        question="What made the new wheel appear?",
        cause=f"The children agreed on careful work and spoke the {charm_name} charm together.",
        result="Moonlight curled around the peg and became a shining fourth wheel.",
    )
    awaken_cart(world)
    cart.location = "moonlit garden"
    child.memes["brave"] = 1.0
    helper.memes["proud"] = 1.0
    child.memes["worry"] = 0.0
    helper.memes["calm"] = 1.0

    world.narrate(
        "turn",
        f"Round and round went the new wheel. The cart gave a tiny bell-jingle, "
        f"then rolled from the nursery into the moonlit garden.",
        question="How did the children know the cart was truly fixed?",
        cause="The fourth wheel held, the patched seat stayed flat, and the cart rolled without a scrape.",
        result="They could guide it safely into the moonlit garden.",
    )
    world.say("child", "Look! It rolls as softly as a cloud.")
    world.say("helper", "And the gingham patch is dancing, not tearing.")
    world.say("child", "What shall we carry first?")
    world.say("helper", "The bells, the blue blanket, and a basket of moon pears.")

    world.narrate(
        "ending",
        f"By the moonlit gate, {c_name} and {h_name} loaded the bells and blanket. "
        f"The little cart twinkled on its {cloth_name} seat, and the new wheel left four neat circles in the dew.",
        question="What showed that the children's plan had worked?",
        cause="They patched the seat, made a fourth wheel with magic, and tested the cart gently.",
        result="The cart carried its load into the garden and left four bright tracks in the dew.",
    )

    sample = WorldSample(world, params).make()
    check_sample(sample)
    return sample


class WorldSample:
    def __init__(self, world: World, params: StoryParams):
        self.world = world
        self.params = params

    def make(self) -> StorySample:
        questions = [
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in self.world.history
            if event.question
        ]
        world_qa = [
            QAItem(
                "What kind of cloth was used on the cart?",
                f"The children used {self.params.cloth} cloth to patch the cart seat.",
            ),
            QAItem(
                "Where did the cart go at the end?",
                "It rolled into the moonlit garden.",
            ),
        ]
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.world.history),
            prompts=[PROMPT],
            story_qa=questions,
            world_qa=world_qa,
            world=self.world,
        )


ASP_RULES = """
usable(C) :- charm(C).
usable_cloth(C) :- cloth(C).
valid(C,F) :- charm(C), cloth(F).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [fact("charm", charm) for charm in CHARMS]
        + [fact("cloth", cloth) for cloth in CLOTHES]
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--child")
    parser.add_argument("--helper")
    parser.add_argument("--charm", choices=tuple(CHARMS))
    parser.add_argument("--cloth", choices=tuple(CLOTHES))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAMES)
    helper = args.helper or rng.choice([name for name in NAMES if name != child])
    params = StoryParams(
        child=child,
        helper=helper,
        charm=args.charm or rng.choice(tuple(CHARMS)),
        cloth=args.cloth or rng.choice(tuple(CLOTHES)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    combos = asp_combos()
    expected = {(charm, cloth) for charm in CHARMS for cloth in CLOTHES}
    if combos != expected:
        raise StoryError("Python and ASP disagree about magical cloth combinations.")
    tested = 0
    for charm in CHARMS:
        for cloth in CLOTHES:
            sample = generate(
                StoryParams(
                    child="Pip",
                    helper="Mabel",
                    charm=charm,
                    cloth=cloth,
                )
            )
            check_sample(sample)
            tested += 1
    print(f"OK: {tested} story states; {len(combos)} Python/ASP-compatible pairs.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            samples = []
            for charm in CHARMS:
                for cloth in CLOTHES:
                    params = StoryParams(
                        child=args.child or "Pip",
                        helper=args.helper or "Mabel",
                        charm=charm,
                        cloth=cloth,
                        seed=args.seed,
                    )
                    samples.append(generate(params))
        else:
            samples = [
                generate(resolve_params(args, rng))
                for _ in range(args.n)
            ]

        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
