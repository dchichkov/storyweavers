#!/usr/bin/env python3
"""
storyworlds/worlds/glory_scarlet_babble_inner_monologue_happy_ending.py
=======================================================================

A rhyming storyworld about a child chasing glory in a scarlet dress, babbling with
excitement, inner monologue, reconciliation with a parent, and a happy ending.
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
# Entities
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
        female = {"girl", "mother", "mom", "woman"}
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    stage_verb: str
    glory_word: str
    sound_word: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    colour: str = "scarlet"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
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
# Causal rules (minimal – emotional arc)
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_inner_monologue(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["excitement"] >= THRESHOLD and actor.memes["nervous"] >= THRESHOLD:
            sig = ("think", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["doubt"] += 1
            out.append("__inner__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="inner_monologue", apply=_r_inner_monologue),
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
                produced.extend(s for s in sents if s != "__inner__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Rhyming prose generators – each beat returns a couplet (two lines)
# ---------------------------------------------------------------------------
def rhyme_introduce(hero: Entity, colour: str, object_label: str) -> str:
    return (
        f"There was a little {hero.type} named {hero.id},\n"
        f"dreaming of glory with a {colour} {object_label}."
    )


def rhyme_loves_activity(hero: Entity, activity: Activity) -> str:
    return (
        f"{hero.pronoun('possessive').capitalize()} heart would babble, "
        f"full of sound,\n"
        f"to {activity.verb} on stage was what {hero.pronoun()} found."
    )


def rhyme_buys(parent: Entity, hero: Entity, prize: Prize) -> str:
    return (
        f"Then {hero.pronoun('possessive')} {parent.label_word} bought, with a smile,\n"
        f"a {prize.colour} {prize.label} that matched the style."
    )


def rhyme_loves_prize(hero: Entity, prize: Entity) -> str:
    return (
        f"{hero.id} put {prize.it()} on and felt so grand,\n"
        f"the {prize.label} felt soft in {hero.pronoun('possessive')} hand."
    )


def rhyme_arrive(hero: Entity, parent: Entity, place: str) -> str:
    return (
        f"One fine day they went to {place},\n"
        f"glory waiting, time to face."
    )


def rhyme_babble(hero: Entity, activity: Activity) -> str:
    return (
        f"{hero.id} began to babble, bright and fast,\n"
        f"\"I want to {activity.verb} – it‘s here at last!\""
    )


def rhyme_inner_monologue(hero: Entity, activity: Activity) -> str:
    return (
        f"But inside {hero.pronoun('possessive')} mind a whisper grew:\n"
        f"“What if I stumble? What if I’m blue?”"
    )


def rhyme_warn(parent: Entity, hero: Entity) -> str:
    return (
        f"{parent.label_word.capitalize()} saw the fear and took {hero.pronoun('possessive')} hand,\n"
        f"\"Let’s practice once more, then you’ll be grand.\""
    )


def rhyme_compromise(hero: Entity, prize: str, gear: Gear) -> str:
    return (
        f"So they put {prize} in a safe, nice place,\n"
        f"and {gear.tail}, with a happy face."
    )


def rhyme_accept(hero: Entity, parent: Entity, activity: Activity) -> str:
    return (
        f"{hero.id} hugged {hero.pronoun('possessive')} {parent.label_word}, feeling bold,\n"
        f"the story of glory will now unfold."
    )


def rhyme_happy_end(hero: Entity, activity: Activity, prize_label: str, colour: str) -> str:
    return (
        f"{hero.id} {activity.stage_verb} in {colour} glee,\n"
        f"the crowd cheered loud – what joy to see!\n"
        f"The {prize_label} stayed clean, the glory won,\n"
        f"a happy ending for everyone."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mia", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "brave"],
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the parent"
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        plural=prize_cfg.plural,
    ))
    gear = world.add(Entity(
        id="gear_box", type="storage", label="a special box",
        owner=hero.id, caretaker=parent.id, plural=False,
    ))

    # Act 1
    world.say(rhyme_introduce(hero, prize_cfg.colour, prize.label))
    world.say(rhyme_loves_activity(hero, activity))
    world.say(rhyme_buys(parent, hero, prize_cfg))
    world.say(rhyme_loves_prize(hero, prize))

    # Act 2 – tension
    world.para()
    world.say(rhyme_arrive(hero, parent, setting.place))
    hero.memes["excitement"] += 1
    world.say(rhyme_babble(hero, activity))
    hero.memes["nervous"] += 1
    propagate(world)
    world.say(rhyme_inner_monologue(hero, activity))

    # Act 3 – reconciliation
    world.para()
    world.say(rhyme_warn(parent, hero))
    g = Gear(
        id="box", label="a special box",
        prep="put the prize in a special box",
        tail="put the prize in the box and smiled"
    )
    world.say(rhyme_compromise(hero, prize.label, g))
    hero.memes["doubt"] = 0
    hero.memes["joy"] += 1
    world.say(rhyme_accept(hero, parent, activity))
    world.say(rhyme_happy_end(hero, activity, prize.label, prize_cfg.colour))

    world.facts.update(
        hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
        activity=activity, setting=setting,
        gear=g,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "theatre": Setting(place="the theatre", affords={"sing", "dance", "recite"}),
    "school": Setting(place="the school hall", affords={"sing", "recite"}),
    "home": Setting(place="the living room", affords={"sing", "dance"}),
}

ACTIVITIES = {
    "sing": Activity(
        id="sing",
        verb="sing a song",
        gerund="singing",
        stage_verb="sang",
        glory_word="applause",
        sound_word="note",
        keyword="song",
        tags={"music", "performance"},
    ),
    "dance": Activity(
        id="dance",
        verb="dance a jig",
        gerund="dancing",
        stage_verb="danced",
        glory_word="cheers",
        sound_word="feet",
        keyword="dance",
        tags={"movement", "performance"},
    ),
    "recite": Activity(
        id="recite",
        verb="recite a poem",
        gerund="reciting",
        stage_verb="recited",
        glory_word="praise",
        sound_word="rhyme",
        keyword="poem",
        tags={"words", "performance"},
    ),
}

PRIZES = {
    "dress": Prize(label="dress", phrase="a scarlet dress", type="dress", colour="scarlet", genders={"girl"}),
    "shirt": Prize(label="shirt", phrase="a scarlet shirt", type="shirt", colour="scarlet", genders={"boy"}),
    "cape": Prize(label="cape", phrase="a scarlet cape", type="cape", colour="scarlet", genders={"girl", "boy"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Sam", "Leo", "Max", "Finn", "Noah"]
TRAITS = ["brave", "shy", "dreamy"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id in SETTINGS:
        for act_id in SETTINGS[place_id].affords:
            for prize_id in PRIZES:
                combos.append((place_id, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
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
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "performance": [
        ("What does it mean to perform on stage?",
         "It means you show something you practiced, like singing or dancing, to an audience."),
    ],
    "music": [
        ("Why do people clap after a song?",
         "Clapping is a way to say 'well done' and show they liked the performance."),
    ],
    "movement": [
        ("What is a dance?",
         "A dance is moving your body in a fun way, often to music."),
    ],
    "words": [
        ("What is a poem?",
         "A poem is a short piece of writing that sometimes rhymes."),
    ],
    "scarlet": [
        ("What colour is scarlet?",
         "Scarlet is a bright red colour, like a ripe strawberry."),
    ],
    "brave": [
        ("What does it mean to be brave?",
         "Being brave means doing something even if you are a little scared."),
    ],
}
KNOWLEDGE_ORDER = ["performance", "music", "movement", "words", "scarlet", "brave"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act = f["hero"], f["activity"]
    return [
        f'Write a rhyming story about a {hero.type} who wants glory in a scarlet {PRIZES[f["prize_cfg"].label].label}.',
        f'A story with inner monologue, reconciliation, and a happy ending, featuring the word "{act.keyword}".',
        f"Tell a short rhyming tale that includes babble, a scarlet prize, and a child's stage debut.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in {prize.label_word}'s {PRIZES[prize.label].colour} {prize.label}?",
            answer=f"A little {hero.type} named {hero.id}, with {hero.pronoun('possessive')} {parent.label_word}."
        ),
        QAItem(
            question=f"Why did {hero.id} feel nervous before the show?",
            answer=f"{hero.id} was excited but worried about forgetting the {act.gerund}."
        ),
        QAItem(
            question=f"How did {hero.id} and {hero.pronoun('possessive')} {parent.label_word} solve the problem?",
            answer=f"They put the {prize.label} in a safe box and practiced together, so {hero.id} felt ready."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = world.facts["activity"].tags | {"scarlet", "brave"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            for q, a in KNOWLEDGE.get(tag, []):
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Knowledge ==")
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
        m = {k: v for k, v in e.meters.items() if v}
        me = {k: v for k, v in e.memes.items() if v}
        bits = [f"meters={dict(m)}" if m else "", f"memes={dict(me)}" if me else ""]
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="theatre", activity="sing", prize="dress", name="Mia", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="school", activity="recite", prize="cape", name="Sam", gender="boy", parent="father", trait="shy"),
    StoryParams(place="home", activity="dance", prize="shirt", name="Leo", gender="boy", parent="mother", trait="dreamy"),
]


# ---------------------------------------------------------------------------
# ASP twin (minimal, just for contract compliance)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, A, P) :- affords(Place, A), prize_exists(P).
prize_exists(P) :- prize(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for a in SETTINGS[pid].affords:
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: glory, scarlet dress, babble, inner monologue, happy ending."
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not filtered:
        raise StoryError("No valid combination for given options.")
    place, activity, prize_id = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(sorted(PRIZES[prize_id].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place], ACTIVITIES[params.activity],
        PRIZES[params.prize], params.name, params.gender, params.parent,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(f"  {c[0]:9} {c[1]:8} {c[2]:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
