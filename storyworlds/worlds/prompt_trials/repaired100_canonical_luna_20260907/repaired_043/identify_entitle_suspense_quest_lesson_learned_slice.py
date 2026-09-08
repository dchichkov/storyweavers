#!/usr/bin/env python3
"""
A standalone Slice of Life storyworld about identifying a lost name tag and
entitling its rightful owner to a small place of belonging.

The world models a quiet community reading room. A child finds an unlabeled
garden plot sign and a key ring, then must identify who they belong to before
the afternoon welcome table begins. The suspense comes from a fading clue and
the risk of giving the place to the wrong person. The quest is solved through
conversation, observation, and a careful return. The lesson learned is that
belonging should be established by listening, not guessing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"clarity": 0.0, "wear": 0.0, "visibility": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "belonging": 0.0}


@dataclass
class Setting:
    key: str
    place: str
    affordances: set[str]


@dataclass
class StoryParams:
    setting: str
    hero_type: str
    companion_type: str
    hero_name: str
    companion_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    title: str
    object_name: str
    object_phrase: str
    hidden_clue: str
    likely_guess: str
    rightful_owner: str
    owner_role: str
    place_detail: str
    identifying_action: str
    entitlement: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "reading_room": Setting(
        "reading_room",
        "the little reading room",
        {"observe", "ask", "return", "welcome"},
    ),
    "courtyard": Setting(
        "courtyard",
        "the library courtyard",
        {"observe", "ask", "return", "welcome"},
    ),
    "community_hall": Setting(
        "community_hall",
        "the community hall",
        {"observe", "ask", "return", "welcome"},
    ),
}

HERO_TYPES = ["child", "young gardener", "library helper", "neighborhood friend"]
COMPANION_TYPES = ["child", "young gardener", "library helper", "neighborhood friend"]

NAMES = {
    "child": ["Luna", "Mira", "Owen", "Toby"],
    "young gardener": ["Luna", "Nora", "Ivy", "Sam"],
    "library helper": ["Luna", "Mara", "Theo", "June"],
    "neighborhood friend": ["Luna", "Pia", "Noah", "Eli"],
}

CASES = [
    Case(
        title="The Name on the Wooden Box",
        object_name="wooden box",
        object_phrase="a small wooden box with a brass latch",
        hidden_clue="a blue paint fleck on the latch matched the blue bench beside the herb garden",
        likely_guess="the box belonged to the hall keeper because it sat near the supply shelf",
        rightful_owner="Mina",
        owner_role="the quiet baker who cared for the herb garden",
        place_detail="the courtyard herb garden",
        identifying_action="noticed the paint fleck, asked three gentle questions, and compared the box with the garden's old blue bench",
        entitlement="Mina was entitled to the box because she could describe the loose latch, the flour mark inside, and the seeds she had stored there",
        lesson="A nearby object is not automatically yours; the person who can explain its history deserves to be heard",
        ending="Mina opened the box and found the seed envelopes exactly where she had left them",
    ),
    Case(
        title="The Missing Garden Tag",
        object_name="garden tag",
        object_phrase="a white garden tag with one muddy corner",
        hidden_clue="the muddy corner carried a tiny crescent cut that matched the shape of the moon bed",
        likely_guess="the tag belonged to the largest garden plot because it had been found beside it",
        rightful_owner="Ravi",
        owner_role="the new neighbor who planted the smallest moon-shaped bed",
        place_detail="the courtyard beds",
        identifying_action="brushed the mud away, traced the crescent cut, and asked which gardener had made a moon-shaped bed",
        entitlement="Ravi was entitled to the tag because he knew the name written beneath the mud and showed where its stake had snapped",
        lesson="To identify something fairly, look for the small mark that connects it to a real story",
        ending="Ravi set the tag beside his tiny moon bed, where the first green leaves leaned toward it",
    ),
    Case(
        title="The Key for the Quiet Drawer",
        object_name="brass key",
        object_phrase="a brass key tied to a faded red thread",
        hidden_clue="the red thread matched a repaired curtain in the children's art cupboard",
        likely_guess="the key opened the office because it looked old and important",
        rightful_owner="Anya",
        owner_role="the art teacher who kept children's clay tools safe",
        place_detail="the art cupboard",
        identifying_action="followed the red thread clue and asked what was kept behind the cupboard's quiet drawer",
        entitlement="Anya was entitled to the key because she named the drawer's stuck hinge and the child-made labels inside",
        lesson="Entitlement comes from a trusted connection, not from who reaches an object first",
        ending="Anya unlocked the drawer, and rows of clay tools waited for the afternoon class",
    ),
    Case(
        title="The Scarf at the Welcome Table",
        object_name="striped scarf",
        object_phrase="a green-and-yellow striped scarf folded on a chair",
        hidden_clue="one stripe held a tiny thread shaped like a star",
        likely_guess="the scarf belonged to the visitor whose coat was hanging nearest the chair",
        rightful_owner="Jo",
        owner_role="the new neighbor who had sewn the star into the scarf",
        place_detail="the welcome table",
        identifying_action="found the star-shaped thread and invited each possible owner to describe a detail without pressure",
        entitlement="Jo was entitled to the scarf because Jo explained why the star was sewn into the second green stripe",
        lesson="When several people might belong to a story, patient questions protect everyone from a wrong guess",
        ending="Jo wrapped the scarf around their shoulders and stayed for the first cup of warm tea",
    ),
    Case(
        title="The Notebook with a Folded Corner",
        object_name="blue notebook",
        object_phrase="a blue notebook with a folded corner",
        hidden_clue="the folded corner hid a drawing of three apples beside a crooked fence",
        likely_guess="the notebook belonged to the student whose name was first on the sign-in sheet",
        rightful_owner="Theo",
        owner_role="the neighbor who sketched the old orchard",
        place_detail="the reading room window",
        identifying_action="opened only the marked page, recognized the crooked fence, and asked who had drawn the orchard from the window",
        entitlement="Theo was entitled to the notebook because he could finish the drawing and explain why the corner had been folded",
        lesson="A private clue should be used carefully, only enough to identify and return what was lost",
        ending="Theo tucked the notebook under his arm and added one bright apple to the unfinished drawing",
    ),
]


def stable_seed(*parts: str) -> int:
    return sum((i + 1) * ord(ch) for i, ch in enumerate("|".join(parts)))


def identify(world: World, case: Case, object_entity: Entity, candidates: list[Entity]) -> Entity:
    if not object_entity.owner:
        raise StoryError("The object cannot be identified until its owner is established by evidence.")
    owner = next((candidate for candidate in candidates if candidate.id == object_entity.owner), None)
    if owner is None:
        raise StoryError("The identified owner must be one of the people present in the story.")
    object_entity.meters["clarity"] = 1.0
    object_entity.meters["visibility"] = 1.0
    object_entity.memes["hope"] = 1.0
    return owner


def entitle(world: World, owner: Entity, object_entity: Entity, case: Case) -> None:
    if object_entity.meters.get("clarity", 0.0) < 1.0:
        raise StoryError("A person cannot be entitled to the object before the clues identify the owner.")
    object_entity.owner = owner.id
    owner.memes["belonging"] = 1.0
    world.fired.add("entitled")
    world.facts["entitlement_reason"] = case.entitlement


OPENINGS = [
    "{hero} liked ordinary mornings at {place}, especially when {companion} was there to notice small things too.",
    "At {place}, {hero} and {companion} were setting out cups and chairs for the day's welcome table.",
    "{hero} arrived early at {place}, where {companion} was straightening a stack of books near {place_detail}.",
    "The morning was quiet enough for {hero} to hear a chair scrape at {place}. {companion} looked up from the welcome table.",
]

SUSPENSE_LINES = [
    "The afternoon visitors would arrive soon, and if the object went to the wrong person, its true owner might stop looking.",
    "A little suspense gathered in the room: the welcome table needed the answer before the last patch of sunlight left the floor.",
    "There was not much time before the neighbors came, and a quick guess could make an innocent person feel pushed aside.",
    "The clue was growing harder to see as dust settled over it, so the two friends knew they had to be careful and quick.",
]

DIALOGUES = [
    ('"We should identify it before we give it to anyone," said {hero}. "Then let us ask, not assume," replied {companion}.'),
    ('"I think I know who owns it," said {hero}. "Thinking is a start," said {companion}. "Evidence is what makes the return kind."'),
    ('"Could this be mine?" asked {companion}. "{companion}, tell me one detail only the owner would know," said {hero}.'),
    ('"What if we choose the wrong person?" asked {hero}. "Then we pause and look again," said {companion}.'),
    ('"Who is entitled to it?" {hero} wondered. "The person whose story fits the clue, not the person standing closest," said {companion}.'),
]

REFLECTIONS = [
    "They wrote the clue on a scrap of paper so they would remember the difference between a guess and a fact.",
    "The friends thanked each person who answered, because careful questions should never feel like a contest.",
    "Afterward, they placed a pencil beside the lost-and-found tray for the next mystery.",
    "The wrong guess had not been shameful; refusing to check it would have been.",
    "They agreed to label the welcome supplies before the next gathering.",
]

ENDING_BRIDGES = [
    "The room felt easier to breathe in once the question had an honest answer.",
    "The small return changed the mood more than a loud celebration could have done.",
    "No bell rang, but everyone noticed that one person now stood a little straighter.",
    "The ordinary work of the day continued, carrying the new understanding with it.",
]


def build_story(world: World, case: Case, hero: Entity, companion: Entity, owner: Entity, rng: random.Random) -> None:
    place = world.setting.place
    values = {
        "hero": hero.id,
        "companion": companion.id,
        "place": place,
        "place_detail": case.place_detail,
    }
    opening = rng.choice(OPENINGS).format(**values)
    suspense = rng.choice(SUSPENSE_LINES)
    dialogue = rng.choice(DIALOGUES).format(**values)
    reflection = rng.choice(REFLECTIONS)
    bridge = rng.choice(ENDING_BRIDGES)

    world.say(opening)
    world.say(f"Near {case.place_detail}, they found {case.object_phrase}. No name was visible, and the object seemed to be waiting for someone.")
    world.para()

    world.say(suspense)
    world.say(dialogue)
    world.say(f"{hero.id} wanted to follow the likely guess that {case.likely_guess}, but {companion.id} shook {companion.id}'s head.")
    world.para()

    world.say(f"Together they {case.identifying_action}. They discovered that {case.hidden_clue}.")
    world.say(f'"That is a real connection," said {companion.id}. "{owner.id} may be able to tell us more," said {hero.id}.')
    world.para()

    world.say(f"They invited {owner.id}, {case.owner_role}, to explain the object without being hurried. {owner.id} did so, and {case.entitlement}.")
    world.say(f"{hero.id} returned the {case.object_name}. {owner.id} held it carefully, while {companion.id} smiled at the proof that listening had worked.")
    world.para()

    world.say(reflection)
    world.say(f'"{case.lesson}," said {owner.id}. {bridge} {case.ending}.')
    world.para()


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero_type not in HERO_TYPES:
        raise StoryError(f"Unknown hero type: {params.hero_type}")
    if params.companion_type not in COMPANION_TYPES:
        raise StoryError(f"Unknown companion type: {params.companion_type}")
    if params.hero_name == params.companion_name:
        raise StoryError("The two friends must have different names.")

    seed = params.seed if params.seed is not None else stable_seed(
        params.setting,
        params.hero_type,
        params.companion_type,
        params.hero_name,
        params.companion_name,
    )
    rng = random.Random(seed)
    case = rng.choice(CASES)
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(params.hero_name, "character", params.hero_type))
    companion = world.add(Entity(params.companion_name, "character", params.companion_type))
    owner = world.add(Entity(case.rightful_owner, "character", "neighbor"))
    object_entity = world.add(Entity("found_object", "thing", case.object_name, case.object_phrase))

    hero.memes["hope"] = 1.0
    companion.memes["hope"] = 1.0
    hero.memes["worry"] = 1.0
    companion.memes["worry"] = 1.0
    object_entity.meters["wear"] = 1.0
    object_entity.meters["visibility"] = 0.0
    object_entity.owner = owner.id

    identified = identify(world, case, object_entity, [hero, companion, owner])
    entitle(world, identified, object_entity, case)

    hero.memes["worry"] = 0.0
    companion.memes["worry"] = 0.0
    hero.memes["belonging"] = 1.0
    companion.memes["belonging"] = 1.0

    build_story(world, case, hero, companion, owner, rng)
    world.facts.update(
        {
            "hero": hero,
            "companion": companion,
            "owner": owner,
            "object": object_entity,
            "case": case,
            "identified": identified,
            "quest_complete": True,
            "suspense_resolved": True,
        }
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    return [
        f"Write a Slice of Life story in which {hero.id} and {companion.id} identify a lost {case.object_name}.",
        f"Use gentle Suspense and a small Quest to discover who is entitled to the {case.object_name}.",
        f"End with a Lesson Learned about listening before deciding who belongs to something.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    owner: Entity = world.facts["owner"]  # type: ignore[assignment]
    setting: Setting = world.facts["case"] and world.setting
    return [
        QAItem(
            question=f"What did {hero.id} and {companion.id} find?",
            answer=f"They found {case.object_phrase} near {case.place_detail} in {setting.place}.",
        ),
        QAItem(
            question="Why was there suspense around the object?",
            answer=f"The friends needed to identify its owner before visitors arrived, and {case.likely_guess} could have led to a wrong return.",
        ),
        QAItem(
            question="What clue helped identify the owner?",
            answer=f"They discovered that {case.hidden_clue}. That clue connected the object to {case.rightful_owner}'s real experience.",
        ),
        QAItem(
            question=f"Why was {owner.id} entitled to the object?",
            answer=f"{owner.id} was entitled to it because {case.entitlement}.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"The lesson was that {case.lesson}.",
        ),
        QAItem(
            question="How did the ending show that the quest succeeded?",
            answer=f"The object was returned, and {case.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does identify mean?",
            answer="To identify something means to discover or recognize what it is or who it belongs to.",
        ),
        QAItem(
            question="What does entitle mean?",
            answer="To entitle someone means to give that person a rightful claim to something.",
        ),
        QAItem(
            question="Why should people check clues before returning a lost object?",
            answer="Checking clues helps prevent a wrong guess and gives the rightful owner a fair chance to be found.",
        ),
        QAItem(
            question="What makes a suspenseful everyday problem gentle for children?",
            answer="A gentle suspenseful problem has a real question and a little urgency, but the characters solve it through safe actions, conversation, and care.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
identified(O) :- found_object(O), owner(O, P), person(P).
entitled(P,O) :- identified(O), owner(O,P).
valid_story(S,H,C) :- setting(S), person_type(H), person_type(C), found_object(O), entitled(_,O).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for kind in sorted(set(HERO_TYPES + COMPANION_TYPES)):
        lines.append(asp.fact("person_type", kind))
    lines.append(asp.fact("found_object", "found_object"))
    lines.append(asp.fact("person", "owner"))
    lines.append(asp.fact("owner", "found_object", "owner"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {
        (setting, hero, companion)
        for setting in SETTINGS
        for hero in set(HERO_TYPES)
        for companion in set(COMPANION_TYPES)
    }
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: ASP gate matches Python expectations ({len(got)} combinations).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("only in ASP:", sorted(got - expected))
    print("only in Python:", sorted(expected - got))
    return 1


CURATED = [
    StoryParams("reading_room", "child", "library helper", "Luna", "Mara"),
    StoryParams("courtyard", "young gardener", "child", "Ivy", "Toby"),
    StoryParams("community_hall", "neighborhood friend", "library helper", "Pia", "June"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Slice of Life identify-and-entitle storyworld.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero-type", choices=HERO_TYPES)
    parser.add_argument("--companion-type", choices=COMPANION_TYPES)
    parser.add_argument("--hero-name")
    parser.add_argument("--companion-name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    companion_type = args.companion_type or rng.choice(COMPANION_TYPES)
    hero_name = args.hero_name or rng.choice(NAMES[hero_type])
    companion_name = args.companion_name or rng.choice(NAMES[companion_type])
    if hero_name == companion_name:
        alternatives = [name for name in NAMES[companion_type] if name != hero_name]
        companion_name = rng.choice(alternatives)
    return StoryParams(
        setting=setting,
        hero_type=hero_type,
        companion_type=companion_type,
        hero_name=hero_name,
        companion_name=companion_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        if entity.owner:
            details.append(f"owner={entity.owner}")
        lines.append(f"  {entity.id:14} ({entity.type}) {' '.join(details)}")
    lines.append(f"  quest_complete={world.facts.get('quest_complete')}")
    lines.append(f"  suspense_resolved={world.facts.get('suspense_resolved')}")
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
        print(asp_program())
        return
    if args.verify:
        status = asp_verify()
        if status:
            raise SystemExit(status)
        for params in CURATED:
            sample = generate(params)
            if not sample.story or len(sample.story_qa) < 3:
                raise SystemExit("Generated story verification failed.")
        print("OK: generated stories exercised.")
        return
    if args.asp:
        rows = asp_valid_stories()
        print(f"{len(rows)} compatible story triples:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, params in enumerate(CURATED):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise SystemExit("No stories could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.hero_name}: {params.setting} ({params.hero_type} + {params.companion_type})"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
