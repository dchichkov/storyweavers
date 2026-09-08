#!/usr/bin/env python3
"""
A small mythic quest storyworld about nine curry cakes, a watchful caw, and
the brave choice that restores a hungry village's golden bell.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
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
    seed: Optional[int] = None
    hero_name: str = "Luma"
    crow_name: str = "Caw"
    village: str = "Ashgrove"
    curry_kind: str = "sunny curry"
    quest_id: int = 0
    telling_mode: int = 0
    detail_variant: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


HERO_NAMES = ["Luma", "Neri", "Tavi", "Mira", "Oren"]
CROW_NAMES = ["Caw", "Blackwing", "Kek", "Rook"]
VILLAGES = ["Ashgrove", "Moonreed", "Redwillow", "Candlefen"]
CURRY_KINDS = ["sunny curry", "mango curry", "pumpkin curry", "golden curry"]

QUESTS = [
    {
        "title": "the bell on the cloud hill",
        "opening": "the village's bronze bell vanished before the first morning prayer",
        "danger": "a storm was climbing the valley, and without the bell's clear note, travelers could miss the safe road home",
        "clue": "nine warm curry cakes rested in a ring beside the empty bell rope",
        "trial": "a stone giant guarded the hill path and demanded a meal before it would move",
        "turn": "the giant was not cruel; it had been waiting alone through a long winter",
        "gift": "the giant lifted the bell from beneath a fallen cedar",
        "ending": "the restored bell rang over the valley while curry-scented steam curled toward the stars",
        "lesson": "a quest grows lighter when courage makes room for kindness",
    },
    {
        "title": "the river of red leaves",
        "opening": "the village spring turned red with leaves from a tree that had never grown there",
        "danger": "the strange current was carrying the village's drinking water toward a whirlpool",
        "clue": "nine curry cakes floated upstream, each marked with a tiny feather",
        "trial": "a river spirit asked the traveler to choose between a jeweled bridge and a plain bridge",
        "turn": "the plain bridge was made for everyone, while the jeweled one belonged only to the spirit",
        "gift": "the spirit opened the clear spring beneath the roots",
        "ending": "the water ran bright again, and nine curry cakes steamed on the riverbank",
        "lesson": "the fairest path is often the one that leaves room for others",
    },
    {
        "title": "the moon orchard",
        "opening": "the moon orchard stopped glowing, and every silver fruit curled into a hard little stone",
        "danger": "without the orchard's light, the village's night gardens would wither",
        "clue": "a single caw echoed from the highest branch whenever someone shared food",
        "trial": "a pale fox offered to return the light only if the traveler kept all nine curry cakes",
        "turn": "the hero noticed that the fox's den held no food at all",
        "gift": "after the cakes were shared, the fox led the way to a hidden moon seed",
        "ending": "the orchard bloomed again, with silver fruit shining above a grateful fox",
        "lesson": "generosity can reveal a door that greed leaves hidden",
    },
]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a quest?",
        answer="A quest is a purposeful journey in which someone faces trials while seeking a meaningful goal.",
    ),
    QAItem(
        question="Why does a myth use a talking animal or spirit?",
        answer="A myth may give animals or spirits a voice so they can reveal wisdom, test a hero, or show a hidden truth.",
    ),
    QAItem(
        question="What is curry?",
        answer="Curry is a flavorful dish or sauce made with a blend of spices and other ingredients.",
    ),
    QAItem(
        question="What does a crow's caw sound like?",
        answer="A crow's caw is a short, rough call that can serve as a warning or a greeting.",
    ),
]


ASP_RULES = r"""
quest(Q) :- quest_seed(Q).
has_nine(N) :- cakes(N), N = 9.
kind_quest(Q) :- quest(Q), has_nine(9), curry.
valid_story(Q) :- kind_quest(Q), caw.
"""


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed if params.seed is not None else 11)
    quest = QUESTS[params.quest_id % len(QUESTS)]
    hero = Entity(
        "hero",
        "character",
        params.hero_name,
        meters={"courage": 1.0, "hunger": 0.2},
        memes={"kindness": 0.5, "hope": 0.8},
    )
    crow = Entity(
        "crow",
        "bird",
        params.crow_name,
        meters={"alertness": 1.0},
        memes={"trust": 0.2},
    )
    cakes = Entity(
        "cakes",
        "food",
        "nine curry cakes",
        meters={"count": 9.0, "warmth": 1.0},
        memes={"welcome": 1.0},
    )
    world = World()
    world.add(hero)
    world.add(crow)
    world.add(cakes)

    opening_lines = [
        f"In the old days, beyond the red hills, the village of {params.village} woke beneath a pale sun.",
        f"At the edge of the world stood {params.village}, where every dawn began with a bell and a bowl of spice.",
        f"Long ago, when the hills still whispered to travelers, {params.village} kept one golden promise: no hungry guest would leave its gate.",
    ]
    world.say(opening_lines[params.detail_variant % len(opening_lines)])
    world.say(
        f"{params.hero_name} carried {params.curry_kind} made into exactly nine warm cakes, "
        f"for the village feast."
    )
    world.say(
        f"Above the gate, {params.crow_name} gave one sharp caw, then flew toward the eastern path."
    )

    world.para()
    world.say(f"That morning, {quest['opening']}.")
    world.say(f"The elders said, \"Whoever follows the caw may find what was taken.\"")
    world.say(f"{params.hero_name} answered, \"I will go, but I will not go empty-hearted.\"")
    world.say(
        f"So the hero set out with the nine curry cakes. {quest['danger'].capitalize()}."
    )
    world.say(f"At the first crossroads, {quest['clue'].capitalize()}.")

    world.para()
    world.say(f"The trail led to {quest['title']}, where {quest['trial']}.")
    world.say(
        f"{params.crow_name} circled overhead and cried, \"Caw! Look closely before you choose!\""
    )
    world.say(f"{params.hero_name} asked, \"What are you trying to show me?\"")
    world.say(f"The crow answered, \"The loudest guard may be the loneliest one.\"")
    world.say(f"Then {quest['turn'].capitalize()}.")
    world.say(
        f"{params.hero_name} divided the nine curry cakes instead of hiding them. "
        f"The hero offered three to the guardian, three to the crow, and three to the waiting path."
    )
    world.say(
        f"The choice changed the quest: {quest['gift'].capitalize()}."
    )

    world.para()
    hero.meters["courage"] += 1.0
    hero.memes["kindness"] += 1.0
    hero.memes["hope"] += 0.4
    crow.memes["trust"] += 1.0
    cakes.meters["count"] = 0.0
    world.say(
        f"{params.crow_name} bowed its black head. \"You had nine cakes,\" it said. "
        f"\"Now you have nine reasons to be remembered.\""
    )
    world.say(
        f"{params.hero_name} smiled. \"A feast is not smaller when it is shared.\""
    )
    world.say(f"The lesson of the quest was clear: {quest['lesson'].capitalize()}.")
    world.say(f"When evening came, {quest['ending'].capitalize()}.")

    world.facts.update(
        hero=hero,
        crow=crow,
        cakes=cakes,
        quest=quest,
        village=params.village,
        resolved=True,
        nine=True,
        curry=True,
        caw=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    return [
        "Write a child-friendly mythic quest involving nine curry cakes and a mysterious caw.",
        f"Tell a myth about {world.facts['hero'].label} completing {q['title']} through courage and kindness.",
        "Create a quest where sharing food changes what a guardian reveals.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    q = f["quest"]
    hero = f["hero"].label
    crow = f["crow"].label
    return [
        QAItem(
            question=f"Why did {hero} begin the quest?",
            answer=f"{hero} began the quest because {q['opening']}. The village needed someone to follow {crow}'s caw and discover the truth.",
        ),
        QAItem(
            question="What did the nine curry cakes do in the story?",
            answer="The nine curry cakes gave the hero a way to show kindness. Sharing them changed a lonely guardian from an obstacle into a helper.",
        ),
        QAItem(
            question=f"What did {crow} reveal?",
            answer=f"{crow} revealed that the loudest guard might be the loneliest one, so the hero should look closely instead of judging quickly.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"The quest ended when {q['gift'].capitalize()} and {q['ending']}. The village was safe, and the hero had learned to share courage with kindness.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("quest_seed", "mythic_quest"),
            asp.fact("cakes", 9),
            asp.fact("curry"),
            asp.fact("caw"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> None:
    if not params.hero_name.strip():
        raise StoryError("The quest hero needs a name.")
    if not params.crow_name.strip():
        raise StoryError("The guiding crow needs a name.")
    if params.hero_name == params.crow_name:
        raise StoryError("The hero and the crow must have different names.")
    if len(params.curry_kind.strip()) < 3:
        raise StoryError("The curry description is too short.")


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    found = set(asp.atoms(model, "valid_story"))
    expected = {("mythic_quest",)}
    if found == expected:
        print("OK: ASP gate matches Python reasonableness gate.")
        for seed in (3, 17, 42):
            params = StoryParams(seed=seed, quest_id=seed % len(QUESTS))
            python_reasonable(params)
            sample = generate(params)
            if "nine" not in sample.story.lower() or "curry" not in sample.story.lower():
                return 1
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("  ASP:", sorted(found))
    print("  PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic quest about nine curry cakes and a guiding caw.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--crow-name", choices=CROW_NAMES)
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--curry-kind", choices=CURRY_KINDS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        crow_name=args.crow_name or rng.choice(CROW_NAMES),
        village=args.village or rng.choice(VILLAGES),
        curry_kind=args.curry_kind or rng.choice(CURRY_KINDS),
        quest_id=rng.randrange(len(QUESTS)),
        telling_mode=rng.randrange(4),
        detail_variant=rng.randrange(12),
    )
    python_reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=list(WORLD_KNOWLEDGE),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:6} ({entity.kind:9}) "
            f"meters={meters} memes={memes}"
        )
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


CURATED = [
    StoryParams(hero_name="Luma", crow_name="Caw", village="Ashgrove", curry_kind="sunny curry", quest_id=0),
    StoryParams(hero_name="Neri", crow_name="Rook", village="Moonreed", curry_kind="mango curry", quest_id=1),
    StoryParams(hero_name="Tavi", crow_name="Blackwing", village="Redwillow", curry_kind="pumpkin curry", quest_id=2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        values = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(values)} valid quest pattern(s):")
        for value in values:
            print(" ", value)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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
