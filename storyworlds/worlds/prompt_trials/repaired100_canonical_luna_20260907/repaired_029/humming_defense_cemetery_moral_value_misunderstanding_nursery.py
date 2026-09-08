#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about humming, a cemetery, defense, moral value,
and a misunderstanding repaired by listening.
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
    location: str = ""

    def add_meter(self, key: str, value: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + value

    def add_meme(self, key: str, value: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + value


@dataclass
class Setting:
    id: str
    label: str
    affords: set[str]


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


SETTINGS = {
    "moon_cemetery": Setting(
        "moon_cemetery",
        "the moonlit cemetery",
        {"hum"},
    ),
    "bell_cemetery": Setting(
        "bell_cemetery",
        "the old bell cemetery",
        {"hum"},
    ),
    "rose_cemetery": Setting(
        "rose_cemetery",
        "the rose-covered cemetery",
        {"hum"},
    ),
}

NAMES = ["Luna", "Nell", "Milo", "Pip", "Tilly", "Ollie"]
TRAITS = ["kind", "brave", "gentle", "thoughtful", "patient"]
HUMS = [
    "a low silver hum",
    "a warm little hum",
    "a moon-soft humming",
    "a bright hum that bobbed like a bee",
]
MISUNDERSTANDINGS = [
    (
        "The humming seemed to warn trespassers away",
        "the cemetery was being defended from a frightened family of night moths",
        "the stones were humming a welcome for a lost moth",
    ),
    (
        "The humming sounded like a command to shut the gate",
        "the gate was being defended from a loose windmill that could topple the old stones",
        "the tune was really asking someone to hold the gate gently",
    ),
    (
        "The humming seemed to say that no one should enter",
        "the cemetery was being defended from rainwater rushing toward a tiny grave garden",
        "the tune was calling for help to guide the water around the flowers",
    ),
]


@dataclass(frozen=True)
class StoryParams:
    setting: str
    name: str
    trait: str
    hum: str
    misunderstanding: int
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    if setting not in SETTINGS:
        raise StoryError(f"Unknown cemetery setting: {setting}")
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    hum = args.hum or rng.choice(HUMS)
    misunderstanding = (
        args.misunderstanding
        if args.misunderstanding is not None
        else rng.randrange(len(MISUNDERSTANDINGS))
    )
    if not 0 <= misunderstanding < len(MISUNDERSTANDINGS):
        raise StoryError("Misunderstanding must be 0, 1, or 2.")
    return StoryParams(setting, name, trait, hum, misunderstanding, args.seed)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity("hero", "child", params.name, location=setting.id))
    keeper = world.add(Entity("keeper", "helper", "the small bell keeper", location=setting.id))
    cemetery = world.add(Entity("cemetery", "place", setting.label, location=setting.id))
    defense = world.add(Entity("defense", "problem", "the quiet defense", location=setting.id))
    world.facts.update(hero=hero, keeper=keeper, cemetery=cemetery, defense=defense)

    first, truth, clue = MISUNDERSTANDINGS[params.misunderstanding]

    world.say(
        f"{params.name} was a {params.trait} child who walked softly where the old "
        f"stones slept."
    )
    world.say(
        f"At {setting.label}, {params.hum} curled through the grass: "
        f"\"Hush-a-bye, guard nearby.\""
    )
    world.say(
        f"The humming rose and fell, rose and fell, like a tiny nursery bell."
    )

    hero.add_meme("curiosity")
    defense.add_meter("active")
    world.para()
    world.say(f"{params.name} heard the tune and thought, \"{first}.\"")
    world.say(
        f"The little bell keeper hurried over. \"Please do not run,\" said the keeper. "
        f"\"A defense can sound stern when its reason is hidden.\""
    )
    world.say(
        f"\"Is the cemetery in danger?\" asked {params.name}. "
        f"\"Or is it danger to us?\""
    )
    world.say(
        f"\"Let us listen before we judge,\" replied the keeper. "
        f"\"Kindness is a strong defense too.\""
    )
    hero.add_meme("worry")
    keeper.add_meme("patience")

    world.para()
    hero.add_meter("observed")
    world.say(
        f"{params.name} stood still. Beneath the humming, a softer note repeated "
        f"near the flower beds."
    )
    world.say(f"Then {params.name} noticed that {clue}.")
    world.say(
        f"Together they followed the tune, not with a shout or a shove, but with "
        f"careful feet and open ears."
    )
    world.say(
        f"The humming changed its words: \"Guard the small, and help them home.\""
    )
    hero.add_meme("understanding")
    world.facts["truth"] = truth
    world.facts["clue"] = clue

    world.para()
    world.say(
        f"At last they understood: {truth}."
    )
    world.say(
        f"{params.name} helped the keeper mend the little boundary and guide the "
        f"trouble away from the sleeping stones."
    )
    defense.add_meter("resolved")
    hero.add_meme("kindness")
    hero.add_meme("moral_value")
    world.say(
        f"\"I mistook the warning for a welcome turned away,\" said {params.name}."
    )
    world.say(
        f"\"And I mistook your fear for carelessness,\" said the keeper. "
        f"\"Listening repaired both mistakes.\""
    )
    world.say(
        f"The cemetery grew peaceful. The humming no longer sounded like a command; "
        f"it sounded like a lullaby."
    )
    world.say(
        f"Under the moon, {params.name} learned the moral value of patient listening: "
        f"a misunderstanding may make a wall, but kindness can open a gate."
    )
    world.say(
        f"And all night long the old stones hummed, \"Care for the small, "
        f"and the small will sing.\""
    )
    world.facts["resolution"] = (
        "The defense became gentle guidance, and the misunderstanding was cleared "
        "by listening."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    hero: Entity = world.facts["hero"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a nursery-rhyme story about {hero.label} hearing humming in a cemetery.",
            "Show how a misunderstanding about defense is repaired through patient listening.",
            "End with a clear moral value about kindness and understanding.",
        ],
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    setting: Setting = world.setting
    return [
        QAItem(
            "Where did the humming happen?",
            f"The humming happened at {setting.label}.",
        ),
        QAItem(
            f"What did {hero.label} misunderstand?",
            f"{hero.label} misunderstood the humming and thought it was a warning or rejection instead of a request for help.",
        ),
        QAItem(
            "What was the cemetery defending?",
            f"The cemetery was defending its small, sleeping, or fragile parts from harm; in this story, {f['truth']}.",
        ),
        QAItem(
            f"How did {hero.label} discover the truth?",
            f"{hero.label} stood still, listened beneath the first tune, and noticed that {f['clue']}.",
        ),
        QAItem(
            "What moral value did the story teach?",
            "The story taught that patient listening and kindness can repair a misunderstanding and protect others.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a cemetery?",
            "A cemetery is a quiet place where people remember and honor those who have died.",
        ),
        QAItem(
            "What does defense mean?",
            "Defense means protecting someone or something from harm.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone interprets words or actions incorrectly.",
        ),
        QAItem(
            "Why is listening valuable?",
            "Listening is valuable because it can reveal the truth and prevent hurried judgments.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
            f"  {entity.label}: location={entity.location}, "
            f"meters={meters}, memes={memes}"
        )
    return "\n".join(lines)


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


ASP_RULES = r"""
safe_setting(S) :- setting(S), affords(S, hum).
defense_possible(S) :- safe_setting(S), cemetery(S).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("cemetery", sid))
        for action in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, action))
    return "\n".join(lines)


def asp_program(show: str = "#show defense_possible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "defense_possible"))
    expected = {(sid,) for sid in SETTINGS}
    if found == expected:
        print(f"OK: ASP defense gate matches Python ({len(expected)} settings).")
        for seed in range(5):
            params = StoryParams(
                setting=list(SETTINGS)[seed % len(SETTINGS)],
                name=NAMES[seed],
                trait=TRAITS[seed % len(TRAITS)],
                hum=HUMS[seed % len(HUMS)],
                misunderstanding=seed % len(MISUNDERSTANDINGS),
                seed=seed,
            )
            sample = generate(params)
            if not sample.story or "humming" not in sample.story:
                return 1
        print("OK: generated stories exercised.")
        return 0
    print("ASP/Python mismatch:", sorted(found), sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A nursery-rhyme world of humming, defense, cemetery, and understanding."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--hum", choices=HUMS)
    parser.add_argument("--misunderstanding", type=int, choices=range(len(MISUNDERSTANDINGS)))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show defense_possible/1."))
        print("ASP defense settings:")
        for item in sorted(asp.atoms(model, "defense_possible")):
            print(" ", item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, setting in enumerate(SETTINGS):
            params = StoryParams(
                setting=setting,
                name=NAMES[index % len(NAMES)],
                trait=TRAITS[index % len(TRAITS)],
                hum=HUMS[index % len(HUMS)],
                misunderstanding=index % len(MISUNDERSTANDINGS),
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(max(0, args.n)):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params = StoryParams(
                params.setting,
                params.name,
                params.trait,
                params.hum,
                params.misunderstanding,
                seed,
            )
            samples.append(generate(params))

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
