#!/usr/bin/env python3
"""
A humorous tall-tale storyworld about a mountain-spring quest, a pail of water,
and SPIC, the Sprocket-Powered Irrigation Caddy.

A traveler and a companion must bring spring water back to Windy-Bend. When the
loaded cart wobbles on the mountain trail, careful observation and shared work
turn a risky trip into a successful one.
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


_STORYWORLDS_ROOT = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()),
    None,
)
if _STORYWORLDS_ROOT is None:
    raise RuntimeError("Could not find storyworlds/results.py from this script.")

sys.path.insert(0, str(_STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Quest:
    id: str
    title: str
    goal: str
    stakes: str
    keyword: str


@dataclass(frozen=True)
class HumorMode:
    id: str
    title: str
    beat: str
    observation: str
    reply: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


def meter(entity: Entity | Setting, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity | Setting, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


def propagate(world: World) -> list[str]:
    """Apply the world's small set of causal rules and return their story lines."""
    hero = world.get("hero")
    helper = world.get("helper")
    cart = world.get("spic")
    pail = world.get("pail")
    pump = world.get("wind_pump")
    garden = world.get("garden")
    out: list[str] = []

    changed = True
    while changed:
        changed = False

        focus_sig = ("focus", hero.id)
        if (
            meme(hero, "curiosity") >= THRESHOLD
            and meme(hero, "worry") >= THRESHOLD
            and focus_sig not in world.fired
        ):
            world.fired.add(focus_sig)
            add_meme(hero, "focus")
            out.append(
                f"{hero.label} stopped tugging long enough to study the wheel tracks."
            )
            changed = True

        team_sig = ("teamwork", hero.id, helper.id)
        if (
            meme(hero, "focus") >= THRESHOLD
            and meter(helper, "observed_trouble") >= THRESHOLD
            and meter(hero, "listened") >= THRESHOLD
            and team_sig not in world.fired
        ):
            world.fired.add(team_sig)
            add_meter(hero, "teamwork")
            add_meme(helper, "trust")
            out.append(
                f"Because {hero.label} listened to {helper.label}'s observation, they made a plan together."
            )
            changed = True

        steady_sig = ("steady_load", cart.id, pail.id)
        if (
            meter(cart, "load_low") >= THRESHOLD
            and meter(pail, "secured") >= THRESHOLD
            and meter(hero, "teamwork") >= THRESHOLD
            and steady_sig not in world.fired
        ):
            world.fired.add(steady_sig)
            add_meter(cart, "steady")
            out.append(
                f"With the pail low and snug, SPIC stopped seesawing and held steady on the trail."
            )
            changed = True

        prime_sig = ("prime_pump", pump.id)
        if (
            meter(pail, "delivered") >= THRESHOLD
            and meter(pail, "water") >= THRESHOLD
            and prime_sig not in world.fired
        ):
            world.fired.add(prime_sig)
            add_meter(pump, "primed")
            out.append(
                "The spring water filled the wind pump's dry priming basin."
            )
            changed = True

        water_sig = ("water_garden", garden.id)
        if (
            meter(pump, "primed") >= THRESHOLD
            and meter(world.setting, "wind") >= THRESHOLD
            and water_sig not in world.fired
        ):
            world.fired.add(water_sig)
            add_meter(pump, "turning")
            add_meter(garden, "watered")
            garden.meters["thirsty"] = 0.0
            out.append(
                "The wind caught the pump blades, and well water ran into the thirsty garden."
            )
            changed = True

    return out


PLACES = {
    "windy_bend": Setting(
        id="windy_bend",
        place="Windy-Bend",
        affords={"mountain_spring", "wind_pump", "garden", "quest"},
        meters={"wind": 1.0},
        memes={"neighborly": 1.0},
    )
}

QUESTS = {
    "spring_water": Quest(
        id="spring_water",
        title="mountain-spring quest",
        goal="bring a pail of clear spring water back to Windy-Bend",
        stakes="the dry wind pump cannot draw well water for the garden",
        keyword="quest",
    )
}

HUMOR_MODES = {
    "spring_song": HumorMode(
        id="spring_song",
        title="the singing springs",
        beat="SPIC's springs squealed so high that a cloud stopped to hum the last note.",
        observation=(
            "Listen: SPIC squeals whenever the full pail swings, and the downhill "
            "wheel sinks at the same time."
        ),
        reply=(
            "You're right; let's lower the pail and tie it down. Will you hold the "
            "brake while I move it?"
        ),
    ),
    "hat_compass": HumorMode(
        id="hat_compass",
        title="the runaway hat",
        beat=(
            "A gust spun {helper}'s broad hat like a weather vane; it pointed "
            "downhill every time the pail leaned."
        ),
        observation=(
            "My hat points downhill whenever the pail swings, and that wheel track "
            "deepens at the same moment."
        ),
        reply=(
            "You're right; the load is rocking the cart. Let's lower the pail and "
            "tie it down. Will you hold the brake?"
        ),
    ),
    "goose_echo": HumorMode(
        id="goose_echo",
        title="the bowing goose",
        beat=(
            "A goose marched behind them, bowing to the pail every time it sloshed; "
            "it seemed to think water was royalty."
        ),
        observation=(
            "That goose bows whenever the pail swings, and the downhill wheel sinks "
            "at the same moment."
        ),
        reply=(
            "You're right; I was fighting the wobble. Let's lower the pail and tie it "
            "down. Will you hold the brake?"
        ),
    ),
}

NAMES = ["Mara", "Tavi", "Niko", "Jori", "Leda", "Odo", "Fenna", "Pip"]
HELPER_NAMES = ["Kit", "Bo", "Fenn", "Iva", "Ren", "Sela", "Toma", "Una"]

TALL_TALE_IMAGES = [
    "Mount Whistle was so tall that its shadow reached Windy-Bend a day before its peak did.",
    "At the summit, the snow had never met the ground and still introduced itself as a cloud.",
    "The mountain was so high that even its echo had to climb in stages.",
    "The spring at the top made a silver thread so fine that an ant could leap across it.",
]

SETTING = PLACES["windy_bend"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place_id, quest_id, humor_id)
        for place_id in PLACES
        for quest_id in QUESTS
        for humor_id in HUMOR_MODES
        if place_id == "windy_bend" and quest_id == "spring_water"
    ]


@dataclass
class StoryParams:
    place: str
    quest: str
    humor: str
    name: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Tell a humorous tall tale about a mountain-spring quest, a pail, "
            "and a spring-powered irrigation caddy."
        )
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--quest", choices=sorted(QUESTS))
    parser.add_argument("--humor", choices=sorted(HUMOR_MODES))
    parser.add_argument("--name", help="Name of the traveler.")
    parser.add_argument("--helper", help="Name of the traveler's companion.")
    parser.add_argument("-n", type=int, default=1, help="Number of stories to generate.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true", help="Generate each registered humor style.")
    parser.add_argument("--trace", action="store_true", help="Show the simulated world state.")
    parser.add_argument("--qa", action="store_true", help="Show prompts and question-and-answer sets.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--asp", action="store_true", help="Print the ASP twin and its facts.")
    parser.add_argument("--verify", action="store_true", help="Check ASP parity and generated stories.")
    parser.add_argument("--show-asp", action="store_true", help="Print the ASP twin and its facts.")
    return parser


def _valid_name(name: str) -> bool:
    return bool(name) and len(name) <= 32 and re.fullmatch(r"[A-Za-z][A-Za-z'-]*", name) is not None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "windy_bend"
    quest = args.quest or "spring_water"
    humor = args.humor or rng.choice(sorted(HUMOR_MODES))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        quest=quest,
        humor=humor,
        name=name,
        helper=helper,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place {params.place!r}; choose a registered place.")
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest {params.quest!r}; choose a registered quest.")
    if params.humor not in HUMOR_MODES:
        raise StoryError(f"Unknown humor style {params.humor!r}; choose a registered style.")
    if (params.place, params.quest, params.humor) not in valid_combos():
        raise StoryError(
            "That place, quest, and humor style do not form a supported tall-tale combination."
        )
    if not _valid_name(params.name):
        raise StoryError("The traveler's name must be a simple name of at most 32 letters.")
    if not _valid_name(params.helper):
        raise StoryError("The companion's name must be a simple name of at most 32 letters.")
    if params.name.casefold() == params.helper.casefold():
        raise StoryError("The traveler and companion need different names.")


def _say_events(world: World) -> None:
    for event in propagate(world):
        world.say(event)


def tell(world: World, params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    humor = HUMOR_MODES[params.humor]
    variant = (
        params.seed
        if params.seed is not None
        else sum((index + 1) * ord(char) for index, char in enumerate(
            f"{params.name}|{params.helper}|{params.humor}"
        ))
    )
    mountain_image = TALL_TALE_IMAGES[variant % len(TALL_TALE_IMAGES)]

    world.setting = Setting(
        id=place.id,
        place=place.place,
        affords=set(place.affords),
        meters=dict(place.meters),
        memes=dict(place.memes),
    )

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="traveler",
            label=params.name,
            meters={"sharing": 0.0},
            memes={"curiosity": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="companion",
            label=params.helper,
            meters={},
            memes={"trust": 0.0},
        )
    )
    spring = world.add(
        Entity(
            id="spring",
            kind="place",
            type="mountain_spring",
            label="the mountain spring",
            meters={"clear_water": 1.0},
            memes={},
        )
    )
    cart = world.add(
        Entity(
            id="spic",
            kind="thing",
            type="irrigation_caddy",
            label="SPIC",
            phrase="the SPIC cart",
            owner=hero.id,
            meters={"spring_coils": 6.0, "hook_height": 0.0},
            memes={},
        )
    )
    pail = world.add(
        Entity(
            id="pail",
            kind="thing",
            type="pail",
            label="pail",
            phrase="the stout wooden pail",
            owner=hero.id,
            meters={"water": 0.0},
            memes={},
        )
    )
    pump = world.add(
        Entity(
            id="wind_pump",
            kind="thing",
            type="wind_pump",
            label="the village wind pump",
            meters={"primed": 0.0, "turning": 0.0},
            memes={},
        )
    )
    garden = world.add(
        Entity(
            id="garden",
            kind="place",
            type="bean_garden",
            label="the bean garden",
            meters={"thirsty": 1.0, "watered": 0.0},
            memes={},
        )
    )

    if humor.id == "goose_echo":
        world.add(
            Entity(
                id="goose",
                kind="animal",
                type="goose",
                label="a goose",
                meters={"bowed_at_pail": 0.0},
                memes={"curious": 1.0},
            )
        )

    add_meme(hero, "curiosity")
    add_meme(world.setting, "hope")

    world.say(
        f"{place.place} was so windy that the mayor kept a spare hat on a weather vane, just in case the first hat escaped."
    )
    if meter(pump, "primed") < THRESHOLD and meter(garden, "thirsty") >= THRESHOLD:
        world.say(
            f"The wind pump had stopped, and {quest.stakes}. The bean leaves drooped like little green flags after a parade."
        )
    world.say(
        f"The mayor asked {hero.label} and {helper.label} to begin a {quest.title}: {quest.goal}."
    )
    world.say(
        f"They brought SPIC, the Sprocket-Powered Irrigation Caddy, a rattly little cart with six spring coils and a spoon for a steering lever."
    )
    world.say(
        f"{mountain_image} At its top, a clear spring bubbled into a stone cup."
    )

    world.para()
    if meter(spring, "clear_water") >= THRESHOLD:
        pail.meters["water"] = 1.0
        add_meter(spring, "collected")
        world.say(
            f"{hero.label} filled the pail with clear spring water. To keep it from bumping rocks, they hung it from SPIC's tall hook."
        )
    cart.meters["hook_height"] = 1.0

    if meter(pail, "water") >= THRESHOLD and meter(cart, "hook_height") >= THRESHOLD:
        add_meter(cart, "wobble")
        add_meter(pail, "spill_risk")
        add_meme(hero, "worry")

    world.say(
        f"On the way down, the full pail swung above the wheels. Each time it leaned, the downhill wheel cut a deeper groove, and water sloshed close to the rim."
    )
    add_meter(hero, "yanked")
    world.say(
        f"{hero.label} grabbed for the high handle and tugged harder. SPIC bounced sideways, and the water climbed even closer to the pail's lip."
    )
    _say_events(world)

    beat = humor.beat.format(helper=helper.label)
    world.say(beat)
    world.say(f'{helper.label} said, “{humor.observation}”')
    add_meter(helper, "observed_trouble")
    add_meter(hero, "listened")
    world.say(f'{hero.label} replied, “{humor.reply}”')
    add_meter(hero, "sharing")
    add_meter(helper, "sharing")
    world.say(f'{helper.label} answered, “I have the brake. Lower it when you are ready!”')

    world.para()
    cart.meters["hook_height"] = 0.0
    cart.meters["load_low"] = 1.0
    cart.meters["brake_held"] = 1.0
    pail.meters["secured"] = 1.0
    add_meter(hero, "lowered_load")
    add_meter(helper, "held_brake")
    world.say(
        f"Together, {hero.label} lowered the pail into the cart bed and wrapped it in a spare scarf. {helper.label} held the brake while {hero.label} tied the pail snugly in place."
    )
    _say_events(world)

    if (
        meter(cart, "steady") >= THRESHOLD
        and meter(pail, "secured") >= THRESHOLD
        and meter(pail, "water") >= THRESHOLD
    ):
        add_meter(cart, "safe_descent")
        add_meter(pail, "delivered")
        world.say(
            f"With the load steady, they took the bends slowly. The pail stayed upright, and not a drop of spring water escaped."
        )
    else:
        raise StoryError(
            "The cart could not make a safe descent; its load was not secured by teamwork."
        )

    world.para()
    world.say(
        f"Back in {place.place}, {hero.label} poured the spring water into the wind pump's dry priming basin."
    )
    _say_events(world)
    if meter(garden, "watered") >= THRESHOLD:
        add_meme(hero, "pride")
        add_meme(helper, "pride")
        world.say(
            f"By evening, water ran from the pump to the bean rows. The leaves lifted, and a radish grew so fast that it nudged the mayor's hat an inch into the air."
        )
        world.say(
            "The quest taught them that a clever cart still needs people who notice what its load is doing—and a friend willing to hold the brake."
        )
    else:
        raise StoryError("The spring water did not restart the village pump.")

    world.facts.update(
        hero=hero,
        helper=helper,
        spring=spring,
        cart=cart,
        pail=pail,
        pump=pump,
        garden=garden,
        quest=quest,
        humor=humor,
        mountain_image=mountain_image,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"]
    helper = facts["helper"]
    quest = facts["quest"]
    humor = facts["humor"]
    return [
        f"Write a humorous tall tale about {hero.label} and {helper.label} completing a mountain-spring quest with a pail.",
        f"Tell a child-friendly adventure in which {hero.label} learns to steady a swinging load by listening to {helper.label}.",
        f"Write a tall tale featuring SPIC, the Sprocket-Powered Irrigation Caddy, and this comic turn: {humor.beat}",
        f"Tell the story of how the village pump was restarted during the {quest.title}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    helper = facts["helper"]
    quest = facts["quest"]
    humor = facts["humor"]
    return [
        QAItem(
            question="Who went on the mountain-spring quest?",
            answer=(
                f"{hero.label} and {helper.label} went together to bring spring water "
                f"back to Windy-Bend."
            ),
        ),
        QAItem(
            question="Why did the village need the pail of spring water?",
            answer=(
                f"The wind pump's priming basin was dry, so the pump could not draw "
                f"well water for the bean garden until {hero.label} and {helper.label} "
                f"filled it with spring water."
            ),
        ),
        QAItem(
            question="Why did SPIC wobble on the mountain trail?",
            answer=(
                "The full pail hung high above the wheels. When it swung on the steep "
                "trail, the downhill wheel dug a deeper groove and the water sloshed "
                "close to the rim."
            ),
        ),
        QAItem(
            question="What clue helped them understand the trouble?",
            answer=(
                f"{helper.label} noticed that the downhill wheel sank whenever the "
                "pail swung. That observation showed {hero.label} that they should "
                "lower and secure the load instead of pulling harder."
            ),
        ),
        QAItem(
            question="How did they keep the pail safe on the way down?",
            answer=(
                f"{hero.label} lowered the pail into SPIC's cart bed and wrapped it in "
                f"a scarf while {helper.label} held the brake. The low, snug load let "
                f"them take the bends slowly without spilling the spring water."
            ),
        ),
        QAItem(
            question="What was the funny moment on their trip?",
            answer=(
                f"During the trip, {humor.beat.format(helper=helper.label)} "
                "The joke made the tall, bumpy journey feel a little less serious."
            ),
        ),
        QAItem(
            question="What changed after they returned to Windy-Bend?",
            answer=(
                "They poured the spring water into the pump's priming basin. The wind "
                "turned the pump, water flowed into the bean garden, and the leaves "
                "lifted again."
            ),
        ),
        QAItem(
            question="What did the travelers learn?",
            answer=(
                "They learned that noticing a problem and listening to a companion "
                "can work better than simply pulling harder."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer=(
                "A quest is a journey with a purpose, often one that asks travelers "
                "to solve a problem or help someone."
            ),
        ),
        QAItem(
            question="Why is it helpful to secure a heavy pail low on a cart?",
            answer=(
                "A low, tied-down load is less likely to swing and tip the cart, so it "
                "is easier to move safely."
            ),
        ),
        QAItem(
            question="What does a wind pump do?",
            answer=(
                "A wind pump uses moving air to turn its blades and help lift water "
                "from a well."
            ),
        ),
        QAItem(
            question="What is a tall tale?",
            answer=(
                "A tall tale is a funny story that makes events wonderfully bigger "
                "and more surprising than ordinary life."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    place = PLACES[params.place]
    world = World(
        setting=Setting(
            id=place.id,
            place=place.place,
            affords=set(place.affords),
            meters=dict(place.meters),
            memes=dict(place.memes),
        )
    )
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    setting_bits = []
    if world.setting.meters:
        setting_bits.append(f"meters={world.setting.meters}")
    if world.setting.memes:
        setting_bits.append(f"memes={world.setting.memes}")
    lines.append(
        f"{world.setting.id}: setting {' '.join(setting_bits)}".rstrip()
    )
    for entity in world.entities.values():
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(
            f"{entity.id}: {entity.type} {' '.join(bits)}".rstrip()
        )
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,Q,H) :- place(P), quest(Q), humor(H), supports(P,Q,H).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for quest_id in QUESTS:
        lines.append(asp.fact("quest", quest_id))
    for humor_id in HUMOR_MODES:
        lines.append(asp.fact("humor", humor_id))
    for place_id, quest_id, humor_id in valid_combos():
        lines.append(asp.fact("supports", place_id, quest_id, humor_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES.strip()}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        import asp  # noqa: F401
    except ImportError as error:
        print(f"ASP verification needs clingo and storyworlds/asp.py: {error}")
        return 2

    python_combos = set(valid_combos())
    try:
        clingo_combos = set(asp_valid_combos())
    except Exception as error:
        print(f"ASP verification failed: {error}")
        return 2

    if python_combos != clingo_combos:
        print(f"MISMATCH: Python={sorted(python_combos)} ASP={sorted(clingo_combos)}")
        return 1

    generated = 0
    for index, (place, quest, humor) in enumerate(sorted(python_combos)):
        params = StoryParams(
            place=place,
            quest=quest,
            humor=humor,
            name="Mara",
            helper="Kit",
            seed=9100 + index,
        )
        try:
            sample = generate(params)
        except StoryError as error:
            print(f"Generated-story check failed for {params}: {error}")
            return 1

        if (
            sample.world is None
            or not sample.story.strip()
            or "said, “" not in sample.story
            or "replied, “" not in sample.story
            or "water ran from the pump" not in sample.story
            or not sample.story_qa
            or not sample.world_qa
        ):
            print(f"Generated-story check failed for humor style {humor}.")
            return 1

        live = sample.world
        if (
            meter(live.get("spic"), "steady") < THRESHOLD
            or meter(live.get("pail"), "delivered") < THRESHOLD
            or meter(live.get("wind_pump"), "turning") < THRESHOLD
            or meter(live.get("garden"), "watered") < THRESHOLD
        ):
            print(f"World-state check failed for humor style {humor}.")
            return 1
        generated += 1

    try:
        generate(
            StoryParams(
                place="unknown",
                quest="spring_water",
                humor="spring_song",
                name="Mara",
                helper="Kit",
            )
        )
    except StoryError:
        pass
    else:
        print("Invalid-place check failed: an unsupported place was accepted.")
        return 1

    print(
        f"OK: ASP matches Python ({len(python_combos)} combinations); "
        f"generated and checked {generated} complete stories."
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


CURATED = [
    StoryParams(
        place="windy_bend",
        quest="spring_water",
        humor="spring_song",
        name="Mara",
        helper="Kit",
    ),
    StoryParams(
        place="windy_bend",
        quest="spring_water",
        humor="hat_compass",
        name="Tavi",
        helper="Bo",
    ),
    StoryParams(
        place="windy_bend",
        quest="spring_water",
        humor="goose_echo",
        name="Niko",
        helper="Sela",
    ),
]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp or args.asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.n < 1 and not args.all:
        parser.error("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    try:
        if args.all:
            for index, curated in enumerate(CURATED):
                params = StoryParams(
                    place=curated.place,
                    quest=curated.quest,
                    humor=curated.humor,
                    name=curated.name,
                    helper=curated.helper,
                    seed=base_seed + index,
                )
                samples.append(generate(params))
        else:
            seen: set[str] = set()
            attempts = 0
            limit = max(args.n * 40, 40)
            while len(samples) < args.n and attempts < limit:
                seed = base_seed + attempts
                attempts += 1
                rng = random.Random(seed)
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError(
                    f"Could generate only {len(samples)} distinct stories after {attempts} attempts."
                )
    except StoryError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} and {sample.params.helper}: {HUMOR_MODES[sample.params.humor].title}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
