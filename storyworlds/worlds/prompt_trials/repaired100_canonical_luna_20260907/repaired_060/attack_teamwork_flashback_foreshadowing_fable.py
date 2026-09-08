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
threat(crow).
feature(teamwork).
feature(flashback).
feature(foreshadowing).
feature(fable).
plan(stone_rattle).
memory(old_scare).
warning(dangling_ribbon).

can_prepare :- threat(crow), plan(stone_rattle), warning(dangling_ribbon).
can_cooperate :- feature(teamwork).
can_learn :- feature(flashback), memory(old_scare).
wise_turn :- can_prepare, can_cooperate, can_learn.
safe_resolution :- wise_turn.
happy_fable :- safe_resolution, feature(fable).
#show happy_fable/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    partner: str = "Pip"
    guardian: str = "the old gardener"
    place: str = "the moonlit garden"
    prize: str = "a silver bell"
    threat: str = "a hungry crow"


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

    def say(self, text: str) -> None:
        self.trace.append(text)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, thing: ObjectThing) -> ObjectThing:
        self.objects[thing.name] = thing
        return thing

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the attack on the berry patch",
        "premise": "a black crow swooped into the berry patch and began pecking at the ripest fruit",
        "foreshadowing": "earlier that morning, Luna had noticed a red ribbon hanging from the scarecrow's loose arm",
        "flashback": "Luna remembered how a flock had once scattered the garden seeds when everyone chased birds in different directions",
        "plan": "Pip would ring the little bell, Luna would lift the ribbon, and the gardener would open the far gate",
        "turn": "The crow darted toward the bell, but the red ribbon fluttered beside it and made the bird veer toward the open gate",
        "resolution": "The crow flew into the meadow, while the berries stayed safe for the village children",
        "ending": "The silver bell chimed softly above a basket of red berries",
        "lesson": "one brave helper may face a problem, but wise teamwork gives courage a better path",
    },
    {
        "title": "the attack on the seed shelf",
        "premise": "a quick little squirrel attacked the seed shelf, scattering beans across the warm soil",
        "foreshadowing": "before breakfast, Luna had seen three acorns placed in a neat line beneath the shelf",
        "flashback": "She remembered the gardener saying that frightened animals run farther when people shout",
        "plan": "Luna would place acorns by the hedge, Pip would shield the seedlings with a basket, and the gardener would mend the shelf",
        "turn": "When the squirrel returned, the acorns formed a quiet trail away from the seedlings",
        "resolution": "The squirrel followed the trail, and the new shelf held the seeds safely again",
        "ending": "tiny green shoots stood beneath the repaired shelf like a row of hopeful flags",
        "lesson": "a gentle plan can turn an attack into a safe invitation",
    },
    {
        "title": "the attack at the pond gate",
        "premise": "a storm of geese attacked the pond gate, honking and pushing against its wooden slats",
        "foreshadowing": "a loose blue cord had been trembling on the gate since sunrise",
        "flashback": "Luna recalled that the geese had once followed a blue cord to a patch of tender grass",
        "plan": "Pip would carry the feed bucket, Luna would guide the cord toward the meadow, and the gardener would brace the gate",
        "turn": "The geese chased the blue cord away from the gate and into the meadow",
        "resolution": "The gate stopped shaking, and the pond water grew calm again",
        "ending": "ripples spread around the silver bell floating safely on its hook",
        "lesson": "teamwork makes a noisy danger smaller when each friend follows a clear part of the plan",
    },
    {
        "title": "the attack on the moon flowers",
        "premise": "a band of beetles attacked the moon flowers and chewed holes through their pale leaves",
        "foreshadowing": "a line of shiny shells had appeared beside the flower bed before the attack",
        "flashback": "Luna remembered that the gardener once saved roses by moving a lantern near the leaves",
        "plan": "Luna would carry the lantern, Pip would tap a tin cup, and the gardener would move the flowers behind a fine screen",
        "turn": "The lantern showed the beetles a brighter patch of wild leaves beyond the screen",
        "resolution": "The beetles left the flowers, and the damaged leaves began to curl toward the light",
        "ending": "moon flowers opened beside the lantern as if they were small white stars",
        "lesson": "remembered wisdom helps teamwork choose a kinder defense",
    },
]


OPENINGS = [
    "At dusk, Luna entered {place} with {partner} and a basket for the {prize}.",
    "The moon was rising over {place} when Luna and {partner} began their evening work.",
    "Luna was polishing the {prize} beside {place} when a sudden rustle shook the leaves.",
    "In the quiet hour before supper, Luna and {partner} walked between the garden beds.",
    "The flowers were closing for the night when Luna heard wings above {place}.",
]


TURNS = [
    "Then the first small sign became important.",
    "Luna did not rush; she let the old memory guide her.",
    "The warning had seemed tiny, but now it pointed toward a wise choice.",
    "The past offered a lesson, and the present offered a chance to use it.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable of attack, teamwork, memory, and wise preparation.")
    parser.add_argument("--name")
    parser.add_argument("--partner")
    parser.add_argument("--guardian")
    parser.add_argument("--place")
    parser.add_argument("--prize")
    parser.add_argument("--threat")
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
    place = args.place or "the moonlit garden"
    if place != "the moonlit garden":
        raise StoryError("This fable takes place in the moonlit garden.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Mira", "Tavi", "Niko"]),
        partner=args.partner or rng.choice(["Pip", "Roo", "Moss"]),
        guardian=args.guardian or "the old gardener",
        place=place,
        prize=args.prize or rng.choice(["a silver bell", "a brass key", "a blue lantern"]),
        threat=args.threat or "a hungry crow",
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "garden"),
            asp.fact("threat", "crow"),
            asp.fact("feature", "teamwork"),
            asp.fact("feature", "flashback"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("feature", "fable"),
            asp.fact("plan", "stone_rattle"),
            asp.fact("memory", "old_scare"),
            asp.fact("warning", "dangling_ribbon"),
        ]
    )


def asp_program(show: str = "#show happy_fable/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return bool(SCENARIOS) and all(
        scenario.get("foreshadowing")
        and scenario.get("flashback")
        and scenario.get("plan")
        and scenario.get("resolution")
        for scenario in SCENARIOS
    )


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    asp_ok = bool(asp.atoms(model, "happy_fable"))
    py_ok = python_reasonable_story()
    if asp_ok != py_ok:
        print(f"MISMATCH: asp={asp_ok} python={py_ok}")
        return 1
    for seed in range(8):
        params = StoryParams(seed=seed)
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 4:
            print(f"MISMATCH: generated story failed at seed {seed}")
            return 1
    print("OK: ASP and Python agree, and generated fables pass the story gate.")
    return 0


def generate_story(world: World) -> None:
    p = world.params
    index = (p.seed or 0) % len(SCENARIOS)
    scenario = SCENARIOS[index]
    opening = OPENINGS[((p.seed or 0) // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[((p.seed or 0) // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]

    luna = world.add_character(Character(p.name, "young gardener"))
    partner = world.add_character(Character(p.partner, "helpful friend"))
    guardian = world.add_character(Character(p.guardian, "wise guardian"))
    bell = world.add_object(ObjectThing(p.prize, "garden tool"))
    ribbon = world.add_object(ObjectThing("the red ribbon", "warning sign"))

    luna.add_meme("curiosity", 1)
    luna.add_meme("bravery", 0.5)
    partner.add_meme("teamwork", 1)
    guardian.add_meme("wisdom", 1)
    ribbon.add_meter("warning", 1)

    world.say(opening.format(place=p.place, partner=p.partner, prize=p.prize))
    world.say(f"The garden had promised a peaceful evening, but {scenario['premise']}.")
    world.say(f"Before anyone acted, Luna remembered a sign: {scenario['foreshadowing']}.")
    world.say(f"{scenario['flashback']}. {turn}")
    world.say(
        f"Luna said, \"Pip, will you help me?\" "
        f"{p.partner} answered, \"Together, we can make a careful plan.\""
    )
    world.say(f"They decided that {scenario['plan']}.")
    luna.add_meter("steps", 6)
    partner.add_meter("helpful_actions", 3)
    guardian.add_meter("steady_hands", 1)
    bell.add_meter("usefulness", 1)
    world.say(f"{scenario['turn']}. The {p.threat} paused, surprised by the friendly trap.")
    world.say(
        f"The old gardener called, \"Keep close and keep calm!\" "
        f"Luna replied, \"We remember, we watch, and we work together.\""
    )
    luna.add_meme("bravery", 1)
    luna.add_meme("care", 1)
    partner.add_meme("trust", 1)
    world.say(f"{scenario['resolution']}. No one was hurt, and the garden breathed quietly again.")
    world.say(f"{scenario['lesson'].capitalize()}.")
    world.say(f"As the stars appeared, {scenario['ending']}. Luna carried {p.prize} home with {p.partner}.")

    world.facts = {
        "title": scenario["title"],
        "premise": scenario["premise"],
        "foreshadowing": scenario["foreshadowing"],
        "flashback": scenario["flashback"],
        "plan": scenario["plan"],
        "turn": scenario["turn"],
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What attack did {p.name} and {p.partner} face?",
            answer=f"They faced this attack: {f['premise']}. They treated the danger seriously without hurting anyone.",
        ),
        QAItem(
            question="What earlier sign foreshadowed the trouble?",
            answer=f"The foreshadowing sign was that {f['foreshadowing']}. It helped Luna understand that the danger was not completely unexpected.",
        ),
        QAItem(
            question="What did Luna remember in the flashback?",
            answer=f"Luna remembered that {f['flashback']}. The memory changed the group's choice from rushing to planning.",
        ),
        QAItem(
            question="How did teamwork solve the problem?",
            answer=f"The team agreed that {f['plan']}. Each person had a useful job, so the group could respond safely.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{f['resolution']} The closing image was {f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share a goal, listen to one another, and each do a useful part.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an earlier detail that gives a quiet hint about something that will matter later.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a return to an earlier event or memory that helps explain a present choice.",
        ),
        QAItem(
            question="What makes a fable?",
            answer="A fable is a short tale in which choices and consequences teach a clear lesson.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Tell a child-facing fable about {p.name} facing {f['premise']}.",
        f"Use this foreshadowing and flashback: {f['foreshadowing']} Then show how {f['flashback']}.",
        f"Show {p.name} and {p.partner} using teamwork through this plan: {f['plan']}.",
        f"End with the concrete image: {f['ending']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(
            f"  {character.name} ({character.role}) "
            f"meters={character.meters} memes={character.memes}"
        )
    for thing in world.objects.values():
        lines.append(
            f"  {thing.name} ({thing.kind}) "
            f"meters={thing.meters} memes={thing.memes}"
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("happy_fable" if asp.atoms(model, "happy_fable") else "(no happy_fable)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            partner=args.partner or "Pip",
            guardian=args.guardian or "the old gardener",
            place=args.place or "the moonlit garden",
            prize=args.prize or "a silver bell",
            threat=args.threat or "a hungry crow",
        )
        if params.place != "the moonlit garden":
            raise StoryError("This fable takes place in the moonlit garden.")
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
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
