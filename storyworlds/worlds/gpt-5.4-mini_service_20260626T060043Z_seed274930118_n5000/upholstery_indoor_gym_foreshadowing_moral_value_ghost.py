#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/upholstery_indoor_gym_foreshadowing_moral_value_ghost.py
================================================================================================

A compact storyworld for a gentle ghost story set in an indoor gym.

Premise:
- A child in an indoor gym notices a strange whisper coming from an upholstered
  bench.
- The whisper foreshadows trouble: rough play could scratch or tear the upholstery.
- A moral-value turn leads the child to choose care over carelessness.
- The ending proves the change in the world state: the upholstery stays clean,
  safe, and softly spooky rather than damaged.

The world is intentionally small and constraint-checked. It models physical
state with meters and emotional state with memes, and it includes an inline ASP
twin for the same reasonableness gate.
"""

from __future__ import annotations

import argparse
import copy
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dusty": 0.0, "torn": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "curiosity": 0.0, "kindness": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the indoor gym"
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for kind in ("dusty", "torn"):
            if actor.meters.get(kind, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.region not in world.zone:
                    continue
                sig = ("damage", actor.id, item.id, kind)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[kind] = item.meters.get(kind, 0.0) + 1.0
                out.append(f"{item.label.capitalize()} seemed to shiver a little in the dim gym light.")
    return out


def _r_safe(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.kind == "thing" and item.type == "upholstery" and item.meters.get("safe", 0.0) < THRESHOLD:
            if item.meters.get("dusty", 0.0) < THRESHOLD and item.meters.get("torn", 0.0) < THRESHOLD:
                sig = ("safe", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["safe"] = 1.0
                out.append(f"The soft cover stayed whole, like it was listening.")
    return out


CAUSAL_RULES = [_r_damage, _r_safe]


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


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "damaged": prize.meters.get("dusty", 0.0) >= THRESHOLD or prize.meters.get("torn", 0.0) >= THRESHOLD,
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1.0
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    prize.worn_by = hero.id

    world.say(
        f"{hero.id} came to the indoor gym with a quiet heart and a bright pair of shoes."
    )
    world.say(
        f"Near the wall, {hero.pronoun('possessive')} {prize.label} looked even softer than a cloud."
    )
    world.say(
        f"At first, the room felt ordinary. Then the upholstered bench gave a tiny creak, as if it knew a secret."
    )

    world.para()
    world.say(
        f"{hero.id} liked the strange hush of the gym and wanted to {activity.verb} right away."
    )
    world.say(
        f"But the little creak returned, and it sounded like a warning hiding inside the stuffing."
    )
    if predict_mess(world, hero, activity, prize.id)["damaged"]:
        world.say(
            f'"If you {activity.verb}, {hero.pronoun("possessive")} {prize.label} could get {activity.soil}," '
            f'{parent.label} said. "That would be hard to mend."'
        )

    hero.memes["fear"] += 1.0
    world.say(
        f"{hero.id} stopped and listened. The bench whispered again, and this time it sounded less spooky than sad."
    )
    world.say(
        f"{hero.id} understood the foreshadowing: rough feet and quick hands could hurt something that many children shared."
    )

    world.para()
    hero.memes["kindness"] += 1.0
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No reasonable soft covering exists for this gym story.")
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id, caretaker=parent.id,
        region="", plural=gear_def.plural,
    ))
    gear.worn_by = hero.id

    world.say(
        f'"How about we {gear_def.prep} first?" {parent.label} said, pointing to the soft cover.'
    )
    world.say(
        f"{hero.id} nodded and helped carefully. The bench stayed wrapped and safe, and the whisper turned gentle."
    )
    _do_activity(world, hero, activity, narrate=True)
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1.0
    world.say(
        f"{hero.id} smiled and {activity.gerund}, while {hero.pronoun('possessive')} {prize.label} stayed clean."
    )
    world.say(
        f"By the end, the ghostly creak was only a sleepy sound in the upholstered gym, and {hero.id} had learned a small moral value: shared things deserve care."
    )

    world.facts.update(
        hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg, activity=activity,
        setting=setting, gear=gear_def, resolved=True, conflict=True,
    )
    return world


SETTINGS = {
    "gym": Setting(place="the indoor gym", indoor=True, affords={"bounce"}),
}

ACTIVITIES = {
    "bounce": Activity(
        id="bounce",
        verb="bounce on the benches",
        gerund="bouncing on the benches",
        rush="rush across the floor",
        mess="dusty",
        soil="dusty and worn",
        zone={"seat"},
        keyword="bounce",
        tags={"ghost", "foreshadowing", "moral_value", "indoor_gym", "upholstery"},
    ),
}

PRIZES = {
    "bench": Prize(
        label="upholstered bench",
        phrase="a soft upholstered bench",
        type="upholstery",
        region="seat",
    ),
}

GEAR = [
    Gear(
        id="cover",
        label="a clean blanket",
        covers={"seat"},
        guards={"dusty", "torn"},
        prep="put a clean blanket over the bench",
        tail="lifted the blanket back carefully",
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Sora", "Nora"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Eli", "Milo"]
TRAITS = ["quiet", "curious", "gentle", "careful"]


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
    "ghost": [(
        "What is a ghost in a spooky story?",
        "A ghost in a spooky story is usually a made-up spirit that helps make the scene feel mysterious or eerie."
    )],
    "foreshadowing": [(
        "What is foreshadowing?",
        "Foreshadowing is when a story gives a small hint about something that may happen later."
    )],
    "moral_value": [(
        "What is a moral value?",
        "A moral value is a good lesson about how to treat people and things, like being honest, gentle, or caring."
    )],
    "upholstery": [(
        "What is upholstery?",
        "Upholstery is the soft fabric or padding that covers chairs, benches, and sofas."
    )],
    "indoor_gym": [(
        "What is an indoor gym?",
        "An indoor gym is a room or building where people can exercise and play indoors."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        'Write a gentle ghost story set in an indoor gym that includes upholstery and a small warning.',
        f"Tell a child-friendly story where {hero.id} wants to {act.verb} in {world.setting.place} but {parent.label} worries about the {prize.label}.",
        f"Write a short spooky-but-kind story with foreshadowing, a moral value, and a soft upholstered bench.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Where does {hero.id}'s story happen?",
            answer=f"It happens in {world.setting.place}, which is an indoor gym."
        ),
        QAItem(
            question=f"What seemed spooky at first in the gym?",
            answer=f"The upholstered bench seemed spooky at first because it made a tiny whispering creak."
        ),
        QAItem(
            question=f"What was {hero.id} warned might happen if {hero.id} kept trying to {act.verb}?",
            answer=f"{hero.id} was warned that the {prize.label} could get {act.soil}."
        ),
        QAItem(
            question=f"What did {hero.id} choose instead of being rough?",
            answer="They chose to be careful, use a soft blanket, and treat the shared bench gently."
        ),
        QAItem(
            question=f"What moral value did {hero.id} learn by the end?",
            answer="They learned that shared things deserve care."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for key in ["ghost", "foreshadowing", "moral_value", "upholstery", "indoor_gym"]:
        if key in tags or key == "upholstery":
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="gym", activity="bounce", prize="bench", name="Mina", gender="girl", parent="mother", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the upholstery would not be at risk in this scene.)"
    if not select_gear(activity, prize):
        return "(No story: there is no reasonable soft covering for the upholstered bench.)"
    return "(No story: this combination is not reasonable.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this prize is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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
    ap = argparse.ArgumentParser(description="Indoor-gym ghost story world with upholstery, foreshadowing, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


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

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
