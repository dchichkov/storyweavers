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
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% Registry facts define the small superhero world.
feature(twist).
feature(reconciliation).
feature(bacon).
feature(remove).

hero(halcyon).
villain(murmur).
situation(dinner_mishap).
can_fix(reconciliation) :- feature(reconciliation).
can_trigger(twist) :- feature(twist).
has_prop(bacon) :- feature(bacon).
can_remove(remove) :- feature(remove).

good_story :- hero(halcyon), villain(murmur), situation(dinner_mishap), can_fix(reconciliation), can_trigger(twist), has_prop(bacon), can_remove(remove).
#show good_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Captain Comet"
    sidekick_name: str = "Zip"
    city_name: str = "Brindle Bay"
    snack: str = "bacon"
    object_name: str = "the sticky splitter"
    twist_name: str = "Twist"
    reconciliation_name: str = "Reconciliation"


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

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.name] = ch
        return ch

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the bacon ribbon twist",
        "premise": "a bacon ribbon stuck to the city bridge and flapped like a red cape",
        "obstacle": "People were laughing, but the ribbon was also tugging loose the lunch cart latch",
        "clue": "each tug came from a tiny sparking gadget hidden under the bun tray",
        "mistake": "At first, {hero_name} tried to yank the bacon free with one quick pull",
        "action": "{hero_name} stopped, asked {sidekick_name} to hold the cart, and used {object_name} to lift the latch open",
        "dialogue": "'That was a twist I did not expect,' {hero_name} said. 'Then let's solve it together,' {sidekick_name} replied",
        "resolution": "The gadget popped out safely, the bacon ribbon came loose, and the cart rolled back into line",
        "ending": "the bridge lights glowed over a tidy lunch cart while one crisp bacon strip rested on a napkin like a tiny trophy",
        "lesson": "a surprise twist becomes easier when the hero slows down and thinks",
    },
    {
        "title": "the rooftop apology round",
        "premise": "a smoky smell drifted over the rooftops, and it turned out to be burned bacon from the watchtower kitchen",
        "obstacle": "Murmur the prankster had hidden the pan lid, so the cook could not cool the pan fast enough",
        "clue": "the missing lid left a silver trail of grease footprints toward the rain barrel",
        "mistake": "{hero_name} nearly blamed Murmur before checking the trail",
        "action": "{hero_name} followed the footprints, found the lid wedged by the barrel, and asked Murmur why he had taken it",
        "dialogue": "'I wanted a joke, not a mess,' Murmur muttered. 'Then let's make it right,' said {hero_name}",
        "resolution": "Together they cleaned the stove, cooled the pan, and returned the lid to the cook",
        "ending": "by sunset, Murmur and the cook were sharing a plate of bacon biscuits on the warm roof",
        "lesson": "reconciliation starts when somebody tells the truth and helps repair the harm",
    },
    {
        "title": "the sideways rescue sign",
        "premise": "the rescue sign on Main Street had been hung sideways, so every beep from the alarm looked like a joke",
        "obstacle": "The tilted sign pointed lost visitors toward the alley instead of the safe shelter",
        "clue": "one bolt had vanished, and bacon grease from the diner door covered the loose bracket",
        "mistake": "{hero_name} wanted to fly up and twist the sign straight immediately",
        "action": "{hero_name} asked {sidekick_name} to remove the broken bracket first, then replaced it with a spare from the tool belt",
        "dialogue": "'Remove the broken part before fixing the rest,' {sidekick_name} said. 'Exactly,' {hero_name} answered",
        "resolution": "The sign hung true again, and the shelter door lights pointed everyone the right way",
        "ending": "the alley grew quiet while the clean red sign shone over the street like a hero's smile",
        "lesson": "careful removal can be the bravest part of a fix",
    },
    {
        "title": "the bacon cloud over the parade",
        "premise": "a parade float rolled by with a bacon-cloud cannon that puffed too much smoke",
        "obstacle": "The smoke hid a little child waving for help near the curb",
        "clue": "the cloud thinned whenever the cannon wheel spun backward",
        "mistake": "{hero_name} first shouted for everyone to run, which only made the crowd panic",
        "action": "{hero_name} took one breath, asked the band to stop, and told {sidekick_name} to remove the cannon cap",
        "dialogue": "'I can see now,' said the child. 'Good,' said {hero_name}, 'then let's keep it that way.'",
        "resolution": "The cap came off, the smoke drifted away, and the child joined the parade with a waving ribbon",
        "ending": "the float finished under blue sky, with one harmless bacon banner fluttering behind it",
        "lesson": "a calm plan can turn a twist into a rescue",
    },
    {
        "title": "the caped lunch switch",
        "premise": "someone had switched the hero's lunch with a giant bacon sandwich wrapped in a cape",
        "obstacle": "The sandwich kept sticking to the control panel in the patrol tower",
        "clue": "a note under the bun said, TWIST FIRST, ASK LATER",
        "mistake": "{hero_name} laughed and almost ate the sandwich before noticing the note was from {sidekick_name}",
        "action": "{hero_name} found {sidekick_name}, who explained the sandwich hid a broken button that needed removal",
        "dialogue": "'It was a prank with a purpose,' {sidekick_name} said. 'Then we fix it with purpose too,' replied {hero_name}",
        "resolution": "The button was removed, the panel worked again, and the sandwich was finally shared at lunch",
        "ending": "two capes hung from the chair backs while bacon crumbs sparkled on the tower table",
        "lesson": "good friends can turn a prank into a practical repair",
    },
    {
        "title": "the alley of sorry notes",
        "premise": "the alley wall was covered in sorry notes after a noisy hero training day",
        "obstacle": "Murmur had glued the notes over the door handle, and nobody could get into the community room",
        "clue": "a fresh line of glue dripped from one note that said, I CAN HELP",
        "mistake": "{hero_name} almost ripped the notes away, but that would have torn the apologies too",
        "action": "{hero_name} asked Murmur to remove the glue himself, then helped him carry a bucket of warm water",
        "dialogue": "'I made the mess,' Murmur said. 'And now you can help unmake it,' said {hero_name}",
        "resolution": "The door opened, the notes stayed whole, and the room filled with neighbors talking calmly",
        "ending": "the wall kept one note that read THANK YOU in black crayon beside a paper bacon star",
        "lesson": "reconciliation keeps the apology and the repair together",
    },
    {
        "title": "the twist in the tunnel",
        "premise": "a tunnel under the city made a strange twist in the map and led straight toward the bakery",
        "obstacle": "The bakery ovens were heating up too fast, and the tunnel warm air fed them even more",
        "clue": "the warm air stopped when {sidekick_name} held a cold metal tray over the vent",
        "mistake": "{hero_name} guessed the vent was blocked and started to punch the wall",
        "action": "{hero_name} paused, listened, and let {sidekick_name} remove the loose vent cover with a wrench",
        "dialogue": "'That was close,' said {sidekick_name}. 'Yes,' said {hero_name}, 'and now we know the real problem.'",
        "resolution": "The vent cleared, the ovens settled, and the bakery kept every loaf from burning",
        "ending": "steam curled safely from the roof while one golden loaf cooled beside a plate of bacon rolls",
        "lesson": "a twist in the path is easier to handle when the hero listens first",
    },
    {
        "title": "the mirror of reconciliation",
        "premise": "the city museum displayed a mirror that showed every hero and villain wearing the same worried face",
        "obstacle": "The mirror had cracked during a quarrel, and its shards kept reflecting angry memories back and forth",
        "clue": "when anyone said sorry, the crack stopped shining for a moment",
        "mistake": "{hero_name} tried to cover the mirror with a curtain, but the reflections still leaked around the edges",
        "action": "{hero_name} invited Murmur to speak honestly, then asked the curator to remove the shattered backing",
        "dialogue": "'I broke the calm,' Murmur said. 'And I can help mend it,' said {hero_name}",
        "resolution": "The mirror was repaired, the room grew quiet, and the old argument finally lost its hold",
        "ending": "the restored mirror held one clear image of two faces smiling beside a plate of bacon at the museum cafe",
        "lesson": "reconciliation is a stronger shield than pretending nothing happened",
    },
]


OPENINGS = [
    "In bright daytime at {city_name}, {hero_name} and {sidekick_name} heard trouble before they saw it.",
    "The sun was high over {city_name} when {hero_name} zipped across the avenue with {sidekick_name}.",
    "{city_name} buzzed like a comic-book panel as {hero_name} arrived for a calm patrol.",
    "On a busy afternoon in {city_name}, {hero_name} noticed a problem hiding behind an ordinary lunch break.",
    "{hero_name} and {sidekick_name} were halfway through a rooftop snack when the city called for help.",
]

TURNS = [
    "Then the scene took a twist that changed the plan.",
    "That twist made the problem look different, and {hero_name} had to think again.",
    "The first idea was fast, but the better idea was careful.",
    "A small detail turned the whole rescue from loud to smart.",
    "Instead of rushing, {hero_name} chose a move that could also help the feelings in the room.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with bacon, twist, and reconciliation.")
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--city-name")
    ap.add_argument("--snack")
    ap.add_argument("--object-name")
    ap.add_argument("--twist-name")
    ap.add_argument("--reconciliation-name")
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
    hero_name = args.hero_name or rng.choice(["Captain Comet", "Solar Spark", "The Blue Comet", "Star Shield"])
    sidekick_name = args.sidekick_name or rng.choice(["Zip", "Pepper", "Midge", "Nova"])
    city_name = args.city_name or rng.choice(["Brindle Bay", "Pineport", "Sunrise City"])
    snack = args.snack or "bacon"
    object_name = args.object_name or rng.choice(["the sticky splitter", "the silver wrench", "the quiet latch"])
    twist_name = args.twist_name or "Twist"
    reconciliation_name = args.reconciliation_name or "Reconciliation"
    if snack != "bacon":
        raise StoryError("This world uses bacon as the seed snack.")
    return StoryParams(
        seed=None,
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        city_name=city_name,
        snack=snack,
        object_name=object_name,
        twist_name=twist_name,
        reconciliation_name=reconciliation_name,
    )


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("feature", "bacon"),
            asp.fact("feature", "remove"),
            asp.fact("hero", "halcyon"),
            asp.fact("villain", "murmur"),
            asp.fact("situation", "dinner_mishap"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/0."))
    asp_ok = bool(asp.atoms(model, "good_story"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the superhero story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    story_seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[story_seed % len(SCENARIOS)]
    opening = OPENINGS[(story_seed // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[(story_seed // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]
    values = {
        "hero_name": p.hero_name,
        "sidekick_name": p.sidekick_name,
        "city_name": p.city_name,
        "object_name": p.object_name,
        "snack": p.snack,
    }

    hero = world.add_character(Character(name=p.hero_name, role="hero"))
    sidekick = world.add_character(Character(name=p.sidekick_name, role="sidekick"))
    villain = world.add_character(Character(name="Murmur", role="villain"))
    gadget = world.add_object(ObjectThing(name=p.object_name, kind="tool"))
    bacon = world.add_object(ObjectThing(name="bacon", kind="snack"))

    hero.add_meme("duty", 1)
    hero.add_meme("curiosity", 1)
    sidekick.add_meme("loyalty", 1)

    world.say(opening.format(**values))
    world.say(
        f"{p.hero_name} carried a lunch box with {p.snack} inside, and {p.sidekick_name} carried the map to the plaza."
    )
    world.say(f"The trouble was called {scenario['title']}: {scenario['premise']}.")
    world.say(f"{scenario['obstacle']}. {scenario['clue']}.")

    hero.add_meter("flight", 7)
    sidekick.add_meter("helpfulness", 2)
    world.say(f"{scenario['mistake'].format(**values)}. {turn.format(**values)}")
    world.say(f"{scenario['action'].format(**values)}. {scenario['dialogue'].format(**values)}")

    hero.add_meme("patience", 1)
    villain.add_meme("relief", 1)
    gadget.add_meter("fixed", 1)
    bacon.add_meter("shared", 1)
    world.say(
        f"{scenario['resolution']}. Then {p.hero_name} and {p.sidekick_name} shared the bacon and gave Murmur a clean plate."
    )
    world.say(
        f"That was {p.reconciliation_name}: nobody pretended the mess had never happened, but everybody could look each other in the eye."
    )
    world.say(
        f"By the end, {scenario['ending']}. {p.hero_name} smiled at {p.sidekick_name} and said, "
        f"'A twist can be surprising, but reconciliation is what makes the ending stick.'"
    )

    world.facts = {
        "hero_name": p.hero_name,
        "sidekick_name": p.sidekick_name,
        "city_name": p.city_name,
        "snack": p.snack,
        "object_name": p.object_name,
        "scenario": scenario["title"],
        "obstacle": scenario["obstacle"],
        "clue": scenario["clue"],
        "resolution": scenario["resolution"],
        "ending_image": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What problem did {p.hero_name} notice in {p.city_name}?",
            answer=f"{f['obstacle']}. It mattered because the city needed a safe, calm fix.",
        ),
        QAItem(
            question="What clue helped the hero change the plan?",
            answer=f"{f['clue']}. That clue showed the hero where to look instead of letting the first guess control the story.",
        ),
        QAItem(
            question="How did the hero show both twist-awareness and reconciliation?",
            answer=f"{f['resolution']}. The hero solved the physical problem and also made room for peace after the trouble.",
        ),
        QAItem(
            question="What is the ending image?",
            answer=f"{f['ending_image']}. It proves the world changed by showing the scene after the rescue and repair.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero story?",
            answer="A superhero story is a tale where someone with courage, skill, and care steps in to help others.",
        ),
        QAItem(
            question="What does remove mean in this world?",
            answer="Remove means to take away the broken, harmful, or stuck part so the bigger fix can happen safely.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a conflict by being honest, kind, and ready to repair harm.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a superhero story in {p.city_name} where {p.hero_name} deals with {f['scenario']} and bacon is part of the problem.",
        f"Show a twist through this clue: {f['clue']}. Let the hero choose a careful remove-and-fix action.",
        f"End with reconciliation and a concrete ending image: {f['ending_image']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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
    for ch in world.characters.values():
        lines.append(f"  {ch.name} ({ch.role}) meters={ch.meters} memes={ch.memes}")
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show good_story/0."))
        print("good_story" if asp.atoms(model, "good_story") else "(no good_story)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            hero_name=args.hero_name or "Captain Comet",
            sidekick_name=args.sidekick_name or "Zip",
            city_name=args.city_name or "Brindle Bay",
            snack="bacon",
            object_name=args.object_name or "the sticky splitter",
            twist_name=args.twist_name or "Twist",
            reconciliation_name=args.reconciliation_name or "Reconciliation",
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
