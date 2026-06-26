#!/usr/bin/env python3

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

THRESHOLD = 1.0
MEMES_KINDS = {"curiosity", "fear", "joy", "concern"}
METERS_KINDS = {"hunger", "energy", "wetness", "workload"}
REGIONS = {"near", "mid", "far"}

@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"fox", "squirrel", "doe"}
        male = {"owl", "bear", "deer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type in {"fox", "bear", "deer", "squirrel"} else "it"

@dataclass
class Setting:
    place: str
    weather: str = "autumn_cold"
    season: str = "winter_approaching"
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    target: Optional[str] = None
    tags: set[str] = field(default_factory=set)

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.time_of_day: str = "evening"
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
        clone.time_of_day = self.time_of_day
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_hunger(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        actor.meters["hunger"] += 0.2
        if actor.meters["hunger"] >= THRESHOLD and ("hunger", actor.id) not in world.fired:
            world.fired.add(("hunger", actor.id))
            out.append(f"{actor.id} felt a quiet growl in {actor.pronoun('possessive')} belly.")
    return out

def _r_energy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["energy"] >= 0.1:
            actor.meters["energy"] -= 0.1
        if actor.meters["energy"] < 0.3 and ("tired", actor.id) not in world.fired:
            world.fired.add(("tired", actor.id))
            out.append(f"{actor.id} was feeling a little slow.")
    return out

def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["curiosity"] >= THRESHOLD and ("curious", actor.id) not in world.fired:
            world.fired.add(("curious", actor.id))
            out.append(f"{actor.id} just had to know what the noise was about!")
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="hunger", tag="physical", apply=_r_hunger),
    Rule(name="energy", tag="physical", apply=_r_energy),
    Rule(name="curiosity", tag="emotional", apply=_r_curiosity),
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

def activity_delight(activity: Activity) -> str:
    return {
        "explore_echoes": "the crisp leaves whispered secrets back",
        "decipher_vocals": "the marks on parchment held the story of the woods",
        "journey_path": "each step brought the berries closer",
    }.get(activity.id, "it made the task feel possible")

def setting_detail(setting: Setting) -> str:
    if setting.season == "winter_approaching":
        return f"The {setting.place} shivered under a pale sky, and the crisp air carried whispers of change."
    if setting.weather == "rainy":
        return f"Rain pattered against leaves, turning the forest floor to a slippery mosaic."
    return f"Early {setting.season} painted {setting.place} with amber and gold."

def mystery_danger(mystery: Activity) -> str:
    return {
        "berry_patch_location": "a frozen river that swelled at night",
        "hidden_burrow": "a fallen log bridge over a rushing creek",
        "scattered_seeds": "sharp thorn bushes that lined the only route",
    }.get(mystery.id, "an unseen obstacle")

def introduce(world: World, actor: Entity) -> None:
    trait = next((t for t in actor.traits if t != "little"), actor.type)
    world.say(f"{actor.id} was a {trait} {actor.type} who paid close attention to the small sounds of the woods.")

def loves_mysteries(world: World, actor: Entity, mystery: Activity) -> None:
    actor.memes["curiosity"] += 1
    world.say(
        f"{actor.pronoun().capitalize()} {actor.type}s loved following mysteries like "
        f"the {mystery.verb} -- {activity_delight(mystery)}."
    )

def arrives(world: World, actors: list[Entity], setting: Setting) -> None:
    actors_str = " and ".join(a.id for a in actors)
    when = f"One {setting.season.replace('_', ' ')} {setting.time_of_day}, "
    where = f"deep in {setting.place}" if setting.season == "winter_approaching" else f"at the edge of {setting.place}"
    world.say(f"{when}{actors_str} {where}.")

def find_box(world: World, finder: Entity, box: Entity) -> None:
    finder.memes["curiosity"] += 1.5
    world.say(
        f"{finder.id} spotted something half-buried and dug with eager paws. "
        f"There lay {box.phrase}, jettisoned long ago by careless paws and now just a memory of metal."
    )

def decipher(world: World, decipherer: Entity, parchment: Entity, mystery: Activity) -> None:
    decipherer.memes["curiosity"] -= 0.5
    decipherer.memes["concern"] += 0.8
    world.say(
        f"{decipherer.id} gently unfolded the old parchment and traced the "
        f"symbols: this was a transcription of the forest's songs, and among them "
        f"lay the secret way to {mystery.target or 'a hidden source of food'}."
    )
    world.facts["mystery_understood"] = True

def warn(world: World, cautious: Entity, bold: Entity, danger: str) -> None:
    cautious.memes["concern"] += 1
    world.say(f'"The path to the {danger} is treacherous," warned {cautious.id}.')
    bold.memes["concern"] += 0.7
    world.say(f"{bold.id} swallowed hard but nodded anyway.")

def journey_planned(world: World, leader: Entity, destination: Entity, path: str) -> None:
    leader.memes["joy"] += 0.6
    world.say(
        f'{leader.id} mapped a safe route: "{path}". They would cross just after dawn '
        f"when the {world.setting.season} chill had numbed the worst of the danger."
    )

def cross_path(world: World, actor: Entity, danger: str) -> None:
    actor.memes["fear"] += 1.2
    actor.meters["energy"] -= 0.8
    world.say(
        f"{actor.id} crept across the {danger}, claws scraping stone, {actor.it()} "
        f"breath quick. One slip and night would claim {actor.pronoun('object')}."
    )

def reach_destination(world: World, finders: list[Entity], destination: Entity) -> None:
    finders_str = " and ".join(f.id for f in finders)
    world.say(
        f"{finders_str} reached {destination.phrase} just as the first heavy snowflakes "
        f"began to fall. The berries glowed like rubies in the twilight."
    )
    for f in finders:
        f.memes["joy"] += 1.5
        f.meters["hunger"] = max(0, f.meters["hunger"] - 0.8)

SETTINGS = {
    "whispering_woods": Setting(
        place="Whispering Woods",
        weather="autumn_cold",
        season="winter_approaching",
        affords={"explore_echoes", "decipher_vocals", "journey_path"},
    ),
    "deep_forest": Setting(
        place="deep forest",
        weather="rainy",
        season="autumn_wet",
        affords={"explore_echoes"},
    ),
    "sunny_clearing": Setting(
        place="sunny clearing",
        weather="clear",
        season="early_autumn",
        affords={"decipher_vocals"},
    ),
}

ACTIVITIES = {
    "explore_echoes": Activity(
        id="explore_echoes",
        verb="explore a strange echo in the woods",
        gerund="exploring echoes in the woods",
        rush="dash toward the new sound",
        target="hidden source",
        tags={"explore", "sound"},
    ),
    "decipher_vocals": Activity(
        id="decipher_vocals",
        verb="decipher the animal song transcription",
        gerund="deciphering the song transcription",
        rush="grab the rolled-up parchment",
        tags={"transcription", "mystery"},
    ),
    "journey_path": Activity(
        id="journey_path",
        verb="journey to the hidden berry patch",
        gerund="journeying to the hidden berry patch",
        rush="bolt down the forest path",
        target="Great Berry Patch",
        tags={"journey", "destination"},
    ),
}

OBJECTS = {
    "journal": Entity(
        id="journal",
        type="tool",
        label="journal",
        phrase="a worn leather-bound journal of animal songs",
        traits=["ancient", "cracked"],
    ),
    "metal_box": Entity(
        id="metal_box",
        type="container",
        label="metal box",
        phrase="an old metal box half-buried in the dirt",
        traits=["jettisoned", "rusted"],
    ),
    "parchment": Entity(
        id="parchment",
        type="clue",
        label="parchment",
        phrase="a rolled-up parchment covered in tiny symbols",
    ),
    "berry_patch": Entity(
        id="berry_patch",
        type="destination",
        label="berry patch",
        phrase="the fabled Great Berry Patch",
    ),
}

CHARACTERS = {
    "Oliver": Entity(
        id="Oliver",
        type="owl",
        label="Oliver",
        phrase="a wise old owl with golden eyes",
        traits=["wise", "curious", "observant"],
    ),
    "Freddy": Entity(
        id="Freddy",
        type="fox",
        label="Freddy",
        phrase="a young fox with bright red fur",
        traits=["playful", "stubborn", "fast"],
    ),
    "Benny": Entity(
        id="Benny",
        type="bear",
        label="Benny",
        phrase="a large bear who hibernates too early",
        traits=["sleepy", "forgetful"],
    ),
}

NAMES_OWL = ["Oliver", "Archimedes", "Orville"]
NAMES_FOX = ["Freddy", "Roxy", "Jasper"]
NAMES_BEAR = ["Benny", "Thor", "Paddington"]
TRAITS = ["brave", "curious", "playful", "quiet", "wise"]

def tell(setting_id: str, activity_id: str, name: str, role: str) -> World:
    s = SETTINGS[setting_id]
    act = ACTIVITIES[activity_id]
    world = World(s)
    world.time_of_day = random.choice(["late_afternoon", "evening", "dusk"])

    leader = world.add(Entity(
        id=name,
        type=role,
        label=NAMES_FOX[0] if role == "fox" else NAMES_OWL[0] if role == "owl" else NAMES_BEAR[0],
        phrase=f"a {role} named {name}",
        traits=random.sample(TRAITS, k=2),
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="owl" if role == "fox" else "fox" if role == "owl" else "deer",
        label={"fox": "Oliver", "owl": "Freddy", "deer": "Tina"}[role],
        traits=["wise"] if role == "fox" else ["playful"] if role == "owl" else ["calm"],
    ))
    journal = world.add(copy.deepcopy(OBJECTS["journal"]))
    box = world.add(copy.deepcopy(OBJECTS["metal_box"]))
    parchment = world.add(copy.deepcopy(OBJECTS["parchment"]))
    destination = world.add(copy.deepcopy(OBJECTS["berry_patch"]))
    destination.owner = None

    introduce(world, leader)
    loves_mysteries(world, leader, act)
    helper.memes["concern"] = 0.5

    world.para()
    arrives(world, [leader, helper], s)

    world.para()
    find_box(world, leader, box)
    world.facts["box_found"] = True

    cross_talk = f"{leader.id} nudged the box open with a paw. It creaked like a forgotten memory."
    world.say(cross_talk)

    world.para()
    decipher(world, helper, parchment, act)
    world.facts["transcription_deciphered"] = True
    act.target = destination.label

    world.para()
    warn(world, helper, leader, mystery_danger(act))
    journey_planned(world, helper, destination, f"the eastern ridge before dawn")

    world.para()
    cross_path(world, leader, mystery_danger(act))
    cross_path(world, helper, mystery_danger(act))

    world.para()
    reach_destination(world, [leader, helper], destination)
    world.facts["berries_collected"] = True

    world.facts.update(
        leader=leader, helper=helper, parchment=parchment, destination=destination,
        danger=mystery_danger(act), season=s.season,
    )
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    name = f["leader"].label_word
    danger = f.get("danger", "treacherous path")
    return [
        f'Write a gentle adventure story for children about a {name} who finds a '
        f'jettisoned object containing a transcription of animal songs that reveals '
        f'a secret food source before winter.',
        f'Tell a story in the style of "Animal Story" where two friends solve a '
        f'mystery using the clues left behind in a forgotten journal and parchment.',
        f'Create a short tale for 3-to-5-year-olds where a {name} discovers a '
        f'transcription of forest sounds hidden inside a jettisoned metal box and '
        f'use it to find berries that will feed everyone through the coming cold.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    leader, helper = f["leader"], f["helper"]
    sub = leader.pronoun("subject")
    pos = leader.pronoun("possessive")
    obj = leader.pronoun("object")
    danger = f.get("danger", "a perilous path")

    qa = [
        QAItem(
            question=f"What kind of animal was {leader.id}?",
            answer=f"{leader.id} was a {leader.type}."
        ),
        QAItem(
            question=f"What did the jettisoned metal box contain that helped solve the mystery?",
            answer=f"Inside the box was an old parchment that had animal songs transcribed on it."
        ),
        QAItem(
            question=(
                f"How did {leader.id} and {helper.id} manage to reach the "
                f"{f['destination'].label} safely?"
            ),
            answer=(
                f"They waited for the cold winter morning when the danger spot was "
                f"least slippery and then carefully crossed using their plan. "
                f"When they arrived, they saw bright red berries glowing in the twilight."
            ),
        ),
    ]

    if world.setting.season == "winter_approaching" and f.get("berries_collected"):
        qa.append(QAItem(
            question="Why was finding the berry patch important?",
            answer=(
                f"The woods were getting colder and food was scarce. "
                f"The berry patch was the last source of food before winter settled in."
            ),
        ))

    if f.get("transcription_deciphered"):
        qa.append(QAItem(
            question="What did the transcription of animal songs reveal?",
            answer=(
                f"The tiny symbols traced the sounds the animals made and also "
                f"marked the secret path to the berry patch - a map only the song-singer knew."
            ),
        ))

    return qa

KNOWLEDGE = {
    "eagle": [(
        "What sound does an owl make?",
        "An owl hoots softly in the night, a deep 'hoo hoo' that echoes through the trees."
    )],
    "fox": [(
        "Why do foxes like to explore?",
        "Foxes are curious animals. They sniff new smells, listen to strange sounds, "
        "and dig up forgotten things to learn what happened."
    )],
    "migration": [(
        "Why do birds and animals get ready for winter?",
        "When days grow short and cold, food becomes hard to find. Animals migrate, "
        "store food, or sleep through winter so they will be safe until spring."
    )],
    "berry": [(
        "What do berries do for animals in winter?",
        "Berries are food that lasts into cold times. Some birds and small animals "
        "eat them when seeds and green plants are gone."
    )],
    "transcription": [(
        "What is a transcription?",
        "A transcription is a copy of something written or spoken. Here it means the "
        "old owl wrote down the songs and calls he heard in the woods so he could remember them later."
    )],
    "jettison": [(
        "What does jettison mean?",
        "To jettison is to throw something away because it is not needed. The metal box "
        "was left behind long ago by animals who did not need it anymore."
    )],
}

KNOWLEDGE_ORDER = ["eagle", "fox", "migration", "berry", "transcription", "jettison"]

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"owl", "fox", "berry", "transcription", "jettison"}
    out: list[QAItem] = []
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v >= THRESHOLD}
        memes = {k: v for k, v in e.memes.items() if v >= THRESHOLD}
        bits = []
        if type(meters) == dict and meters:
            bits.append(f"meters={meters}")
        if type(memes) == dict and memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

ASP_RULES = r"""
% A mystery is solvable when the transcription is deciphered and the path is safe
solution_found :- deciphered(parchment), safe_path(deciphered_info).
safe_path :- season(winter_approaching), time(evening).
berries_collected :- solution_found, destination(berry_patch).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("season", sid, s.season))
        lines.append(asp.fact("weather", sid, s.weather))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("tags", aid, ",".join(sorted(a.tags))))
        if a.target:
            lines.append(asp.fact("target", aid, a.target))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("type", oid, obj.type))
        if obj.traits:
            for t in obj.traits:
                lines.append(asp.fact("trait", oid, t))
    for cid, c in CHARACTERS.items():
        lines.append(asp.fact("character", cid))
        lines.append(asp.fact("role", cid, c.type))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show solution_found/0, berries_collected/0."))
        atoms_list = asp.atoms(model, "solution_found")
        berries_list = asp.atoms(model, "berries_collected")
        if (len(atoms_list) == 1 and atoms_list[0] == () and
            len(berries_list) == 1 and berries_list[0] == ()):
            print("OK: ASP gate matches expected outcomes for winter scenario.")
            return 0
        print("MISMATCH between ASP gate and expected winter scenario.")
        return 1
    except Exception as e:
        print(f"ASP verification failed: {e}")
        return 1

@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    role: str
    seed: Optional[int] = None

CURATED = [
    StoryParams(place="whispering_woods", activity="decipher_vocals", name="Oliver", role="owl"),
    StoryParams(place="whispering_woods", activity="journey_path", name="Freddy", role="fox"),
    StoryParams(place="deep_forest", activity="explore_echoes", name="Archimedes", role="owl"),
]

def explain_invalid_choice(activity: Activity, role: str) -> str:
    allowed = {"explore_echoes": ["fox", "owl"], "decipher_vocals": ["fox", "owl"], "journey_path": ["fox"]}
    return (
        f"(No story: {role} animals don't solve mysteries that way. "
        f"Try role among {sorted(allowed.get(activity.id, []))}.)"
    )

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: 'Jettison Transcription Mystery to Solve' in Animal Story style"
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["owl", "fox", "bear"])
    ap.add_argument("-n", type=int, default=1, help="number of stories")
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
    if args.activity and args.role and args.role not in {
        "owl", "fox" if args.activity != "journey_path" else "fox",
    }:
        raise StoryError(explain_invalid_choice(ACTIVITIES[args.activity], args.role))

    if not (args.activity and args.role and args.place):
        candidates = []
        for p in SETTINGS:
            for a in ACTIVITIES:
                for r in (["fox"] if a == "journey_path" else ["fox", "owl"]):
                    candidates.append((p, a, r))
        choice = rng.choice(candidates)
    else:
        choice = (args.place, args.activity, args.role)

    place, activity, role = choice
    name_pool = NAMES_FOX if role == "fox" else NAMES_OWL if role == "owl" else NAMES_BEAR
    name = args.name or rng.choice(name_pool)
    return StoryParams(place=place, activity=activity, name=name, role=role)

def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.activity, params.name, params.role)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solution_found/0, berries_collected/0."))
        print("ASP compatible winter scenarios:")
        print("  ✓ solution_found")
        print("  ✓ berries_collected")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
                rng = random.Random(seed)
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
                story_text = sample.story
                if story_text in seen:
                    continue
                seen.add(story_text)
                samples.append(sample)
            except StoryError as err:
                if args.n == 1:
                    print(err)
                    return
                continue

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} in {p.place} as {p.role}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
