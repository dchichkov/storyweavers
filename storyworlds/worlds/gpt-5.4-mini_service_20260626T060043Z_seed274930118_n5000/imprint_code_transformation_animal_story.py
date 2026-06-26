#!/usr/bin/env python3
"""
storyworlds/worlds/imprint_code_transformation_animal_story.py
==============================================================

A small animal-story world about an imprint, a code, and a gentle
transformation.

Seed premise:
- A young animal loves making an imprint.
- A grown-up worries that a coded mark, stamp, or trail will spoil something treasured.
- They discover a safer way, and the child changes from frustrated to delighted.

The domain is deliberately small and constraint-checked:
- one setting
- one activity
- one prized object
- one protective or transforming helper
- state-driven emotion and physical meters
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    protective: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


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
class Helper:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    transform_note: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
        return any(g.protective and region in getattr(g, "covers", set()) for g in self.worn_items(actor))

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.weather = self.weather
        w.fired = set(self.fired)
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_mark_spoil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("imprint", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.id == "helper":
                continue
            if item.meters.get("messy", 0.0) >= THRESHOLD:
                continue
            if item.id in {"notebook"} and "paper" not in world.zone:
                continue
            sig = ("spoil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["messy"] = item.meters.get("messy", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got smudged.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("worry", 0.0) >= THRESHOLD and actor.memes.get("brave", 0.0) >= THRESHOLD:
            sig = ("calm", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["worry"] = 0.0
            actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("mark_spoil", _r_mark_spoil),
    Rule("calm", _r_calm),
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
                produced.extend(s for s in sents if s != "__calm__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_helper(activity: Activity, prize: Prize) -> Optional[Helper]:
    for h in HELPERS:
        if activity.mess in h.guards and prize.region in h.covers:
            return h
    return None


def predict_spoil(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return prize.meters.get("dirty", 0.0) >= THRESHOLD or prize.meters.get("messy", 0.0) >= THRESHOLD


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["imprint"] = actor.meters.get("imprint", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    adj = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {adj} {hero.type} who loved tiny discoveries.")


def loves_activity(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {act.gerund}, because every mark felt like a secret message.")


def arrives(world: World, hero: Entity, parent: Entity, act: Activity) -> None:
    where = "inside" if world.setting.indoor else "outside"
    day = "One day"
    world.say(f"{day}, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(f"The air felt {('soft and still' if world.setting.indoor else 'fresh and open')}, and {hero.id} was ready to play {where}.")


def wants(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {act.verb} right away.")


def warn(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> bool:
    if not predict_spoil(world, hero, act, prize.id):
        return False
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.facts["predicted_soil"] = act.soil
    world.say(f'"If you do that, your {prize.label} will get {act.soil}," {parent.label} said.')
    return True


def defy(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"{hero.id} blinked at the warning and tried to {act.rush} anyway.")


def gentle_grab(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["held"] = hero.memes.get("held", 0.0) + 1
    world.say(f"But {hero.pronoun('possessive')} {parent.label} held {hero.pronoun('possessive')} paw and stayed calm.")


def compromise(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> Optional[Helper]:
    helper_def = select_helper(act, prize)
    if helper_def is None:
        return None
    helper = world.add(Entity(
        id=helper_def.id,
        kind="thing",
        type="helper",
        label=helper_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        plural=helper_def.plural,
    ))
    helper.worn_by = hero.id
    if predict_spoil(world, hero, act, prize.id):
        helper.worn_by = None
        del world.entities[helper.id]
        return None
    world.say(f'{parent.label.capitalize()} smiled. "{helper_def.prep}," {parent.label} said.')
    return helper


def accept(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity, helper: Helper) -> None:
    hero.memes["brave"] = hero.memes.get("brave", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.id}'s ears lifted, and {hero.id} hugged {hero.pronoun('possessive')} {parent.label}.")
    world.say(
        f'"Yes!" {hero.id} said. "{helper.transform_note}" '
        f"After that, {hero.id} was {act.gerund}, {prize.label} stayed clean, and "
        f"the small code on the card looked like a happy little path."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "fox",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["curious", "stubborn"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=prize_cfg.plural,
    ))

    intro(world, hero)
    loves_activity(world, hero, activity)
    world.say(f"{hero.id} had a favorite {prize.label} to carry, and {hero.id} loved how it shone.")
    world.para()

    arrives(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defy(world, hero, activity)
    gentle_grab(world, parent, hero)

    world.para()
    helper = compromise(world, parent, hero, activity, prize)
    if helper:
        accept(world, parent, hero, activity, prize, helper)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, helper=helper, resolved=helper is not None)
    return world


SETTINGS = {
    "garden": Setting("the garden", False, {"stamp", "trail"}),
    "forest": Setting("the forest", False, {"stamp", "trail"}),
    "porch": Setting("the porch", False, {"stamp"}),
    "playroom": Setting("the playroom", True, {"stamp"}),
}

ACTIVITIES = {
    "stamp": Activity(
        id="stamp",
        verb="stamp the clay with a paw print",
        gerund="stamping paw prints",
        rush="rush to the clay mat",
        mess="mud",
        soil="muddy",
        zone={"paws"},
        weather="sunny",
        keyword="imprint",
        tags={"imprint", "clay"},
    ),
    "trail": Activity(
        id="trail",
        verb="follow the dotted code trail",
        gerund="following code trails",
        rush="dash along the marked path",
        mess="ink",
        soil="ink-streaked",
        zone={"paws", "tail"},
        weather="sunny",
        keyword="code",
        tags={"code", "trail"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a tiny picture",
        gerund="painting tiny pictures",
        rush="grab the paint pots",
        mess="paint",
        soil="paint-spotted",
        zone={"paws", "fur"},
        weather="",
        keyword="code",
        tags={"code", "paint"},
    ),
}

PRIZES = {
    "ribbon": Prize("ribbon", "a bright ribbon", "ribbon", "tail"),
    "blanket": Prize("blanket", "a soft blanket", "blanket", "back"),
    "shirt": Prize("shirt", "a clean shirt", "shirt", "fur"),
}

HELPERS = [
    Helper(
        id="apron",
        label="a tiny apron",
        covers={"fur", "back"},
        guards={"paint"},
        prep="put on a tiny apron first",
        tail="took off the apron after the picture",
        transform_note="The apron turned the messy paint into neat spots on paper instead of on fur.",
    ),
    Helper(
        id="boots",
        label="little mud boots",
        covers={"paws"},
        guards={"mud"},
        prep="put on little mud boots first",
        tail="stomped back happily in the mud boots",
        transform_note="The boots changed the muddy stamp into a clean paw print on the clay.",
    ),
    Helper(
        id="card",
        label="a code card",
        covers={"paws"},
        guards={"ink"},
        prep="hold a code card over the trail",
        tail="walked the trail with the code card",
        transform_note="The code card made the dotted path feel like a game and kept the ink off the blanket.",
    ),
]

NAMES = {
    "fox": ["Mina", "Pip", "Tilly", "Nell", "Ruby"],
    "rabbit": ["Bun", "Miri", "Tobi", "Luna", "Holly"],
    "bear": ["Tad", "Ollie", "Momo", "Bram", "Nico"],
}

TRAITS = ["curious", "playful", "brave", "gentle", "shy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if activity_risk(act, prize) and select_helper(act, prize):
                    out.append((place, aid, pid))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    species: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short animal story for a preschooler about an "{act.keyword}" and a "{prize.label}".',
        f"Tell a gentle story where {hero.id}, a little {hero.type}, wants to {act.verb} but {parent.label} worries about {prize.phrase}.",
        f"Write a story about an imprint, a code, and a kinder way to play at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    helper = f.get("helper")
    qs = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the {prize.label}?",
            answer=f"{parent.label} worried because {prize.label} could get {act.soil} if {hero.id} kept playing that way.",
        ),
        QAItem(
            question=f"What helped {hero.id} play more safely?",
            answer=f"{helper.label} helped, and it changed the play so the {prize.label} stayed clean.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and braver after the grown-up found a safer plan.",
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an imprint?",
            answer="An imprint is a mark left by something pressing into a soft surface, like a paw in mud or a stamp in clay.",
        ),
        QAItem(
            question="What is a code?",
            answer="A code is a set of signs or symbols that stands for a message or a rule.",
        ),
        QAItem(
            question="Why can mud be messy?",
            answer="Mud is soft and wet, so it can stick to paws, clothes, and blankets.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
protects(H,A,P) :- helper(H), prize_at_risk(A,P), guards(H,M), mess_of(A,M), covers(H,R), worn_on(P,R).
valid(P,A,Pr) :- setting(P), affords(P,A), prize_at_risk(A,Pr), protects(_,A,Pr).
valid_story(P,A,Pr,G) :- valid(P,A,Pr), wears(G,Pr).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, c))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(valid_combos_asp())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    if a - b:
        print(" only in asp:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about imprint, code, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--species", choices=list(NAMES))
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (activity_risk(act, pr) and select_helper(act, pr)):
            raise StoryError("No story: that activity would not honestly threaten the prize, or no helper can fix it.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    place, activity, prize = rng.choice(sorted(combos))
    species = args.species or rng.choice(list(NAMES))
    name = args.name or rng.choice(NAMES[species])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, species=species, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.species, [params.trait], params.parent)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("garden", "stamp", "shirt", "Mina", "fox", "mother", "curious"),
    StoryParams("forest", "trail", "blanket", "Pip", "rabbit", "father", "brave"),
    StoryParams("playroom", "paint", "shirt", "Tad", "bear", "mother", "gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = valid_combos_asp()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} ({p.species})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
