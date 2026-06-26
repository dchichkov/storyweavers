#!/usr/bin/env python3
"""
A mythic storyworld about a child at a shrine-stall full of wonders, where
temptation, repetition, and an inner monologue lead to a bad ending.

The seed words are woven into the domain:
- subsequent
- stall
- galore

Style notes:
- Mythic, child-facing, concrete.
- Bad ending is deliberate and state-driven, not a joke.
- Inner monologue and repetition are modeled as part of the world.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {
                "dust": 0.0,
                "sticky": 0.0,
                "spilled": 0.0,
                "crowded": 0.0,
            }
        if not self.memes:
            self.memes = {
                "curiosity": 0.0,
                "greed": 0.0,
                "warning": 0.0,
                "shame": 0.0,
                "dread": 0.0,
                "resolve": 0.0,
                "repetition": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    inner_monologue: list[str] = field(default_factory=list)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.inner_monologue = list(self.inner_monologue)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shrine_market": Setting(place="the shrine market", affords={"offer_honey", "lift_lantern"}),
    "river_steps": Setting(place="the river steps", affords={"gather_pebbles"}),
    "echo_hall": Setting(place="the echo hall", affords={"speak_choir"}),
}

ACTIVITIES = {
    "offer_honey": Activity(
        id="offer_honey",
        verb="buy honey at the stall",
        gerund="buying honey at the stall",
        rush="rush to the stall and ask for more",
        mess="sticky",
        soil="sticky and spoiled",
        keyword="stall",
        tags={"stall", "honey", "sticky", "galore"},
    ),
    "lift_lantern": Activity(
        id="lift_lantern",
        verb="lift the sacred lantern",
        gerund="lifting the sacred lantern",
        rush="run toward the lantern",
        mess="dusty",
        soil="dusty and dim",
        keyword="lantern",
        tags={"lantern", "dust"},
    ),
    "gather_pebbles": Activity(
        id="gather_pebbles",
        verb="gather river pebbles",
        gerund="gathering river pebbles",
        rush="dash into the water",
        mess="wet",
        soil="wet and cold",
        keyword="pebbles",
        tags={"river", "water"},
    ),
    "speak_choir": Activity(
        id="speak_choir",
        verb="speak the choir words",
        gerund="speaking the choir words",
        rush="call out to the echoes again",
        mess="dusty",
        soil="dusty and hoarse",
        keyword="echo",
        tags={"echo", "voice"},
    ),
}

PRIZES = {
    "cloak": Prize(
        label="cloak",
        phrase="a white cloak with a red border",
        type="cloak",
        region="torso",
    ),
    "sandals": Prize(
        label="sandals",
        phrase="new sandals with bright cords",
        type="sandals",
        region="feet",
        plural=True,
    ),
    "tablet": Prize(
        label="tablet",
        phrase="a smooth wax tablet",
        type="tablet",
        region="hands",
    ),
    "wreath": Prize(
        label="wreath",
        phrase="a green wreath for the head",
        type="wreath",
        region="head",
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Sera", "Asha", "Lina", "Iris", "Tala"]
BOY_NAMES = ["Oren", "Davi", "Rian", "Kian", "Tomo", "Eli", "Jalen"]
TRAITS = ["bold", "quiet", "curious", "earnest", "restless", "bright"]


# ---------------------------------------------------------------------------
# Parameters
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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in {"torso", "feet", "hands", "head"} and (
        activity.mess in {"sticky", "dusty", "wet"}
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize):
                    combos.append((place, aid, pid))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly threaten {prize.label}, "
        f"so there is no mythic warning to tell.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok} for a {PRIZES[prize_id].label} tale.)"


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def predict_mess(world: World, hero: Entity, act: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(hero.id), act, narrate=False)
    prize = sim.get(prize_id)
    return {
        "soiled": prize.meters.get(act.mess, 0.0) >= THRESHOLD,
        "shame": sim.get(hero.id).memes.get("shame", 0.0),
    }


def do_activity(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    if act.id not in world.setting.affords:
        return
    actor.meters[act.mess] = actor.meters.get(act.mess, 0.0) + 1.0
    actor.memes["curiosity"] += 1.0
    if narrate:
        world.say(f"{actor.id} did {act.gerund}.")


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> None:
    world.say(
        f"In the old days, {hero.id} walked to {world.setting.place}, where the stalls stood in galore like a small row of bright shrines."
    )
    world.say(
        f"{hero.id} loved {act.gerund}, and {hero.pronoun('possessive')} {parent.type} had given {hero.pronoun('object')} {prize.phrase} for the feast."
    )


def inner_voice(world: World, hero: Entity, prize: Entity, act: Activity) -> None:
    thought1 = f"Maybe just one more glance, {hero.id} thought, and no harm will come."
    thought2 = f"Still, {hero.id} thought again: the {prize.label} is bright, the stall is full, the day is long."
    world.inner_monologue.extend([thought1, thought2])
    hero.memes["repetition"] += 1.0
    world.say(
        f"{hero.id} kept a private whisper in {hero.pronoun('possessive')} chest: “Maybe just one more look.”"
    )
    world.say(
        f"Again and again, the whisper returned: “Maybe just one more look.”"
    )


def warn(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, act, prize.id)
    if not pred["soiled"]:
        return False
    hero.memes["warning"] += 1.0
    world.say(
        f'"If you go on like this, your {prize.label} will be {act.soil}," '
        f"{parent.id} said."
    )
    return True


def stall(world: World, hero: Entity, act: Activity, prize: Entity) -> None:
    hero.memes["greed"] += 1.0
    world.say(
        f"But {hero.id} stalled beside the stall, and the waiting made {hero.pronoun('possessive')} heart grow louder than {hero.pronoun('possessive')} feet."
    )
    world.say(
        f"{hero.id} reached for the honey anyway, and the jars shook as if the gods themselves had breathed upon them."
    )


def subsequent_turn(world: World, hero: Entity, prize: Entity, act: Activity) -> None:
    prize.meters[act.mess] = prize.meters.get(act.mess, 0.0) + 1.0
    prize.meters["spilled"] += 1.0
    hero.memes["dread"] += 1.0
    world.say(
        f"Subsequent to that choice, the honey slipped where it should not have slipped."
    )
    world.say(
        f"It clung to the {prize.label} and to {hero.id}'s fingers, sticky as a curse."
    )


def bad_ending(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> None:
    hero.memes["shame"] += 1.0
    world.say(
        f"{hero.id} looked down at the ruined {prize.label} and felt the whole shrine-market grow quiet around {hero.pronoun('object')}."
    )
    world.say(
        f"No feast followed, no blessing came, and {hero.id} went home with empty hands, while the stall keeper washed the floor and the moon watched in silence."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={},
        memes={},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=prize_cfg.plural,
    ))
    hero.memes["curiosity"] = 1.0
    hero.memes["resolve"] = 0.0

    setup(world, hero, parent, prize, activity)
    world.para()
    inner_voice(world, hero, prize, activity)
    warn(world, parent, hero, activity, prize)
    stall(world, hero, activity, prize)
    subsequent_turn(world, hero, prize, activity)
    world.para()
    bad_ending(world, hero, parent, prize, activity)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "stall": [
        (
            "What is a stall?",
            "A stall is a small place where someone sets out goods to sell or share.",
        )
    ],
    "galore": [
        (
            "What does galore mean?",
            "Galore means there is a lot of something, almost as if there is plenty everywhere.",
        )
    ],
    "sticky": [
        (
            "Why is sticky honey hard to clean?",
            "Sticky honey clings to skin and cloth, so it spreads and needs careful washing.",
        )
    ],
    "lantern": [
        (
            "What is a lantern for?",
            "A lantern gives light, especially in dark places or on an evening road.",
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that comes back after it bounces off walls or cliffs.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f"Write a short myth for a child about {hero.id} at {f['setting'].place} with a stall in galore.",
        f"Tell a gentle but sad myth where {hero.id} wants to {act.verb} and loses {hero.pronoun('possessive')} {prize.label}.",
        f"Write a story with an inner monologue, repetition, and the word subsequent, ending in a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        QAItem(
            question=f"Where did {hero.id} go at the start of the story?",
            answer=f"{hero.id} went to {f['setting'].place}, where the stalls stood in galore.",
        ),
        QAItem(
            question=f"What did {hero.id} keep thinking inside {hero.pronoun('possessive')} head?",
            answer=(
                f"{hero.id} kept thinking, “Maybe just one more look,” and that thought returned again and again."
            ),
        ),
        QAItem(
            question=f"What did the parent warn would happen to the {prize.label}?",
            answer=f"The parent warned that the {prize.label} would become {act.soil}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=(
                f"It ended badly: the {prize.label} was ruined, the shrine-market went quiet, and {hero.id} went home with empty hands."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["stall", "galore", "sticky", "lantern", "echo"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A, P) :- mess_of(A, M), risky_mess(M), worn_on(P, R), splashes(A, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P).
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
        for t in sorted(a.tags):
            lines.append(asp.fact("tagged", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for m in ["sticky", "dusty", "wet"]:
        lines.append(asp.fact("risky_mess", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A mythic storyworld of stall, galore, repetition, and a bad ending."
    )
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
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, prize):
            raise StoryError(explain_rejection(act, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

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
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible (place, activity, prize) combos:")
        for place, act, prize in models:
            print(f"  {place:12} {act:14} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams("shrine_market", "offer_honey", "cloak", "Mira", "girl", "mother", "curious"),
        StoryParams("shrine_market", "lift_lantern", "tablet", "Oren", "boy", "father", "quiet"),
        StoryParams("echo_hall", "speak_choir", "wreath", "Asha", "girl", "mother", "earnest"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
