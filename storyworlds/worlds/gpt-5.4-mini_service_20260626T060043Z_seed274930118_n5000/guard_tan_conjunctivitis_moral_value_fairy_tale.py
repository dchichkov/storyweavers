#!/usr/bin/env python3
"""
storyworlds/worlds/guard_tan_conjunctivitis_moral_value_fairy_tale.py
=====================================================================

A small fairy-tale story world about a guard who wants a tan, but must be
wise about conjunctivitis, cleanliness, and moral value.

Premise:
- A young castle guard loves the summer sun and wishes for a tan.
- The guard already has conjunctivitis, so bright wind and rubbing eyes are risky.
- A mentor urges careful habits: clean hands, no sharing cloths, and a shaded rest.

State-driven beats:
- sun + dust can deepen the guard's tan and make the eyes more irritated
- rubbing eyes spreads irritation and increases the healer's work
- a clean cloth, a shaded bench, and patience resolve the trouble

The moral value is simple and child-facing:
- Being brave does not mean ignoring sickness.
- Clean hands and careful sharing help everyone stay well.
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

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "guard", "man"}:
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
    indoor: bool = False
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_tan(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("sun", 0.0) < THRESHOLD:
            continue
        sig = ("tan", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["tan"] = actor.meters.get("tan", 0.0) + 1
        out.append(f"{actor.id}'s skin grew a little more tan in the summer light.")
    return out


def _r_eye(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("dust", 0.0) < THRESHOLD:
            continue
        sig = ("eye", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["conjunctivitis"] = actor.meters.get("conjunctivitis", 0.0) + 1
        out.append(f"{actor.id}'s eyes became more sore and pink from the dust.")
    return out


def _r_rub(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("rubs_eyes", 0.0) < THRESHOLD:
            continue
        sig = ("rub", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["conjunctivitis"] = actor.meters.get("conjunctivitis", 0.0) + 1
        out.append(f"That made {actor.id}'s conjunctivitis worse.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] = caretaker.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {caretaker.label_word}.")
    return out


CAUSAL_RULES = [_r_tan, _r_eye, _r_rub, _r_work]


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


def activity_risk(activity: Activity, prize: "Prize") -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: "Prize") -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "tan": actor.meters.get("tan", 0.0),
    }


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a little {trait} guard at the castle gate, and {hero.pronoun()} loved the warm sun.")


def desire_tan(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} wished for a tan and longed to {activity.verb} by the garden wall.")


def warn(world: World, mentor: Entity, hero: Entity, activity: Activity) -> None:
    world.say(f'"A wise guard does not rub sore eyes," {mentor.label_word} said. "Clean hands are kinder than a careless touch."')
    world.say(f"{hero.id} heard the warning, but the sunshine still looked sweet.")


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.meters["sun"] = actor.meters.get("sun", 0.0) + 1
    if activity.id == "dusty_patrol":
        actor.meters["dust"] = actor.meters.get("dust", 0.0) + 1
    propagate(world, narrate=narrate)


def rub(world: World, actor: Entity) -> None:
    actor.memes["rubs_eyes"] = actor.memes.get("rubs_eyes", 0.0) + 1
    world.say(f"{actor.id} almost rubbed {actor.pronoun('possessive')} eyes, and the sight made the healer frown.")


def offer_cloth(world: World, mentor: Entity, hero: Entity, activity: Activity, prize: Prize) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=mentor.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    world.say(f'{mentor.label_word} brought {gear_def.label} and said, "{gear_def.prep}."')
    return gear_def


def accept(world: World, mentor: Entity, hero: Entity, activity: Activity, prize: Prize, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    hero.memes["rubs_eyes"] = 0.0
    world.say(f"{hero.id} smiled, washed {hero.pronoun('possessive')} hands, and promised not to share a cloth again.")
    world.say(
        f"Then {hero.id} went to {gear_def.tail}, sat in the shade, and still came away with a gentle tan while {prize.label} stayed well cared for."
    )


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "castle_garden": Setting("the castle garden", False, {"sunbathing", "dusty_patrol"}),
    "rose_lane": Setting("the rose lane", False, {"sunbathing", "dusty_patrol"}),
    "courtyard": Setting("the courtyard", False, {"sunbathing", "dusty_patrol"}),
}

ACTIVITIES = {
    "sunbathing": Activity(
        id="sunbathing",
        verb="bask in the sun",
        gerund="basking in the sun",
        rush="run into the bright yard",
        mess="sun",
        soil="more tan",
        zone={"face", "arms"},
        weather="sunny",
        keyword="tan",
        tags={"tan", "sun", "moral"},
    ),
    "dusty_patrol": Activity(
        id="dusty_patrol",
        verb="patrol the dusty road",
        gerund="patrolling the dusty road",
        rush="run down the dusty road",
        mess="dust",
        soil="more dust",
        zone={"face", "eyes"},
        weather="windy",
        keyword="conjunctivitis",
        tags={"conjunctivitis", "dust", "moral"},
    ),
}

PRIZES = {
    "cloak": Prize("cloak", "a clean white cloak", "cloak", "torso"),
    "mask": Prize("mask", "a soft linen face cloth", "mask", "face"),
    "badge": Prize("badge", "a bright silver badge", "badge", "torso"),
}

GEAR = [
    Gear("hat", "a wide straw hat", {"face"}, {"sun"}, "put on a wide straw hat first", "the shade tree", False),
    Gear("cloth", "a clean handkerchief", {"face"}, {"dust"}, "use a clean handkerchief and keep it for yourself", "the healer's bench", False),
    Gear("visor", "a little visor", {"face"}, {"sun", "dust"}, "wear the little visor and rest under the awning", "the awning", False),
]

GIRL_NAMES = ["Ava", "Mira", "Nora", "Elin", "Iris"]
BOY_NAMES = ["Bram", "Tomas", "Ewan", "Luca", "Piers"]
TRAITS = ["brave", "patient", "gentle", "cheerful", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, hero_traits: list[str], mentor_type: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + hero_traits))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label="the healer"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=mentor.id, region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    desire_tan(world, hero, activity)
    world.say(f"At {setting.place}, {hero.id} carried {hero.pronoun('possessive')} {prize.label} and looked toward the light.")
    world.para()
    warn(world, mentor, hero, activity)
    do_activity(world, hero, activity)
    rub(world, hero)
    propagate(world)
    world.para()
    gear_def = offer_cloth(world, mentor, hero, activity, prize)
    if gear_def:
        accept(world, mentor, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, mentor=mentor, prize=prize, activity=activity, setting=setting, gear=gear_def)
    world.facts["resolved"] = gear_def is not None
    world.facts["conflict"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mentor, activity, prize = f["hero"], f["mentor"], f["activity"], f["prize"]
    return [
        f'Write a fairy tale about a guard named {hero.id} who wants a {activity.keyword} and learns a moral lesson about clean hands.',
        f"Tell a gentle story where {hero.id} has conjunctivitis, wants to {activity.verb}, and listens to {mentor.label_word}.",
        f'Write a child-friendly tale that includes the words "guard", "{activity.keyword}", and "conjunctivitis".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, activity, prize = f["hero"], f["mentor"], f["activity"], f["prize"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {next(t for t in hero.traits if t != 'little')} guard at the castle.",
        ),
        QAItem(
            question=f"What did {hero.id} want from the sunshine?",
            answer=f"{hero.id} wanted a tan and hoped to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did the healer warn {hero.id}?",
            answer=f"The healer warned {hero.id} because {hero.id} had conjunctivitis, and rubbing eyes or sharing a cloth could make things worse.",
        ),
        QAItem(
            question=f"What helped {hero.id} in the end?",
            answer=f"A clean cloth, shade, and patience helped {hero.id} stay safe while enjoying the day.",
        ),
        QAItem(
            question=f"What moral value does the tale teach?",
            answer="It teaches that a brave person also stays clean, careful, and kind so everyone can stay well.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label} helped because it kept {hero.id}'s face protected while {hero.id} rested in the shade and still got a gentle tan.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a guard?",
            answer="A guard is a person who watches over a place and helps keep people safe.",
        ),
        QAItem(
            question="What does tan mean?",
            answer="Tan is a light brown color, and skin can look a little tan after time in the sun.",
        ),
        QAItem(
            question="What is conjunctivitis?",
            answer="Conjunctivitis is an eye sickness that can make the eyes red, sore, and watery.",
        ),
        QAItem(
            question="Why are clean hands important?",
            answer="Clean hands help keep dirt and germs away from eyes, noses, and food.",
        ),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("castle_garden", "sunbathing", "cloak", "Bram", "boy", "the healer", "brave"),
    StoryParams("rose_lane", "dusty_patrol", "mask", "Elin", "girl", "the healer", "gentle"),
    StoryParams("courtyard", "sunbathing", "badge", "Tomas", "boy", "the healer", "steady"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not activity_risk(activity, prize):
        return f"(No story: {activity.gerund} does not put the {prize.label} at risk.)"
    if select_gear(activity, prize) is None:
        return f"(No story: no careful gear in this world can reasonably help with {activity.keyword} and a {prize.label}.)"
    return "(No story: the requested options do not make a good fairy-tale shape.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: that prize is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
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
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale guard story world with tan, conjunctivitis, and a moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["queen", "healer"])
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
        if not (activity_risk(act, pr) and select_gear(act, pr)):
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = args.mentor or "healer"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, mentor=mentor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.mentor)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            print(f"  {place:12} {act:14} {prize:8}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
