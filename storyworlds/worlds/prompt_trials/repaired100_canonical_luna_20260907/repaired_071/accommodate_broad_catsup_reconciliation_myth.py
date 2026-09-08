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
class StoryParams:
    hero: str
    companion: str
    place: str
    seed: int | None = None


HEROES = ["Luna", "Mara", "Ivo", "Nell", "Orin"]
COMPANIONS = ["Pip", "Suri", "Tavi", "Bram", "Eli"]
PLACES = ["the Moonlit Meadow", "the Broad Hill", "the Willow Court", "the Lantern Valley"]

TALES = [
    {
        "title": "The Catsup Sun",
        "problem": "the red catsup sun had slipped from its place above the village feast",
        "object": "a little clay sun painted red",
        "cause": "the sun had rolled behind the broad feast stone when the tablecloth was pulled",
        "repair": "they placed the clay sun on a steady shelf and shared the feast beneath it",
        "lesson": "A small mistake can cast a broad shadow, but patient hearts can make room for one another",
        "ending": "the clay sun glowed above bowls of warm stew and bright laughter",
    },
    {
        "title": "The Broad Bridge",
        "problem": "the broad stone bridge had closed its middle path between two quarreling villages",
        "object": "an ancient bridge of pale stone",
        "cause": "each village had stacked its festival baskets on the same crossing",
        "repair": "they moved the baskets to one shared table and opened the bridge again",
        "lesson": "To accommodate another heart, first make space where both hearts can stand",
        "ending": "the bridge shone beneath the moon while both villages crossed together",
    },
    {
        "title": "The Red River Bowl",
        "problem": "a red river bowl had appeared in the shrine, and each village claimed it belonged only to them",
        "object": "a round bowl marked with a red sun",
        "cause": "the old inscription said the bowl was made for every traveler who arrived hungry",
        "repair": "they filled it with catsup-colored berry soup and passed it from hand to hand",
        "lesson": "A treasure grows when its welcome is broad enough for everyone",
        "ending": "the red bowl rested between the villages as if it had always known their names",
    },
]


@dataclass
class World:
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


def build_world(params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join([
            params.hero, params.companion, params.place
        ])))
    rng = random.Random(seed ^ 0xA91C)
    tale = rng.choice(TALES)
    w = World()

    hero = w.add(Entity("hero", "person", params.hero, {"steps": 0}, {"curiosity": 0, "kindness": 0}))
    companion = w.add(Entity("companion", "person", params.companion, {"steps": 0}, {"hurt": 0, "trust": 0}))
    spirit = w.add(Entity("spirit", "mythic", "the Hearth Spirit", {"warmth": 1}, {"welcome": 0}))
    token = w.add(Entity("token", "object", tale["object"], {"weight": 1}, {"belonging": 0}))

    w.facts.update(
        hero=hero,
        companion=companion,
        spirit=spirit,
        token=token,
        tale=tale,
        place=params.place,
        resolved=False,
    )

    w.say(
        f"In {params.place}, where the hills were broad enough to hold a hundred shadows, "
        f"{hero.label} listened for the voice of the Hearth Spirit."
    )
    w.say(
        f"The spirit guarded {tale['title']}, a wonder that helped strangers "
        f"accommodate one another whenever an argument grew hot."
    )
    w.say(
        f"{companion.label} came carrying a small basket, and {hero.label} came carrying a lantern. "
        f"Together they hoped to bring the wonder to the evening gathering."
    )

    w.para()
    w.say(f"But {tale['problem']}.")
    w.say(
        f"{companion.label} pointed toward {hero.label}. "
        f'"You moved it without asking," {companion.label} said.'
    )
    w.say(
        f'"I did not," {hero.label} answered. "But I will help look, if you will help me search."'
    )
    companion.memes["hurt"] += 1
    hero.memes["curiosity"] += 1
    w.say(
        "The accusation made a narrow silence between them, though the night itself was broad and full of stars."
    )

    w.para()
    w.say(
        f"{hero.label} did not pull at the old stones or shout at the dark. "
        f"{hero.label} counted footprints, listened to the wind, and asked who had needed room."
    )
    w.say(
        f"{companion.label} noticed a smear of red near the feast path. "
        f'"That looks like catsup," {companion.label} said. "It leads behind the stone."'
    )
    w.say(
        f'"Then the clue is speaking," said {hero.label}. "Let us follow it together."'
    )
    hero.meters["steps"] += 3
    companion.meters["steps"] += 3
    w.say(
        f"Behind the broad stone they found the {token.label}. "
        f"The cause was simple: {tale['cause']}."
    )

    w.para()
    w.say(
        f"The Hearth Spirit rose from the lantern flame. "
        f'"A place can hold two truths," it said. '
        f'"One of you found the mark, and the other kept searching. Reconciliation begins when both deeds are seen."'
    )
    w.say(
        f"{companion.label} lowered their eyes. "
        f'"I was afraid the wonder would be lost, so I blamed you before I knew."'
    )
    w.say(
        f'{hero.label} replied, "I should have told you where I was looking. Let us accommodate each other now."'
    )
    companion.memes["hurt"] = 0
    companion.memes["trust"] += 1
    hero.memes["kindness"] += 1
    spirit.memes["welcome"] += 1
    token.memes["belonging"] += 1
    w.facts["resolved"] = True

    w.say(f"Together they {tale['repair']}.")
    w.say(
        f"The spirit smiled, because {tale['lesson']}."
    )
    w.say(f"At last, {tale['ending']}.")
    return w


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    return [
        'Write a child-friendly myth using the words "accommodate", "broad", and "catsup".',
        f"Tell a myth about {world.facts['hero'].label} and {world.facts['companion'].label} in which Reconciliation solves {tale['title']}.",
        f"Show how the characters discover that {tale['cause']} and repair their friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale = world.facts["tale"]
    hero = world.facts["hero"].label
    companion = world.facts["companion"].label
    return [
        QAItem(
            f"What problem did {hero} and {companion} discover?",
            f"They discovered that {tale['problem']}. The missing wonder caused fear and an argument.",
        ),
        QAItem(
            f"What clue helped {hero} and {companion} find the lost object?",
            f"{companion} noticed a catsup-colored smear near the feast path, and they followed it behind the broad stone.",
        ),
        QAItem(
            "How was the conflict reconciled?",
            f"{companion} apologized for blaming {hero}, and {hero} admitted that clearer sharing would help. They chose to accommodate each other and repaired the problem together.",
        ),
        QAItem(
            "What did the Hearth Spirit teach them?",
            f"The Hearth Spirit taught that {tale['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is reconciliation?",
            "Reconciliation is the making of peace after people have been hurt or disagreed.",
        ),
        QAItem(
            "What does accommodate mean?",
            "To accommodate someone means to make room for their needs or help them fit comfortably.",
        ),
        QAItem(
            "What does broad mean?",
            "Broad means wide or covering a large space.",
        ),
        QAItem(
            "What is catsup?",
            "Catsup is a red sauce often made from tomatoes and used with food.",
        ),
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HEROES)
    choices = [name for name in COMPANIONS if name != hero]
    companion = args.companion or rng.choice(choices)
    place = args.place or rng.choice(PLACES)
    if hero == companion:
        raise StoryError("hero and companion must be different characters")
    return StoryParams(hero=hero, companion=companion, place=place, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append(f"  reconciled={world.facts['resolved']}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    sections = [
        ("== (1) Generation prompts ==", sample.prompts),
        ("== (2) Story questions ==", sample.story_qa),
        ("== (3) World knowledge ==", sample.world_qa),
    ]
    lines: list[str] = []
    for title, items in sections:
        lines.append(title)
        for item in items:
            if isinstance(item, QAItem):
                lines.append(f"Q: {item.question}")
                lines.append(f"A: {item.answer}")
            else:
                lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).rstrip()


ASP_RULES = r"""
valid_hero(H) :- hero(H).
valid_companion(C) :- companion(C).
valid_place(P) :- place(P).
valid_story(H,C,P) :- valid_hero(H), valid_companion(C), valid_place(P), H != C.
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    facts = []
    for hero in HEROES:
        facts.append(asp.fact("hero", hero))
    for companion in COMPANIONS:
        facts.append(asp.fact("companion", companion))
    for place in PLACES:
        facts.append(asp.fact("place", place))
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> set[tuple[str, str, str]]:
    return {
        (hero, companion, place)
        for hero in HEROES
        for companion in COMPANIONS
        for place in PLACES
        if hero != companion
    }


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    found = set(asp.atoms(model, "valid_story"))
    expected = valid_combos()
    if found != expected:
        print("ASP/Python parity mismatch.")
        print("Only in ASP:", sorted(found - expected))
        print("Only in Python:", sorted(expected - found))
        return 1
    for index, combo in enumerate(sorted(expected)[:5]):
        sample = generate(StoryParams(*combo[:2], combo[2], seed=index))
        if not sample.story or "Reconciliation" not in sample.story and "reconciliation" not in sample.story.lower():
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP/Python parity matches ({len(expected)} combinations).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic reconciliation storyworld.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--place", choices=PLACES)
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


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        raise SystemExit(asp_verify())
    if args.asp:
        print("Compatible myth combinations:")
        for combo in sorted(valid_combos()):
            print("  " + " | ".join(combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, (hero, companion, place) in enumerate(sorted(valid_combos())):
            if index >= max(1, args.n):
                break
            samples.append(generate(StoryParams(hero, companion, place, base_seed + index)))
    else:
        for index in range(max(1, args.n)):
            local = argparse.Namespace(
                hero=args.hero,
                companion=args.companion,
                place=args.place,
                seed=base_seed + index,
            )
            params = resolve_params(local, random.Random(base_seed + index))
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
