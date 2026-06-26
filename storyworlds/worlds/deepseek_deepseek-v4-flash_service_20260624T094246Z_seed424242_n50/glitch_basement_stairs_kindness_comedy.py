#!/usr/bin/env python3
"""
storyworlds/worlds/glitch_basement_stairs_kindness_comedy.py
============================================================

A standalone story world about a glitchy staircase in a basement,
where kindness (and a bit of comedy) makes everything work out.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "glitch"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "glitch": "glitch"}.get(
            self.type, self.type
        )


# ---------------------------------------------------------------------------
# Setting, Activity, Glitch, KindnessItem
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the basement stairs"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    glitch_mess: str
    zone: str
    keyword: str = ""
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
class KindnessItem:
    id: str
    label: str
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_glitch_react(world: World) -> list[str]:
    """If the hero tries to rush without kindness, the glitch escalates."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["tried_rush"] >= THRESHOLD and actor.memes["kindness"] < THRESHOLD:
            glitch = world.entities.get("glitch")
            if glitch and glitch.meters["annoyed"] < THRESHOLD:
                sig = ("glitch_escalate", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    glitch.meters["annoyed"] += 1
                    out.append(
                        "The glitchy stair creaked louder and flickered "
                        "in a silly, confusing way."
                    )
    return out


def _r_glitch_fix(world: World) -> list[str]:
    """Kindness reduces glitch annoyance."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["kindness"] >= THRESHOLD:
            glitch = world.entities.get("glitch")
            if glitch and glitch.meters["annoyed"] > 0:
                sig = ("glitch_calm", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    glitch.meters["annoyed"] = max(0, glitch.meters["annoyed"] - 1)
                    out.append("The glitchy stair seemed to giggle and calm down.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="glitch_react", tag="comedy", apply=_r_glitch_react),
    Rule(name="glitch_fix", tag="kindness", apply=_r_glitch_fix),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Prediction helper
# ---------------------------------------------------------------------------
def predict_glitch(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    sim_actor = sim.get(actor.id)
    sim_prize = sim.get(prize.id)
    sim_glitch = sim.get("glitch")
    # Simulate a rushed attempt
    sim_actor.memes["tried_rush"] += 1
    propagate(sim, narrate=False)
    glitched = sim_glitch and sim_glitch.meters["annoyed"] >= THRESHOLD
    prize_dirty = sim_prize and sim_prize.meters["glitched"] >= THRESHOLD
    return {"glitched": glitched, "prize_ruined": prize_dirty}


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved adventures, even in a basement.")


def loves_stairs(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} "
        f"because every step felt like a tiny bounce."
    )


def prize_owned(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id}'s {parent.label_word} gave {hero.pronoun('object')} "
        f"{prize.phrase} as a special treat."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.owner = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"carried {prize.it()} everywhere."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One funny afternoon, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} stood at the top of the basement stairs."
    )
    world.say(
        "The stairs looked normal, but the air had a fizzy, glitchy feel."
    )


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away. "
        f"\"Can I go down?\" {hero.pronoun()} asked."
    )


def warn_glitch(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"\"Wait,\" {parent.label_word} said. \"There is a glitch on the stairs. "
        f"If you rush, your {prize.label} might get tangled in the glitch.\""
    )


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["tried_rush"] += 1
    world.say(
        f"{hero.id} didn't listen. {hero.pronoun().capitalize()} "
        f"tried to {activity.rush}."
    )
    propagate(world, narrate=True)


def glitch_happens(world: World, hero: Entity, prize: Entity) -> None:
    glitch = world.get("glitch")
    if glitch.meters["annoyed"] >= THRESHOLD:
        world.say(
            "The third stair blinked purple and made a silly 'boing' sound. "
            f"{hero.pronoun('possessive').capitalize()} {prize.label} got flipped upside down!"
        )
        prize.meters["glitched"] += 1


def suggest_kindness(world: World, parent: Entity, hero: Entity, kindness: KindnessItem) -> None:
    world.say(
        f"\"Maybe the glitch just needs a bit of kindness,\" "
        f"{parent.label_word} said. \"How about we {kindness.prep}?\""
    )


def show_kindness(world: World, hero: Entity, kindness: KindnessItem, glitch: Entity) -> None:
    hero.memes["kindness"] += 1
    glitch.meters["glitchiness"] = 0
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} did exactly that. The glitch stair let out a happy little chime. "
        f"\"Thank you!\" it seemed to say."
    )


def resolve(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"Now the stairs were safe. {hero.pronoun().capitalize()} "
        f"{activity.gerund} all the way down, and "
        f"{hero.pronoun('possessive')} {parent.label_word} laughed."
    )
    world.say(
        "The glitch had turned into a friend, and everything felt warm and funny."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    kindness: KindnessItem,
    hero_name: str = "Finn",
    hero_type: str = "boy",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=["little"] + (hero_traits or ["curious", "brave"]),
        )
    )
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(
        Entity(
            id="prize",
            kind="thing",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            plural=prize_cfg.plural,
        )
    )
    glitch = world.add(
        Entity(
            id="glitch",
            kind="thing",
            type="glitch",
            label="the glitch",
            phrase="a twinkly, mischievous glitch on the stairs",
        )
    )

    # Act 1
    introduce(world, hero)
    loves_stairs(world, hero, activity)
    prize_owned(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn_glitch(world, parent, hero, prize)

    # Act 2 – defiance + glitch
    world.para()
    defies(world, hero, activity)
    glitch_happens(world, hero, prize)

    # Act 3 – kindness resolves
    world.para()
    suggest_kindness(world, parent, hero, kindness)
    show_kindness(world, hero, kindness, glitch)
    resolve(world, hero, parent, activity)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        kindness=kindness,
        glitch_resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "basement": Setting(place="the basement stairs", indoor=True, affords={"climb"}),
}

ACTIVITIES = {
    "climb": Activity(
        id="climb",
        verb="climb down the stairs",
        gerund="climbing down the stairs",
        rush="run down the stairs",
        glitch_mess="glitched",
        zone="feet",
        keyword="stairs",
        tags={"stairs", "glitch"},
    ),
}

PRIZES = {
    "teddy": Prize(
        label="teddy bear",
        phrase="a fluffy teddy bear with a red bow",
        type="teddy",
        region="torso",
        plural=False,
        genders={"girl", "boy"},
    ),
    "cape": Prize(
        label="toy cape",
        phrase="a sparkly toy cape",
        type="cape",
        region="shoulders",
        plural=False,
        genders={"girl", "boy"},
    ),
}

KINDNESS_ITEMS = [
    KindnessItem(
        id="compliment",
        label="a kind compliment",
        prep="tell the glitch a nice compliment",
        tail="told the glitch it looked very sparkly",
    ),
    KindnessItem(
        id="snack",
        label="a snack",
        prep="offer the glitch a pretend cookie",
        tail="offered the glitch a pretend cookie",
        plural=True,
    ),
    KindnessItem(
        id="song",
        label="a funny song",
        prep="sing a funny little song to the glitch",
        tail="sang a soft tune to the glitch",
    ),
]

GIRL_NAMES = ["Luna", "Zara", "Nina", "Mila", "Rosa"]
BOY_NAMES = ["Finn", "Ollie", "Kai", "Leo", "Toby"]
TRAITS = ["curious", "brave", "silly", "gentle", "cheerful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    """(place, activity, prize, kindness) tuples that form a reasonable story."""
    combos = []
    for place, s in SETTINGS.items():
        for act_id in s.affords:
            for prize_id in PRIZES:
                for kindness in KINDNESS_ITEMS:
                    combos.append((place, act_id, prize_id, kindness.id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    kindness: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "stairs": [
        ("Why can stairs be tricky sometimes?",
         "Stairs are steep and you have to watch your step, or you might trip."),
        ("What is a glitch?",
         "A glitch is a little hiccup in how things work, like a flicker or a wobble."),
    ],
    "glitch": [
        ("Can a glitch be friendly?",
         "Yes, sometimes glitches just want attention. Being kind to them can help."),
    ],
}

KNOWLEDGE_ORDER = ["stairs", "glitch"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short comedy story for a child about a glitch on some stairs, '
        f'using the word "{act.keyword}".',
        f"Tell a funny tale where a {hero.type} named {hero.id} meets a glitchy stair "
        f"and learns that kindness works better than rushing.",
        f"Write a gentle story about a glitch that becomes a friend after someone shows kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize_cfg"]
    act = f["activity"]
    kindness = f["kindness"]
    sub = hero.pronoun("subject")
    pos = hero.pronoun("possessive")
    obj = hero.pronoun("object")
    pw = parent.label_word

    qa = [
        QAItem(
            question=(
                f"Who wanted to {act.verb} with {pos} {prize.label} "
                f"at the basement stairs?"
            ),
            answer=(
                f"A little {hero.type} named {hero.id} wanted to {act.verb} "
                f"while carrying {pos} {prize.label}. {sub} was with {pw}."
            ),
        ),
        QAItem(
            question=(
                f"What happened when {hero.id} tried to {act.rush}?"
            ),
            answer=(
                f"The glitch on the stairs got annoyed and made the {prize.label} "
                f"flip upside down. It was a silly mess."
            ),
        ),
        QAItem(
            question=(
                f"How did {hero.id} calm the glitch?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} suggested {kindness.prep}. "
                f"{hero.id} did it, and the glitch turned friendly."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="basement",
        activity="climb",
        prize="teddy",
        kindness="compliment",
        name="Luna",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="basement",
        activity="climb",
        prize="cape",
        kindness="snack",
        name="Finn",
        gender="boy",
        parent="father",
        trait="brave",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin (minimal for this domain)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Simple: any combo is valid if setting affords activity.
valid(Place, A, P, K) :- affords(Place, A), prize(P), kindness(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for k in KINDNESS_ITEMS:
        lines.append(asp.fact("kindness", k.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print("  only in clingo:", clingo_set - python_set)
    print("  only in python:", python_set - clingo_set)
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a glitchy basement stair, kindness, comedy."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--kindness", choices=[k.id for k in KINDNESS_ITEMS])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if args.kindness:
        combos = [c for c in combos if c[3] == args.kindness]
    if not combos:
        raise StoryError("No valid combination for given options.")
    place, act, prize_id, kind_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=act,
        prize=prize_id,
        kindness=kind_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    kindness = next(k for k in KINDNESS_ITEMS if k.id == params.kindness)
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        kindness,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(f"  {t[0]:10} {t[1]:8} {t[2]:8} {t[3]:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.activity} at {p.place} (kindness: {p.kindness})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
