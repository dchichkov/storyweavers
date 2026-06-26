#!/usr/bin/env python3
"""
storyworlds/worlds/nocturnal_sharing_adventure.py
=================================================

A small nocturnal adventure storyworld about sharing gear, light, and courage.

Seed premise:
- A child wants a nighttime adventure.
- The adventure is only safe and fun if something important is shared.
- The story turns when the characters stop hoarding and cooperate.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    handheld_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
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
    nocturnal: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    allows: set[str] = field(default_factory=set)  # what it shares well
    boost: str = ""  # what positive thing it adds


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    tells: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "camp": Setting(place="the quiet camp", nocturnal=True, affords={"lantern_walk", "map_search"}),
    "garden": Setting(place="the moonlit garden", nocturnal=True, affords={"lantern_walk", "snack_search"}),
    "beach": Setting(place="the dark beach", nocturnal=True, affords={"lantern_walk", "shell_search"}),
    "attic": Setting(place="the old attic", nocturnal=True, affords={"map_search", "lantern_walk"}),
}

ACTIVITIES = {
    "lantern_walk": Activity(
        id="lantern_walk",
        verb="walk by the lantern light",
        gerund="walking by lantern light",
        rush="dash into the dark path",
        mess="dim",
        soil="lost in the dark",
        zone={"hands", "feet"},
        keyword="lantern",
        tags={"lantern", "dark", "night"},
    ),
    "map_search": Activity(
        id="map_search",
        verb="search for a hidden path",
        gerund="searching for a hidden path",
        rush="race into the wrong hallway",
        mess="scattered",
        soil="mixed up",
        zone={"hands", "eyes"},
        keyword="map",
        tags={"map", "night"},
    ),
    "snack_search": Activity(
        id="snack_search",
        verb="find the midnight snack",
        gerund="looking for a midnight snack",
        rush="grab the first crumbly box",
        mess="crumbled",
        soil="crumbled and sticky",
        zone={"hands", "mouth"},
        keyword="snack",
        tags={"snack", "night"},
    ),
    "shell_search": Activity(
        id="shell_search",
        verb="look for shining shells",
        gerund="looking for shining shells",
        rush="rush to the waterline",
        mess="sandy",
        soil="full of sand",
        zone={"hands", "feet"},
        keyword="shell",
        tags={"shell", "night", "beach"},
    ),
}

SHARE_ITEMS = {
    "lantern": ShareItem(
        id="lantern",
        label="lantern",
        phrase="a bright lantern",
        region="hands",
        allows={"lantern_walk", "map_search"},
        boost="gave them a brave little circle of light",
    ),
    "map": ShareItem(
        id="map",
        label="map",
        phrase="a folded paper map",
        region="hands",
        allows={"map_search"},
        boost="made the path feel easier to understand",
    ),
    "blanket": ShareItem(
        id="blanket",
        label="blanket",
        phrase="a warm blanket",
        region="shoulders",
        allows={"lantern_walk", "shell_search"},
        boost="kept the night air from feeling too cold",
        plural=False,
    ),
    "snack": ShareItem(
        id="snack",
        label="snack",
        phrase="a small snack box",
        region="hands",
        allows={"snack_search"},
        boost="kept their bellies happy and steady",
    ),
}

AIDS = {
    "firefly": Aid(
        id="firefly",
        label="firefly",
        phrase="a tiny firefly friend",
        helps={"lantern_walk", "map_search"},
        tells="Its blink-blink glow showed where the path bent.",
    ),
    "older_sibling": Aid(
        id="older_sibling",
        label="older sibling",
        phrase="an older sibling with calm hands",
        helps={"map_search", "snack_search"},
        tells="They knew how to pause, share, and check the next step together.",
    ),
}

GIRL_NAMES = ["Mina", "Iris", "Lena", "Nina", "Ruby", "Tess"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Milo", "Ezra", "Jude"]
TRAITS = ["curious", "brave", "gentle", "restless", "cheerful", "careful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    share_item: str
    name: str
    gender: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_valid(P) :- setting(P).
activity_valid(A) :- activity(A).

shared_ok(A, I) :- activity(A), share_item(I), helps(I, A).
valid_story(P, A, I) :- setting(P), activity(A), share_item(I), affords(P, A), shared_ok(A, I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.nocturnal:
            lines.append(asp.fact("nocturnal", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for iid, item in SHARE_ITEMS.items():
        lines.append(asp.fact("share_item", iid))
        for a in sorted(item.allows):
            lines.append(asp.fact("helps", iid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    c = set(asp_valid_combos())
    p = set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def shared_ok(activity: Activity, item: ShareItem) -> bool:
    return activity.id in item.allows


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for item_id, item in SHARE_ITEMS.items():
                if shared_ok(act, item):
                    combos.append((place, act_id, item_id))
    return combos


def explain_rejection(activity: Activity, item: ShareItem) -> str:
    return (
        f"(No story: {item.label} does not sensibly support {activity.gerund}. "
        f"Choose a shared thing that actually helps with that night adventure.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def predict(world: World, hero: Entity, activity: Activity, item: Entity) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(hero.id), activity, narrate=False)
    return {
        "messy": any(v >= THRESHOLD for k, v in sim.get(item.id).meters.items() if k in {"dim", "scattered", "crumbled", "sandy"}),
        "joy": sum(e.memes.get("joy", 0.0) for e in sim.characters()),
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["excitement"] = actor.memes.get("excitement", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} began to {activity.verb}.")


def introduce(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'curious')} {hero.type} who loved "
        f"nighttime adventures."
    )
    world.say(
        f"{hero.id} and {friend.id} had {item.phrase}, and both of them wanted to use it."
    )


def arrive(world: World, hero: Entity, friend: Entity, setting: Setting, activity: Activity) -> None:
    world.say(
        f"One nocturnal evening, {hero.id} and {friend.id} stepped into {setting.place}."
    )
    world.say(
        f"The dark around them felt big, but the place was ready for {activity.gerund}."
    )


def want_and_worry(world: World, hero: Entity, friend: Entity, activity: Activity, item: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    friend.memes["worry"] = friend.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {friend.id} worried that "
        f"one shared thing would not be enough."
    )
    world.say(
        f'"If we hurry and do not share it," {friend.id} said, "we might lose our way."'
    )


def hoard(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1.0
    world.say(
        f"{hero.id} clutched {item.phrase} a little too tightly and started to run ahead."
    )
    world.say(
        f"{friend.id} slowed down, because the dark path felt less safe without a shared plan."
    )


def helper_arrives(world: World, helper: Entity, activity: Activity) -> None:
    world.say(helper.tells)
    world.say(
        f"That made {activity.gerund} feel like an adventure instead of a scramble."
    )


def share(world: World, hero: Entity, friend: Entity, item: Entity, activity: Activity) -> None:
    hero.memes["share"] = hero.memes.get("share", 0.0) + 1.0
    friend.memes["share"] = friend.memes.get("share", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    world.say(
        f"Then {hero.id} handed {item.it()} to {friend.id}, and they used it together."
    )
    world.say(
        f"The shared {item.label} {SHARE_ITEMS[item.id].boost}, and the path stopped feeling so large."
    )


def ending(world: World, hero: Entity, friend: Entity, activity: Activity, item: Entity) -> None:
    world.say(
        f"At the end of the nocturnal adventure, {hero.id} and {friend.id} were still close by, "
        f"still sharing, and still smiling."
    )
    world.say(
        f"They went home with {item.phrase}, and {hero.id} remembered that a small shared thing can make a dark night brave."
    )


def tell(setting: Setting, activity: Activity, item: ShareItem, hero_name: str, hero_type: str,
         friend_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"trait": trait}))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend"))
    shared = world.add(Entity(id=item.id, type="thing", label=item.label, phrase=item.phrase, plural=item.plural))

    introduce(world, hero, friend, shared)
    world.para()
    arrive(world, hero, friend, setting, activity)
    want_and_worry(world, hero, friend, activity, shared)
    hoard(world, hero, friend, shared)
    if activity.id in {"lantern_walk", "map_search"}:
        helper = world.add(Entity(id="helper", kind="character", type="firefly" if activity.id == "lantern_walk" else "older_sibling"))
        world.para()
        helper_arrives(world, helper, activity)
    world.para()
    share(world, hero, friend, shared, activity)
    do_activity(world, hero, activity)
    ending(world, hero, friend, activity, shared)
    world.facts = {
        "hero": hero,
        "friend": friend,
        "item": shared,
        "activity": activity,
        "setting": setting,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    item = f["item"]
    return [
        f'Write a short nocturnal adventure story for a young child about {hero.id} and {friend.id} sharing {item.phrase}.',
        f"Tell a gentle adventure where two children must share a {item.label} to safely {act.verb}.",
        f'Write a story that uses the word "nocturnal" and ends with friends sharing a small tool for a dark-night adventure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    item = f["item"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who went on the nocturnal adventure at {place}?",
            answer=f"{hero.id} and {friend.id} went together on a nighttime adventure at {place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label}?",
            answer=f"{hero.id} wanted to {act.verb}, and the {item.label} was the shared thing that made it possible.",
        ),
        QAItem(
            question=f"Why did the story turn from worry to happiness?",
            answer=f"It turned happy when {hero.id} stopped clutching the {item.label} alone and started sharing it with {friend.id}.",
        ),
        QAItem(
            question=f"What showed that the adventure ended well?",
            answer=f"At the end, {hero.id} and {friend.id} were still smiling and still sharing {item.phrase}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "nocturnal": [
        QAItem(
            question="What does nocturnal mean?",
            answer="Nocturnal means active at night or during the dark part of the day.",
        )
    ],
    "lantern": [
        QAItem(
            question="What does a lantern help people do at night?",
            answer="A lantern helps people see the way when it is dark.",
        )
    ],
    "map": [
        QAItem(
            question="What is a map for?",
            answer="A map helps people understand where to go and how to find places.",
        )
    ],
    "sharing": [
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing is helpful because one person does not have to do everything alone, and everyone can enjoy the same thing.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts["item"].id == "lantern":
        tags.add("lantern")
    if world.facts["item"].id == "map":
        tags.add("map")
    tags.add("nocturnal")
    tags.add("sharing")
    out: list[QAItem] = []
    for key in ["nocturnal", "lantern", "map", "sharing"]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters, resolution, generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nocturnal storyworld about sharing on a small adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--share-item", choices=SHARE_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.activity and args.share_item:
        if not shared_ok(ACTIVITIES[args.activity], SHARE_ITEMS[args.share_item]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], SHARE_ITEMS[args.share_item]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.share_item is None or c[2] == args.share_item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, share_item=item, name=name, gender=gender, friend_name=friend_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        SHARE_ITEMS[params.share_item],
        params.name,
        params.gender,
        params.friend_name,
        params.trait,
    )
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="camp", activity="lantern_walk", share_item="lantern", name="Mina", gender="girl", friend_name="Owen", trait="curious"),
    StoryParams(place="garden", activity="snack_search", share_item="snack", name="Theo", gender="boy", friend_name="Ruby", trait="gentle"),
    StoryParams(place="attic", activity="map_search", share_item="map", name="Lena", gender="girl", friend_name="Milo", trait="careful"),
    StoryParams(place="beach", activity="shell_search", share_item="blanket", name="Ezra", gender="boy", friend_name="Nina", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible story combos:\n")
        for place, act, item in combos:
            print(f"  {place:10} {act:14} {item}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (share: {p.share_item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
