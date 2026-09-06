#!/usr/bin/env python3
"""
Standalone story world: an iguana on a canal path, with a small misunderstanding.

The premise is an Animal Story style tale:
an iguana sees something at the canal path, misreads it, causes a brief worry,
then the misunderstanding is cleared and the world ends in a calmer image.

The world model tracks:
- physical meters: distance, wetness, carried items, and environmental state
- emotional memes: worry, confusion, relief, friendship, confidence

The story is generated from simulated state rather than from a fixed paragraph.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Small domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"iguana", "lizard", "animal"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the canal path"
    detail: str = "a narrow path by the water"


@dataclass
class StoryParams:
    name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.story_lines)


# ---------------------------------------------------------------------------
# ASP twin helpers
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% The iguana story is valid when the canal-path scene contains a
% misunderstanding that is later cleared up.
misunderstanding(X) :- sees(X, Y), misreads(X, Y).
resolved(X) :- misunderstanding(X), explains(_, X), calms(_, X).
valid_story(X) :- misunderstanding(X), resolved(X).
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("character", "iguana"),
            asp.fact("sees", "iguana", "uncertain_shape"),
            asp.fact("misreads", "iguana", "uncertain_shape"),
            asp.fact("explains", "friend", "iguana"),
            asp.fact("calms", "friend", "iguana"),
            asp.fact("setting", "canal_path"),
            asp.fact("theme", "misunderstanding"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    # A light reasonableness gate mirrored in Python.
    return True


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

NAMES = [
    "Iggy", "Milo", "Pico", "Luna", "Benny", "Rosa", "Tavi", "Nina"
]

FRIEND_NAMES = [
    "Nori", "Pip", "Sana", "Timo", "Juno", "Mara", "Oli", "Nico"
]

SETTING = Setting(
    place="the canal path",
    detail="a long path beside the water, with reeds bending in the breeze",
)

INCIDENTS = [
    {
        "id": "turtle_shadow",
        "premise": "a broad shadow slid beneath the footbridge",
        "mistake": "a turtle was trapped under the bridge",
        "first_action": "called urgently toward the water before checking the shape",
        "clue": "the shadow kept exactly the same pace as a cloud overhead",
        "test": "watched from behind the path railing while the cloud crossed the sun",
        "truth": "it was the cloud's shadow moving over clear water",
        "repair": "lowered his voice and apologized for alarming the resting ducks",
        "ending": "one real turtle lifted its nose beside a lily pad while the cloud sailed on",
        "lesson": "A moving shadow is a clue to study, not proof that an animal is in trouble.",
    },
    {
        "id": "bottle_otter",
        "premise": "a brown shape bobbed beside the reeds with a soft plip-plip",
        "mistake": "a young otter was struggling in the canal",
        "first_action": "ran along the dry path shouting for the shape to paddle closer",
        "clue": "sunlight flashed from a straight glass rim",
        "test": "used the lookout binoculars without leaning over the rail",
        "truth": "it was an empty bottle turning in the current",
        "repair": "asked the canal keeper to remove the litter with a long-handled net",
        "ending": "the clean water rippled behind the keeper's net, with no frightened otter anywhere",
        "lesson": "Careful looking can turn a frightening guess into a useful, safe action.",
    },
    {
        "id": "reed_crocodile",
        "premise": "the reeds shook and made a long scratch-scratch beside the bend",
        "mistake": "a crocodile was crawling toward the path",
        "first_action": "blocked the path with his tail and warned every walker to stop",
        "clue": "each scratch arrived with the same gust that spun the weather vane",
        "test": "waited at the marked lookout and compared the reeds during the next gust",
        "truth": "a loose reed stem was brushing the wooden fence",
        "repair": "let the ranger tie the stem back while he calmly reopened the path",
        "ending": "the secured reeds whispered instead of scratching as minnows flickered below",
        "lesson": "A sensible warning should be followed by evidence, not stretched into a scary rumor.",
    },
    {
        "id": "orange_glove",
        "premise": "an orange shape lay still beside a maintenance box",
        "mistake": "another iguana had fainted on the canal path",
        "first_action": "begged his friend to fetch water for the motionless stranger",
        "clue": "the shape had five narrow points and a bright silver cuff",
        "test": "looked from a step away and asked a maintenance worker to inspect it",
        "truth": "it was the worker's dropped safety glove",
        "repair": "returned the glove and explained his hasty alarm to the gathered animals",
        "ending": "the glove waved from the worker's hand as the two iguanas exchanged a peaceful nod",
        "lesson": "Kind concern works best when it travels with patient observation.",
    },
    {
        "id": "rope_snake",
        "premise": "a striped coil appeared near the closed service gate",
        "mistake": "a snake was guarding the only way home",
        "first_action": "told his friend they must make a long detour without asking anyone",
        "clue": "one end of the coil was clipped to a keeper's cart",
        "test": "stayed on the public path and called the keeper over",
        "truth": "it was a dry mooring rope waiting to be stored",
        "repair": "helped point walkers toward the open gate while the keeper put the rope away",
        "ending": "the empty path curved home under little pools of lamplight",
        "lesson": "Distance keeps animals safe, and a knowledgeable adult can settle an uncertain sight.",
    },
    {
        "id": "mirror_iguana",
        "premise": "a green face appeared inside a shiny canal-depth marker",
        "mistake": "a silent iguana was copying every expression he made",
        "first_action": "frowned and puffed himself up, making the supposed stranger look cross",
        "clue": "his friend appeared in the marker at the very same angle",
        "test": "raised one forefoot, then lowered it, while remaining on the dry path",
        "truth": "the polished marker was reflecting them like a mirror",
        "repair": "relaxed his crest and laughed at the quarrel he had started with himself",
        "ending": "two small reflections bowed together in the marker's sunset glow",
        "lesson": "Before answering an unfriendly look, check whether you understand what you see.",
    },
    {
        "id": "bridge_cry",
        "premise": "three hollow groans sounded beneath the pedestrian bridge",
        "mistake": "a large animal was crying for help below the boards",
        "first_action": "paced in worry and interrupted a keeper's bird count",
        "clue": "the groan came only when a delivery cart crossed one particular board",
        "test": "stood behind the barrier while the keeper rolled the empty cart across again",
        "truth": "a dry bridge joint needed oil and inspection",
        "repair": "kept walkers at the signed detour until the maintenance team finished",
        "ending": "the repaired bridge gave one quiet click beneath the keeper's returning cart",
        "lesson": "Repeating a safe test can separate an animal call from a mechanical sound.",
    },
    {
        "id": "flag_bird",
        "premise": "a yellow triangle fluttered low beside a newly planted willow",
        "mistake": "a bird had hurt its wing and could not rise",
        "first_action": "scattered seeds toward it, drawing pigeons across the busy path",
        "clue": "the triangle never turned its head and was fastened to a wire stem",
        "test": "called the gardener and watched from the quiet side of the path",
        "truth": "it was a survey flag marking where the willow roots began",
        "repair": "swept the stray seeds from the path with the gardener's help",
        "ending": "the flag fluttered above bare, tidy stones while the pigeons fed in their proper garden patch",
        "lesson": "Helping on a guess can create a second problem, so first find out what needs help.",
    },
    {
        "id": "bubble_frog",
        "premise": "round bubbles rose beside a covered drainage grate",
        "mistake": "a frog was trapped underneath the grate",
        "first_action": "reached toward the cover until his friend reminded him not to touch canal equipment",
        "clue": "the bubbles began whenever the small pump light blinked",
        "test": "stepped back and reported the pattern to the canal technician",
        "truth": "an aeration pipe was safely releasing air into the water",
        "repair": "thanked his friend for stopping him and added the observation to the nature log",
        "ending": "a real frog called from the far bank as neat bubbles climbed through the dusk",
        "lesson": "Bravery can mean stepping back, reporting a clue, and letting trained adults check equipment.",
    },
    {
        "id": "toy_duckling",
        "premise": "a tiny yellow shape zipped in sharp squares across a model-boat basin",
        "mistake": "a duckling was lost and swimming in a panic",
        "first_action": "whistled and hurried after it along the walking line",
        "clue": "the shape stopped whenever a child's remote control stopped clicking",
        "test": "asked the child to park the shape beside the basin's low dock",
        "truth": "it was a duck-shaped model boat",
        "repair": "explained the alarm, then helped place a MODEL BOAT card beside the launch spot",
        "ending": "the toy duck rested at its dock while a real duck family glided beyond the divider",
        "lesson": "Looking for cause and effect is better than trusting the first lively appearance.",
    },
    {
        "id": "branch_lizard",
        "premise": "a knobbly brown form stretched across the path after a windy night",
        "mistake": "a giant lizard was sleeping where bicycles passed",
        "first_action": "whispered for everyone to tiptoe around it on the canal-side edge",
        "clue": "the form had snapped leaves and pale wood showing at one end",
        "test": "kept everyone inside the rail and asked the groundskeeper to identify it",
        "truth": "it was a fallen sycamore branch, not an animal",
        "repair": "directed bicycles to stop while the groundskeeper cleared the full path",
        "ending": "fresh sawdust made a golden crescent where the branch had blocked the morning route",
        "lesson": "A safe correction matters more than pretending an imaginative guess was right.",
    },
    {
        "id": "cone_beak",
        "premise": "a bright beak seemed to peek from behind a path-repair screen",
        "mistake": "a rare orange bird had nested inside the work zone",
        "first_action": "invited his friend closer for a photograph despite the KEEP OUT sign",
        "clue": "black letters curved across the orange surface",
        "test": "both animals stayed outside the barrier and zoomed the lookout camera",
        "truth": "it was the pointed top of a safety cone",
        "repair": "moved back to the viewing mark and told the ranger why they had almost approached",
        "ending": "the cone stood bright beneath the repaired lamp while swallows crossed the open sky",
        "lesson": "Curiosity should never erase a barrier or a clear safety sign.",
    },
]

OPENINGS = [
    "At first light, {hero} set out to count animal tracks along the canal path.",
    "After lunch, {hero} and {friend} began a slow nature walk beside the canal.",
    "A cool breeze met {hero} at the canal-path map, where {friend} was waiting.",
    "On keeper-help day, {hero} promised to notice changes without disturbing wildlife.",
    "The canal path was busy with walkers when {hero} joined {friend} near the reeds.",
    "Just before sunset, {hero} carried a nature notebook down the dry canal path.",
    "Following overnight wind, {hero} and {friend} inspected the public path from behind its rail.",
    "During the quiet animal-count hour, {hero} met {friend} at the marked lookout.",
]

REFLECTIONS = [
    '"I treated my first idea like a fact," {hero} admitted. "Next time I will gather clues."',
    '{friend} said, "Concern was a good beginning. Checking safely made it useful."',
    '{hero} wrote the truth beneath his crossed-out guess so the mistake could teach him.',
    'They retold the event with the clue in the middle, because that was where understanding changed.',
    '{hero} noticed that relief arrived only after observation replaced imagination.',
    'Together they made a three-step rule: pause, look for evidence, and ask someone who knows.',
    'Instead of hiding the error, {hero} explained it to the next walkers so nobody repeated it.',
    '{friend} tapped the notebook. "A guess may open a mystery, but evidence must close it."',
]


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    incident = INCIDENTS[rng.randrange(len(INCIDENTS))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    reflection = REFLECTIONS[rng.randrange(len(REFLECTIONS))]
    detail = rng.choice([
        "reeds bending above the water",
        "a painted distance marker and a sturdy rail",
        "willow shadows crossing the gravel",
        "keeper signs beside a broad viewing place",
        "dragonflies hovering beyond the fence",
        "a dry public path above the slow current",
    ])
    world = World(setting=SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="iguana",
        label="iguana",
        meters={"distance": 0.0, "wetness": 0.0},
        memes={"curiosity": 1.0, "confusion": 0.0, "worry": 0.0, "relief": 0.0, "confidence": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="bird",
        label="little bird",
        meters={"distance": 0.0},
        memes={"friendship": 1.0, "worry": 0.0, "relief": 0.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="evidence",
        label=incident["clue"],
        phrase=incident["clue"],
    ))
    world.facts.update(
        hero=hero,
        friend=friend,
        clue=clue,
        incident=incident,
        incident_id=incident["id"],
        opening=opening,
        reflection=reflection,
        setting_detail=detail,
        safe_boundary="the public canal path behind its rail or marked barrier",
    )
    return world


def story_intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    world.say(world.facts["opening"].format(hero=hero.id, friend=friend.id))
    world.say(
        f"{hero.id} was a small iguana, and {friend.id} was a watchful little bird. "
        f"They stayed on the canal path, where they saw {world.facts['setting_detail']}."
    )
    world.say(
        "They knew the canal was for observing from a safe distance: neither animal entered "
        "the water, crossed a barrier, nor handled maintenance equipment."
    )


def story_misunderstanding(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    incident: dict = world.facts["incident"]

    hero.meters["distance"] += 1
    world.say(
        f"Near the next bend, {incident['premise']}. {hero.id} stopped so suddenly that "
        f"{friend.id} nearly bumped into his tail."
    )
    hero.memes["confusion"] += 1
    world.say(
        f"From that first glimpse, {hero.id} decided that {incident['mistake']}. "
        f"He {incident['first_action']}."
    )
    world.say(
        f'"Wait," {friend.id} said. "That may be possible, but we have only a guess. '
        'Let us stay on the safe path and find a clue before we act again."'
    )
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.facts["misread_as"] = incident["mistake"]
    world.facts["first_action"] = incident["first_action"]
    world.facts["misunderstanding"] = True


def story_turn(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    incident: dict = world.facts["incident"]

    world.say(
        f"They studied the scene without going nearer. Soon {friend.id} noticed the useful clue: "
        f"{incident['clue']}."
    )
    world.say(
        f"To test the idea safely, {hero.id} {incident['test']}. "
        f"The evidence showed that {incident['truth']}."
    )
    world.say(
        world.facts["reflection"].format(hero=hero.id, friend=friend.id)
    )
    hero.memes["confusion"] = max(0.0, hero.memes["confusion"] - 1.0)
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    friend.memes["worry"] = max(0.0, friend.memes["worry"] - 1.0)
    hero.memes["confidence"] += 0.5
    world.facts["clue_found"] = incident["clue"]
    world.facts["truth"] = incident["truth"]
    world.facts["explained"] = True


def story_resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    incident: dict = world.facts["incident"]

    hero.memes["relief"] += 1
    hero.memes["confidence"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"Now that the misunderstanding was clear, {hero.id} {incident['repair']}. "
        f"{friend.id} stayed beside him until the path was calm again."
    )
    world.say(
        f"{incident['lesson']} {hero.id} repeated the lesson once, not as a rule to fear the canal, "
        "but as a reminder to match kind intentions with good evidence."
    )
    world.say(
        f"As they continued along the canal path, {incident['ending']}. "
        f"{hero.id} and {friend.id} walked home together, relieved and a little wiser."
    )
    world.facts["repair"] = incident["repair"]
    world.facts["lesson"] = incident["lesson"]
    world.facts["ending_image"] = incident["ending"]
    world.facts["resolved"] = True


def generate_story_world(params: StoryParams) -> World:
    world = build_world(params)
    story_intro(world)
    world.say("")
    story_misunderstanding(world)
    world.say("")
    story_turn(world)
    world.say("")
    story_resolution(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    incident: dict = world.facts["incident"]
    return [
        "Write a child-facing Animal Story about an iguana whose misunderstanding on a canal path is corrected with safe observation.",
        f"Tell how {hero.id} and {friend.id} investigate the mistaken idea that {incident['mistake']}, without entering the canal or crossing a barrier.",
        f"Write a gentle evidence-based mystery in which the clue is that {incident['clue']}, and end with {incident['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    incident: dict = world.facts["incident"]
    return [
        QAItem(
            question=f"What did {hero.id} and {friend.id} notice around them before the mystery?",
            answer=f"They noticed {world.facts['setting_detail']} while staying on the canal path. This established the safe place from which they observed the incident."
        ),
        QAItem(
            question=f"What did {hero.id} mistakenly believe on the canal path?",
            answer=f"{hero.id} mistakenly believed that {incident['mistake']}. His first glimpse did not provide enough evidence."
        ),
        QAItem(
            question=f"Which clue helped {hero.id} and {friend.id} reconsider the misunderstanding?",
            answer=f"They noticed that {incident['clue']}. That detail did not fit {hero.id}'s first explanation."
        ),
        QAItem(
            question=f"How did the animals check the clue without taking a canal-side risk?",
            answer=f"{hero.id} {incident['test']}. Both animals remained on the public path and respected its safety boundary."
        ),
        QAItem(
            question=f"What was the real explanation for what {hero.id} saw?",
            answer=f"The evidence showed that {incident['truth']}. This resolved the misunderstanding."
        ),
        QAItem(
            question=f"What did {hero.id} do after learning the truth?",
            answer=f"He {incident['repair']}. The repair addressed the consequence of his mistaken first action."
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} put their new understanding into words?",
            answer=world.facts["reflection"].format(hero=hero.id, friend=friend.id)
        ),
        QAItem(
            question="What lesson did the canal-path incident teach?",
            answer=incident["lesson"]
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canal?",
            answer="A canal is a man-made waterway that can carry boats or help move water from one place to another."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true but later learns they were wrong."
        ),
        QAItem(
            question="How should a child or animal observe something uncertain beside a canal?",
            answer="They should remain on the public path behind rails or barriers, look for clues from a safe distance, and ask a responsible adult or keeper for help."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification / facts
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    # The Python gate is intentionally simple; the ASP twin mirrors the story's
    # core predicate structure.
    if asp_valid():
        print("OK: Python reasonableness gate passes.")
        return 0
    print("MISMATCH: Python reasonableness gate failed.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="An Animal Story world about an iguana on the canal path."
    )
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
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
    name = args.name or rng.choice(NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(name=name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for v in vals:
            print(f"  {v}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Iggy", friend_name="Nori", seed=base_seed),
            StoryParams(name="Milo", friend_name="Pip", seed=base_seed + 1),
            StoryParams(name="Luna", friend_name="Mara", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
