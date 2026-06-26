#!/usr/bin/env python3
"""
A storyworld for a tall-tale quest about dye, rhyme, and a little rescue.

Premise:
A young trail-rider wants a bright banner dyed for the spring fair. The dye pot
must be stirred with a rhyme, but the color only comes right if the seeker
fetches the last blue berry from a wind-bent hill.

Tension:
The banner is plain, the dye is too pale, and the rhyme is easy to forget.
The seeker must travel, gather, and speak carefully or the cloth will end up
muddy or dull.

Turn:
A helpful old singer teaches the right rhyme, and the quester follows a clue
through the reeds to the hill.

Resolution:
The banner comes back bright as a morningbird, and the whole camp cheers.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

VOWELS = set("aeiou")


def a_an(word: str) -> str:
    return "an" if word and word[0].lower() in VOWELS else "a"


def capitalize_sentence(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


@dataclass
class Character:
    name: str
    kind: str = "person"
    title: str = ""
    trait: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class QuestItem:
    id: str
    label: str
    color: str
    role: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    weather: str
    feature: str


@dataclass
class StoryParams:
    place: str
    quest: str
    dye: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.characters: dict[str, Character] = {}
        self.items: dict[str, QuestItem] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add_character(self, c: Character) -> Character:
        self.characters[c.name] = c
        return c

    def add_item(self, item: QuestItem) -> QuestItem:
        self.items[item.id] = item
        return item

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def rhyme_line(quest: str, dye: str) -> str:
    return f"By river and reed, by moon and flame, bring {dye} back home and sing its name"


def quest_hint(place: str) -> str:
    return {
        "riverbend": "the water curled around the stones like a blue rope",
        "hill": "the wind kept tugging at every loose hat and ribbon",
        "market": "the stalls rang with copper cups and bright cloth",
    }[place]


def dye_behavior(dye: str) -> tuple[str, str]:
    return {
        "blue": ("deep blue", "bright as a morningbird"),
        "gold": ("golden", "warm as butter on bread"),
        "red": ("red", "bold as a drumbeat"),
    }[dye]


def is_reasonable(params: StoryParams) -> bool:
    return params.quest in QUESTS and params.place in SETTINGS and params.dye in DYESTUFF


def build_story_world(params: StoryParams) -> World:
    if not is_reasonable(params):
        raise StoryError("The requested quest does not fit this little tale world.")

    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add_character(Character(name=params.hero, kind="person", title="quester", trait="brave"))
    helper = world.add_character(Character(name=params.helper, kind="person", title="singer", trait="old"))

    dye_item = world.add_item(QuestItem(id="dye", label=f"{params.dye} dye", color=params.dye, role="potion"))
    banner = world.add_item(QuestItem(id="banner", label="banner", color="plain", role="cloth", owner=hero.name))

    world.facts.update(hero=hero, helper=helper, dye_item=dye_item, banner=banner, params=params)
    return world


def narrate(world: World) -> None:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    helper: Character = world.facts["helper"]  # type: ignore[assignment]
    banner: QuestItem = world.facts["banner"]  # type: ignore[assignment]

    dye_word, final_image = dye_behavior(p.dye)
    rhyme = rhyme_line(p.quest, p.dye)
    place_note = quest_hint(p.place)

    hero.meters["hope"] = 1
    hero.memes["wonder"] = 1
    banner.meters["plain"] = 1

    world.say(
        f"In the {world.setting.place}, {hero.name} was a little quester with a big wish: "
        f"to make a banner shine {dye_word} for the fair."
    )
    world.say(
        f"The trouble was simple enough to fit in a teacup and sturdy enough to stall a wagon: "
        f"the dye would not wake up unless someone spoke the right rhyme."
    )

    world.para()
    world.say(
        f"{helper.name}, an old singer with a voice like a fiddle on a porch, nodded and said, "
        f"“{rhyme}.”"
    )
    world.say(
        f"But the last bit was still missing, and {place_note} said the clue lived far off on the {p.quest}."
    )

    world.para()
    hero.meters["travel"] = 1
    hero.memes["resolve"] = 1
    world.say(
        f"So {hero.name} took the banner cloth under one arm and set off on the quest, "
        f"following the creek, the reeds, and the windy bend where the berries clung to the hill."
    )
    world.say(
        f"At the top, {hero.name} found the last little berry, blue as dusk, and carried it home without dropping a crumb."
    )

    world.para()
    banner.color = dye_word
    banner.meters["dyed"] = 1
    hero.memes["joy"] = 2
    world.say(
        f"At last the rhyme was sung, the dye turned true, and the banner drank the color until it shone {final_image}."
    )
    world.say(
        f"{hero.name} held it high while {helper.name} laughed, and the whole camp cheered as if the stars had come down for supper."
    )
    world.facts["rhyme"] = rhyme
    world.facts["final_image"] = final_image


QUESTS = {
    "blue berry": "blue berry",
    "hill berry": "hill berry",
    "windberry": "windberry",
}

DYESTUFF = {"blue", "gold", "red"}

SETTINGS = {
    "riverbend": Setting(place="riverbend", weather="clear", feature="reeds"),
    "hill": Setting(place="windy hill", weather="blustery", feature="berries"),
    "market": Setting(place="the market square", weather="warm", feature="stalls"),
}

HERO_NAMES = ["Mira", "Jory", "Nell", "Pip", "Tess", "Wren", "Bram", "Lark"]
HELPER_NAMES = ["Old Mabel", "Uncle Pruitt", "Aunt Liza", "Captain Hush", "Merry Tom"]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for quest in QUESTS:
            for dye in DYESTUFF:
                if place == "market" and dye == "blue":
                    out.append((place, quest, dye))
                elif place != "market":
                    out.append((place, quest, dye))
    return out


def sample_name(rng: random.Random) -> str:
    return rng.choice(HERO_NAMES)


def sample_helper(rng: random.Random) -> str:
    return rng.choice(HELPER_NAMES)


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a tall tale for a child about a {p.dye} dye quest in {p.place}.",
        f"Tell a rhyming story where {p.hero} must finish a quest to make dye work.",
        f"Create a short, grand-sounding adventure with a helper, a rhyme, and a banner that changes color.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    hero: Character = world.facts["hero"]  # type: ignore[assignment]
    helper: Character = world.facts["helper"]  # type: ignore[assignment]
    rhyme = world.facts["rhyme"]
    return [
        QAItem(
            question=f"What did {hero.name} want to do in the story?",
            answer=f"{hero.name} wanted to finish a quest and dye the banner {p.dye} for the fair.",
        ),
        QAItem(
            question=f"Who helped {hero.name} with the rhyme?",
            answer=f"{helper.name}, the old singer, helped by sharing the rhyme that woke the dye.",
        ),
        QAItem(
            question="What happened to the banner at the end?",
            answer=f"The banner turned {p.dye} and shone {world.facts['final_image']}.",
        ),
        QAItem(
            question="What was the rhyme for?",
            answer=f"The rhyme was for waking the dye so the banner could take the color properly.",
        ),
        QAItem(
            question="What clue did the quest lead to?",
            answer=f"The quest led to the last berry at the windy place, which the hero brought back for the dye.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dye used for?",
            answer="Dye is used to change the color of cloth, thread, paper, or other things.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line or song where sounds at the ends of words match or nearly match.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal, like finding something important or helping someone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for c in world.characters.values():
        lines.append(f"{c.name}: meters={c.meters} memes={c.memes}")
    for item in world.items.values():
        lines.append(f"{item.id}: label={item.label} color={item.color} meters={item.meters}")
    return "\n".join(lines)


ASP_RULES = r"""
place(riverbend). place(hill). place(market).
quest(blue_berry). quest(hill_berry). quest(windberry).
dye(blue). dye(gold). dye(red).

compatible(P,Q,D) :- place(P), quest(Q), dye(D), P != market.
compatible(market,blue,Q) :- quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q.replace(" ", "_")))
    for d in DYESTUFF:
        lines.append(asp.fact("dye", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about dye, rhyme, and quest.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--dye", choices=sorted(DYESTUFF))
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.dye:
        combos = [c for c in combos if c[2] == args.dye]
    if not combos:
        raise StoryError("No valid tall-tale quest matches those options.")
    place, quest, dye = rng.choice(sorted(combos))
    hero = args.hero or sample_name(rng)
    helper = args.helper or sample_helper(rng)
    return StoryParams(place=place, quest=quest, dye=dye, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
    narrate(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place, quest, dye in sorted(valid_combos()):
            params = StoryParams(
                place=place,
                quest=quest,
                dye=dye,
                hero=HERO_NAMES[0],
                helper=HELPER_NAMES[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
