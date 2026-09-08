#!/usr/bin/env python3
"""A small bridge, a small misunderstanding, and the chitter that mends it."""

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
    kind: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    speaker: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Milo"
    bird: str = "Pip"
    bridge_material: str = "wooden"
    repair: str = "peg"
    seed: int = 777


NAMES = ("Luna", "Milo", "Nia", "Oren", "Tess", "Pia")
BIRDS = ("Pip", "Chirp", "Dot", "Wren")
MATERIALS = {
    "wooden": "thin wooden bridge",
    "rope": "little rope bridge",
    "paper": "folded paper bridge",
}
REPAIRS = {
    "peg": "a peg",
    "knot": "a knot",
    "strip": "a paper strip",
}
PROMPT = (
    "Write a slice-of-life children's story about Luna and a friend repairing "
    "a small bridge after a misunderstanding, with a bird's chitter helping them reconcile."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity(
                "hero", params.hero, "character", "garden_path",
                memes={"hurt": 0.0, "trust": 0.7},
            ),
            "friend": Entity(
                "friend", params.friend, "character", "garden_path",
                memes={"hurt": 0.0, "trust": 0.7},
            ),
            "bird": Entity(
                "bird", params.bird, "bird", "bridge_rail",
                memes={"calm": 0.4},
            ),
            "bridge": Entity(
                "bridge", MATERIALS[params.bridge_material], "bridge",
                "over_puddle", meters={"gap": 2.0, "strength": 1.0, "tested": 0.0},
            ),
            "repair": Entity(
                "repair", REPAIRS[params.repair], "tool", "bench",
                meters={"available": 1.0},
            ),
            "basket": Entity(
                "basket", "the berry basket", "basket", "near_bridge",
                meters={"delivered": 0.0},
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
            raise StoryError("A conversation used an unknown speaker.")
        self.history.append(
            Event(
                kind="speech",
                text=f'{self.entities[speaker].label} said, "{text}"',
                speaker=speaker,
                state=self.snapshot(),
            )
        )


def validate_params(params: StoryParams):
    if params.bridge_material not in MATERIALS:
        raise StoryError("Choose a known bridge material.")
    if params.repair not in REPAIRS:
        raise StoryError("Choose a known repair.")
    if len({params.hero, params.friend, params.bird}) != 3:
        raise StoryError("The two children and the bird need different names.")
    for name in (params.hero, params.friend, params.bird):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def repair_bridge(world: World):
    bridge = world.entities["bridge"]
    supply = world.entities["repair"]
    if supply.meters["available"] < 1:
        raise StoryError("The repair piece has already been used.")
    if world.entities["hero"].beliefs.get("shared_plan") != "repair_together":
        raise StoryError("The children must agree on a shared repair first.")
    supply.meters["available"] = 0
    bridge.meters["strength"] = 2.0
    bridge.meters["tested"] = 0.0


def test_bridge(world: World) -> bool:
    bridge = world.entities["bridge"]
    bridge.meters["tested"] += 1
    if bridge.meters["strength"] >= 2.0:
        world.entities["basket"].location = "far_bank"
        world.entities["basket"].meters["delivered"] = 1.0
        return True
    return False


def check_ending(world: World):
    if world.entities["bridge"].meters["strength"] < 2.0:
        raise StoryError("The bridge was not actually repaired.")
    if world.entities["basket"].meters["delivered"] != 1.0:
        raise StoryError("The berry basket must reach the far bank.")
    if any(
        world.entities[key].memes["trust"] < 1.0
        for key in ("hero", "friend")
    ):
        raise StoryError("The reconciliation was not completed.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = world.entities["hero"].label
    f = world.entities["friend"].label
    b = world.entities["bird"].label
    bridge = world.entities["bridge"].label
    repair = world.entities["repair"].label

    world.narrate(
        "beginning",
        f"{h} carried a basket of berries to the puddle behind the community garden. "
        f"{f} was waiting there beside a {bridge}, and {b} watched from its rail.",
    )
    world.say("hero", f"I brought the berries. Can we take them across?")
    world.say("friend", "The bridge is wobbly. I thought you were going to fix it.")
    world.say("hero", "I thought you said you would fix it.")
    world.entities["hero"].memes["hurt"] = 1.0
    world.entities["friend"].memes["hurt"] = 1.0

    world.narrate(
        "misunderstanding",
        f"The two children looked at the bridge instead of at each other. "
        f"From the rail came a quick, bright chitter: {b} chittered, chitter-chit.",
        question="Why did the children stop at the puddle?",
        cause=f"The {bridge} was too weak to carry the berry basket safely.",
        result="They needed to repair it before making the delivery.",
    )
    world.say("friend", "That sounds like Pip is telling us something.")
    world.say("hero", "Maybe the bird is saying we should stop blaming each other.")
    world.say("friend", "I did not mean to leave the work for you.")
    world.say("hero", "I did not mean to leave it for you either.")

    world.entities["hero"].beliefs["shared_plan"] = "repair_together"
    world.entities["friend"].beliefs["shared_plan"] = "repair_together"
    world.entities["hero"].memes["hurt"] = 0.5
    world.entities["friend"].memes["hurt"] = 0.5

    world.narrate(
        "reconciliation",
        f"{h} picked up {repair} from the bench. {f} held the bridge steady while "
        f"{h} fitted the repair piece beneath its loose middle.",
        question="How did the children begin to reconcile?",
        cause="They admitted that both had misunderstood the plan.",
        result="They chose to hold and repair the bridge together.",
    )
    world.say("friend", "You hold this side, and I will press the middle.")
    world.say("hero", "Together?")
    world.say("friend", "Together. Then we can both carry the basket.")
    world.say("hero", "All right. I am glad you told me.")

    repair_bridge(world)
    world.narrate(
        "repair",
        f"The {bridge} gave a small wooden click as {repair} settled into place. "
        f"It still crossed the puddle, but now it felt firm beneath their hands.",
        question="What changed in the bridge?",
        cause=f"The children used {repair} beneath its loose middle.",
        result="The bridge became strong enough for the basket.",
    )
    world.say("friend", "Let us test it with one empty step first.")
    world.say("hero", "Then we will take the berries slowly.")

    if not test_bridge(world):
        raise StoryError("The repaired bridge failed its test.")
    world.narrate(
        "delivery",
        f"They stepped onto the bridge together. It held. {h} and {f} carried the "
        f"berry basket to the far bank without spilling a single berry.",
        question="How did they know the repair worked?",
        cause="They tested the bridge before carrying the full basket.",
        result="It held their careful steps, so they delivered the berries safely.",
    )
    world.say("friend", "You take the left handle.")
    world.say("hero", "And you take the right one. No guessing this time.")
    world.say("friend", "No guessing. We ask.")
    world.say("hero", f"Thank you, {f}.")
    world.say("friend", f"Thank you, {h}.")

    world.entities["hero"].memes["hurt"] = 0.0
    world.entities["friend"].memes["hurt"] = 0.0
    world.entities["hero"].memes["trust"] = 1.0
    world.entities["friend"].memes["trust"] = 1.0
    world.entities["bird"].memes["calm"] = 1.0

    world.narrate(
        "ending",
        f"On the way back, {b} gave one last soft chitter from the rail. "
        f"{h} and {f} smiled at each other, already discussing what they would repair next.",
    )

    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history
            if event.question
        ],
        world_qa=[
            QAItem(
                "What is the purpose of reconciliation in this story?",
                "Reconciliation helps the children repair their misunderstanding by listening, apologizing, and making a shared plan.",
            ),
            QAItem(
                "What does the bird's chitter do?",
                "The bird's chitter gives the children a gentle pause that helps them notice their disagreement and talk honestly.",
            ),
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    check_ending(sample.world)
    speeches = [event for event in sample.world.history if event.kind == "speech"]
    if len(speeches) < 12:
        raise StoryError("The story needs a sustained back-and-forth conversation.")
    if not any(event.speaker == "hero" for event in speeches):
        raise StoryError("The hero must speak.")
    if not any(event.speaker == "friend" for event in speeches):
        raise StoryError("The friend must speak.")
    if "chitter" not in sample.story.lower():
        raise StoryError("The story must include the bird's chitter.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs grounded questions and answers.")


ASP_RULES = """
repairable(Material,Repair) :- material(Material), repair(Repair).
valid(Material,Repair) :- repairable(Material,Repair).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact

    facts = [fact("material", key) for key in MATERIALS]
    facts += [fact("repair", key) for key in REPAIRS]
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    model = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(model, "valid"))


def verify():
    expected = {(material, repair) for material in MATERIALS for repair in REPAIRS}
    if asp_combos() != expected:
        raise StoryError("Python and ASP disagree about valid bridge choices.")
    count = 0
    for material in MATERIALS:
        for repair in REPAIRS:
            sample = generate(
                StoryParams(
                    bridge_material=material,
                    repair=repair,
                    hero="Luna",
                    friend="Milo",
                    bird="Pip",
                )
            )
            check_sample(sample)
            count += 1
    print(f"OK: {count} reconciliation stories; ASP parity confirmed.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--bird")
    parser.add_argument("--bridge-material", choices=tuple(MATERIALS))
    parser.add_argument("--repair", choices=tuple(REPAIRS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    friend_choices = [name for name in NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    bird_choices = [name for name in BIRDS if name not in {hero, friend}]
    bird = args.bird or rng.choice(bird_choices)
    params = StoryParams(
        hero=hero,
        friend=friend,
        bird=bird,
        bridge_material=args.bridge_material or rng.choice(tuple(MATERIALS)),
        repair=args.repair or rng.choice(tuple(REPAIRS)),
        seed=args.seed,
    )
    validate_params(params)
    return params


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
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            combinations = [
                (material, repair)
                for material in MATERIALS
                for repair in REPAIRS
            ]
            samples = [
                generate(
                    StoryParams(
                        hero=args.hero or "Luna",
                        friend=args.friend or "Milo",
                        bird=args.bird or "Pip",
                        bridge_material=material,
                        repair=repair,
                        seed=args.seed,
                    )
                )
                for material, repair in combinations
            ]
        else:
            samples = [
                generate(resolve_params(args, rng))
                for _ in range(args.n)
            ]

        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2))
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
