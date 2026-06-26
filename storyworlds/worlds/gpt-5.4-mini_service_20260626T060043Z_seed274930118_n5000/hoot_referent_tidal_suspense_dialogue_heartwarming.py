#!/usr/bin/env python3
"""
storyworlds/worlds/hoot_referent_tidal_suspense_dialogue_heartwarming.py
=========================================================================

A small heartwarming story world about a child, a caring grown-up, and a
tidal outing that becomes suspenseful only long enough to find a gentle,
safe compromise.

The seed image:
- A child wants to stay by the tidal water.
- A grown-up worries about a beloved wearable item getting soaked.
- The child hears a hoot from an owl and follows a referent cue back to safety.
- They solve the problem with a warm, practical choice and end together.

This world keeps the prose child-facing and concrete, with a small amount of
dialogue and suspense, and a resolution that proves something changed in the
world state.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wet", "dirty", "worry", "joy", "love", "fear", "conflict", "relief", "guide"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the tidal beach"
    affords: set[str] = field(default_factory=lambda: {"tidal_walk", "watch_hoots"})


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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone.facts = dict(self.facts)
        return clone


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["wet"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would worry {carer.label}.")
    return out


def _r_hootsafety(world: World) -> list[str]:
    for ent in world.characters():
        if ent.memes["guide"] < THRESHOLD or ent.memes["fear"] < THRESHOLD:
            sig = ("calm", ent.id)
            if sig not in world.fired:
                return []
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soak, _r_worry):
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
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["dirty"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This setting cannot host that activity.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def start(world: World, hero: Entity, grownup: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} loved going to {world.setting.place} at low tide, because the water made the stones shine."
    )
    world.say(
        f"{hero.pronoun().capitalize()} also loved {hero.pronoun('possessive')} {prize.label}, which felt soft and safe to wear."
    )
    world.say(
        f"On the way, {hero.id} heard a little owl hoot from the rocks, and {hero.id} smiled at the sound."
    )


def suspense(world: World, hero: Entity, grownup: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"Then the tide slid closer, and {grownup.label} said, "
        f"\"We need to be careful.\""
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {grownup.label} looked at {hero.pronoun('possessive')} {prize.label} and said, "
        f"\"If the water reaches that, it will get {activity.soil}.\""
    )


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] += 1
    world.say(
        f"{hero.id} hesitated, then tried to {activity.rush}, even while the wavelet whispered at {hero.id}'s feet."
    )


def hoot_dialogue(world: World, hero: Entity, grownup: Entity) -> None:
    hero.memes["guide"] += 1
    world.say(
        f"Just then, the owl gave another warm hoot, and {grownup.label} pointed to the safer path."
    )
    world.say(
        f"\"That way,\" {grownup.label} said gently, \"is the referent we want — the dry path, not the shiny edge.\""
    )


def offer(world: World, grownup: Entity, hero: Entity, activity: Activity, prize: Prize) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
        caretaker=grownup.id,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[gear.id]
        gear.worn_by = None
        return None
    world.say(
        f"{grownup.label} smiled and said, \"How about we put on {gear_def.label} first, and then you can {activity.verb}?\""
    )
    return gear


def accept(world: World, grownup: Entity, hero: Entity, activity: Activity, prize: Prize, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} nodded, hugged {grownup.label}, and said, \"Okay, let's do the safe way.\""
    )
    world.say(
        f"Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the owl's hoot sounded happy over the tidal shore."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl", parent_type: str = "grandmother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    grownup = world.add(Entity(id="Grownup", kind="character", type=parent_type, label="Grandma"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        owner=hero.id,
        caretaker=grownup.id,
    ))
    start(world, hero, grownup, prize, activity)
    world.para()
    suspense(world, hero, grownup, prize, activity)
    defy(world, hero, activity)
    hoot_dialogue(world, hero, grownup)
    world.para()
    gear_def = offer(world, grownup, hero, activity, prize)
    if gear_def:
        accept(world, grownup, hero, activity, prize, gear_def)
    world.facts.update(hero=hero, grownup=grownup, prize=prize, activity=activity, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "tidal_beach": Setting(place="the tidal beach", affords={"tidal_walk"}),
    "rockpool": Setting(place="the rockpool shore", affords={"tidal_walk"}),
    "harbor": Setting(place="the harbor path", affords={"tidal_walk"}),
}

ACTIVITIES = {
    "tidal_walk": Activity(
        id="tidal_walk",
        verb="walk along the tide line",
        gerund="walking along the tide line",
        rush="dash toward the shiny water",
        mess="wet",
        soil="soaked and sandy",
        zone={"feet", "legs"},
        keyword="tidal",
        tags={"tidal", "wet", "hoot", "referent"},
    ),
}

PRIZES = {
    "socks": Prize(label="socks", phrase="striped socks", type="socks", region="feet", plural=True),
    "shoes": Prize(label="shoes", phrase="little canvas shoes", type="shoes", region="feet", plural=True),
    "skirt": Prize(label="skirt", phrase="a bright skirt", type="skirt", region="legs", genders={"girl"}),
}

GEAR = [
    Gear(
        id="tideboots",
        label="tide boots",
        covers={"feet"},
        guards={"wet"},
        prep="put on the tide boots",
        tail="walked back toward the dry path",
        plural=True,
    ),
    Gear(
        id="slicker",
        label="a rain slicker",
        covers={"legs"},
        guards={"wet"},
        prep="zip up the rain slicker",
        tail="headed out with the slicker on",
    ),
]

GIRL_NAMES = ["Mina", "Lia", "Nora", "Pia", "Rosa"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Theo", "Kai"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, grownup, act, prize = f["hero"], f["grownup"], f["activity"], f["prize"]
    return [
        f'Write a heartwarming story about a child at "{world.setting.place}" with a little hoot of an owl in the background.',
        f"Tell a short suspenseful-but-kind story where {hero.id} wants to {act.verb} while {grownup.label} worries about {prize.phrase}.",
        f"Write a dialogue-rich story about a tidal outing, a safe choice, and a quiet referent that points the way home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, grownup, prize, act = f["hero"], f["grownup"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Why did {hero.id} stop and listen when the owl hooted?",
            answer=f"{hero.id} heard the owl hoot and noticed that {grownup.label} was pointing out the safer path by the tidal water.",
        ),
        QAItem(
            question=f"What was {grownup.label} worried would happen to {prize.label} at the tide line?",
            answer=f"{grownup.label} worried that {prize.label} would get {act.soil} if {hero.id} stayed too close to the water.",
        ),
        QAItem(
            question=f"What did {hero.id} and {grownup.label} do so the outing could stay happy?",
            answer=f"They chose a safer way, and if there was gear, they used {gear.label if gear else 'their careful plan'} so {hero.id} could still enjoy {act.gerund}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the ending show that {hero.id} felt better?",
            answer=f"At the end, {hero.id} was smiling, {grownup.label} was smiling too, and the tide stayed away from {prize.label}.",
        ))
    return qa


KNOWLEDGE = {
    "tidal": [("What does tidal mean?", "Tidal means related to the tide, which is the rise and fall of the sea.")],
    "hoot": [("What is a hoot?", "A hoot is the sound an owl makes.")],
    "referent": [("What is a referent?", "A referent is the thing a word points to or refers to.")],
    "wet": [("Why do wet clothes feel different?", "Wet clothes can feel heavy and cool because they hold water.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["hoot", "referent", "tidal", "wet"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="tidal_beach", activity="tidal_walk", prize="socks", name="Mina", gender="girl", parent="grandmother"),
    StoryParams(place="rockpool", activity="tidal_walk", prize="shoes", name="Owen", gender="boy", parent="grandmother"),
    StoryParams(place="harbor", activity="tidal_walk", prize="skirt", name="Lia", gender="girl", parent="grandmother"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} would not honestly threaten {prize.label}, so there is no suspenseful problem to solve.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "grandmother"
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming tidal story world with hoots, referents, and a safe compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandmother"])
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


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
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
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
