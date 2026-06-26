#!/usr/bin/env python3
"""
storyworlds/worlds/macrame_friend_sift_friendship_moral_value_lesson.py
=======================================================================

A small fairy-tale storyworld about macrame, a friend who sifts, and a gentle
lesson about friendship and moral value.

The world is built from a short simulated premise:
- a child and a friend are making a macrame item,
- one of them sifts for small bright pieces or shells,
- a snag, delay, or mix-up creates tension,
- sharing, patience, and kindness resolve it,
- the ending carries a clear lesson learned.

The script keeps the storyworld contract:
- typed entities with physical meters and emotional memes,
- a reasonableness gate in Python and an inline ASP twin,
- generation, QA, JSON, trace, verify, and show-ASP support.
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    keyword: str
    requires_sift: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    region: str
    value: str
    fragile: bool = False


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    placeable: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "garden": Setting(place="the garden", mood="sunlit", affords={"macrame", "sift"}),
    "meadow": Setting(place="the meadow", mood="windy", affords={"macrame", "sift"}),
    "courtyard": Setting(place="the courtyard", mood="quiet", affords={"macrame", "sift"}),
}

ACTIVITIES = {
    "macrame": Activity(
        id="macrame",
        verb="weave a macrame charm",
        gerund="weaving macrame charms",
        mess="tangled",
        soil="all tangled",
        keyword="macrame",
        requires_sift=False,
        tags={"macrame"},
    ),
    "sift": Activity(
        id="sift",
        verb="sift through little bits in the bowl",
        gerund="sifting through little bits",
        mess="scattered",
        soil="scattered everywhere",
        keyword="sift",
        requires_sift=True,
        tags={"sift"},
    ),
}

TREASURES = {
    "cord": Treasure(
        id="cord",
        label="cord",
        phrase="a soft bundle of bright cord",
        region="hands",
        value="useful",
    ),
    "beads": Treasure(
        id="beads",
        label="beads",
        phrase="a little bag of shining beads",
        region="hands",
        value="pretty",
    ),
    "shells": Treasure(
        id="shells",
        label="shells",
        phrase="a small bowl of tiny shells",
        region="hands",
        value="treasured",
        fragile=True,
    ),
}

GIFTS = {
    "wallhanging": Gift(
        id="wallhanging",
        label="wall hanging",
        phrase="a wall hanging with knots and loops",
        placeable="hang on the cottage wall",
        tags={"macrame"},
    ),
    "bracelet": Gift(
        id="bracelet",
        label="bracelet",
        phrase="a bracelet with a tiny tassel",
        placeable="wear on the wrist",
        tags={"macrame"},
    ),
    "pouch": Gift(
        id="pouch",
        label="pouch",
        phrase="a little pouch with a neat tie",
        placeable="hold small things",
        tags={"macrame"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ada", "Elsie", "Rose", "Tilly"]
BOY_NAMES = ["Evan", "Owen", "Theo", "Finn", "Jasper", "Robin"]
FRIEND_NAMES = ["Pip", "Nell", "Bram", "Wren", "Milo", "Clara"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wore_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"tangled": 0.0, "scattered": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "care": 0.0, "frustration": 0.0, "trust": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    activity: str
    treasure: str
    gift: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


THRESHOLD = 1.0


def _narrate_join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["care"] < THRESHOLD or friend.memes["care"] < THRESHOLD:
        return out
    if hero.meters["tangled"] >= THRESHOLD and ("tangle", "hero") not in world.fired:
        world.fired.add(("tangle", "hero"))
        hero.memes["frustration"] += 1
        out.append("The knots tugged at the cord, and the work became tricky.")
    if friend.meters["scattered"] >= THRESHOLD and ("scatter", "friend") not in world.fired:
        world.fired.add(("scatter", "friend"))
        friend.memes["frustration"] += 1
        out.append("The little bits slipped apart, and the bowl looked messy.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["trust"] < THRESHOLD or friend.memes["trust"] < THRESHOLD:
        return out
    if hero.memes["joy"] >= THRESHOLD and friend.memes["joy"] >= THRESHOLD and ("help",) not in world.fired:
        world.fired.add(("help",))
        hero.memes["lesson"] += 1
        friend.memes["lesson"] += 1
        out.append("Together, they found a kinder way to finish.")
    return out


RULES = [_r_tangle, _r_help]


def propagate(world: World) -> list[str]:
    said: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            produced = rule(world)
            if produced:
                changed = True
                said.extend(produced)
    for s in said:
        world.say(s)
    return said


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero_care(H) :- cares(H).
friendship(H,F) :- trusts(H,F), trusts(F,H).
tension(H) :- tangled(H).
tension(F) :- scattered(F).
lesson(H) :- friendship(H,_), chooses_kindness(H).
resolution :- lesson(hero), lesson(friend).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if a.requires_sift:
            lines.append(asp.fact("requires_sift", aid))
        lines.append(asp.fact("mess", aid, a.mess))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("value", tid, t.value))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_tag", gid, "macrame"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Simple parity check: every setting allows both activities, so facts are stable.
    model = asp.one_model(asp_program("#show setting/1."))
    seen = set(asp.atoms(model, "setting"))
    want = {(sid,) for sid in SETTINGS}
    if seen == want:
        print(f"OK: ASP facts match settings ({len(seen)} settings).")
        return 0
    print("MISMATCH in ASP settings.")
    print("  seen:", sorted(seen))
    print("  want:", sorted(want))
    return 1


# ---------------------------------------------------------------------------
# Story synthesis
# ---------------------------------------------------------------------------
def _make_story(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    treasure = world.get("treasure")
    gift = world.get("gift")

    world.say(
        f"Once in {world.setting.place}, there lived a little {hero.type} named {hero.id}, "
        f"who loved gentle work and bright days."
    )
    world.say(
        f"{hero.id} had a dear friend named {friend.id}, and together they began to make "
        f"{gift.phrase} from {treasure.phrase}."
    )
    world.say(
        f"They sat by a low stone table and smiled, for the day was {world.setting.mood} "
        f"and the cord looked like a thread of moonlight."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to {ACTIVITIES[world.facts['activity']].verb}, while {friend.id} "
        f"chose to sift carefully for the finest pieces."
    )
    if world.facts["activity"] == "sift":
        friend.meters["scattered"] += 1
        friend.memes["care"] += 1
        world.say("The tiny bits slid through the fingers like rain through a fence.")
    else:
        hero.meters["tangled"] += 1
        hero.memes["care"] += 1
        world.say("The cords curled and knotted, and the pattern would not lie still.")

    world.say(
        f"Then a small trouble came: {friend.id} grew worried that {treasure.label} would be "
        f"used up too quickly, and {hero.id} grew cross when the knots slowed their hands."
    )
    hero.memes["frustration"] += 1
    friend.memes["frustration"] += 1
    propagate(world)

    world.para()
    world.say(
        f"At last {friend.id} said, '{hero.id}, let us share the work. You twist the cord, "
        f"and I will sift for the neatest pieces.'"
    )
    world.say(
        f"{hero.id} nodded, because a true friend listens before the sun goes down."
    )
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    propagate(world)

    world.para()
    world.say(
        f"By evening, the macrame charm was finished. It shone softly, and its knots were "
        f"as even as little pearls."
    )
    world.say(
        f"{hero.id} and {friend.id} hung the gift where the wind could touch it, and both "
        f"felt proud that patience had made the best magic."
    )
    world.say(
        "Lesson learned: when friends share the work, a hard task can become a happy one."
    )


def tell_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_type))
    treasure = world.add(Entity(id="treasure", type="thing", label=TREASURES[params.treasure].label))
    gift = world.add(Entity(id="gift", type="thing", label=GIFTS[params.gift].label))

    hero.memes["care"] = 1.0
    friend.memes["care"] = 1.0
    hero.memes["trust"] = 0.5
    friend.memes["trust"] = 0.5

    world.facts.update(
        place=params.place,
        activity=params.activity,
        treasure=params.treasure,
        gift=params.gift,
        hero=hero,
        friend=friend,
    )
    _make_story(world)
    world.facts["resolved"] = hero.memes["lesson"] >= THRESHOLD and friend.memes["lesson"] >= THRESHOLD
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story about macrame and friendship that includes the word "{ACTIVITIES[f["activity"]].keyword}".',
        f"Tell a gentle story in {world.setting.place} where a child and a friend make {GIFTS[f['gift']].label} from {TREASURES[f['treasure']].label}.",
        f"Write a child-friendly lesson story where a friend sifts carefully and the friends finish their craft together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = ACTIVITIES[f["activity"]]
    treasure = TREASURES[f["treasure"]]
    gift = GIFTS[f["gift"]]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {hero.id} and {friend.id}, who worked together like good friends in {world.setting.place}.",
        ),
        QAItem(
            question=f"What were they making with the {treasure.label}?",
            answer=f"They were making {gift.phrase}, using {treasure.phrase} and careful hands.",
        ),
        QAItem(
            question=f"Why did the work become tricky?",
            answer=f"The work became tricky because {hero.id} and {friend.id} wanted different parts of the job, and the cord and little pieces needed patience.",
        ),
        QAItem(
            question=f"What lesson was learned at the end?",
            answer="The lesson was that friends should share the work, listen kindly, and finish hard tasks together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is macrame?",
            answer="Macrame is a craft made by tying cords into knots and patterns.",
        ),
        QAItem(
            question="What does it mean to sift?",
            answer="To sift means to let small pieces pass through carefully so you can find what you need.",
        ),
        QAItem(
            question="Why is friendship valuable?",
            answer="Friendship is valuable because a friend can help, listen, and make a hard day feel lighter.",
        ),
    ]
    if f["activity"] == "sift":
        out.append(QAItem(
            question="Why did sifting matter in this story?",
            answer="Sifting mattered because it helped choose the neatest little pieces for the craft.",
        ))
    return out


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / validation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for treasure_id in TREASURES:
                for gift_id in GIFTS:
                    if act_id == "sift" and treasure_id == "cord":
                        continue
                    combos.append((place, act_id, treasure_id, gift_id))
    return combos


CURATED = [
    StoryParams(
        place="garden",
        activity="macrame",
        treasure="beads",
        gift="wallhanging",
        hero_name="Mina",
        hero_type="girl",
        friend_name="Pip",
        friend_type="boy",
    ),
    StoryParams(
        place="meadow",
        activity="sift",
        treasure="shells",
        gift="pouch",
        hero_name="Evan",
        hero_type="boy",
        friend_name="Nell",
        friend_type="girl",
    ),
    StoryParams(
        place="courtyard",
        activity="macrame",
        treasure="cord",
        gift="bracelet",
        hero_name="Ada",
        hero_type="girl",
        friend_name="Wren",
        friend_type="girl",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about macrame, a friend, and sifting.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.treasure is None or c[2] == args.treasure)
              and (args.gift is None or c[3] == args.gift)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, treasure, gift = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if friend_name == hero_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        activity=activity,
        treasure=treasure,
        gift=gift,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_program_valid() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for treasure in TREASURES:
                for gift in GIFTS:
                    lines.append(asp.fact("valid", place, act, treasure, gift))
    return "\n".join(lines) + "\n"


def asp_verify_gate() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP gate matches Python valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python combos.")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:\n")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name} in {p.place} ({p.activity})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
