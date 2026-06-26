#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/pajama_display_cautionary_rhyming_story.py
===============================================================================================================

A small cautionary rhyming storyworld about a child who wants to display new
pajamas, learns why a showy choice can go wrong, and finds a safer way to shine.

The seed image:
- A child adores a pair of pajamas.
- The child wants to display them.
- The story should feel like a rhyming, child-facing cautionary tale.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wet", "muddy", "snagged", "cold", "dusty"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "pride", "worry", "relief", "patience", "embarrassment"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str]


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
    keyword: str = "display"
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
    transparent: bool = False
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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
    return {
        "soiled": prize.meters["wet"] >= THRESHOLD or prize.meters["muddy"] >= THRESHOLD or prize.meters["dusty"] >= THRESHOLD,
        "cold": prize.meters["cold"] >= THRESHOLD,
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"The setting {world.setting.place!r} cannot host {activity.id!r}.")
    world.zone = set(activity.zone)
    actor.memes["pride"] += 1
    actor.meters[activity.mess] += 1
    if world.weather == "rainy":
        actor.meters["cold"] += 0.5
    if narrate:
        propagate(world, narrate=True)


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD and actor.meters["muddy"] < THRESHOLD and actor.meters["dusty"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += actor.meters["wet"]
            item.meters["muddy"] += actor.meters["muddy"]
            item.meters["dusty"] += actor.meters["dusty"]
            item.meters["cold"] += 1
            out.append(f"{actor.id}'s {item.label} got damp and dim.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["wet"] >= THRESHOLD or item.meters["muddy"] >= THRESHOLD or item.meters["cold"] >= THRESHOLD:
            if item.caretaker and ("care", item.id) not in world.fired:
                world.fired.add(("care", item.id))
                caretaker = world.get(item.caretaker)
                caretaker.memes["worry"] += 1
                out.append(f"That would give {caretaker.label} a worry to carry.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["stopped"] if "stopped" in actor.memes else 0:
            pass
        if actor.memes["worry"] >= THRESHOLD and actor.memes["pushback"] >= THRESHOLD:
            if ("conflict", actor.id) not in world.fired:
                world.fired.add(("conflict", actor.id))
                actor.memes["embarrassment"] += 1
                return ["__conflict__"]
    return []


CAUSAL_RULES = [
    _r_soak,
    _r_worry,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule(world)
            if items:
                changed = True
                produced.extend(x for x in items if x != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhymes() -> dict[str, str]:
    return {
        "setup": "Night by night, with lamp-light bright,",
        "joy": "A child can beam, but must choose the scheme.",
        "warn": "If you go to show and the puddles glow,",
        "turn": "A little slip can spoil the trip.",
        "fix": "A safer way can save the day.",
        "end": "Soft and neat, the pajamas look sweet.",
    }


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoors:
        return "The hallway gleamed, and the mirror made everything look like a stage."
    return "The porch stood dim, and the grass below looked damp and slim."


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name,
                            meters={}, memes={"joy": 0, "pride": 0, "worry": 0, "relief": 0, "patience": 0, "embarrassment": 0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="Mom" if parent_type == "mother" else "Dad",
                              meters={}, memes={"joy": 0, "worry": 0, "patience": 0, "relief": 0, "pushback": 0}))
    prize = world.add(Entity(id="pajamas", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))

    trait = (hero_traits or ["cheerful"])[0]
    world.say(f"{rhymes()['setup']} {hero.id} was a little {trait} {hero.type}, light as a kite.")
    world.say(f"{hero.id} loved {activity.gerund} and liked to {activity.keyword} and strut; the pajamas felt shiny and snug.")
    world.say(f"One day {parent.label} bought {hero.id} {prize.phrase}, a soft little set to wear and to hug.")
    world.say(f"{hero.id} loved the pajama display; {hero.id} wanted to show them off in a bright, proud way.")

    world.para()
    world.say(setting_detail(setting, activity))
    world.say(f"Then {hero.id} ran to {world.setting.place} to {activity.verb}, while the wind gave a sigh and a sly little cry.")
    hero.memes["pushback"] += 1
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f'"You should not go," {parent.label} said low. "Your {prize.label} will get wet, and then it will be a fret."')
    hero.meters[activity.mess] += 1
    hero.meters["cold"] += 1
    propagate(world, narrate=True)
    world.say(f"{hero.id} frowned and tried to keep going, but the porch was slippery, glimmering, and slow-ing.")
    hero.memes["pushback"] += 1
    parent.memes["worry"] += 1

    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No safe, fitting gear exists for this storyworld.")
    safe = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=hero.id, caretaker=parent.id,
                            protective=True, covers=set(gear.covers), plural=gear.plural))
    safe.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        safe.worn_by = None
        del world.entities[safe.id]
        raise StoryError("The offered gear does not actually keep the pajamas safe.")
    world.say(f"Then {parent.label} smiled and said, \"Let's not race in the rain; let's use {gear.label} instead.\"")
    world.say(f"\"We can still display them and keep them dry,\" {parent.label} said with a wink and a nod.")
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    parent.memes["relief"] += 1
    world.say(f"{hero.id} slipped on {gear.label}, and the see-through shine let the pajamas stay in sight.")
    world.say(f"{gear.tail.capitalize()}, and {hero.id} posed in the hall, where the light was soft and bright.")
    world.say(f"{rhymes()['end']} {hero.id} smiled, all calm and mild, and the caution turned gentle for the child.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=True,
    )
    return world


SETTINGS = {
    "porch": Setting(place="the porch", indoors=False, affords={"display"}),
    "yard": Setting(place="the yard", indoors=False, affords={"display"}),
    "hall": Setting(place="the hallway", indoors=True, affords={"display"}),
}

ACTIVITIES = {
    "display": Activity(
        id="display",
        verb="show off the pajamas",
        gerund="posing in pajamas",
        rush="dash outside to display them",
        mess="wet",
        soil="damp and muddy",
        zone={"torso", "legs"},
        weather="rainy",
        keyword="display",
        tags={"display", "wet"},
    )
}

PRIZES = {
    "pajamas": Prize(
        label="pajamas",
        phrase="a striped pair of pajamas",
        type="pajamas",
        region="torso",
        plural=True,
    )
}

GEAR = [
    Gear(
        id="clear_cape",
        label="a clear rain cape",
        covers={"torso", "legs"},
        guards={"wet", "muddy"},
        prep="put on a clear rain cape",
        tail="they went back inside to fetch the clear rain cape",
        transparent=True,
        plural=False,
    )
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Rosa", "Pia"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Ben", "Jude"]
TRAITS = ["cheerful", "curious", "spirited", "proud", "playful"]


@dataclass
class _Args:
    setting: Optional[str] = None
    activity: Optional[str] = None
    prize: Optional[str] = None
    gender: Optional[str] = None
    parent: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary rhyming storyworld about pajamas on display.")
    ap.add_argument("--setting", choices=SETTINGS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    activity = args.activity or "display"
    prize = args.prize or "pajamas"
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in PRIZES[prize].genders:
        raise StoryError("This child type does not fit the chosen pajamas in this world.")
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    act = ACTIVITIES[activity]
    pr = PRIZES[prize]
    if not prize_at_risk(act, pr) or select_gear(act, pr) is None:
        raise StoryError("No cautionary turn is possible with these choices.")
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        'Write a short rhyming story for a young child about pajamas on display and a safer choice.',
        f"Tell a cautionary rhyming tale where {hero.id} wants to {act.verb} but {parent.label} worries about {prize.label}.",
        f'Write a gentle story with the word "{act.keyword}" and a happy, safer ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the pajamas?",
            answer=f"{hero.id} wanted to {act.verb} and put the pajamas on display.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the pajamas?",
            answer=f"{parent.label} worried because if {hero.id} went outside to {act.verb}, the pajamas could get wet and muddy.",
        ),
        QAItem(
            question=f"What safer choice did they make at the end?",
            answer=f"They used {f['gear'].label} and stayed in the safer place, so the pajamas could still be displayed without getting ruined.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a display?",
            answer="A display is a way of showing something so other people can see it clearly.",
        ),
        QAItem(
            question="Why is rain tricky for cloth clothes?",
            answer="Rain can soak cloth and make it heavy, cold, and messy.",
        ),
        QAItem(
            question="What does a clear rain cape do?",
            answer="A clear rain cape helps keep clothes dry while still letting people see what is underneath.",
        ),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid_story(S,A,P) :- setting(S), affords(S,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for a in setting.affords:
            for p, prize in PRIZES.items():
                if prize_at_risk(ACTIVITIES[a], prize) and select_gear(ACTIVITIES[a], prize):
                    combos.append((s, a, p))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = [
            StoryParams(setting="porch", activity="display", prize="pajamas", name="Mina", gender="girl", parent="mother", trait="cheerful"),
            StoryParams(setting="yard", activity="display", prize="pajamas", name="Finn", gender="boy", parent="father", trait="curious"),
            StoryParams(setting="hall", activity="display", prize="pajamas", name="Lila", gender="girl", parent="mother", trait="playful"),
        ]
        samples = [generate(p) for p in params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
