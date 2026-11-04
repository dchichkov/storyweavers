#!/usr/bin/env python3
"""
A tall-tale storyworld about a pail, a curious squeak called a spic, and a
quest to bring rain back to a thirsty prairie town.

The story is simulated from physical meters and emotional memes: a failed kite
plan gives way to careful listening, a shared rhythm, and a full town cistern.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if _parent.name == "storyworlds":
        sys.path.insert(0, str(_parent.parent))
        break

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    name: str
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Quest:
    id: str
    title: str
    goal: str
    reward: str


@dataclass(frozen=True)
class Humor:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class Companion:
    id: str
    speaker: str
    kind: str
    introduction: str


@dataclass(frozen=True)
class Route:
    id: str
    method: str
    comic_consequence: str
    ending_image: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple[str, str]] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


PLACES = {
    "dry_gulch": Setting(
        id="dry_gulch",
        name="Dry Gulch",
        place="the prairie town of Dry Gulch",
        affords={"ridge", "well", "wind", "clouds"},
    )
}

QUESTS = {
    "cloud_pail": Quest(
        id="cloud_pail",
        title="Cloud Pail Quest",
        goal="bring a pailful of rain down from the cloud on Tin Cup Ridge",
        reward="the first clear cup from the refilled town cistern",
    )
}

HUMORS = {
    "tall_tale": Humor(
        id="tall_tale",
        name="Tall Tale",
        description="a playful prairie yarn with impossible scale and a kind ending",
    )
}

COMPANIONS = {
    "mule": Companion(
        id="mule",
        speaker="Pip",
        kind="mule",
        introduction="Pip the mule",
    ),
    "goose": Companion(
        id="goose",
        speaker="Dot",
        kind="goose",
        introduction="Dot the goose",
    ),
    "goat": Companion(
        id="goat",
        speaker="Bram",
        kind="goat",
        introduction="Bram the goat",
    ),
    "dog": Companion(
        id="dog",
        speaker="Tumble",
        kind="dog",
        introduction="Tumble the dog",
    ),
}

ROUTES = [
    Route(
        id="bread",
        method="a staircase of sourdough loaves baked hard as wagon wheels",
        comic_consequence="the mule ate one step, so they bounced the last few yards",
        ending_image="one tiny green sprout poked through the last ridge-top crumb",
    ),
    Route(
        id="springs",
        method="a ladder made from old wagon springs",
        comic_consequence="each rung bounced them so high that they landed facing backward",
        ending_image="the last wagon spring gave a happy little bounce beside the bubbling well",
    ),
    Route(
        id="socks",
        method="a rope ladder knitted from mismatched wool socks",
        comic_consequence="the socks stretched like taffy and swung them gently over the summit",
        ending_image="three wool socks dried on the ridge, each holding a bead of sunlight",
    ),
    Route(
        id="pie_plates",
        method="a staircase of enormous tin pie plates",
        comic_consequence="every step rang like a dinner bell, and the final plate flipped them onto the ridge",
        ending_image="a pie plate on the ridge held a puddle that reflected the whole town",
    ),
]

NAMES = ["Juniper", "Milo", "Tansy", "Rufus", "Clover", "Willa", "Otis", "Fern"]
TRAITS = ["bold", "patient", "cheerful", "curious", "sturdy-hearted", "inventive"]

OPENINGS = [
    "Dry Gulch was so thirsty that its well hauled up one scoop of dust and a beetle wearing a puzzled expression.",
    "The prairie sun baked Dry Gulch until the town's weather vane pointed down, just to get out of the heat.",
    "In Dry Gulch, the creek had shrunk to a ribbon, and even the ducks had started carrying canteens.",
    "Dry Gulch had gone so long without rain that the mayor's fountain coughed up a tumbleweed and apologized.",
]

DIALOGUES = [
    (
        "That spic falls between the cloud's hiccups. The pail is keeping time, not leaking!",
        "Then we will climb close and tap its rhythm instead of hauling it through the sky.",
    ),
    (
        "Hear that? The cloud coughs twice, and your pail squeaks right in the middle.",
        "Good ears! I will follow the beat, and you tell me when the cloud answers.",
    ),
    (
        "That little spic matches the pause in the thunder. Maybe the cloud is waiting for a reply.",
        "Then let us answer gently. The kite can stay tangled in the hay.",
    ),
    (
        "The pail's squeak comes just before the cloud hiccups again. It is a clue, not a leak.",
        "You are right. We will use the sound to find the cloud's rhythm.",
    ),
]

PARAMETER_REGISTRIES = {
    "place": PLACES,
    "quest": QUESTS,
    "humor": HUMORS,
    "companion": COMPANIONS,
}
COMPATIBLE_COMBOS = [("dry_gulch", "cloud_pail", "tall_tale")]


@dataclass
class StoryParams:
    place: str
    quest: str
    humor: str
    name: str
    companion: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return list(COMPATIBLE_COMBOS)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place {params.place!r}; this quest takes place in Dry Gulch.")
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest {params.quest!r}; the available quest is the Cloud Pail Quest.")
    if params.humor not in HUMORS:
        raise StoryError(f"Unknown humor style {params.humor!r}; this story uses the Tall Tale style.")
    if params.companion not in COMPANIONS:
        choices = ", ".join(sorted(COMPANIONS))
        raise StoryError(f"Unknown companion {params.companion!r}; choose one of: {choices}.")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown hero trait {params.trait!r}.")
    if not re.fullmatch(r"[A-Za-z][A-Za-z'-]{0,19}", params.name):
        raise StoryError("A hero's name must be 1–20 simple letters, with an optional apostrophe or hyphen.")
    if (params.place, params.quest, params.humor) not in COMPATIBLE_COMBOS:
        raise StoryError("The Cloud Pail Quest only fits the prairie setting and Tall Tale style.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tell a humorous tall tale about a prairie quest, a pail, and a curious squeak."
    )
    parser.add_argument("--place")
    parser.add_argument("--quest")
    parser.add_argument("--humor")
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--trait")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        place=args.place or "dry_gulch",
        quest=args.quest or "cloud_pail",
        humor=args.humor or "tall_tale",
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(sorted(COMPANIONS)),
        trait=args.trait or rng.choice(TRAITS),
    )
    reasonableness_gate(params)
    return params


def propagate(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    pail = world.get("pail")
    cloud = world.get("cloud")
    town = world.get("town")

    if meter(pail, "swing") >= 1 and meter(pail, "loose_handle") >= 1:
        signature = ("spic", pail.id)
        if signature not in world.fired:
            world.fired.add(signature)
            add_meter(pail, "spic_count", 1)
            add_meme(pail, "noticed", 1)

    if meme(hero, "attention") >= 1 and meme(companion, "insight") >= 1:
        signature = ("shared_clue", hero.id)
        if signature not in world.fired:
            world.fired.add(signature)
            add_meme(hero, "plan", 1)
            add_meme(companion, "trust", 1)

    if (
        meme(hero, "plan") >= 1
        and meter(hero, "at_ridge") >= 1
        and meter(pail, "rhythm") >= 1
    ):
        signature = ("cloud_hears", cloud.id)
        if signature not in world.fired:
            world.fired.add(signature)
            add_meme(cloud, "amused", 1)

    if meme(cloud, "amused") >= 1:
        signature = ("rain", cloud.id)
        if signature not in world.fired:
            world.fired.add(signature)
            add_meter(cloud, "rain_released", 1)
            add_meter(pail, "water", 1)
            add_meme(hero, "relief", 1)

    if meter(pail, "water") >= 1 and meter(pail, "returned") >= 1:
        signature = ("cistern", town.id)
        if signature not in world.fired:
            world.fired.add(signature)
            add_meter(town, "cistern_water", 1)
            add_meme(town, "hope", 1)


def tell(world: World, params: StoryParams) -> World:
    variant = params.seed if params.seed is not None else sum(
        (index + 1) * ord(char)
        for index, char in enumerate(
            f"{params.name}|{params.companion}|{params.trait}"
        )
    )
    route = ROUTES[variant % len(ROUTES)]
    opening = OPENINGS[(variant // len(ROUTES)) % len(OPENINGS)]
    dialogue = DIALOGUES[(variant // (len(ROUTES) * len(OPENINGS))) % len(DIALOGUES)]
    companion_info = COMPANIONS[params.companion]
    quest = QUESTS[params.quest]

    hero = world.add(Entity("hero", "character", "child", params.name))
    companion = world.add(
        Entity("companion", "character", companion_info.kind, companion_info.speaker)
    )
    pail = world.add(Entity("pail", "thing", "pail", "the dented pail"))
    cloud = world.add(Entity("cloud", "weather", "cloud", "the cloud on Tin Cup Ridge"))
    town = world.add(Entity("town", "place", "town", "Dry Gulch"))

    add_meme(hero, "curiosity", 1)
    add_meme(companion, "willingness", 1)
    add_meter(pail, "loose_handle", 1)
    add_meter(cloud, "thunder_hiccups", 2)

    world.say(opening)
    world.say(
        f"{hero.label}, a {params.trait} child, accepted the {quest.title}: {quest.goal}."
    )
    world.say(
        f"{companion_info.introduction} came along with a dented pail. Its loose handle made a bright little \"spic!\" whenever it swung; in Dry Gulch, spic was the old word for that particular squeak."
    )

    world.para()
    world.say(
        f"First, {hero.label} tied the pail to a kite as wide as a barn door and tried to fly it straight to the cloud."
    )
    add_meter(hero, "kite_attempt", 1)
    add_meter(pail, "swing", 1)
    propagate(world)
    add_meter(pail, "caught_in_hay", 1)
    add_meme(hero, "worry", 1)
    world.say(
        "The kite tugged once, the pail swung with a spic, and both landed in a haystack. The pail held no rain, but above the ridge the cloud gave two thunder hiccups."
    )

    first_line, second_line = dialogue
    world.say(f'{companion_info.speaker} cocked an ear. "{first_line}"')
    world.say(f'{hero.label} grinned. "{second_line}"')
    add_meme(companion, "insight", 1)
    add_meme(hero, "attention", 1)
    propagate(world)

    world.para()
    add_meter(hero, "at_ridge", 1)
    add_meter(companion, "at_ridge", 1)
    world.say(
        f"Using {route.method}, the pair climbed Tin Cup Ridge; {route.comic_consequence}."
    )
    add_meter(pail, "rhythm", 1)
    add_meter(pail, "swing", 1)
    propagate(world)
    world.say(
        f"Under the cloud, {hero.label} held the pail steady while {companion_info.speaker} counted the thunder hiccups. They swung the handle in time: spic, spic, spic."
    )

    if meter(pail, "water") < 1:
        raise StoryError("The shared rhythm did not reach the cloud; the quest cannot be completed.")
    world.say(
        "The cloud tried to stay stern, but the pail's little answer tickled it into a laugh. One silver drop became a shower, and the pail filled before the cloud could hiccup again."
    )

    world.para()
    add_meter(pail, "returned", 1)
    add_meter(hero, "brought_water_home", 1)
    propagate(world)
    if meter(town, "cistern_water") < 1:
        raise StoryError("The pail returned without filling Dry Gulch's cistern.")
    add_meme(hero, "pride", 1)
    add_meme(companion, "pride", 1)
    world.say(
        f"Back in Dry Gulch, {hero.label} poured the rain into the town cistern, where neighbors could share it. The quest's reward was {quest.reward}."
    )
    world.say(
        f"By sundown, cups were full and the well was bubbling again. {route.ending_image}; beside it, the kite drooped in the hay like a sleepy bat."
    )
    world.say(
        "After that, the pail hung by the well. Whenever its handle went spic, the children remembered to listen for a clue before launching anything."
    )

    world.facts.update(
        hero=hero,
        companion=companion,
        companion_info=companion_info,
        pail=pail,
        cloud=cloud,
        town=town,
        quest=quest,
        route=route,
        dialogue=dialogue,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(PLACES[params.place])
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"]
    quest = facts["quest"]
    route = facts["route"]
    return [
        f"Write a child-friendly Tall Tale about {hero.label} completing the {quest.title} with a pail and a curious sound.",
        f"Tell a humorous prairie quest in which {hero.label} learns to listen before choosing how to reach a cloud.",
        f"Write a complete story about a pail whose handle makes a little spic, and explain how that sound helps Dry Gulch.",
        f"Use an exaggerated but kind adventure in which the heroes climb by {route.method} and bring rain home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    companion = facts["companion_info"]
    pail = facts["pail"]
    town = facts["town"]
    route = facts["route"]
    quest = facts["quest"]
    return [
        QAItem(
            question=f"What quest did {hero.label} accept?",
            answer=f"{hero.label} accepted the {quest.title}, a quest to bring a pailful of rain down from the cloud on Tin Cup Ridge.",
        ),
        QAItem(
            question="What did the word spic mean in Dry Gulch?",
            answer="In Dry Gulch, a spic was the bright little squeak made by the pail's loose handle when the pail swung.",
        ),
        QAItem(
            question=f"Why did {hero.label}'s first plan fail?",
            answer=f"{hero.label} tied the pail to a huge kite, but the swinging pail pulled it into a haystack before it could reach the cloud, so it brought back no water.",
        ),
        QAItem(
            question="What clue changed the heroes' plan?",
            answer=f"{companion.speaker} noticed that the pail's spic came between the cloud's two thunder hiccups, so the squeak could keep time instead of being treated as a leak.",
        ),
        QAItem(
            question="How did the heroes reach Tin Cup Ridge?",
            answer=f"They climbed by {route.method}; {route.comic_consequence}.",
        ),
        QAItem(
            question=f"How did {hero.label} get rain into the pail?",
            answer=f"{hero.label} held the pail steady while {companion.speaker} counted the cloud's hiccups, and they swung the handle in rhythm. The cloud laughed at the answering squeak and released rain into the pail.",
        ),
        QAItem(
            question="How did the quest change Dry Gulch?",
            answer=f"{hero.label} brought the full pail home and poured it into {town.label}'s cistern, giving the neighbors water to share and making the well bubble again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pail?",
            answer="A pail is a sturdy container with a handle, useful for carrying things such as water.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a playful story that stretches events into wonderfully exaggerated adventures.",
        ),
        QAItem(
            question="Why can listening carefully help solve a problem?",
            answer="Listening carefully can reveal a pattern or clue that changes what someone knows and helps them choose a better plan.",
        ),
        QAItem(
            question="Why is rain useful to a town?",
            answer="Rain can refill wells and cisterns, giving people and plants water they need.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    parts.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    parts.extend(["", "== World QA =="])
    for item in sample.world_qa:
        parts.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        state = []
        if entity.meters:
            state.append(f"meters={entity.meters}")
        if entity.memes:
            state.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {entity.type} {' '.join(state)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_type(Q).
humor(H) :- humor_type(H).
valid(P,Q,H) :- place(P), quest(Q), humor(H), fits(P,Q,H).

fits(dry_gulch,cloud_pail,tall_tale).
"""


def asp_facts() -> str:
    from storyworlds import asp

    facts = []
    for place in PLACES:
        facts.append(asp.fact("setting", place))
    for quest in QUESTS:
        facts.append(asp.fact("quest_type", quest))
    for humor in HUMORS:
        facts.append(asp.fact("humor_type", humor))
    return "\n".join(facts)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams("dry_gulch", "cloud_pail", "tall_tale", "Juniper", "mule", "bold", 0),
    StoryParams("dry_gulch", "cloud_pail", "tall_tale", "Milo", "goose", "patient", 1),
    StoryParams("dry_gulch", "cloud_pail", "tall_tale", "Tansy", "goat", "cheerful", 2),
    StoryParams("dry_gulch", "cloud_pail", "tall_tale", "Rufus", "dog", "inventive", 3),
]


def asp_verify() -> int:
    try:
        samples = [generate(params) for params in CURATED]
        for sample in samples:
            if "spic" not in sample.story or "pail" not in sample.story.lower():
                raise AssertionError("A generated tale omitted a required story element.")
            if len(sample.story_qa) < 5 or not sample.world:
                raise AssertionError("A generated tale is missing its story model or grounded answers.")
            if sample.world.entities["pail"].meters.get("water", 0) < 1:
                raise AssertionError("A generated tale did not complete its pail quest.")

        try:
            generate(StoryParams("dry_gulch", "unknown", "tall_tale", "Mira", "mule", "bold"))
        except StoryError:
            pass
        else:
            raise AssertionError("The reasonableness gate accepted an invalid quest.")

        from storyworlds import asp

        python_combos = set(valid_combos())
        answer_sets = set(asp_valid_combos())
        if python_combos != answer_sets:
            print(f"MISMATCH: Python={sorted(python_combos)} ASP={sorted(answer_sets)}")
            return 1
    except (ImportError, ModuleNotFoundError) as error:
        print(f"Verification could not load the ASP helper: {error}")
        return 1
    except (AssertionError, StoryError) as error:
        print(f"Verification failed: {error}")
        return 1

    print(
        f"OK: ASP matches Python ({len(python_combos)} combo); "
        f"{len(samples)} generated stories completed their quests."
    )
    return 0


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.n < 1 and not args.all:
        print("The number of stories must be at least one.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 30, 30):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
            header = f"### {params.name}: {params.quest} / {params.humor}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
