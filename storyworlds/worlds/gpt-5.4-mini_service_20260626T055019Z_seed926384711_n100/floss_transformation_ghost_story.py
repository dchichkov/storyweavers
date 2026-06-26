#!/usr/bin/env python3
"""
storyworlds/worlds/floss_transformation_ghost_story.py
======================================================

A small ghost-story world where a child and a friendly ghost use floss to
transform something spooky and dusty into something bright, clear, and safe.

Seed premise:
- A child finds a little spool of floss in an old house.
- The house is full of cobwebs, and something hidden is stuck behind them.
- A friendly ghost warns that the wrong pull could make the room feel scarier.
- With patience, the child uses floss to transform the dusty tangle into a
  clean opening that reveals a gentle surprise.

This world is deliberately tiny and constraint-checked:
- The story is driven by a live world model.
- The central feature is transformation.
- The style aims for a child-friendly ghost story: moody, but kind.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "shine": 0.0, "tension": 0.0, "fear": 0.0, "wonder": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "bravery": 0.0, "calm": 0.0, "spook": 0.0}

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
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    mess: str
    transforms_from: str
    transforms_to: str
    zone: set[str]
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
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
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
        import copy as _copy

        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.zone = set(self.zone)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dust"] < THRESHOLD:
            continue
        sig = ("transform", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["shine"] += 1
        actor.meters["dust"] = max(0.0, actor.meters["dust"] - 1)
        actor.memes["wonder"] += 1
        out.append(f"A soft glow clung to {actor.id}.")
    return out


def _r_scare(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["fear"] < THRESHOLD:
            continue
        sig = ("scare", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["tension"] += 1
        out.append(f"The room felt colder for a moment.")
    return out


CAUSAL_RULES = [
    _r_transform,
    _r_scare,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "transformed": bool(prize and prize.meters["shine"] >= THRESHOLD),
        "tension": sum(e.meters["tension"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["dust"] += 1
    actor.memes["bravery"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.type_traits if t != "little"), "quiet")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved the hush of old rooms."
    )


def loves_floss(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} found a tiny spool of floss and thought it looked almost magical."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, because {activity.gerund} might change the spooky room into something kind."
    )


def arrive(world: World, hero: Entity, ghost: Entity, activity: Activity) -> None:
    world.say(
        f"One moonlit night, {hero.id} and the ghost drifted into {world.setting.place}."
    )
    world.say(
        f"The air felt {world.setting.mood}, and the cobwebs swayed like pale lace."
    )


def warn(world: World, ghost: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["transformed"]:
        return False
    world.say(
        f'"Careful," the ghost whispered. "If you tug too hard, the web will only get scarier."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"{hero.id} swallowed hard, but the floss still felt brave in {hero.pronoun('possessive')} hand."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tried to {activity.rush}, then stopped when the old boards creaked."
    )


def offer_help(world: World, ghost: Entity, hero: Entity, gear: Optional[Gear]) -> Optional[Gear]:
    if gear is None:
        return None
    ghost.memes["calm"] += 1
    world.say(
        f"The ghost floated closer and said, \"Let's use the gentle kind first.\""
    )
    world.say(
        f'"We can {gear.prep} and do it slowly."'
    )
    return gear


def accept(world: World, hero: Entity, ghost: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} nodded and smiled. Together they {gear.tail}."
    )
    _do_activity(world, hero, activity, narrate=False)
    prize.meters["shine"] += 1
    prize.meters["dust"] = 0.0
    world.say(
        f"The floss pulled the gray cobweb away in one clean thread, and the hidden thing behind it changed from dusty to bright."
    )
    world.say(
        f"In the opening, a little silver music box appeared, and it gave one tiny chime instead of a fright."
    )
    world.say(
        f"{hero.id} laughed, and even the ghost looked less spooky in the shining light."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.type_traits = ["little", "curious", "careful"]
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost"))
    prize = world.add(Entity(
        id="hidden_item",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=ghost.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_floss(world, hero, activity)
    world.say(f"{hero.id} was carrying a small {prize.label} wrapped in paper, as if it were a secret.")
    world.para()
    arrive(world, hero, ghost, activity)
    warn(world, ghost, hero, activity, prize)
    defies(world, hero, activity)
    world.say(f"The ghost lifted one pale finger and pointed to the web.")
    world.para()
    gear = offer_help(world, ghost, hero, select_gear(activity, prize))
    if gear is None:
        raise StoryError("No gentle way exists for this floss story.")
    accept(world, hero, ghost, activity, prize, gear)

    world.facts.update(
        hero=hero,
        ghost=ghost,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=True,
    )
    return world


SETTINGS = {
    "attic": Setting(place="the attic", mood="cold and whispery", affords={"floss"}),
    "hallway": Setting(place="the hallway", mood="quiet and blue", affords={"floss"}),
    "cellar": Setting(place="the cellar", mood="damp and still", affords={"floss"}),
}

ACTIVITIES = {
    "floss": Activity(
        id="floss",
        verb="use the floss",
        gerund="using the floss",
        rush="reach into the web",
        keyword="floss",
        mess="dust",
        transforms_from="dusty cobweb",
        transforms_to="bright opening",
        zone={"torso"},
        tags={"floss", "ghost", "transformation"},
    )
}

PRIZES = {
    "music_box": Prize(
        label="music box",
        phrase="a tiny silver music box",
        type="music_box",
        region="torso",
    ),
    "mirror": Prize(
        label="mirror",
        phrase="an old round mirror",
        type="mirror",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="lamp",
        label="a small lamp",
        prep="turn on the small lamp first",
        tail="turned on the small lamp",
        covers={"torso"},
        guards={"dust"},
    ),
    Gear(
        id="gloves",
        label="soft gloves",
        prep="put on soft gloves first",
        tail="put on the soft gloves",
        covers={"torso"},
        guards={"dust"},
        plural=True,
    ),
]

GIRL_NAMES = ["Mina", "Nora", "Luna", "Ivy", "Elsie"]
BOY_NAMES = ["Theo", "Finn", "Owen", "Bram", "Levi"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a short ghost story for a young child that includes the word "{activity.keyword}" and ends with a transformation.',
        f"Tell a gentle spooky story where {hero.id} uses {activity.verb} to reveal {prize.phrase} in {f['setting'].place}.",
        f"Write a child-friendly ghost story about a hidden {prize.label}, a quiet room, and a kind surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ghost, prize, activity = f["hero"], f["ghost"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} use to change the spooky cobweb?",
            answer=f"{hero.id} used floss, carefully and slowly, so the cobweb could change without getting worse.",
        ),
        QAItem(
            question=f"Who warned {hero.id} about pulling too hard in {f['setting'].place}?",
            answer=f"The friendly ghost warned {hero.id} to be gentle, because a hard tug could make the room feel scarier.",
        ),
        QAItem(
            question=f"What was hidden behind the dusty web?",
            answer=f"Behind the dusty web was {prize.phrase}, and it appeared after the floss made a clean opening.",
        ),
        QAItem(
            question=f"How did the room change by the end of the story?",
            answer=f"The room changed from dusty and spooky to bright and calm, because the floss transformed the cobweb into a clear opening.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is floss?",
            answer="Floss is a thin thread people use carefully to clean tiny spaces or pull away light tangles.",
        ),
        QAItem(
            question="Why do cobwebs look spooky?",
            answer="Cobwebs can look spooky because they are pale, tangled, and quiet, especially in an old room at night.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a different form or becomes very different from before.",
        ),
        QAItem(
            question="Why can a ghost story still be kind?",
            answer="A ghost story can be kind when the spooky parts lead to a safe surprise, a helper, or a happy ending.",
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
        m = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", activity="floss", prize="music_box", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="hallway", activity="floss", prize="mirror", name="Theo", gender="boy", parent="father"),
    StoryParams(place="cellar", activity="floss", prize="music_box", name="Luna", gender="girl", parent="mother"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
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
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            act = ACTIVITIES[act_id]
            for pr_id, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    out.append((place, act_id, pr_id))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="A child-friendly ghost story world about floss and transformation.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:8} {act:8} {prize:10} [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.activity} in {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
