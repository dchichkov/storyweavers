#!/usr/bin/env python3
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the apartment courtyard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    world.zone = set(action.zone)
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        item.meters[action.mess] = item.meters.get(action.mess, 0.0) + 1
        item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
        if item.caretaker:
            carer = world.get(item.caretaker)
            carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
            if narrate:
                world.say(f"That would mean more work for {carer.label}.")
        if narrate:
            world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got {action.mess} and dirty.")


def main_hero_intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} with a brave heart and a bright mask.")


def loves_power(world: World, hero: Entity, action: Action) -> None:
    hero.memes["love_power"] = hero.memes.get("love_power", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {action.gerund}; it made the whole courtyard feel like a mission.")


def setup_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id}'s {parent.label} brought home {hero.pronoun('object')} {prize.phrase}.")
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} like a badge.")


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say("The air felt still, but somewhere above the courtyard, a storm cloud was getting heavier.")


def wants(world: World, hero: Entity, action: Action) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} pointed at the open space and said, \"I can stop the falling drone before it hits the ground!\"")
    world.say(f"{hero.pronoun().capitalize()} wanted to {action.verb}, but the mission looked risky.")


def warn(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    pred = predict_mess(world, hero, action, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = action.soil
    world.say(f"\"You'll get your {prize.label} {action.soil},\" {parent.label} said. \"And then the whole plan slows down.\"")
    return True


def suspense(world: World, hero: Entity) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.say(f"The clock on the lobby wall ticked fast. Time was running out.")


def defy(world: World, hero: Entity, action: Action) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} shook {hero.pronoun('possessive')} head and ran toward the danger.")
    world.say(f"{hero.pronoun().capitalize()} tried to {action.rush}.")


def stop_and_talk(world: World, parent: Entity, hero: Entity, action: Action) -> None:
    world.say(f'\"Wait,\" {parent.label} said. \"You do want to help. We just need the smart way.\"')
    world.say(f'\"How much time do we have?\" {hero.id} asked.')
    world.say(f'\"Not much,\" {parent.label} answered. \"But enough to choose carefully.\"')


def compromise(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(action, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        worn_by=hero.id,
    ))
    if predict_mess(world, hero, action, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(f"\"Then let's use {gear_def.label} first,\" {parent.label} said. \"That can keep {prize.label} safe.\"")
    return gear_def


def resolution(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["defiance"] = 0.0
    world.say(f"{hero.id} grinned and nodded. \"Okay!\" {hero.pronoun()} said.")
    world.say(f"They fastened the {gear_def.label}, and then {hero.id} darted across {world.setting.place}, {action.gerund}, while {prize.label} stayed clean.")
    world.say(f"The courtyard flashed bright with action, and the hero's quick choice saved the day.")


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    main_hero_intro(world, hero)
    loves_power(world, hero, action)
    setup_prize(world, parent, hero, prize)

    world.para()
    arrive(world, hero, parent)
    wants(world, hero, action)
    warn(world, parent, hero, action, prize)
    suspense(world, hero)
    defy(world, hero, action)
    stop_and_talk(world, parent, hero, action)

    world.para()
    gear_def = compromise(world, parent, hero, action, prize)
    if gear_def:
        resolution(world, parent, hero, action, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, action=action, gear=gear_def, setting=setting)
    return world


SETTINGS = {
    "courtyard": Setting(place="the apartment courtyard", affords={"dash", "glide", "lift"}),
}

ACTIONS = {
    "dash": Action(
        id="dash",
        verb="dash across the courtyard",
        gerund="dashing through the courtyard",
        rush="dash through the wet tiles",
        mess="dusty",
        soil="dusty and dull",
        zone={"feet", "legs"},
        keyword="timeisrunningout",
        tags={"hero", "suspense", "timeisrunningout"},
    ),
    "glide": Action(
        id="glide",
        verb="glide over the slick stones",
        gerund="gliding over the stones",
        rush="glide over the slick stones",
        mess="wet",
        soil="wet and streaked",
        zone={"feet", "legs", "torso"},
        keyword="timeisrunningout",
        tags={"hero", "suspense", "timeisrunningout"},
    ),
    "lift": Action(
        id="lift",
        verb="lift the fallen sign",
        gerund="lifting heavy things",
        rush="lift the heavy sign alone",
        mess="dusty",
        soil="dusty and scuffed",
        zone={"hands", "torso"},
        keyword="timeisrunningout",
        tags={"hero", "suspense", "timeisrunningout"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a red hero cape", type="cape", region="torso"),
    "boots": Prize(label="boots", phrase="shiny rescue boots", type="boots", region="feet", plural=True),
    "suit": Prize(label="suit", phrase="a clean hero suit", type="suit", region="torso"),
}

GEAR = [
    Gear(id="rainboots", label="rain boots", covers={"feet"}, guards={"wet", "dusty"}, prep="put on rain boots", tail="snapped on the rain boots", plural=True),
    Gear(id="gloves", label="strong gloves", covers={"hands"}, guards={"dusty"}, prep="put on strong gloves", tail="pulled on the strong gloves", plural=True),
    Gear(id="mask", label="a clean mask cover", covers={"torso"}, guards={"dusty", "wet"}, prep="wrap the clean mask cover around the suit", tail="secured the clean mask cover"),
]

NAMES = ["Nova", "Max", "Zara", "Kai", "Mira", "Leo"]
TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIONS[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, aid, pid))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, action, prize = f["hero"], f["parent"], f["action"], f["prize"]
    return [
        f'Write a superhero story for a child using the word "{action.keyword}" in the apartment courtyard.',
        f"Tell a suspenseful story where {hero.id} wants to {action.verb} but {parent.label} worries about {prize.phrase}.",
        f"Write a short dialogue-heavy superhero story about {hero.id}, {parent.label}, and a smart rescue plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, action, prize = f["hero"], f["parent"], f["action"], f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the hero in the story?",
            answer=f"The hero is {hero.id}, a brave little {hero.type} who wants to help in the apartment courtyard.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to do in the courtyard?",
            answer=f"{hero.id} wanted to {action.verb}, but the risky plan could have ruined the {prize.label}.",
        ),
        QAItem(
            question=f"Why did {parent.label} speak up?",
            answer=f"{parent.label} was worried that the {prize.label} would get {action.soil} if {hero.id} rushed ahead.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did the heroes solve the problem?",
            answer=f"They used {gear.label} first, so {hero.id} could act like a superhero while the {prize.label} stayed clean.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a courtyard?",
            answer="A courtyard is an open area in the middle of a building or apartment complex where people can walk, play, or meet.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling that something important might happen soon, so you keep wondering what will come next.",
        ),
        QAItem(
            question="Why do superheroes wear special gear?",
            answer="Superheroes wear special gear to stay safe, move fast, and help protect the people and things they care about.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- action(A), prize(P), zone(A, R), region(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), region(P, R).
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
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld set in an apartment courtyard.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
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
    if args.action and args.prize:
        act, prize = ACTIONS[args.action], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError("That action and prize do not make a reasonable superhero problem.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], params.name, params.gender, params.parent)
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


CURATED = [
    StoryParams(place="courtyard", action="glide", prize="cape", name="Nova", gender="girl", parent="mother"),
    StoryParams(place="courtyard", action="dash", prize="boots", name="Kai", gender="boy", parent="father"),
    StoryParams(place="courtyard", action="lift", prize="suit", name="Mira", gender="girl", parent="mother"),
]


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
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for t in vals:
            print(" ", t)
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
