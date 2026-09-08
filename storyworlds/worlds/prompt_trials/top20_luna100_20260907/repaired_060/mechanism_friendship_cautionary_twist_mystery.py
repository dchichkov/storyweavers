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
mystery(mechanism).
safe_method(listen_and_inspect).
helpful(friendship) :- feature(friendship).
careful(cautionary) :- feature(cautionary).
revealing_twist(mystery) :- feature(twist), mystery(mechanism).
solved :- helpful(friendship), careful(cautionary), revealing_twist(mystery),
          safe_method(listen_and_inspect).
#show solved/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    friend: str = "Milo"
    place: str = "the old clockwork greenhouse"
    object_name: str = "the brass humming box"
    snack: str = "cinnamon pears"


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
        "title": "the ticking seed drawer",
        "premise": "a locked seed drawer ticked three times whenever the greenhouse fan turned",
        "obstacle": "the rare moon seeds inside were needed before night, but the drawer's key was missing",
        "clue": "a smear of blue pollen ran from the drawer to a loose gear beneath the fan",
        "twist": "the ticking was not a warning clock at all; it was the drawer asking the fan to slow down",
        "caution": "Luna almost forced the lock with a garden hook, but the gear shivered when she touched it",
        "action": "Luna and Milo stopped the fan, counted its safe clicks, and followed the pollen to a tiny release lever",
        "resolution": "The lever opened the drawer without breaking its delicate mechanism",
        "ending": "moon seeds gleamed in their paper packets while the quiet fan breathed over sleeping vines",
        "lesson": "a mystery can hide a request for help, so friendship and caution belong together",
    },
    {
        "title": "the lantern under the pond",
        "premise": "a green light blinked beneath the lily pond whenever someone rang the garden bell",
        "obstacle": "Luna and Milo feared that a lost creature was trapped below the water",
        "clue": "the blink always came two breaths after the bell, and a silver cord vanished into the reeds",
        "twist": "the light came from a pond-cleaning wheel, not a trapped creature",
        "caution": "Milo reached toward the cord, but Luna noticed the reeds twitching around a hidden paddle",
        "action": "They kept their hands out of the water and asked the gardener to lift the inspection grate",
        "resolution": "The gardener freed a leaf from the wheel and showed them the harmless lantern mechanism",
        "ending": "the pond shone with clear green reflections, and two frogs settled beside the repaired wheel",
        "lesson": "friends protect one another by checking a strange clue before touching it",
    },
    {
        "title": "the whispering gate",
        "premise": "the greenhouse gate whispered a name whenever the evening latch moved",
        "obstacle": "Luna worried that someone was hiding outside, while Milo wanted to open the gate quickly",
        "clue": "the whisper repeated only when the wind pulled a thread across a row of seed bells",
        "twist": "the gate was not calling a person; its hollow hinge was carrying the bells' sound",
        "caution": "Milo raised the latch, but Luna held it still before the rusty hinge could snap",
        "action": "Together they tied back the thread and invited the caretaker to oil the hinge",
        "resolution": "The whisper became an ordinary chime, and the gate opened smoothly",
        "ending": "warm bell notes floated over the path as Luna and Milo walked home side by side",
        "lesson": "caution gives friendship time to replace a frightening guess with the truth",
    },
    {
        "title": "the missing wheel",
        "premise": "a little water wheel vanished from the greenhouse's bright irrigation table",
        "obstacle": "the upper plants were drying, and muddy tracks led toward a locked tool shed",
        "clue": "one track ended at a nest made from copper wire and soft moss",
        "twist": "the wheel had not been stolen; a mother wren had carried its loose spokes to build a nest",
        "caution": "Luna wanted to pull the nest away, but Milo heard tiny chicks beneath it",
        "action": "They called the caretaker, who replaced the wheel and moved the nest to a safe shelf",
        "resolution": "Water reached the plants, and the wren family kept its warm new home",
        "ending": "fresh droplets rolled down every leaf while copper-colored wings fluttered above the shelf",
        "lesson": "a careful friendship can solve a problem without harming a smaller neighbor",
    },
    {
        "title": "the map that changed",
        "premise": "a painted map in the greenhouse turned one path red whenever Luna and Milo stood together",
        "obstacle": "the red path led toward a cracked glass roof marked for repair",
        "clue": "the color appeared only when both friends stepped on two brass floor plates",
        "twist": "the map was a safety mechanism, not a prophecy; it warned when their combined weight shook the old walkway",
        "caution": "Milo suggested crossing quickly, but Luna backed away from the trembling boards",
        "action": "They tested the plates from a safe distance and fetched a repair ladder",
        "resolution": "The caretaker braced the walkway and reset the map's warning mechanism",
        "ending": "the map returned to blue, pointing toward a sound wooden path beneath the glass roof",
        "lesson": "when a mystery gives a caution, good friends listen before they move",
    },
    {
        "title": "the vanished breakfast bell",
        "premise": "the breakfast bell rang from somewhere inside the walls, though its hook stood empty",
        "obstacle": "the greenhouse children searched every room and still could not find the bell",
        "clue": "a warm vibration traveled through the pipes beside a cupboard of old tools",
        "twist": "the bell had rolled into a maintenance tube, where a turning water valve made it ring",
        "caution": "Luna nearly pushed a stick into the tube, but Milo pointed to the warning mark painted beside it",
        "action": "They marked the tube, told the caretaker, and listened while she shut the valve",
        "resolution": "The bell slid out safely when the tube was opened from its service hatch",
        "ending": "breakfast began with one gentle ring and a table bright with shared fruit",
        "lesson": "friendship means stopping a risky idea and choosing a safer way to learn",
    },
    {
        "title": "the shadow in the gear room",
        "premise": "a tall shadow moved across the gear room even when the lamps were still",
        "obstacle": "Luna and Milo thought a stranger had entered the locked greenhouse",
        "clue": "the shadow's arm always pointed toward a small pulley above the west window",
        "twist": "the stranger was a sun-powered shade mechanism, throwing its own silhouette across the wall",
        "caution": "Milo reached for the door bolt, but Luna noticed dust on the inside of the lock",
        "action": "They stayed together, examined the window from the hall, and called the caretaker",
        "resolution": "The caretaker freed a stuck pulley and showed how sunlight had made the moving shadow",
        "ending": "the gear room held only honest shadows, turning slowly while the friends laughed with relief",
        "lesson": "staying together and checking evidence can turn fear into understanding",
    },
    {
        "title": "the silver drip",
        "premise": "silver drops fell upward from a pipe near the winter roses",
        "obstacle": "the strange leak was pulling water away from the roots",
        "clue": "each drop rose when the nearby pressure wheel made a sharp click",
        "twist": "the pipe was not leaking upward; a hidden suction valve was reversing the water flow",
        "caution": "Luna started to twist the wheel, but Milo read the faded arrow that warned against turning it alone",
        "action": "They shut the aisle gate, found the valve number, and brought the greenhouse mechanic",
        "resolution": "The mechanic reset the valve and sent water gently back to the roses",
        "ending": "ordinary drops rested on the rose leaves like tiny silver buttons",
        "lesson": "a cautionary sign is a friend speaking through paint, even when the mystery feels exciting",
    },
]


OPENINGS = [
    "On a cool afternoon, {name} carried {snack} to {place} with {friend}.",
    "{name} and {friend} entered {place} together, saving {snack} for after their work.",
    "Rain tapped the roof of {place} when {name} and {friend} arrived with {snack}.",
    "The glass roof glowed softly as {name} shared {snack} with {friend} inside {place}.",
    "{name} had promised {friend} a quiet tour of {place}, with {snack} tucked in a cloth bag.",
    "At the end of the school day, {name} and {friend} brought {snack} into {place}.",
]


TURNS = [
    "The new detail changed their question.",
    "A mystery was easier to face when the friends named what they actually knew.",
    "Instead of guessing faster, they decided to observe more carefully.",
    "The warning did not end the adventure; it showed them how to continue safely.",
    "Luna and Milo looked at each other and made the same careful choice.",
    "That small sound turned their first idea upside down.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery world about mechanisms, friendship, and cautious discoveries."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--place")
    parser.add_argument("--object-name")
    parser.add_argument("--snack")
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
    name = args.name or rng.choice(["Luna", "Nora", "Iris", "Pia", "Zane"])
    friend = args.friend or rng.choice(["Milo", "Tess", "Owen", "Aya", "Finn"])
    place = args.place or "the old clockwork greenhouse"
    object_name = args.object_name or rng.choice(
        ["the brass humming box", "the silver gear case", "the little blue mechanism"]
    )
    snack = args.snack or rng.choice(["cinnamon pears", "berry buns", "warm oat cakes"])
    if not place:
        raise StoryError("The mystery needs a setting.")
    if name == friend:
        raise StoryError("The main character and friend must have different names.")
    return StoryParams(
        seed=None,
        name=name,
        friend=friend,
        place=place,
        object_name=object_name,
        snack=snack,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("mystery", "mechanism"),
            asp.fact("safe_method", "listen_and_inspect"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return bool(SCENARIOS) and all(
        scenario.get("twist")
        and scenario.get("caution")
        and scenario.get("action")
        and scenario.get("resolution")
        for scenario in SCENARIOS
    )


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0."))
    asp_ok = bool(asp.atoms(model, "solved"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        for seed in range(min(10, len(SCENARIOS) * 2)):
            params = StoryParams(seed=seed)
            sample = generate(params)
            if not sample.story or len(sample.story_qa) < 4:
                print("MISMATCH: generated story verification failed")
                return 1
        print("OK: ASP and Python agree, and generated stories passed.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[(seed // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]

    values = {
        "name": p.name,
        "friend": p.friend,
        "place": p.place,
        "object_name": p.object_name,
        "snack": p.snack,
    }

    luna = world.add_character(Character(p.name, "curious friend"))
    friend = world.add_character(Character(p.friend, "careful friend"))
    mechanism = world.add_object(ObjectThing(p.object_name, "mysterious mechanism"))

    luna.add_meme("curiosity", 1)
    luna.add_meme("caution", 0.5)
    friend.add_meme("friendship", 1)
    friend.add_meme("caution", 0.75)
    mechanism.add_meter("mystery", 1)

    world.say(opening.format(**values))
    world.say(
        f"Near the entrance stood {p.object_name}, a small device whose brass teeth "
        f"seemed to remember every sound in {p.place}."
    )
    world.say(f"Then they noticed {scenario['title']}: {scenario['premise']}.")
    world.say(f"The trouble was clear: {scenario['obstacle']}.")
    world.say(f"They found a clue: {scenario['clue']}. {turn}")
    world.say(f"{scenario['caution']}.")
    world.say(f'"Let us not pull anything yet," {p.friend} said. "{p.name}, can we inspect it together?"')
    world.say(f'"Together," {p.name} replied. "If it is a mechanism, it may be trying to tell us something."')
    world.say(f"The friends chose a safe plan. {scenario['action']}.")
    mechanism.add_meter("understanding", 1)
    luna.add_meme("bravery", 1)
    friend.add_meme("trust", 1)
    world.say(f"Then came the twist: {scenario['twist']}.")
    world.say(f"{scenario['resolution']}. They opened the cloth bag and shared {p.snack}.")
    world.say(
        f"{p.name} understood that {scenario['lesson']}. "
        "The mystery had changed because their careful friendship changed what they did next."
    )
    world.say(
        f"At last, {scenario['ending']}. "
        f"{p.name} and {p.friend} left {p.place} with the mechanism quiet, understood, and safe."
    )

    world.facts = {
        "title": scenario["title"],
        "premise": scenario["premise"],
        "obstacle": scenario["obstacle"],
        "clue": scenario["clue"],
        "twist": scenario["twist"],
        "caution": scenario["caution"],
        "action": scenario["action"],
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What mystery did {p.name} and {p.friend} find?",
            answer=f"They found {f['title']}: {f['premise']}.",
        ),
        QAItem(
            question="What clue helped the friends investigate?",
            answer=f"{f['clue']}. The clue mattered because it connected the strange event to a mechanism rather than a wild guess.",
        ),
        QAItem(
            question="What caution did the friends take?",
            answer=f"{f['caution']}. They avoided forcing or touching the mechanism until they understood it.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {f['twist']}. Their first explanation was wrong, but careful observation revealed the truth.",
        ),
        QAItem(
            question="How was the mystery resolved?",
            answer=f"{f['action']}. Then {f['resolution']}, so the place became safe again.",
        ),
        QAItem(
            question="What image closes the story?",
            answer=f"The ending image is: {f['ending']}. It shows the concrete result of the friends' careful work.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can friendship help during a mystery?",
            answer="Friendship gives people someone to listen with, compare clues with, and encourage when the first idea may be wrong.",
        ),
        QAItem(
            question="Why is caution useful around a mechanism?",
            answer="Caution prevents a curious person from forcing a moving or unknown part and causing harm before the mechanism is understood.",
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer="A twist is a surprising new fact that changes how the earlier clues are understood.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a child-facing mystery about {p.name} and {p.friend} investigating {f['title']} in {p.place}.",
        f"Use this mechanism clue: {f['clue']}. Show the friends choosing caution instead of forcing the device.",
        f"Reveal this twist naturally: {f['twist']}. End with this concrete image: {f['ending']}.",
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
    lines.append("  trace events:")
    lines.extend(f"    - {event}" for event in world.trace)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/0."))
        print("solved" if asp.atoms(model, "solved") else "(no solved)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            friend=args.friend or "Milo",
            place=args.place or "the old clockwork greenhouse",
            object_name=args.object_name or "the brass humming box",
            snack=args.snack or "cinnamon pears",
        )
        if params.name == params.friend:
            raise StoryError("The main character and friend must have different names.")
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and index < limit:
            seed = base_seed + index
            index += 1
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
