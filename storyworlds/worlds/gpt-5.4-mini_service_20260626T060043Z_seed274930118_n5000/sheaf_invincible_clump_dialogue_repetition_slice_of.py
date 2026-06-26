#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sheaf_invincible_clump_dialogue_repetition_slice_of.py
===============================================================================================================================

A small slice-of-life storyworld about a child, a sheaf of papers, and one
annoying little clump that seems invincible until the family finds a gentle fix.

The seed image for this world is simple:
- A child has a sheaf of papers on the table.
- A clump of sticky stuff keeps getting in the way.
- The child and caregiver talk it through.
- Repetition is used for rhythm, comfort, and a real sense of effort.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

LOCATIONS = {
    "kitchen": {
        "place": "the kitchen table",
        "indoor": True,
        "details": [
            "The table was warm from the afternoon sun.",
            "A bowl, a spoon, and a folded towel waited nearby.",
        ],
        "affords": {"sort_papers", "knead_dough", "fix_clump"},
    },
    "studio": {
        "place": "the little art studio",
        "indoor": True,
        "details": [
            "The lamp made the paper edges glow softly.",
            "Crayons and pencils were lined up in a neat row.",
        ],
        "affords": {"sort_papers", "cut_shapes", "fix_clump"},
    },
    "porch": {
        "place": "the porch step",
        "indoor": False,
        "details": [
            "A breeze kept passing by and lifting the corners of the paper.",
            "The day felt quiet and ordinary in the best way.",
        ],
        "affords": {"sort_papers", "fold_boats", "fix_clump"},
    },
}

ACTIVITIES = {
    "sort_papers": {
        "verb": "sort the papers",
        "gerund": "sorting papers",
        "rush": "try to sweep the papers together too fast",
        "mess": "flutter",
        "soil": "all mixed up",
        "zone": {"table"},
        "keyword": "sheaf",
        "tags": {"paper", "home", "sheaf"},
    },
    "knead_dough": {
        "verb": "knead the dough",
        "gerund": "kneading dough",
        "rush": "press the dough with both hands",
        "mess": "sticky",
        "soil": "sticky and lumpy",
        "zone": {"hands", "table"},
        "keyword": "clump",
        "tags": {"food", "sticky", "clump"},
    },
    "cut_shapes": {
        "verb": "cut out paper shapes",
        "gerund": "cutting out shapes",
        "rush": "grab the scissors at once",
        "mess": "flutter",
        "soil": "scattered everywhere",
        "zone": {"table"},
        "keyword": "sheaf",
        "tags": {"paper", "art", "sheaf"},
    },
    "fold_boats": {
        "verb": "fold paper boats",
        "gerund": "folding paper boats",
        "rush": "crumple the pages into boats too quickly",
        "mess": "flutter",
        "soil": "wrinkled and messy",
        "zone": {"table", "hands"},
        "keyword": "sheaf",
        "tags": {"paper", "play", "sheaf"},
    },
    "fix_clump": {
        "verb": "smooth the clump away",
        "gerund": "working the clump loose",
        "rush": "poke at the clump and make it worse",
        "mess": "sticky",
        "soil": "still stuck",
        "zone": {"table", "hands"},
        "keyword": "clump",
        "tags": {"sticky", "cleaning", "clump"},
    },
}

ROLES = {
    "child": {
        "types": {"girl", "boy"},
        "names": {
            "girl": ["Mia", "Lena", "Ava", "June", "Nora", "Tia"],
            "boy": ["Owen", "Ben", "Eli", "Noah", "Theo", "Max"],
        },
        "traits": ["gentle", "curious", "patient", "busy", "quiet", "bright"],
    },
    "adult": {
        "types": {"mother", "father", "grandmother", "grandfather"},
        "names": {
            "mother": ["Mom", "Mara", "Rina"],
            "father": ["Dad", "Owen", "Paul"],
            "grandmother": ["Grandma", "Nana", "Iris"],
            "grandfather": ["Grandpa", "Henry", "Evan"],
        },
    },
}

PRIZES = {
    "sheaf": {
        "label": "sheaf of papers",
        "article": "a",
        "region": "table",
        "plural": False,
        "genders": {"girl", "boy"},
        "meter": "mixed",
        "story_word": "sheaf",
    },
    "clump": {
        "label": "clump of sticky dough",
        "article": "a",
        "region": "hands",
        "plural": False,
        "genders": {"girl", "boy"},
        "meter": "sticky",
        "story_word": "clump",
    },
}

GEAR = {
    "towel": {
        "label": "a clean towel",
        "covers": {"hands", "table"},
        "guards": {"sticky"},
        "prep": "put down a clean towel first",
        "tail": "laid out a clean towel",
    },
    "tray": {
        "label": "a big tray",
        "covers": {"table"},
        "guards": {"flutter"},
        "prep": "slide a big tray under the papers",
        "tail": "set out a big tray",
    },
    "clips": {
        "label": "paper clips",
        "covers": {"table"},
        "guards": {"flutter"},
        "prep": "use paper clips to hold the sheaf together",
        "tail": "used paper clips",
    },
}


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
            self.meters = {"sticky": 0.0, "flutter": 0.0, "work": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "patience": 0.0, "stuck": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother"}
        male = {"boy", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    location: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _repetition_line(phrase: str) -> str:
    return f"{phrase}. {phrase}."


def _apply_sticky(world: World) -> list[str]:
    out: list[str] = []
    for child in world.entities.values():
        if child.kind != "character":
            continue
        if child.meters["sticky"] < THRESHOLD:
            continue
        for thing in world.entities.values():
            if thing.kind != "thing" or thing.worn_by is not None:
                continue
            if thing.region != "table":
                continue
            sig = ("sticky", child.id, thing.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if thing.id == "sheaf":
                thing.meters["flutter"] += 1
            if thing.id == "clump":
                thing.meters["sticky"] += 1
            out.append(f"The little clump kept sticking to everything.")
    return out


def _apply_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    adult = world.facts.get("adult")
    if not child or not adult:
        return out
    if child.meters["sticky"] >= THRESHOLD and child.memes["stuck"] >= THRESHOLD:
        sig = ("worry", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            adult.memes["worry"] += 1
            out.append(f"That made {adult.label} worry a little.")
    return out


def _apply_fix(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    adult = world.facts.get("adult")
    gear = world.facts.get("gear")
    if not child or not adult or not gear:
        return out
    if child.meters["sticky"] < THRESHOLD:
        return out
    if not gear.protective:
        return out
    if "sticky" not in gear.covers and "table" not in gear.covers:
        return out
    sig = ("fix", child.id, gear.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["sticky"] = 0.0
    child.memes["stuck"] = 0.0
    child.memes["joy"] += 1
    adult.memes["patience"] += 1
    out.append(f"Then the mess finally loosened.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_apply_sticky, _apply_worry, _apply_fix):
            lines = fn(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    location: str
    activity: str
    prize: str
    child_type: str
    child_name: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc_id, loc in LOCATIONS.items():
        for act_id in loc["affords"]:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize["region"] in act["zone"]:
                    combos.append((loc_id, act_id, prize_id))
    return combos


def prize_at_risk(activity: dict, prize: dict) -> bool:
    return prize["region"] in activity["zone"]


def select_gear(activity: dict, prize: dict) -> Optional[dict]:
    for gear in GEAR.values():
        if prize["region"] in gear["covers"] and activity["mess"] in gear["guards"]:
            return gear
    return None


def reasonableness_gate(location: str, activity: str, prize: str) -> None:
    act = ACTIVITIES[activity]
    pr = PRIZES[prize]
    if not prize_at_risk(act, pr):
        raise StoryError("This scene would not create a real problem for the prize.")
    if select_gear(act, pr) is None:
        raise StoryError("There is no reasonable fix for that activity and prize.")


def build_world(params: StoryParams) -> World:
    world = World(params.location)
    loc = LOCATIONS[params.location]
    act = ACTIVITIES[params.activity]
    pr = PRIZES[params.prize]

    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child_name,
        meters={"sticky": 0.0, "flutter": 0.0, "work": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "patience": 0.0, "stuck": 0.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=params.adult_type,
        label=ROLES["adult"]["names"][params.adult_type][0],
        meters={"sticky": 0.0, "flutter": 0.0, "work": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "patience": 0.0, "stuck": 0.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type="thing",
        label=pr["label"],
        phrase=pr["label"],
        owner=child.id,
        caretaker=adult.id,
        region=pr["region"],
    ))
    clump = world.add(Entity(
        id="clump",
        type="thing",
        label="clump",
        phrase="a clump of sticky dough",
        region="table",
    ))
    sheaf = world.add(Entity(
        id="sheaf",
        type="thing",
        label="sheaf",
        phrase="a sheaf of papers",
        region="table",
    ))

    gear_def = select_gear(act, pr)
    gear = None
    if gear_def:
        gear = world.add(Entity(
            id="gear",
            type="thing",
            label=gear_def["label"],
            phrase=gear_def["label"],
            protective=True,
            covers=set(gear_def["covers"]),
        ))

    world.facts.update(
        child=child, adult=adult, prize=prize, clump=clump, sheaf=sheaf, gear=gear,
        activity=act, location=loc, gear_def=gear_def, params=params,
    )
    return world


def tell(world: World) -> None:
    child: Entity = world.facts["child"]
    adult: Entity = world.facts["adult"]
    prize: Entity = world.facts["prize"]
    act: dict = world.facts["activity"]
    loc: dict = world.facts["location"]
    gear_def = world.facts["gear_def"]

    world.say(f"{child.label} sat at {loc['place']} with a sheaf of papers.")
    world.say(f"{child.label} liked the tidy sound of pages sliding from one stack to another.")
    world.say(_repetition_line(f"{child.label} whispered, “Just one more page”"))
    world.say(f"On the table, a little clump of sticky dough kept rolling near the papers.")
    world.say(f"{child.label} frowned. “That clump is invincible,” {child.pronoun()} said.")
    world.say(f"{adult.label} looked over and smiled. “Invincible?” {adult.pronoun()} asked.")
    world.say(f'"It keeps coming back," {child.label} said. "I push it away, and it comes back."')
    world.para()

    world.say(loc["details"][0])
    world.say(f"{child.label} wanted to {act['verb']}, but the clump kept tugging at the whole moment.")
    world.say(f'"I can do it," {child.label} said. "I can do it. I can do it."')
    child.memes["stuck"] += 1
    child.meters["sticky"] += 1
    if prize.region == "table":
        prize.meters["flutter"] += 1
    propagate(world, narrate=True)

    world.say(f'{adult.label} said, "Let me help. We do not need to beat the clump. We only need to move it."')
    if gear_def:
        gear = world.facts["gear"]
        gear.worn_by = child.id
        world.say(f'{adult.label} added, "First, we will {gear_def["prep"]}."')
    else:
        world.say(f'{adult.label} added, "First, we will clear a little space."')
    world.para()

    world.say(f'{child.label} nodded. "Okay," {child.pronoun()} said. "Okay, okay."')
    world.say(f'{adult.label} used a careful finger to roll the clump onto the towel.')
    world.say(f"{child.label} laughed. “It moved! It moved!”")
    child.meters["sticky"] = 0.0
    child.memes["joy"] += 1
    adult.memes["patience"] += 1
    world.say(f"The sheaf stayed neat, and the clump was no longer in charge of the table.")
    world.say(f"{child.label} went back to the pages, one by one, one by one, until the work felt easy again.")
    world.say(f'{adult.label} said, "There. Not invincible after all."')
    child.memes["stuck"] = 0.0
    child.memes["joy"] += 1

    world.facts["resolved"] = True
    world.facts["gear"] = world.facts.get("gear")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    act = f["activity"]
    return [
        f'Write a gentle slice-of-life story for a young child about a {params.child_type} named {params.child_name}, a sheaf, and a clump.',
        f'Tell a small domestic story where "{act["keyword"]}" appears naturally and the characters talk about the problem.',
        "Write a short story with dialogue and a bit of repetition about tidying a table and solving a stubborn little mess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    prize: Entity = f["prize"]
    act: dict = f["activity"]
    gear_def = f.get("gear_def")
    out = [
        QAItem(
            question=f"What was {child.label} doing at {f['location']['place']}?",
            answer=f"{child.label} was sitting at {f['location']['place']} with a sheaf of papers and trying to {act['verb']}.",
        ),
        QAItem(
            question=f"What did {child.label} call the clump at first?",
            answer=f"{child.label} called it invincible because it kept coming back whenever {child.pronoun()} pushed it away.",
        ),
        QAItem(
            question=f"How did {adult.label} help?",
            answer=f"{adult.label} helped by staying calm, speaking gently, and moving the clump to a safer spot so the table could stay neat.",
        ),
    ]
    if gear_def:
        out.append(
            QAItem(
                question=f"What was the practical fix for the sticky problem?",
                answer=f"The practical fix was to {gear_def['prep']}, which gave the child a cleaner space and kept the sheaf in order.",
            )
        )
    out.append(
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the clump was out of the way, the sheaf stayed neat, and {child.label} went back to the pages with a happier feeling.",
        )
    )
    return out


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a sheaf?",
        answer="A sheaf is a bundle or stack of papers held together as one group.",
    ),
    QAItem(
        question="What does invincible mean?",
        answer="Invincible means something seems impossible to beat or stop.",
    ),
    QAItem(
        question="What is a clump?",
        answer="A clump is a small lump or bunch of things stuck together.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for loc_id, loc in LOCATIONS.items():
        lines.append(asp.fact("location", loc_id))
        if loc["indoor"]:
            lines.append(asp.fact("indoor", loc_id))
        for a in sorted(loc["affords"]):
            lines.append(asp.fact("affords", loc_id, a))
    for act_id, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", act_id))
        lines.append(asp.fact("mess_of", act_id, act["mess"]))
        for r in sorted(act["zone"]):
            lines.append(asp.fact("splashes", act_id, r))
    for prize_id, pr in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("worn_on", prize_id, pr["region"]))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        for c in sorted(gear["covers"]):
            lines.append(asp.fact("covers", gear_id, c))
        for g in sorted(gear["guards"]):
            lines.append(asp.fact("guards", gear_id, g))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
compatible(A,P,G) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid_story(L,A,P) :- affords(L,A), prize_at_risk(A,P), compatible(A,P,_).
#show valid_story/3.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set()
    for loc, act, prize in valid_combos():
        python_set.add((loc, act, prize))
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
    ap = argparse.ArgumentParser(description="A small slice-of-life storyworld about a sheaf and an invincible clump.")
    ap.add_argument("--location", choices=sorted(LOCATIONS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--child-type", choices=sorted(ROLES["child"]["types"]))
    ap.add_argument("--adult-type", choices=sorted(ROLES["adult"]["types"]))
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.location:
        combos = [c for c in combos if c[0] == args.location]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    location, activity, prize = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(sorted(ROLES["child"]["types"]))
    adult_type = args.adult_type or rng.choice(sorted(ROLES["adult"]["types"]))
    name = args.name or rng.choice(ROLES["child"]["names"][child_type])
    trait = rng.choice(ROLES["child"]["traits"])
    return StoryParams(
        location=location,
        activity=activity,
        prize=prize,
        child_type=child_type,
        child_name=name,
        adult_type=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params.location, params.activity, params.prize)
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({r for r, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(location="kitchen", activity="knead_dough", prize="clump", child_type="girl", child_name="Mia", adult_type="mother", trait="curious"),
    StoryParams(location="studio", activity="cut_shapes", prize="sheaf", child_type="boy", child_name="Theo", adult_type="father", trait="patient"),
    StoryParams(location="porch", activity="fold_boats", prize="sheaf", child_type="girl", child_name="June", adult_type="grandmother", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({r for r, *_ in world.fired})}")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
