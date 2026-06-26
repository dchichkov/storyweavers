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

# Nursery-rhyme threshold for 'embedding' an effect into prose
THRESHOLD = 0.8

# Body regions served by arteries
REGIONS = {"chest", "abdomen", "legs"}

# Emotional dimensions
MEMOS = {"curiosity", "frustration", "joy"}

# Physical dimensions
METERS = {"clogness", "stretchiness", "goodness", "mileage"}

# Kinds of nuisances that block a vessel
NUISANCES = {"clog", "twist", "narrow"}

# Tiny nursery names for our artery cast
ARTERY_NAMES = [
    "Twinkle Artery", "Bounce Tube", "Skip Line", "Red Ribbon", 
    "Pumpkin Pipe", "Dancer Tube", "Jolly Route", "Giggle Vessel",
    "Zippy Stream", "Mellow Line"
]

ORGANS = {
    "lungs": {"label": "tiny lungs", "share": "clean air", "need": "oxygen"},
    "stomach": {"label": "good tummy", "share": "fresh stew", "need": "energy"},
    "muscles": {"label": "strong muscles", "share": "helpful push", "need": "strength"},
}

# ---------------------------------------------------------------------------
# Entity: one character or object in the circulatory tale
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    label: str = ""
    phrase: str = ""
    region: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if case == "subject": return "it"
        if case == "object": return "it"
        if case == "possessive": return "its"
        return "it"

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def is_clogged(self) -> bool:
        return self.meters["clogness"] >= THRESHOLD

# ---------------------------------------------------------------------------
# World: entity store + evolving narrative paragraphs
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}  # facts collected during simulation

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities.get(eid)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to fixpoint through the circulatory system
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_engage_cells(world: World) -> list[str]:
    """Heart pump builds goodness meters in served regions."""
    out: list[str] = []
    heart = world.get("StrongHeart")
    if not heart: return out
    for r in REGIONS:
        ruler = world.get(f"ruler_{r}")
        if ruler and ruler.memes["joy"] > THRESHOLD:
            for e in world.entities.values():
                if e.region == r and e.kind == "thing" and e.meters.get("goodness",0) < THRESHOLD*3:
                    e.meters["goodness"] += 0.5
            out.append(f"Glowing red streams circle {r} to bring fresh life near.")
    return out

def _r_grow_curious(world: World) -> list[str]:
    """High goodness in a region sparks exploratory curiosity."""
    out: list[str] = []
    for r in REGIONS:
        for art in world.entities.values():
            if art.region == r and art.memes["curiosity"] < 5:
                if any(e.meters.get("goodness",0) >= THRESHOLD*2 for e in world.entities.values() if e.region == r):
                    art.memes["curiosity"] += 0.25
                    out.append(f"The {art.label} in {r} wiggled with growing curiosity.")
    return out

def _r_spot_nuisance(world: World) -> list[str]:
    """If a nuisance entity co-locates with an artery, the clog/twist/narrow stress increases."""
    out: list[str] = []
    for nuis_id, nuis in world.entities.items():
        if nuis.label not in NUISANCES: continue
        for art in world.entities.values():
            if art.kind != "character": continue
            if art.meters["frustration"] < THRESHOLD*4:  # baseline patience
                sig = (nuis.id, art.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    art.meters["clogness"] += {"clog":2.0, "twist":1.5, "narrow":1.0}[nuis.label]
                    art.memes["frustration"] += {"clog":0.8, "twist":0.5, "narrow":0.3}[nuis.label]
                    out.append(
                        f"Oh dear!  {art.label} met a {nuis.phrase} right there in {art.region}, "
                        f"and feelings grew sour."
                    )
    return out

def _r_clearing_share(world: World) -> list[str]:
    """Sharing organs (lungs/stomach) reduce clog; helper's helper meters rise."""
    out: list[str] = []
    for org in world.entities.values():
        if org.kind == "organ_helper":
            for art in world.entities.values():
                if art.region == org.region and art.is_clogged and org.meters.get("share_points",0) > 0:
                    sig = ("share", art.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        art.meters["clogness"] -= 0.7
                        art.meters["goodness"] += 0.4
                        org.meters["share_points"] -= 1
                        art.memes["frustration"] -= 0.3
                        out.append(
                            f"The {org.label} shared {org.helper} nearby, "
                            f"and the little artery breathed easier."
                        )
    return out

def _r_bounce_back(world: World) -> list[str]:
    """If goodness >= THRESHOLD*3 and curiosity > failure, artery celebrates with joy."""
    out: list[str] = []
    for art in world.entities.values():
        if art.kind == "character" :
            if art.meters["goodness"] >= THRESHOLD*3 and art.memes["frustration"] < THRESHOLD:
                art.memes["joy"] += 0.6
                sig = ("bounce", art.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append(
                        f"Hurray!  {art.label} wiggled happily; the weary way was through."
                    )
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="engage_cells", tag="physical", apply=_r_engage_cells),
    Rule(name="grow_curious", tag="emotional", apply=_r_grow_curious),
    Rule(name="spot_nuisance", tag="physical", apply=_r_spot_nuisance),
    Rule(name="clearing_share", tag="social", apply=_r_clearing_share),
    Rule(name="bounce_back", tag="emotional", apply=_r_bounce_back),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply rules until a quiescent state is reached."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                if narrate:
                    produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Constraint helpers — reasonableness gates for world generation
# ---------------------------------------------------------------------------
def valid_combo(location: str, context: str, obstacle_type: str) -> bool:
    """Only certain obstacle types make sense in each context."""
    risky = {"working", "playing"}
    blocked = {"clog"}
    twisted = {"twist"}
    narrows = {"narrow"}
    if context in risky:
        return obstacle_type in blocked | twisted | narrows
    return True

def explain_rejection(context: str, obstacle_type: str) -> str:
    if context == "resting" and obstacle_type == "clog":
        return ("(No small story: clogs rarely form when the body is still; "
                "try a twist or narrow at rest.)")
    if obstacle_type == "narrow" and context == "resting":
        return "(No story: narrowed passage fits play/exertion, not rest.)"
    return "(No small story for these options together.)"

def meter_dict(e: Entity) -> dict:
    return {k: round(v,2) for k,v in e.meters.items() if abs(v)>=0.01}

# ---------------------------------------------------------------------------
# Tiny Nursery Verbs — the screenplay for one little artery’s day
# ---------------------------------------------------------------------------
def nursery_rhyme_title(name: str) -> str:
    return f"The Day {name} Danced Through Tubes"

def gentle_intro(heart: Entity, artery: Entity) -> None:
    heart.memes["joy"] += 0.3
    artery.memes["curiosity"] += 0.4
    heart.say(
        f"{heart.id} the heart went PUMP-pump-pump tune, "
        f"sending {artery.pronoun('possessive')} buddy down the sunny lane."
    )

def journey_begin(artery: Entity) -> None:
    artery.memes["curiosity"] += 0.2
    artery.say(
        f"{artery.label} zigged and zagged on a merry mission there, "
        f"carrying red blood every route to share."
    )

def encounter_nuisance(world: World, artery: Entity, nuisance: Entity) -> None:
    world.say(
        f"Oh!  A {nuisance.phrase} ahead blocked the fun right away, "
        f"but {artery.label} frowned—‘I’ll push and I’ll shove!’ they would say."
    )

def share_comes_to_help(world: World, org: Entity, artery: Entity) -> None:
    world.say(
        f"Then {org.id} piped up, ‘We’ll send you our {org.helper}!’ "
        f"‘Fresh streams will clear every clogging bummer!’"
    )
    org.meters["share_points"] = 2

def happy_outro(artery: Entity, region: str) -> None:
    artery.memes["joy"] += 0.5
    artery.say(
        f"Now {region} is bright with life anew, "
        f"and {artery.label} dances on its happy merry way to you!"
    )

def full_nursery_stanza(title: str, body: str) -> str:
    return f"\n\n{title}\n{body}\n"

# ---------------------------------------------------------------------------
# A tiny heart and one little artery become a story right away
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    location: str
    context: str          # resting, playing, working
    weather: str = ""

def tell(setting: Setting, name: str = "Twinkle", obstacle_type: str = "clog") -> World:
    world = World(setting)
    region = setting.location

    # Place the StrongHeart character
    heart = world.add(Entity(
        id="StrongHeart",
        kind="character",
        label="the heart",
        phrase="the strong pump at the center of the tale",
        region=region,
    ))

    # Our star artery; give it a nursery name and a region
    artery_id = name.replace(" ", "")
    artery = world.add(Entity(
        id=artery_id,
        kind="character",
        label=name,
        phrase="the lively red artery",
        region=region,
        meters={"clogness": 0.0, "stretchiness": 0.0, "goodness": 0.0, "mileage": 0.0},
        memes={"curiosity": 0.5, "frustration": 0.0, "joy": 0.2},
    ))

    # An organ helper co-located
    org_id = f"{region}_helper"
    helper = world.add(Entity(
        id=org_id,
        kind="organ_helper",
        label=ORGANS[org_id]["label"] if org_id in ORGANS else "a nearby helper",
        region=region,
        helper=ORGANS[org_id]["share"] if org_id in ORGANS else "helpful push",
        meters={"share_points": 2},
    ))

    # Act 1: gentle introduction
    world.paragraphs = [[nursery_rhyme_title(name)]]
    gentle_intro(heart, artery)
    journey_begin(artery)

    # Occasionally drop a nuisance body in the same region
    if random.Random().random() < 0.8 or obstacle_type != "none":
        nuisance = world.add(Entity(
            id=f"{obstacle_type}_{artery_id}",
            kind="thing",
            label=obstacle_type,
            phrase=f"little {obstacle_type} in the way",
            region=region,
        ))
        encounter_nuisance(world, artery, nuisance)

    # Act 2: obstacles → growing frustration
    world.para()
    if obstacle_type != "none":
        _ = _r_spot_nuisance(world)

    # Act 3: sharing and resolution
    world.para()
    share_comes_to_help(world, helper, artery)
    _ = _r_clearing_share(world)
    _ = _r_bounce_back(world)
    world.para()
    happy_outro(artery, region)

    # Capture final state for Q&A
    world.facts.update(
        artery=artery,
        heart=heart,
        helper=helper,
        obstacle_type=obstacle_type,
        location=region,
        context=setting.context,
        total_goodness=sum(e.meters.get("goodness",0) for e in world.entities.values()),
        clog_count=sum(1 for e in world.entities.values()
                       if e.meters.get("clogness",0) >= THRESHOLD),
    )

    return world

# ---------------------------------------------------------------------------
# Registries: no swapable knobs for this tiny world; fixed settings & plots
# ---------------------------------------------------------------------------
SETTINGS = {
    "chest": Setting(location="chest", context="resting"),
    "abdomen": Setting(location="abdomen", context="playing"),
    "legs": Setting(location="legs", context="working"),
}

CONTEXTS = {"resting", "playing", "working"}
OBSTACLE_TYPES = list(NUISANCES) + ["none"]

# ---------------------------------------------------------------------------
# Story parameters — the tiny domain switches
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    location: str
    context: str
    obstacle_type: str
    name: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A Generators — child-facing, concrete, full sentences
# ---------------------------------------------------------------------------
def generation_prompts(_: World) -> list[str]:
    return [
        'Tell a short, gentle story for 3-to-6-year-olds about a happy little artery '
        'dancing through tubes, carrying red blood, meeting obstacles, and having helpers.',
        'Write a TinyStory on the theme “curiosity, sharing, and rhyme” that uses '
        'the words “artery” and “nuisance”.',
        'Create a nursery rhyme with anapestic meter on the topic of blood vessels '
        'helping each other to stay clear of clogs.'
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    art, hel = f["artery"], f["helper"]
    region = f["location"]
    obstacle = f["obstacle_type"]
    joy = art.memes.get("joy",0) >= THRESHOLD
    clean = art.meters.get("clogness",5) < THRESHOLD
    qa: list[QAItem] = [
        QAItem(
            question="Who was the main character in the little blood-vessel story?",
            answer=f"The main character was {art.label}, a tiny red artery dancing through "
                   f"{region} bringing fresh life and red blood drops with each beat."
        ),
        QAItem(
            question="Where did this little artery travel and dance?",
            answer=f"It traveled and danced inside {region}, going zig-zag on a merry route "
                   "to bring nutrients and oxygen to all the places that need to play every day."
        ),
        QAItem(
            question="What little nuisance tried to block the artery’s merry way?",
            answer=(f"A small {obstacle} appeared in {region} which wanted to block the "
                    "red-blood highway, but our little friend pushed and wiggled through with "
                    "help from friends nearby.")
        ),
    ]
    if joy and clean:
        qa.append(QAItem(
            question="How did the story end for the little artery and its red blood?",
            answer=(
                "At the end, the little artery was dancing happily again because "
                f"{hel.label} had shared {hel.helper} to clear every cloggy bummer, "
                "and the red blood could flow freely once more."
            )
        ))
    return qa

def world_knowledge_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an artery in a body?",
            answer="An artery is a tiny tube that carries fresh red blood from "
                   "the heart to all the places that need life—like muscles, lungs, "
                   "and the tummy."
        ),
        QAItem(
            question="Why do some arteries get clogged and narrow?",
            answer="Sometimes yucky stuff builds up inside the tubes and makes "
                   "it hard for the red blood to go through, so the tubes feel "
                   "grumpy and narrow."
        ),
        QAItem(
            question="How can you keep your arteries healthy so blood can flow freely?",
            answer="Moving your body, drinking water, and eating good food helps "
                   "keep the tubes stretchy and clear so they can dance with the red stream."
        ),
        QAItem(
            question="What do you call words that sound the same at the end of lines in poems?",
            answer="Words that rhyme at the end of lines are called rhyming words, "
                   "and nursery rhymes are full of twinkly rhyming tunes."
        )
    ]

# ---------------------------------------------------------------------------
# ASP Twin — the declarative twin checking our tiny gates
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An obstacle is a nuisance in a region served by an artery.
has_obstacle(Region) :- nuisance(_, Region, _).

% An artery is happy when clogness is low and goodness is high.
is_happy(Artery) :- artery(Artery,_), clogness(Artery,C), goodness(Artery,G), C<2, G>2.
is_happy(Artery) :- has_share_help(Artery).

% If an artery can receive sharing help it clears its troubles.
has_share_help(Artery) :- organ_helper(O,Region), affords_share(O,Artery),
                          clogness(Artery,C), C>=1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc, setg in SETTINGS.items():
        lines.append(asp.fact("location", loc))
        lines.append(asp.fact("context", loc, setg.context))
    for art in ARTERY_NAMES:
        lines.append(asp.fact("artery", art))
    for obs in NUISANCES:
        lines.append(asp.fact("nuisance_kind", obs))
    for olabel, ol in ORGANS.items():
        lines.append(asp.fact("organ_helper", olabel))
        lines.append(asp.fact("offers", olabel, ol["share"]))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple[str,int]]:
    import asp
    model = asp.one_model(asp_program("#show is_happy/1."))
    return sorted(set(asp.atoms(model, "is_happy")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set((a.id, 1) for a in ARTERY_NAMES)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches artery cast ({len(clingo_set)} tellable stories).")
        return 0
    print("MISMATCH between clingo and python valid_story sets:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny Nursery Circulation World: a little artery danced through tubes!")
    ap.add_argument("--location", choices=SETTINGS, help="body region for the tale")
    ap.add_argument("--context", choices=CONTEXTS, help="body state: resting|playing|working")
    ap.add_argument("--obstacle", choices=OBSTACLE_TYPES, dest="obstacle_type",
                    help="tiny nuisance to meet")
    ap.add_argument("--name", help="name for the star artery")
    ap.add_argument("-n", type=int, default=1, help="how many stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducibility")
    ap.add_argument("--all", action="store_true", help="show the classic tiny trio")
    ap.add_argument("--trace", action="store_true", help="print world meter state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="show the clingo-valid artery roster")
    ap.add_argument("--verify", action="store_true", help="ASP vs Python gate parity")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle_type:
        if not valid_combo(args.location or "chest", args.context or "resting", args.obstacle_type):
            raise StoryError(explain_rejection(args.context or "resting", args.obstacle_type))

    chosen_location = args.location or rng.choice(list(SETTINGS))
    chosen_context = args.context or rng.choice(list(CONTEXTS))
    chosen_obstacle = args.obstacle_type or rng.choice(OBSTACLE_TYPES)
    chosen_name = args.name or rng.choice(ARTERY_NAMES)

    return StoryParams(
        location=chosen_location,
        context=chosen_context,
        obstacle_type=chosen_obstacle,
        name=chosen_name,
        seed=args.seed,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.location], params.name, params.obstacle_type)
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
        print("\n--- world state ---")
        for e in sample.world.entities.values():
            print(f"{e.id:>12} | clog={e.meters.get('clogness',0):.2f} "
                  f"stretch={e.meters.get('stretchiness',0):.2f} "
                  f"good={e.meters.get('goodness',0):.2f} "
                  f"joy={e.memes.get('joy',0):.2f}")

def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation asks that tell this tiny story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Wh-questions grounded in this little artery tale ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) General child-level facts on arteries and rhymes ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)

# Curated, constraint-valid trio
CURATED = [
    StoryParams(location="chest",  context="resting", obstacle_type="twist",  name="Bounce Tube"),
    StoryParams(location="abdomen",context="playing", obstacle_type="clog",   name="Skip Line"),
    StoryParams(location="legs",   context="working", obstacle_type="narrow", name="Jolly Route"),
]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} clingo-valid tiny artery stories:\n")
        for name, _ in stories:
            print(f"  - {name}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(1000000)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n*30, 50):
            i += 1
            seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} – {p.location} ({p.context})"
        elif len(samples) > 1:
            header = f"### variant {idx+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples)-1:
            print("="*80 + "\n")

if __name__ == "__main__":
    main()
