#!/usr/bin/env python3
"""
A small ghost storyworld about a literate correction made beside a river path.

Luna finds a ghostly rhyme scratched on a sign. By repeating it and sharing the
right correction, she helps a lost river ghost find its way home.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Tale:
    id: str
    lost_line: str
    wrong_line: str
    correction: str
    ghost_need: str
    river_sign: str
    ending: str


SETTINGS = {
    "river_path": Setting(
        "river_path",
        "the river path",
        {"walk", "read", "share"},
    ),
}

FEATURES = ("rhyme", "repetition", "sharing")

TALES = {
    "silver_reeds": Tale(
        "silver_reeds",
        "At the river bend, the pale ghost waits.",
        "At the river bend, the pale ghost wades.",
        "At the river bend, the pale ghost waits.",
        "a way to remember the old lantern crossing",
        "silver reeds bent toward a dark stone",
        "the ghost crossed in a ribbon of moonlight and left the path warm",
    ),
    "echoing_stones": Tale(
        "echoing_stones",
        "Read the river rhyme, then follow the light.",
        "Read the river rhyme, then swallow the light.",
        "Read the river rhyme, then follow the light.",
        "a friend who could not hear the river's old directions",
        "three wet stones glimmered in a row",
        "the ghost's small lantern floated safely toward the bridge",
    ),
    "willow_whisper": Tale(
        "willow_whisper",
        "Share the true words where willow shadows sleep.",
        "Share the two words where willow shadows sleep.",
        "Share the true words where willow shadows sleep.",
        "the name of a child who had once read beside the water",
        "a willow leaf tapped twice against the sign",
        "the ghost whispered its name, and the willow answered with green light",
    ),
    "moonlit_bridge": Tale(
        "moonlit_bridge",
        "Repeat the rhyme until the river shows the way.",
        "Repeat the rhyme until the river throws the way.",
        "Repeat the rhyme until the river shows the way.",
        "a safe path through mist beneath the bridge",
        "a pale reflection formed a bright arrow",
        "the ghost followed the arrow and vanished beyond the mist",
    ),
}

NAMES = ["Luna", "Mara", "Nell", "Ivy", "Tess"]
TRAITS = ["curious", "careful", "kind", "literate", "brave"]

OPENINGS = [
    "{hero} walked beside the river path when {sign}.",
    "At dusk, {hero} found the river path shining with wet stones, and {sign}.",
    "The river was quiet, but the old sign was not. {sign}, and {hero} stopped to read it.",
    "A thin mist curled above the river path. Then {sign}, so {hero} opened her notebook.",
]

REFLECTIONS = [
    "Luna learned that a correction can be a kindness when it helps someone find the truth.",
    "The words mattered because they were shared, repeated, and made clear.",
    "A rhyme may sound small, but the right word can turn a frightening path into a safe one.",
    "Luna understood that being literate was not only knowing words; it was noticing when a word needed care.",
]


@dataclass
class StoryParams:
    setting: str = "river_path"
    tale: str = "silver_reeds"
    name: str = "Luna"
    trait: str = "literate"
    seed: Optional[int] = None


def _bump(entity: Entity, collection: str, key: str, amount: float = 1.0) -> None:
    values = getattr(entity, collection)
    values[key] = values.get(key, 0.0) + amount


def valid_combos() -> list[tuple[str, str]]:
    return [
        (setting_id, tale_id)
        for setting_id, setting in SETTINGS.items()
        for tale_id in TALES
        if "read" in setting.affords and "share" in setting.affords
    ]


def tell(params: StoryParams, rng: random.Random) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.tale not in TALES:
        raise StoryError(f"Unknown tale: {params.tale}")
    if params.name.strip() == "":
        raise StoryError("The reader's name cannot be empty.")

    setting = SETTINGS[params.setting]
    tale = TALES[params.tale]
    world = World(setting)

    hero = world.add(Entity(params.name, "character", params.name))
    ghost = world.add(Entity("river_ghost", "ghost", "the river ghost"))
    sign = world.add(Entity("old_sign", "sign", "the old wooden sign"))

    world.facts.update(
        hero=hero,
        ghost=ghost,
        sign=sign,
        tale=tale,
        setting=setting,
    )

    _bump(hero, "memes", "curiosity")
    _bump(hero, "meters", "reading")
    _bump(ghost, "memes", "loneliness")

    opening = rng.choice(OPENINGS).format(hero=hero.label, sign=tale.river_sign)
    world.say(
        f"{hero.label} was a {params.trait} child who loved words, especially words that sounded like little bells."
    )
    world.say(opening)
    world.say(
        f"On the old sign, a ghostly hand had written, \"{tale.lost_line}\""
    )

    world.para()
    world.say(
        f"A pale ghost rose from the river grass. It pointed to the sign and whispered, "
        f"\"I have repeated that line for many nights, but it never leads me home.\""
    )
    world.say(
        f"{hero.label} asked, \"What does the sign say when you read it aloud?\" "
        f"The ghost answered, \"{tale.wrong_line}\""
    )
    _bump(hero, "memes", "listening")
    _bump(ghost, "memes", "hope")

    world.say(
        f"{hero.label} read both lines slowly. The rhyme sounded close, but one word was wrong."
    )
    world.say(
        f"\"The correction is {tale.correction[:-1].lower()}\" she said. "
        f"\"May I share it with you?\""
    )
    world.say(
        f"\"Please,\" said the ghost. \"A shared word may be stronger than a lonely one.\""
    )
    _bump(hero, "memes", "problem_solving")
    _bump(hero, "meters", "correction")

    world.para()
    world.say(
        f"{hero.label} repeated the corrected rhyme once, twice, and a third time: "
        f"\"{tale.correction}\""
    )
    world.say(
        f"The ghost repeated it too. Each repetition made the river brighter, and {tale.river_sign}."
    )
    _bump(hero, "meters", "repetition", 3.0)
    _bump(ghost, "meters", "repetition", 3.0)
    _bump(ghost, "memes", "belonging")

    world.say(
        f"Together they shared the words with the reeds, the stones, and the dark water."
    )
    world.say(
        f"Then {tale.ending}."
    )
    world.say(rng.choice(REFLECTIONS))
    world.say(
        f"{hero.label} closed the notebook. On the sign, the corrected rhyme glowed softly for the next reader."
    )
    _bump(hero, "memes", "joy")
    _bump(ghost, "meters", "homeward", 1.0)

    world.facts.update(
        rhyme=tale.correction,
        wrong_line=tale.wrong_line,
        correction=tale.correction,
        river_sign=tale.river_sign,
        ending=tale.ending,
    )
    world.fired.update({"rhyme_found", "correction_made", "rhyme_repeated", "words_shared"})
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    tale: Tale = world.facts["tale"]
    return [
        f"Write a child-friendly ghost story about {hero.label} reading a rhyme beside the river path.",
        f"Include a literate correction where {hero.label} notices that the word '{tale.wrong_line}' is wrong and shares the better wording.",
        "Use rhyme, repetition, and sharing to help a lonely river ghost find its way home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    tale: Tale = world.facts["tale"]
    return [
        QAItem(
            f"Where did {hero.label} find the ghostly writing?",
            f"{hero.label} found the writing on an old sign beside the river path.",
        ),
        QAItem(
            "What was wrong with the ghost's version of the rhyme?",
            f"The ghost used the line '{tale.wrong_line}', but the correct line was '{tale.correction}'.",
        ),
        QAItem(
            f"How did {hero.label} make the correction helpful?",
            f"{hero.label} read the lines carefully, explained the correction, and shared the corrected rhyme with the ghost.",
        ),
        QAItem(
            "Why did the child repeat the corrected rhyme?",
            "Repeating the corrected rhyme helped the ghost remember the true directions and made the river show the way home.",
        ),
        QAItem(
            "What changed at the end?",
            f"The ghost found its way home, and the corrected rhyme glowed on the sign for another reader.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a rhyme?",
            "A rhyme is a pattern in which words have matching or similar ending sounds.",
        ),
        QAItem(
            "What is a correction?",
            "A correction is a change that makes a word, sentence, or idea accurate.",
        ),
        QAItem(
            "What does it mean to be literate?",
            "Being literate means being able to read and understand written language.",
        ),
        QAItem(
            "Why can repetition help someone learn?",
            "Repetition can help someone remember an important word, pattern, or instruction.",
        ),
        QAItem(
            "What does sharing mean in this story?",
            "Sharing means giving another person useful knowledge so they can understand or act safely too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:12} ({entity.kind:9}) meters={meters} memes={memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else params.tale)
    world = tell(params, rng)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


ASP_RULES = r"""
valid_setting(S) :- setting(S), affords(S,read), affords(S,share).
valid_tale(T) :- tale(T), correction(T).
valid(S,T) :- valid_setting(S), valid_tale(T), available(S,T).
"""


def asp_facts() -> str:
    from storyworlds import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for affordance in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, affordance))
    for tale_id, tale in TALES.items():
        lines.append(asp.fact("tale", tale_id))
        lines.append(asp.fact("correction", tale_id))
        for setting_id, _ in valid_combos():
            if tale_id in TALES and setting_id in SETTINGS:
                lines.append(asp.fact("available", setting_id, tale_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if python_combos != asp_combos:
        print("MISMATCH between Python and ASP:")
        print("  Python only:", sorted(python_combos - asp_combos))
        print("  ASP only:", sorted(asp_combos - python_combos))
        return 1

    for tale_id in TALES:
        sample = generate(
            StoryParams(
                setting="river_path",
                tale=tale_id,
                name="Luna",
                trait="literate",
                seed=17,
            )
        )
        if "correction" not in sample.story.lower():
            print(f"Generated story failed correction check: {tale_id}")
            return 1
        if "river" not in sample.story.lower():
            print(f"Generated story failed river check: {tale_id}")
            return 1

    print(f"OK: ASP matches Python ({len(asp_combos)} combinations), and stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A ghost story of literate correction, rhyme, repetition, and sharing on a river path."
    )
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--tale", choices=TALES, default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--trait", choices=TRAITS, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "river_path"
    tale = args.tale or rng.choice(sorted(TALES))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if setting not in SETTINGS:
        raise StoryError(f"Invalid setting '{setting}'.")
    if tale not in TALES:
        raise StoryError(f"Invalid tale '{tale}'.")
    return StoryParams(
        setting=setting,
        tale=tale,
        name=name,
        trait=trait,
        seed=args.seed,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, tale_id in enumerate(sorted(TALES)):
            samples.append(
                generate(
                    StoryParams(
                        setting="river_path",
                        tale=tale_id,
                        name=NAMES[index % len(NAMES)],
                        trait="literate",
                        seed=base_seed + index,
                    )
                )
            )
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
