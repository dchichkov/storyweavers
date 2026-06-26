#!/usr/bin/env python3
"""
Thin Bid Conflict Mystery
=========================

A standalone storyworld about a small, child-friendly mystery: a thin clue,
a bid that causes conflict, and a gentle resolution when the truth is found.

The world is built from a short source-tale premise:
- a child wants to make a bid at a little auction
- a thin scrap of evidence goes missing or seems suspicious
- the wrong person gets blamed
- the child follows clues, finds the real reason, and the conflict softens

The simulation tracks physical meters and emotional memes, then turns them into
complete, state-driven prose.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    place: str
    thin: bool = False
    suspicious: bool = False


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    honest: bool
    nervous: bool = False


@dataclass
class BidItem:
    id: str
    label: str
    phrase: str
    value: int
    fragile: bool = False


@dataclass
class StoryParams:
    place: str
    hero: str
    gender: str
    parent: str
    suspect: str
    item: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "attic_shop": Setting(place="the attic shop", affords={"bid", "search", "inspect"}),
    "silent_room": Setting(place="the silent room", affords={"bid", "search", "inspect"}),
    "old_market": Setting(place="the old market", affords={"bid", "search", "inspect"}),
}

HERO_NAMES = ["Mina", "Toby", "Lina", "Evan", "Ruby", "Noah", "Ivy", "Arlo"]
BOY_NAMES = ["Toby", "Evan", "Noah", "Arlo"]
GIRL_NAMES = ["Mina", "Lina", "Ruby", "Ivy"]
PARENT_TYPES = ["mother", "father"]

SUSPECTS = {
    "mason": Suspect(id="mason", label="Mr. Mason", type="man", alibi="was pricing boxes in the back room", honest=True),
    "greta": Suspect(id="greta", label="Mrs. Greta", type="woman", alibi="was carrying a stack of old books", honest=True),
    "piper": Suspect(id="piper", label="Piper", type="girl", alibi="was tying a ribbon on a chair", honest=False, nervous=True),
}

ITEMS = {
    "clock": BidItem(id="clock", label="clock", phrase="a tiny brass clock", value=12, fragile=True),
    "book": BidItem(id="book", label="book", phrase="a picture book with a blue cover", value=7),
    "shell": BidItem(id="shell", label="shell", phrase="a bright shell in a paper tray", value=5),
}

CLUES = {
    "thread": Clue(id="thread", label="thread", phrase="a thin white thread", place="chair leg", thin=True),
    "receipt": Clue(id="receipt", label="receipt", phrase="a thin receipt slip", place="table edge", thin=True),
    "dust": Clue(id="dust", label="dust", phrase="a thin line of dust", place="window sill", thin=True),
}


@dataclass
class StoryModel:
    hero: Entity
    parent: Entity
    suspect: Entity
    item: Entity
    clue: Entity
    setting: Setting
    conflict: bool = False
    resolved: bool = False
    culprit: Optional[str] = None


def bid_possible(item: BidItem) -> bool:
    return item.value > 0


def clue_is_thin(clue: Clue) -> bool:
    return clue.thin


def suspicious_combo(suspect: Suspect, clue: Clue) -> bool:
    return clue.place in {"chair leg", "table edge", "window sill"} and suspect.nervous


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Thin bid conflict mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    item = args.item or rng.choice(list(ITEMS))
    clue = args.clue or rng.choice(list(CLUES))

    if clue == "thread" and item != "clock":
        # thin thread clue pairs best with the fragile clock mystery.
        item = "clock"
    if item == "clock" and suspect == "mason":
        # still valid; no explicit rejection.
        pass

    return StoryParams(place=place, hero=hero, gender=hero_gender, parent=parent, suspect=suspect, item=item, clue=clue)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(id=params.hero, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    suspect = SUSPECTS[params.suspect]
    suspect_ent = world.add(Entity(id=suspect.id, kind="character", type=suspect.type, label=suspect.label))
    item = ITEMS[params.item]
    item_ent = world.add(Entity(id=item.id, type="thing", label=item.label, phrase=item.phrase, caretaker=parent.id))
    clue = CLUES[params.clue]
    clue_ent = world.add(Entity(id=clue.id, type="thing", label=clue.label, phrase=clue.phrase))

    model = StoryModel(hero=hero, parent=parent, suspect=suspect_ent, item=item_ent, clue=clue_ent, setting=world.setting)
    world.facts["model"] = model
    world.facts["bid_item"] = item
    world.facts["clue_def"] = clue
    world.facts["suspect_def"] = suspect

    # Act 1
    world.say(
        f"{hero.id} was a little {params.gender} who loved quiet rooms and careful questions."
    )
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {params.parent} went to {world.setting.place}, where a small bid could win {item.phrase}."
    )
    world.say(
        f"{hero.id} wanted to make a bid, but {hero.pronoun('possessive')} eyes kept returning to {clue.phrase}."
    )

    # Act 2
    world.para()
    if bid_possible(item):
        hero.memes["desire"] = hero.memes.get("desire", 0) + 1
        world.say(
            f"The room felt still, and then a hush fell when {hero.id} held up a hand for the bid."
        )
        world.say(
            f"At the same time, someone whispered that the {clue.label} looked suspiciously thin."
        )

    clue_ent.meters["thin"] = 1 if clue_is_thin(clue) else 0
    suspect_ent.memes["nervous"] = 1 if suspect.nervous else 0
    model.conflict = True
    world.facts["conflict"] = True
    world.say(
        f"{params.parent.capitalize()} frowned, because the clue was thin and the first guess pointed at {suspect.label}."
    )
    world.say(
        f"{suspect.label} looked startled and said {suspect.alibi}, but that only made the room feel more tense."
    )

    # Act 3: investigation
    world.para()
    world.say(
        f"{hero.id} did not rush. {hero.pronoun().capitalize()} bent down, followed the thin clue, and checked where it ended."
    )
    if clue.id == "thread":
        world.say(
            f"The thread led to the chair leg, where a snag had pulled it loose from the item's wrapping."
        )
        culprit = "accident"
    elif clue.id == "receipt":
        world.say(
            f"The receipt slip matched the item tray, so the missing piece had simply been moved by the wind."
        )
        culprit = "wind"
    else:
        world.say(
            f"The line of dust pointed to the window sill, where sunlight had carried it into a neat stripe."
        )
        culprit = "dust"

    if suspect.nervous:
        world.say(
            f"{suspect.label} had only been nervous because {suspect.alibi}, not because {culprit} was a lie."
        )
    world.say(
        f"Then {hero.id} showed how the clue fit the scene, and the blame lifted away from {suspect.label}."
    )

    # Resolution
    world.para()
    model.resolved = True
    model.culprit = culprit
    world.facts["resolved"] = True
    world.facts["culprit"] = culprit
    world.say(
        f"{params.parent.capitalize()} nodded and said the bid could still happen."
    )
    world.say(
        f"{hero.id} made the bid, and when the little item was finally won, the room felt calm instead of sharp."
    )
    world.say(
        f"By the end, the thin clue was no longer mysterious, and {hero.id} stood beside {suspect.label} with a relieved smile."
    )
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    model: StoryModel = f["model"]
    return [
        'Write a short mystery story for a young child that includes a thin clue and a bid.',
        f"Tell a gentle mystery about {model.hero.id} at {world.setting.place} where a bid causes conflict and a thin clue helps solve the problem.",
        f"Write a child-friendly story where {model.hero.id} follows a thin clue, clears {model.suspect.label}'s name, and makes a bid.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    model: StoryModel = f["model"]
    item: BidItem = f["bid_item"]
    clue: Clue = f["clue_def"]
    suspect: Suspect = f["suspect_def"]
    return [
        QAItem(
            question=f"What did {model.hero.id} want to do at {world.setting.place}?",
            answer=f"{model.hero.id} wanted to make a bid for {item.phrase} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why was the room tense when the clue looked suspicious?",
            answer=f"The room felt tense because the clue was thin, and people first guessed that {suspect.label} might be to blame.",
        ),
        QAItem(
            question=f"How did {model.hero.id} solve the mystery?",
            answer=f"{model.hero.id} followed the thin clue, saw how it fit the scene, and proved that {suspect.label} was not the culprit.",
        ),
        QAItem(
            question=f"What happened after the mystery was understood?",
            answer=f"The blame lifted, the bid could happen, and the room became calm again.",
        ),
        QAItem(
            question=f"Why was the clue described as thin?",
            answer=f"It was a thin scrap of evidence, like a little thread or slip of paper, so it was easy to miss unless someone looked closely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bid?",
            answer="A bid is an offer to pay a certain amount of money for something, often in an auction.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story or problem where something is not understood at first, and clues help find the answer.",
        ),
        QAItem(
            question="What does thin mean?",
            answer="Thin means not wide or thick; a thin thing can be narrow like a thread or a small slip of paper.",
        ),
        QAItem(
            question="Why do people look at clues?",
            answer="People look at clues because clues can point to what really happened and help solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    model: StoryModel = world.facts["model"]
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  conflict={model.conflict}")
    lines.append(f"  resolved={model.resolved}")
    lines.append(f"  culprit={model.culprit}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic_shop", hero="Mina", gender="girl", parent="mother", suspect="piper", item="clock", clue="thread"),
    StoryParams(place="old_market", hero="Toby", gender="boy", parent="father", suspect="greta", item="book", clue="receipt"),
    StoryParams(place="silent_room", hero="Ivy", gender="girl", parent="mother", suspect="mason", item="shell", clue="dust"),
]


ASP_RULES = r"""
place(attic_shop). place(old_market). place(silent_room).
affords(attic_shop,bid). affords(attic_shop,search). affords(attic_shop,inspect).
affords(old_market,bid). affords(old_market,search). affords(old_market,inspect).
affords(silent_room,bid). affords(silent_room,search). affords(silent_room,inspect).

item(clock). item(book). item(shell).
thin_clue(thread). thin_clue(receipt). thin_clue(dust).
clue_place(thread,chair_leg). clue_place(receipt,table_edge). clue_place(dust,window_sill).
suspicious_place(chair_leg). suspicious_place(table_edge). suspicious_place(window_sill).

bid_safe(P) :- item(P).
mystery_ok(C) :- thin_clue(C), clue_place(C,_).
valid_story(Place,Item,Clue) :- place(Place), item(Item), thin_clue(Clue), affords(Place,bid), mystery_ok(Clue), bid_safe(Item).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in sorted(SETTINGS[p].affords):
            lines.append(asp.fact("affords", p, a))
    for i in ITEMS:
        lines.append(asp.fact("item", i))
    for c in CLUES:
        lines.append(asp.fact("thin_clue", c))
        lines.append(asp.fact("clue_place", c, CLUES[c].place.replace(" ", "_")))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for item in ITEMS:
            for clue in CLUES:
                if "bid" in setting.affords and clue_is_thin(CLUES[clue]):
                    combos.append((place, item, clue))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection() -> str:
    return "(No story: the requested choices do not make a believable thin-clue bid mystery.)"


def resolve_random_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError(explain_rejection())
    if args.item and args.item not in ITEMS:
        raise StoryError(explain_rejection())
    if args.clue and args.clue not in CLUES:
        raise StoryError(explain_rejection())
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        hero=args.hero or rng.choice(HERO_NAMES if not args.gender else (GIRL_NAMES if args.gender == "girl" else BOY_NAMES)),
        gender=args.gender or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(PARENT_TYPES),
        suspect=args.suspect or rng.choice(list(SUSPECTS)),
        item=args.item or rng.choice(list(ITEMS)),
        clue=args.clue or rng.choice(list(CLUES)),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(set(asp.atoms(model, 'valid_story')))} compatible combos:")
        for t in asp.atoms(model, "valid_story"):
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_random_choice(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.item} / {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
