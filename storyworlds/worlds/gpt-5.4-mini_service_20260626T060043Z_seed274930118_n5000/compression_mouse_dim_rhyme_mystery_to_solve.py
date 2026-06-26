#!/usr/bin/env python3
"""
storyworlds/worlds/compression_mouse_dim_rhyme_mystery_to_solve.py
===================================================================

A small slice-of-life story world about a child, a tiny mystery, and a careful
act of compression.

Seed idea:
- compression
- mouse-dim
- rhyme
- mystery to solve

Premise:
A child hears a faint little rhyme-like sound during an ordinary chore. The
sound comes from something mouse-dim and hidden in a soft pile. The grown-up
and child solve the mystery together, using a gentle compression-related fix
that keeps the little thing safe.

The domain stays small on purpose:
- one cozy setting
- one child hero
- one grown-up helper
- one tiny mystery object
- one careful action that could flatten it
- one safe compromise that solves the mystery
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
        for k in ["compression", "care", "tension", "joy", "curiosity", "mystery"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_compress(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["compression"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id and item.owner != actor.id:
                continue
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("compress", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["compression"] += 1
            item.meters["care"] += 1
            out.append(f"{item.label.capitalize()} got squished a little.")
    return out


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["tension"] < THRESHOLD:
            continue
        sig = ("tension", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["mystery"] += 1
        out.append(f"{actor.id} felt a little stuck and worried.")
    return out


CAUSAL_RULES = [Rule("compress", _r_compress), Rule("tension", _r_tension)]


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


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.risk in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "compressed": bool(prize and prize.meters["compression"] >= THRESHOLD),
        "tension": actor.memes["tension"],
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        return
    world.zone = set(action.zone)
    actor.meters["compression"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quiet")
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked small, tidy moments at home.")


def loves_rhyme(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved making up little rhymes while doing ordinary chores, "
        f"because the words felt bouncy and bright."
    )


def setup_scene(world: World, hero: Entity, parent: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"One afternoon, {hero.id} heard a tiny rhyme-like sound in {world.setting.place}."
    )
    world.say(
        f"It sounded so small and neat that {hero.pronoun('subject')} thought it might be a mouse-dim mystery."
    )
    world.say(
        f"{hero.id} wanted to {action.verb}, but {hero.pronoun('possessive')} {parent.type} noticed the soft pile was hiding something."
    )


def warn(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    pred = predict_mess(world, hero, action, prize.id)
    if not pred["compressed"]:
        return False
    world.facts["predicted_compression"] = action.risk
    world.say(
        f'"If you {action.verb}, your {prize.label} could get squashed," '
        f"{hero.pronoun('possessive')} {parent.type} said. "
        f'"Let us solve the mystery first."'
    )
    return True


def wonder(world: World, hero: Entity, action: Action) -> None:
    hero.memes["tension"] += 1
    world.say(f"{hero.id} paused, listening closely, and the little sound seemed even more mysterious.")


def search(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    world.say(
        f"Together they lifted the soft pile instead of pressing it down, and the mystery began to make sense."
    )


def reveal(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["mystery"] = 0
    world.say(
        f"Inside they found a mouse-dim wind-up mouse, tucked beside {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"It had been making the tiny rhyme sound all along, because its little spring was ticking against the fabric."
    )


def compromise(world: World, parent: Entity, hero: Entity, action: Action, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(action, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="thing",
            label=gear_def.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        )
    )
    gear.worn_by = hero.id
    if predict_mess(world, hero, action, prize.id)["compressed"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.type} smiled and said, '
        f'"How about we {gear_def.prep}?"'
    )
    return gear_def


def resolve(world: World, hero: Entity, parent: Entity, action: Action, prize: Entity, gear_def: Gear) -> None:
    hero.memes["tension"] = 0
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} nodded, and they used the {gear_def.label} to keep the pile neat without crushing the tiny mouse."
    )
    world.say(
        f"Then {hero.id} whispered a new rhyme, and the whole room felt calm again."
    )


SETTINGS = {
    "laundry room": Setting(place="the laundry room", indoors=True, affords={"press"}),
    "bedroom": Setting(place="the bedroom", indoors=True, affords={"press"}),
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"press"}),
}

ACTIVITIES = {
    "press": Action(
        id="press",
        verb="press the soft pile flat",
        gerund="pressing the soft pile flat",
        rush="push down on the blanket stack",
        risk="compression",
        zone={"table", "basket", "pile"},
        keyword="compression",
        tags={"compression", "rhyme", "mystery"},
    ),
}

PRIZES = {
    "mouse": Prize(
        label="mouse",
        phrase="a mouse-dim wind-up mouse",
        type="mouse",
        region="pile",
    ),
    "card": Prize(
        label="card",
        phrase="a tiny rhyme card",
        type="card",
        region="pile",
    ),
}

GEAR = [
    Gear(
        id="tray",
        label="a flat tray",
        covers={"pile"},
        guards={"compression"},
        prep="slide a flat tray under the soft pile first",
        tail="slid a flat tray under the pile",
    ),
    Gear(
        id="board",
        label="a thin board",
        covers={"pile"},
        guards={"compression"},
        prep="place a thin board on top first",
        tail="placed a thin board on top",
    ),
]

GIRL_NAMES = ["Mina", "Nora", "June", "Ari", "Lily", "Zoe"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Milo", "Finn", "Leo"]
TRAITS = ["careful", "curious", "gentle", "quiet", "cheerful"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region))
    world.facts.update(hero=hero, parent=parent, prize=prize, action=action, setting=setting)

    introduce(world, hero)
    loves_rhyme(world, hero)
    setup_scene(world, hero, parent, prize, action)
    world.para()
    warn(world, parent, hero, action, prize)
    wonder(world, hero, action)
    search(world, hero, parent, prize)
    reveal(world, hero, parent, prize)
    world.para()
    gear_def = compromise(world, parent, hero, action, prize)
    if gear_def:
        resolve(world, hero, parent, action, prize, gear_def)
    world.facts["gear"] = gear_def
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, action, prize = f["hero"], f["parent"], f["action"], f["prize"]
    return [
        f'Write a short slice-of-life story for a young child that includes the word "{action.keyword}".',
        f"Tell a gentle mystery story where {hero.id} hears a tiny sound in {world.setting.place} and solves it with {parent.type} help.",
        f"Write a story about compression, a mouse-dim surprise, and a happy rhyme at home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, action, prize = f["hero"], f["parent"], f["action"], f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} hear in {world.setting.place}?",
            answer=f"{hero.id} heard a tiny rhyme-like sound, which turned out to come from a mouse-dim wind-up mouse.",
        ),
        QAItem(
            question=f"Why did {parent.type} stop {hero.id} from pressing the pile right away?",
            answer=f"{parent.type} stopped {hero.id} because pressing the soft pile could have squashed {hero.pronoun('possessive')} {prize.label} before they solved the mystery.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.type} solve the mystery?",
            answer=f"They lifted the soft pile gently and found the mouse-dim wind-up mouse hiding inside.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help?",
                answer=f"It kept the soft pile neat while they looked, so they could solve the mystery without crushing the tiny mouse.",
            )
        )
    qa.append(
        QAItem(
            question=f"What was the ending like for {hero.id}?",
            answer=f"The ending was calm and cheerful, with {hero.id} whispering a new rhyme after the mystery was solved.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is compression?",
            answer="Compression is when something gets pressed or squeezed into a smaller space.",
        ),
        QAItem(
            question="What does mouse-dim mean?",
            answer="Mouse-dim means very tiny, about as small as a little mouse.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the ends, which can make a song or poem feel bouncy.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand at first, so you look for clues until it makes sense.",
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(action: Action, prize: Prize) -> str:
    if not prize_at_risk(action, prize):
        return "(No story: the action would not put the prize at risk, so there is no honest mystery to solve.)"
    return "(No story: no gear in this tiny world can protect that prize from compression.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: compression, mouse-dim mystery, and a little rhyme.")
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
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
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
prize_at_risk(A,P) :- zone(A,R), region(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,compression), covers(G,R), region(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
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
    import asp
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: clingo gate matches valid_combos() ({len(cset)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(cset - pset))
    print("only in python:", sorted(pset - cset))
    return 1


CURATED = [
    StoryParams(place="laundry room", activity="press", prize="mouse", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bedroom", activity="press", prize="card", name="Owen", gender="boy", parent="father", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
