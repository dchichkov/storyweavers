#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/scripture_pimento_bustle_misunderstanding_repetition_bedtime_story.py
====================================================================================================================================================

A standalone story world for "The Pimento Mix‑Up" – a gentle bedtime story about
misunderstanding and repetition.  The world incorporates the seed words
*scripture*, *pimento*, *bustle* into a kitchen‑centered domain where a child and
parent make sandwiches.

Causal model:
  * misunderstanding        -> child.memes["confusion"]++, parent.memes["patience"]++
  * correction              -> parent.memes["guidance"]++, child.memes["learning"]++
  * repetition of a phrase  -> child.memes["calm"]++, parent.memes["warmth"]++
  * bustle (busy kitchen)   -> actor.meters["breadcrumbs"]++, actor.memes["hurry"]++
  * discovery of scripture  -> actor.memes["wonder"]++           (the bedtime book)
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
MESS_KINDS = {"crumbly", "sticky", "smeary"}

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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in ("girl", "mother", "mom", "woman"):
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in ("boy", "father", "dad", "man"):
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Setting / Activity / Prize / Gear
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str] = field(default_factory=set)
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.repeated_phrase: str = ""          # the bedtime mantra

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
        clone.zone = set(self.zone)
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

def _r_mess(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            sig = ("stain", actor.id, mess)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{actor.pronoun('possessive').capitalize()} {mess} fingers left tiny marks everywhere.")
    return out

def _r_bustle(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["hurry"] < THRESHOLD:
            continue
        sig = ("bustle", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("The kitchen bustled with hurry and the clatter of jars.")
    return out

def _r_misunderstanding(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["confusion"] < THRESHOLD:
            continue
        sig = ("confuse", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("__confusion__")
    return out

CAUSAL_RULES = [
    Rule("mess", "physical", _r_mess),
    Rule("bustle", "social", _r_bustle),
    Rule("misunderstanding", "social", _r_misunderstanding),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__confusion__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Predict helper
# ---------------------------------------------------------------------------
def predict_is_misunderstanding(world: World, child: Entity, ingredient: Entity) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["confusion"] += 1
    propagate(sim, narrate=False)
    return sim.get(child.id).memes["confusion"] >= THRESHOLD

# ---------------------------------------------------------------------------
# Verbs / beats
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "")
    desc = f"little {trait} {child.type}".strip()
    world.say(f"{child.id} was a {desc} who loved helping in the kitchen.")

def loves_activity(world: World, child: Entity, activity: Activity) -> None:
    world.say(f"{child.pronoun().capitalize()} loved {activity.gerund}; the {activity.keyword} felt like a game.")

def buys(world: World, parent: Entity, child: Entity, prize: Entity) -> None:
    world.say(f"Last week, {child.id}'s {parent.label_word} bought {child.pronoun('object')} {prize.phrase}.")

def loves_prize(world: World, child: Entity, prize: Entity) -> None:
    prize.held_by = child.id
    world.say(f"{child.id} loved {child.pronoun('possessive')} {prize.label} and wore it every morning.")

def arrive(world: World, child: Entity, parent: Entity) -> None:
    world.say(f"One evening, the kitchen was full of bustle. {child.id} and {child.pronoun('possessive')} {parent.label_word} stood by the counter.")
    world.say("The counters were covered with bread, jars, and a big open book — the Scripture of Spreads.")

def wants(world: World, child: Entity, parent: Entity) -> None:
    world.say(f'"{child.id}, would you like to help make the pimento sandwiches?" asked {parent.label_word}.')
    world.say(f'{child.id} nodded eagerly. "I can do it!" {child.pronoun()} said.')

def misunderstand(world: World, child: Entity, parent: Entity, correct_ingredient: Entity, wrong_ingredient: Entity) -> None:
    child.memes["confusion"] += 1
    propagate(world, narrate=False)
    world.say(f'{child.id} reached for the {wrong_ingredient.label} jar instead of the {correct_ingredient.label}.')
    world.say(f'"That is not pimento, sweetie," said {parent.label_word} gently.')
    world.say('__confusion__')

def correct(world: World, parent: Entity, child: Entity, correct_ingredient: Entity) -> None:
    parent.memes["patience"] += 1
    child.memes["learning"] += 1
    world.say(f'"{correct_ingredient.label} is the one we need — see the label?" {parent.label_word} pointed at the word "pimento".')

def repeat_phrase(world: World, phrase: str, child: Entity, parent: Entity) -> None:
    world.repeated_phrase = phrase
    child.memes["calm"] += 1
    parent.memes["warmth"] += 1
    world.say(phrase)

def resolve(world: World, child: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    world.say(f'{child.id} carefully spread the pimento on the bread. {child.pronoun("possessive").capitalize()} {prize.label} stayed clean.')
    world.say(f'Together they packed the sandwiches and read from the Scripture of Spreads before bed.')
    world.say(f'{child.id} whispered the mantra: "{world.repeated_phrase}"')

# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         correct_ingredient: Entity, wrong_ingredient: Entity,
         child_name: str = "Lily", child_type: str = "girl",
         child_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)

    child = world.add(Entity(
        id=child_name, kind="character", type=child_type,
        traits=["little"] + (child_traits or ["curious", "eager"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=child.id, caretaker=parent.id,
        plural=prize_cfg.plural,
    ))
    # Add the two jars as entities (not characters)
    correct = world.add(Entity(
        id="pimento_jar", type="jar", label="pimento jar",
        phrase="a tiny jar of red pimento",
        owner=parent.id, plural=False,
    ))
    wrong = world.add(Entity(
        id="wrong_jar", type="jar", label="peppermint extract",
        phrase="a little bottle with green label",
        owner=parent.id, plural=False,
    ))

    introduce(world, child)
    loves_activity(world, child, activity)
    buys(world, parent, child, prize)
    loves_prize(world, child, prize)

    world.para()
    arrive(world, child, parent)
    wants(world, child, parent)
    misunderstand(world, child, parent, correct, wrong)
    correct(world, parent, child, correct)

    world.para()
    repeat_phrase(world, "It's okay, we can fix it.", child, parent)
    repeat_phrase(world, "Now I know pimento.", child, parent)  # repetition

    resolve(world, child, parent, activity, prize)

    world.facts.update(child=child, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting,
                       correct_ingredient=correct, wrong_ingredient=wrong,
                       repeated_phrase=world.repeated_phrase,
                       misunderstanding=child.memes["confusion"] >= THRESHOLD)
    return world

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the warm kitchen", indoor=True, affords={"sandwich"}),
    "pantry": Setting(place="the pantry", indoor=True, affords={"sandwich"}),
}

ACTIVITIES = {
    "sandwich": Activity(
        id="sandwich",
        verb="make a pimento sandwich",
        gerund="making pimento sandwiches",
        rush="grab the jar without looking",
        mess="crumbly",
        soil="a little messy but clean",
        zone={"torso"},
        keyword="pimento",
        tags={"pimento", "bread"},
    ),
}

PRIZES = {
    "apron": Prize(label="apron", phrase="a soft blue apron", type="apron", region="torso"),
    "bowl": Prize(label="bowl", phrase="a little wooden bowl", type="bowl", region="hands"),
}

GEAR = [
    Gear(id="spoon", label="a small spreading spoon",
         covers={"hands"}, guards={"sticky"}, prep="use a small spoon to spread",
         tail="used the small spoon to spread the pimento"),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "eager", "gentle", "helpful", "cheerful"]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                combos.append((place, act_id, prize_id))
    return combos

# ---------------------------------------------------------------------------
# Params
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
# Q&A / prompts / knowledge
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "pimento": [
        ("What is pimento?",
         "Pimento is a kind of sweet red pepper that is often chopped into small "
         "pieces and put into jars for spreading on bread."),
    ],
    "scripture": [
        ("What is the Scripture of Spreads?",
         "The Scripture of Spreads is a special recipe book that tells you how "
         "to make all kinds of delicious spreads for bread."),
    ],
    "bustle": [
        ("What does bustle mean?",
         "Bustle means busy, quick activity — like when lots of things happen "
         "at the same time in a kitchen."),
    ],
    "apron": [
        ("Why do we wear an apron?",
         "An apron keeps your clothes clean when you cook or make something messy."),
    ],
}
KNOWLEDGE_ORDER = ["pimento", "scripture", "bustle", "apron"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, act, prize_cfg = f["child"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a bedtime story for a young child about misunderstanding the word "pimento" and the gentle correction from a parent.',
        f'A story where a {child.type} helps make sandwiches, learns from a mistake, and hears a repeated calming phrase.',
        f'Include the words scripture, pimento, and bustle in a short, warm tale.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, prize, act = f["child"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {child.type} named {child.id} and {child.pronoun('possessive')} {pw} in the kitchen."
        ),
        QAItem(
            question=f"What did {child.id} want to do at first?",
            answer=f"{child.pronoun().capitalize()} wanted to help make pimento sandwiches."
        ),
        QAItem(
            question=f"What did {child.id} grab by mistake?",
            answer=f"{child.pronoun().capitalize()} grabbed the peppermint extract instead of the pimento jar."
        ),
        QAItem(
            question=f"How did {pw} help {child.id} understand?",
            answer=f"{pw.capitalize()} showed the label and said, 'This is the one we need.'"
        ),
        QAItem(
            question=f"What phrase did they repeat together?",
            answer=f"They repeated '{f['repeated_phrase']}' and later '{'Now I know pimento.'}'"
        ),
    ]
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("pimento")
    tags.add("scripture")
    tags.add("bustle")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World‑knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP twin (minimal – verifies the combo set)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, Act, Prize) :- affords(Place, Act), prize(Act, Prize).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Build / Resolve / Generate / Emit
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a misunderstanding about pimento, repetition, and a warm fix.")
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
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, parent=parent, trait=trait)

def generate(params: StoryParams) -> StorySample:
    correct = Entity("pimento_jar", type="jar", label="pimento jar", phrase="a tiny jar of red pimento")
    wrong = Entity("wrong_jar", type="jar", label="peppermint extract", phrase="a little bottle with green label")
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], correct, wrong,
                 params.name, params.gender, [params.trait, "eager"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.meters.items() if v}
            me = {k: v for k, v in e.memes.items() if v}
            bits = []
            if m: bits.append(f"meters={dict(m)}")
            if me: bits.append(f"memes={dict(me)}")
            lines.append(f"  {e.id} {' '.join(bits)}")
        print("\n".join(lines))
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
        print(f"{len(combos)} compatible (place, activity, prize) combos:")
        for pl, ac, pr in combos:
            print(f"  {pl:9} {ac:8} {pr}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        cur = [StoryParams(place="kitchen", activity="sandwich", prize="apron",
                           name="Lily", gender="girl", parent="mother", trait="curious")]
        samples = [generate(p) for p in cur]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
