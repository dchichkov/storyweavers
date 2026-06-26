#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/disgust_bushel_best_twist_conflict_space_adventure.py
==============================================================================================================

A tiny space-adventure story world built from the seed words:
disgust, bushel, best.

Premise:
A crew on a small starship finds a bushel-sized cargo bundle that is
supposed to be the best part of their supply run. The bundle looks and smells
disgusting, so the captain and the scout disagree about what to do with it.
The twist is that the disgusting bundle hides something useful and kind.

World shape:
- concrete physical state: cargo, slime, filter seals, hull bay, supplies
- emotional state: joy, disgust, conflict, trust, relief
- causal turn: a questionable-looking bushel triggers disgust and conflict
- resolution: a careful cleaning / opening reveals the best value in the bundle

The story stays small, authored, and child-facing, but the underlying state
drives the prose and Q&A.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "scout"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy as _copy

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        return c


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _bump_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = _meter(ent, key) + amount


def _bump_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = _meme(ent, key) + amount


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if _meter(actor, "disgust") >= THRESHOLD:
                for item in world.entities.values():
                    if item.kind != "thing" or item.carried_by != actor.id:
                        continue
                    sig = ("dirty_item", actor.id, item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    _bump_meter(item, "grime", 1)
                    out.append(f"{actor.pronoun('possessive').capitalize()} cargo picked up a nasty grime.")
            if _meme(actor, "conflict") >= THRESHOLD and _meme(actor, "trust") < THRESHOLD:
                sig = ("tense", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append(f"The cabin felt tense.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def _risk(activity: Activity, prize: Prize) -> bool:
    return prize.label == "bushel" and activity.id == "open"


def _fix(activity: Activity, prize: Prize) -> bool:
    return _risk(activity, prize)


def _foresee(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": _meter(prize, "grime") >= THRESHOLD, "disgust": _meme(actor, "disgust")}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This setting cannot host that space action.")
    actor.meters[activity.mess] = _meter(actor, activity.mess) + 1
    _bump_meme(actor, "disgust", 1)
    _bump_meme(actor, "curiosity", 1)
    if narrate:
        world.say(f"{actor.id} did the thing, and the air felt strange.")
    _propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved looking out the window at the stars."
    )


def love_best(world: World, hero: Entity, prize: Entity) -> None:
    _bump_meme(hero, "love", 1)
    world.say(
        f"{hero.id} thought {hero.pronoun('possessive')} {prize.label} was the best thing on the ship."
    )


def arrive(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    world.say(
        f"One day, {hero.id} and {friend.id} went to {world.setting.place}. {world.setting.detail}"
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {activity.gerund} felt like an adventure."
    )


def warn(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = _foresee(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    _bump_meme(captain, "worry", 1)
    world.say(
        f"'{prize.label.capitalize()} will get disgusting,' {captain.id} said. "
        f"'Let's not rush.'"
    )
    return True


def conflict_beats(world: World, hero: Entity, captain: Entity, activity: Activity) -> None:
    _bump_meme(hero, "conflict", 1)
    _bump_meme(captain, "conflict", 1)
    world.say(
        f"{hero.id} still tried to {activity.rush}, but {captain.id} put up a gentle hand."
    )
    world.say(
        f"That made {hero.id} frown, because {hero.pronoun()} wanted the fun now."
    )


def twist(world: World, hero: Entity, prize: Entity) -> None:
    _bump_meme(hero, "curiosity", 1)
    world.say(
        f"Then came the twist: the nasty-looking {prize.label} was hiding a tiny silver key inside."
    )


def resolve(world: World, captain: Entity, hero: Entity, prize: Entity, gear: Gear) -> None:
    _bump_meme(hero, "joy", 1)
    _bump_meme(hero, "trust", 1)
    hero.memes["conflict"] = 0
    world.say(
        f"{captain.id} used {gear.label} first, and {hero.id} listened."
    )
    world.say(
        f"They {gear.tail}. Under the grime, the {prize.label} turned out to be the best surprise of the trip."
    )
    world.say(
        f"{hero.id} grinned at the little key, and the ship felt bright again."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         name: str = "Mina", hero_type: str = "girl", parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=hero_type, role="hero"))
    captain = world.add(Entity(id="Captain", kind="character", type=parent_type, role="captain"))
    friend = world.add(Entity(id="Twist", kind="character", type="scout", role="friend"))
    prize = world.add(Entity(
        id="bushel",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=captain.id,
    ))
    gear = world.add(Entity(
        id="filter",
        kind="thing",
        type="tool",
        label="a clean filter mask",
        protective=True,
    ))
    prize.carried_by = hero.id
    world.facts.update(hero=hero, captain=captain, friend=friend, prize=prize, activity=activity, gear=gear)

    introduce(world, hero)
    love_best(world, hero, prize)
    world.para()
    arrive(world, hero, friend, activity)
    warn(world, captain, hero, activity, prize)
    conflict_beats(world, hero, captain, activity)
    world.para()
    twist(world, hero, prize)
    resolve(world, captain, hero, prize, Gear(
        id="filter",
        label="a clean filter mask",
        guards={"smell"},
        prep="put on the filter mask",
        tail="opened the bushel slowly",
    ))
    return world


SETTINGS = {
    "cargo_bay": Setting(
        place="the cargo bay",
        detail="The metal floor shone, and a long row of supply crates waited by the wall.",
        affords={"open", "carry"},
    ),
    "moon_dock": Setting(
        place="the moon dock",
        detail="The dock lights blinked blue, and the low gravity made every bag float a little.",
        affords={"open", "carry"},
    ),
    "greenhouse": Setting(
        place="the ship greenhouse",
        detail="Soft lamps glowed over the plants, and the air smelled warm and green.",
        affords={"open", "carry"},
    ),
}

ACTIVITIES = {
    "open": Activity(
        id="open",
        verb="open the bushel",
        gerund="opening the bushel",
        rush="pull open the lid",
        mess="disgust",
        soil="smelled awful",
        keyword="bushel",
        tags={"bushel", "disgust"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry the bushel",
        gerund="carrying the bushel",
        rush="haul the bushel fast",
        mess="disgust",
        soil="smelled awful",
        keyword="bushel",
        tags={"bushel", "disgust"},
    ),
}

PRIZES = {
    "bushel": Prize(
        label="bushel",
        phrase="a bushel of best moon berries",
        type="container",
        plural=False,
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nia", "Rin", "Tara", "Jessa"]
BOY_NAMES = ["Pax", "Oren", "Milo", "Finn", "Koa", "Theo"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="cargo_bay", activity="open", prize="bushel", name="Mina", gender="girl", parent="captain"),
    StoryParams(place="moon_dock", activity="carry", prize="bushel", name="Pax", gender="boy", parent="captain"),
    StoryParams(place="greenhouse", activity="open", prize="bushel", name="Luna", gender="girl", parent="captain"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, pr) for p in SETTINGS for a in SETTINGS[p].affords for pr in PRIZES]


KNOWLEDGE = {
    "bushel": [(
        "What is a bushel?",
        "A bushel is a big basket or container used to hold a lot of things, like fruit."
    )],
    "disgust": [(
        "What does disgust mean?",
        "Disgust is the feeling you get when something seems very gross or yucky."
    )],
    "best": [(
        "What does best mean?",
        "Best means the one you like most, or the one that is strongest, nicest, or most helpful."
    )],
    "twist": [(
        "What is a twist in a story?",
        "A twist is a surprise turn that changes what you thought was going to happen."
    )],
    "conflict": [(
        "What is conflict in a story?",
        "Conflict is a problem or disagreement that makes the characters push against each other before they solve it."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        f'Write a short space-adventure story for a child about {hero.id}, a {activity.keyword}, and a disgusting {prize.label}.',
        f"Tell a gentle story where {hero.id} thinks the {prize.label} is the best thing on the ship, but a captain worries about the smell.",
        f'Write a story that includes the words "disgust", "bushel", and "best", and ends with a surprising twist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    prize = f["prize"]
    activity = f["activity"]
    qa = [
        QAItem(
            question=f"Why did {hero.id} want to {activity.verb} in the first place?",
            answer=f"{hero.id} wanted to {activity.verb} because {hero.pronoun('possessive')} {prize.label} was the best thing on the ship, and {hero.id} was curious about it.",
        ),
        QAItem(
            question=f"What worried {captain.id} about the {prize.label}?",
            answer=f"{captain.id} worried that the {prize.label} would smell disgusting if they opened it too fast.",
        ),
        QAItem(
            question=f"What happened after the twist?",
            answer=f"After the twist, they found a tiny silver key inside the {prize.label}, so the yucky-looking bundle turned out to be useful.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended with {hero.id} smiling at the little key and feeling happy that the best surprise was hidden inside the disgusting bushel.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("best")
    out: list[QAItem] = []
    for tag in ["bushel", "disgust", "best", "twist", "conflict"]:
        if tag in tags or tag in {"best", "twist", "conflict"}:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,P) :- activity(A), prize(P), mess(A,M), prize_mess(P,M).
fix(A,P) :- risk(A,P), gear(G), guards(G,M), mess(A,M).
valid(Place,A,P) :- setting(Place), affords(Place,A), risk(A,P), fix(A,P).
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
        lines.append(asp.fact("mess", aid, a.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_mess", pid, "disgust"))
    lines.append(asp.fact("gear", "filter"))
    lines.append(asp.fact("guards", "filter", "disgust"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def explain_rejection() -> str:
    return "(No story: this space action has no reasonable, problem-solving twist.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with disgust, bushel, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "captain"
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
