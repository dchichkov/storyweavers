#!/usr/bin/env python3
"""
A fairy-tale storyworld about a frown, a dim passage, and the bravery to enter it.

Luna must pass a dim passage beneath the old hill. Her first fear makes the
stone guardian frown, but bravery grows when Luna tells the truth, accepts a
small helper, and carries a steady spark for someone else.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "princess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "prince"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trial:
    id: str
    title: str
    risk: str
    clue: str
    reward: str


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    obstacle: str
    false_start: str
    clue: str
    helper: str
    shared_item: str
    careful_action: str
    result: str
    change: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def meme(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = meter(entity, key) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = meme(entity, key) + amount


SETTING = Setting(
    place="the moonlit hill",
    affords={"courage", "listening", "passage", "kindness"},
)

TRIALS = {
    "pass_dim": Trial(
        id="pass_dim",
        title="the dim passage trial",
        risk="the tunnel might turn and hide the way home",
        clue="a tiny silver mark glimmered where the safe stones began",
        reward="the lantern key",
    )
}

SCENARIOS = [
    Scenario(
        id="echoing_steps",
        opening="At the foot of the moonlit hill stood a narrow door with no handle.",
        obstacle="Beyond it lay a dim passage where every footstep came back as a strange whisper.",
        false_start="Luna nearly ran away, for the whisper sounded like a giant following her.",
        clue="the echo returned from the left wall more quickly than from the right",
        helper="a small silver mouse",
        shared_item="a blue thread",
        careful_action="tied the blue thread along the right wall while the silver mouse listened for the returning echo",
        result="the passage opened into a warm chamber, and no giant had been hiding there",
        change="every traveler would leave a bright thread behind and listen before turning",
        lesson="bravery is not the absence of a frown or a fear; it is choosing a careful step while fear is present",
        ending="Luna carried the lantern key home, and the once-dim passage shone with a blue thread like a little river of sky.",
    ),
    Scenario(
        id="sleeping_stones",
        opening="The hill door opened only when the moon touched its silver hinge.",
        obstacle="Inside, sleeping stones blocked the path and grumbled whenever anyone hurried past them.",
        false_start="Luna stamped her foot and tried to make the stones obey.",
        clue="one stone sighed whenever a nearby drop of water fell",
        helper="a patient brook sprite",
        shared_item="a wooden cup",
        careful_action="shared the wooden cup with the brook sprite and poured water beside the stones one drop at a time",
        result="the stones rolled aside peacefully and revealed a stair beneath the hill",
        change="future travelers would wake the hill with patience instead of noise",
        lesson="bravery can sound like a gentle voice when anger would only make the darkness harder",
        ending="The stones slept on either side of the stair, while Luna's brave cup rang softly in the moonlight.",
    ),
    Scenario(
        id="thorn_shadow",
        opening="A crown of thorns guarded the entrance to the old fairy road.",
        obstacle="Its shadow stretched across the pass, making the path look far longer than it was.",
        false_start="Luna reached for a sword-shaped branch and planned to cut the shadow away.",
        clue="the shadow moved only when the thorn crown moved",
        helper="a kind raven",
        shared_item="a red ribbon",
        careful_action="asked the raven to watch the sun and tied the red ribbon to the living branch instead of striking it",
        result="the crown bent aside, and the shadow became no bigger than a cloak",
        change="the fairy road would be marked by ribbons rather than broken branches",
        lesson="bravery grows wiser when it observes before it fights",
        ending="The raven flew above a red ribbon road, and Luna walked through without wounding the thorn crown.",
    ),
    Scenario(
        id="bell_of_fear",
        opening="A bell hung over the passage, though no hand could reach its rope.",
        obstacle="Each frightened thought made the bell ring, and each ringing made the passage dimmer.",
        false_start="Luna covered her ears and wished the bell would vanish.",
        clue="the bell grew quiet whenever she named one true thing she could see",
        helper="an old candle fairy",
        shared_item="a warm candle",
        careful_action="held the warm candle with the fairy and named the stones, the door, and her own steady feet",
        result="the bell became silent and the passage filled with gentle gold light",
        change="the kingdom would teach children to name what was true when fear made pictures",
        lesson="bravery gives fear a smaller room when truth is spoken aloud",
        ending="The bell slept above the door, and Luna's candle made a golden circle wherever she went.",
    ),
    Scenario(
        id="lost_star",
        opening="A fallen star had rolled into the deepest part of the hill.",
        obstacle="Its light was too dim to show the way out, and its lonely glow made the fairies frown.",
        false_start="Luna wanted to carry the star alone, though it was too heavy for her arms.",
        clue="the star brightened when two hands touched its cool edge",
        helper="a shy cloud child",
        shared_item="a woven sling",
        careful_action="asked the cloud child to hold one side of the woven sling and lifted the star together",
        result="the star rose lightly and lit the whole passage from floor to ceiling",
        change="lost lights would always be carried by more than one willing helper",
        lesson="bravery does not insist on being alone; it knows when shared strength is the safer magic",
        ending="The star returned to the sky, and its silver beam rested on Luna's smiling face.",
    ),
    Scenario(
        id="dragon_breath",
        opening="A young dragon guarded the only gate through the hill.",
        obstacle="Every time the dragon sneezed, a red cloud covered the stones and made the passage dim.",
        false_start="Luna raised a shield and prepared to challenge the dragon.",
        clue="the dragon sneezed only when the dusty gate creaked",
        helper="the dragon's little sister",
        shared_item="a soft feather",
        careful_action="shared the soft feather with the dragon's sister and brushed dust from the gate hinge",
        result="the dragon stopped sneezing and politely opened the way",
        change="the gate would be oiled and swept before every traveler arrived",
        lesson="bravery can protect a frightening friend instead of turning every danger into a battle",
        ending="The dragon waved its tail as Luna passed, and a clean breath warmed the dim stones.",
    ),
    Scenario(
        id="mirror_water",
        opening="The fairy queen sent Luna through a passage lined with still pools.",
        obstacle="Each pool showed a gloomy face, and the faces made the queen frown.",
        false_start="Luna tried to splash every gloomy face away.",
        clue="the water smiled when Luna smiled at the real face above it",
        helper="a reed flute fairy",
        shared_item="a small mirror",
        careful_action="held the small mirror beside the pools while the flute fairy played one clear note",
        result="the water reflected the ceiling stars instead of the gloomy faces",
        change="the passage pools would be cleaned and filled with star-shaped lamps",
        lesson="bravery may begin with meeting a worried face kindly rather than fighting its reflection",
        ending="Stars trembled in every pool, and Luna bowed to her own brave reflection.",
    ),
    Scenario(
        id="frozen_gate",
        opening="Winter had frozen the fairy gate shut.",
        obstacle="The pass grew dim each evening, and the gate's icy frown frightened every traveler.",
        false_start="Luna pulled at the gate until her gloves tore.",
        clue="a warm breath melted one small flower-shaped patch in the ice",
        helper="a woolly mountain goat",
        shared_item="a scarlet scarf",
        careful_action="wrapped the scarlet scarf around the goat and let its warm breath soften the flower-shaped patch",
        result="the gate opened without cracking, and the path beyond remained safe",
        change="the gate would be warmed gently rather than forced open",
        lesson="bravery is patient strength guided by care",
        ending="The goat trotted through first, and Luna followed beneath a gate sparkling like glass.",
    ),
    Scenario(
        id="whispering_map",
        opening="The map to the fairy tower had lost all its ink.",
        obstacle="Only a dim passage remained on the blank parchment, and every turn seemed wrong.",
        false_start="Luna almost tore the map in two.",
        clue="the map whispered whenever she held it near the north wind",
        helper="a feathered map sprite",
        shared_item="a crumb of moon bread",
        careful_action="shared the moon bread with the map sprite and held the parchment up to the north wind",
        result="the hidden ink appeared and pointed toward the tower",
        change="maps would be stored beside an open window so their secret ink could breathe",
        lesson="bravery sometimes means waiting long enough for a quiet answer",
        ending="The tower bells rang above the hill, and the map's silver road curled safely home.",
    ),
    Scenario(
        id="riddle_door",
        opening="A door with a stone frown asked a riddle before it would open.",
        obstacle="The riddle's words echoed through a dim passage and sounded impossible to understand.",
        false_start="Luna guessed loudly and blamed the door when it stayed shut.",
        clue="the last word of the riddle matched the first mark on the floor",
        helper="a thoughtful beetle",
        shared_item="a golden pebble",
        careful_action="placed the golden pebble beside each mark while the beetle repeated the riddle slowly",
        result="the answer became clear, and the stone frown turned into a smile",
        change="all royal riddles would be spoken slowly enough for small listeners",
        lesson="bravery listens to confusion instead of pretending to know",
        ending="The door smiled in the lantern glow, and Luna entered the fairy tower with the beetle on her shoulder.",
    ),
    Scenario(
        id="silent_wolves",
        opening="Three moon wolves watched the road through the hill.",
        obstacle="They did not growl, but their silence made the dim passage feel colder.",
        false_start="Luna thought silence meant danger and reached for a stone.",
        clue="each wolf lowered its head whenever Luna lowered hers",
        helper="the youngest moon wolf",
        shared_item="a bowl of milk",
        careful_action="set down the bowl of milk and bowed beside the youngest wolf without making a sudden move",
        result="the wolves guided her through the darkness to a moonlit exit",
        change="travelers would greet the moon wolves with quiet bows and fresh milk",
        lesson="bravery can be gentle enough to make room for another creature's fear",
        ending="The wolves vanished among the stars, leaving silver pawprints beside Luna's path.",
    ),
    Scenario(
        id="rainbow_rift",
        opening="A rainbow had cracked across the fairy hill after a storm.",
        obstacle="The crack left one dim passage between the colors, and no one knew whether it would hold.",
        false_start="Luna planned to leap across before the rainbow faded.",
        clue="the colors steadied whenever a song was sung in a slow rhythm",
        helper="a humming garden fairy",
        shared_item="a green ribbon",
        careful_action="held the green ribbon with the garden fairy and sang each note before taking one careful step",
        result="the rainbow mended beneath their feet and carried them safely across",
        change="storm bridges would be crossed with a shared song and a steady pace",
        lesson="bravery is not a race toward danger; it is a rhythm that lets courage keep its balance",
        ending="The repaired rainbow arched over the hill, with Luna's green ribbon shining at its heart.",
    ),
]


NAMES = ["Luna", "Mira", "Nella", "Tessa", "Iris", "Faye"]
TRAITS = ["curious", "patient", "kind", "lively", "thoughtful", "gentle"]
DIALOGUES = [
    "What is the smallest safe step?",
    "Could the darkness be hiding a clue?",
    "Will you listen with me before we choose?",
    "What do you notice that I have missed?",
    "May we carry this worry together?",
    "What would kindness do here?",
]
REFLECTIONS = [
    "The bravest heart is not the one that never trembles, but the one that keeps caring while it trembles.",
    "A true hero does not chase away every fear; she learns which step fear is asking her to take carefully.",
    "Bravery became brighter when Luna made room for another voice.",
    "The fairies remembered that a careful question can be a lantern in a dark place.",
    "Luna discovered that courage grows when it is shared.",
]


@dataclass
class StoryParams:
    place: str
    trial: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [("moonlit_hill", "pass_dim")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fairy tale about a frown, a dim passage, and Bravery."
    )
    ap.add_argument("--place", choices=["moonlit_hill"])
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or "moonlit_hill"
    trial = args.trial or "pass_dim"
    if place not in {"moonlit_hill"}:
        raise StoryError("This fairy tale can only unfold at the moonlit hill.")
    if trial not in TRIALS:
        raise StoryError("The requested trial is not part of this storyworld.")
    gender = args.gender or "girl"
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, trial, name, gender, trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "moonlit_hill":
        raise StoryError("The moonlit hill is the only setting where the dim passage can be tested.")
    if params.trial != "pass_dim":
        raise StoryError("The only supported trial is pass-dim, the dim passage trial.")
    if not params.name.strip():
        raise StoryError("A traveler needs a name.")
    if params.trait not in TRAITS:
        raise StoryError("The traveler needs a recognized gentle trait.")


def tell(world: World, params: StoryParams) -> World:
    variant = params.seed if params.seed is not None else sum(
        (i + 1) * ord(ch)
        for i, ch in enumerate(f"{params.name}|{params.trait}|{params.gender}")
    )
    scenario = SCENARIOS[variant % len(SCENARIOS)]
    dialogue = DIALOGUES[(variant // len(SCENARIOS)) % len(DIALOGUES)]
    reflection = REFLECTIONS[
        (variant // (len(SCENARIOS) * len(DIALOGUES))) % len(REFLECTIONS)
    ]
    trial = TRIALS[params.trial]

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            label=params.name,
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type="fairy_helper",
            label=scenario.helper,
        )
    )
    gate = world.add(
        Entity(
            id="Gate",
            kind="thing",
            type="stone_gate",
            label="the stone gate",
        )
    )
    spark = world.add(
        Entity(
            id="Spark",
            kind="thing",
            type="fairy_light",
            label="the fairy light",
        )
    )

    add_meme(hero, "fear", 1.0)
    add_meme(hero, "curiosity", 1.0)
    add_meme(gate, "frown", 1.0)

    world.say(
        f"Once, beneath {world.setting.place}, {params.name}, a {params.trait} child, found a stone gate with a deep frown."
    )
    world.say(
        f"The gate guarded {trial.title}, a passage that every brave traveler hoped to cross before the moon reached its highest place."
    )
    world.say(scenario.opening)
    world.say(
        f"The fairy keeper whispered that {trial.risk}, but the kingdom needed someone to discover a safe way through."
    )
    world.para()

    add_meme(hero, "desire", 1.0)
    world.say(
        f"{params.name} wanted to pass the dim passage and earn {trial.reward}, yet her knees trembled when the gate groaned."
    )
    world.say(scenario.obstacle)
    world.say(scenario.false_start)
    add_meme(hero, "worry", 1.0)

    world.say(f'“{dialogue}” {params.name} asked {scenario.helper}.')
    world.say(
        f"{scenario.helper.capitalize()} answered, “I will look with you, but I will not choose your brave step for you.”"
    )
    world.say(
        f"{params.name} took a breath and replied, “Then let us make the next step a careful one.”"
    )
    world.para()

    add_meme(hero, "listening", 1.0)
    add_meter(hero, "sharing", 1.0)
    world.say(f"Together they noticed the clue: {scenario.clue}.")
    world.say(
        f"{params.name} shared {scenario.shared_item} with {scenario.helper}, so neither traveler had to face the dim passage alone."
    )
    world.say(f"Then {params.name} {scenario.careful_action}.")
    add_meme(hero, "bravery", 1.0)
    add_meter(hero, "safe_steps", 1.0)

    if meme(hero, "bravery") >= THRESHOLD and meter(hero, "safe_steps") >= THRESHOLD:
        add_meme(gate, "trust", 1.0)
        add_meme(hero, "confidence", 1.0)
        world.say("The stone gate's frown softened, for it recognized Bravery joined to care.")
    world.say(f"The result was wonderful: {scenario.result}.")
    add_meter(spark, "light", 1.0)
    world.para()

    add_meme(hero, "pride", 1.0)
    world.say(
        f"The fairy keeper gave {params.name} {trial.reward}, but the child asked what should change for the next traveler."
    )
    world.say(f"The kingdom adopted a new rule: {scenario.change}.")
    world.say(f"The lesson was clear: {scenario.lesson}. {reflection}")
    world.say(scenario.ending)

    world.facts.update(
        hero=hero,
        helper=helper,
        gate=gate,
        spark=spark,
        trial=trial,
        scenario=scenario,
        dialogue=dialogue,
        reflection=reflection,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(World(SETTING), params)
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
    trial = facts["trial"]
    scenario = facts["scenario"]
    return [
        f"Write a fairy tale about {hero.id} facing a frown and trying to pass-dim, the dim passage trial.",
        f"Tell a child-friendly Bravery story in which {hero.id} uses {scenario.shared_item} and a helper to cross a dangerous passage.",
        f"Write a gentle tale where a stone gate changes because {hero.id} notices this clue: {scenario.clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    trial = facts["trial"]
    scenario = facts["scenario"]
    return [
        QAItem(
            question=f"Who tried to pass the dim passage?",
            answer=f"{hero.id}, a {hero.meters and 'careful' or 'curious'} child from the moonlit hill, tried to pass the dim passage.",
        ),
        QAItem(
            question="Why did the stone gate frown?",
            answer=f"The gate guarded a risky passage, and the darkness made travelers uncertain. Its frown showed that the trial required care rather than rushing.",
        ),
        QAItem(
            question=f"What first made {hero.id} afraid?",
            answer=f"{hero.id} became afraid because {scenario.obstacle}",
        ),
        QAItem(
            question=f"What clue helped {hero.id}?",
            answer=f"The helpful clue was that {scenario.clue}. It showed {hero.id} how to choose a safer way.",
        ),
        QAItem(
            question=f"How did {hero.id} show Bravery?",
            answer=f"{hero.id} showed Bravery by {scenario.careful_action}. She kept moving carefully even while fear was present.",
        ),
        QAItem(
            question="How did the helper change the outcome?",
            answer=f"The helper shared the work with the traveler. Together they used {scenario.shared_item}, which made the careful solution possible.",
        ),
        QAItem(
            question="What changed after the trial?",
            answer=f"The passage became safer because {scenario.change}. The ending showed the change when {scenario.ending.lower()}",
        ),
        QAItem(
            question="What lesson did the fairy tale teach?",
            answer=f"It taught that {scenario.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is choosing a careful and helpful action even when something feels frightening.",
        ),
        QAItem(
            question="Why can a helper be useful?",
            answer="A helper can notice a clue, share a task, or offer support so a difficult problem can be solved safely.",
        ),
        QAItem(
            question="What is a passage?",
            answer="A passage is a path or way through a place, such as a tunnel, doorway, or narrow road.",
        ),
        QAItem(
            question="Why should someone listen before acting?",
            answer="Listening may reveal an important clue and can prevent a rushed choice from making a problem worse.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {prompt}")
    parts.append("")
    parts.append("== Story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {entity.type} {' '.join(details)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(moonlit_hill, pass_dim).
bravery_required(pass_dim).
frown(gate) :- bravery_required(pass_dim).
safe_passage(pass_dim) :- bravery_required(pass_dim).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("setting", "moonlit_hill"),
            asp.fact("trial", "pass_dim"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if py != cl:
        print(f"MISMATCH: Python={sorted(py)} ASP={sorted(cl)}")
        return 1
    for params in CURATED:
        sample = generate(params)
        if "Bravery" not in sample.story or "dim passage" not in sample.story:
            print("MISMATCH: generated story lost required narrative features")
            return 1
    print(f"OK: ASP matches Python ({len(py)} combo); generated stories passed.")
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
    StoryParams("moonlit_hill", "pass_dim", "Luna", "girl", "curious"),
    StoryParams("moonlit_hill", "pass_dim", "Mira", "girl", "patient"),
    StoryParams("moonlit_hill", "pass_dim", "Iris", "girl", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(1, args.n) and attempts < max(20, args.n * 20):
            seed = base_seed + attempts
            attempts += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
            except StoryError as exc:
                print(exc)
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
        if args.all:
            params = sample.params
            header = f"### {params.name}: {params.trial}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
