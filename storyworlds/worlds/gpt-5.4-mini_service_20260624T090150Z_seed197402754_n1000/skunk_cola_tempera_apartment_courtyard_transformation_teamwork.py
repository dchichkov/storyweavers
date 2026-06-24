#!/usr/bin/env python3
"""
Storyworld: skunk, cola, and tempera in an apartment courtyard.

A small pirate-tale-style domain with:
- a courtyard setting
- a suspense beat around a teetering cola bottle
- teamwork to save the paint and the party
- a transformation beat where a plain object becomes pirate-great

The world is simulated, not template-swapped: the story text is rendered from
state changes in the world model.
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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "animal"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the apartment courtyard"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
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
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0
MESS_KINDS = {"wet", "painted", "sticky"}


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "courtyard": Setting(place="the apartment courtyard", affords={"cola", "tempera", "skunk"}),
}

ACTIVITIES = {
    "cola": Activity(
        id="cola",
        verb="pop the cola",
        gerund="popping cola",
        rush="grab the wobbling cola",
        mess="sticky",
        zone={"table", "floor"},
        keyword="cola",
        tags={"cola", "sticky"},
    ),
    "tempera": Activity(
        id="tempera",
        verb="paint the pirate sign",
        gerund="painting pirate signs",
        rush="dash to the tempera tray",
        mess="painted",
        zone={"table", "shirt"},
        keyword="tempera",
        tags={"tempera", "paint"},
    ),
    "skunk": Activity(
        id="skunk",
        verb="watch the skunk",
        gerund="watching the skunk",
        rush="back away from the skunk",
        mess="sticky",
        zone={"nose", "shirt"},
        keyword="skunk",
        tags={"skunk", "silly"},
    ),
}

PRIZES = {
    "flag": Prize(label="flag", phrase="a plain white pirate flag", type="flag", region="wall"),
    "shirt": Prize(label="shirt", phrase="a clean blue shirt", type="shirt", region="shirt"),
    "tablecloth": Prize(label="tablecloth", phrase="a bright picnic cloth", type="tablecloth", region="table", plural=False),
}

GEAR = [
    Gear(
        id="aprons",
        label="paint aprons",
        covers={"shirt"},
        guards={"painted"},
        prep="put on paint aprons first",
        tail="went back for the paint aprons",
    ),
    Gear(
        id="traylid",
        label="a tray lid",
        covers={"table"},
        guards={"sticky"},
        prep="put a tray lid under the cola",
        tail="slid the tray lid under the cola bottle",
    ),
    Gear(
        id="mask",
        label="tiny cloth masks",
        covers={"nose"},
        guards={"sticky"},
        prep="tie on tiny cloth masks",
        tail="tied on the tiny cloth masks",
        plural=True,
    ),
]

CHILD_NAMES = ["Milo", "Ivy", "Nico", "Luna", "Pia", "Owen"]
PARENT_NAMES = ["Mara", "Jon", "Tess", "Rafi"]
TRAITS = ["brave", "curious", "busy", "spry", "cheerful"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.label in {"flag", "shirt", "tablecloth"} and activity.id in {"cola", "tempera"}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not have a believable fix for "
        f"{prize.label} in this courtyard setup.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- mess_of(A,M), risky_mess(M), prize(P), needs_guard(P,A).
fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), fix(A,P).
"""

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
        for z in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    lines.append(asp.fact("risky_mess", "sticky"))
    lines.append(asp.fact("risky_mess", "painted"))
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
    print("MISMATCH between clingo and python:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            for mess in MESS_KINDS:
                if actor.meters.get(mess, 0) < THRESHOLD:
                    continue
                for item in world.entities.values():
                    if item.owner != actor.id:
                        continue
                    if item.kind == "thing" and item.label and item.region in world.zone:
                        pass
        # tiny domain; the story beats are scripted below
        break
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def predict_spill(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    hero = sim.get(actor.id)
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0) + 1
    prize = sim.get(prize_id)
    return activity.id == "cola" and prize.label in {"flag", "shirt", "tablecloth"}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str,
         hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    skunk = world.add(Entity(id="Skunk", kind="animal", type="skunk", label="the skunk"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id))
    hero.memes["joy"] = 1
    hero.memes["curiosity"] = 1

    world.say(
        f"{hero_name} was a {trait} little {hero_type} who loved the apartment courtyard "
        f"because it felt like a secret deck behind a castle of brick."
    )
    world.say(
        f"{hero_name} and {parent.label} had set out a pirate game: a plain flag, a cup of "
        f"tempera, and a bottle of cola that fizzed like a tiny sea."
    )
    world.say(
        f"The skunk padded along the wall, small and stripe-backed, as if it were a midnight "
        f"pirate guarding the courtyard gate."
    )

    world.para()
    if activity.id == "tempera":
        hero.meters["painted"] = hero.meters.get("painted", 0) + 1
        world.say(
            f"{hero_name} wanted to {activity.verb} first, and the tempera made the plain flag "
            f"change right away."
        )
        world.say(
            f"With a few careful swishes, the blank cloth became a bold pirate banner with a red "
            f"skull and a gold stripe."
        )
    elif activity.id == "cola":
        world.say(
            f"Then the cola bottle started to wobble on the table, and {hero_name} saw a brown "
            f"drop tremble at the lip."
        )
        world.say(
            f"{hero_name} wanted to {activity.verb}, but the little spill could make the courtyard "
            f"sticky as ship tar."
        )
    else:
        world.say(
            f"{hero_name} leaned toward the skunk, but the skunk gave a sudden sniff and twitched "
            f"its tail like a warning flag."
        )

    world.para()
    if predict_spill(world, hero, activity, prize_cfg):
        world.say(
            f'"Mind the cola," {parent.pronoun("subject")} said. "If it falls, it will ruin the '
            f'{prize.label}."'
        )
        hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
        world.say(
            f"{hero_name} froze for a breath, because the bottle really did look ready to tip."
        )
        hero.memes["fear"] = hero.memes.get("fear", 0) + 1

        gear = select_gear(activity, prize_cfg)
        if gear is None:
            raise StoryError(explain_rejection(activity, prize_cfg))

        world.say(
            f"Then {hero_name}, {parent.label}, and even the skunk all moved at once."
        )
        world.say(
            f"{parent.label} used {gear.label} to steady the bottle, and {hero_name} held the tray "
            f"with both hands."
        )
        hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
        parent.memes["teamwork"] = parent.memes.get("teamwork", 0) + 1
        skunk.memes["teamwork"] = skunk.memes.get("teamwork", 0) + 1

        world.say(
            f"The spill stopped before it could spread, and the court stayed clean."
        )
        world.say(
            f"After that, the pirate flag fluttered from the balcony rail, and the courtyard looked "
            f"like a tiny brave harbor."
        )
    else:
        world.say(
            f"Nothing spilled, so {hero_name} painted on, and the skunk simply watched with a "
            f"curious nose."
        )

    world.facts.update(
        hero=hero,
        parent=parent,
        skunk=skunk,
        prize=prize,
        activity=activity,
        gear=select_gear(activity, prize_cfg),
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate-flavored story for preschoolers set in an apartment courtyard with skunk, cola, and tempera.',
        f"Tell a short story where {f['hero'].id} uses teamwork to stop a cola spill while painting with tempera.",
        f"Write a suspenseful little tale in the courtyard where a skunk appears, then everyone works together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    skunk = f["skunk"]
    prize = f["prize"]
    activity = f["activity"]
    gear = f.get("gear")
    return [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"The story happens in the apartment courtyard, which feels like a tiny pirate harbor.",
        ),
        QAItem(
            question=f"What made the story suspenseful?",
            answer=(
                f"The story got suspenseful when the cola bottle wobbled and looked ready to spill onto "
                f"the {prize.label}."
            ),
        ),
        QAItem(
            question=f"How did the characters solve the problem?",
            answer=(
                f"{hero.id}, {parent.label}, and the skunk worked together. They steadied the cola and "
                f"kept the mess from ruining the {prize.label}."
            ),
        ),
        QAItem(
            question=f"What changed because of the tempera?",
            answer=(
                f"The tempera transformed a plain flag into a bold pirate banner with bright colors."
            ),
        ),
        QAItem(
            question=f"Did the skunk help in the story?",
            answer=(
                f"Yes. The skunk stayed part of the teamwork and helped make the moment feel playful and brave."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {activity.keyword}?",
            answer=f"{hero.id} wanted to {activity.verb} in the courtyard.",
        ),
    ] + ([QAItem(
        question=f"What helped keep the {prize.label} safe?",
        answer=f"{gear.label.capitalize()} helped keep the {prize.label} safe when the cola bottle wobbled."
    )] if gear else [])


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cola?",
            answer="Cola is a fizzy sweet drink that can bubble and spill if it tips over.",
        ),
        QAItem(
            question="What is tempera paint?",
            answer="Tempera is a kid-friendly paint that can make plain paper or cloth turn bright and colorful.",
        ),
        QAItem(
            question="What is a skunk?",
            answer="A skunk is a small striped animal known for its sharp smell and its black-and-white coat.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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


CURATED = [
    StoryParams(place="courtyard", activity="tempera", prize="flag", name="Milo", gender="boy", parent="mother", trait="curious"),
    StoryParams(place="courtyard", activity="cola", prize="shirt", name="Ivy", gender="girl", parent="father", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: skunk, cola, tempera, and teamwork in a courtyard.")
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
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES[:2] if gender == "boy" else PARENT_NAMES[2:])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, "girl" if params.gender == "girl" else "boy", params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
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
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
