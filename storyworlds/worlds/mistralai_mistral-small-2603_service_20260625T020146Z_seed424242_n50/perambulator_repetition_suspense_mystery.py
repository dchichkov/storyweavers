#!/usr/bin/env python3
"""
A standalone story world sketch for "The Perambulator's Secret":
a tiny, suspenseful mystery driven by the little wheels’ creaking song
and the slow-unfolding night-time investigation.

Seed phrase: perambulator
Style: classical mystery (Gothic children’s tone)
Devices: repetition (daily creak), suspense (mounting curiosity),
         locked-garden tropes (old park, night-time digging).
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

THRESHOLD = 1.0           # narrative threshold for ‘noticeable’ change

# ---------------------------------------------------------------------------
# Entities: characters, perambulator, oak tree, and the mysterious box.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, mother, perambulator, tree ...
    label: str = ""                # noun phrase core, e.g. "perambulator"
    phrase: str = ""               # full phrase, e.g. "a brass-bound perambulator"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""               # for items worn/held
    protective: bool = False
    plural: bool = False

    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom"}
        male = {"boy", "son", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Parameter knobs – domain vocabulary
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    has_oak: bool = False        # does this place shelter the old oak?

@dataclass
class Activity:
    id: str
    verb: str            # “go for an evening push in the perambulator”
    gerund: str          # “pushing the silver perambulator”
    rush: str            # “Race through the garden gates”
    mess: str            # meter key that accumulates: “worn”
    soil: str            # consequence phrase: “worn wheels”
    zone: str            # location where the mystery can be discovered, e.g. “under the oak”
    keyword: str = ""    # story-topic word, e.g. “creak”
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False

# ---------------------------------------------------------------------------
# World simulation
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules: wear → creak → curiosity → investigation
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_wear(world: World) -> list[str]:
    for actor in world.characters():
        meters = world.entities.get("perambulator", None)
        if meters and meters.meters.get("worn", 0) < THRESHOLD:
            meters.meters["worn"] += 0.6
            return [f"Each evening’s push made the {meters.label} a little more worn."]
    return []

def _r_creak(world: World) -> list[str]:
    oak = world.entities.get("oak")
    peramb = world.entities.get("perambulator")
    emma = next((c for c in world.characters() if "littl" in c.traits[0]), None)
    out: list[str] = []
    if oak and peramb and emma and oak.region == "under_path":
        if peramb.meters.get("worn", 0) >= THRESHOLD and peramb.region == oak.region:
            sig = ("creak", "oak")
            if sig not in world.fired:
                world.fired.add(sig)
                emma.memes["curio"] += 0.7
                out.append(
                    'A soft, wooden creak sang through the twilight '
                    'as they crept past the old oak.'
                )
    return out

def _r_curiosity(world: World) -> list[str]:
    emma = next((c for c in world.characters() if "littl" in c.traits[0]), None)
    out: list[str] = []
    if emma and emma.memes.get("curio", 0) >= 2.0 and ("meet_oak",) not in world.fired:
        world.fired.add(("meet_oak",))
        emma.memes["resolve"] += 1.0
        return [
            f"{emma.pronoun().capitalize()} could not stop wondering about the creak.",
            "Quietly she pressed her ear to the bark and listened for a heartbeat.",
        ]
    return out

def _r_dig_box(world: World) -> list[str]:
    emma = next((c for c in world.characters() if "littl" in c.traits[0]), None)
    oak = world.entities.get("oak")
    out: list[str] = []
    if oak and emma and emma.memes.get("resolve", 0) >= THRESHOLD and ("dig", "box") not in world.fired:
        world.fired.add(("dig", "box"))
        box = world.add(Entity(
            id="box", kind="thing", type="small_box",
            phrase="a tiny iron-bound box", owner=emma.id,
        ))
        return [
            "That very midnight, with a trowel nicked from the shed, "
            f"{emma.id} scooped moss away near the tree’s roots.",
            f"At last {emma.pronoun()} drew out {box.phrase} tarnished with centuries of leaf-mould."
        ]
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="wear", tag="physical", apply=_r_wear),
    Rule(name="creak", tag="physical", apply=_r_creak),
    Rule(name="curio", tag="emotional", apply=_r_curiosity),
    Rule(name="dig_box", tag="action", apply=_r_dig_box),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return "Inside, the air smelled of lavender and fading sunlight."
    if setting.has_oak:
        return "The old park squatted under a twilight-blue sky, the oak’s limbs like outstretched arms."
    return "A quiet garden waited, bathed in copper light."

def activity_delight(activity: Activity) -> str:
    return {
        "creaky_walk": "the ticking rhythm of wheels on gravel",
        "owl_hoot": "distant hoots dropped like soft pebbles into the hush",
        "owl_watch": "the silver disk of the moon peered through the boughs",
    }.get(activity.id, "the hush of late evening wrapped every sound in velvet")

def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved rides in the dusk "
        f"when the day folded its wings."
    )

def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    where = "inside" if world.setting.indoor else "out under the sky"
    world.say(
        f"{hero.pronoun().capitalize()} adored {activity.gerund} in {where}; "
        f"{activity_delight(activity)}."
    )

def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That afternoon the {parent.label_word} had laid "
        f"{hero.pronoun('object')} {prize.phrase} before {hero.pronoun('object')}."
    )

def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} hugged the {prize.label} and would not let go for an hour; "
        f"then wore {prize.it()} proudly all evening."
    )

def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.paragraphs.append([])
    world.say(setting_detail(world.setting))

def creep_past_oak(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} steered the {world.get('perambulator').label} "
        f"past the gnarled oak, the wheels whispering on the gravel."
    )
    propagate(world)

def wonder(world: World, hero: Entity) -> None:
    world.say(
        'For the tenth evening "Mama, why does the oak sing to us?" '
        f"{hero.pronoun()} asked, eyes round as coins."
    )

def investigate(world: World, hero: Entity, parent: Entity) -> None:
    world.paragraphs.append([])
    world.say(
        f'{hero.pronoun("subject").capitalize()} tugged the {parent.label} toward '
        "the tree and knelt in the cool, fragrant earth."
    )
    propagate(world)

def open_box(world: World, hero: Entity, prize: Entity) -> None:
    box = world.get("box")
    world.paragraphs.append([])
    world.say(
        f"With trembling hands {hero.id} lifted the lid; "
        f"inside rested {prize.phrase}, gleaming like moonlight on metal."
    )
    hero.memes["awe"] += 1.0

# ---------------------------------------------------------------------------
# The screenplay – three acts of mounting mystery
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize: Prize,
         name: str = "Mira", gender: str = "girl",
         trait: str = "quiet", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name, kind="character", type=gender,
        traits=["little", trait],
    ))
    mother = world.add(Entity(id="Mama", kind="character", type="mother", label="Mama"))
    perambulator = world.add(Entity(
        id="perambulator", kind="thing", type="perambulator",
        label="perambulator", phrase="a brass-bound perambulator",
        wear_by=hero.id, region="container",
    ))
    oak = world.add(Entity(
        id="oak", kind="thing", type="oak", region="under_path",
        phrase="a gnarled oak tree", has_oak=True,
    ))
    box = world.add(Entity(
        id="box", kind="thing", type="small_box",
        phrase="a tiny silver locket",
    ))

    # Act 1: love of dusk rides
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, mother, hero, perambulator)
    loves_prize(world, hero, perambulator)

    # Act 2: the creaking mystery
    world.para()
    arrive(world, hero, mother, activity)
    creep_past_oak(world, hero, mother, activity)
    wonder(world, hero)
    creep_past_oak(world, hero, mother, activity)
    creep_past_oak(world, hero, mother, activity)

    # Act 3: midnight revelation
    world.para()
    investigate(world, hero, mother)
    open_box(world, hero, prize)

    # Facts
    world.facts.update(
        hero=hero, parent=mother, prize=prize, perambulator=perambulator,
        activity=activity, setting=setting, oak=oak, box=box,
        daily_creak_count=3, mystery_solved=True,
    )
    return world

# ---------------------------------------------------------------------------
# Registries – every variation trees from the little oak
# ---------------------------------------------------------------------------
SETTINGS = {
    "old_park": Setting(
        place="the old park",
        indoor=False,
        affords={"creaky_walk"},
        has_oak=True,
    ),
}

ACTIVITIES = {
    "creaky_walk": Activity(
        id="creaky_walk",
        verb="go for an evening push in the perambulator",
        gerund="pushing the silver perambulator",
        rush="Race from lamplight into the twilight",
        mess="worn",
        soil="worn wheels",
        zone="under_path",
        keyword="creak",
        tags={"creak", "oak", "twilight"},
    ),
}

PRIZES = {
    "silver_locket": Prize(
        label="locket",
        phrase="a tiny silver locket on a chain",
        type="locket",
        region="neck",
    ),
}

GIRL_NAMES = ["Mira", "Lumi", "Nora", "Anya", "Saskia"]
TRAITS = ["quiet", "watchful", "thoughtful", "dreamy"]

def valid_combos() -> list[tuple[str, str]]:
    """Only settings with an oak admit the creaky mystery."""
    out: list[tuple[str, str]] = []
    for name, setting in SETTINGS.items():
        if setting.has_oak:
            for act_id in setting.affords:
                out.append((name, act_id))
    return out

# ---------------------------------------------------------------------------
# World knowledge (child-level)
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "perambulator": [
        ("What is a perambulator?",
         "A perambulator is an old word for a baby carriage used long ago."),
    ],
    "creak": [
        ("Why do things creak?",
         "Creaks happen when wood or metal bends a little—the sound is like a whisper."),
    ],
    "locket": [
        ("What do people keep in lockets?",
         "Small lockets often hold photos or a curl of hair from someone dear."),
    ],
    "oak": [
        ("How old can an oak tree live?",
         "Some oaks live for hundreds of years, storing memories in every ring."),
    ],
}

# ---------------------------------------------------------------------------
# Q&A generators – three tiers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    kw = f["activity"].keyword or "silver"
    return [
        f'Tell a child-aged story about a little {hero.type} who hears a secret song '
        f'every evening when {hero.pronoun("possessive")} {hero.type} rides '
        f'in {kw}. What do they find when they look closer?',
        f'Write a gentle mystery story for 3-to-6-year-olds: one small creak, '
        "a midnight trowel, and the tiny treasure that explains the nightly tune.",
        'Craft a short tale using the word "creak" three times and ending with '
        'a sleepy "mmm" of satisfaction.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mother, prize = f["hero"], f["parent"], f["prize"]
    sub, obj = (hero.pronoun("subject"), hero.pronoun("object"))
    where = world.setting.place
    act = f["activity"].verb
    day = "one evening"  # all tales occur at dusk/twilight
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the little {hero.type} in the story that rides in the "
                f"perambulator in {where} during {day}?"
            ),
            answer=(
                f"It is {hero.id}, a {hero.type} about four years old. "
                f"Each {day} {sub} rides in {hero.pronoun("possessive")} beloved "
                f"brass-bound perambulator with {mother.label}."
            ),
        ),
        QAItem(
            question=(
                f"What made the little {hero.type} start wondering about the "
                f"sounds near the old oak tree?"
            ),
            answer=(
                f'A soft, wooden creak sang from the oak every time they crept past '
                f"on {day}s for a {f['activity'].gerund}. After many evenings, "
                f"{sub} pressed an ear to the bark and felt the tree hum."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id} and {mother.label} find when they "
                f"dug at the oak’s roots on the last {day}?"
            ),
            answer=(
                f"Near the roots they uncovered a tiny {prize.label}. "
                f"When {hero.id} opened it, inside rested {prize.phrase}, "
                "gleaming like captured moonlight."
            ),
        ),
    ]
    if f.get("mystery_solved"):
        qa.append(QAItem(
            question="Why was the new locket extra special to the little girl?",
            answer=(
                "The locket held a miniature photograph of the very oak tree "
                "when it was still a sapling—its song was the sound of memory."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = f["activity"].tags
    out: list[QAItem] = []
    for tag in ["perambulator", "creak", "locket", "oak"]:
        if tag in tags or tag == "percent" or True:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out

# ---------------------------------------------------------------------------
# ASP twin – declarative gate forcing SettingHasOak ∧ ActivityCreaky
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The mystery needs an old oak in the park
setting_has_oak(P) :- has_oak(P).

% Creaky walks can only happen where there is an oak
compatible(P, A) :- setting_has_oak(P), activity(A), affords(P, A).

valid_story(P, A) :- compatible(P, A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.has_oak:
            lines.append(asp.fact("has_oak", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return [tuple(x) for x in asp.atoms(model, "valid_story")]

def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
# StoryParams and CLI glue
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None

CURATED = [
    StoryParams(
        place="old_park",
        activity="creaky_walk",
        name="Mira",
        gender="girl",
        parent="mother",
        trait="quiet",
    ),
    StoryParams(
        place="old_park",
        activity="creaky_walk",
        name="Lumi",
        gender="girl",
        parent="mother",
        trait="watchful",
    ),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a little mystery of creaks at dusk.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl"])
    ap.add_argument("--parent", choices=["mother"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of tales to spin")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="print the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world state")
    ap.add_argument("--qa", action="store_true", help="print three tiers of Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text blocks")
    ap.add_argument("--asp", action="store_true", help="list ASP-valid combos")
    ap.add_argument("--verify", action="store_true", help="check ASP↔Python agreement")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No tales can happen without the old oak tree’s creaky song.)")
    place, activity = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES)
    gender = args.gender or "girl"
    parent = args.parent or "mother"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name,
                       gender=gender, parent=parent, trait=trait)

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES["silver_locket"], params.name, params.gender,
                 params.trait, params.parent)
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
    if trace and sample.world:
        print("\n---\nworld state:")
        for k, v in sample.world.entities.items():
            print(f"{k}: wear={v.meters.get('worn',0):.1f} curio={v.memes.get('curio',0):.1f}")
    if qa:
        print("\n---\n" + format_qa(sample))

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Questions that would spin this tale =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story answers (grounded in the text) ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) Mysteries solved (child-level) ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"ASP gate allows {len(pairs)} (place, activity) pairs:\n")
        for p, a in pairs:
            print(f"{p:12}  {a}")
        return

    base_seed = args.seed or random.randrange(2**31)
    samples: list[StorySample] = []
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
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, smp in enumerate(samples):
        hdr = ""
        if args.all:
            p = smp.params
            hdr = f"### {p.name} & the late-evening creak ({p.activity}) in {p.place}"
        elif len(samples) > 1:
            hdr = f"### twilight tale #{idx+1}"
        emit(smp, trace=args.trace, qa=args.qa, header=hdr)
        if idx < len(samples) - 1:
            print("\n" + "~" * 70 + "\n")

if __name__ == "__main__":
    main()
