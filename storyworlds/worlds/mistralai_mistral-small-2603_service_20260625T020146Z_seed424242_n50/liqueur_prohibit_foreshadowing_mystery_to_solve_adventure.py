#!/usr/bin/env python3
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
from results import QAItem, StoryError, StorySample

# Constants
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities: characters, places, and items share one typed representation.
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"detective", "daughter", "mother"}
        male = {"detective", "son", "mayor", "baker", "grocer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this domain.
# ---------------------------------------------------------------------------
@dataclass
class Location:
    id: str
    phrase: str
    interior: bool = False
    affords: set[str] = field(default_factory=set)

@dataclass
class Noun:
    id: str
    label: str
    phrase: str
    type: str = "object"

LIQUEURS = {
    "grand_marnier": Noun(
        id="grand_marnier",
        label="bottle of Grand Marnier",
        phrase="a corner-cut liqueur bottle of Grand Marnier",
        type="liqueur",
    ),
    "chartreuse": Noun(
        id="chartreuse",
        label="bottle of Chartreuse",
        phrase="a velvety green bottle of Chartreuse",
        type="liqueur",
    ),
    "cointreau": Noun(
        id="cointreau",
        label="bottle of Cointreau",
        phrase="a crystal-clear bottle of Cointreau",
        type="liqueur",
    ),
}

@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    affords: set[str] = field(default_factory=set)

CLUES = {
    "shard": Clue(id="shard", label="broken bottle shard", phrase="a sharp piece of broken glass", affords={"place", "track"}),
    "muddy_boots": Clue(id="muddy_boots", label="muddy boots", phrase="heavy work boots caked in river mud", affords={"bakery"}),
    "empty_glass": Clue(id="empty_glass", label="empty coupe", phrase="a lead-crystal coupe rinsed and left on the bar", affords={"saloon"}),
    "apron_stain": Clue(id="apron_stain", label="flour handprint", phrase="a white smear across the baker’s apron pocket", affords={"bakery"}),
    "rail_receipt": Clue(id="rail_receipt", label="railroad receipt", phrase="a crumpled receipt for a 1-case shipment of Chartreuse", affords={"grocery", "town_hall"}),
    "perfume": Clue(id="perfume", label="perfume", phrase="a trace of sweet violet perfume on a doorknob", affords={"mayors_office", "house"}),
}

@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    traits: list[str] = field(default_factory=list)

SUSPECTS = {
    "mayor": Suspect(
        id="Mayor Whitmore",
        label="Mayor Whitmore",
        phrase="the portly mayor in a tailored waistcoat",
        traits=["charming", "secretive"],
    ),
    "baker": Suspect(
        id="Baker Willis",
        label="Baker Willis",
        phrase="a flour-dusted baker with flour everywhere",
        traits=["edgy", "always-busy"],
    ),
    "grocer": Suspect(
        id="Grocer Hamm",
        label="Grocer Hamm",
        phrase="the burly grocer behind thick spectacles",
        traits=["hasty", "bad-temper"],
    ),
}

SUSPECT_NAMES = list(SUSPECTS.keys())

# ---------------------------------------------------------------------------
# World state and causal forward chaining
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Location) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.stolen = None
        self.clues_planted: dict[str, str] = {}
        self.facts: dict = {"discovered_clues": set(), "used_items": set()}
        self.weather = random.choice(["rainy", "drizzly", "gray"])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def find_by_type(self, kind: str) -> list[Entity]:
        return [e for e in self.entities.values() if e.type == kind]

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
        clone.facts = dict(self.facts)
        return clone

# ---------------------------------------------------------------------------
# Causal rule set
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_notice_clue(world: World) -> list[str]:
    out: list[str] = []
    found = world.facts["discovered_clues"] - set(world.entities.keys())
    for cid in found:
        clue = world.entities[cid]
        suspect = world.entities[clue.affords & world.entities.keys()]
        if suspect:
            sig = ("plant", cid, suspect.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(f"{clue.label.capitalize()} lay beside {suspect.id.lower()}'s workspace.")
    return out

def _r_accuse(world: World) -> list[str]:
    for town in world.find_by_type("saloon"):
        if town.memes["suspicion"] >= 2.0:
            world.say(f"{town.label.capitalize()} leaned forward, eyes narrowing. 'You’re accusing the {town.label} itself?'")
            town.memes["dogged"] += 1
            return ["__accuse__"]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="notice_clue", tag="detective", apply=_r_notice_clue),
    Rule(name="accuse", tag="climax", apply=_r_accuse),
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
                produced.extend(s for s in sents if s != "__accuse__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# World-building verbs
# ---------------------------------------------------------------------------
def opening(world: World, detective: Entity) -> None:
    l = world.setting.label
    w = world.weather.title()
    world.say(f"{detective.label.capitalize()} pushed through the creaking door into {l}, the morning light barely piercing the {w} sky.")
    world.say(f"Sunlight caught the brass bell above the door and set it to chiming.")

def summon_the_town(world: World, detective: Entity, saloon: Entity) -> None:
    world.say(f"Every pair of eyes inside turned toward {detective.pronoun('object')} as {detective.label} crossed the worn floorboards toward the bar.")
    saloon.memes["crowded"] += 1

def reveal_missing(world: World, saloon: Entity, liqueur: Noun) -> None:
    world.say(f"'{detective.label}' murmured, 'where is that {liqueur.label} I left in the back cabinet last evening?'")
    saloon.memes["shock"] += 1
    saloon.memes["suspicion"] = 0.1

def plant_clue(world: World, item: Entity, location: Entity) -> str:
    if "grassy" in location.id:
        msg = f"{item.label} glittered beside the railroad ties."
        world.clues_planted[item.id] = location.id
        return msg
    msg = f"{item.label} peeked from beneath a flour sack."
        world.clues_planted[item.id] = location.id
        return msg

def conceals_liqueur(world: World, suspect: Entity, safe: Entity) -> None:
    world.say(f"{suspect.id} slipped a dull key back into {suspect.pronoun('possessive')} vest pocket, eyes darting.")
    suspect.meters["caution"] += 1
    safe.meters["locked"] += 1

def trace_spill(world: World, detective: Entity) -> str:
    world.say(f"{detective.label} studied the faint amber rings on the cabinet shelf.")
    return "amber drip line"

def investigator_spot(world: World, detective: Entity, place: str) -> None:
    world.say(f"{detective.label} stepped carefully over the threshold into {place}.")

def notices_stain(world: World, suspect: Entity, clue: Entity) -> None:
    world.say(f"{suspect.id} blinked at {clue.label}, then hastily wiped {suspect.pronoun('possessive')} apron.")
    suspect.memes["nervous"] += 1

def interrogate(world: World, suspect: Entity, item: Entity) -> None:
    world.say(f"‘And this little bottle? Where did you last place it yourself?’ {detective.label} tapped the glass.")
    item.meters["held"] += 1
    suspect.memes["pressure"] += 1

def solve(world: World, detective: Entity) -> None:
    world.say(f"{detective.label.capitalize()} exhaled, ‘Well, folks, we’ve solved the mystery.’")
    for s in world.entities.values():
        if s.type == "character" and "suspect" in s.label:
            s.memes["shame"] += 1

# ---------------------------------------------------------------------------
# The screenplay one short mystery
# ---------------------------------------------------------------------------
def tell(setting_id: str, liqueur_id: str, clue_ids: list[str], suspect_id: str) -> World:
    place = LOCATIONS[setting_id]
    liquor = LIQUEURS[liqueur_id]
    world = World(place)
    world.stolen = liquor.id

    # Central characters
    detective = world.add(Entity(
        id="Detective Leah", kind="character", type="detective",
        label="Detective Leah", traits=["curious", "dogged"],
    ))
    saloon = world.add(Entity(
        id="Old Saloon", kind="saloon", label="the Old Saloon’s back cabinet",
        type="place", phrase="the old oaken back cabinet of the saloon",
    ))
    suspect = world.add(Entity(
        id=SUSPECTS[suspect_id].id, kind="character", type="suspect",
        label=SUSPECTS[suspect_id].label,
        traits=SUSPECTS[suspect_id].traits + ["unsuspecting"],
    ))
    safe = world.add(Entity(
        id=f"{suspect.id.lower()}_safe", type="safe", label="a small iron strongbox",
        phrase="a small iron strongbox hidden behind sacks",
        owner=suspect.id,
    ))

    # Scene 1 – quiet morning, the offer of a rare liqueur
    opening(world, detective)
    world.say(f"There, tucked into the oak cabinet, sat {liquor.phrase}—a gift meant for last night’s quiet toast.")
    saloon.memes["content"] += 1

    # Foreshadowing: someone returning late, a whispered conversation
    world.para()
    world.say(f"{detective.label} recalled the rustle of footsteps outside at half-past nine.")

    # Foreshadowing: a dropped hint gathered up later
    world.facts["ambers"] = ["would turn the whole story amber"]

    # Scene 2 – the discovery the next morning
    world.para()
    reveal_missing(world, saloon, liquor)
    saloon.memes["panic"] = 0.9

    # Scene 3 – investigation begins: scour the township
    world.para()
    world.say(f"But the bottle was gone, vanished overnight without so much as a broken pane.")

    # Drop clues around town linked to the suspect’s routines
    for cid in clue_ids:
        clue = CLUES[cid]
        world.add(Entity(id=cid, type="clue", label=clue.label, phrase=clue.phrase, affords=clue.affords))
        world.facts["discovered_clues"].add(cid)
        where = "the railroad ties" if "rail" in cid else "the bakery floor"
        world.say(plant_clue(world, world.entities[cid], saloon))

    propagate(world, narrate=True)

    # Scene 4 – narrowing the list to one who protects sweets
    world.para()
    accuse_id = suspect_id
    accuse = world.entities[SUSPECTS[accuse_id].id]
    interrogate(world, accuse, liquor)
    world.say(f"‘I haven’t seen a drop,’ {accuse.id} answered too quickly, hands tapping the counter.")

    # The simple resolution image
    world.para()
    solve(world, detective)
    world.say(f"The next dawn {accuse.id} stood beside {detective.label}, returning {liquor.label} to its shelf.")

    # Facts for downstream Q&A
    world.facts.update(
        detective=detective,
        saloon=saloon,
        accused=accuse,
        liqueur=liquor,
        setting=place,
    )
    return world

# ---------------------------------------------------------------------------
# Parameter registries
# ---------------------------------------------------------------------------
LOCATIONS = {
    "saloon": Location(
        id="saloon",
        phrase="the Old Saloon on Fleet Street",
        interior=True,
        affords={"lieu", "track", "grassy"},
    ),
    "bakery": Location(
        id="bakery",
        phrase="the Riverside Bakery",
        interior=True,
        affords={"bakery", "grassy"},
    ),
    "grocery": Location(
        id="grocery",
        phrase="Hamm’s Grocery at the Railroad Stop",
        interior=True,
        affords={"grocery", "liquor_track"},
    ),
    "mayors_office": Location(
        id="mayors_office",
        phrase="the mayor’s back office",
        interior=True,
        affords={"mayors_office"},
    ),
    "house": Location(
        id="house",
        phrase="the modest frame house above the river bend",
        interior=True,
        affords={"house"},
    ),
}

# Build a small set of reasonable combos
def valid_combos() -> list[tuple[str, str, list[str], str]]:
    combos: list[tuple[str, str, list[str], str]] = []
    for ll in LIQUEURS:
        liq = LL
        for sid in SUSPECTS:
            for hidx in range(3):
                clue_ids = random.sample(list(CLUES.keys()), hidx+2)
                combos.append((hid, ll, clue_ids, sid)
    return combos[:12]  # 12 curated micro-variants

# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    location: str
    liqueur: str
    clues: list[str]
    suspect: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generators
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    acto = world.entities[f["liqueur"]].label.replace("bottle of ", "")
    return [
        f'Create a crisp noir-style story (~150 words) titled "The {acto} Caper" for a '
        '4–6-year-old: the first half foreshadows with small hints, the second half '
        f'centers on "who could have taken the {acto}" and ends with Detective '
        "Leah revealing the answer in a single concrete image.",
        f"Tell a short adventure mystery where a detective hunts a stolen liqueur "
        "in a small town, gathering clues linked to a suspect’s daily rounds.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, saloon, accused, liq = f["detective"], f["saloon"], f["accused"], f["liqueur"]
    qa: list[QAItem] = [
        QAItem(
            question="Who noticed first that the precious bottle was missing?",
            answer=f"{det.label} pushed through the creaking door and wondered aloud where "
                   f"that {liq.label} had vanished.",
        ),
        QAItem(
            question="What small trace did Detective Leah find near the railroad ties?",
            answer="A crumpled railroad receipt for a case of Chartreuse hinted at "
                   "a recent delivery to the nearby grocery.",
        ),
    ]
    if "ambers" in world.facts:
        qa.append(QAItem(
            question="What did Detective Leah recall from last night’s quiet toast?",
            answer="Leah remembered the rustle of footsteps and quiet laughter just before "
                   "half-past nine, foreshadowing the evening’s intrigue.",
        ))
    if world.entities[accused.id].memes["shame"] > THRESHOLD:
        qa.append(QAItem(
            question="How was the mystery finally solved the next dawn?",
            answer=f"{detective.label} stood beside {accused.id} as the culprit slid the "
                   f"{liq.label} back into its shelf, the amber drip line still clinging.",
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is liqueur?",
            answer="Liqueur is a sweet, flavored alcoholic drink, often enjoyed in small "
                   "amounts after meals or as a celebratory toast.",
        ),
        QAItem(
            question="What does ‘prohibition’ mean?",
            answer="Back then, the law forbade many drinks from being bought or sold to "
                   "keep towns peaceful and orderly.",
        ),
    ]

# ---------------------------------------------------------------------------
# Trace output for --trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- town state ---"]
    for e in world.entities.values():
        ms = {k:v for k,v in e.meters.items() if v}
        mmes = {k:v for k,v in e.memes.items() if v}
        if ms or mmes:
            lines.append(f"  {e.id:20} meters={dict(ms)} memes={dict(mmes)}")
    lines.append(f"  fired: {sorted(set(n for n,*_ in world.fired))}")
    return "\n".join(lines)

# ASP Twin: clingo rules mirrored above
ASP_RULES = r"""
% A theft occurred; each suspect ties to a location visited overnight
theft(liqueur) :- item(liqueur), holds(S, liqueur, evening), moved(S).

% Whoever last held the liqueur is most suspicious
suspicious(S) :- theft(liqueur), holds(S, liqueur, T), last_time(T).

% Clues connect a suspect to the place they visited
hint(C, S) :- clue(C), visited(S,L), affords(L, A), covers(A, C).

% The accused is the one whose visited places all have matching clues
accused(S) :- suspicious(S), forall visited(S,L) (exists C hint(C,S), affords(L,A), covers(A,C)).

% A reasonable story needs at least two hints scattered in the town
reasonable :- accused(S), #count{C : hint(C,S)} >= 2.

% Only output valid micro-mysteries
#show reasonable.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in LOCATIONS.items():
        lines.append(asp.fact("location", pid))
        if s.interior:
            lines.append(asp.fact("interior", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for lid, li in LIQUEURS.items():
        lines.append(asp.fact("item", lid))
        lines.append(asp.fact("liqueur", lid))
    for cid, cl in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for a in sorted(cl.affords):
            lines.append(asp.fact("covers", cid, a))
    for sid, sp in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("visited", sid, sp.affords))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    python_set = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show accused/1."))
    clingo_set = set(asp.atoms(model, "accused"))
    if clingo_set == {tuple(c[0:1]) for c in python_set}:
        print(f"OK: clingo gate agrees with valid_combos ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python registries")
    return 1

# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny prohibition-era liqueur mystery.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--liqueur", choices=LIQUEURS)
    ap.add_argument("--clues", nargs="+", metavar="CLUE")
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.liqueur and args.location and args.suspect and args.clues:
        liq = LIQUEURS[args.liqueur]
        loc = LOCATIONS[args.location]
        return StoryParams(args.location, args.liqueur, args.clues, args.suspect, None)
    combos = valid_combos()
    s = rng.choice(sorted(combos))
    return StoryParams(*s, seed=None)

def generate(params: StoryParams) -> StorySample:
    world = tell(params.location, params.liqueur, params.clues, params.suspect)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool, qa: bool, header: str) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\nStory Q&A:")
        for item in sample.story_qa:
            print(f"  Q: {item.question}\n  A: {item.answer}")
        print("\nWorld Q&A:")
        for item in sample.world_qa:
            print(f"  Q: {item.question}\n  A: {item.answer}")

_CURATED = [
    StoryParams("saloon", "chartreuse", ["shard", "rail_receipt"], "baker"),
    StoryParams("saloon", "cointreau", ["empty_glass", "perfume"], "mayor"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show accused/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base = args.seed or random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [_CURATED[i % len(_CURATED)] for i in range(3)]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n*50, 250):
            seed = base + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            tx = sample.story
            if tx in seen:
                continue
            seen.add(tx)
            samples.append(sample)
    if args.json:
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
    else:
        for i, s in enumerate(samples):
            hdr = f"### Mystery #{i+1}"
            emit(s, trace=args.trace, qa=args.qa, header=hdr)
            if i < len(samples)-1:
                print("\n"+("="*70)+"\n")

if __name__ == "__main__":
    main()
