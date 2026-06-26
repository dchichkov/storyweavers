#!/usr/bin/env python3
"""
storyworlds/worlds/leisure_teamwork_kindness_nursery_rhyme.py
=============================================================

A small story world about leisure, teamwork, and kindness, written in a
nursery-rhyme-like tone.

The premise is simple:
- friends have free time in a gentle place,
- they want to enjoy a leisure activity,
- something small goes wrong or gets stuck,
- kindness and teamwork turn the day sweet again.

The world model tracks physical state with meters and emotional state with memes.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Leisure:
    id: str
    verb: str
    gerund: str
    delight: str
    snag: str
    fix: str
    requires: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedThing:
    label: str
    phrase: str
    kind: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Aid:
    id: str
    label: str
    helps: set[str]
    cover: set[str]
    prep: str
    ending: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.facts = dict(self.facts)
        clone.zone = self.zone
        return clone


@dataclass
class StoryParams:
    place: str
    leisure: str
    object: str
    name: str
    gender: str
    friend: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting("the garden", False, {"kite", "picnic", "puzzle"}),
    "playroom": Setting("the playroom", True, {"blocks", "puzzle", "story"}),
    "meadow": Setting("the meadow", False, {"kite", "picnic"}),
    "porch": Setting("the porch", False, {"storybook", "puzzle", "music"}),
}

LEISURES = {
    "kite": Leisure(
        id="kite",
        verb="fly the kite",
        gerund="flying the kite",
        delight="the ribbon danced like a bright little snake",
        snag="the string got knotted in a twist",
        fix="the knot came loose",
        requires="string",
        tags={"wind", "kite", "share"},
    ),
    "picnic": Leisure(
        id="picnic",
        verb="have a picnic",
        gerund="sharing a picnic",
        delight="the blankets and berries made a merry feast",
        snag="the crumb basket tipped on its side",
        fix="the treats were gathered again",
        requires="basket",
        tags={"food", "share", "blanket"},
    ),
    "puzzle": Leisure(
        id="puzzle",
        verb="finish the puzzle",
        gerund="working on the puzzle",
        delight="the picture looked like a tiny window to a fairytale",
        snag="a few pieces hid under the table",
        fix="the last pieces slipped into place",
        requires="pieces",
        tags={"pieces", "share", "think"},
    ),
    "blocks": Leisure(
        id="blocks",
        verb="build a tower with blocks",
        gerund="stacking blocks",
        delight="the tower rose higher and higher like a small castle",
        snag="one block wobbled and tumbled down",
        fix="the tower stood firm again",
        requires="hands",
        tags={"blocks", "share", "build"},
    ),
    "story": Leisure(
        id="story",
        verb="read a storybook",
        gerund="reading a storybook",
        delight="the pages sounded soft as feathers",
        snag="the book was too big for one lap alone",
        fix="two laps made one cozy reading spot",
        requires="pages",
        tags={"book", "share", "quiet"},
    ),
    "music": Leisure(
        id="music",
        verb="play the little drum",
        gerund="making music",
        delight="the beat went tap-tap like happy rain",
        snag="the drumstick rolled away",
        fix="the beat found its way back",
        requires="drumstick",
        tags={"music", "share", "sound"},
    ),
}

OBJECTS = {
    "kite": SharedThing("kite", "a red kite with a gold tail", "kite"),
    "picnic": SharedThing("picnic basket", "a picnic basket full of apples and bread", "basket"),
    "puzzle": SharedThing("puzzle", "a bright picture puzzle", "puzzle"),
    "blocks": SharedThing("blocks", "a stack of wooden blocks", "blocks", plural=True),
    "story": SharedThing("storybook", "a big, gentle storybook", "book"),
    "music": SharedThing("drum", "a little hand drum", "drum"),
}

AIDS = [
    Aid("scissors", "small scissors", {"kite", "picnic"}, {"string", "paper"}, "use small scissors to free the knot", "went to get the small scissors"),
    Aid("basket", "a sturdy basket", {"picnic"}, {"basket"}, "bring a sturdy basket with both hands", "came back with the sturdy basket", True),
    Aid("lamp", "a tiny lamp", {"puzzle", "story"}, {"pages", "pieces"}, "set a tiny lamp beside the table", "brought back the tiny lamp"),
    Aid("hands", "two careful hands", {"blocks", "music"}, {"hands", "pieces", "drumstick"}, "use two careful hands together", "held up their careful hands", True),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for leisure_id in setting.affords:
            for obj_id in OBJECTS:
                if leisure_id == obj_id:
                    combos.append((place, leisure_id, obj_id))
    return combos


def _do_activity(world: World, actor: Entity, leisure: Leisure, narrate: bool = True) -> None:
    actor.meters[leisure.id] = actor.meters.get(leisure.id, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    world.zone = leisure.requires
    if narrate:
        world.say(f"{actor.id} was busy {leisure.gerund}.")


def _snag(world: World, actor: Entity, leisure: Leisure, obj: Entity) -> None:
    key = ("snag", actor.id, leisure.id)
    if key in world.fired:
        return
    world.fired.add(key)
    actor.memes["trouble"] = actor.memes.get("trouble", 0) + 1
    obj.meters["stuck"] = obj.meters.get("stuck", 0) + 1


def _kindness(world: World, helper: Entity, actor: Entity) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    actor.memes["warmth"] = actor.memes.get("warmth", 0) + 1


def predict(world: World, actor: Entity, leisure: Leisure, obj: Entity) -> dict:
    sim = world.copy()
    sim_actor = sim.get(actor.id)
    sim_obj = sim.get(obj.id)
    _do_activity(sim, sim_actor, leisure, narrate=False)
    _snag(sim, sim_actor, leisure, sim_obj)
    return {
        "stuck": sim_obj.meters.get("stuck", 0) >= THRESHOLD,
    }


def select_aid(leisure: Leisure, obj: Entity) -> Optional[Aid]:
    for aid in AIDS:
        if leisure.id in aid.helps and obj.kind in aid.cover:
            return aid
    return None


def choose_name(gender: str, rng: random.Random) -> str:
    girls = ["Mina", "Luna", "Ivy", "Nina", "Pia", "Rose"]
    boys = ["Ollie", "Finn", "Milo", "Theo", "Noah", "Ezra"]
    return rng.choice(girls if gender == "girl" else boys)


def tell(setting: Setting, leisure: Leisure, obj_cfg: SharedThing,
         hero_name: str, gender: str, friend_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_type, label="the friend"))
    obj = world.add(Entity(
        id=obj_cfg.label.replace(" ", "_"),
        type=obj_cfg.kind,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        plural=obj_cfg.plural,
        owner=hero.id,
    ))

    hero.memes["wish"] = 1
    friend.memes["care"] = 1

    world.say(f"{hero.id} was a little {gender} with a heart for leisure and play.")
    world.say(f"{hero.pronoun().capitalize()} loved {leisure.gerund}, and {leisure.delight}.")
    world.say(f"One day, {friend.label} brought {hero.pronoun('object')} {obj.phrase}.")
    world.say(f"{hero.id} smiled, for {hero.pronoun('possessive')} {obj.label} was a treasure for free time.")

    world.para()
    world.say(f"At {setting.place}, the air was mild and sweet.")
    world.say(f"{hero.id} wanted to {leisure.verb}, and {friend.label} came along to help.")
    _do_activity(world, hero, leisure)

    if predict(world, hero, leisure, obj)["stuck"]:
        world.say(f"But oh my, {leisure.snag}.")
        _snag(world, hero, leisure, obj)
        world.say(f"{hero.id} looked worried, and {friend.label} looked kind.")
        _kindness(world, friend, hero)

    world.para()
    aid = select_aid(leisure, obj)
    if aid is None:
        raise StoryError("No kind teamwork aid fits this leisure and object pairing.")
    world.say(f"Then {friend.label} said, \"Let's help together,\" and {hero.id} nodded nice and slow.")
    world.say(f"They decided to {aid.prep}.")
    world.say(f"Together, they worked with care, and {leisure.fix}.")
    _kindness(world, hero, friend)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1

    if leisure.id == "story":
        world.say(f"The storybook rested on both laps, and the pages sounded soft and glad.")
    elif leisure.id == "kite":
        world.say(f"The kite rose up again, and its tail waved like a ribbon in a nursery rhyme.")
    elif leisure.id == "picnic":
        world.say(f"The basket sat steady, and the apples stayed snug and round.")
    elif leisure.id == "puzzle":
        world.say(f"The last piece clicked home, and the picture smiled from the table.")
    elif leisure.id == "blocks":
        world.say(f"The tower stood tall and tidy, because two careful sets of hands had helped.")
    elif leisure.id == "music":
        world.say(f"The drum went tap-tap once more, and the little song came back to dance.")

    world.say(f"{hero.id} and {friend.label} finished in peace, with kind hearts and happy feet.")
    world.facts.update(hero=hero, friend=friend, obj=obj, leisure=leisure, aid=aid, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    leisure = f["leisure"]
    obj = f["obj"]
    setting = f["setting"]
    return [
        f'Write a nursery-rhyme-like story about {hero.id} at {setting.place} where the theme is "leisure".',
        f"Tell a gentle story where friends use teamwork and kindness to help with {obj.phrase} while {hero.id} is {leisure.gerund}.",
        f'Write a short, child-friendly tale about {leisure.verb} that ends with everyone working together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    leisure = f["leisure"]
    obj = f["obj"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} spend the quiet leisure day?",
            answer=f"{hero.id} spent the day at {setting.place}, where there was room for gentle play.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the problem happened?",
            answer=f"{hero.id} wanted to {leisure.verb}, and that was the fun thing on the mind.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when things got tricky?",
            answer=f"{friend.label} helped with kindness, and the two of them worked together.",
        ),
        QAItem(
            question=f"What made the play moment hard for {hero.id}?",
            answer=f"{leisure.snag.capitalize()}. That small snag was enough to slow the fun for a moment.",
        ),
        QAItem(
            question=f"How did the children fix the trouble?",
            answer=f"They used teamwork and kindness to {leisure.fix.lower()}, so the day could stay sweet.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "kite": [("What does a kite do?", "A kite flies in the air when the wind lifts it.")],
    "picnic": [("What is a picnic?", "A picnic is a meal or snack eaten outdoors on a blanket or table.")],
    "puzzle": [("What is a puzzle?", "A puzzle is a game where pieces fit together to make a picture.")],
    "blocks": [("What are blocks for?", "Blocks are toys you can stack and build with.")],
    "story": [("What is a storybook?", "A storybook is a book filled with tales and pictures.")],
    "music": [("What is a drum?", "A drum is a music toy you tap to make a beat.")],
    "share": [("What does it mean to share?", "To share means to let someone else use or enjoy something with you.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and thoughtful to others.")],
    "teamwork": [("What is teamwork?", "Teamwork means people work together to do something.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["leisure"].tags)
    tags.add("share")
    tags.add("kindness")
    tags.add("teamwork")
    out: list[QAItem] = []
    for tag, pairs in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "kite", "kite", "Mina", "girl", "boy"),
    StoryParams("playroom", "puzzle", "puzzle", "Ollie", "boy", "girl"),
    StoryParams("meadow", "picnic", "picnic", "Luna", "girl", "boy"),
    StoryParams("porch", "story", "story", "Finn", "boy", "girl"),
    StoryParams("playroom", "blocks", "blocks", "Rose", "girl", "boy"),
]


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for leisure_id in setting.affords:
            combos.append((place, leisure_id, leisure_id, "girl"))
            combos.append((place, leisure_id, leisure_id, "boy"))
    return combos


def explain_rejection(place: str, leisure: str, obj: str) -> str:
    return f"(No story: {place} does not fit {leisure} with {obj} in this small nursery-rhyme world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme leisure stories about teamwork and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--leisure", choices=LEISURES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = valid_story_combos()
    if args.place and args.leisure and args.object:
        if (args.place, args.leisure, args.object, args.gender or "girl") not in combos:
            raise StoryError(explain_rejection(args.place, args.leisure, args.object))
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.leisure is None or c[1] == args.leisure)
                and (args.object is None or c[2] == args.object)
                and (args.gender is None or c[3] == args.gender)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, leisure, obj, gender = rng.choice(filtered)
    name = args.name or choose_name(gender, rng)
    friend = args.friend or rng.choice(["girl", "boy"])
    return StoryParams(place=place, leisure=leisure, object=obj, name=name, gender=gender, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], LEISURES[params.leisure], OBJECTS[params.object],
                 params.name, params.gender, params.friend)
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
place(garden;playroom;meadow;porch).
leisure(kite;puzzle;picnic;blocks;story;music).
object(kite;puzzle;picnic;blocks;story;music).

affords(garden,kite). affords(garden,picnic). affords(garden,puzzle).
affords(playroom,puzzle). affords(playroom,blocks). affords(playroom,story).
affords(meadow,kite). affords(meadow,picnic).
affords(porch,story). affords(porch,puzzle). affords(porch,music).

valid(P,L,O) :- affords(P,L), object(O), O = L.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        if s.indoor:
            lines.append(asp.fact("indoor", p))
        for l in sorted(s.affords):
            lines.append(asp.fact("affords", p, l))
    for l in LEISURES:
        lines.append(asp.fact("leisure", l))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(valid_story_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_story_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.leisure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
