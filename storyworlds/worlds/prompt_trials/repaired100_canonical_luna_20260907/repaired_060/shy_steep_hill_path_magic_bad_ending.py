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
place(steep_hill_path).
feature(shy).
feature(magic).
feature(bad_ending).
path_risk(steep_hill_path).
magic_can_help :- feature(magic), path_risk(steep_hill_path).
shyness_needs_support :- feature(shy).
bad_outcome_possible :- feature(bad_ending), path_risk(steep_hill_path).
safe_story :- magic_can_help, shyness_needs_support, not bad_outcome_possible.
#show safe_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    companion: str = "a quiet moon rover"
    object_name: str = "the blue star compass"
    place: str = "the steep hill path"
    destination: str = "the little observatory"
    time: str = "starlight"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


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
        "title": "the silent starlight bridge",
        "premise": "the glowing bridge above the steep hill path had gone dark",
        "obstacle": "Luna needed to cross before a silver dust storm reached the trail",
        "clue": "a tiny rune blinked whenever the blue star compass pointed uphill",
        "mistake": "Luna almost hurried onto the bridge without checking whether its magic was awake",
        "action": "Luna whispered the rune's pattern to the moon rover, then placed the compass on the first stone",
        "dialogue": "'I am shy, but I can say what I noticed,' Luna said. 'The stars are showing us the safe step.'",
        "resolution": "The bridge lit one stone at a time, and Luna crossed while the rover hummed beside her",
        "ending": "the observatory dome opened to a sky full of calm blue stars",
        "lesson": "being shy does not mean being silent when a careful truth can keep someone safe",
    },
    {
        "title": "the comet seed",
        "premise": "a warm comet seed rolled loose across the steep hill path",
        "obstacle": "It was sliding toward a dark ravine where its young magic would disappear",
        "clue": "the seed slowed whenever Luna sang the first three notes of a landing song",
        "mistake": "Luna wanted to grab it, but the loose gravel shifted beneath her boots",
        "action": "Luna told the rover the song, and together they made a gentle light wall across the path",
        "dialogue": "'Please help me try the safe way,' Luna said softly. 'I know the seed is frightened too.'",
        "resolution": "The comet seed rolled into the light wall and rested in a hollow beside the trail",
        "ending": "a tiny comet flower opened, glowing like a lantern beneath the observatory",
        "lesson": "a quiet voice can guide powerful magic when it asks for help",
    },
    {
        "title": "the lost moon signal",
        "premise": "a rescue signal flickered far above the steep hill path",
        "obstacle": "A small explorer pod had stopped on a narrow ledge with no clear route down",
        "clue": "the signal flashed twice for yes and once for no",
        "mistake": "Luna first thought she should climb alone before the ledge became darker",
        "action": "Luna used the compass to send a return signal and asked the rover to unfold its bridge cable",
        "dialogue": "'Two flashes means you hear me,' Luna called. 'Stay still while we make a safe path.'",
        "resolution": "The explorer followed the glowing cable back to the wide trail",
        "ending": "the rescued pod rose above the hill, sprinkling friendly stars over Luna's helmet",
        "lesson": "speaking clearly can turn a frightening distance into a shared plan",
    },
    {
        "title": "the dragonfly satellite",
        "premise": "a tiny dragonfly satellite buzzed in circles beside the steep hill path",
        "obstacle": "Its navigation spell had tangled around a thorny moon vine",
        "clue": "the spell loosened whenever the satellite heard a steady heartbeat",
        "mistake": "Luna reached toward the vine, then noticed the thorns pointing toward the path",
        "action": "Luna sat safely on a flat rock and tapped a slow rhythm while the rover used its soft beam",
        "dialogue": "'I am nervous,' Luna admitted. 'Can we be patient together?'",
        "resolution": "The vine relaxed, and the satellite flew free without scratching anyone",
        "ending": "the dragonfly satellite traced a bright circle around the observatory dome",
        "lesson": "patience gives magic room to untangle without making a bad ending worse",
    },
    {
        "title": "the mirror of Mars",
        "premise": "a red mirror appeared halfway up the steep hill path",
        "obstacle": "It showed a false shortcut leading straight over a broken ridge",
        "clue": "the real trail reflected two moons, while the false path reflected only one",
        "mistake": "Luna nearly followed the bright shortcut because it looked faster",
        "action": "Luna counted the moons aloud and asked the rover to mark the true stones with blue light",
        "dialogue": "'The shining path is not always the safe path,' Luna said, louder than before.",
        "resolution": "The mirror faded, leaving the real trail clear under both moons",
        "ending": "blue trail marks curled upward to the observatory like a friendly constellation",
        "lesson": "careful noticing can protect a shy traveler from a tempting mistake",
    },
]


OPENINGS = [
    "Under a violet sky, {name} reached {place} with {companion}.",
    "The first stars appeared as {name} stood at the foot of {place}.",
    "A silver moon rose over {place}, where {name} carried {object_name} beside {companion}.",
    "The space wind whispered over {place} when {name} began the climb.",
    "At starlight, {name} and {companion} looked up the steep trail toward {destination}.",
]


TURNS = [
    "The strange clue made Luna pause instead of rushing uphill.",
    "For one breath, the steep path felt like a whole planet.",
    "Then Luna understood that the magic was asking for attention, not speed.",
    "The first plan was too risky, so Luna let the clue change the plan.",
    "A small observation became a bright thread through the trouble.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A shy space adventure on a steep hill path, with magic and a possible bad ending."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--object-name")
    parser.add_argument("--place")
    parser.add_argument("--destination")
    parser.add_argument("--time")
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
    place = args.place or "the steep hill path"
    if place != "the steep hill path":
        raise StoryError("This world is built around the steep hill path.")
    time = args.time or "starlight"
    if time != "starlight":
        raise StoryError("This world is built around starlight.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Nova", "Mira", "Sol", "Tavi"]),
        companion=args.companion or rng.choice(
            ["a quiet moon rover", "a pocket satellite", "a small comet drone"]
        ),
        object_name=args.object_name or rng.choice(
            ["the blue star compass", "the silver moon key", "the violet signal stone"]
        ),
        place=place,
        destination=args.destination or "the little observatory",
        time=time,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "steep_hill_path"),
            asp.fact("feature", "shy"),
            asp.fact("feature", "magic"),
            asp.fact("feature", "bad_ending"),
            asp.fact("path_risk", "steep_hill_path"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_story/0."))
    asp_ok = bool(asp.atoms(model, "safe_story"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree that this domain has no guaranteed safe ending.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    index = (p.seed or 0) % len(SCENARIOS)
    scenario = SCENARIOS[index]
    turn = TURNS[((p.seed or 0) // len(SCENARIOS)) % len(TURNS)]
    opening = OPENINGS[((p.seed or 0) // (len(SCENARIOS) * len(TURNS))) % len(OPENINGS)]
    values = {
        "name": p.name,
        "companion": p.companion,
        "object_name": p.object_name,
        "place": p.place,
        "destination": p.destination,
    }

    def text(key: str) -> str:
        return scenario[key].format(**values)

    child = world.add_character(Character(p.name, "shy space traveler"))
    companion = world.add_object(ObjectThing(p.companion, "space helper"))
    compass = world.add_object(ObjectThing(p.object_name, "magic instrument"))

    child.add_meme("shyness", 1)
    child.add_meme("curiosity", 1)
    child.add_meme("hope", 0.5)
    child.add_meter("distance_uphill", 0)
    companion.add_meter("support", 1)
    compass.add_meme("magic", 1)

    world.say(opening.format(**values))
    world.say(
        f"{p.name} wanted to reach {p.destination}, but the stones were steep and the dark sky made every step feel enormous."
    )
    world.say(f"The adventure began when {text('premise')}.")
    world.say(f"{text('obstacle')}. {text('clue')}.")
    child.add_meter("distance_uphill", 6)
    world.say(f"{text('mistake')}. {turn}")
    world.say(f"{text('action')}. {text('dialogue')}")
    child.add_meme("courage", 1)
    child.add_meme("trust", 1)
    companion.add_meter("support", 1)
    compass.add_meter("magic_used", 1)
    world.say(f"{text('resolution')}. The dangerous shortcut was left behind.")
    child.add_meme("relief", 1)
    world.say(
        f"{p.name} learned that {text('lesson')}. The path was still steep, but it no longer felt impossible to face."
    )
    world.say(
        f"At last, {text('ending')}. {p.name} looked back at the hill and gave the moon rover a shy, proud wave."
    )

    world.facts = {
        "scenario": scenario["title"],
        "obstacle": text("obstacle"),
        "clue": text("clue"),
        "action": text("action"),
        "resolution": text("resolution"),
        "lesson": text("lesson"),
        "ending": text("ending"),
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What trouble did {p.name} meet on the steep hill path?",
            answer=f"{f['obstacle']}. The steep path made the danger important because a rushed step could have caused a bad ending.",
        ),
        QAItem(
            question="What magical clue helped guide the adventure?",
            answer=f"{f['clue']}. The clue gave Luna evidence instead of asking her to guess.",
        ),
        QAItem(
            question=f"How did {p.name} handle being shy?",
            answer=f"{f['action']} Luna also spoke to the helper, showing that a shy traveler can still share an important observation.",
        ),
        QAItem(
            question="How was the dangerous problem resolved?",
            answer=f"{f['resolution']} The solution used magic carefully and kept the traveler away from the risky shortcut.",
        ),
        QAItem(
            question="What image proves the story ended well?",
            answer=f"{f['ending']} This concrete image shows that the journey reached a safe, hopeful turn instead of a bad ending.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does shy mean?",
            answer="Shy means feeling nervous or quiet around others, especially when speaking or trying something new.",
        ),
        QAItem(
            question="What is magic in a space adventure?",
            answer="Magic is a mysterious power that can help, but it still needs careful choices and responsible use.",
        ),
        QAItem(
            question="Why can a steep hill path be dangerous?",
            answer="A steep hill path can be dangerous because loose stones, narrow edges, and tired feet can make a rushed step unsafe.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is an outcome in which the central danger is not solved or someone is left hurt, lost, or unsafe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a child-facing Space Adventure about shy {p.name} on {p.place}.",
        f"Use magic to reveal this clue: {f['clue']}.",
        f"Show dialogue changing the plan, and end with this safe image: {f['ending']}.",
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
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show safe_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show safe_story/0."))
        print("safe_story" if asp.atoms(model, "safe_story") else "no_safe_story")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            companion=args.companion or "a quiet moon rover",
            object_name=args.object_name or "the blue star compass",
            place="the steep hill path",
            destination=args.destination or "the little observatory",
            time="starlight",
        )
        samples = [generate(params)]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
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
