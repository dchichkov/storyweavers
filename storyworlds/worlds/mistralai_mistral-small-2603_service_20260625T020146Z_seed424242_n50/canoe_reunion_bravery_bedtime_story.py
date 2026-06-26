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

THRESHOLD = 1.0
MESS_KINDS = {"wet"}
REGIONS = {"feet", "legs", "torso"}

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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        mapping = {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}
        return mapping.get(self.type, self.type)

@dataclass
class Setting:
    place: str = "the lake shore"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    weather: str = "calm"

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
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
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def scored(action: str, entity: Entity, amount: float) -> None:
    if action == "increase":
        entity.memes["bravery"] += amount
        entity.memes["fear"] -= amount * 0.5
    elif action == "decrease":
        entity.memes["fear"] += amount

def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wetness"] < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.region and not item.protective and not world.covered(actor, item.region):
                sig = ("soak", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                if item.meters[item.meters] < THRESHOLD:
                    item.meters["dampness"] = min(1.0, item.meters.get("dampness", 0) + actor.meters["wetness"])
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} felt damp from the splash.")
    return out

def _r_bravery_state(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["bravery"] < THRESHOLD and actor.memes["fear"] >= 1.2:
            scored("increase", actor, 0.4)
            out.append(f"{actor.id} took a deep breath and tried to be brave.")
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="bravery_state", tag="emotional", apply=_r_bravery_state),
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

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone

def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if "wet" in gear.guards and prize.region in gear.covers:
            return gear
    return None

def activity_delight(activity: Activity) -> str:
    return "the soft lapping of water and the rustle of leaves mixed into a perfect evening song."

def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.weather == "stormy":
        return "Gentle rain tapped the water and the lantern flickered."
    return "Stars glittered above the quiet water, and an evening breeze danced through the pines."

def bravery_note(activity: Activity) -> str:
    return "bravery meant doing something even when your heart feels jumpy like a butterfly in your chest."

def _do_canoe(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if "canoeing" not in world.setting.affords:
        return
    actor.meters["wetness"] += 1
    if activity.mess in MESS_KINDS:
        actor.memes["fear"] += 1
    propagate(world, narrate=narrate)

def introduce_world(world: World, hero: Entity, setting: Setting) -> None:
    world.say(f"On a {setting.weather} evening by {setting.place}, the world felt full of quiet promise.")

def loves_canoeing(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    joy_detail = activity_delight(activity)
    world.say(f"{hero.pronoun().capitalize()} loved paddling under twinkling stars like {joy_detail}")

def family_visit_notice(world: World, hero: Entity, caretaker: Entity, visitor_type: str) -> None:
    visitor = caretaker.label_word if caretaker.label_word else visitor_type
    world.say(f"That evening, {hero.id} learned {hero.pronoun('possessive')} {visitor} would visit for story-time.")

def wants_to_go_crossing(world: World, hero: Entity, caretaker: Entity) -> None:
    caretaker_name = caretaker.label_word
    world.say(f"{hero.id} wanted to paddle across and greet {caretaker.pronoun('object')} by boat, but {hero.pronoun('possessive')} {caretaker_name} helped steady the canoe first.")

def warn_and_suggest(world: World, hero: Entity, caretaker: Entity, activity: Activity) -> None:
    world.say(f'"The water is dark tonight," {caretaker.id} said, hugging {hero.pronoun('possessive')} shoulders. "But if we use {hero.pronoun('possessive')} life jacket, you can feel safer paddling across."')

def don_gear(world: World, hero: Entity, gear_def: Gear) -> None:
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        worn_by=hero.id, protective=True, region=hero.region,
        covers=set(gear_def.covers), plural=False,
    ))
    hero.memes["bravery"] += 0.5
    hero.memes["fear"] -= 0.3
    world.say(f'{hero.pronoun("possessive").capitalize()} {caretaker.label_word} said, "{gear_def.prep}." Soon {hero.id} was snug with {gear.label}.')

def brave_canoeing(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["bravery"] += 0.8
    hero.memes["fear"] -= 0.6
    world.say(f'{hero.pronoun().capitalize()} pushed the canoe from the shore and began {activity.gerund}. The stars guided {hero.pronoun("object")}, now wearing {prize.label}.')

def reunite_and_rest(world: World, hero: Entity, visitor: Entity) -> None:
    world.say(f'At last, {hero.id} arrived and wrapped {hero.pronoun("possessive")} arms around {visitor.pronoun("object")}.')
    world.say(f'{visitor.pronoun().capitalize()} tucked a warm {hero.pronoun("possessive")} life jacket into a soft blanket and smiled. "Your bravery sparkled brighter than these stars." {hero.id}’s cheeks glowed, and soon {hero.pronoun()} was curled up, listening to stories, sleepy and warm.')

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, caretaker_type: str = "grandmother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["playful", "thoughtful"]),
    ))
    caretaker = world.add(Entity(
        id=f"{caretaker_type}_caretaker", kind="character", type=caretaker_type,
        label=caretaker_type.title(), traits=["gentle"],
    ))
    prize = world.add(Entity(
        id="reunion_blanket", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=caretaker.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    introduce_world(world, hero, setting)
    loves_canoeing(world, hero, activity)
    family_visit_notice(world, hero, caretaker, caretaker_type)
    world.para()
    wants_to_go_crossing(world, hero, caretaker)
    warn_and_suggest(world, hero, caretaker, activity)
    gear_def = select_gear(activity, prize_cfg)
    if gear_def:
        don_gear(world, hero, gear_def)
    world.para()
    brave_canoeing(world, hero, prize, activity)
    world.para()
    reunite_and_rest(world, hero, caretaker)

    world.facts.update(hero=hero, caretaker=caretaker, prize=prize,
                       activity=activity, setting=setting, gear=gear_def,
                       bravery_act=gear_def is not None)
    return world

SETTINGS = {
    "lake": Setting(place="the quiet lake shore", indoor=False, weather="calm", affords={"canoeing"}),
    "lake_stars": Setting(place="the lake shore under glittering stars", indoor=False, weather="calm", affords={"canoeing"}),
}

ACTIVITIES = {
    "canoeing": Activity(
        id="canoeing",
        verb="paddle across the lake",
        gerund="paddling across the lake in the twilight",
        rush="grab the paddle quickly",
        mess="wet",
        soil="damp and chilly",
        zone={"legs", "torso"},
        weather="calm",
        keyword="canoeing",
        tags={"canoe", "water", "brave"},
    ),
}

GEAR = [
    Gear(
        id="life_jacket",
        label="bright red life jacket",
        covers={"torso"},
        guards={"wet"},
        prep="grab the bright life jacket from the hook by the door",
        tail="zipped on the life jacket",
    ),
    Gear(
        id="poncho",
        label="yellow rain poncho",
        covers={"legs", "torso"},
        guards={"wet"},
        prep="pull the yellow poncho over their head",
        tail="took shelter under the yellow poncho",
    ),
]

PRIZES = {
    "blanket": Prize(
        label="blanket",
        phrase="a cozy red blanket woven with silver threads",
        type="blanket",
        region="torso",
        plural=False,
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["playful", "curious", "thoughtful", "gentle", "brave", "dreamy"]

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_key, setting in SETTINGS.items():
        act = ACTIVITIES["canoeing"]
        for prize_key, prize in PRIZES.items():
            if prize_at_risk(act, prize) and select_gear(act, prize):
                combos.append((setting_key, "canoeing", prize_key))
    return combos

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

KNOWLEDGE = {
    "canoe": [("What is a canoe?",
                "A canoe is a narrow boat that you paddle with a long stick called a paddle. "
                "People often use canoes to travel across calm lakes or rivers.")],
    "blanket": [("Why do people use blankets?",
                 "Blankets keep you warm and cozy. Wrapping in a blanket at bedtime helps your body relax "
                 "and signals your brain that it’s time to sleep.")],
    "bravery": [("What does being brave mean?",
                 "Being brave doesn’t mean you don’t feel scared. It means you do what’s right "
                 "even when you feel fear, like paddling across dark water to meet someone you love.")],
    "life_jacket": [("What is a life jacket used for?",
                     "A life jacket keeps you safely afloat in water. It’s shaped to turn you face-up "
                     "even if you fall in, so you can breathe and stay calm until help arrives.")],
}

KNOWLEDGE_ORDER = ["canoe", "blanket", "bravery", "life_jacket"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, care = f["hero"], f["caretaker"]
    act = f["activity"]
    subj = hero.pronoun("subject")
    poss = hero.pronoun("possessive")
    return [
        f'Write a gentle bedtime story for a 3-to-6-year-old about a child who feels nervous but '
        f'bravely does something kind and important. Include the word "stars" for calming imagery.',
        f'Tell a peaceful story where a {hero.type} named {hero.id} wants to greet {care.label_word} using '
        f'a canoe, and learns that bravery means trying even when you feel a little shaky inside.',
        f'Create a short bedtime tale that uses the noun "canoe" and ends with both characters '
        f'warm under a cozy blanket after a happy reunion.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, care = f["hero"], f["caretaker"]
    act = f["activity"]
    subj, obj, poss = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    bravery_act = "used the life jacket and paddled ahead alone" if f.get("gear") else "paddled bravely after getting the suggestion"
    return [
        QAItem(
            question=f"Who is the story about when {hero.id} goes to meet {care.id}?",
            answer=f"It is about {poss} little {hero.type} named {hero.id} and {poss} {care.label_word} {care.id}. "
                   f"They meet by the quiet lake under the starlit sky.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the lake that felt a little scary but brave?",
            answer=f"{hero.id} decided to paddle {act.gerund} to greet {care.pronoun('object')} despite feeling nervous. "
                   f'Using {poss} life jacket helped {obj} feel steadier on the water.',
        ),
        QAItem(
            question=f"What gift did {care.label_word} give {hero.id} after the brave moment?",
            answer=f"{care.pronoun().capitalize()} wrapped a warm {hero.pronoun('possessive')} new blanket around {hero.pronoun('object')} "
                   f"after they arrived safely, praising {obj} for {bravery_act}.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id.split("_")[0])
    out: list[QAItem] = []
    for kw in KNOWLEDGE_ORDER:
        if kw in tags or (kw == "blanket" and "reunion" in tags):
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(kw, []))
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ===")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge Q&A ===")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world state ---"]
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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

def explain_rejection(activity: Activity, prize: Prize) -> str:
    act_word = {"wet": "splashing around"}.get(activity.mess, activity.mess)
    return (f"(No story: {act_word} would make {prize.label} too damp to feel cozy, "
            f"and nothing in the gear list keeps blankets warm and dry when wet. "
            f"Try --gear that blocks water fully.)")

CURATED = [
    StoryParams(
        place="lake",
        activity="canoeing",
        prize="blanket",
        name="Lily",
        gender="girl",
        parent="grandmother",
        trait="thoughtful",
    ),
    StoryParams(
        place="lake_stars",
        activity="canoeing",
        prize="blanket",
        name="Tim",
        gender="boy",
        parent="grandmother",
        trait="brave",
    ),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a child, a canoe, and a cozy reunion. "
                                            "Unspecified choices are chosen at random (seeded).")
    ap.add_argument("--place", choices=list(SETTINGS.keys()))
    ap.add_argument("--activity", choices=list(ACTIVITIES.keys()))
    ap.add_argument("--prize", choices=list(PRIZES.keys()))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP vs Python gate")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.prize == "blanket" and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"(Blankets are gifts for both girls and boys; try a prize that fits the gender.")

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
    parent = args.parent or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice([t for t in TRAITS if t in ("playful", "thoughtful", "brave")])
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

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.weather == "stormy":
            lines.append(asp.fact("stormy", pid))
        for a in s.affords:
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in a.zone:
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in pr.genders:
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in g.guards:
            lines.append(asp.fact("guards", g.id, m))
        for r in g.covers:
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)

ASP_RULES = r"""
% A prize is at risk when the activity splashes the region it is worn on.
prize_at_risk(A, P) :- activity(A), prize(P), worn_on(P, R), splashes(A, R).

% Gear is a compatible fix only when it guards the mess kind AND
% covers the at-risk region of the prize.
protects(G, A, P) :- gear(G), guards(G, M), mess_of(A, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import asp
        clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid"))
        python_set = set((s[0], s[1], s[2]) for s in valid_combos())
        if clingo_set == python_set:
            print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
            return 0
        print("MISMATCH between clingo and Python gates:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1
    except Exception as e:
        print("ASP verification error:", e)
        return 1

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
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
            header = f"### {p.name}: {p.activity} at {SETTINGS[p.place].place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
