#!/usr/bin/env python3
"""
Standalone story world: the cassette that laughed at the wrong ending.

A small mythic simulation about a magical cassette, a boastful ending, and
the reconciliation that teaches a better story.
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    hero_name: str
    hero_gender: str
    companion_name: str
    companion_role: str
    guardian: str
    quest: str
    opening_variant: int = 0
    response_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


GUARDIANS = {
    "moon_mountain": {
        "label": "the moon mountain",
        "object": "the silver bell",
        "lesson": "a mountain is not conquered by shouting at it",
    },
    "whispering_forest": {
        "label": "the whispering forest",
        "object": "the acorn crown",
        "lesson": "the quietest tree may know the oldest truth",
    },
    "sunken_city": {
        "label": "the sunken city",
        "object": "the pearl key",
        "lesson": "a treasure is safest when it is shared",
    },
    "cloud_bridge": {
        "label": "the cloud bridge",
        "object": "the feather of dawn",
        "lesson": "even the sky needs a helping hand",
    },
}

QUESTS = {
    "ring_the_bell": {
        "goal": "bring back a sound that would wake the sleeping valley",
        "danger": "the cassette played a boastful ending in which the hero alone saved everyone",
        "evidence": "The valley went silent, and even the moon hid behind a thin cloud",
        "repair": "rewound the tape and recorded the companion's brave part beside the hero's",
        "result": "the bell rang for the whole valley, not for one proud voice",
    },
    "find_the_crown": {
        "goal": "return the acorn crown before the forest forgot its own name",
        "danger": "the cassette announced that the hero had found it without help",
        "evidence": "The trees turned their leaves away from the path",
        "repair": "spoke the companion's name into the microphone and thanked every tree that had guided them",
        "result": "the forest brightened, and the crown rested gently on two heads",
    },
    "unlock_the_city": {
        "goal": "open the sunken gate before the tide covered the last street",
        "danger": "the cassette ended with the hero claiming the pearl key as a trophy",
        "evidence": "The gate groaned shut, and the fish stopped circling its carved door",
        "repair": "admitted the mistake, then let the companion turn the key while the hero held the lamp",
        "result": "the gate opened and warm lights returned to the empty windows",
    },
    "cross_the_bridge": {
        "goal": "carry the feather of dawn across the cloud bridge",
        "danger": "the cassette made the hero sound like a giant who needed no one",
        "evidence": "The bridge folded one bright plank beneath the lonely voice",
        "repair": "recorded both voices counting each careful step across the wind",
        "result": "the bridge stretched wide enough for the morning sun",
    },
}

OPENINGS = [
    "At the edge of the first night, {hero} found a cassette beneath a stone that hummed.",
    "When the moon rose blue, {hero} discovered a little cassette in the pocket of an ancient statue.",
    "The old storyteller gave {hero} a cassette and warned, “A recording can remember more than words.”",
]

RESPONSES = [
    '{companion} said, “That ending leaves me out.” {hero} answered, “Then I will make it true, not merely grand,” and {repair}.',
    '“A hero who forgets a friend is only a loud echo,” said {companion}. {hero} listened and {repair}.',
    '{hero} asked, “Can the cassette learn a kinder ending?” “Only if we tell it one,” said {companion}, so {repair}.',
]

ENDINGS = [
    "The cassette clicked softly, as if it had learned to laugh with everyone.",
    "From then on, the recording kept two voices, and neither one had to shout.",
    "The old myth traveled from village to village, growing funnier and kinder each time.",
    "Even the stars seemed to lean closer when the new ending played.",
]

HERO_NAMES = ["Luna", "Mina", "Ivy", "Nora", "Pia", "Tess", "Eli", "Milo", "Finn"]
COMPANION_NAMES = ["Sol", "Taro", "Mira", "Jo", "Ari", "Rin"]


def valid_combo(guardian: str, quest: str) -> bool:
    if guardian not in GUARDIANS:
        return False
    if quest not in QUESTS:
        return False
    return True


def explain_rejection(guardian: str, quest: str) -> str:
    return f"No story: {guardian} and {quest} do not form a usable cassette myth."


def tell(params: StoryParams) -> World:
    if not valid_combo(params.guardian, params.quest):
        raise StoryError(explain_rejection(params.guardian, params.quest))

    place = GUARDIANS[params.guardian]
    quest = QUESTS[params.quest]
    world = World(place=place["label"])

    hero = world.add(Entity(
        params.hero_name,
        "character",
        params.hero_name,
        meters={"courage": 1.0},
        memes={"pride": 1.0},
    ))
    companion = world.add(Entity(
        params.companion_name,
        "character",
        params.companion_name,
        meters={"wisdom": 1.0},
        memes={"care": 1.0},
    ))
    cassette = world.add(Entity(
        "cassette",
        "artifact",
        "the enchanted cassette",
        meters={"memory": 1.0},
        memes={"humor": 1.0},
    ))
    guardian = world.add(Entity(
        params.guardian,
        "place",
        place["label"],
        meters={"wonder": 1.0},
        memes={"patience": 1.0},
    ))

    opening = OPENINGS[params.opening_variant % len(OPENINGS)].format(hero=hero.label)
    world.say(opening)
    world.say(
        f"It contained a myth about {hero.label} and {companion.label}, who had gone to "
        f"{place['label']} to {quest['goal']}."
    )
    world.say(
        f"The cassette had one strange rule: it always played the ending before the adventure was finished."
    )

    world.para()
    world.say(
        f"When {hero.label} pressed PLAY, the tiny speaker made a heroic trumpet sound: "
        f"“Ta-da-da-daaa!” Then it announced, “{hero.label} did everything alone!”"
    )
    world.say(f"That was the bad ending: {quest['danger']}.")
    world.say(f"{quest['evidence']}.")
    world.facts["bad_ending"] = True
    world.facts["hero_proud"] = True
    world.facts["companion_hurt"] = True
    hero.memes["pride"] = 2.0
    companion.memes["hurt"] = 1.0
    cassette.meters["wrongness"] = 1.0
    world.fired.add("bad_ending")

    world.para()
    response = RESPONSES[params.response_variant % len(RESPONSES)].format(
        companion=companion.label,
        hero=hero.label,
        repair=quest["repair"],
    )
    world.say(response)
    world.say(
        f"The cassette squeaked, “Rewind, rewind!” in a voice so tiny that it sounded like "
        f"a mouse trying to command a dragon."
    )
    world.say(f"Together they {quest['repair']}.")
    world.say(f"At once, {quest['result']}.")
    world.facts["reconciled"] = True
    world.facts["humor"] = True
    world.facts["resolution"] = quest["result"]
    hero.memes["pride"] = 0.5
    hero.memes["care"] = 1.0
    companion.memes["hurt"] = 0.0
    companion.memes["trust"] = 1.0
    cassette.meters["wrongness"] = 0.0
    cassette.memes["shared_story"] = 1.0
    world.fired.add("reconciliation")

    world.para()
    ending = ENDINGS[params.ending_variant % len(ENDINGS)]
    world.say(ending)
    world.say(
        f"And when the cassette played the tale again, it remembered that {place['lesson']}."
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        cassette=cassette,
        guardian=guardian,
        place=place["label"],
        object=place["object"],
        quest=quest,
        lesson=place["lesson"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a mythic children's story about an enchanted cassette with a bad ending.",
        f"Show how {f['hero'].label} and {f['companion'].label} repair a story that wrongly leaves one hero out.",
        f"Use humor, reconciliation, and a magical place; end with {f['resolution']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    return [
        QAItem(
            question=f"What did {hero.label} find?",
            answer=f"{hero.label} found an enchanted cassette beneath a humming stone. It could play the ending of a myth before the adventure was over.",
        ),
        QAItem(
            question="What was wrong with the first ending?",
            answer=f"The first ending claimed that {hero.label} did everything alone, even though {companion.label} was part of the quest. That made the story hurtful and left out an important helper.",
        ),
        QAItem(
            question=f"How did {hero.label} and {companion.label} repair the story?",
            answer=f"They admitted that the ending was wrong and {f['quest']['repair']}. Their shared recording changed the bad ending into a fair one.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The cassette remembered both voices, and {f['resolution']}. The myth became kinder because the heroes shared the credit.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cassette?",
            answer="A cassette is a small case containing magnetic tape that can store and play recorded sounds.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old or imaginative story about extraordinary people, creatures, places, or events that often carries a lesson.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a relationship after hurt feelings or a disagreement so people can trust one another again.",
        ),
        QAItem(
            question="Why is sharing credit important?",
            answer="Sharing credit is important because everyone who helps should be noticed and treated fairly.",
        ),
        QAItem(
            question="Why can humor help after a mistake?",
            answer="Gentle humor can make a mistake feel less frightening, but people still need to apologize and fix the harm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
guardian(moon_mountain).
guardian(whispering_forest).
guardian(sunken_city).
guardian(cloud_bridge).

quest(ring_the_bell).
quest(find_the_crown).
quest(unlock_the_city).
quest(cross_the_bridge).

cassette(cassette).
bad_ending(cassette).
reconciliation(cassette).
humor(cassette).

good_story(G, Q) :- guardian(G), quest(Q), cassette(cassette),
                     bad_ending(cassette), reconciliation(cassette),
                     humor(cassette).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for guardian in GUARDIANS:
        lines.append(asp.fact("guardian", guardian))
    for quest in QUESTS:
        lines.append(asp.fact("quest", quest))
    lines.extend([
        asp.fact("cassette", "cassette"),
        asp.fact("bad_ending", "cassette"),
        asp.fact("reconciliation", "cassette"),
        asp.fact("humor", "cassette"),
    ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = sorted((guardian, quest) for guardian in GUARDIANS for quest in QUESTS)
    cl = asp_valid_combos()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        for params in curated_params():
            generate(params)
        print("OK: generated stories exercised.")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", py)
    print("clingo:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mythic cassette story world with a bad ending, humor, and reconciliation."
    )
    parser.add_argument("--guardian", choices=GUARDIANS)
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--role", default="friend")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_pool = [n for n in HERO_NAMES if n not in {args.companion}]
    hero_name = args.name or rng.choice(hero_pool)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero_name])
    guardian = args.guardian or rng.choice(list(GUARDIANS))
    quest = args.quest or rng.choice(list(QUESTS))
    if not valid_combo(guardian, quest):
        raise StoryError(explain_rejection(guardian, quest))
    return StoryParams(
        hero_name=hero_name,
        hero_gender=gender,
        companion_name=companion,
        companion_role=args.role,
        guardian=guardian,
        quest=quest,
        opening_variant=rng.randrange(len(OPENINGS)),
        response_variant=rng.randrange(len(RESPONSES)),
        ending_variant=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("Luna", "girl", "Sol", "friend", "moon_mountain", "ring_the_bell"),
        StoryParams("Eli", "boy", "Mira", "friend", "whispering_forest", "find_the_crown"),
        StoryParams("Nora", "girl", "Taro", "friend", "sunken_city", "unlock_the_city"),
        StoryParams("Milo", "boy", "Rin", "friend", "cloud_bridge", "cross_the_bridge"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
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
        header = ""
        if args.all:
            header = (
                f"### {sample.params.hero_name}: "
                f"{sample.params.guardian} / {sample.params.quest}"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
