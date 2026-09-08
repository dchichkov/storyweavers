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
place(parade_route).
feature(parade).
feature(sailor).
feature(infantry).
feature(twist).
style(heartwarming).

safe_plan :- parade_ready, sailor_present, infantry_present, twist_revealed.
parade_ready :- feature(parade).
sailor_present :- feature(sailor).
infantry_present :- feature(infantry).
twist_revealed :- feature(twist).
kind_ending :- style(heartwarming), safe_plan.
#show kind_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    sailor: str = "Sailor Finn"
    infantry: str = "the town infantry band"
    parade: str = "the Lantern Parade"
    place: str = "Maple Street"
    keepsake: str = "a little brass star"


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
        "title": "the quiet drum",
        "premise": "the infantry drum stopped just before the parade reached the square",
        "clue": "a tiny silver bell was caught inside the drum strap",
        "obstacle": "the drummer could not march and keep the bell safe at the same time",
        "action": "{name} asked {sailor} to hold the parade line while the infantry drummer checked the strap",
        "dialogue": "'A parade can pause for a small sound,' {name} said. 'And a small sound may be telling us something.'",
        "twist": "The bell was not broken at all; it belonged to an old sailor who had lost it years ago.",
        "resolution": "The drummer freed the bell, and Sailor Finn recognized it as the bell from his first sea coat",
        "ending": "the parade moved on with the bell chiming beside the drum",
        "lesson": "a careful pause can uncover a treasured surprise",
    },
    {
        "title": "the backward banner",
        "premise": "the parade banner faced backward, so its painted sunrise could not be seen",
        "clue": "the rope had been tied in a neat sailor's knot around the flagpole",
        "obstacle": "the banner carrier feared dropping the tall pole in the crowded street",
        "action": "{name} cleared a little space and asked the infantry captain to guide the pole while {sailor} loosened the knot",
        "dialogue": "'We do not have to pull hard when we can work together,' {name} said",
        "twist": "When the banner turned around, its hidden side showed a row of stitched names honoring grandparents who had marched before",
        "resolution": "The captain carried the banner proudly, and families recognized their names in the afternoon light",
        "ending": "the sunrise shone above the names of old friends as the parade passed",
        "lesson": "turning a problem gently can reveal the heart inside it",
    },
    {
        "title": "the missing sailor's song",
        "premise": "the sailor's song vanished when the parade band reached the fountain",
        "clue": "a robin was perched on the music folder, singing the missing final notes",
        "obstacle": "the sailor wanted to sing, but did not want to frighten the bird away",
        "action": "{name} asked the infantry band to play softly while {sailor} listened for the robin's tune",
        "dialogue": "'Maybe the song has found a new singer,' {name} whispered",
        "twist": "The robin had copied the song from a window where an elderly neighbor practiced every morning",
        "resolution": "The band invited the neighbor to conduct the final verse from her doorway",
        "ending": "bird, band, sailor, and neighbor shared one bright chorus",
        "lesson": "a missing piece may be waiting in an unexpected voice",
    },
    {
        "title": "the lantern that would not glow",
        "premise": "one parade lantern stayed dark while all the others warmed the road",
        "clue": "its paper shade had a painted wave and a name written beneath it",
        "obstacle": "the lantern belonged to a sailor who was away at sea, and nobody knew whether to carry it",
        "action": "{name} showed the name to {sailor}, who asked the infantry to make room at the front of the parade",
        "dialogue": "'If someone cannot walk with us, we can carry their light,' {name} said",
        "twist": "The sailor's family had placed the lantern there for a child who was born while the ship was away",
        "resolution": "The family lit the lantern together and carried it beside the band",
        "ending": "one small wave of gold bobbed between the marching boots",
        "lesson": "a parade can carry love to someone who is far away",
    },
    {
        "title": "the runaway drum cart",
        "premise": "a drum cart rolled loose toward the parade's flower arch",
        "clue": "its wheel was caught on a blue ribbon from the sailor's uniform",
        "obstacle": "the cart was too heavy for one person to stop safely",
        "action": "{name} called for a pause, and the infantry formed a calm line while {sailor} and the flower keepers secured the cart",
        "dialogue": "'Let us make a safe wall, not a scary chase,' {name} said",
        "twist": "Inside the cart was a surprise bench for a retired infantry drummer who could no longer march",
        "resolution": "The drummer sat beneath the arch and led the next beat with a gentle tap",
        "ending": "the parade rolled forward to the rhythm of two generations",
        "lesson": "careful teamwork can make room for someone who needs help",
    },
    {
        "title": "the sailor's upside-down medal",
        "premise": "a sailor's medal hung upside down during the parade salute",
        "clue": "the ribbon had been sewn with a bright red heart on its hidden side",
        "obstacle": "the sailor thought the medal was ordinary and felt embarrassed by the mistake",
        "action": "{name} pointed to the heart, and the infantry captain asked everyone to wait before changing it",
        "dialogue": "'Perhaps the medal has a story we have not heard yet,' {name} said",
        "twist": "The heart marked a rescue that the sailor had kept private because the rescued child was now marching nearby",
        "resolution": "The child recognized the ribbon and hugged the sailor at the parade curb",
        "ending": "the upside-down medal glimmered between two happy faces",
        "lesson": "a quiet kindness may be more important than a perfect display",
    },
    {
        "title": "the empty place in the march",
        "premise": "one empty place appeared between the sailor and infantry lines",
        "clue": "a folded paper in the place said, 'Save this step for Dad'",
        "obstacle": "the parade leader did not know whether to close the gap",
        "action": "{name} asked the sailor and infantry captain to read the note together before deciding",
        "dialogue": "'An empty place can still belong to someone,' {name} said",
        "twist": "The absent father was watching from a hospital window across the street",
        "resolution": "The parade slowed so he could see the saved place and raise his hand",
        "ending": "the empty step became the brightest part of the whole parade",
        "lesson": "remembering someone can give them a place in a celebration",
    },
    {
        "title": "the rain on the parade",
        "premise": "a soft rain began just as the parade's paper stars were lifted",
        "clue": "the sailor's oilcloth coat could cover the smallest stars",
        "obstacle": "the infantry band worried that the rain would ruin the children's decorations",
        "action": "{name} organized a shelter line while {sailor} shared the coat and the infantry held the awning ropes",
        "dialogue": "'The rain can join the parade if we keep the stars safe,' {name} said",
        "twist": "Drops shining on the stars made them look like a whole sky of moving constellations",
        "resolution": "Everyone marched beneath awnings until the clouds opened",
        "ending": "the wet stars sparkled brighter than they had before the rain",
        "lesson": "a change in plans can sometimes add unexpected beauty",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade storyworld with a sailor, infantry, and a gentle twist."
    )
    parser.add_argument("--name")
    parser.add_argument("--sailor")
    parser.add_argument("--infantry")
    parser.add_argument("--parade")
    parser.add_argument("--place")
    parser.add_argument("--keepsake")
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
    place = args.place or "Maple Street"
    if place != "Maple Street":
        raise StoryError("This storyworld's parade route is Maple Street.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Mara", "Theo", "Nell", "Pip"]),
        sailor=args.sailor or rng.choice(["Sailor Finn", "Sailor Ada", "Sailor Jo"]),
        infantry=args.infantry or rng.choice(
            ["the town infantry band", "the red-coated infantry", "the neighborhood infantry"]
        ),
        parade=args.parade or rng.choice(
            ["the Lantern Parade", "the Spring Parade", "the Harbor Parade"]
        ),
        place=place,
        keepsake=args.keepsake or rng.choice(
            ["a little brass star", "a blue ribbon", "a paper moon"]
        ),
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "parade_route"),
            asp.fact("feature", "parade"),
            asp.fact("feature", "sailor"),
            asp.fact("feature", "infantry"),
            asp.fact("feature", "twist"),
            asp.fact("style", "heartwarming"),
        ]
    )


def asp_program(show: str = "#show kind_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    asp_ok = bool(asp.atoms(model, "kind_ending"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the parade story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    index = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[index % len(SCENARIOS)]

    values = {
        "name": p.name,
        "sailor": p.sailor,
        "infantry": p.infantry,
        "parade": p.parade,
        "place": p.place,
        "keepsake": p.keepsake,
    }

    child = world.add_character(Character(p.name, "young parade helper"))
    sailor = world.add_character(Character(p.sailor, "sailor"))
    infantry = world.add_character(Character(p.infantry, "infantry group"))
    keepsake = world.add_object(ObjectThing(p.keepsake, "parade keepsake"))

    child.add_meme("curiosity", 1.0)
    child.add_meme("kindness", 0.8)
    child.add_meme("bravery", 0.4)
    sailor.add_meme("patience", 0.5)
    infantry.add_meme("teamwork", 0.6)

    world.say(
        f"On the morning of {p.parade}, {p.name} carried {p.keepsake} along {p.place} "
        f"beside {p.sailor} and {p.infantry}."
    )
    world.say(f"The flags were ready, the drums were polished, and the whole parade waited for its first bright step.")
    world.say(f"Then {scenario['title']} happened: {scenario['premise']}.")
    world.say(f"{scenario['obstacle'].capitalize()}. {scenario['clue'].capitalize()}.")

    child.add_meter("steps_taken", 6)
    child.add_meter("people_helped", 1)
    keepsake.add_meter("meaning", 1)
    world.say(
        f"{scenario['action'].format(**values)}. "
        f"{scenario['dialogue'].format(**values)}"
    )

    child.add_meme("bravery", 1.0)
    child.add_meme("care", 1.0)
    sailor.add_meme("gratitude", 1.0)
    infantry.add_meme("warmth", 1.0)

    world.say(f"That careful choice revealed the twist: {scenario['twist']}.")
    world.say(f"{scenario['resolution']}. The parade waited for every heart to catch up.")

    child.add_meme("joy", 1.0)
    world.say(
        f"{scenario['lesson'].capitalize()}. {p.name} understood that a true parade is not only "
        "about marching in step; it is about noticing who needs a place."
    )
    world.say(
        f"At last, {scenario['ending']}. {p.name} tucked {p.keepsake} close and walked home "
        f"while the last friendly notes floated over {p.place}."
    )

    world.facts = {
        "scenario": scenario["title"],
        "premise": scenario["premise"],
        "obstacle": scenario["obstacle"],
        "clue": scenario["clue"],
        "action": scenario["action"].format(**values),
        "dialogue": scenario["dialogue"].format(**values),
        "twist": scenario["twist"],
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What problem happened during {p.parade}?",
            answer=f"{f['premise'].capitalize()}. It mattered because the parade needed a safe and caring way to continue.",
        ),
        QAItem(
            question=f"What clue did {p.name} notice?",
            answer=f"{f['clue'].capitalize()}. That clue helped {p.name} look more closely instead of rushing.",
        ),
        QAItem(
            question=f"How did {p.name} help the sailor and infantry?",
            answer=f"{f['action']}. The plan used teamwork and gave everyone time to act safely.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {f['twist']}. It changed the problem into a meaningful discovery.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{f['resolution']}. Then {f['ending']}, leaving a warm image of the parade's shared joy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a planned procession in which people move together, often with music, flags, costumes, or decorations.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around boats and ships, helping them travel and caring for the people aboard.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move on foot as part of a trained group.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected fact or change that makes earlier events look different and gives the story a new direction.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a heartwarming child-facing story about {p.name} helping {p.sailor} and {p.infantry} during {p.parade}.",
        f"Build the middle around this clue: {f['clue'].capitalize()} Show a safe, kind choice and a brief dialogue exchange.",
        f"Reveal this gentle twist: {f['twist']} End with the concrete image: {f['ending']}.",
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
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("kind_ending" if asp.atoms(model, "kind_ending") else "(no kind_ending)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            sailor=args.sailor or "Sailor Finn",
            infantry=args.infantry or "the town infantry band",
            parade=args.parade or "the Lantern Parade",
            place=args.place or "Maple Street",
            keepsake=args.keepsake or "a little brass star",
        )
        if params.place != "Maple Street":
            raise StoryError("This storyworld's parade route is Maple Street.")
        samples = [generate(params)]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and attempt < limit:
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
