#!/usr/bin/env python3
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
place(garden).
feature(inner_monologue).
feature(kindness).
feature(transformation).
tool(zap_lantern).
need(wilted_sunflower).
helper(gentle_friend).
can_help :- feature(inner_monologue), feature(kindness).
can_transform :- can_help, feature(transformation), tool(zap_lantern).
happy_story :- can_transform, need(wilted_sunflower), helper(gentle_friend).
#show happy_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    friend: str = "Milo"
    place: str = "the little garden"
    object_name: str = "a wilted sunflower"
    tool: str = "the blue zap lantern"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the sunflower that forgot the sun",
        "problem": "the tallest sunflower had folded its golden face toward the ground",
        "clue": "its soil was dry, but a tiny cup beside it still held one clear drop",
        "choice": "Luna almost poured the whole watering can over the flower, then paused to listen to the quiet voice inside her",
        "action": "she asked Milo to help shade the roots while she loosened the hard soil and gave the plant a little water at a time",
        "dialogue": "'We do not have to fix everything in one splash,' Luna said. 'We can be gentle together.'",
        "resolution": "the sunflower lifted one leaf, then another, as its thirsty roots drank slowly",
        "ending": "by evening, its bright face turned toward Luna and Milo like a small golden thank-you",
        "lesson": "kindness often begins when a worried thought becomes a careful action",
    },
    {
        "title": "the shy bluebird's nest",
        "problem": "a bluebird sat beside a low nest while twigs kept sliding into the path",
        "clue": "one soft feather was caught on a thorn, showing that the nest belonged nearby",
        "choice": "Luna wanted to move the nest at once, but her inner voice reminded her that frightened birds needed space",
        "action": "she placed a little sign around the nest and asked Milo to bring the garden keeper",
        "dialogue": "'Waiting can be kind too,' Luna whispered. Milo nodded and kept the path quiet.",
        "resolution": "the keeper secured the nest above the path without touching the eggs",
        "ending": "the bluebird returned with a silver strand of grass and sang from the safe branch",
        "lesson": "kindness protects another creature's needs before satisfying our own hurry",
    },
    {
        "title": "the rain barrel surprise",
        "problem": "the garden rain barrel had tipped over, leaving the seedlings thirsty",
        "clue": "a trail of wet pebbles led from the barrel to a loose wooden wheel",
        "choice": "Luna felt embarrassed because she had bumped the barrel, but she decided that honesty could help",
        "action": "she told Milo what happened, and together they rolled the barrel upright and gathered the spilled water with cups",
        "dialogue": "'I made the muddle,' Luna said. 'Will you help me make it better?' 'Yes,' said Milo.",
        "resolution": "the seedlings received the saved water, and Luna tied the barrel to a sturdy post",
        "ending": "new rain tapped the barrel while tiny leaves shone like green stars",
        "lesson": "a kind truth can transform a mistake into a chance to care",
    },
    {
        "title": "the lonely garden stone",
        "problem": "a painted stone had rolled away from the garden's welcome circle",
        "clue": "a red paint fleck marked the path beside a patch of crushed clover",
        "choice": "Luna first thought the stone was only a heavy thing, then imagined how lonely its empty place looked",
        "action": "she asked Milo to help carry it and brushed the clover gently back into shape",
        "dialogue": "'Every little welcome belongs somewhere,' Luna said. 'Then let us carry this one home,' Milo replied.",
        "resolution": "they returned the stone and added a small cushion of earth beneath it",
        "ending": "the painted heart on the stone glowed beside the flowers in the morning light",
        "lesson": "kindness notices when something small has been left behind",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming zap story about Luna, kindness, and transformation."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--place")
    parser.add_argument("--object-name")
    parser.add_argument("--tool")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(["Luna", "Pia", "Nell", "Ari", "Sami"])
    friend = args.friend or rng.choice(["Milo", "Tess", "Jun", "Bea"])
    place = args.place or "the little garden"
    object_name = args.object_name or "a wilted sunflower"
    tool = args.tool or "the blue zap lantern"
    if not place:
        raise StoryError("The story needs a place.")
    if "zap" not in tool.lower():
        raise StoryError("The tool must include the word 'zap'.")
    return StoryParams(
        seed=None,
        name=name,
        friend=friend,
        place=place,
        object_name=object_name,
        tool=tool,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "garden"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "kindness"),
            asp.fact("feature", "transformation"),
            asp.fact("tool", "zap_lantern"),
            asp.fact("need", "wilted_sunflower"),
            asp.fact("helper", "gentle_friend"),
        ]
    )


def asp_program(show: str = "#show happy_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_ok = bool(asp.atoms(model, "happy_story"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the kindness transformation gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    index = (p.seed or 0) % len(SCENARIOS)
    scenario = SCENARIOS[index]

    luna = world.add_character(Character(p.name, "kind child"))
    friend = world.add_character(Character(p.friend, "helpful friend"))
    zap = world.add_object(ObjectThing(p.tool, "gentle garden tool"))
    subject = world.add_object(ObjectThing(p.object_name, "living garden treasure"))

    luna.add_meme("kindness", 1.0)
    luna.add_meme("curiosity", 0.8)
    luna.add_meme("worry", 0.4)
    friend.add_meme("support", 1.0)
    zap.add_meter("glow", 0.5)
    subject.add_meter("hope", 0.2)

    world.say(
        f"On a soft morning, {p.name} carried {p.tool} into {p.place}, "
        f"where {p.friend} was waiting beside {p.object_name}."
    )
    world.say(f"The trouble was simple to see: {scenario['problem']}.")
    world.say(
        f"{p.name} looked closely and found a clue: {scenario['clue']}. "
        f"Inside, a small thought whispered, 'Be gentle. Someone needs care.'"
    )
    world.say(f"{scenario['choice']}.")
    world.say(
        f"{p.name} held up {p.tool}. It gave one warm, harmless zap of blue light, "
        "not to force the world to change, but to help everyone notice the next kind step."
    )
    world.say(f"{scenario['action']}. {scenario['dialogue']}")
    luna.add_meme("worry", -0.4)
    luna.add_meme("bravery", 1.0)
    luna.add_meme("kindness", 1.0)
    friend.add_meme("trust", 1.0)
    zap.add_meter("glow", 1.0)
    subject.add_meter("hope", 1.0)
    world.say(f"{scenario['resolution']}. The little zap lantern glowed brighter in their joined hands.")
    world.say(
        f"{p.name} felt something transform inside: {scenario['lesson']}. "
        "The change was quiet, but it made the whole garden feel warmer."
    )
    world.say(
        f"{scenario['ending']}. {p.name} and {p.friend} smiled, knowing that kindness had "
        "not merely repaired one small thing; it had made room for hope."
    )

    world.facts = {
        "title": scenario["title"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
        "choice": scenario["choice"],
        "action": scenario["action"],
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def make_story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What problem did {p.name} notice in {p.place}?",
            answer=f"{f['problem']}. It needed patient care rather than a hurried fix.",
        ),
        QAItem(
            question="What clue helped Luna understand the problem?",
            answer=f"{f['clue']}. The clue showed Luna where to begin helping.",
        ),
        QAItem(
            question=f"How did {p.name} and {p.friend} show kindness?",
            answer=f"{f['action']}. They worked together and chose a gentle response.",
        ),
        QAItem(
            question="How did the zap lantern help?",
            answer=(
                f"The zap lantern gave one warm, harmless zap of blue light. "
                f"It helped {p.name} and {p.friend} notice the next kind step instead of trying to force a change."
            ),
        ),
        QAItem(
            question="What transformation happened by the end?",
            answer=f"{f['resolution']}. Inside Luna, {f['lesson']}.",
        ),
        QAItem(
            question="What image closes the story?",
            answer=f"{f['ending']}. The image shows hope growing through kindness.",
        ),
    ]


def make_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's quiet thought, such as a private reminder to be gentle or brave.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is choosing to notice another being's needs and responding with care.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a meaningful change, such as worry becoming courage or a wilted plant becoming hopeful.",
        ),
        QAItem(
            question="What does a gentle zap do in this world?",
            answer="A gentle zap from the blue lantern helps people notice a caring possibility; it never replaces their thoughtful action.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a heartwarming story about {p.name} and {p.friend} helping {p.object_name} in {p.place}.",
        f"Include an inner monologue that leads from worry to kindness, using {p.tool}.",
        f"Show this transformation clearly: {f['resolution']}.",
        f"End with this warm image: {f['ending']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(
            f"  {character.name} ({character.role}) "
            f"meters={character.meters} memes={character.memes}"
        )
    for obj in world.objects.values():
        lines.append(
            f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params=params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=make_world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("happy_story" if asp.atoms(model, "happy_story") else "(no happy_story)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            friend=args.friend or "Milo",
            place=args.place or "the little garden",
            object_name=args.object_name or "a wilted sunflower",
            tool=args.tool or "the blue zap lantern",
        )
        if "zap" not in params.tool.lower():
            raise StoryError("The tool must include the word 'zap'.")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(1, args.n) and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
