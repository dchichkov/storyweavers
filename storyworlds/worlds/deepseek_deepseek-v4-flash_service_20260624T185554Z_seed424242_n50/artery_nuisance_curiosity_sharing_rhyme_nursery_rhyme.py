#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/artery_nuisance_curiosity_sharing_rhyme_nursery_rhyme.py
==============================================================================================================================

A nursery‑rhyme storyworld: a curious child, a nuisance on the village artery,
sharing a rhyme to make things right.  Prose is written in rhythmic couplets.
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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "maiden"}
        male = {"boy", "father", "lad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mum", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the village artery"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    rhyme_line: str = ""          # a line that rhymes with the story couplet
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
        self.weather: str = ""
        self.facts: dict = {}
        # track if we used rhyme to share
        self.shared_rhyme: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.shared_rhyme = self.shared_rhyme
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_irritate(world: World) -> list[str]:
    """The nuisance’s noise increases when curious child approaches."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        nuisance = world.entities.get("nuisance")
        if nuisance and "noise" in nuisance.meters:
            sig = ("irritate", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                nuisance.meters["noise"] += 1
                out.append("The clatter grew louder, a terrible sound.")
    return out


def _r_share_rhyme(world: World) -> list[str]:
    """When child shares a rhyme, nuisance of noise fades."""
    if not world.shared_rhyme:
        return []
    nuisance = world.entities.get("nuisance")
    if not nuisance or nuisance.meters.get("noise", 0) <= 0:
        return []
    sig = ("calm", "nuisance")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    nuisance.meters["noise"] = 0
    return ["The noise slipped away like a sigh after rain."]


CAUSAL_RULES: list[Rule] = [
    Rule(name="irritate", tag="social", apply=_r_irritate),
    Rule(name="share_rhyme", tag="social", apply=_r_share_rhyme),
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
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Verb helpers (rhymed narrative)
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"Little {hero.type} {hero.id} was {trait} and bright,")
    world.say(f"Loving the artery from morning till night.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.verb}, oh what a treat,")
    world.say(activity.rhyme_line)


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.id}'s {parent.label_word} bought {hero.pronoun('object')} {prize.phrase},")
    world.say(f"A shiny new prize for {hero.pronoun('possessive')} daily {activity}.")  # placeholder activity


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} so,")
    world.say(f"{hero.pronoun().capitalize()} wore {prize.it()} wherever {hero.pronoun()} chose to go.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One sunny day they went to the artery lane,")
    world.say(f"Curious {hero.id} wanted to {activity.verb} again.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right then,")
    world.say(f"But {parent.label_word} said, 'Wait, my little hen.'")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"Oh child, the {activity.mess} will spoil your {prize.label},"')
    world.say(f'"And cleaning it later is a terrible spell."')
    return True


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
    }


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning but still felt the pull,")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush} — the turn was full.")


def grab_hand(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    world.say(f"But {parent.label_word} grabbed {hero.pronoun('possessive')} hand with care,")
    world.say(f'"There is a nuisance, we must beware."')


def pout(world: World, hero: Entity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f"{hero.id} pouted and folded {hero.pronoun('possessive')} arms,")
        world.say(f'"But I want to explore all the artery farms!"')


def see_nuisance(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"A clattering cart, a noisy old thing,")
    world.say(f"Blocked the artery — what a nuisance it brings!")


def share_rhyme(world: World, hero: Entity, activity: Activity) -> None:
    world.shared_rhyme = True
    hero.memes["sharing"] += 1
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} thought of a rhyme {hero.pronoun()} learned at school,")
    world.say(f"And shared it aloud: 'Oh noisy old mule!'")
    propagate(world)  # will trigger the calming rule


def resolve(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    world.say(f"The cart gave a creak and quietly rolled away,")
    world.say(f"{hero.id} could {activity.verb} on a much safer day.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {prize.label} stayed clean, not a speck of {activity.mess},")
    world.say(f"And {parent.label_word} kissed {hero.pronoun('object')}, so full of success.")


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Pip", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "sunny"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "curious", "kind"],
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    # Add the nuisance as a character-like entity
    nuisance = world.add(Entity(
        id="nuisance", kind="thing", type="cart",
        label="clattering cart",
        phrase="a noisy old cart that blocks the way",
    ))

    # Act 1 – setup
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 – conflict
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    world.say(f"But the nuisance was there, right in the {setting.place} —")  # missing decl
    defies(world, hero, activity)
    grab_hand(world, parent, hero)
    see_nuisance(world, hero, parent)
    pout(world, hero)

    # Act 3 – resolution through sharing a rhyme
    world.para()
    share_rhyme(world, hero, activity)
    resolve(world, hero, parent, activity, prize)

    # Record facts for Q&A
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, nuisance=nuisance,
                       conflict=True, resolved=True)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "artery": Setting(place="the village artery", indoor=False, affords={"stroll"}),
}

ACTIVITIES = {
    "stroll": Activity(
        id="stroll",
        verb="stroll down the artery",
        gerund="strolling down the artery",
        rush="skip down the street",
        mess="dusty",
        soil="dusty and grey",
        zone={"legs"},
        rhyme_line="A walk on the artery, steady and neat.",
        keyword="artery",
        tags={"street", "walk"},
    ),
}

PRIZES = {
    "cap": Prize(
        label="new red cap", phrase="a new red cap with a shiny visor",
        type="cap", region="torso", genders={"girl", "boy"},
    ),
    "scarf": Prize(
        label="woolly scarf", phrase="a long woolly scarf of blue and white",
        type="scarf", region="torso", genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="sturdy boots",
        covers={"legs"},
        guards={"dusty"},
        prep="put on our sturdy boots",
        tail="put on their sturdy boots",
        plural=True,
    ),
]

GIRL_NAMES = ["Pip", "Nell", "Rose", "Lily", "Mae"]
BOY_NAMES = ["Tom", "Ben", "Sam", "Leo", "Finn"]
TRAITS = ["curious", "kind", "brave", "lively"]


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
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "artery": [
        ("What is an artery in the story?",
         "In the story, the artery is the main road through the village "
         "where everyone walks and plays."),
    ],
    "nuisance": [
        ("What does 'nuisance' mean?",
         "A nuisance is something annoying, like a loud cart that blocks "
         "the way and makes a clatter."),
    ],
    "stroll": [
        ("What does it mean to stroll?",
         "To stroll is to walk slowly and enjoy the place, looking around "
         "with curiosity."),
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is a little poem where words sound the same at the end, "
         "like 'cart' and 'start'."),
    ],
}
KNOWLEDGE_ORDER = ["artery", "nuisance", "stroll", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        f'Write a nursery rhyme where a {hero.type} named {hero.id} meets '
        f'a nuisance on the {world.setting.place}.',
        f'Tell a simple rhyme about {act.gerund} and sharing a song to '
        f'solve a problem.',
        f'Include the words "artery" and "nuisance" in a gentle poem for young children.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a {hero.traits[0]} {hero.type} named {hero.id} "
                   f"and {pos} {pw} on the {world.setting.place}.",
        ),
        QAItem(
            question=f"What nuisance did {hero.id} meet on the artery?",
            answer=f"{hero.id} met a clattering old cart that blocked the way "
                   f"and made a terrible noise.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the nuisance?",
            answer=f"{hero.id} shared a friendly rhyme with the cart, and the "
                   f"noise faded away, so {sub} could {act.verb} safely.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
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
    lines.append("== (3) World‑knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / trace
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="artery", activity="stroll", prize="cap",
                name="Pip", gender="boy", parent="mother", trait="curious"),
    StoryParams(place="artery", activity="stroll", prize="scarf",
                name="Nell", gender="girl", parent="father", trait="kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery‑rhyme storyworld: artery, nuisance, curiosity, sharing, rhyme.")
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
    # only one setting and one activity exist, so trivial
    place = "artery"
    activity = "stroll"
    combos = valid_combos()
    if args.prize and args.prize not in [c[2] for c in combos]:
        raise StoryError("invalid prize for this activity")
    prize_id = args.prize or rng.choice([c[2] for c in combos])
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait], params.parent)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP twin (simplified – just enough for --verify)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(artery).
affords(artery, stroll).
activity(stroll).
mess_of(stroll, dusty).
splashes(stroll, legs).

prize(cap). prize(scarf).
worn_on(cap, torso). worn_on(scarf, torso).
wears(girl, cap). wears(boy, cap). wears(girl, scarf). wears(boy, scarf).

gear(boots).
guards(boots, dusty).
covers(boots, legs).

prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
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
# main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:")
        for t in triples:
            print(f"  {t[0]:8} {t[1]:8} {t[2]:8}")
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
