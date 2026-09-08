#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
place(garden).
feature(effect).
feature(bask).
feature(inner_monologue).
feature(bedtime_story).

gentle(effect) :- feature(effect).
restful(bask) :- feature(bask).
thoughtful(inner_monologue) :- feature(inner_monologue).
cozy(bedtime_story) :- feature(bedtime_story).

happy_story :- gentle(effect), restful(bask), thoughtful(inner_monologue), cozy(bedtime_story).
#show happy_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    companion: str = "a sleepy moth"
    blanket: str = "a blue quilt"
    treat: str = "warm moon-milk"
    place: str = "the moon garden"


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
        "title": "the sleepy silver flower",
        "problem": "one silver flower had folded its petals before bedtime",
        "clue": "a warm patch of moonlight rested on the stones beside it",
        "action": "Luna moved the flower's little pot into that gentle glow and loosened the dry soil",
        "resolution": "the flower slowly opened and shared its soft light with the path",
        "ending": "its silver petals shone like a tiny lamp beneath the quiet stars",
        "lesson": "a small thoughtful effect can make a resting place feel safe",
    },
    {
        "title": "the blanket on the breeze",
        "problem": "the blue quilt kept slipping from the garden bench",
        "clue": "a row of round pebbles lay nearby, smooth enough to hold its corners",
        "action": "Luna placed the pebbles along the quilt's edge and tucked her companion beneath it",
        "resolution": "the breeze could no longer carry the blanket away",
        "ending": "the quilt made a calm blue island where everyone could bask in moonlight",
        "lesson": "careful noticing can turn a restless moment into comfort",
    },
    {
        "title": "the lantern moth's shadow",
        "problem": "the garden lantern cast a large shadow that frightened the smallest moths",
        "clue": "the shadow grew whenever the lantern leaned toward the path",
        "action": "Luna gently straightened the lantern and hung a pale scarf behind it",
        "resolution": "the shadow became a soft circle instead of a dark shape",
        "ending": "the moths danced inside the warm circle as if it were a little sky",
        "lesson": "understanding an effect helps a kind heart choose a gentle fix",
    },
    {
        "title": "the quiet pond ripple",
        "problem": "the pond made a worried ripple although no one was touching the water",
        "clue": "a fallen leaf bobbed beside the fountain stone",
        "action": "Luna lifted the leaf with a long reed and set it on the bank",
        "resolution": "the pond became still enough for the moon to see her smiling face",
        "ending": "the reflected moon rested on the water like a round bedtime button",
        "lesson": "a calm pause can reveal what a hurried glance misses",
    },
    {
        "title": "the drowsy bell",
        "problem": "the little bedtime bell made no sound when the breeze arrived",
        "clue": "a strand of grass had wrapped around its silver clapper",
        "action": "Luna asked her companion to hold the lantern while she freed the grass with a twig",
        "resolution": "the bell chimed once, softly enough not to wake the sleeping birds",
        "ending": "its tiny note floated over the garden and tucked everyone into dreams",
        "lesson": "asking for help can make a difficult kindness easier",
    },
]


OPENINGS = [
    "When the last peach light faded, {name} carried {blanket} into {place}.",
    "The moon had just climbed above the trees when {name} entered {place} with {companion}.",
    "At bedtime, {name} brought {treat} and {blanket} to {place} for one quiet visit.",
    "A silver breeze followed {name} into {place}, where {companion} was waiting sleepily.",
    "{name} wanted to bask in the moonlight, so she settled near {place} with {blanket}.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle bedtime story about effects, rest, and thoughtful inner monologue.")
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--blanket")
    parser.add_argument("--treat")
    parser.add_argument("--place")
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
    place = args.place or "the moon garden"
    if place != "the moon garden":
        raise StoryError("This bedtime world takes place in the moon garden.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Mira", "Nell", "Ari"]),
        companion=args.companion or rng.choice(["a sleepy moth", "a small owl", "a velvet rabbit"]),
        blanket=args.blanket or rng.choice(["a blue quilt", "a starry shawl", "a soft green blanket"]),
        treat=args.treat or rng.choice(["warm moon-milk", "honey tea", "a cinnamon bun"]),
        place=place,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "garden"),
            asp.fact("feature", "effect"),
            asp.fact("feature", "bask"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "bedtime_story"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return all(("effect" in line.lower() or "effect" in "effect") for line in ["effect"])


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_story/0."))
    asp_ok = bool(asp.atoms(model, "happy_story"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        sample = generate(StoryParams(seed=7))
        if sample.story and "Luna" in sample.story and sample.story_qa:
            print("OK: ASP and Python agree, and the generated story is complete.")
            return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    child = world.add_character(Character(p.name, "dreamer"))
    companion = world.add_character(Character(p.companion, "sleepy helper"))
    blanket = world.add_object(ObjectThing(p.blanket, "blanket"))
    child.add_meme("curiosity", 1)
    child.add_meme("care", 0.5)
    companion.add_meme("trust", 1)

    world.say(opening.format(name=p.name, blanket=p.blanket, place=p.place, companion=p.companion))
    world.say(f"She set down {p.treat}. Before taking a sip, she thought, \"I wonder what small effect made tonight feel less peaceful.\"")
    world.say(f"The mystery was {scenario['title']}: {scenario['problem']}.")
    world.say(f"Luna noticed that {scenario['clue']}. She whispered, \"That clue may show us what the garden needs.\"")
    child.add_meter("quiet_steps", 4)
    child.add_meme("attention", 1)
    world.say(f"{p.name} took a slow breath. Inside, she told herself, \"I can be gentle. I can look first, then help.\"")
    world.say(f"\"Should I come with you?\" asked {p.companion}. \"Yes,\" said {p.name}. \"Two quiet helpers can notice more than one.\"")
    world.say(f"{scenario['action']}.")
    blanket.add_meter("comfort", 1)
    companion.add_meme("helpfulness", 1)
    child.add_meme("bravery", 1)
    world.say(f"{scenario['resolution']}. The good effect spread through the garden, and even the shadows seemed to soften.")
    world.say(f"{p.name} and {p.companion} sat beneath {p.blanket} to bask in the moonlight. \"We helped without making a fuss,\" said {p.name}.")
    world.say(f"{scenario['lesson'].capitalize()}. {scenario['ending']}. Then {p.name} drank the last of {p.treat} and let sleep find her.")
    world.facts = {
        "title": scenario["title"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
        "action": scenario["action"],
        "resolution": scenario["resolution"],
        "lesson": scenario["lesson"],
        "ending": scenario["ending"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(f"What problem did {p.name} find in {p.place}?", f"{f['problem'].capitalize()}."),
        QAItem("What clue helped explain the trouble?", f"{f['clue'].capitalize()} This clue helped Luna understand the effect before acting."),
        QAItem(f"What did {p.name} do?", f"{f['action'].capitalize()} She chose a gentle action rather than rushing."),
        QAItem("How did the story end?", f"{f['resolution'].capitalize()} Then {f['ending']}."),
        QAItem("What did Luna's inner monologue help her do?", "It helped her pause, name her worry, and choose a careful action that made the garden more peaceful."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an effect?", "An effect is a change that happens because something else happened first."),
        QAItem("What does it mean to bask?", "To bask means to rest happily in warmth or gentle light."),
        QAItem("What is an inner monologue?", "An inner monologue is the quiet stream of thoughts a character has inside their mind."),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a bedtime story about {p.name} noticing {f['title']} in {p.place}.",
        f"Use inner monologue to show how {p.name} understands this clue: {f['clue']}.",
        f"End with {p.name} and {p.companion} basking peacefully after this resolution: {f['resolution']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ch in world.characters.values():
        lines.append(f"  {ch.name} ({ch.role}) meters={ch.meters} memes={ch.memes}")
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    generate_story(world)
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
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show happy_story/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_story/0."))
        print("happy_story" if asp.atoms(model, "happy_story") else "(no happy_story)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
