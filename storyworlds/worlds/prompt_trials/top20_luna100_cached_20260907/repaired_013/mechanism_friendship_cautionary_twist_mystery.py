#!/usr/bin/env python3
"""
A small mystery storyworld about a friendship tested by a hidden mechanism,
with a cautionary twist.
"""

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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the clockwork lighthouse"
    hero: str = "Lina"
    friend: str = "Milo"
    keeper: str = "the quiet keeper"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the clockwork lighthouse": {
        "tags": {"mechanism", "mystery", "friendship"},
        "mood": "briny and full of ticking sounds",
    },
    "the abandoned train station": {
        "tags": {"mechanism", "mystery", "caution"},
        "mood": "dusty and echoing",
    },
    "the glasshouse on the hill": {
        "tags": {"mechanism", "mystery", "twist"},
        "mood": "green, dim, and whispering",
    },
}


@dataclass(frozen=True)
class MysteryArc:
    title: str
    premise: str
    problem: str
    clue: str
    dialogue: str
    action: str
    twist: str
    result: str
    ending: str
    problem_answer: str
    clue_answer: str
    twist_answer: str
    result_answer: str


ARCS = [
    MysteryArc(
        "The Bell That Counted Backward",
        "At midnight, the lighthouse bell began counting down instead of calling ships home.",
        "A brass panel had opened beneath the stairs, and its turning gears were pulling the beacon toward darkness.",
        "Lina noticed that every third tooth on the largest gear bore a tiny painted star.",
        "\"Do not turn it yet,\" Milo whispered. \"A machine can hide a warning inside its rhythm.\"",
        "They marked the starred teeth with chalk and used the rhythm to lift a jammed spring without forcing the panel.",
        "The countdown was not a threat from an enemy; it was the lighthouse warning that its old counterweight had been tied incorrectly.",
        "The beacon brightened, and the bell rang once for safe ships and once for careful friends.",
        "At dawn, two chalky fingerprints remained beside the repaired gear.",
        "The lighthouse bell counted backward while a hidden gear mechanism pulled the beacon toward darkness.",
        "Lina found a repeating pattern of painted stars on every third gear tooth.",
        "The countdown was a warning caused by a wrongly tied counterweight, not an enemy attack.",
        "The friends repaired the mechanism by following its rhythm instead of forcing the brass panel.",
    ),
    MysteryArc(
        "The Footprints Under Glass",
        "Fresh footprints appeared beneath the locked glasshouse floor each morning.",
        "The prints led to a sealed seed cabinet, while the night watcher's key was found inside the cabinet.",
        "Milo saw that the footprints stopped wherever moonlight touched the floor.",
        "\"We should follow the light, not the prints,\" Lina said. \"Someone may want us looking down.\"",
        "They placed mirrors along the moonlit path and revealed a narrow service tunnel beneath the tiles.",
        "The footprints were shadows cast by a rotating garden mechanism; the real intruder had entered through the tunnel.",
        "The friends closed the tunnel and left a harmless bell on the cabinet to warn them next time.",
        "In the morning, the glass floor showed only their two real footprints and one bright square of moonlight.",
        "Footprints led beneath the glasshouse toward a locked seed cabinet, but the key was already inside.",
        "Moonlight stopped the footprints, showing that they were shadows rather than real tracks.",
        "A rotating garden mechanism made the false footprints while a real intruder used a service tunnel.",
        "The friends found and closed the tunnel, then added a bell to warn them of another opening.",
    ),
    MysteryArc(
        "The Map With a Missing Corner",
        "A map in the station office showed a platform that no timetable named.",
        "When Lina touched the missing corner, the station clock stopped and every door clicked shut.",
        "The map's torn edge matched the shape of a small lever hidden behind the clock.",
        "\"If the map is a key,\" Milo said, \"we must learn what it locks before we use it.\"",
        "They studied the timetable and pulled the lever only after opening the emergency latch.",
        "The secret platform was not a treasure room; it was a safety bay built to stop runaway trains.",
        "The doors opened, and the forgotten mechanism guided a loose luggage cart into the safety bay.",
        "The map was pinned beside a new note: Never unlock a mystery before checking who it protects.",
        "Touching the missing corner stopped the station clock and locked every door.",
        "The torn corner matched a lever behind the clock, proving the map worked as a key.",
        "The hidden platform was a safety bay, not a treasure room.",
        "The friends opened the emergency latch first and used the mechanism to stop a runaway cart.",
    ),
    MysteryArc(
        "The Whispering Gear",
        "One gear in the hilltop observatory whispered a person's name whenever it turned.",
        "It whispered Milo's name, and the dome began closing even though no one had touched the controls.",
        "Lina found a thread caught in the teeth; it carried a drop of lavender oil from the caretaker's coat.",
        "\"The gear knows a scent, not a person,\" she explained. \"Let us test the clue safely.\"",
        "They stopped the dome with the hand brake and used a clean cloth to remove the thread.",
        "The whisper was made by a reed hidden in the gear, and the thread had been placed to make the caretaker seem guilty.",
        "The dome opened again, while the friends kept the thread in a jar for the town constable.",
        "The gear was silent at sunset, but the jar made a tiny lavender shadow on the desk.",
        "A whispering gear named Milo while the observatory dome began closing by itself.",
        "A thread carrying lavender oil was caught in the gear, linking the sound to the caretaker's coat.",
        "The gear used a hidden reed, and someone had planted the thread to frame the caretaker.",
        "The friends stopped the dome safely, preserved the clue, and reported it instead of accusing anyone.",
    ),
    MysteryArc(
        "The Lantern With Two Shadows",
        "A lantern in the old theater cast two shadows for every person who passed it.",
        "The second shadows moved toward a locked prop room after the theater had been emptied.",
        "Milo saw that the lantern's lower mirror was loose and pointed toward a row of polished costumes.",
        "\"A shadow can copy a secret,\" Lina said, \"but it cannot carry one.\"",
        "They fixed the mirror with a ribbon and watched the false shadows reveal a thin door behind the costumes.",
        "The door held stolen stage letters, but the thief had left before the shadows exposed the hiding place.",
        "The letters were returned, and the lantern was hung where its light could show both the stage and the exits.",
        "The next show began with one honest shadow behind every actor.",
        "The lantern's loose mirror made extra shadows that moved toward the locked prop room.",
        "The mirror reflected polished costumes and sent false shadows toward a hidden door.",
        "The hidden door contained stolen letters; the shadows revealed the hiding place but not the absent thief.",
        "The friends recovered the letters and repaired the lantern so it illuminated the theater safely.",
    ),
]


OPENINGS = [
    "On a foggy evening, {hero} and {friend} entered {setting}, where the air was {mood}.",
    "Everyone in town avoided {setting} after sunset, but {hero} and {friend} went there together.",
    "The mystery began when {hero} found {friend} waiting outside {setting} with a pocket lamp.",
    "At the edge of town stood {setting}. One evening, {hero} and {friend} noticed that something inside was moving.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.friend, params.keeper))
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _lower(text: str) -> str:
    return text[:1].lower() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    arc: MysteryArc = f["arc"]
    opening = _fill(OPENINGS[f["opening_variant"]], f)
    parts = [
        opening,
        f"{_fill(arc.premise, f)} {_fill(arc.problem, f)}",
        f"{_fill(arc.clue, f)} {_fill(arc.dialogue, f)}",
        _fill(arc.action, f),
        f"{_fill(arc.twist, f)} {_fill(arc.result, f)}",
        f"By morning, {_fill(arc.ending, f)}.",
    ]
    if f["structure_variant"] == 1:
        parts[0], parts[1] = parts[1], parts[0]
        parts[3] = f"Before touching anything, {f['hero']} and {f['friend']} agreed to move carefully. {_fill(arc.action, f)}"
    elif f["structure_variant"] == 2:
        parts[2] = f"\"What do you think?\" asked {f['hero']}. {_fill(arc.dialogue, f)} Then {_fill(arc.clue, f).lower()}"
        parts[4] = f"The answer surprised them. {_fill(arc.twist, f)} {_fill(arc.result, f)}"
    elif f["structure_variant"] == 3:
        parts[0] = f"The ending was clear by dawn: {_fill(arc.ending, f)}."
        parts[5] = f"That is why the people of {f['setting']} still remember the warning: a mystery deserves patience before bravery."
    return parts


ASP_RULES = r"""
setting(clockwork_lighthouse).
setting(abandoned_train_station).
setting(glasshouse_on_the_hill).

feature(mechanism).
feature(friendship).
feature(cautionary).
feature(twist).
style(mystery).

valid_setting(S) :- setting(S), feature(mechanism), feature(friendship),
                     feature(cautionary), feature(twist), style(mystery).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    for feature in ("mechanism", "friendship", "cautionary", "twist"):
        lines.append(asp.fact("feature", feature))
    lines.append(asp.fact("style", "mystery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A friendship mystery about a hidden mechanism.")
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--keeper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Lina", "Nora", "Pip", "Tessa", "Ivo"])
    friend = args.friend or rng.choice(["Milo", "Jae", "Omi", "Rafi", "Suri"])
    keeper = args.keeper or rng.choice(
        ["the quiet keeper", "the station guard", "the glasshouse caretaker"]
    )
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    if not hero.strip() or not friend.strip():
        raise StoryError("Hero and friend names must not be empty.")
    return StoryParams(setting=setting, hero=hero, friend=friend, keeper=keeper)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different characters.")

    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(params.hero, "character", meters={"alertness": 0.8}, memes={"trust": 1.0})
    )
    friend = world.add(
        Entity(params.friend, "character", meters={"alertness": 0.9}, memes={"trust": 1.0})
    )
    keeper = world.add(
        Entity(params.keeper, "possible_witness", meters={"distance": 1.0}, memes={"secrecy": 0.5})
    )
    mechanism = world.add(
        Entity(
            "the hidden mechanism",
            "mechanism",
            meters={"motion": 0.7, "danger": 0.4},
            memes={"warning": 1.0},
        )
    )
    clue = world.add(
        Entity(
            "the physical clue",
            "clue",
            meters={"visibility": 0.8},
            memes={"truth": 0.7},
        )
    )

    facts = {
        "hero": params.hero,
        "friend": params.friend,
        "keeper": params.keeper,
        "setting": params.setting,
        "mood": SETTING_REGISTRY[params.setting]["mood"],
        "arc": arc,
        "opening_variant": (seed // len(ARCS)) % len(OPENINGS),
        "structure_variant": (seed // (len(ARCS) * len(OPENINGS))) % 4,
    }
    for key in ("premise", "problem", "clue", "dialogue", "action", "twist", "result", "ending"):
        facts[key] = _fill(getattr(arc, key), facts)
    world.facts.update(facts)
    world.facts["mechanism_state"] = "observed, tested carefully, and made safe"
    world.facts["theme"] = "mechanism, friendship, caution, twist, mystery"

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a mystery about {params.hero} and {params.friend} investigating a mechanism in {params.setting}.",
        "Tell a child-facing cautionary mystery where friendship changes the investigation.",
        "Write a mystery with a physical clue, a hidden mechanism, and a surprising but fair twist.",
    ]
    story_qa = [
        QAItem(
            question=f"What danger or mystery did {params.hero} and {params.friend} discover?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question="What clue helped the friends investigate safely?",
            answer=arc.clue_answer,
        ),
        QAItem(
            question="What was the cautionary twist?",
            answer=arc.twist_answer,
        ),
        QAItem(
            question="How did the friends resolve the mystery?",
            answer=arc.result_answer,
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of moving parts that work together to make something happen.",
        ),
        QAItem(
            question="Why should people be cautious around an unknown mechanism?",
            answer="They should be cautious because moving parts may be fragile or dangerous, and careful observation can reveal how to make them safe.",
        ),
        QAItem(
            question="How can friendship help solve a mystery?",
            answer="Friends can compare what they notice, listen to one another, and make safer decisions together.",
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer="A twist is a surprising change in what the clues seem to mean, while still fitting the evidence.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
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
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
        print(f"facts: {sample.world.facts['mechanism_state']}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def _valid_python() -> list[str]:
    return sorted(setting.replace("the ", "").replace(" ", "_") for setting in SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_setting/1."))
    return sorted(set(asp.atoms(model, "valid_setting")))


def asp_verify() -> int:
    python_values = {(value,) for value in _valid_python()}
    asp_values = set(_asp_valid())
    if python_values == asp_values:
        print(f"OK: clingo gate matches python ({len(python_values)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(python_values - asp_values))
    print("clingo only:", sorted(asp_values - python_values))
    return 1


def verify_generation() -> int:
    for seed in range(12):
        params = StoryParams(
            setting=list(SETTING_REGISTRY)[seed % len(SETTING_REGISTRY)],
            hero="Lina",
            friend="Milo",
            keeper="the quiet keeper",
            seed=seed,
        )
        sample = generate(params)
        if not sample.story.strip():
            print("Generation failed: empty story.")
            return 1
        if "{" in sample.story or "}" in sample.story:
            print("Generation failed: unresolved template field.")
            return 1
        if not any(word in sample.story.lower() for word in ("said", "asked", "whispered")):
            print("Generation failed: missing dialogue.")
            return 1
    print("OK: generated stories passed validation.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_setting/1."))
        return
    if args.verify:
        status = asp_verify()
        if status == 0:
            status = verify_generation()
        sys.exit(status)
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, setting in enumerate(SETTING_REGISTRY):
            params = StoryParams(
                setting=setting,
                hero="Lina",
                friend="Milo",
                keeper="the quiet keeper",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
