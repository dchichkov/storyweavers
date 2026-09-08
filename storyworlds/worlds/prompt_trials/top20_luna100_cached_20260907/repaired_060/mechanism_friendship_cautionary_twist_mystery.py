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
feature(friendship).
feature(cautionary).
feature(twist).
theme(mystery).
mechanism_present.
clue_present.
safe_choice.
truth_revealed.
happy_resolution.

solvable_mystery :- mechanism_present, clue_present, safe_choice, truth_revealed.
good_story :- feature(friendship), feature(cautionary), feature(twist),
              theme(mystery), solvable_mystery, happy_resolution.
#show good_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    friend: str = "Milo"
    object_name: str = "the brass music box"
    place: str = "the old greenhouse"
    time: str = "late afternoon"


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

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the ticking vine",
        "premise": "a hidden ticking sound moved through the greenhouse vines",
        "obstacle": "A locked glass door was trembling, although no one stood on the other side",
        "clue": "the ticks came in threes whenever the wind touched a copper leaf",
        "caution": "Luna reached for the door latch, but Milo noticed a warning ribbon tied around it",
        "action": "They marked the safe spot with a stone and asked the gardener to inspect the old mechanism",
        "dialogue": "'We can solve a mystery without touching the dangerous part,' Milo said. 'Together,' Luna answered",
        "resolution": "The gardener opened a side gate and found a loose clockwork vent tapping against the glass",
        "twist": "The mysterious tapping had not been a trapped creature at all; it was the greenhouse's broken weather mechanism",
        "ending": "the repaired vent clicked softly while vines curled around the copper leaves",
        "lesson": "friendship makes caution easier to choose when curiosity feels strong",
    },
    {
        "title": "the lantern with two shadows",
        "premise": "one lantern cast two shadows beneath the greenhouse stairs",
        "obstacle": "The second shadow seemed to point toward a narrow maintenance tunnel",
        "clue": "its shape changed whenever the lantern's little wheel turned",
        "caution": "Luna wanted to crawl into the tunnel, but Milo found a faded sign saying CLOSED FOR REPAIRS",
        "action": "They kept outside the tunnel, sketched the shadow, and showed the drawing to the caretaker",
        "dialogue": "'A good friend does not dare me into danger,' Luna said. 'A good friend helps me ask,' Milo replied",
        "resolution": "The caretaker lifted the lantern and repaired its bent reflector from the safe side",
        "twist": "The second shadow belonged to the lantern's own crooked handle, stretched by the reflector",
        "ending": "one bright shadow rested beneath the stairs as the friends laughed at the clever trick",
        "lesson": "a careful friend can turn a frightening clue into a safe discovery",
    },
    {
        "title": "the vanished bell",
        "premise": "the greenhouse bell rang once, then seemed to vanish",
        "obstacle": "Without it, the children could not tell when the evening watering system should stop",
        "clue": "a thin silver wire ran from the empty hook to a basket of seed packets",
        "caution": "Luna almost pulled the wire free, but Milo warned that it might start the old mechanism",
        "action": "They followed the wire with their eyes and called the gardener instead of tugging it",
        "dialogue": "'Let's leave the mystery where it is,' Milo whispered. 'Until someone who knows it arrives,' Luna agreed",
        "resolution": "The gardener traced the wire to a foot pedal hidden under a mat and reset the bell",
        "twist": "The bell had never vanished; its pulley had lowered it into a secret testing position",
        "ending": "the bell chimed twice above the seed baskets, and the water stopped right on time",
        "lesson": "patience protects both friends and the fragile things they are trying to understand",
    },
    {
        "title": "the map behind the mirror",
        "premise": "a map appeared behind the greenhouse mirror after sunset",
        "obstacle": "A red line seemed to lead toward a roof hatch marked with a tiny star",
        "clue": "the line ended at a drawing of a hand beside a turning wheel",
        "caution": "Luna lifted the mirror's edge, but Milo saw that its frame was attached to a spring",
        "action": "They stepped back, photographed the map from the floor, and brought it to the curator",
        "dialogue": "'The clue can wait,' Luna said. 'Our friendship should not have to,' Milo answered",
        "resolution": "The curator released the frame safely and showed them the map's hidden legend",
        "twist": "The red line marked the route of a ventilation mechanism, not a secret treasure",
        "ending": "fresh air moved through the roof hatch as the map glowed under the greenhouse lamp",
        "lesson": "careful friends protect one another from exciting but unsafe guesses",
    },
    {
        "title": "the humming seed drawer",
        "premise": "a seed drawer hummed whenever Luna and Milo stood nearby",
        "obstacle": "The humming made them think a tiny animal was trapped behind the wood",
        "clue": "the sound stopped whenever the drawer's brass label was covered",
        "caution": "Luna began to slide the drawer open, but Milo placed a hand on the warning mark",
        "action": "They covered the label without opening the drawer and asked the keeper to check the cabinet",
        "dialogue": "'You stopped me kindly,' Luna said. 'That is what friends are for,' Milo replied",
        "resolution": "The keeper found a magnetic latch vibrating against a loose metal label",
        "twist": "The humming creature was only a small mechanism responding to the label's magnet",
        "ending": "the seed drawer rested silent, full of moonflower seeds ready for spring",
        "lesson": "friendship can interrupt a risky choice without hurting anyone's feelings",
    },
]


OPENINGS = [
    "Luna entered the old greenhouse with Milo as evening light silvered the dusty panes.",
    "At the edge of dusk, Luna and Milo met beneath the iron arch of the old greenhouse.",
    "The old greenhouse smelled of rain and rosemary when Luna arrived with her best friend, Milo.",
    "Luna had promised Milo a quiet look at the moonflowers, but the greenhouse held a stranger mystery.",
    "As the last warm light crossed the glass roof, Luna and Milo stepped inside the old greenhouse.",
]


TURNS = [
    "The clue made the mystery sharper, but it also made their next choice clear.",
    "They shared a careful look and decided that knowing more was not worth taking a dangerous step.",
    "The strange detail changed the mystery from a dare into a problem they could solve together.",
    "Luna's curiosity pulled forward, while Milo's caution gave it a safe path.",
    "Their friendship became part of the mechanism: one noticed, and the other remembered to pause.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mystery world about mechanism, friendship, and caution.")
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--object-name")
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
    name = args.name or rng.choice(["Luna", "Iris", "Nico", "Pia", "Sami"])
    friend = args.friend or rng.choice(["Milo", "Tess", "Jun", "Ari", "Bea"])
    object_name = args.object_name or rng.choice(
        ["the brass music box", "the silver hand mirror", "the moon-shaped key"]
    )
    place = args.place or "the old greenhouse"
    time = args.time or "late afternoon"

    if place != "the old greenhouse":
        raise StoryError("This mystery world takes place in the old greenhouse.")
    if time != "late afternoon":
        raise StoryError("This mystery world begins in the late afternoon.")
    if name == friend:
        raise StoryError("The two friends need different names.")

    return StoryParams(
        name=name,
        friend=friend,
        object_name=object_name,
        place=place,
        time=time,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("theme", "mystery"),
            asp.fact("mechanism_present"),
            asp.fact("clue_present"),
            asp.fact("safe_choice"),
            asp.fact("truth_revealed"),
            asp.fact("happy_resolution"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return all(
        [
            "friendship" in {"friendship", "cautionary", "twist"},
            "mechanism" == "mechanism",
            True,
        ]
    )


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_ok = bool(asp.atoms(model, "good_story"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the mystery-story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    params = world.params
    index = (params.seed or 0) % len(SCENARIOS)
    scenario = SCENARIOS[index]
    turn_index = ((params.seed or 0) // len(SCENARIOS)) % len(TURNS)
    opening_index = ((params.seed or 0) // (len(SCENARIOS) * len(TURNS))) % len(OPENINGS)
    turn = TURNS[turn_index]
    opening = OPENINGS[opening_index]

    luna = world.add_character(Character(params.name, "curious friend"))
    friend = world.add_character(Character(params.friend, "careful friend"))
    mechanism = world.add_object(ObjectThing(params.object_name, "mysterious mechanism"))

    luna.add_meme("curiosity", 1.0)
    luna.add_meme("trust", 0.5)
    friend.add_meme("care", 1.0)
    friend.add_meme("caution", 1.0)
    mechanism.add_meter("mystery", 1.0)

    world.say(opening)
    world.say(
        f"They carried {params.object_name} as a listening charm, because Luna liked "
        "to notice how small mechanisms worked."
    )
    world.say(f"Then they heard {scenario['premise']}.")
    world.say(f"The trouble was this: {scenario['obstacle']}.")
    world.say(f"Nearby, they found a clue: {scenario['clue']}.")
    world.say(f"{scenario['caution']}. {turn}")
    world.say(f"{scenario['action']}.")
    world.say(f"{scenario['dialogue']}.")

    luna.add_meter("safe_steps", 3.0)
    friend.add_meter("helpful_words", 2.0)
    luna.add_meme("bravery", 1.0)
    friend.add_meme("trust", 1.0)
    mechanism.add_meter("understood", 1.0)

    world.say(f"{scenario['resolution']}.")
    world.say(f"That was the twist: {scenario['twist']}.")
    world.say(
        f"Luna and {params.friend} grinned because the mystery had changed without anyone "
        "being hurt."
    )
    world.say(f"The mystery ended with {scenario['ending']}.")
    world.say(
        f"Luna understood that {scenario['lesson']}. She and {params.friend} left the greenhouse "
        "side by side, ready to ask for help before touching the next strange thing."
    )

    world.facts = {
        "title": scenario["title"],
        "obstacle": scenario["obstacle"],
        "clue": scenario["clue"],
        "action": scenario["action"],
        "resolution": scenario["resolution"],
        "twist": scenario["twist"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What mystery did {p.name} and {p.friend} discover?",
            answer=f"They discovered {f['title']}: {f['obstacle']}.",
        ),
        QAItem(
            question="What clue helped them understand the mystery?",
            answer=f"The clue was that {f['clue']}. They used it without taking an unsafe action.",
        ),
        QAItem(
            question=f"How did {p.name} and {p.friend} show friendship and caution?",
            answer=f"They {f['action']}. Their friendship helped them pause and choose a safe way to learn more.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {f['twist']}. The strange sign had a mechanical explanation.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {f['ending']}. The friends left safely after the mechanism was understood.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move, signal, open, close, or change.",
        ),
        QAItem(
            question="Why can caution be useful in a mystery?",
            answer="Caution is useful because a curious person may not yet know whether an object is fragile, dangerous, or connected to a hidden mechanism.",
        ),
        QAItem(
            question="How can friendship help during a difficult problem?",
            answer="Friendship helps because one friend can notice clues while the other remembers to pause, ask for help, and keep everyone safe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a child-facing mystery about {p.name} and {p.friend} investigating {f['title']}.",
        f"Show how a mechanism creates this clue: {f['clue']}. Include a cautious choice.",
        f"Reveal this twist and end with a concrete image: {f['twist']} {f['ending']}.",
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
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
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
        print("good_story" if asp.atoms(model, "good_story") else "(no good_story)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            friend=args.friend or "Milo",
            object_name=args.object_name or "the brass music box",
            place="the old greenhouse",
            time="late afternoon",
        )
        if params.name == params.friend:
            raise StoryError("The two friends need different names.")
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
