#!/usr/bin/env python3
"""
storyworlds/worlds/intellectual_condense_peek_quest_ghost_story.py
==================================================================

A small standalone storyworld about a gentle ghost, an intellectual quest,
and a careful compromise.

Seed tale premise:
- A thoughtful little ghost loves a Quest.
- The ghost wants to peek into a misty old place to find a clue.
- A grown-up ghost worries the clue will condense with damp and spoil.
- They choose a safer way, and the Quest still goes on.

This world keeps the prose child-facing, concrete, and state-driven.
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
        if not self.meters:
            self.meters = {"wet": 0.0, "dusty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "desire": 0.0, "worry": 0.0, "curiosity": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "ghostgirl"}
        male = {"boy", "father", "dad", "man", "ghostboy"}
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
    place: str
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
    weather: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if actor.meters.get("wet", 0.0) < THRESHOLD and actor.meters.get("dusty", 0.0) < THRESHOLD:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if actor.meters.get("wet", 0.0) >= THRESHOLD:
                item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            if actor.meters.get("dusty", 0.0) >= THRESHOLD:
                item.meters["dusty"] = item.meters.get("dusty", 0.0) + 1
            out.append(f"{actor.id}'s {item.label_word} got damp and dusty.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("wet", 0.0) + item.meters.get("dusty", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That gave {carer.label_word} more worry.")
    return out


CAUSAL_RULES = [
    ("soak", _r_soak),
    ("worry", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _name, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and (prize.meters.get("wet", 0.0) >= THRESHOLD or prize.meters.get("dusty", 0.0) >= THRESHOLD)),
        "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Milo", hero_type: str = "ghostboy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "ghostmother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        label=hero_name, traits=["little", "intellectual"] + (hero_traits or ["quiet", "curious"]),
    ))
    parent = world.add(Entity(id="Guide", kind="character", type=parent_type, label="the grown-up ghost"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    hero.memes["desire"] += 1
    hero.memes["curiosity"] += 1

    world.say(f"{hero.id} was a little intellectual ghost who loved every quiet Quest.")
    world.say(f"{hero.id} kept {hero.pronoun('possessive')} {prize.label} close, because a Quest felt better with a trusty clue-book.")
    world.say(f"Together with {parent.label_word}, {hero.id} planned a moonlit Quest.")

    world.para()
    world.say(f"One foggy night, {hero.id} went to the old {setting.place} and wanted to {activity.verb}.")
    world.say(f"{hero.pronoun().capitalize()} hoped to {activity.keyword} the way a clever ghost might study a mystery.")
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        hero.memes["worry"] += 0.5

    if pred["soiled"]:
        world.say(f'"If you do that, your {prize.label} will {activity.soil}," {parent.label_word} whispered.')
        world.say(f"{hero.id} still wanted to peek, but {hero.pronoun('possessive')} wish for the Quest was strong.")
        hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 1
        hero.memes["conflict"] += 1
        world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}, and the fog began to condense on the {prize.label}.")
        hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 0  # keep state simple
        gear_def = select_gear(activity, prize)
        if not gear_def:
            raise StoryError("(No story: no safe ghostly gear fits this Quest.)")
        gear = world.add(Entity(
            id=gear_def.id, type="gear", label=gear_def.label,
            owner=hero.id, caretaker=parent.id, protective=True,
            covers=set(gear_def.covers), plural=gear_def.plural,
        ))
        gear.worn_by = hero.id
        if predict_mess(world, hero, activity, prize.id)["soiled"]:
            gear.worn_by = None
            del world.entities[gear.id]
            raise StoryError("(No story: the chosen gear does not actually keep the prize safe.)")
        world.para()
        world.say(f'{parent.label_word} smiled and said, "{gear_def.prep}, and then you can {activity.verb} safely."')
        world.say(f"{hero.id}'s face glowed like a lantern. {hero.id} agreed at once.")
        hero.memes["joy"] += 1
        hero.memes["love"] = hero.memes.get("love", 0.0) + 1
        hero.memes["conflict"] = 0.0
        world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, and the {prize.label} stayed dry and tidy.")
    else:
        world.say(f"{parent.label_word} watched closely, but the little Quest stayed safe.")
        world.say(f"{hero.id} got to {activity.verb} without any trouble.")

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=world.entities.get("gear") if "gear" in world.entities else None,
                       resolved="gear" in world.entities)
    return world


# fix copy method after class definition
def _world_copy(self: World) -> World:
    import copy
    clone = World(self.setting)
    clone.entities = copy.deepcopy(self.entities)
    clone.fired = set(self.fired)
    clone.zone = set(self.zone)
    clone.weather = self.weather
    clone.paragraphs = [[]]
    clone.facts = dict(self.facts)
    return clone


World.copy = _world_copy  # type: ignore[attr-defined]


SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, affords={"peek"}),
    "library": Setting(place="the old library", indoor=True, affords={"peek"}),
    "garden": Setting(place="the moonlit garden", indoor=False, affords={"peek"}),
}

ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="peek into the mist",
        gerund="peeking through the mist",
        rush="glide toward the shadowy corner",
        mess="wet",
        soil="turn damp and blurry",
        zone={"torso"},
        weather="foggy",
        keyword="peek",
        tags={"ghost", "mystery", "quest"},
    ),
    "condense": Activity(
        id="condense",
        verb="condense the fog into beads",
        gerund="condensing the fog into tiny beads",
        rush="gather the fog with a swirl",
        mess="wet",
        soil="turn damp and blurry",
        zone={"torso"},
        weather="foggy",
        keyword="condense",
        tags={"ghost", "mystery", "quest"},
    ),
}

GEAR = [
    Gear(
        id="lantern_case",
        label="a lantern case",
        covers={"torso"},
        guards={"wet"},
        prep="put the quest map inside a lantern case first",
        tail="walked on with the quest map tucked safely away",
    ),
    Gear(
        id="wax_pouch",
        label="a wax pouch",
        covers={"torso"},
        guards={"wet"},
        prep="slip the quest note into a wax pouch first",
        tail="glided on with the quest note safe and dry",
    ),
]

PRIZES = {
    "map": Prize(label="quest map", phrase="a folded quest map", type="map", region="torso"),
    "note": Prize(label="quest note", phrase="a little quest note", type="note", region="torso"),
}

GHOST_NAMES = ["Milo", "Nia", "Pip", "Luna", "Ollie", "Bea"]
TRAITS = ["quiet", "careful", "brave"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ghost": [("What is a ghost?", "A ghost is a made-up spooky character in stories. In gentle stories, ghosts can be kind and helpful.")],
    "mystery": [("What is a mystery?", "A mystery is something you do not know yet, so you look for clues to understand it.")],
    "quest": [("What is a quest?", "A quest is a trip or job where you go looking for something important.")],
    "wet": [("What does wet mean?", "Wet means covered with water or dampness.")],
}

KNOWLEDGE_ORDER = ["ghost", "mystery", "quest", "wet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a little child about an intellectual {f["hero"].type} on a Quest.',
        f'Write a gentle story that uses the words "peek" and "condense" and ends with a safe Quest.',
        f'Tell a child-friendly ghost story where {f["hero"].id} wants to {f["activity"].verb} but {f["parent"].label_word} helps keep the {f["prize"].label} dry.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little intellectual ghost who loved a Quest.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the old place?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.pronoun().capitalize()} was curious and ready to peek at the mystery.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about the {prize.label}?",
            answer=f"{parent.label_word} worried because the fog could condense on the {prize.label} and make it damp.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {f['gear'].label} so {hero.id} could keep going on the Quest while the {prize.label} stayed safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story quest world: intellectual, peek, condense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(p, a, pr) for p in SETTINGS for a in SETTINGS[p].affords for pr in PRIZES if prize_at_risk(ACTIVITIES[a], PRIZES[pr]) and select_gear(ACTIVITIES[a], PRIZES[pr])]
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid ghost story matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GHOST_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
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
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set((p, a, pr) for p in SETTINGS for a in SETTINGS[p].affords for pr in PRIZES if prize_at_risk(ACTIVITIES[a], PRIZES[pr]) and select_gear(ACTIVITIES[a], PRIZES[pr]))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid combos ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="attic", activity="peek", prize="map", name="Milo", gender="boy", parent="mother", trait="intellectual"),
    StoryParams(place="library", activity="peek", prize="note", name="Luna", gender="girl", parent="father", trait="quiet"),
    StoryParams(place="garden", activity="condense", prize="map", name="Pip", gender="boy", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for c in combos:
            print("  ", c)
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
