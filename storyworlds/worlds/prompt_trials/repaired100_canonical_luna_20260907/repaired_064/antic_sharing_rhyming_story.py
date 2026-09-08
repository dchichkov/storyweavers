#!/usr/bin/env python3
"""A child-facing rhyming storyworld about an antic act of sharing."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    weather: str
    mood: str


@dataclass
class StoryParams:
    place: str
    treat: str
    name: str
    friend: str
    helper: str
    plan: str = ""
    rhyme: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class SharingPlan:
    missing: str
    tempting: str
    antic: str
    turn: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


PLACES = {
    "moonlit meadow": Scene("the moonlit meadow", "a soft silver breeze", "bright and mellow"),
    "rainy market": Scene("the rainy market", "a pattering shower", "cozy and humming"),
    "sunny hill": Scene("the sunny hill", "a warm golden wind", "cheery and wide"),
    "lantern lane": Scene("lantern lane", "a twinkling dusk", "glowy and gay"),
}

TREATS = {
    "berry bun": "a berry bun",
    "honey cake": "a honey cake",
    "apple tart": "an apple tart",
    "sugar plum": "a sugar plum",
}

FRIENDS = {"Mira": "girl", "Pip": "boy", "Nia": "girl", "Toby": "boy"}
HELPERS = {"rabbit": "rabbit", "badger": "badger", "sparrow": "sparrow", "fox": "fox"}
PLANS = {
    "berry_bun": SharingPlan(
        "one warm berry bun",
        "to hide the bun behind a drum",
        "danced a zigzag jig, then nearly hugged the bun instead of sharing it",
        "the bun was too large for one small belly but just right for a circle of friends",
        "split the bun into bright berry bites and offered the first piece to a quiet neighbor",
        "a treat grows sweeter when every friend gets a fair share",
        "crumbs made a happy ring while the moon shone clear and bright",
    ),
    "honey_cake": SharingPlan(
        "a round honey cake",
        "to carry the cake away in a purple pail",
        "wore a paper crown and marched around the cake, declaring, 'Mine, mine, mine!'",
        "the helper reminded everyone that the cake had been baked for the whole picnic",
        "cut the cake into equal wedges and passed them around the blanket",
        "fair pieces help a happy gathering stay happy",
        "sticky smiles shone beneath the lanterns after every plate was clean",
    ),
    "apple_tart": SharingPlan(
        "a crisp apple tart",
        "to stack the tart beneath a tall hat",
        "wobbled, bobbled, and made a grand antic bow when the hat tipped over",
        "the tumble showed that keeping everything alone made the tart harder to carry",
        "set the tart on a plate and invited each friend to choose one slice",
        "asking others to join can turn a mistake into a celebration",
        "the empty plate gleamed while apple-sweet laughter filled the lane",
    ),
    "sugar_plum": SharingPlan(
        "a sparkling sugar plum",
        "to roll the plum under a bench",
        "skipped in three circles and sang, 'No one may see my treat but me!'",
        "a smaller friend had brought no snack and watched with hopeful eyes",
        "cut the plum into tiny shining pieces for everyone to taste",
        "kindness notices who is waiting at the edge",
        "one little plum became many bright tastes beneath the evening star",
    ),
}

ROUTES = ("rhythm_first", "dialogue_first", "antic_first", "quiet_first", "crumb_map", "rain_first")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A rhyming story about antic sharing.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--treat", choices=sorted(TREATS))
    parser.add_argument("--name")
    parser.add_argument("--friend", choices=sorted(FRIENDS))
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


ASP_RULES = """
valid(Place,Treat) :- place(Place), treat(Treat).
""".strip()


def valid_combos() -> list[tuple[str, str]]:
    return [(place, treat) for place in sorted(PLACES) for treat in sorted(TREATS)]


def asp_facts() -> str:
    import asp
    facts = [asp.fact("place", place) for place in PLACES]
    facts.extend(asp.fact("treat", treat) for treat in TREATS)
    return "\n".join(facts)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    symbols = asp.one_model(asp_program())
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    python_pairs = set(valid_combos())
    asp_pairs = set(asp_valid_combos())
    if python_pairs == asp_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(python_pairs)} combos).")
        return 0
    print("MISMATCH:", sorted(python_pairs - asp_pairs), sorted(asp_pairs - python_pairs))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if not args.place or pair[0] == args.place
        if not args.treat or pair[1] == args.treat
    ]
    if not choices:
        raise StoryError("No valid sharing story fits those options.")
    place, treat = rng.choice(choices)
    name = args.name or "Luna"
    friend_choices = [friend for friend in sorted(FRIENDS) if friend != name]
    if not friend_choices:
        friend_choices = sorted(FRIENDS)
    return StoryParams(
        place=place,
        treat=treat,
        name=name,
        friend=args.friend or rng.choice(friend_choices),
        helper=args.helper or rng.choice(sorted(HELPERS)),
        plan=rng.choice(sorted(PLANS)),
        rhyme=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    key = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.treat,
            params.name,
            params.friend,
            params.helper,
            params.plan,
            params.rhyme,
        )
    )
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    plan = PLANS[params.plan]
    rng = story_rng(params)
    world = World(scene)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        meters={"care": 0.4, "sharing": 0.2},
        memes={"curiosity": 0.7},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type=FRIENDS[params.friend],
        meters={"hunger": 0.5},
        memes={"hope": 0.6},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=HELPERS[params.helper],
        meters={"wisdom": 0.7},
        memes={"patience": 0.8},
    ))
    treat = world.add(Entity(
        id="treat",
        kind="food",
        type="shared_treat",
        label=TREATS[params.treat],
        meters={"whole": 1.0, "pieces": 1.0},
        memes={"joy": 0.2},
    ))

    openings = {
        "rhythm_first": (
            f"At {scene.place}, beneath {scene.weather}, Luna found {plan.missing}. "
            f"It was round and golden, a treasure to hold, and the day felt {scene.mood}."
        ),
        "dialogue_first": (
            f'"Look at this!" {hero.id} cried at {scene.place}. '
            f'{plan.missing.capitalize()} sat by the picnic mat, while {scene.weather} whispered by.'
        ),
        "antic_first": (
            f"{hero.id} spotted {plan.missing} at {scene.place} and began an antic parade. "
            f"Step, hop, and twirl went the feet as {scene.weather} danced nearby."
        ),
        "quiet_first": (
            f"The meadow grew quiet at {scene.place}. Then {friend.id} saw {plan.missing}, "
            f"and {hero.id} held it close beneath {scene.weather}."
        ),
        "crumb_map": (
            f"{hero.id} drew a crumb-map through {scene.place}. At its end waited {plan.missing}, "
            f"shining like a small sun in {scene.mood} air."
        ),
        "rain_first": (
            f"When {scene.weather} began at {scene.place}, {hero.id} found {plan.missing}. "
            f"The treat looked warm, bright, and ready for a story."
        ),
    }
    world.say(openings[params.rhyme])
    world.say(rng.choice([
        f"{friend.id} smiled, but their empty basket made a tiny, rumbly sound.",
        f"{friend.id} clapped twice, then glanced at the bare picnic cloth.",
        f"The friends had brought bright cups, but only one cup held a snack.",
        f"{helper.id} watched kindly from a nearby stump and said nothing yet.",
    ]))
    world.para()

    world.say(f"At first, {hero.id} thought {plan.tempting}.")
    world.say(f"Then came the antic: {plan.antic}.")
    hero.memes["greedy_urge"] = 0.8
    world.say(rng.choice([
        f'"Could we share it?" {friend.id} asked. "A little bite would make the picnic bright."',
        f'"Mine alone?" {friend.id} asked softly. "Or can we make many smiles from one treat?"',
        f'"Please wait," said {friend.id}. "A feast feels best when no one is left out."',
        f'{helper.id} chuckled. "A treat held tight is small, but a treat shared right can travel far."',
    ]))
    world.say(f"{hero.id} stopped the antic and looked at {friend.id}, then at {helper.id}.")
    world.para()

    world.say(f"{helper.id} pointed out that {plan.turn}.")
    world.say(rng.choice([
        f"{hero.id} counted the cups: one, two, three, and more.",
        f"{friend.id} spread the napkins in a circle so every place looked important.",
        f"{hero.id} took a slow breath and traded a grab for a gentle plan.",
        f"The wind moved the crumbs toward the empty basket, as if showing the way.",
    ]))
    world.say(f'"Let us make it fair," {hero.id} said. "You may help me."')
    world.say(f'"Then I will pass the first piece," {friend.id} replied.')
    hero.meters["sharing"] = 1.0
    friend.memes["hope"] = 1.0
    world.para()

    world.say(f"Together, they {plan.repair}.")
    treat.meters["whole"] = 0.0
    treat.meters["pieces"] = 4.0
    treat.memes["joy"] = 1.0
    world.say(rng.choice([
        f"The antic became a happy dance, with no one pushed aside.",
        f"The silly crown became a serving hat, and everyone laughed at its new job.",
        f"The hiding place became a picnic place, open and bright.",
        f"The little snack made a large circle of welcome.",
    ]))
    world.say(f"{hero.id} learned that {plan.lesson}.")
    hero.memes["greedy_urge"] = 0.0
    world.say(rng.choice([
        f"At last, {plan.ending}.",
        f"When the crumbs were gone, {plan.ending}.",
        f"Under the {scene.mood} sky, {plan.ending.capitalize()}.",
        f"And so, with happy hands and hearts, {plan.ending}.",
    ]))
    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        treat=treat,
        scene=scene,
        plan=plan,
        treat_label=TREATS[params.treat],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    plan = facts["plan"]
    hero = facts["hero"]
    return [
        f"Write a rhyming story for young children about {hero.id} learning to share {facts['treat_label']}.",
        f"Include an antic but gentle moment, a brief dialogue between {hero.id} and {facts['friend'].id}, and a fair sharing solution.",
        f"End with the image that {plan.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    plan = facts["plan"]
    hero = facts["hero"]
    friend = facts["friend"]
    return [
        QAItem(
            question=f"What did {hero.id} find at {facts['scene'].place}?",
            answer=f"{hero.id} found {plan.missing} at {facts['scene'].place}.",
        ),
        QAItem(
            question=f"What antic did {hero.id} do before deciding to share?",
            answer=f"{hero.id} {plan.antic}.",
        ),
        QAItem(
            question=f"How did {friend.id}'s words change {hero.id}'s choice?",
            answer=f'{friend.id} asked for a fair share and explained that everyone could enjoy the treat. {hero.id} stopped the antic and chose to share.',
        ),
        QAItem(
            question=f"How did the friends divide the treat?",
            answer=f"Together, they {plan.repair}.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that {plan.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means allowing others to use or enjoy something with you, while trying to make the arrangement fair.",
        ),
        QAItem(
            question="What is an antic?",
            answer="An antic is a silly, playful, or surprising action, such as a funny dance or an exaggerated bow.",
        ),
        QAItem(
            question="Why can sharing make a small treat feel special?",
            answer="Sharing includes more people in the joy, so the treat becomes part of a friendly memory instead of belonging to only one person.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = [
        "== prompts ==",
        *(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1)),
        "",
        "== story qa ==",
    ]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  lesson={world.facts['plan'].lesson}")
    return "\n".join(lines)


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="moonlit meadow",
        treat="berry bun",
        name="Luna",
        friend="Mira",
        helper="rabbit",
        plan="berry_bun",
        rhyme="rhythm_first",
        seed=101,
    ),
    StoryParams(
        place="rainy market",
        treat="honey cake",
        name="Luna",
        friend="Pip",
        helper="badger",
        plan="honey_cake",
        rhyme="dialogue_first",
        seed=202,
    ),
    StoryParams(
        place="lantern lane",
        treat="sugar plum",
        name="Luna",
        friend="Nia",
        helper="sparrow",
        plan="sugar_plum",
        rhyme="antic_first",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, treat in combos:
            print(f"  {place:18} {treat}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header="### curated story"
            if args.all
            else (f"### variant {index + 1}" if len(samples) > 1 else ""),
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
