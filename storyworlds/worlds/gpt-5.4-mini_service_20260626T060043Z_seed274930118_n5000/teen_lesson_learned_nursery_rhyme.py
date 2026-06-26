#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/teen_lesson_learned_nursery_rhyme.py
===============================================================================================================

A small story world in a nursery-rhyme style about a teen who learns a lesson
the hard way, then makes things right.

Premise:
- A teen wants to do something fun or fast.
- A practical warning says to slow down or do a chore first.
- The teen ignores the warning, causing a small, concrete problem.

Turn:
- The teen sees the consequence.
- A helper offers a simple fix or a better way.

Resolution:
- The teen accepts the lesson learned and ends more thoughtful.

The world is intentionally tiny and constraint-checked: only plausible
problem/fix pairings are allowed.
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man", "teen"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy", "teen"})


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
        return any(g.region == region and g.meters.get("protective", 0) >= THRESHOLD for g in self.worn_items(actor))

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
        c.facts = dict(self.facts)
        return c


def _r_mess(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mess in {"dirty", "wet"}:
            if actor.meters.get(mess, 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.region not in world.zone:
                    continue
                sig = ("mess", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0) + 1
                out.append(f"{actor.id}'s {item.label} got {mess}.")
    return out


def _r_lesson(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("oops", 0) < THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["lesson"] = actor.memes.get("lesson", 0) + 1
        out.append(f"{actor.id} learned a lesson.")
    return out


CAUSAL_RULES = [_r_mess, _r_lesson]


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


def activity_line(activity: Activity) -> str:
    return {
        "skate": "The wheels went zip and zip, like a tune in spring.",
        "bike": "The tires went hum-hum-hum, a breezy little thing.",
        "phone": "The screen went glow and bright, and buzzed like a bee.",
        "snack": "The crumbs went crunch and crack, as happy as could be.",
    }.get(activity.id, "It made a tiny, bright, and bouncy kind of sound.")


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": bool(prize.meters.get(activity.mess, 0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["oops"] = actor.memes.get("oops", 0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Tessa", hero_type: str = "teen",
         parent_type: str = "mother") -> World:
    world = World(setting)
    teen = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=teen.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    world.say(f"{teen.id} was a teen who loved to move in the morning light.")
    world.say(f"{activity_line(activity)} {teen.pronoun().capitalize()} wanted to {activity.verb},")
    world.say(f"and {teen.pronoun('possessive')} {parent.label} said, \"First, please mind {teen.pronoun('possessive')} {prize.label}.\"")
    world.say(f"But {teen.id} smiled and dashed off to {activity.verb}.")

    world.para()
    _do_activity(world, teen, activity, narrate=True)
    world.say(f"{teen.id} saw that {teen.pronoun('possessive')} {prize.label} had gotten {activity.soil}.")
    world.say(f"That was a small, sad clue that rushing can make a mess.")

    world.para()
    gear = select_gear(activity, prize)
    if gear and not predict_mess(world, teen, activity, prize.id)["soiled"]:
        gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=teen.id))
        gear_ent.worn_by = teen.id
        gear_ent.region = prize.region
        gear_ent.meters["protective"] = 1
        world.say(f"Then {teen.pronoun('possessive')} {parent.label} brought out {gear.label}.")
        world.say(f"\"How about we {gear.prep} and try again?\" she said in a sing-song way.")
        teen.memes["lesson"] = teen.memes.get("lesson", 0) + 1
        world.say(f"{teen.id} nodded, and {teen.pronoun()} knew the lesson at once.")
        world.say(f"They {gear.tail}, and this time {prize.label} stayed nice and clean.")
    else:
        world.say(f"{teen.id} paused, cleaned up, and promised to try the careful way next time.")
        teen.memes["lesson"] = teen.memes.get("lesson", 0) + 1
        world.say(f"That was the lesson learned: slow steps save the day.")

    world.facts.update(hero=teen, parent=parent, prize=prize, activity=activity, gear=gear)
    return world


SETTINGS = {
    "home": Setting(place="home", affords={"skate", "phone", "snack"}),
    "street": Setting(place="the street", affords={"skate", "bike"}),
    "porch": Setting(place="the porch", affords={"snack", "phone"}),
}

ACTIVITIES = {
    "skate": Activity(
        id="skate",
        verb="ride the skateboard",
        gerund="riding a skateboard",
        rush="zip down the sidewalk",
        mess="dirty",
        soil="dusty and dirty",
        zone={"feet", "legs"},
        keyword="skate",
        tags={"skate", "dirty"},
    ),
    "bike": Activity(
        id="bike",
        verb="ride the bike",
        gerund="riding a bike",
        rush="race down the lane",
        mess="dirty",
        soil="dusty and dirty",
        zone={"feet", "legs", "hands"},
        keyword="bike",
        tags={"bike", "dirty"},
    ),
    "phone": Activity(
        id="phone",
        verb="scroll on the phone",
        gerund="scrolling on a phone",
        rush="keep staring at the glow",
        mess="wet",
        soil="spotted with spills",
        zone={"hands", "torso"},
        keyword="phone",
        tags={"phone", "wet"},
    ),
    "snack": Activity(
        id="snack",
        verb="eat the snack",
        gerund="snacking happily",
        rush="grab another bite",
        mess="dirty",
        soil="crumbly and dirty",
        zone={"hands", "torso"},
        keyword="snack",
        tags={"snack", "dirty"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "shoes": Prize(label="shoes", phrase="fresh sneakers", type="shoes", region="feet", plural=True),
    "jacket": Prize(label="jacket", phrase="a neat jacket", type="jacket", region="torso"),
    "cap": Prize(label="cap", phrase="a bright cap", type="cap", region="head"),
}

GEAR = [
    Gear(id="apron", label="an apron", covers={"torso"}, guards={"dirty", "wet"}, prep="put on an apron first", tail="walked back for the apron"),
    Gear(id="socks", label="clean socks", covers={"feet"}, guards={"dirty"}, prep="change into clean socks", tail="came back with clean socks", plural=True),
    Gear(id="raincoat", label="a raincoat", covers={"torso"}, guards={"wet"}, prep="put on a raincoat first", tail="came back with the raincoat"),
]

TEEN_NAMES = ["Ari", "Maya", "Noah", "Zoe", "Finn", "Riley", "Jules", "Kai"]
PARENT_NAMES = ["mother", "father"]
TRAITS = ["brave", "restless", "curious", "bright", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a nursery-rhyme-style story about a teen named {hero.id} who wants to {act.verb} but learns a lesson about {prize.label}.',
        f"Tell a short, musical story where {hero.id} rushes to {act.verb}, but {hero.pronoun('possessive')} {parent.label} helps {hero.pronoun('object')} make a wiser choice.",
        f'Write a child-friendly rhyme that includes the word "teen" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a teen named {hero.id}, and {hero.pronoun('possessive')} {parent.label} was there too.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {act.verb}, even though that could make {hero.pronoun('possessive')} {prize.label} messy.",
        ),
        QAItem(
            question=f"What problem happened when {hero.id} rushed ahead?",
            answer=f"{hero.id}'s {prize.label} got {act.soil}, which showed that the first choice was not the careful one.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label} gave {hero.id} a safer way to try again, so the lesson could be learned without making more trouble.",
        ))
    qa.append(QAItem(
        question=f"What lesson did {hero.id} learn?",
        answer=f"{hero.id} learned to slow down, listen first, and choose the careful way before rushing into fun.",
    ))
    return qa


KNOWLEDGE = {
    "teen": [("What is a teen?", "A teen is a young person who is old enough to help more, but still has lots to learn.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is a useful idea someone understands after trying something and seeing what happens.")],
    "skate": [("What is a skateboard?", "A skateboard is a small board with wheels that people can ride on smooth ground.")],
    "bike": [("What is a bike?", "A bike is a two-wheeled ride that people pedal to move along.")],
    "phone": [("What is a phone used for?", "A phone can be used to call, message, or look up things, but it is best to use it safely.")],
    "snack": [("What is a snack?", "A snack is a small food that gives you a little energy between bigger meals.")],
    "dirty": [("Why do dirty clothes need washing?", "Dirty clothes need washing so the stains and dust can come out and they can be worn again.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("teen")
    tags.add("lesson")
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for key in ["teen", "lesson", "skate", "bike", "phone", "snack", "dirty"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.label}.)"
    if not select_gear(activity, prize):
        return f"(No story: there is no fitting fix for a {prize.label} in this situation.)"
    return "(No story: invalid combination.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a teen who learns a lesson.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(TEEN_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, "teen", params.parent)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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


CURATED = [
    StoryParams(place="home", activity="skate", prize="shirt", name="Ari", parent="mother", trait="bouncy"),
    StoryParams(place="street", activity="bike", prize="jacket", name="Maya", parent="father", trait="curious"),
    StoryParams(place="porch", activity="snack", prize="shirt", name="Noah", parent="mother", trait="bright"),
    StoryParams(place="porch", activity="phone", prize="shirt", name="Zoe", parent="father", trait="restless"),
]


if __name__ == "__main__":
    main()
