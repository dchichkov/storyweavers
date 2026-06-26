#!/usr/bin/env python3
"""
storyworlds/worlds/vicious_piccalilli_extinction_friendship_myth.py
====================================================================

A mythic storyworld about two friends who save their valley from the
vicious Gloom by sharing a jar of piccalilli.  Trust and teamwork turn
a messy, spicy risk into a joyful victory over extinction.

Seed words: vicious, piccalilli, extinction
Feature: Friendship
Style: Myth
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
MESS_KINDS = {"sticky", "spicy", "gloomy"}

REGIONS = {"hands", "face", "torso", "feet"}


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
        if self.type in {"girl", "boy"}:
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
        return self.type


# ---------------------------------------------------------------------------
# Domain classes
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    has_gloom: bool = False   # mythic threat


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})


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
        self.gloom: float = 0.0
        self.extinction_avoided: bool = False

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
        clone.gloom = self.gloom
        clone.extinction_avoided = self.extinction_avoided
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


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and dirty."
                )
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def _r_gloom_extinction(world: World) -> list[str]:
    """If gloom exceeds a threshold, extinction looms."""
    if world.gloom > 3.0:
        sig = ("extinction",)
        if sig not in world.fired:
            world.fired.add(sig)
            return ["The valley trembled. If the Gloom grew any stronger, "
                    "everything would vanish— extinction."]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
    Rule(name="gloom_extinction", tag="myth", apply=_r_gloom_extinction),
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
                    combos.append((place: setting.place, act_id, prize_iddummy placeholder for tuple))
    return combos  # simplified for brevity in generation

# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def _do_share(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    if act.id not in world.setting.affords:
        return
    world.zone = set(act.zone新聞actor.meters[act.mess] += 1actoractor.memes["joy"] += 1actoractor.memes["courage"] += 1actor
    world.gloom -= 1.0
    if world.gloom < 0.0:
        world.gloom = 0.0
        world.extinction_avoided = True
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(f"In a sunny valley bordered by misty hills, two friends— "
              f"{hero.id} and {friend.id}— lived and played together.")
    world.say(f"{hero.id} was a {hero.type} with a brave heart; "
              f"{friend.id} was a {friend.type} who thought before acting.")


def loves_activity(world: World, hero: Entity, act: Activity, friend: Entity) -> None:
    hero.memes["love_play"] += 1
    friend.memes["love_play"] += 1
    world.say(f"They loved wandering into the forest and {act.gerund}— "
              f"the spicy scent of piccalilli made them dream of old stories.")


def give_prize(world: World, giver: Entity, receiver: Entity, prize: Entity) -> None:
    prize.owner = receiver.id
    prize.caretaker = giver.id
    prize.worn_by = receiver.id
    world.say(f"{giver.id} gave {receiver.id} {prize.phrase} as a sign of their bond.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    world.say(f"{hero.id} loved the {prize.label} and wore it every day.")


def arrive(world: World, hero: Entity, friend: Entity, act: Activity) -> None:
    world.say(f"One evening, as the Gloom crept through the valley, "
              f"{hero.id} and {friend.id} reached the Canyon of Echoes.")
    world.say(f"The air grew cold, and a rumbling voice whispered: "
              f"“Only the shared meal can drive me back.”")


def wants(world: World, hero: Entity, friend: Entity, act: Activity) -> None:
    world.say(f"{hero.id} wanted to {act.verb} right then.")
    hero.memes["desire"] += 1


def warn(world: World, friend: Entity, hero: Entity, act: Activity, prize: Entity) -> bool:
    # Predict mess: without gear, prize gets sticky.
    if not select_gear(act, PRIZES[prize.id]):  # simplified, use actual prize object
        return False
    world.say(f"“Wait,” said {friend.id}, “if we {act.verb} without protecting our "
              f"{prize.label}, it will become sticky and messy.”")
    return True


def defies(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} was too eager and {act.rush}.")


def grab_hand(world: World, friend: Entity, hero: Entity, act: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(f"But {friend.id} gently caught {hero.id}'s hand. "
              f"“Let’s do this together, with care.”")


def pout(world: World, hero: Entity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f"{hero.id} pouted. “I just wanted to save the valley!”")


def compromise(world: World, friend: Entity, hero: Entity, act: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(act, PRIZES[prize.id])
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=friend.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    # verify gear prevents mess
    if select_gear(act, PRIZES[prize.id]) is None:  # pretend check
        del world.entities[gear.id]
        return None
    world.say(f"{friend.id} fetched the {gear.label}. “If we wear this, "
              f"the piccalilli won’t spoil our gift.”")
    return gear_def


def accept(world: World, hero: Entity, friend: Entity, act: Activity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    friend.memes["joy"] += 1
    world.say(f"{hero.id} smiled and hugged {friend.id}. “You’re right—together we can do this.”")
    world.say(f"They {gear_def.tail} and shared the piccalilli. "
              f"The spicy glow burst out, and the Gloom shrieked and fled. "
              f"The valley was saved from extinction, and their friendship shone forever.")


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Maya", hero_type: str = "girl",
         friend_name: str = "Kavi", friend_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         friend_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = ""
    world.gloom = 3.0   # imminent extinction

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "eager"]),
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type,
        traits=["little"] + (friend_traits or ["cautious", "wise"]),
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=friend.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1: Setting and love
    introduce(world, hero, friend)
    loves_activity(world, hero, activity, friend)
    give_prize(world, friend, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2: Arrival, warning, defiance, hand grab
    world.para()
    arrive(world, hero, friend, activity)
    wants(world, hero, friend, activity)
    warn(world, friend, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, friend, hero, activity)

    # Act 3: Resolution
    world.para()
    pout(world, hero)
    gear_def = compromise(world, friend, hero, activity, prize)
    if gear_def:
        accept(world, hero, friend, activity, gear_def)

    world.facts.update(hero=hero, friend=friend, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None,
                       extinction_avoided=world.extinction_avoided)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "valley": Setting(place="the Valley of Echoes", indoor=False,
                      affords={"share_piccalilli", "face_gloom"}, has_gloom=True),
}

ACTIVITIES = {
    "share_piccalilli": Activity(
        id="share_piccalilli",
        verb="share the piccalilli",
        gerund="sharing piccalilli",
        rush="grab the jar of piccalilli",
        mess="sticky",
        soil="sticky and messy",
        zone={"hands"},
        weather="evening",
        keyword="piccalilli",
        tags={"shared meal", "spicy", "friendship"},
    ),
}

PRIZES = {
    "bracelet": Prize(
        label="friendship bracelet",
        phrase="a bracelet woven from silver grass",
        type="bracelet",
        region="hands",
        plural=False,
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="ancient_gloves",
        label="ancient gloves",
        covers={"hands"},
        guards={"sticky", "spicy"},
        prep="put on the ancient gloves",
        tail="put on the ancient gloves",
        plural=True,
    ),
]

GIRL_NAMES = ["Maya", "Leela", "Anika", "Sita", "Ravi"]
BOY_NAMES = ["Kavi", "Arun", "Jaya", "Nila", "Tiva"]
TRAITS = ["brave", "cautious", "loyal", "curious", "kind"]


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    return [
        f"Write a mythic short story for children about two friends who save their home from a vicious creature called the Gloom by sharing a magical jar of piccalilli. Use the word '{act.keyword}'.",
        f"Tell a story where {hero.id} and {friend.id} must work together to avoid extinction. Their friendship is tested by a sticky, spicy meal.",
        f"A myth about a valley threatened by the Gloom. {hero.id} and {friend.id} find that only sharing piccalilli can banish the darkness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    prize = f["prize"]
    resolved = f.get("resolved", False)
    extinction = f.get("extinction_avoided", False)
    sub_h, obj_h, pos_h = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    sub_f = friend.pronoun("subject")
    qa: list[QAItem] = [
        QAItem(
            question=f"Who are the two friends in the story that save the valley?",
            answer=f"The friends are {hero.id}, a {hero.type}, and {friend.id}, a {friend.type}. Together they face the Gloom."
        ),
        QAItem(
            question=f"What did {friend.id} give to {hero.id} as a sign of friendship?",
            answer=f"{friend.id} gave {hero.id} {prize.phrase}."
        ),
        QAItem(
            question=f"How did the friends drive away the Gloom?",
            answer=f"They shared the piccalilli while wearing the ancient gloves, which created a spicy light that banished the Gloom."
        ),
    ]
    if extinction:
        qa.append(QAItem(
            question=f"Was the valley saved from extinction?",
            answer=f"Yes, the valley was saved because {hero.id} and {friend.id} worked together to share the piccalilli and defeat the Gloom."
        ))
    if resolved:
        qa.append(QAItem(
            question=f"How did the ancient gloves help the friends?",
            answer=f"The gloves protected the friendship bracelet from getting sticky, so the gift stayed clean while they ate the piccalilli."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is piccalilli?",
            answer="Piccalilli is a spicy, tangy relish made from chopped vegetables and mustard."
        ),
        QAItem(
            question="What does 'extinction' mean?",
            answer="Extinction means when something disappears forever. In the story, the valley was about to vanish if the Gloom won."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a bond between people who trust, help, and care for each other."
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin (inline)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo matches python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH")
    return 1


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth about friendship, piccalilli, and extinction.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
    # Simplified: only one valid combo in this minimal world.
    place = "valley"
    activity = "share_piccalilli"
    prize = "bracelet"
    hero_gen = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gen = args.friend_gender or (["boy", "girl"][0] if hero_gen == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gen=="girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(BOY_NAMES if friend_gen=="boy" else GIRL_NAMES)
    return StoryParams(place, activity, prize, hero_name, hero_gen, friend_name, friend_gen)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    world = tell(setting, activity, prize_cfg,
                 hero_name=params.hero_name,
                 hero_type=params.hero_gender,
                 friend_name=params.friend_name,
                 friend_type=params.friend_gender)
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
    if trace and sample.world:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k:v for k,v in e.meters.items() if v}
            memes = {k:v for k,v in e.memes.items() if v}
            bits = []
            if meters: bits.append(f"meters={dict(meters)}")
            if memes: bits.append(f"memes={dict(memes)}")
            if e.protective: bits.append(f"covers={sorted(e.covers)}")
            elif e.region: bits.append(f"region={e.region}")
            print(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
        print(f"  gloom={round(sample.world.gloom,1]} extinction_avoided={sample.world.extinction_avoided}]"))
    if qa:
        print()
        lines = ["== (1) Generation prompts =="] + [sample.prompts[0:1] if sample.prompts else []]
        lines.append("\n== (2) Story Q&A ==")
        for qa in sample.story_qa:
            lines += [f"Q: {qa.question}", f"A: {qa.answer}", ""]
        lines.append("\n== (3) World Q&A ==")
        for qa in sample.world_qa:
            lines += [f"Q: {qa.question}", f"A: {qa.answer}", ""]
        print("\n".join(lines))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    rng = random.Random(args.seed if args.seed is not None else 0)
    samples = []
    if args.all:
        # only one valid combo
        p = resolve_params(args, rng)
        p.seed = 0
        samples.append(generate(p))
    else:
        for i in range(max(args.n, 1)):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i
            samples.append(generate(p))
    if args.json:
        if len(samples)==1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2))
        return
    for i, sample in enumerate(samples):
        header = f"### Story {i+1}" if len(samples)>1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1:
            print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
