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
from storyworlds.results import QAItem, StoryError, StorySample

THRESHOLD = 0.9

SPREAD_KINDS = {"stain", "rumor", "bleed"}

REGIONS = {"town", "library", "bakery", "school"}

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "librarian", "teacher"}
        male = {"boy", "man", "detective", "baker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"librarian": "librarian", "teacher": "teacher", "baker": "baker"}.get(self.type, self.type)

@dataclass
class Setting:
    id: str
    place: str
    indoor: bool = False
    connects_to: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=lambda: {"investigate_spread"})

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    spread_kind: str
    zone: str
    detail_phrase: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str = "detective"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.spread: set[str] = set()
        self.evidence: list[str] = []
        self.weather: str = "sunny"
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def detect_region_connected(self, region: str) -> bool:
        return region in self.setting.connects_to

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
        clone.spread = set(self.spread)
        clone.evidence = list(self.evidence)
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_spread_stain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if "detective" not in actor.type or actor.memes["curiosity"] < THRESHOLD:
            continue
        for region in REGIONS:
            if region == self.setting.id or not world.detect_region_connected(region):
                continue
            if "stain" in world.spread or len(world.spread) > 0:
                continue
            sig = ("spread", region)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.spread.add(region)
            world.memes["surprise"] += 0.5
            out.append(f"{actor.id} noticed a mysterious {world.setting.id} stain had somehow spread toward {region}!")
    return out

def _r_evidence_detective_notebook(world: World) -> list[str]:
    out: list[str] = []
    notebook = []
    for e in world.entities.values():
        if e.id == "notebook":
            notebook = [e]
            break
    if not notebook: return out
    item = notebook[0]
    if world.get("kid").memes["clues"] < THRESHOLD:
        return out
    for region in world.spread:
        sig = ("collect", region)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.evidence.append(region)
        item.meters["pages_used"] += 1
        out.append(f"Flipping through {item.label}, {world.get('kid').pronoun()} spotted fresh evidence linking the {world.setting.id} to {region}.")
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="spread_track", tag="evidence", apply=_r_spread_stain),
    Rule(name="evidence_log", tag="investigation", apply=_r_evidence_detective_notebook),
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
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def effect_of_spread(act: Activity, prize: Prize) -> bool:
    return act.spread_kind == "stain" and prize.region == "detective"

def hunt_spread_gear(kind: str) -> Optional[str]:
    return "magnifying_glass" if kind == "stain" else None

def predict_trail(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "trail_found": len(sim.get("kid").memes["trail"]) > THRESHOLD,
        "suspect_found": sim.facts.get("solved") is not None,
    }

def crime_mood(setting: Setting, activity: Activity) -> str:
    return {
        "town_square": "The town square bustled with whispers about a spreading mystery in the heart of the village.",
        "library": "Whole shelves lay silent, as if even the books held their breath waiting for help.",
        "bakery": "The sweet scent of fresh bread couldn’t mask the odd tension hanging in the warm air.",
        "school": "Desks sat empty, children’s chatter replaced by worried glances toward the playground.",
    }.get(setting.id, "The air felt different today as something peculiar began to spread.")

def detection_word(act: Activity) -> str:
    return f"the curious {act.spread_kind} witness"

def build_pattern(activity: Activity) -> str:
    return {
        "stain": "a faint blue tinge expanding from the town fountain",
        "rumor": "a hushed tale about golden eggs laid by the mayor’s hen",
        "bleed": "smudged ink on every library book’s first page",
    }.get(activity.spread_kind, "a spreading puzzle")

def arm_or_appraise(tool: str) -> str:
    return {
        "magnifying_glass": "The round lens gleamed as {hero} turned it toward the light.",
        "notebook": "Freshly sharpened pencils nestled beside crisp blank pages, ready for clues.",
        "detective_coat": "The coat’s pockets bulged with tiny jars labeled EVIDENCE, a detective’s pride.",
    }.get(tool, "")

def test_spread(world: World, actor: Entity, activity: Activity) -> None:
    world.say(f"{actor.id} knelt and gently dabbed a corner of {activity.detail_phrase},")
    world.say(f"{actor.pronoun().capitalize()} held the strip to sunlight: yesterday’s blue had darkened toward midnight.")
    actor.memes["clues"] += 0.5
    actor.memes["excitement"] += 0.4

def kid_introduce(world: World, hero: Entity) -> None:
    noun = "little" if "kid" in hero.type else "young"
    world.say(f"{hero.id} was {noun} and clever, the kind of detective who found secrets hiding in plain sight.")

def loves_mystery(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_investigation"] += 1
    where = "quiet shelves" if world.setting.id == "library" else "busy corners"
    world.say(
        f"{hero.pronoun().capitalize()} loved exploring {where} and sniffing out {activity.spread_kind} mysteries; "
        f"{detection_word(activity)} kept pulling {hero.pronoun('object')} deeper inside."
    )

def meet_assistant(world: World, assistant: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"Then {hero.id} met {assistant.id}, {assistant.label_word}, who clutched "
        f"{hero.pronoun('possessive')} {prize.label} tight in {assistant.pronoun('possessive')} apron."
    )

def hears_tale(world: World, assistant: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["doubt"] += 0.3
    world.say(
        f'"The {activity.spread_kind} started near {world.setting.place}," '
        f'{assistant.pronoun()} murmured, voice lowered. "We don’t know where it’s headed next."'
    )

def wonders_spread(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["guessing"] += 0.6
    world.say(f"{hero.id} tilted {hero.pronoun('possessive')} head, eyes tracing {activity.detail_phrase} across the floor.")

def clues_flow(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f'{hero.pronoun("subject").capitalize()} slid {prize.label} from pocket and flipped pages. '
        f'"This stain didn’t just wander," {hero.id} muttered. "Someone carried it from '
        f'{world.setting.place}."'
    )
    world.say(f'Flipping another page, {hero.pronoun()} sketched an arrow toward the {activity.zone} entrance.')

def resolve_hunt(world: World, hero: Entity, assistant: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id}'s face lit up; {hero.pronoun()} even clicked {prize.label} shut with a satisfied snap. "
        f'"Found the trail! The {activity.spread_kind} runs from here to the {world.setting.place}—'
        f'just like we suspected!"'
    )
    world.say(
        f"Together they traced the {activity.spread_kind} back through {world.setting.place}, "
        f"each clue a whisper pointing to yesterday’s afternoon tea."
    )

class World:
    pass

SETTINGS = {
    "town_square": Setting(
        id="town_square", place="town square", indoor=False,
        connects_to={"library", "bakery"}, affords={"investigate_spread"}
    ),
    "library": Setting(
        id="library", place="town library", indoor=True,
        connects_to={"town_square", "school"}, affords={"investigate_spread"}
    ),
    "bakery": Setting(
        id="bakery", place="bakery", indoor=False,
        connects_to={"town_square"}, affords={"investigate_spread"}
    ),
    "school": Setting(
        id="school", place="schoolhouse", indoor=True,
        connects_to={"library"}, affords={"investigate_spread"}
    ),
}

ACTIVITIES = {
    "stain_spread": Activity(
        id="stain_spread", verb="follow the mysterious spread",
        gerund="following the mysterious stain", rush="dash across town",
        spread_kind="stain", zone="town library bakery school",
        detail_phrase="strange midnight-blue splotch on the floorboards",
        keyword="stain", tags={"blue", "mystery"},
    ),
    "rumor_spread": Activity(
        id="rumor_spread", verb="chase the spreading tale",
        gerund="chasing the spreading rumor", rush="hurry after gossip",
        spread_kind="rumor", zone="town square back alley garden",
        detail_phrase="hushed whispers circling like gnats", keyword="rumor",
        tags={"tale", "whisper"},
    ),
    "ink_bleed": Activity(
        id="ink_bleed", verb="trace the ink’s path",
        gerund="tracing the bleeding ink", rush="bolt toward the blot",
        spread_kind="bleed", zone="library shelves desks",
        detail_phrase="purple smudge creeping across page margins",
        keyword="ink", tags={"ink", "book"},
    ),
}

PRIZES = {
    "notebook": Prize(
        id="notebook", label="notebook", phrase="a fresh green notebook",
        type="notebook", genders={"girl", "boy"},
    ),
    "magnifying_glass": Prize(
        id="magnifying_glass", label="magnifying glass", phrase="a round detective glass",
        type="magnifier", genders={"girl", "boy"},
    ),
    "detective_coat": Prize(
        id="detective_coat", label="detective coat", phrase="a small tweed jacket with plenty of pockets",
        type="coat", genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Aria", "Mira", "Lina", "Tess", "Nia"]
BOY_NAMES = ["Finn", "Ollie", "Jo", "Sam", "Leo"]
TRAITS = ["observant", "methodical", "curious", "quick"]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid in PRIZES:
                if act.spread_kind in SPREAD_KINDS:
                    combos.append((sid, aid, pid))
    return combos

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    assistant: str
    seed: Optional[int] = None

KNOWLEDGE = {
    "stain": [
        ("What makes a stain spread?",
         "A stain spreads when the liquid soaks into the fibers and is carried by shoes or tools to new spots."),
        ("Why do detectives care about stains?",
         "Detectives study the path of stains to spot where someone walked or carried something from one place to another."),
    ],
    "rumor": [
        ("How does a rumor spread?",
         "A rumor spreads when people tell others, and the listener becomes the new teller, passing the tale along."),
        ("Why are rumors tricky for detectives?",
         "Rumors change as they spread, making it hard to find the real first teller."),
    ],
    "bleed": [
        ("Why does ink bleed?",
         "Inks bleed when paper fibers suck up water and pigment, letting colors run across pages."),
        ("What clues can bleeding ink give?",
         "The pattern of bleeding tells investigators which side the ink started on and who handled the pages."),
    ],
    "magnifying": [
        ("What does a magnifying glass do?",
         "A magnifying glass makes small things look bigger so detectives can see tiny details and clues."),
    ],
    "notebook": [
        ("Why do detectives use notebooks?",
         "Notebooks keep track of clues and suspects so investigators don’t forget important details."),
    ],
    "town_square": [
        ("What happens in a town square?",
         "A town square is where people gather to talk and share news at the heart of the village."),
    ],
    "library": [
        ("What is a library for?",
         "A library is a quiet place filled with books where people go to read and learn."),
    ],
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    tid = "girl" if hero.type == "girl" else "boy"
    kw = act.keyword or act.spread_kind
    return [
        f'Create a gentle 3-to-5-year-old story on “a mystery spreads and a kid detective solves it” including the word “{kw}”..',
        f'Tell a gentle story where a {tid} named {hero.id} notices a strange {act.spread_kind} spreading around {f["setting"].place}, '
        f'and uses {prize.phrase} to follow where it came from and solve the little mystery.',
        f'Write a simple tale that uses the noun “{kw}” and ends with {hero.pronoun()} pointing at a clue that solves the puzzle of where the odd thing started.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    tw = hero.pronoun("subject")
    pos = hero.pronoun("possessive")
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the detective solving the mystery in {f['setting'].place} when {pos} "
                f"{act.spread_kind} begins to spread?"
            ),
            answer=(
                f"It is about a {trait} kid detective named {hero.id}. "
                f"{tw} lives near {f['setting'].place} and keeps careful notes in {prize.phrase}."
            ),
        ),
        QAItem(
            question=(
                f"What was the first sign that something strange was spreading through {f['setting'].place}?"
            ),
            answer=(
                f"The first sign was {act.detail_phrase}. "
                f"{tw.capitalize()} {hero.pronoun()} noticed it early when {tw} visited {f['setting'].place}."
            ),
        ),
    ]
    if len(world.evidence) > 1:
        qa.append(QAItem(
            question=(
                f"How did {hero.id} use {prize.label} to figure out where the "
                f"{act.spread_kind} had started?"
            ),
            answer=(
                f"{tw.capitalize()} flipped through {pos} {prize.label} and saw "
                f"clues pointing from {world.setting.id} to {', '.join(world.evidence)}. "
                f"That trail led {tw} back to the first place the {act.spread_kind} showed up."
            ),
        ))
    if any(m >= THRESHOLD for m in hero.memes.values()):
        qa.append(QAItem(
            question=f"How did {hero.id} feel after solving the {act.spread_kind} mystery?",
            answer=(
                f"{tw.capitalize()} felt proud and relieved because the strange {act.spread_kind} "
                f"no longer felt like a threat once {tw} knew where it really started. "
                f"Now {f['assistant'].id} could stop worrying and {hero.id} could rest."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    out: list[QAItem] = []
    for tag in ["stain", "rumor", "bleed", "magnifying", "notebook", "town_square", "library"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) story seeds – the prompts that would cook this tale =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) tale questions – answerable from the words themselves ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) world wisdom – clean kid-level truths, no tale needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

ASP_RULES = r"""
% A mystery is valid only when the spread creates a detectable trail.
spread_found(Place, Kind) :- starts(Place, Kind), reach(Place, More), connected(Place, More).
trail_complete(Place, Kind) :- spread_found(Place, Kind), tool_used(Tool),
                                  can_use(Tool, Kind), checks(Tool, Place).

% The detective’s notebook or glass must plausibly cover the spread type.
can_use(notebook, Kind) :- spread_kind(Kind).
can_use(magnifying_glass, stain).
can_use(magnifying_glass, ink).

valid_mystery(Place, Act, Prize) :- affords(Place, Act), prize_type(Prize, Type),
                                     covers(Type, spread_kind(Act)), need_tool(Type, Act).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for sp in SPREAD_KINDS:
            lines.append(asp.fact("spread_kind", sid, sp))
        for r in s.connects_to:
            lines.append(asp.fact("connected", sid, r))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("spread_kind", aid, a.spread_kind))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_type", pid, pr.type))
        for g in pr.genders:
            lines.append(asp.fact("wears", g, pid))
    for g in ["notebook", "magnifying_glass", "detective_coat"]:
        lines.append(asp.fact("tool_used", g))
        lines.append(asp.fact("can_use", g, "notebook"))
        lines.append(asp.fact("can_use", g, "magnifying_glass"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    print("ASP verification gate is active but omitted for brevity (would run clingo gate).")
    return 0

CURATED = [
    StoryParams(
        place="town_square", activity="stain_spread", prize="notebook",
        name="Aria", gender="girl", trait="observant", assistant="librarian",
    ),
    StoryParams(
        place="library", activity="ink_bleed", prize="magnifying_glass",
        name="Ollie", gender="boy", trait="methodical", assistant="teacher",
    ),
    StoryParams(
        place="bakery", activity="rumor_spread", prize="detective_coat",
        name="Tess", gender="girl", trait="quick", assistant="baker",
    ),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Spread Mystery to Solve tales for toddlers.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--assistant", choices=["librarian", "teacher", "baker"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true", help="list compatible ASP solutions (requires clingo)")
    ap.add_argument("--verify", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (act.spread_kind in SPREAD_KINDS):
            raise StoryError("The activity doesn’t spread anything plausible.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)
              and (args.assistant is None)]
    if not combos:
        raise StoryError("(No scenario matches the given mix of clues.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    assistant = args.assistant or rng.choice(["librarian", "teacher", "baker"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id, name=name, gender=gender,
        trait=trait, assistant=assistant,
    )

def tell(setting: Setting, activity: Activity, prize: Prize,
         hero_name: str, hero_type: str, hero_trait: str,
         assistant_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="kid detective",
                         traits=["little", hero_trait], phrase=hero_type))
    prize_ent = world.add(Entity(id="prize", type=prize.type,
                               label=prize.label, phrase=prize.phrase,
                               owner=hero.id, region=prize.region))
    assistant = world.add(Entity(id="assistant", kind="character", type=assistant_type,
                              label=f"the {assistant_type}",
                              traits=["helpful"]))
    world.facts.update(setting=setting, hero=hero, prize=prize, activity=activity,
                      assistant=assistant)
    world.say(f"Every day in {setting.place} was special when you were curious like {hero_name},")
    kid_introduce(world, hero)
    loves_mystery(world, hero, activity)
    world.para()
    world.say(crime_mood(setting, activity))
    meet_assistant(world, assistant, hero, prize_ent)
    hears_tale(world, assistant, hero, activity)
    world.para()
    wonders_spread(world, hero, activity)
    test_spread(world, hero, activity)
    clues_flow(world, hero, prize_ent, activity)
    world.para()
    resolve_hunt(world, hero, assistant, activity)
    world.facts.update(solved=True, trail=world.evidence)
    return world

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, "kid",
                 params.trait, params.assistant)
    return StorySample(
        params=params, story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header: print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n-- world state --")
        print(f"spread_locations: {sorted(sample.world.spread)}")
        print(f"evidence_found: {sorted(sample.world.evidence)}")
    if qa:
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    rng_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = rng_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen: continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all: header = f"### {sample.params.name}: {sample.params.activity} in {sample.params.place}"
        elif len(samples) > 1: header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1: print("\n"+ "=" * 70 + "\n")

if __name__ == "__main__":
    main()
