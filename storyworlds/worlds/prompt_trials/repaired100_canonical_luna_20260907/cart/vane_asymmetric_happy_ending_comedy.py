#!/usr/bin/env python3
"""The Crooked Vane: a lopsided weather vane finds a surprisingly happy job."""

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
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    revealed: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    helper: str = "Pip"
    material: str = "tin"
    roof: str = "barn"
    seed: int = 20260907


NAMES = ("Luna", "Pip", "Milo", "Nia", "Toby", "Zara")
MATERIALS = {
    "tin": ("tin", "bright"),
    "wood": ("wood", "warm"),
    "copper": ("copper", "shiny"),
}
ROOFS = {
    "barn": ("red barn", "chickens"),
    "shed": ("blue shed", "goats"),
    "clubhouse": ("treehouse", "children"),
}
PROMPT = (
    "Write a funny children's story about Luna and a helper repairing an asymmetric "
    "weather vane whose odd shape leads to a happy ending."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity(
                "hero", params.hero, "character",
                memes={"worry": 0.3, "curiosity": 0.8, "confidence": 0.5},
            ),
            "helper": Entity(
                "helper", params.helper, "character",
                memes={"worry": 0.2, "curiosity": 0.7, "confidence": 0.6},
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

    def say(
        self,
        speaker: str,
        text: str,
        *,
        listener: str = "",
        reveal: str = "",
    ):
        if speaker not in self.entities:
            raise StoryError("A story character must exist before speaking.")
        actor = self.entities[speaker]
        if reveal:
            if not listener or reveal not in actor.beliefs:
                raise StoryError("A character cannot share a fact they do not know.")
            self.entities[listener].beliefs[reveal] = actor.beliefs[reveal]
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(
            Event(
                kind="speech",
                text=f'"{text}" {actor.label} {verb}.',
                speaker=speaker,
                listener=listener,
                revealed=reveal,
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(
                    question=event.question,
                    answer=f"{event.cause} {event.result}",
                )
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    question="What does a weather vane show?",
                    answer="A weather vane shows which way the wind is blowing.",
                ),
                QAItem(
                    question="Why can an asymmetric vane still work?",
                    answer="It can still work if its pivot is balanced and its broad tail catches the wind.",
                ),
            ],
            world=self,
        )


def validate_params(params: StoryParams):
    if params.material not in MATERIALS:
        raise StoryError("Choose tin, wood, or copper for the vane.")
    if params.roof not in ROOFS:
        raise StoryError("Choose the barn, shed, or clubhouse roof.")
    if params.hero == params.helper:
        raise StoryError("The two speakers must have different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name) for name in (params.hero, params.helper)):
        raise StoryError("Use simple capitalized names, such as Luna and Pip.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    material, shine = MATERIALS[params.material]
    roof, animals = ROOFS[params.roof]
    world.entities["vane"] = Entity(
        "vane",
        f"the {shine} {material} vane",
        "weather_vane",
        location="workbench",
        meters={"tail_area": 3.0, "nose_area": 1.0, "pivot_friction": 0.0, "height": 0.0},
        memes={"pride": 0.8, "usefulness": 0.2},
        beliefs={"shape": "asymmetric"},
    )
    world.entities["roof"] = Entity(
        "roof",
        f"the {roof} roof",
        "place",
        location="farm",
        meters={"height": 4.0},
        memes={},
        beliefs={"nearby": animals},
    )
    world.entities["wind"] = Entity(
        "wind",
        "the west wind",
        "force",
        location="sky",
        meters={"speed": 2.0, "direction": 270.0},
        memes={},
    )
    world.entities["sign"] = Entity(
        "sign",
        "the welcome sign",
        "sign",
        location="ground",
        meters={"width": 1.5, "height": 0.8},
        memes={},
    )
    return world


def install_vane(world: World):
    vane = world.entities["vane"]
    roof = world.entities["roof"]
    if vane.meters["pivot_friction"] > 0:
        raise StoryError("The vane must have a free pivot before installation.")
    if vane.meters["height"] <= 0:
        raise StoryError("The vane needs a raised support before it can read the wind.")
    vane.location = roof.location
    vane.memes["usefulness"] = 1.0


def test_vane(world: World):
    vane = world.entities["vane"]
    wind = world.entities["wind"]
    if vane.location != world.entities["roof"].location:
        raise StoryError("The vane must be on the roof before testing it.")
    if vane.meters["pivot_friction"] > 0:
        raise StoryError("A stuck pivot prevents the vane from turning.")
    if vane.meters["tail_area"] <= vane.meters["nose_area"]:
        raise StoryError("The tail must catch more wind than the nose.")
    vane.beliefs["direction"] = "west"
    wind.meters["direction"] = 270.0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = world.entities["hero"].label
    p = world.entities["helper"].label
    vane = world.entities["vane"]
    roof = world.entities["roof"]
    sign = world.entities["sign"]
    material, shine = MATERIALS[params.material]
    roof_name, animals = ROOFS[params.roof]

    world.narrate(
        "beginning",
        f"{h} found a {shine} {material} weather vane on a workbench beside the {roof_name}. "
        f"It had a long arrow nose, a very wide tail, and a tiny rooster wearing one boot. "
        f"The vane was cheerfully asymmetric.",
    )
    world.say("hero", "It looks like the rooster fell off and took the tail with him.")
    world.say("helper", "That is not a repair plan. That is an insult with feathers.")
    world.say("hero", "Can we put it on the roof anyway?")
    world.say("helper", "Only if it can tell the wind from a passing chicken.")
    world.narrate(
        "problem",
        f"The vane leaned so far to one side that its arrow pointed at a bucket while the wind "
        f"blew from the west. The nearby {animals} clucked as if they had opinions.",
        question="Why could the vane not be trusted yet?",
        cause="Its asymmetric body was leaning toward a bucket instead of turning freely with the west wind.",
        result="Luna and Pip needed to understand the odd shape before putting it on the roof.",
    )

    world.entities["hero"].beliefs["shape"] = "the tail is broad and the nose is narrow"
    world.say(
        "hero",
        "The tail is broad, but the nose is narrow. The wind should push the broad part around.",
        listener="helper",
        reveal="shape",
    )
    world.say("helper", "Then why is it pointing at that bucket?")
    world.say("hero", "The pivot is rubbing against the crooked hole.")
    world.say("helper", "So the vane is not confused. It is being tickled in the wrong place.")
    world.narrate(
        "discovery",
        f"They lifted the vane and found a burr inside the pivot hole. {h} smoothed it with a file, "
        f"while {p} held the tail steady. The rooster's one boot squeaked.",
        question="What stopped the vane from turning correctly?",
        cause="A burr rubbed inside the pivot hole and held the uneven vane in place.",
        result="Luna filed the burr away so the broad tail could catch the wind.",
    )

    world.say("hero", "Should we make both sides exactly the same?")
    world.say("helper", "Then it might look tidy but never know which way to turn.")
    world.say("hero", "So the lopsided part is useful?")
    world.say("helper", "Useful and dramatic. Like a chicken in a hat.")
    vane.meters["pivot_friction"] = 0.0
    vane.meters["height"] = 1.0
    vane.beliefs["balanced"] = "balanced at the pivot despite its uneven outline"
    world.entities["helper"].beliefs["balanced"] = vane.beliefs["balanced"]
    world.narrate(
        "repair",
        f"They balanced the vane at its pivot without changing its funny shape. The long tail "
        f"now had three times the wind-catching area of the little arrow nose.",
        question="Why did they keep the vane asymmetric?",
        cause="Its broad tail needed to catch more wind than its narrow nose.",
        result="They repaired the pivot but kept the uneven shape that helped the vane turn.",
    )

    world.say("hero", "Let's put it on the roof.")
    world.say("helper", "If it points at the moon, we are blaming the rooster.")
    install_vane(world)
    test_vane(world)
    world.narrate(
        "turn",
        f"They raised the repaired vane onto the {roof_name}. A west breeze pushed its broad tail, "
        f"and the arrow swung around to point east. The rooster spun once and looked surprised.",
        question="How did they know the repair worked?",
        cause="The free pivot let the broad tail catch the west breeze and swing the arrow around.",
        result="The arrow pointed east, showing the wind came from the west.",
    )
    world.say("hero", "It says the wind is from the west!")
    world.say("helper", "And the rooster says it wants a second boot.")
    world.entities["sign"].location = roof.location
    world.narrate(
        "happy_ending",
        f"Everyone cheered, including the {animals}, who had been waiting for a useful forecast. "
        f"Then the wind turned the vane toward the welcome sign, and the one-boot rooster pointed "
        f"straight at a basket of fresh rolls. {h} and {p} followed its beak and shared the snack "
        f"with the whole farm. The happy ending was lopsided, delicious, and perfectly on purpose.",
        question="What happy ending followed the successful repair?",
        cause="The working vane helped them notice the wind and led them toward the basket of fresh rolls.",
        result="Luna and Pip shared the rolls with everyone while the asymmetric vane spun proudly above them.",
    )

    sample = world.sample()
    check_sample(sample)
    return sample


def check_ending(sample: StorySample):
    world = sample.world
    vane = world.entities["vane"]
    if vane.location != world.entities["roof"].location:
        raise StoryError("The repaired vane must end on the chosen roof.")
    if vane.beliefs.get("direction") != "west":
        raise StoryError("The ending must record the west wind.")
    if vane.meters["pivot_friction"] != 0 or vane.meters["tail_area"] <= vane.meters["nose_area"]:
        raise StoryError("The vane must turn freely with a broad wind-catching tail.")
    if world.entities["sign"].location != world.entities["roof"].location:
        raise StoryError("The happy ending needs the shared celebration at the destination.")


def check_sample(sample: StorySample):
    check_ending(sample)
    speech = [event for event in sample.world.history if event.kind == "speech"]
    if len(speech) < 12:
        raise StoryError("The story needs a sustained back-and-forth exchange.")
    for key in ("hero", "helper"):
        if sum(event.speaker == key for event in speech) < 5:
            raise StoryError("Both characters need several spoken turns.")
    if not any(event.revealed for event in speech):
        raise StoryError("Dialogue must pass useful knowledge between characters.")
    if len(sample.story_qa) < 4:
        raise StoryError("The story needs several causal questions and answers.")
    if any(not item.answer.strip() or len(item.answer.split()) < 6 for item in sample.story_qa):
        raise StoryError("Story-grounded answers must be complete explanations.")
    if "asymmetric" not in sample.story.lower() or "vane" not in sample.story.lower():
        raise StoryError("The story must visibly include the seed words.")


ASP_RULES = """
usable(P) :- pivot_free(P), tail_larger(P).
turns(P,D) :- usable(P), wind(P,D).
happy(P) :- turns(P,D), shared_rolls(P).
#show usable/1.
#show turns/2.
#show happy/1.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        [
            fact("pivot_free", "vane"),
            fact("tail_larger", "vane"),
            fact("wind", "vane", "west"),
            fact("shared_rolls", "vane"),
        ]
    )


def asp_state() -> set[tuple]:
    from asp import atoms, one_model

    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return {
        ("usable", args)
        for args in atoms(model, "usable")
    } | {
        ("turns", args)
        for args in atoms(model, "turns")
    } | {
        ("happy", args)
        for args in atoms(model, "happy")
    }


def python_state() -> set[tuple]:
    return {
        ("usable", ("vane",)),
        ("turns", ("vane", "west")),
        ("happy", ("vane",)),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260907)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--material", choices=tuple(MATERIALS))
    parser.add_argument("--roof", choices=tuple(ROOFS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    helper_choices = [name for name in NAMES if name != hero]
    helper = args.helper or rng.choice(helper_choices)
    params = StoryParams(
        hero=hero,
        helper=helper,
        material=args.material or rng.choice(tuple(MATERIALS)),
        roof=args.roof or rng.choice(tuple(ROOFS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if python_state() != asp_state():
        raise StoryError("Python and ASP disagree about the usable vane state.")
    tested = 0
    for hero in NAMES[:3]:
        for helper in NAMES[3:]:
            for material in MATERIALS:
                for roof in ROOFS:
                    sample = generate(
                        StoryParams(
                            hero=hero,
                            helper=helper,
                            material=material,
                            roof=roof,
                        )
                    )
                    check_sample(sample)
                    tested += 1
    print(f"OK: {tested} story states; Python and ASP agree on the vane rules.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""):
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
            print(json.dumps(sorted(asp_state())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params_list = []
            for material in MATERIALS:
                for roof in ROOFS:
                    copied = argparse.Namespace(**vars(args))
                    copied.material = material
                    copied.roof = roof
                    params_list.append(resolve_params(copied, rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(
                json.dumps(
                    payload[0] if len(payload) == 1 else payload,
                    ensure_ascii=False,
                    indent=2,
                )
            )
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
