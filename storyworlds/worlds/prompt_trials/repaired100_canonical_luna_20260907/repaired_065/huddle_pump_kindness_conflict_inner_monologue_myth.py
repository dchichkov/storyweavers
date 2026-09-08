#!/usr/bin/env python3
"""A small mythic storyworld about a huddle, a pump, and kindness under pressure."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAMES = ["Luna", "Mira", "Tavi", "Orin", "Nia", "Sol", "Pax", "Ivo"]
COMPANIONS = ["her brother Rowan", "her friend Elio", "the shepherd boy Finn", "her cousin Mara"]
PLACES = ["the hill of blue stones", "the village square", "the wind-carved valley", "the old cedar field"]
WEATHER = ["a bright wind", "a copper sunset", "a hush of rain", "a silver moonrise"]
OPENINGS = [
    "Long ago, when the hills still remembered every promise,",
    "In the first spring after the river learned to sing,",
    "Before the village had a clock,",
    "On a morning when the clouds rested low,",
    "When the stars were said to listen closely,",
]
LESSONS = [
    "kindness is a strength that grows when it is shared",
    "a conflict becomes smaller when people stop guarding their pride",
    "a careful helper can restore what force would only worsen",
    "a brave heart listens before it acts",
]
SOUNDS = ["whuff-whuff", "puff-puff", "whoom-whoom", "hush-push"]


@dataclass(frozen=True)
class Trial:
    key: str
    creature: str
    need: str
    obstacle: str
    consequence: str
    clue: str
    repair: str
    ending: str
    symbol: str


TRIALS = [
    Trial(
        "cloud_lamb",
        "a cloud-lamb",
        "to climb back to the sky before night",
        "its little sky-balloon had lost its breath",
        "the lamb sank lower each time the quarrel grew louder",
        "the pump's handle moved only when two hands kept a steady rhythm",
        "Luna and her companion formed a huddle, traded turns, and pumped together while speaking gently",
        "the cloud-lamb rose and scattered a soft silver rain over the thirsty garden",
        "a silver bell",
    ),
    Trial(
        "sunbird",
        "a sunbird",
        "to carry dawn over the eastern ridge",
        "the round dawn-sail beneath its wings had gone flat",
        "the valley stayed gray while the children argued over who had caused the trouble",
        "one valve was tucked beneath a red feather",
        "Luna apologized for blaming too quickly, and the huddle searched together before pumping slowly",
        "the sunbird lifted the dawn-sail and poured gold across the valley",
        "a red feather",
    ),
    Trial(
        "river_foal",
        "a river-foal",
        "to return to the river's hidden spring",
        "its water-hoop had wilted beside the dry path",
        "the stream forgot its way whenever angry voices echoed nearby",
        "the hoop's blue mark had to face the north star",
        "the children made a quiet huddle, found the mark, and shared the pump until the hoop stood round",
        "the river-foal splashed home, and a bright stream followed",
        "a blue stone",
    ),
    Trial(
        "moon_tortoise",
        "a moon-tortoise",
        "to carry moonlight to a sleeping village",
        "the moon-pouch on its shell had become empty",
        "the village lamps dimmed as the children pulled the pump in opposite directions",
        "the pouch had a tiny golden seam where the air escaped",
        "Luna listened to the frightened tortoise, found the seam, and invited every helper into one calm huddle",
        "the moon-pouch glowed, and every sleeping window shone",
        "a golden thread",
    ),
    Trial(
        "wind_deer",
        "a wind-deer",
        "to leap over the mountain gate",
        "the wind-sack at its side had folded flat",
        "the mountain gate stayed shut while the helpers competed for the pump",
        "the sack opened only after its creases were smoothed",
        "the children stopped competing, smoothed the sack, and took equal turns with the pump",
        "the wind-deer leaped high enough to ring the mountain bells",
        "a white ribbon",
    ),
    Trial(
        "star_frog",
        "a star-frog",
        "to light the path for lost travelers",
        "the star-pod on its back had no air",
        "the path grew dark while the children accused one another",
        "the pod flashed whenever someone spoke a kind truth",
        "Luna admitted she was afraid, and the huddle answered with kind words before they pumped",
        "the star-frog blinked awake and made a bright road through the reeds",
        "a green spark",
    ),
]


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    weather: str


@dataclass
class Pump:
    label: str = "the old brass pump"
    working: bool = True
    pressure: float = 0.0


@dataclass
class StoryParams:
    place: str
    hero_name: str
    companion: str
    weather: str
    trial_key: str
    opening_index: int = 0
    dialogue_index: int = 0
    ending_index: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[str, str]] = set()

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


DIALOGUES = [
    ("“The pump is mine,” said the companion.", "“Then let us make the work ours,” Luna answered."),
    ("“You made the trouble,” said the companion.", "“I was frightened, not certain,” Luna replied."),
    ("“Push harder!” cried the companion.", "“First, let us listen,” said Luna."),
    ("“Why should I help?” asked the companion.", "“Because the creature is hurting, and we are here,” Luna said."),
    ("“I cannot find the answer,” whispered Luna.", "“You do not have to find it alone,” said the companion."),
    ("“We are wasting the last light,” said the companion.", "“Then kindness must move quickly, but not wildly,” Luna answered."),
]


def trial_for(key: str) -> Trial:
    for trial in TRIALS:
        if trial.key == key:
            return trial
    raise StoryError(f"Unknown trial: {key}")


def tell(setting: Setting, params: StoryParams) -> World:
    trial = trial_for(params.trial_key)
    world = World(setting)
    hero = world.add(Entity("hero", "child", params.hero_name))
    companion = world.add(Entity("companion", "child", params.companion))
    creature = world.add(Entity("creature", "mythic creature", trial.creature))
    pump_entity = world.add(Entity("pump", "tool", "the old brass pump"))
    pump = Pump()

    hero.memes.update(kindness=0.0, courage=0.4, worry=0.5, patience=0.3)
    companion.memes.update(kindness=0.0, pride=0.7, worry=0.4, patience=0.2)
    creature.memes.update(fear=0.8, hope=0.2)
    pump_entity.meters.update(pressure=0.0, shared=0.0)
    pump_entity.owner = "village"
    pump_entity.holder = "hero"

    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    first, second = DIALOGUES[params.dialogue_index % len(DIALOGUES)]
    ending_lead = [
        "When the first stars appeared,",
        "At dawn,",
        "By the time the village lamps were lit,",
        "That night,",
    ][params.ending_index % 4]

    world.say(f"{opening} {params.hero_name} reached {setting.place}.")
    world.say(
        f"There stood {trial.creature}, a being of old legend, needing {trial.need}. "
        f"{trial.obstacle.capitalize()} Nearby rested {pump.label}, its brass handle bright with age."
    )
    world.say(
        f"{params.companion.capitalize()} had one idea, while {params.hero_name} had another. "
        "Their ideas struck together like stones, and the conflict made the creature tremble."
    )
    world.para()

    world.say(first)
    world.say(second)
    world.say(
        f"Inside, {params.hero_name} thought, “If I win this argument, perhaps I will still lose the creature.” "
        "That inner voice was small, but it was honest."
    )
    world.say(f"{trial.consequence.capitalize()}.")
    world.para()

    world.say(
        f"Then {params.hero_name} noticed that {trial.clue}. "
        "Instead of reaching for the pump, Luna lowered her hands."
        if params.hero_name == "Luna"
        else f"Then {params.hero_name} noticed that {trial.clue}. "
        f"Instead of reaching for the pump, {params.hero_name} lowered their hands."
    )
    world.say(
        f"“Let us make a huddle,” said {params.hero_name}. "
        f"The two children gathered close around {trial.creature}, leaving the pump in the middle."
    )
    world.say(
        "In the huddle, each person named one fear and one hope. "
        f"{params.hero_name} admitted, “I was afraid we would fail.” "
        f"{params.companion.capitalize()} answered, “I was afraid you would not need me.”"
    )
    world.say(
        f"They agreed that {trial.repair}. "
        "Kindness did not erase the conflict; it gave the conflict a gentler place to end."
    )
    world.para()

    world.say(
        f"{params.hero_name} held the pump while {params.companion} pressed the handle. "
        f"The pump answered, {SOUNDS[params.ending_index % len(SOUNDS)]}, and the creature's hope grew."
    )
    world.say(trial.repair.capitalize() + ".")
    world.say(f"{ending_lead} {trial.ending.capitalize()}")
    world.say(
        f"The children remembered that {LESSONS[params.ending_index % len(LESSONS)]}. "
        f"Above them, {trial.symbol} shone as a sign that their huddle had changed the tale."
    )

    hero.memes.update(kindness=1.0, courage=0.8, worry=0.2, patience=1.0)
    companion.memes.update(kindness=1.0, pride=0.2, worry=0.1, patience=1.0)
    creature.memes.update(fear=0.1, hope=1.0)
    pump.pressure = 1.0
    pump_entity.meters.update(pressure=1.0, shared=1.0)
    pump_entity.holder = None
    world.fired.update({("conflict", "resolved"), ("huddle", "formed"), ("pump", "shared"), ("kindness", "shown")})
    world.facts.update(
        hero=hero,
        companion=companion,
        creature=creature,
        pump=pump,
        pump_entity=pump_entity,
        trial=trial,
        params=params,
    )
    return world


def prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    return [
        f"Tell a myth about {p.hero_name}, a huddle, and an old pump.",
        f"Show a conflict about helping {trial.creature}, then let kindness change the decision.",
        "Include an inner monologue, spoken dialogue, and a concrete magical resolution.",
    ]


def story_questions(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    trial: Trial = world.facts["trial"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Why did {trial.creature} need the pump?",
            f"{trial.creature.capitalize()} needed the pump because it had to {trial.need}. {trial.obstacle.capitalize()}",
        ),
        QAItem(
            "What caused the conflict?",
            "The children had different ideas and let fear and pride make them argue instead of listening to one another.",
        ),
        QAItem(
            "What happened in the huddle?",
            f"They lowered their hands, named their fears and hopes, and agreed that {trial.repair}.",
        ),
        QAItem(
            f"What did {p.hero_name} think privately?",
            f"{p.hero_name} thought that winning the argument might still mean losing {trial.creature}.",
        ),
        QAItem(
            "How did kindness help?",
            "Kindness made room for both children to speak, so they could share the work instead of competing for it.",
        ),
        QAItem(
            "What proved that the problem was solved?",
            trial.ending.capitalize(),
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    return [
        QAItem("What is a huddle?", "A huddle is a close gathering where people listen, plan, and support one another."),
        QAItem("What is a pump?", "A pump is a tool that moves air or another substance by pressing or pulling its handle."),
        QAItem("What is kindness?", "Kindness is choosing to help, listen, or speak gently when another being needs care."),
        QAItem("What is an inner monologue?", "An inner monologue is a character's private stream of thoughts, not spoken aloud."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {text}" for i, text in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.type} {entity.label} "
            f"meters={entity.meters} memes={entity.memes} "
            f"owner={entity.owner} holder={entity.holder}"
        )
    lines.append(f"events={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
huddle(hero,companion) :- child(hero), child(companion), conflict(hero,companion).
kindness(hero,companion) :- huddle(hero,companion), listens(hero,companion).
kindness(companion,hero) :- huddle(hero,companion), listens(companion,hero).
shared_pump(hero,companion,pump) :- huddle(hero,companion), pump(pump), kindness(hero,companion).
resolved(creature) :- shared_pump(hero,companion,pump), mythic(creature).
#show huddle/2.
#show kindness/2.
#show shared_pump/3.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("child", "hero"),
        asp.fact("child", "companion"),
        asp.fact("conflict", "hero", "companion"),
        asp.fact("listens", "hero", "companion"),
        asp.fact("listens", "companion", "hero"),
        asp.fact("pump", "pump"),
        asp.fact("mythic", "creature"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A mythic storyworld about a huddle and a pump.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--weather", choices=WEATHER)
    parser.add_argument("--trial", choices=[t.key for t in TRIALS])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        weather=args.weather or rng.choice(WEATHER),
        trial_key=args.trial or rng.choice(TRIALS).key,
        opening_index=rng.randrange(len(OPENINGS)),
        dialogue_index=rng.randrange(len(DIALOGUES)),
        ending_index=rng.randrange(4),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(params.place, params.weather), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if not asp.atoms(model, "huddle"):
        raise StoryError("ASP verification found no huddle.")
    if not asp.atoms(model, "shared_pump"):
        raise StoryError("ASP verification found no shared pump.")
    if not asp.atoms(model, "resolved"):
        raise StoryError("ASP verification found no resolution.")
    for trial in TRIALS:
        sample = generate(
            StoryParams(
                place=PLACES[0],
                hero_name="Luna",
                companion=COMPANIONS[0],
                weather=WEATHER[0],
                trial_key=trial.key,
            )
        )
        if not sample.story or "huddle" not in sample.story or "pump" not in sample.story:
            raise StoryError(f"Generated story failed for trial {trial.key}.")
        if not sample.story_qa or not sample.world_qa:
            raise StoryError("Generated story is missing QA.")
    return 0


CURATED = [
    StoryParams("the hill of blue stones", "Luna", "her friend Elio", "a silver moonrise", "cloud_lamb", 0, 0, 0),
    StoryParams("the village square", "Mira", "her cousin Mara", "a copper sunset", "sunbird", 1, 2, 1),
    StoryParams("the old cedar field", "Tavi", "the shepherd boy Finn", "a bright wind", "wind_deer", 3, 4, 2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(max(0, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
