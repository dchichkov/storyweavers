#!/usr/bin/env python3
"""
Storyworld: a small folk-tale about sharing, a false claim, and the chaos it stirs.

A seed tale shape:
- In a little village, neighbors are asked to share a feast basket.
- One hungry helper makes a false claim about who took the bread.
- The village grows noisy and confused.
- The elders ask everyone to discuss the matter.
- The truth comes out, and the sharing becomes fair again.

This script builds that premise as a tiny world model with physical meters
(bread, baskets, crumbs, distance) and emotional memes (joy, worry, shame,
trust, confusion). The story prose is generated from the state changes so the
ending image proves what changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "elder"}
        male = {"boy", "man", "father", "grandfather", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village green"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    treasure: str
    hero: str
    helper: str
    elder: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.truth_revealed: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.truth_revealed = self.truth_revealed
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


TREASURES = {
    "bread": Treasure(
        id="bread",
        label="loaf of bread",
        phrase="a warm loaf of bread",
        plural=False,
    ),
    "berries": Treasure(
        id="berries",
        label="basket of berries",
        phrase="a basket of bright berries",
        plural=True,
    ),
    "porridge": Treasure(
        id="porridge",
        label="pot of porridge",
        phrase="a steaming pot of porridge",
        plural=False,
    ),
}

SETTINGS = {
    "green": Setting(place="the village green", affords={"share"}),
    "hall": Setting(place="the long hall", indoors=True, affords={"share"}),
    "well": Setting(place="the well square", affords={"share"}),
}

HERO_NAMES = ["Mara", "Nell", "Tobin", "Pip", "Hugh", "Elsie"]
HELPER_NAMES = ["Jory", "Bess", "Wren", "Pella", "Rowan", "Dina"]
ELDER_NAMES = ["Grandmother Ada", "Grandfather Bram", "Elder Ivo", "Elder Mira"]
TRAITS = ["kind", "quick", "gentle", "cheerful", "restless", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, tid) for place, s in SETTINGS.items() for tid in s.affords for _ in [0] if tid in {"share"}]


def parse_setting(place: str) -> Setting:
    try:
        return SETTINGS[place]
    except KeyError as exc:
        raise StoryError(f"Unknown place: {place}") from exc


def parse_treasure(tid: str) -> Treasure:
    try:
        return TREASURES[tid]
    except KeyError as exc:
        raise StoryError(f"Unknown treasure: {tid}") from exc


def story_intro(world: World, hero: Entity, helper: Entity, elder: Entity, treasure: Entity) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, {hero.id} loved the old folk way of sharing what little there was."
    )
    world.say(
        f"{helper.id} was fond of the same warm {treasure.label}, and {elder.id} had a wise voice that could calm a room."
    )
    world.say(
        f"They kept the {treasure.label} on a low table so everyone could reach {treasure.it()} with open hands."
    )


def predict_confusion(world: World, hero: Entity, helper: Entity, treasure: Entity) -> dict:
    sim = world.copy()
    _accuse(sim, sim.get(hero.id), sim.get(helper.id), sim.get(treasure.id), narrate=False)
    return {
        "confused": any(e.memes.get("confusion", 0) >= THRESHOLD for e in sim.characters()),
        "trust_lost": sim.get(helper.id).memes.get("shame", 0) >= THRESHOLD,
    }


def _accuse(world: World, hero: Entity, helper: Entity, treasure: Entity, narrate: bool = True) -> None:
    if ("accuse", hero.id, helper.id) in world.fired:
        return
    world.fired.add(("accuse", hero.id, helper.id))
    hero.memes["falsehood"] = hero.memes.get("falsehood", 0) + 1
    helper.memes["confusion"] = helper.memes.get("confusion", 0) + 1
    world.facts["accused"] = True
    if narrate:
        world.say(
            f"Then {hero.id} pointed at {helper.id} and made a false claim that {helper.id} had taken the best share."
        )


def _chaos(world: World, hero: Entity, helper: Entity, elder: Entity, treasure: Entity) -> None:
    if ("chaos", hero.id) in world.fired:
        return
    if hero.memes.get("falsehood", 0) < THRESHOLD:
        return
    world.fired.add(("chaos", hero.id))
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    elder.memes["worry"] = elder.memes.get("worry", 0) + 1
    world.facts["chaos"] = True
    world.say(
        f"At once the village went noisy; people talked at once, and even the crumbs on the table seemed caught in the chaos."
    )
    world.say(
        f"{helper.id} looked hurt, because a false story can sting harder than a hard crust of bread."
    )


def _discuss(world: World, hero: Entity, helper: Entity, elder: Entity, treasure: Entity) -> None:
    if ("discuss", hero.id) in world.fired:
        return
    if world.facts.get("chaos") is not True:
        return
    world.fired.add(("discuss", hero.id))
    elder.memes["calm"] = elder.memes.get("calm", 0) + 1
    hero.memes["shame"] = hero.memes.get("shame", 0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    world.facts["discussed"] = True
    world.say(
        f"{elder.id} raised a hand and asked everyone to discuss the matter one by one, like threading beads on a string."
    )
    world.say(
        f"{hero.id} admitted the truth: {hero.id} had spoken in haste and had not seen {helper.id} take anything at all."
    )


def _share_again(world: World, hero: Entity, helper: Entity, elder: Entity, treasure: Entity) -> None:
    if ("share_again", hero.id) in world.fired:
        return
    if not world.facts.get("discussed"):
        return
    world.fired.add(("share_again", hero.id))
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    elder.memes["joy"] = elder.memes.get("joy", 0) + 1
    treasure.shared = True
    world.say(
        f"With the truth in the open, they shared the {treasure.label} fairly: one piece for each hand, and a little extra for the smallest child."
    )
    world.say(
        f"The false tale fell away, the chaos quieted, and {helper.id} and {hero.id} ate side by side under a clear, peaceful sky."
    )


def propagate(world: World, hero: Entity, helper: Entity, elder: Entity, treasure: Entity, narrate: bool = True) -> None:
    _chaos(world, hero, helper, elder, treasure)
    _discuss(world, hero, helper, elder, treasure)
    _share_again(world, hero, helper, elder, treasure)


def tell(setting: Setting, treasure_cfg: Treasure, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="boy" if params.hero in {"Tobin", "Pip", "Hugh"} else "girl"))
    helper = world.add(Entity(id=params.helper, kind="character", type="boy" if params.helper in {"Jory", "Rowan"} else "girl"))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder"))
    treasure = world.add(Entity(
        id=treasure_cfg.id,
        kind="thing",
        type=treasure_cfg.id,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        shared=True,
        plural=treasure_cfg.plural,
    ))

    hero.memes["desire"] = 1
    helper.memes["trust"] = 1
    elder.memes["calm"] = 1

    story_intro(world, hero, helper, elder, treasure)
    world.para()
    world.say(
        f"One day, the {treasure.label} was meant to be shared after the morning work, but hunger made {hero.id} impatient."
    )
    world.say(
        f"{hero.id} saw {helper.id} reach near the table and made a false claim before thinking twice."
    )

    world.para()
    _accuse(world, hero, helper, treasure)
    propagate(world, hero, helper, elder, treasure)

    world.facts.update(hero=hero, helper=helper, elder=elder, treasure=treasure, setting=setting, treasure_cfg=treasure_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about sharing {f["treasure_cfg"].phrase}, a false claim, and a calm discussion that repairs the village mood.',
        f"Tell a simple story in which {f['hero'].id} and {f['helper'].id} must share {f['treasure'].label}, then a false story causes chaos until {f['elder'].id} asks them to discuss it.",
        f"Write a gentle village story using the words “sharing,” “false,” “discuss,” and “chaos.”",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, elder, treasure = f["hero"], f["helper"], f["elder"], f["treasure"]
    return [
        QAItem(
            question=f"Who made the false claim in the village story?",
            answer=f"{hero.id} made the false claim about {helper.id}, and that is what started the trouble.",
        ),
        QAItem(
            question=f"Why did the village become chaotic?",
            answer=f"It became chaotic because {hero.id} said something false, so everyone started talking at once and the mood turned messy.",
        ),
        QAItem(
            question=f"What did {elder.id} ask everyone to do?",
            answer=f"{elder.id} asked everyone to discuss the matter one by one, so the truth could come out clearly.",
        ),
        QAItem(
            question=f"How did the story end for the {treasure.label}?",
            answer=f"In the end, the {treasure.label} was shared fairly again, and the village became calm and kind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share something?",
            answer="To share something means to let other people have some of it too, instead of keeping it all for yourself.",
        ),
        QAItem(
            question="What is a false claim?",
            answer="A false claim is a statement that is not true.",
        ),
        QAItem(
            question="Why can a discussion help?",
            answer="A discussion can help because people take turns speaking, listen carefully, and sort out confusion.",
        ),
        QAItem(
            question="What is chaos?",
            answer="Chaos is a messy time when things feel loud, confused, and hard to keep in order.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.shared:
            bits.append("shared=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the treasure is shared, a false claim causes chaos,
% and a discussion resolves the confusion.
false_claim(H, T) :- hero(H), treasure(T), hears(H, T).
chaos(H, T) :- false_claim(H, T), village(v1).
discuss(E, H, T) :- elder(E), chaos(H, T).
resolved(T) :- discuss(E, H, T), shared(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.plural:
            lines.append(asp.fact("plural", tid))
        lines.append(asp.fact("shared", tid))
    for name in HERO_NAMES:
        lines.append(asp.fact("hero", name))
        lines.append(asp.fact("hears", name, "bread"))
    for name in ELDER_NAMES:
        lines.append(asp.fact("elder", name))
    lines.append(asp.fact("village", "v1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved/1. #show chaos/2. #show discuss/3."))
    if model:
        print("OK: ASP program loaded.")
        return 0
    print("MISMATCH or empty model.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld about sharing, false claims, discussion, and chaos.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--elder", choices=ELDER_NAMES)
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
    place = args.place or rng.choice(list(SETTINGS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    elder = args.elder or rng.choice(ELDER_NAMES)
    if hero == helper:
        raise StoryError("The hero and helper must be different people.")
    return StoryParams(place=place, treasure=treasure, hero=hero, helper=helper, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(parse_setting(params.place), parse_treasure(params.treasure), params)
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
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show false_claim/2. #show chaos/2. #show discuss/3. #show resolved/1."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for treasure in TREASURES:
                params = StoryParams(
                    place=place,
                    treasure=treasure,
                    hero=HERO_NAMES[0],
                    helper=HELPER_NAMES[0],
                    elder=ELDER_NAMES[0],
                )
                samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
