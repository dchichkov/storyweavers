#!/usr/bin/env python3
"""
A tiny storyworld about Dale at the wharf, where repetition helps a ghost
be seen, understood, and finally soothed.

The premise is a child on a foggy wharf who keeps hearing the same ghostly
knock. The tension is fear mixed with a repeating message. The turn is that
Dale notices the pattern, realizes the ghost is not trying to frighten anyone,
and answers back in a steady voice. The resolution is a calmer wharf, with the
repeated sound becoming a friendly signal instead of a scare.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Dale"
    place: str = "the wharf"
    time: str = "foggy evening"
    charm: str = "a small brass bell"
    light: str = "a lantern"
    spirit_name: str = "the dock ghost"
    repeated_phrase: str = "Please listen"
    emotion: str = "curious"


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    dale: Entity = field(default_factory=lambda: Entity("Dale", "child"))
    ghost: Entity = field(default_factory=lambda: Entity("the dock ghost", "ghost"))
    lantern_lit: bool = False
    bell_ring_count: int = 0
    knock_count: int = 0
    message_understood: bool = False
    ghost_calmer: bool = False
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


ASP_RULES = r"""
#show repeated/1.
#show soothed/0.

repeated(ghost_message) :- ghost_knock(K), K >= 2.
soothed :- repeated(ghost_message), answered_clearly.
"""


def asp_facts() -> str:
    import asp
    p = CURRENT_PARAMS
    return "\n".join([
        asp.fact("location", "wharf"),
        asp.fact("time", p.time),
        asp.fact("ghost_name", p.spirit_name),
        asp.fact("phrase", p.repeated_phrase),
        asp.fact("item", p.charm),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check_story(program: str) -> bool:
    import asp
    model = asp.one_model(program)
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    return ("repeated/1" in atoms) and ("soothed/0" in atoms)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world at a wharf with repetition.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name", default="Dale")
    ap.add_argument("--place", default="the wharf")
    ap.add_argument("--time", default="foggy evening")
    ap.add_argument("--charm", default="a small brass bell")
    ap.add_argument("--light", default="a lantern")
    ap.add_argument("--spirit-name", default="the dock ghost")
    ap.add_argument("--repeated-phrase", default="Please listen")
    ap.add_argument("--emotion", default="curious")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "the wharf"
    if "wharf" not in place.lower():
        raise StoryError("This world only makes sense at a wharf.")
    return StoryParams(
        seed=args.seed,
        name=args.name or "Dale",
        place=place,
        time=args.time or "foggy evening",
        charm=args.charm or "a small brass bell",
        light=args.light or "a lantern",
        spirit_name=args.spirit_name or "the dock ghost",
        repeated_phrase=args.repeated_phrase or "Please listen",
        emotion=args.emotion or "curious",
    )


def _lit_sentence(world: World) -> str:
    return f"{world.params.name} lit {world.params.light} so the fog would have a place to shine."


def _repetition_beats(world: World) -> None:
    p = world.params
    world.say(f"On a {p.time} at {p.place}, {p.name} walked slowly past the ropes and wet posts.")
    world.say(f"{p.name} carried {p.charm} in one hand and {p.light} in the other.")
    world.say(f"The wharf groaned once. Then it groaned again.")
    world.say(f"From the dark water came a knock, and then the same knock again.")
    world.bell_ring_count += 1
    world.knock_count += 2
    world.ghost.meters["near"] = 1.0
    world.dale.memes["unease"] = 1.0
    world.say(f'{p.spirit_name} whispered, "{p.repeated_phrase}."')
    world.say(f'Then it whispered again, "{p.repeated_phrase}."')


def _turn(world: World) -> None:
    p = world.params
    world.para()
    world.lantern_lit = True
    world.say(_lit_sentence(world))
    world.say(f"{p.name} did not run away. {p.name} listened for the pattern instead.")
    world.say(f'After the third knock, {p.name} said, "{p.repeated_phrase}."')
    world.say(f'After the fourth knock, {p.name} said it again: "{p.repeated_phrase}."')
    world.bell_ring_count += 2
    world.message_understood = True
    world.ghost.memes["relief"] = 1.0


def _resolution(world: World) -> None:
    p = world.params
    world.para()
    world.ghost_calmer = True
    world.ghost.memes["sadness"] = 0.0
    world.ghost.memes["calm"] = 1.0
    world.say(f"The ghost drifted closer, no longer trying to frighten anyone.")
    world.say(f'In a thin voice, it explained that the repeated words were a way to ask for help.')
    world.say(f"{p.name} tied the bell to the railing and rang it twice, slow and clear.")
    world.say(f"The ghost answered with one soft knock, then one softer knock.")
    world.say(f"By the end, the wharf was still foggy, but it felt friendly now.")
    world.say(f"{p.name} kept the lantern lit, and the dock ghost stayed near enough to be heard.")


def tell(params: StoryParams) -> World:
    world = World(params=params)
    world.facts.update(
        name=params.name,
        place=params.place,
        spirit_name=params.spirit_name,
        repeated_phrase=params.repeated_phrase,
        charm=params.charm,
        light=params.light,
    )
    world.say(f"{params.name} loved the wharf because the gulls sounded like tiny ghosts in the mist.")
    world.say(f"That night, {params.name} was feeling {params.emotion}.")
    _repetition_beats(world)
    _turn(world)
    _resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle ghost story for a child named {p.name} at {p.place} with a repeated message.",
        f"Tell a short story where {p.name} hears the same ghostly words more than once and answers bravely.",
        f"Write a foggy wharf story that uses repetition to turn a scare into a friendly moment.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question=f"Where did {p.name} hear the repeated knocking?",
            answer=f"{p.name} heard it at {p.place} during a {p.time}.",
        ),
        QAItem(
            question=f"What words did {p.spirit_name} repeat?",
            answer=f"The ghost repeated, '{p.repeated_phrase}.'",
        ),
        QAItem(
            question=f"What did {p.name} do when the message kept repeating?",
            answer=f"{p.name} listened carefully, answered in the same steady words, and helped the ghost feel calmer.",
        ),
        QAItem(
            question=f"How did the story end at the wharf?",
            answer=f"It ended with the lantern lit, the bell ringing softly, and {p.spirit_name} no longer trying to scare anyone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wharf?",
            answer="A wharf is a place by the water where boats can stop and people can walk near the edge.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying or doing something again and again. In stories, it can make a message feel important or help someone notice a pattern.",
        ),
        QAItem(
            question="Why can a lantern help at night?",
            answer="A lantern gives light in dark places, so people can see more clearly when the fog or night makes things hard to see.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world trace ---",
        f"dale.memes={world.dale.memes}",
        f"ghost.memes={world.ghost.memes}",
        f"lantern_lit={world.lantern_lit}",
        f"bell_ring_count={world.bell_ring_count}",
        f"knock_count={world.knock_count}",
        f"message_understood={world.message_understood}",
        f"ghost_calmer={world.ghost_calmer}",
    ])


CURATED = [
    StoryParams(name="Dale", place="the wharf", time="foggy evening", charm="a small brass bell", light="a lantern", spirit_name="the dock ghost", repeated_phrase="Please listen", emotion="curious"),
    StoryParams(name="Dale", place="the wharf", time="misty night", charm="a wooden whistle", light="a lantern", spirit_name="the pale sailor ghost", repeated_phrase="Come closer", emotion="brave"),
]


CURRENT_PARAMS = StoryParams()


def generate(params: StoryParams) -> StorySample:
    global CURRENT_PARAMS
    CURRENT_PARAMS = params
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    params = StoryParams()
    global CURRENT_PARAMS
    CURRENT_PARAMS = params
    program = asp_program("#show repeated/1.\n#show soothed/0.")
    try:
        import asp
        model = asp.one_model(program)
        atoms = {(sym.name, len(sym.arguments)) for sym in model}
        ok = ("repeated", 1) in atoms and ("soothed", 0) in atoms
    except Exception as ex:
        print(f"ASP unavailable or failed: {ex}")
        return 1
    if ok:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH: ASP rules did not derive the expected story shape.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show repeated/1.\n#show soothed/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        rng = random.Random(base_seed)
        for i in range(max(args.n, 1)):
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
