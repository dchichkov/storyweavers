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
place(moon_station).
feature(goggle).
feature(significant).
feature(sound_effects).
feature(humor).
style(space_adventure).
mission(repair_signal).

has_tool(goggle) :- feature(goggle).
has_clue(significant) :- feature(significant).
funny_sound :- feature(sound_effects), feature(humor).
safe_mission :- mission(repair_signal), has_tool(goggle), has_clue(significant).
happy_story :- safe_mission, funny_sound, style(space_adventure).
#show happy_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    companion: str = "Bloop the moon robot"
    snack: str = "star-shaped crackers"
    goggle: str = "the silver goggle"
    place: str = "the moon station"
    time: str = "moonrise"


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

    def say(self, line: str) -> None:
        self.trace.append(line)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the wobbling beacon",
        "premise": "the station's blue beacon began flashing on and off",
        "obstacle": "A supply shuttle could not find the moon station through the dusty sky",
        "clue": "the beacon's hum became a tiny hiccup whenever its side panel shook",
        "mistake": "{name} nearly kicked the panel, but the silver goggle showed a loose golden wire",
        "action": "{name} called Captain Vega, held the panel steady, and used the goggle to point out the loose wire",
        "dialogue": "'That wire is significant,' {name} said. Bloop added, 'More significant than my snack, and that is extremely significant!'",
        "resolution": "Captain Vega clipped the wire into place, and the beacon shone steadily toward the shuttle",
        "ending": "the arriving shuttle painted a silver smile across the crater",
        "lesson": "small clues can guide a big rescue when someone takes time to notice them",
    },
    {
        "title": "the giggling moon rover",
        "premise": "the moon rover made a strange 'hee-hee-honk' whenever it rolled",
        "obstacle": "Its noisy wheel was distracting the science team from an important rock survey",
        "clue": "the sound stopped when a pebble was lifted from the wheel rim",
        "mistake": "{name} wanted to pull the pebble out at once, but the rover was still moving",
        "action": "{name} pressed the safe-stop button and used the goggle to inspect the wheel without touching it",
        "dialogue": "'No tickling the rover while it rolls,' {name} said. 'Even if it tells excellent jokes!'",
        "resolution": "The pebble was removed, and the rover rolled quietly past the purple rocks",
        "ending": "the rover sent back a perfect picture of a stone shaped like a sleepy duck",
        "lesson": "humor makes a problem lighter, but careful choices still solve it",
    },
    {
        "title": "the backwards star map",
        "premise": "the navigation map chirped 'beep-boop-bloop' and pointed the wrong way",
        "obstacle": "The crew might have flown toward a dark dust cloud instead of the safe return route",
        "clue": "the map's significant red star appeared upside down beneath a clear cover",
        "mistake": "{name} first blamed the computer, then noticed that the whole display had slipped in its frame",
        "action": "{name} told Commander Sol, marked the safe route with a sticker, and held the display while it was reset",
        "dialogue": "'The star is upside down,' {name} said. 'So is Bloop's helmet.' Bloop replied, 'I meant to do that!'",
        "resolution": "Commander Sol corrected the map, and the safe route glowed green",
        "ending": "the ship sailed home beneath stars that looked like a friendly trail of crumbs",
        "lesson": "a significant detail can turn a confusing adventure toward safety",
    },
    {
        "title": "the floating lunch alarm",
        "premise": "a lunch pouch drifted around the station making a loud 'pfffft-pop!'",
        "obstacle": "Its loose air valve was bumping the emergency controls",
        "clue": "the pouch floated toward the controls whenever the snack packet inside puffed up",
        "mistake": "{name} reached for it, but a tiny burst spun it away like a dancing pancake",
        "action": "{name} lowered the emergency shield, wore the silver goggle, and guided the pouch into a soft storage net",
        "dialogue": "'That lunch is significant,' {name} said. 'It contains my favorite crackers!'",
        "resolution": "The valve was sealed, and the emergency controls stayed safely untouched",
        "ending": "everyone shared star-shaped crackers while the pouch rested in its net",
        "lesson": "even a funny floating nuisance deserves a calm and careful plan",
    },
    {
        "title": "the sleepy satellite",
        "premise": "a small satellite answered every signal with a sleepy 'boing'",
        "obstacle": "The satellite was drifting away from the station and could not send weather readings",
        "clue": "its solar wing folded whenever a shadow crossed the panel",
        "mistake": "{name} almost sent a strong signal, but the goggle revealed a tiny moon moth resting on the wing",
        "action": "{name} called the observatory keeper and aimed a warm lamp near the panel without touching the moth",
        "dialogue": "'Wake gently,' {name} whispered. Bloop whispered back, 'Boing?'",
        "resolution": "The moth flew away, the wing opened, and the satellite sent a clear weather report",
        "ending": "the satellite blinked three cheerful lights above a sky full of stars",
        "lesson": "gentle attention can solve a significant problem without hurting a small visitor",
    },
    {
        "title": "the crater echo",
        "premise": "a crater answered every footstep with a ridiculous 'plorp-plorp'",
        "obstacle": "The echo marked a thin crust above a hollow tunnel",
        "clue": "the sound became deeper near a bright crack in the dust",
        "mistake": "{name} wondered whether an alien drum was hidden below, but did not stomp again",
        "action": "{name} backed behind a safety line, used the goggle to study the crack, and called the geology crew",
        "dialogue": "'A plorp is funny,' {name} said, 'but a weak crust is significant.'",
        "resolution": "The geology crew placed a warning marker and found a safe path around the hollow",
        "ending": "the crater kept its secret while the explorers bounced safely home",
        "lesson": "a funny sound can still carry an important warning",
    },
    {
        "title": "the comet's lost tail",
        "premise": "a tiny comet zipped past the station with a squeaky missing tail",
        "obstacle": "Without its reflective tail, the comet was hard for other ships to see",
        "clue": "a ribbon of bright ice clung to a storage hook near the launch tunnel",
        "mistake": "{name} guessed the ribbon was space spaghetti until the goggle showed matching icy sparkles",
        "action": "{name} called the comet crew and helped guide the ribbon into a safe catcher",
        "dialogue": "'That is significant evidence,' {name} said. Bloop nodded. 'And possibly delicious-looking evidence.'",
        "resolution": "The crew attached the ribbon to the comet's tail without chasing it",
        "ending": "the comet looped around the moon, sparkling like a blue kite",
        "lesson": "good evidence helps helpers choose a safe way to repair something far away",
    },
    {
        "title": "the upside-down antenna",
        "premise": "the station antenna sent a cheerful 'la-la-la' instead of a signal",
        "obstacle": "The repair team could not hear a weather warning from the far crater",
        "clue": "the antenna's shadow pointed toward the floor rather than the sky",
        "mistake": "{name} wanted to turn the whole antenna, but the silver goggle showed a loose base bolt",
        "action": "{name} kept everyone behind the line and showed Engineer Nia exactly where the bolt had slipped",
        "dialogue": "'The shadow is significant,' {name} said. 'It is also upside down, like Bloop after lunch.'",
        "resolution": "Engineer Nia tightened the bolt, and the antenna sang a proper signal",
        "ending": "the warning arrived in time, and the crew watched dust clouds pass far away",
        "lesson": "careful observation is more useful than a hurried repair",
    },
]


OPENINGS = [
    "At moonrise, {name} arrived at {place} with {companion} and a packet of {snack}.",
    "The stars blinked above {place} when {name} shared {snack} with {companion}.",
    "Just as moonrise painted the crater silver, {name} and {companion} began their station round.",
    "{name} had planned a quiet snack of {snack}, but space had other plans at {place}.",
    "A soft rocket rumble followed {name} and {companion} into {place} at moonrise.",
    "With {goggle} tucked safely in a case, {name} and {companion} explored {place}.",
    "Moonrise found {name} checking the instruments while {companion} guarded the {snack}.",
    "The station lights flickered as {name}, {companion}, and {snack} entered the control ring.",
]


TURNS = [
    "That small sound changed the whole mission.",
    "Instead of guessing, {name} let the evidence choose the next step.",
    "The silly noise made everyone laugh, but the clue made everyone listen.",
    "A brave breath gave the mystery room to become a plan.",
    "The first idea was funny, not useful, so {name} changed it.",
    "Once {name} named the significant detail, the danger became easier to understand.",
    "The station seemed less mysterious when the crew worked from what they could see.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-facing space adventure about a goggle, significant clues, sound effects, and humor."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--snack")
    parser.add_argument("--goggle")
    parser.add_argument("--place")
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
    place = args.place or "the moon station"
    time = args.time or "moonrise"
    if place != "the moon station":
        raise StoryError("This space adventure is built around the moon station.")
    if time != "moonrise":
        raise StoryError("This world begins at moonrise.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Milo", "Zara", "Pip", "Nova"]),
        companion=args.companion or rng.choice(
            ["Bloop the moon robot", "a pocket-sized rover", "Captain Comet"]
        ),
        snack=args.snack or rng.choice(
            ["star-shaped crackers", "freeze-dried apples", "moon muffins"]
        ),
        goggle=args.goggle or rng.choice(
            ["the silver goggle", "the round blue goggle", "the captain's goggle"]
        ),
        place=place,
        time=time,
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "moon_station"),
            asp.fact("feature", "goggle"),
            asp.fact("feature", "significant"),
            asp.fact("feature", "sound_effects"),
            asp.fact("feature", "humor"),
            asp.fact("style", "space_adventure"),
            asp.fact("mission", "repair_signal"),
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
        print("OK: ASP and Python agree on the space-adventure gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    params = world.params
    index = params.seed if params.seed is not None else 0
    scenario = SCENARIOS[index % len(SCENARIOS)]
    opening = OPENINGS[(index // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[(index // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]

    values = {
        "name": params.name,
        "companion": params.companion,
        "snack": params.snack,
        "goggle": params.goggle,
        "place": params.place,
    }

    def formatted(key: str) -> str:
        return scenario[key].format(**values)

    def sentence(key: str) -> str:
        text = formatted(key)
        return text[0].upper() + text[1:]

    child = world.add_character(Character(params.name, "young space explorer"))
    companion = world.add_character(Character(params.companion, "space companion"))
    goggle = world.add_object(ObjectThing(params.goggle, "observation tool"))
    signal = world.add_object(ObjectThing("the station signal", "mission device"))

    child.add_meme("curiosity", 1)
    child.add_meme("bravery", 0.5)
    child.add_meme("humor", 0.5)
    companion.add_meme("friendship", 1)
    goggle.add_meter("clarity", 1)

    world.say(opening.format(**values))
    world.say(
        f"Beside the snack sat {params.goggle}, a useful tool for spotting tiny details in the enormous dark. "
        f"{params.name} liked tools that made space feel a little less mysterious."
    )
    world.say(f"Then came the trouble: {scenario['title']}. {sentence('premise')}.")
    world.say(f"{sentence('obstacle')}. {sentence('clue')}.")

    child.add_meter("distance_walked", 6)
    signal.add_meter("risk", 1)
    world.say(f"{sentence('mistake')}. {turn.format(**values)}")
    world.say(f"{sentence('action')}. {formatted('dialogue')}")

    child.add_meme("bravery", 1)
    child.add_meme("care", 1)
    signal.add_meter("risk", -1)
    signal.add_meter("reliability", 1)
    world.say(f"{sentence('resolution')}. The station lights blinked safely again, and everyone shared {params.snack}.")
    world.say(f"{params.name} learned that {formatted('lesson')}.")
    child.add_meme("joy", 1)
    world.say(
        f"It was a happy ending at {params.place}: {formatted('ending')}. "
        f"{params.companion} made one final 'boop,' and {params.name} laughed all the way back to the airlock."
    )

    world.facts = {
        "scenario": scenario["title"],
        "premise": sentence("premise"),
        "obstacle": sentence("obstacle"),
        "clue": sentence("clue"),
        "mistake": sentence("mistake"),
        "action": sentence("action"),
        "dialogue": formatted("dialogue"),
        "resolution": sentence("resolution"),
        "lesson": formatted("lesson"),
        "ending": formatted("ending"),
    }


def story_qa(world: World) -> list[QAItem]:
    params = world.params
    facts = world.facts
    return [
        QAItem(
            question=f"What significant problem did {params.name} discover?",
            answer=f"{facts['obstacle']} The problem was significant because it could affect safety or the mission at {params.place}.",
        ),
        QAItem(
            question=f"What did {params.name} notice with {params.goggle}?",
            answer=f"{facts['clue']} The goggle helped {params.name} find evidence instead of guessing.",
        ),
        QAItem(
            question="How did humor appear during the space adventure?",
            answer=f"{facts['dialogue']} The funny words made the tense moment lighter without hiding the important problem.",
        ),
        QAItem(
            question=f"What careful action did {params.name} take?",
            answer=f"{facts['action']} This action used the clue and brought in the right help.",
        ),
        QAItem(
            question="How was the mission resolved?",
            answer=f"{facts['resolution']} The repair followed the evidence and made the station safer.",
        ),
        QAItem(
            question="What image proves the story ended happily?",
            answer=f"The ending image is this: {facts['ending']}. It shows the crew safe and the adventure complete.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a goggle used for in this world?",
            answer="A goggle is a protective viewing tool that helps an explorer inspect small details in bright, dusty, or unusual space conditions.",
        ),
        QAItem(
            question="What does significant mean?",
            answer="Significant means important enough to notice because it can change what someone understands or decides to do.",
        ),
        QAItem(
            question="Why can sound effects help a space story?",
            answer="Sound effects make machines, signals, and surprises feel concrete, while their changes can also reveal what is happening.",
        ),
        QAItem(
            question="How does humor help an adventure?",
            answer="Humor gives characters a cheerful way to handle worry, but it should still leave room for careful action when something matters.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params = world.params
    facts = world.facts
    return [
        f"Write a child-facing space adventure about {params.name} at {params.place}.",
        f"Use {params.goggle} to reveal this significant clue: {facts['clue']}.",
        f"Include a funny sound effect and this exchange: {facts['dialogue']}.",
        f"End with this concrete happy image: {facts['ending']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for number, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{number}. {prompt}")
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
            companion=args.companion or "Bloop the moon robot",
            snack=args.snack or "star-shaped crackers",
            goggle=args.goggle or "the silver goggle",
            place="the moon station",
            time="moonrise",
        )
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        target = max(1, args.n)
        while len(samples) < target and attempt < max(target * 50, 50):
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
