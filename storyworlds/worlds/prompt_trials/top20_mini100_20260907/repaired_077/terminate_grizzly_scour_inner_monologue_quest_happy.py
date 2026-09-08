#!/usr/bin/env python3
"""
A small superhero-style story world about a grizzly, a quest, a careful scour,
an inner monologue, and a happy ending.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Nova"
    sidekick_name: str = "Pip"
    setting: str = "the moonlit city park"
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    sidekick: Character
    setting: str
    threat: str = "grizzly"
    quest_complete: bool = False
    alarm_terminated: bool = False
    happy: bool = False
    clues_scoured: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


HERO_NAMES = ["Nova", "Mira", "Jett", "Aria", "Zane", "Lumi", "Kai", "Tess"]
SIDEKICK_NAMES = ["Pip", "Bea", "Rio", "Moss", "Skye", "Len", "Nia", "Bo"]
SETTINGS = [
    "the moonlit city park",
    "the rooftop garden",
    "the bright river bridge",
    "the quiet train station",
    "the downtown museum hall",
    "the old lighthouse steps",
]

INCIDENTS = [
    {
        "title": "the runaway alert drone",
        "threat": "a grizzly-shaped shadow on the security screen",
        "setup": "an alarm drone kept circling the park and shrieking at every breeze",
        "misread": "its shadow made it look like a grizzly was stomping through the grass",
        "risk": "the noise could send families running and keep the night watch from hearing a real problem",
        "quest": "find the drone's control panel and stop the false alarm",
        "scour": "carefully scour the benches, lamp posts, and hedge line for the blinking reset switch",
        "clue": "the drone's red light was reflected in a puddle near the duck fountain",
        "first_try": "charged toward the shadow with a dramatic cape swing",
        "inner": "If this is really a grizzly, I need a plan. If it is not, I need facts faster than fear.",
        "dialogue1": "\"Hold on,\" said {sidekick}. \"Something small is making that giant sound.\"",
        "dialogue2": "\"Then we track the light,\" said {hero}. \"A hero can be brave and careful.\"",
        "fix": "tap the control panel, silence the drone, and announce the all-clear",
        "ending": "the drone fell quiet, the puddle stopped flashing, and the park glowed softly under the stars",
    },
    {
        "title": "the missing honey crate",
        "threat": "a grizzly at the market gate",
        "setup": "a crate of honey jars had rolled behind a delivery cart",
        "misread": "the rumbling cart tracks made it seem as if a grizzly had raided the whole loading dock",
        "risk": "the market workers needed the crate found before bees and jars became a sticky mess",
        "quest": "recover the crate before closing time",
        "scour": "scour the loading dock, the cart wheels, and the stack of aprons for the missing crate",
        "clue": "one jar lid caught a sparkle of sunlight beneath the cart",
        "first_try": "shouted a warning and leaped onto the wrong crate",
        "inner": "I can feel my heart thumping, but that does not mean danger is certain. Look, then act.",
        "dialogue1": "\"Easy, hero,\" said {sidekick}. \"The grizzly is only in the story you were telling yourself.\"",
        "dialogue2": "\"Good catch,\" said {hero}. \"Let's follow the honey sparkle instead.\"",
        "fix": "lift the cart edge, pull out the crate, and return every jar to the counter",
        "ending": "the honey jars lined up neatly while the market gate swung shut in peace",
    },
    {
        "title": "the museum night trail",
        "threat": "a grizzly in the dinosaur hall",
        "setup": "tiny muddy prints appeared beside the fossil display",
        "misread": "the prints looked like a grizzly had wandered indoors",
        "risk": "if the prints were real, a heavy animal could damage the exhibits and frighten visitors",
        "quest": "follow the prints and find where they actually came from",
        "scour": "scour the hall floor, the costume closet, and the open doorway for the source of the mud",
        "clue": "a museum mascot boot with bear-claw paint was left near the gift shop",
        "first_try": "began sealing the whole hall with emergency tape",
        "inner": "These footprints are strange, but strange is not the same as certain. I need to think like a detective.",
        "dialogue1": "\"Those are not giant paws,\" whispered {sidekick}. \"They are splashes from a costume boot.\"",
        "dialogue2": "\"Then let's trace the mud to the right door,\" said {hero}.",
        "fix": "return the boot, wipe the floor, and guide the mascot outside before reopening the hall",
        "ending": "the fossils shone behind clean glass, and the harmless muddy trail ended at the costume room",
    },
    {
        "title": "the bridge echo chase",
        "threat": "a grizzly growl beneath the bridge",
        "setup": "a storm drain kept making low, rolling sounds",
        "misread": "the echo made the sound seem like a grizzly was hiding below the bridge",
        "risk": "a frightened crowd could block traffic and keep an injured person from getting help",
        "quest": "scour the bridge supports and drain grates to find the real source",
        "scour": "carefully scour each grate, each bolt, and each puddle for the source of the growl",
        "clue": "the sound matched a bicycle bell caught in the wind",
        "first_try": "called for backup and pointed dramatically at the river",
        "inner": "Do not let a loud echo turn into a giant monster in your head. Check the metal, check the water, check the wind.",
        "dialogue1": "\"Listen again,\" said {sidekick}. \"It comes and goes with the gusts.\"",
        "dialogue2": "\"Then the bridge is not hiding a grizzly,\" said {hero}. \"It is hiding an echo.\"",
        "fix": "free the bicycle bell from the grate and let the wind pass through the bridge again",
        "ending": "the growl vanished, the crowd laughed with relief, and the river ran on under a clear sky",
    },
    {
        "title": "the lighthouse snack raid",
        "threat": "a grizzly on the steps",
        "setup": "a seagull had carried a snack wrapper into the lighthouse stairwell",
        "misread": "the torn wrapper and deep footprints made it seem like a grizzly had climbed the steps",
        "risk": "the keeper could slip, and the stairs needed to stay open for the signal lamp",
        "quest": "find the bird, the wrapper, and the real muddy cause",
        "scour": "scour the steps, the railing, and the lantern room for the wrapper trail",
        "clue": "the muddy prints belonged to a dog wearing a boot from the beach festival",
        "first_try": "rushed up the steps with heroic speed and a flashlight beam",
        "inner": "A hero's job is not to leap at every shadow. A hero's job is to know what is there.",
        "dialogue1": "\"No bear tracks,\" said {sidekick}. \"See the tiny nails? That is a festival boot.\"",
        "dialogue2": "\"Then the real problem is the mess,\" said {hero}. \"Let's clean it before anyone slips.\"",
        "fix": "collect the wrapper, guide the dog back to its owner, and dry the stairs with a towel",
        "ending": "the lamp shone cleanly from the top of the lighthouse while the steps stayed safe and dry",
    },
    {
        "title": "the rooftop garden alarm",
        "threat": "a grizzly among the tomato pots",
        "setup": "a toppled watering can left dark stains in the soil",
        "misread": "the wide muddy shape looked like a grizzly had rolled through the rooftop garden",
        "risk": "the seedlings could be crushed, and the alarm would bring too many helpers to the roof",
        "quest": "scour the roof for the cause of the muddy shape and save the seedlings",
        "scour": "scour the soil, the rail, and the watering corner for tracks and tools",
        "clue": "a squirrel had dragged the watering can from its hook",
        "first_try": "raised the shield and prepared for battle",
        "inner": "Maybe the danger is large. Maybe it is tiny. Either way, I should look before I launch.",
        "dialogue1": "\"The grizzly left a tail?\" asked {sidekick}. \"No. That is a hose line.\"",
        "dialogue2": "\"Then the garden only needs a fix,\" said {hero}.",
        "fix": "hang the can back up, water the seedlings, and smooth the soil with a gentle rake",
        "ending": "the tomatoes stood straight again, and the rooftop smelled like rain instead of worry",
    },
]

OPENINGS = [
    "The night was quiet until",
    "Just as the hero finished patrol,",
    "While the city lights blinked below,",
    "At the start of a calm evening shift,",
    "As the wind moved over the rooftops,",
    "During a routine sweep of the neighborhood,",
]

CLOSERS = [
    "Happy ending came softly, the way a calm bell settles after the last ring.",
    "By the time the stars brightened, the city felt safe again.",
    "The last shadow shrank into nothing, and the heroes smiled at their good work.",
    "Everyone went home wiser, calmer, and ready for a better tomorrow.",
    "The quest ended with clean hands, clear eyes, and a peaceful street.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero grizzly quest story world.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_choices = [n for n in SIDEKICK_NAMES if n != hero]
    sidekick = args.sidekick_name or rng.choice(sidekick_choices)
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(hero_name=hero, sidekick_name=sidekick, setting=setting)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.sidekick_name:
        raise StoryError("The hero and sidekick need different names.")
    if params.setting not in SETTINGS:
        raise StoryError("That setting is not available in this world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)

    rng = random.Random(params.seed if params.seed is not None else 0)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    closer = rng.choice(CLOSERS)

    hero = Character(name=params.hero_name, kind="superhero", meter={"focus": 8.0, "calm": 6.0}, meme={"hope": 9.0})
    sidekick = Character(name=params.sidekick_name, kind="sidekick", meter={"speed": 7.0}, meme={"loyal": 8.0})
    world = World(hero=hero, sidekick=sidekick, setting=params.setting)

    lines = []
    lines.append(f"{hero.name} patrolled {params.setting} with {sidekick.name} at their side.")
    lines.append(f"{opening} {incident['setup']} near the path.")
    lines.append(f"Someone shouted that a {incident['threat']} was there, because {incident['misread']}.")
    world.facts["setup"] = incident["setup"]
    world.facts["misread"] = incident["misread"]
    world.facts["risk"] = incident["risk"]
    world.facts["quest"] = incident["quest"]
    world.facts["clue"] = incident["clue"]

    lines.append(f"{hero.name} almost acted at once and {incident['first_try']}.")
    lines.append(f"In a quiet inner monologue, {hero.name} told themselves: \"{incident['inner']}\"")
    lines.append(incident["dialogue1"].format(hero=hero.name, sidekick=sidekick.name))
    lines.append(incident["dialogue2"].format(hero=hero.name, sidekick=sidekick.name))
    lines.append(f"Then the real quest became clear: {incident['quest']}.")
    lines.append(f"To do that, they had to {incident['scour']}.")
    lines.append(f"The key clue was simple: {incident['clue']}.")
    lines.append(f"That clue proved the danger was not a real grizzly, but a mix-up that could be fixed safely.")
    lines.append(f"Together they {incident['fix']}.")
    lines.append("The alarm stopped, the mess was cleared, and nobody had to fear the wrong thing anymore.")
    lines.append(f"{closer}")
    lines.append(f"By the end, {incident['ending']}.")

    world.quest_complete = True
    world.alarm_terminated = True
    world.happy = True
    world.clues_scoured = [incident["clue"]]
    world.facts["ending"] = incident["ending"]
    world.facts["happy"] = True
    world.facts["alarm"] = "terminated"

    story = " ".join(lines)

    prompts = [
        "Write a child-friendly superhero story with an inner monologue, a quest, and a happy ending.",
        f"Tell a story where {hero.name} and {sidekick.name} scour the scene and mistake a grizzly-shaped clue for real danger.",
        "Make the spoken dialogue help solve the problem instead of just repeating it.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {hero.name} first think was happening?",
            answer=f"{hero.name} first thought there was a real {incident['threat']}.",
        ),
        QAItem(
            question="What did the inner monologue help the hero do?",
            answer="It helped the hero slow down, think carefully, and avoid rushing into the wrong action.",
        ),
        QAItem(
            question=f"What was the quest they needed to complete?",
            answer=f"They needed to {incident['quest']}.",
        ),
        QAItem(
            question="What clue solved the misunderstanding?",
            answer=f"The clue was that {incident['clue']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the problem fixed and the danger safely gone.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large bear.",
        ),
        QAItem(
            question="What does scour mean in this story world?",
            answer="To scour means to search carefully and thoroughly for a clue or a missing thing.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a determined mission to solve a problem or reach a goal.",
        ),
        QAItem(
            question="What does a happy ending mean?",
            answer="A happy ending means the problem is resolved and the characters finish safe and well.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render() or story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        w = sample.world
        print(f"hero={w.hero.name}, kind={w.hero.kind}, meter={w.hero.meter}, meme={w.hero.meme}")
        print(f"sidekick={w.sidekick.name}, kind={w.sidekick.kind}, meter={w.sidekick.meter}, meme={w.sidekick.meme}")
        print(f"setting={w.setting}, threat={w.threat}, quest_complete={w.quest_complete}, alarm_terminated={w.alarm_terminated}, happy={w.happy}")
        print(f"clues_scoured={w.clues_scoured}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
hero(H) :- name(H).
sidekick(S) :- name(S), not hero(S).
quest_complete :- quest(_), clue(_), not alarm_active.
terminated(alarm) :- alarm_active, fix(_).

#show valid_setting/1.
valid_setting(S) :- setting(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("setting", setting) for setting in SETTINGS)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_setting/1."))
    return sorted(set(asp.atoms(model, "valid_setting")))


def asp_verify() -> int:
    py = set((s,) for s in SETTINGS)
    cl = set(asp_valid_settings())
    if py == cl:
        print(f"OK: clingo gate matches SETTINGS ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        out: list[StoryParams] = []
        for i, setting in enumerate(SETTINGS):
            hero = HERO_NAMES[i % len(HERO_NAMES)]
            sidekick = SIDEKICK_NAMES[(i + 1) % len(SIDEKICK_NAMES)]
            if sidekick == hero:
                sidekick = SIDEKICK_NAMES[(i + 2) % len(SIDEKICK_NAMES)]
            out.append(StoryParams(hero_name=hero, sidekick_name=sidekick, setting=setting))
        return out
    base = args.seed if args.seed is not None else random.randrange(2**31)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p[0]}" for p in asp_valid_settings()))
        return

    samples: list[StorySample] = []
    for i, params in enumerate(generation_samples(args)):
        params.seed = (args.seed if args.seed is not None else 0) + i
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
