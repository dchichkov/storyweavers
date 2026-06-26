#!/usr/bin/env python3
"""
A small tall-tale storyworld about an obsolete fume machine that makes sound
effects big enough to shake the porch rafters.

Seed tale, imagined as a world:
---
A child loved an old, obsolete fume machine that went
"TOOT! HISS! WHOOOF!" like a whole parade in one box.
A parent worried the hot fume would make the child's fine shirt smell smoky.
The child tried to crank it anyway, but the parent spotted a clever fix:
take the machine outside, use the chimney hood, and let the sound effects fly
in the open air.
---

World idea:
- The hero wants to run an obsolete machine that blasts sound effects.
- The machine gives off fume, which can soil nearby clothes with smoky smell.
- A reasonable compromise exists only when the place is outdoors and the gear
  actually covers the at-risk body region.
- Tall-tale style means the narration is big, folksy, and gleefully noisy.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"smoky"}
REGIONS = {"head", "torso"}


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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    obsolete: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["fume", "smoky", "dust", "joy", "worry", "wonder", "need"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    indoor: bool
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
    keyword: str = ""
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
        self.fired: set[tuple] = set()
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fume_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["fume"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id or item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["smoky"] += 1
            out.append(f"{item.label.capitalize()} came out smoky from the hot fume.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["smoky"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That made {carer.label} worry a mite.")
    return out


CAUSAL_RULES = [
    Rule("fume_soil", "physical", _r_fume_soil),
    Rule("worry", "social", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
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


def predict_smoke(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["smoky"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about an obsolete fume machine.")
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


SETTINGS = {
    "yard": Setting(place="the yard", indoor=False, affords={"sound_effects"}),
    "barn": Setting(place="the barn door", indoor=False, affords={"sound_effects"}),
    "porch": Setting(place="the porch", indoor=False, affords={"sound_effects"}),
}

ACTIVITIES = {
    "sound_effects": Activity(
        id="sound_effects",
        verb="make sound effects",
        gerund="making sound effects",
        rush="crank the old box and let it howl",
        mess="fume",
        soil="smoky",
        zone={"torso"},
        weather="windy",
        keyword="sound effects",
        tags={"sound effects", "obsolete", "fume"},
    )
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a fine white shirt", type="shirt", region="torso"),
    "vest": Prize(label="vest", phrase="a new vest", type="vest", region="torso"),
}

GEAR = [
    Gear(
        id="chimney_hood",
        label="a chimney hood",
        covers={"torso"},
        guards={"smoky"},
        prep="put on a chimney hood first",
        tail="stood under the hood while the fume blew away",
    ),
    Gear(
        id="wind_cloak",
        label="a wind cloak",
        covers={"torso"},
        guards={"smoky"},
        prep="throw on a wind cloak",
        tail="let the windcloak catch the smoke",
    ),
]

GIRL_NAMES = ["Mabel", "Ruby", "Ada", "Fay", "June", "Nell"]
BOY_NAMES = ["Hank", "Otis", "Ike", "Bo", "Cal", "Jeb"]
TRAITS = ["bold", "curious", "cheerful", "stubborn", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the sound effects do not reach that prize's region, so nothing honest is at risk.)"
    return "(No story: there is no reasonable gear to keep that prize safe from the fume.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: that prize does not fit a {gender} in this world; try {ok}.)"


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
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    machine = world.add(Entity(
        id="machine", type="machine", label="the obsolete fume machine", obsolete=True
    ))
    world.say(f"{hero_name} was a {trait} little {hero_type} who loved the old, obsolete fume machine.")
    world.say(
        f"It could make sound effects so grand they sounded like a parade thundering through a bucket: "
        f'"TOOT! HISS! WHOOOF!"'
    )
    world.say(f"{hero_name}'s {parent.label_word if hasattr(parent, 'label_word') else parent.type} bought {hero.pronoun('object')} {prize.phrase}.")
    prize.worn_by = hero.id
    world.para()
    world.say(f"One windy day, {hero_name} and {hero.pronoun('possessive')} {parent.type} went to {setting.place}.")
    world.say(f"{hero_name} wanted to {activity.verb}, but the machine puffed out hot fume like a dragon with manners to spare.")
    pred = predict_smoke(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.say(f'"You'll get your {prize.label} smoky," {hero.pronoun("possessive")} {parent.type} said. "Hold your horses and listen."')
    hero.memes["need"] += 1
    hero.memes["worry"] += 1
    world.say(f"{hero_name} sure wanted to {activity.verb} anyway, and {hero.pronoun("subject")} reached for the crank.")
    world.zone = set(activity.zone)
    hero.meters["fume"] += 1
    propagate(world, narrate=True)
    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No reasonable gear exists for this story.")
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers)))
    gear.worn_by = hero.id
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.type} pointed to {gear_def.label} and said, \"{gear_def.prep.capitalize()}, and then let that old box sing.\"")
    hero.memes["joy"] += 1
    world.say(
        f"{hero_name} grinned, {gear_def.tail}, and went on {activity.gerund} while the fume climbed the sky and lost its fight."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a tall tale for a child about an obsolete machine that makes "{act.keyword}" and fume.',
        f"Tell a funny, old-timey story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.type} worries about {prize.phrase}.",
        f"Write a short tall tale about sound effects, a smoky fume, and a clever fix that keeps {hero.pronoun('possessive')} {prize.label} clean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, gear = f["hero"], f["parent"], f["prize"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"What kind of machine did {hero.id} love?",
            answer=f"{hero.id} loved an old, obsolete fume machine that made big sound effects like a parade in a tin bucket."
        ),
        QAItem(
            question=f"Why did {parent.type} worry about {prize.label}?",
            answer=f"{parent.label} worried because the hot fume from the machine could make {hero.pronoun('possessive')} {prize.label} smoky."
        ),
        QAItem(
            question=f"How did they solve the problem before {hero.id} kept {act.gerund}?",
            answer=f"They used {gear.label} and took the machine outside, so {hero.id} could keep {act.gerund} while the smoke drifted away."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does obsolete mean?", answer="Obsolete means old-fashioned or no longer used much, even though it still works."),
        QAItem(question="What is fume?", answer="Fume is a smoky gas or vapor that can drift up from something hot."),
        QAItem(question="What are sound effects?", answer="Sound effects are special noises, like whistles, hisses, bangs, and booms, that help tell a story or make a performance exciting."),
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
        if e.obsolete:
            bits.append("obsolete=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="yard", activity="sound_effects", prize="shirt", name="Mabel", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="porch", activity="sound_effects", prize="vest", name="Hank", gender="boy", parent="father", trait="stubborn"),
]


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
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
    world.facts.update(hero=world.get(params.name), parent=world.get("Parent"), prize=world.get("prize"), activity=ACTIVITIES[params.activity], prize_cfg=PRIZES[params.prize], gear=GEAR[0], setting=SETTINGS[params.place])
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_valid_combos())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
