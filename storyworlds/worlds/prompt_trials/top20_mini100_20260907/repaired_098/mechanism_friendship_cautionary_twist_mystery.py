#!/usr/bin/env python3
"""A child-facing mystery about a mechanism, friendship, caution, and a twist."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Thing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    setting: str = "workshop"
    friend_a: str = "Mina"
    friend_b: str = "Toby"
    mechanism_name: str = "clockwork door"
    missing_piece: str = "a silver gear"
    caution: str = "do not pull the red lever"
    twist: str = "the door was helping to keep something safe inside"
    route: str = "clue_first"


@dataclass(frozen=True)
class MechanismCase:
    mystery: str
    worry: str
    first_test: str
    first_test_result: str
    clue: str
    cause: str
    friend_action: str
    fix: str
    lesson: str
    ending: str


@dataclass
class World:
    place: Place
    friend_a: Thing
    friend_b: Thing
    mechanism: Thing
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CASE_MAP = {
    "clockwork_lock": MechanismCase(
        mystery="the clockwork door kept clicking open by itself",
        worry="little tools might roll out into the hallway",
        first_test="checked the latch by hand and counted three turns of the key",
        first_test_result="the latch stayed shut, so the key was not the problem",
        clue="a string of tiny chalk marks climbed from the floor to the side panel",
        cause="a dangling ribbon had been brushing the release peg whenever the fan turned",
        friend_action="waited beside the mechanism and watched the ribbon instead of yanking anything",
        fix="tied the ribbon back, oiled the peg, and tested the door three calm times",
        lesson="a careful friend looks twice before blaming the loudest part",
        ending="the door slept shut while the ribbon hung still like a quiet white snake",
    ),
    "bell_wheel": MechanismCase(
        mystery="the bell wheel rang whenever nobody touched it",
        worry="the sleeping kittens in the corner kept jumping awake",
        first_test="spun the wheel with a pencil and listened for a loose clink",
        first_test_result="the wheel sounded normal, so the bell itself was not broken",
        clue="dust on the floor curved in a perfect line under the window",
        cause="sunlight had warmed a hanging spoon that nudged the wheel when the curtain moved",
        friend_action="stood by the window and held the curtain still while the sound was tested again",
        fix="moved the spoon, tied the curtain higher, and gave the kittens a nap-time blanket",
        lesson="a mystery can hide in an ordinary shadow and still be solved with patience",
        ending="the bell wheel stayed quiet above the kittens' soft, round backs",
    ),
    "tin_bridge": MechanismCase(
        mystery="a tiny tin bridge rattled like teeth in the wall",
        worry="the bridge might crack and drop the seed cart",
        first_test="pressed each bolt with a wooden spoon and counted the shakes",
        first_test_result="the bolts were tight, so the bridge was not loosening",
        clue="one bolt had a smear of blue paint that matched the toy cart",
        cause="the toy cart had been bumping the wall through a hidden gap beside the shelf",
        friend_action="held the cart back while the other friend followed the sound to the gap",
        fix="patched the gap, parked the cart on a mat, and checked that the bridge stopped rattling",
        lesson="sometimes the thing that seems broken is only being bumped by something nearby",
        ending="the tin bridge rested still while the toy cart waited politely on its mat",
    ),
    "spring_gate": MechanismCase(
        mystery="the spring gate kept popping open at dusk",
        worry="the puppy could wander outside before supper",
        first_test="hooked the gate three times and watched the spring stretch",
        first_test_result="the spring pulled well, so the problem was not the spring itself",
        clue="a trail of seed crumbs led from the garden path to the latch",
        cause="a hungry mouse had been brushing the latch while chasing crumbs under the gate",
        friend_action="kept the puppy inside and followed the crumbs without stepping on them",
        fix="swept the crumbs away, raised the latch, and added a small guard plate",
        lesson="caution means protecting everyone before chasing the answer",
        ending="the spring gate stayed closed while the puppy ate supper by the hearth",
    ),
    "music_box": MechanismCase(
        mystery="the music box played only one lonely note",
        worry="the birthday song would sound broken",
        first_test="turned the key and listened for the tune to begin",
        first_test_result="the key wound properly, so the spring was not the whole trouble",
        clue="one bright peg on the drum had a smear of jam",
        cause="sweet jam had glued the peg enough to stop the melody from moving on",
        friend_action="blushed, confessed the sticky accident, and helped clean the drum carefully",
        fix="washed the peg, dried it, and wound the tune until the full song danced out",
        lesson="a friend can tell the truth and still help fix the mess",
        ending="the music box sang a whole little song while two friends smiled at the table",
    ),
}

ROUTES = (
    "clue_first",
    "dialogue_first",
    "caution_first",
    "twist_first",
    "friend_first",
    "question_first",
)

PLACE_MAP = {
    "workshop": Place(name="the little workshop", kind="workshop"),
    "garden shed": Place(name="the garden shed", kind="shed"),
    "attic room": Place(name="the attic room", kind="attic"),
}


ASP_RULES = r"""
friendship(X,Y) :- friend(X), friend(Y), X != Y.
cautious_story :- caution(_), mechanism(_).
twist_story :- twist(_), solved(_).
solved_story :- mechanism(_), solved(mechanism).
"""


def mechanism_id(text: str) -> str:
    return "m_" + "".join(ch if ch.isalnum() else "_" for ch in text.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("friend", "mina"),
        asp.fact("friend", "toby"),
        asp.fact("mechanism", "mechanism"),
        asp.fact("caution", "do_not_pull_the_red_lever"),
        asp.fact("twist", "hidden_safety_role"),
        asp.fact("solved", "mechanism"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show friendship/2. #show cautious_story/0. #show twist_story/0. #show solved_story/0."))
    facts = set(str(a) for a in model)
    expected = {"friendship(mina,toby)", "friendship(toby,mina)", "cautious_story", "twist_story", "solved_story"}
    if facts == expected:
        print("OK: clingo gate matches python reasoning.")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(facts))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(v) for v in (
        params.seed, params.setting, params.friend_a, params.friend_b,
        params.mechanism_name, params.missing_piece, params.caution, params.twist, params.route
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.setting not in PLACE_MAP:
        raise StoryError(f"Unknown setting: {params.setting}")
    if not params.mechanism_name.strip():
        raise StoryError("mechanism_name cannot be empty")
    case_key = None
    for key, case in CASE_MAP.items():
        if params.missing_piece in case.cause or params.missing_piece in case.mystery:
            case_key = key
            break
    if case_key is None:
        case_key = "clockwork_lock"
    return World(
        place=Place(name=PLACE_MAP[params.setting].name, kind=PLACE_MAP[params.setting].kind),
        friend_a=Thing(name=params.friend_a, kind="friend"),
        friend_b=Thing(name=params.friend_b, kind="friend"),
        mechanism=Thing(name=params.mechanism_name, kind="mechanism"),
        facts={"case_key": case_key},
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    case = CASE_MAP[world.facts["case_key"]]
    a, b, place, mech = world.friend_a, world.friend_b, world.place, world.mechanism
    a.memes["curiosity"] = 1
    b.memes["caution"] = 1
    world.say(
        f"In {place.name}, {mech.name} made the day feel odd. {case.mystery.capitalize()}, and {a.name} and {b.name} both noticed it at once."
    )
    world.say(
        rng.choice([
            f'"We should not touch the red lever," {b.name} said. "{params.caution.capitalize()}."',
            f'{b.name} whispered, "Let us be careful first." {a.name} nodded. "{params.caution.capitalize()}."',
            f'"We can solve this without rushing," {a.name} said. {b.name} answered, "And without pulling anything dangerous."',
        ])
    )
    world.para()
    world.say(f"First, {a.name} {case.first_test}.")
    world.say(f"That did not solve it: {case.first_test_result}.")
    world.say(f"Then the friends noticed that {case.clue}.")
    world.say(f"It turned out that {case.cause}.")
    world.para()
    world.say(
        rng.choice([
            f'"I thought the mechanism was broken," {a.name} admitted.',
            f'"I was ready to blame the loud part," {b.name} said.',
            f'"That was the twist," {a.name} said, smiling in surprise.',
        ])
    )
    world.say(
        rng.choice([
            f'"No," {b.name} replied, "it was protecting us all along."',
            f'"A mystery can have a kinder answer than it first looks," said {b.name}.',
            f'"Friendship means checking together," {b.name} said, and {a.name} agreed.',
        ])
    )
    world.say(f"Together they {case.friend_action} and then {case.fix}.")
    world.para()
    world.say(
        f"In the end, {case.ending}. {case.lesson.capitalize()}, and that was the safest kind of victory."
    )
    world.facts.update(case=case, solved=True)


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        f"Write a child-facing mystery story set in {world.place.name} about {world.mechanism.name}.",
        f"Include a cautious back-and-forth dialogue between {world.friend_a.name} and {world.friend_b.name} that helps solve the problem.",
        f"End with the twist that {case.cause} and the final image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    return [
        QAItem(
            question=f"What was strange about {world.mechanism.name} in the story?",
            answer=f"{case.mystery.capitalize()}"
        ),
        QAItem(
            question="How did the friends avoid a risky mistake?",
            answer=f"They listened, talked, and followed the caution that {world.mechanism.name} should not be rushed or pulled the wrong way."
        ),
        QAItem(
            question="What was the twist in the mystery?",
            answer=f"The surprising truth was that {case.cause}."
        ),
        QAItem(
            question="How did the friends fix the problem?",
            answer=f"They {case.fix}."
        ),
        QAItem(
            question="What lesson did the ending give?",
            answer=f"{case.lesson.capitalize()}."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a machine or moving system made of parts that work together."
        ),
        QAItem(
            question="Why is caution important around a mechanism?",
            answer="Caution helps people avoid hurting themselves or breaking something while they figure out what is happening."
        ),
        QAItem(
            question="Can friends solve a mystery better by talking to each other?",
            answer="Yes. Talking helps them share clues, test ideas, and choose a safe next step together."
        ),
        QAItem(
            question="What makes a twist in a mystery story?",
            answer="A twist is a surprising answer that changes what the characters thought was true."
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery about a mechanism, friendship, and a cautionary twist.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--setting", choices=sorted(PLACE_MAP))
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    case = rng.choice(list(CASE_MAP.values()))
    return StoryParams(
        seed=args.seed,
        setting=args.setting or rng.choice(sorted(PLACE_MAP)),
        friend_a=rng.choice(["Mina", "Lena", "Omar", "Toby"]),
        friend_b=rng.choice(["Toby", "Nia", "Pip", "Jules"]),
        mechanism_name=rng.choice(["clockwork door", "bell wheel", "tin bridge", "spring gate", "music box"]),
        missing_piece=rng.choice(["a silver gear", "a tiny clamp", "a blue pin", "a little spring", "a jam spot"]),
        caution="do not pull the red lever",
        twist=case.cause,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.place, world.friend_a, world.friend_b, world.mechanism):
        lines.append(f"{entity.name}: meters={entity.meters} memes={getattr(entity, 'memes', {})}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show friendship/2. #show cautious_story/0. #show twist_story/0. #show solved_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show friendship/2. #show cautious_story/0. #show twist_story/0. #show solved_story/0."))
        print(sorted(set(str(a) for a in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
