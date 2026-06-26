#!/usr/bin/env python3
"""
storyworlds/worlds/scrub_splash_pad_quest_heartwarming.py
=========================================================

A small heartwarming story world set at a splash pad.

Seed tale premise:
- A child wants to finish a tiny Quest.
- The Quest involves scrubbing something messy before play.
- A caring grown-up worries about the mess and helps turn it into a shared job.
- The ending proves the place is cleaner, the child feels proud, and play can begin.

This world is intentionally narrow: a few plausible combinations, one clear turn,
and a warm resolution.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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


@dataclass
class Setting:
    place: str = "the splash pad"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "scrub"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


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
        return any(item.region == region and item.label in {"rain boots", "rubber gloves", "an apron"} for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_splash_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("wet", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone or item.label in {"rain boots", "rubber gloves", "an apron"}:
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet.")
    return out


def _r_caretaker_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_teamup(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("helped", 0.0) < THRESHOLD:
            continue
        sig = ("teamup", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        actor.memes["pride"] = actor.memes.get("pride", 0.0) + 1
        out.append(f"{actor.id} felt proud to help.")
    return out


CAUSAL_RULES = [_r_splash_soak, _r_caretaker_work, _r_teamup]


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


def predict_mess(world: World, actor: Entity, quest: Quest, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
        "traits": list(v.traits), "owner": v.owner, "caretaker": v.caretaker,
        "worn_by": v.worn_by, "region": v.region, "plural": v.plural,
        "meters": dict(v.meters), "memes": dict(v.memes)
    }) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    _do_quest(sim, sim.get(actor.id), quest, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD or prize.meters.get("wet", 0.0) >= THRESHOLD,
        "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters()),
    }


def quest_starts(quest: Quest) -> str:
    return {
        "scrub": "the tiles shone a little brighter with every wipe",
    }.get(quest.id, "the little task felt important")


def setting_detail(setting: Setting, quest: Quest) -> str:
    return f"The {setting.place.removeprefix('the ')} sparkled in the sun, waiting for a careful hand."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who noticed when a place needed care.")


def loves_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved the {quest.keyword.capitalize()} Quest because {quest_starts(quest)}.")


def arrives(world: World, hero: Entity, parent: Entity, quest: Quest) -> None:
    world.say(f"One bright day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, quest))


def wants(world: World, hero: Entity, parent: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {quest.verb} right away, but {hero.pronoun('possessive')} {parent.label} looked at {prize.label} and worried.")


def warn(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity) -> bool:
    pred = predict_mess(world, hero, quest, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_workload"] = pred["workload"]
    world.say(f"\"You'll get your {prize.label} messy,\" {hero.pronoun('possessive')} {parent.label} said. \"Let's scrub carefully.\"")
    return True


def defies(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} took a tiny breath and started toward the wet floor anyway.")
    world.say(f"{hero.pronoun().capitalize()} tried to {quest.rush}.")


def _do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    world.zone = set(quest.zone)
    actor.meters[quest.mess] = actor.meters.get(quest.mess, 0.0) + 1
    actor.memes["helped"] = actor.memes.get("helped", 0.0) + 1
    propagate(world, narrate=narrate)


def grab_and_help(world: World, parent: Entity, hero: Entity, quest: Quest) -> None:
    hero.memes["held"] = hero.memes.get("held", 0.0) + 1
    world.say(f"Then {hero.pronoun('possessive')} {parent.label} held out a hand and said, \"We can do the Quest together.\"")


def compromise(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(quest, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        plural=gear_def.plural,
    ))
    if predict_mess(world, hero, quest, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} found {gear_def.label} so {hero.id} could help without making a bigger mess.")
    return gear


def accept(world: World, parent: Entity, hero: Entity, quest: Quest, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["defiance"] = 0.0
    world.say(f"{hero.id} smiled, took {hero.pronoun('possessive')} {parent.label}'s hand, and got to work.")
    world.say(f"Soon the {world.setting.place.removeprefix('the ')} was cleaner, the {prize.label} stayed dry, and {hero.id} was {quest.gerund} with a happy heart.")


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "gentle") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                              owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    introduce(world, hero)
    loves_quest(world, hero, quest)
    world.say(f"That morning, {hero.id}'s {parent.label} had brought {hero.pronoun('object')} a {prize.phrase}.")
    hero.worn_prize = prize.id  # harmless extra state for trace-like narrative grounding
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wanted to keep {prize.it()} nice.")
    world.para()
    arrives(world, hero, parent, quest)
    wants(world, hero, parent, quest, prize)
    warn(world, parent, hero, quest, prize)
    defies(world, hero, quest)
    grab_and_help(world, parent, hero, quest)
    world.para()
    gear = compromise(world, parent, hero, quest, prize)
    if gear:
        accept(world, parent, hero, quest, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, quest=quest, gear=gear, setting=setting, resolved=gear is not None)
    return world


SETTINGS = {
    "splash_pad": Setting(place="the splash pad", affords={"scrub"}),
}

QUESTS = {
    "scrub": Quest(
        id="scrub",
        verb="scrub the sticky tiles",
        gerund="scrubbing the sticky tiles",
        rush="run across the wet tiles",
        mess="wet",
        soil="wet and slippery",
        zone={"feet"},
        keyword="scrub",
        tags={"scrub", "clean", "water"},
    ),
}

PRIZES = {
    "socks": Prize(label="socks", phrase="fresh striped socks", type="socks", region="feet", plural=True),
    "sandals": Prize(label="sandals", phrase="bright little sandals", type="sandals", region="feet", plural=True),
    "shirt": Prize(label="shirt", phrase="a clean yellow shirt", type="shirt", region="torso"),
}

GEAR = [
    Gear(id="boots", label="rain boots", covers={"feet"}, guards={"wet"}, prep="put on rain boots first", tail="put on the rain boots"),
    Gear(id="apron", label="an apron", covers={"torso"}, guards={"wet"}, prep="put on an apron first", tail="put on the apron"),
]

GIRL_NAMES = ["Mina", "Lina", "Tia", "Nora", "Ada"]
BOY_NAMES = ["Owen", "Ezra", "Finn", "Theo", "Luca"]
TRAITS = ["gentle", "cheerful", "curious", "helpful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = QUESTS[qid]
            for pid, p in PRIZES.items():
                if p.region in q.zone:
                    combos.append((place, qid, pid))
    return combos


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, quest, prize = f["hero"], f["parent"], f["quest"], f["prize"]
    return [
        f'Write a heartwarming story about a child named {hero.id} and a {quest.keyword.capitalize()} Quest at a splash pad.',
        f"Tell a gentle story where {hero.id} wants to {quest.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.label}.",
        f'Write a small story that includes the word "scrub" and ends with a child and grown-up helping each other at the splash pad.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, quest, prize = f["hero"], f["parent"], f["quest"], f["prize"]
    qa = [
        QAItem(
            question=f"Who wanted to finish the {quest.keyword.capitalize()} Quest at the splash pad?",
            answer=f"{hero.id} wanted to finish the {quest.keyword.capitalize()} Quest, and {hero.pronoun('possessive')} {parent.label} stayed close to help.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to {quest.verb.split(' ',1)[0]}?",
            answer=f"{hero.id} was trying to {quest.verb} while keeping {hero.pronoun('possessive')} {prize.label} safe and clean.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label.capitalize()} worried because the {prize.label} could get {quest.soil} during the Quest at the splash pad.",
        ),
    ]
    if f.get("gear") is not None:
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help with the Quest?",
            answer=f"It helped {hero.id} join the Quest without ruining {hero.pronoun('possessive')} {prize.label}, so the job could stay kind and calm.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and happy, because {hero.pronoun().capitalize()} got to help and the splash pad looked cleaner at the end.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a splash pad?",
            answer="A splash pad is a play place with water that sprays or splashes from the ground, so children can run and play in cool water.",
        ),
        QAItem(
            question="What does scrub mean?",
            answer="To scrub means to rub something hard enough to help wash off dirt or sticky spots.",
        ),
        QAItem(
            question="Why do people clean a place together?",
            answer="People clean together so the work gets done faster and everyone can enjoy the place afterward.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="splash_pad", quest="scrub", prize="socks", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="splash_pad", quest="scrub", prize="sandals", name="Owen", gender="boy", parent="father", trait="helpful"),
    StoryParams(place="splash_pad", quest="scrub", prize="shirt", name="Nora", gender="girl", parent="mother", trait="curious"),
]


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection(quest: Quest, prize: Prize) -> str:
    return f"(No story: the {quest.keyword.capitalize()} Quest would not reasonably threaten {prize.label}.)"


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

prize_at_risk(Q,P) :- quest(Q), splashes(Q,R), worn_on(P,R).
protects(G,Q,P) :- gear(G), prize_at_risk(Q,P), guards(G,M), quest_mess(Q,M), covers(G,R), worn_on(P,R), splashes(Q,R).
has_fix(Q,P) :- protects(_,Q,P).
valid(Place,Q,P) :- affords(Place,Q), prize_at_risk(Q,P), has_fix(Q,P).
valid_story(Place,Q,P,G) :- valid(Place,Q,P), wears(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_mess", qid, q.mess))
        for r in sorted(q.zone):
            lines.append(asp.fact("splashes", qid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        lines.append(asp.fact("wears", "girl", pid))
        lines.append(asp.fact("wears", "boy", pid))
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="Heartwarming splash pad Quest story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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
        print(f"{len(triples)} compatible (place, quest, prize) combos ({len(stories)} with gender):\n")
        for place, q, p in triples:
            genders = sorted(g for (pl, qq, pp, g) in stories if (pl, qq, pp) == (place, q, p))
            print(f"  {place:10} {q:8} {p:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
