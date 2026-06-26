#!/usr/bin/env python3
"""
A small comedy-leaning storyworld about a proud child, a wobbly treat, a tense
moment of suspense, and a happy ending that fixes the mess before the day is
ruined.

This script is self-contained except for the shared storyworld result containers
and the optional ASP helper.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wobble", "mess", "dirty", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "worry", "joy", "conflict", "relief", "suspense"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the backyard"
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.zone = set(self.zone)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.memes["suspense"] >= THRESHOLD and actor.meters["wobble"] >= THRESHOLD:
                sig = ("spill", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    actor.meters["mess"] += 1
                    out.append(f"The tray wobbled so hard that everyone gulped.")
                    changed = True
            if actor.meters["mess"] >= THRESHOLD:
                for item in world.worn_items(actor):
                    if item.protective or item.region not in world.zone:
                        continue
                    if world.covered(actor, item.region):
                        continue
                    sig = ("ruin", item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters["dirty"] += 1
                    out.append(f"{actor.id}'s {item.label} got splashed.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


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
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= THRESHOLD, "mess": actor.meters["mess"]}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That place cannot host that activity.")
    world.zone = set(activity.zone)
    actor.meters["wobble"] += 1
    actor.memes["suspense"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.label_word if hero.label_word else hero.type} "
        f"who felt very proud of {hero.pronoun('possessive')} own careful hands."
    )


def setup_love(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} had a proud smile because {hero.pronoun('subject')} could carry "
        f"{hero.pronoun('possessive')} {prize.label} just right."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} said the treat was for the picnic, "
        f"and {hero.id} wanted to {activity.verb} with it."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return
    hero.memes["worry"] += 1
    world.say(
        f'"If you do that, your {prize.label} could get {activity.soil}," '
        f"{parent.label_word} said, peeking at the tray."
    )


def suspense_beat(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"{hero.id} tried to stay proud, but the tray began to wobble like a silly little boat."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} started to {activity.rush}, and the picnic felt very quiet for a moment."
    )


def offer_fix(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    g.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        g.worn_by = None
        del world.entities[g.id]
        return None
    world.say(
        f'Then {parent.label_word} grinned and said, "How about we {gear.prep}?"'
    )
    return gear


def happy_ending(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["suspense"] = 0.0
    world.say(
        f"{hero.id} took a breath, put on {gear.label}, and felt the wobble settle down."
    )
    world.say(
        f"With the {gear.label}, {hero.id} could {activity.gerund} without ruining {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"By the time they reached the picnic, the near bad ending had become a funny story, and the {prize.label} stayed clean."
    )


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
    "backyard": Setting(place="the backyard", affords={"cupcakes", "jelly"}),
    "garden": Setting(place="the garden", affords={"cupcakes"}),
    "porch": Setting(place="the porch", affords={"jelly"}),
}

ACTIVITIES = {
    "cupcakes": Activity(
        id="cupcakes",
        verb="carry the cupcakes to the picnic",
        gerund="carrying the cupcakes",
        rush="dash for the picnic table",
        mess="squashed",
        soil="squashed and sticky",
        zone={"hands"},
        keyword="cupcakes",
        tags={"sweet", "messy"},
    ),
    "jelly": Activity(
        id="jelly",
        verb="carry the jelly bowl",
        gerund="carrying the jelly bowl",
        rush="hurry to the bench",
        mess="sloppy",
        soil="sloppy and shiny",
        zone={"hands"},
        keyword="jelly",
        tags={"sweet", "jiggly"},
    ),
}

PRIZES = {
    "tray": Prize(label="tray", phrase="a shiny party tray", type="tray", region="hands"),
    "bowls": Prize(label="bowls", phrase="two small dessert bowls", type="bowls", region="hands", plural=True),
}

GEAR = [
    Gear(
        id="carrier",
        label="a cupcake carrier",
        covers={"hands"},
        guards={"squashed", "sloppy"},
        prep="put the treats in the cupcake carrier first",
        tail="carefully carried the treats in the cupcake carrier",
    ),
]


GIRL_NAMES = ["Mina", "Lia", "Tia", "Nora", "Pia"]
BOY_NAMES = ["Owen", "Ned", "Milo", "Theo", "Pip"]
TRAITS = ["cheerful", "curious", "silly", "lively", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not reach the {prize.region}, so there is no honest suspense.)"
    return f"(No story: no gear in this world can protect that prize from {activity.keyword}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Proud comedy storyworld with suspense and a happy ending.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches those options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "proud"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    introduce(world, hero)
    setup_love(world, hero, parent, prize, activity)
    world.para()
    warn(world, parent, hero, activity, prize)
    suspense_beat(world, hero, activity)
    gear = offer_fix(world, parent, hero, activity, prize)
    if gear:
        happy_ending(world, hero, parent, activity, prize, gear)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, activity, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a funny story for a young child about proud {hero.id} trying to {activity.verb} with {prize.phrase}.',
        f"Tell a suspenseful but happy story where {hero.id}'s {parent.label_word} worries about the {prize.label} at {world.setting.place}.",
        f'Write a short comedy with a near bad ending, then a good fix, using the word "{activity.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Why was {hero.id} so careful with the {prize.label}?",
            answer=f"{hero.id} felt proud of carrying it, and {prize.label} was meant for the picnic, so {hero.pronoun('subject')} tried very hard not to drop it.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"The tray started to wobble while {hero.id} was trying to {activity.verb}, so everyone worried for a moment that the treats would get ruined.",
        ),
        QAItem(
            question=f"How did the family avoid the bad ending?",
            answer=f"They used {gear.label} so the treats stayed steady, and the wobbly moment turned into a happy ending instead.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does proud mean?",
            answer="Proud means feeling glad about something you did well or something you have, often with a big smile.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the tense feeling you get when you wonder what will happen next.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets fixed and things turn out well in the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- setting(Place), activity(A), prize(P), prize_at_risk(A,P), protects(_,A,P).
#show valid/3.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(p - a))
    print("asp only:", sorted(a - p))
    return 1


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


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
    StoryParams(place="backyard", activity="cupcakes", prize="tray", name="Mina", gender="girl", parent="mother", trait="proud"),
    StoryParams(place="garden", activity="cupcakes", prize="tray", name="Owen", gender="boy", parent="father", trait="silly"),
    StoryParams(place="porch", activity="jelly", prize="bowls", name="Nora", gender="girl", parent="mother", trait="curious"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
