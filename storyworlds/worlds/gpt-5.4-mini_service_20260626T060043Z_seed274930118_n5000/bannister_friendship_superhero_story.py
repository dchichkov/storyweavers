#!/usr/bin/env python3
"""
Standalone storyworld: a small superhero friendship story around a bannister.

This world models a child superhero, a best friend, and a risky bit of play
near a bannister. The tension comes from wanting to use the bannister for a
superhero-style slide while protecting a prized item; the resolution is a
friendship-based compromise that keeps the adventure safe.
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["scratched", "scuffed", "dirty", "workload"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "love", "worry", "bravery", "conflict", "trust", "friendship", "desire"]:
            self.memes.setdefault(key, 0.0)

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

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the apartment stairwell"
    indoor: bool = True
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["scratched"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("scrape", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scratched"] += 1
            item.meters["scuffed"] += 1
            out.append(f"{actor.id}'s {item.label} got scratched and scuffed.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["scuffed"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        carer.meters["workload"] += 1
        out.append(f"That would make {carer.label_word} worry and clean up later.")
    return out


CAUSAL_RULES = [
    _r_scrape,
    _r_worry,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = copy_world(world)
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["scuffed"] >= THRESHOLD}


def copy_world(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.zone = set(world.zone)
    clone.fired = set(world.fired)
    return clone


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["bravery"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a little superhero who liked brave ideas, and {friend.id} was the best friend who never laughed when the plan got tricky."
    )


def loves_friendship(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"They loved being a team, because friendship made even an ordinary hallway feel like a mission."
    )


def discovery(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One afternoon, {hero.id} looked at the shiny {prize.label} and smiled at the big bannister by the stairs."
    )


def wants(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} like a real hero, but {hero.pronoun('possessive')} {prize.label} was special."
    )


def warn(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you go near the bannister now, your {prize.label} will get {activity.soil}," {friend.pronoun("possessive")} best friend said.'
    )
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] += 1
    world.say(
        f"{hero.id} still wanted to try, and {hero.pronoun()} moved closer to the bannister."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tried to {activity.rush}, just a little too fast."
    )


def friendship_tug(world: World, friend: Entity, hero: Entity) -> None:
    hero.memes["trust"] += 1
    friend.memes["love"] += 1
    world.say(
        f"Then {friend.id} held out a hand and said, 'We can do this together, the safe way.'"
    )


def compromise(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=friend.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict(world, hero, activity, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(
        f"{friend.id} found {gear_def.label} and helped {hero.id} put {gear_def.label} on before the bannister slide."
    )
    return gear_def


def accept(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id}'s face lit up, because {hero.id} and {friend.id} were still a team."
    )
    world.say(
        f"With {gear_def.label} on, {hero.id} could {activity.verb}, and {prize.label} stayed clean."
    )
    world.say(
        f"At the end, the two friends laughed beside the bannister, proud of their safe superhero plan."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nova", friend_name: str = "Pip",
         hero_type: str = "girl", friend_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "brave", "kind"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["best friend", "clever", "kind"]))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=friend.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    prize.worn_by = hero.id

    introduce(world, hero, friend)
    loves_friendship(world, hero, friend)
    discovery(world, hero, prize)
    wants(world, hero, activity, prize)

    world.para()
    warn(world, friend, hero, activity, prize)
    defy(world, hero, activity)
    friendship_tug(world, friend, hero)

    world.para()
    gear_def = compromise(world, friend, hero, activity, prize)
    if gear_def:
        accept(world, hero, friend, activity, prize, gear_def)

    world.facts.update(hero=hero, friend=friend, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "stairwell": Setting(place="the apartment stairwell", indoor=True, affords={"bannister_slide"}),
}

ACTIVITIES = {
    "bannister_slide": Activity(
        id="bannister_slide",
        verb="slide down the bannister",
        gerund="sliding down the bannister",
        rush="zoom down the bannister",
        mess="scratched",
        soil="scratched up",
        zone={"hands", "torso"},
        keyword="bannister",
        tags={"bannister", "friendship", "superhero"},
    ),
}

PRIZES = {
    "gloves": Prize(
        label="gloves",
        phrase="a pair of bright superhero gloves",
        type="gloves",
        region="hands",
        plural=True,
    ),
    "cape": Prize(
        label="cape",
        phrase="a red superhero cape",
        type="cape",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="gripgloves",
        label="grip gloves",
        covers={"hands"},
        guards={"scratched"},
        prep="put on the grip gloves",
        tail="slid carefully",
        plural=True,
    ),
    Gear(
        id="armguards",
        label="arm guards",
        covers={"hands", "torso"},
        guards={"scratched"},
        prep="wear the arm guards first",
        tail="went down the bannister carefully",
        plural=True,
    ),
]

HERO_NAMES = ["Nova", "Mina", "Zee", "Ivy", "Rae", "Tia"]
FRIEND_NAMES = ["Pip", "Bo", "Sam", "Jax", "Noor", "Ellis"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    friend_name: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    prize = f["prize"]
    hero = f["hero"]
    return [
        f'Write a short superhero story about friendship that includes a bannister and the word "{act.keyword}".',
        f"Tell a gentle adventure where {hero.id} and {f['friend'].id} solve a bannister problem without ruining {prize.label}.",
        f"Write a kid-friendly story about two friends making a safe plan for {act.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prize = f["prize"]
    act = f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {hero.id} and {friend.id}, who cared about each other and worked as a team.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do near the bannister?",
            answer=f"{hero.id} wanted to {act.verb} like a superhero.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the {prize.label}?",
            answer=f"{friend.id} worried because {prize.label} could get {act.soil} if {hero.id} tried to {act.verb} without a safer plan.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the friends make the bannister plan safe?",
                answer=f"They used {gear.label} so {hero.id} could {act.verb} while {prize.label} stayed clean.",
            )
        )
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a bannister?",
        answer="A bannister is the rail beside stairs that people hold onto when they go up or down.",
    ),
    QAItem(
        question="What is friendship?",
        answer="Friendship is when people care about each other, help each other, and enjoy being together.",
    ),
    QAItem(
        question="Why do superheroes wear special gear?",
        answer="Superheroes wear special gear to stay safe, protect themselves, or help them do their job better.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A prize is at risk if the activity affects the region it is worn on.
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).

% A gear item is a valid fix if it guards the mess and covers the risk region.
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).

has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero friendship storyworld with a bannister.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    prize_cfg = PRIZES[prize]
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, hero_name=hero_name,
                       friend_name=friend_name, hero_type=hero_type, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.hero_name, params.friend_name, params.hero_type, params.friend_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combinations:\n")
        for place, act, prize in triples:
            print(f"  {place:12} {act:16} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams("stairwell", "bannister_slide", "gloves", "Nova", "Pip", "girl", "boy")),
            generate(StoryParams("stairwell", "bannister_slide", "cape", "Mina", "Jax", "girl", "boy")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
