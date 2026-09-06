#!/usr/bin/env python3
"""
Story world: a tiny space-adventure about a banner, a transformation, and a
lesson learned.

A child on a small ship wants to celebrate a big star crossing with a banner.
The banner cannot stay put in space until the crew changes it into a proper
mission banner with clips and glow tape, and the child learns to plan for the
vacuum instead of fighting it.
"""

from __future__ import annotations

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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Ship:
    name: str
    deck: str = "the bright observation deck"
    outside: str = "the airlock window"
    space: str = "the quiet dark of space"


@dataclass
class StoryParams:
    ship: str = "Comet Lantern"
    hero_name: str = "Milo"
    helper_name: str = "Ari"
    mission: str = "comet festival"
    incident: str = "static"
    telling_mode: str = "mission log"
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SHIP_REGISTRY = {
    "Comet Lantern": Ship(name="Comet Lantern"),
    "Star Finch": Ship(name="Star Finch"),
    "Aurora Kite": Ship(name="Aurora Kite"),
}

HERO_NAMES = ["Milo", "Nia", "Tao", "Luna", "Remy"]
HELPER_NAMES = ["Ari", "Zia", "Juno", "Pax", "Kira"]

MISSIONS = [
    "comet festival",
    "new-crew welcome",
    "seedling-hatch celebration",
    "homeworld message day",
    "meteor-watch night",
    "rescue-drill graduation",
]

TELLING_MODES = [
    "mission log",
    "dialogue opening",
    "mystery opening",
    "countdown opening",
    "quiet reflection",
    "helper viewpoint",
    "problem first",
    "celebration first",
]

INCIDENTS = {
    "static": {
        "premise": "Silver letters kept lifting from the cloth and clinging to the observation window.",
        "mistake": "At first, {hero} pressed every letter down with a mitten, but each touch charged the cloth again.",
        "clue": "A loose thread jumped toward {helper}'s comb, revealing that static charge was tugging at the paint.",
        "change": "They replaced the loose letters with stitched patches and added a grounding tab approved for the cabin.",
        "result": "The words stayed readable without scraps drifting toward the air vents.",
        "lesson": "test unfamiliar materials before decorating near ship equipment",
        "ending": "Beyond the glass, a blue spark of comet dust crossed behind the steady silver letters.",
    },
    "vent": {
        "premise": "The banner sagged across a return vent, and the cabin fan began to hum too hard.",
        "mistake": "{hero} tried shortening one ribbon, which only pulled the other corner across the grille.",
        "clue": "{helper} floated a paper thread nearby and watched it point straight toward the blocked airflow.",
        "change": "They trimmed the cloth into narrow pennants and mounted them on a rigid frame clear of the vent.",
        "result": "Fresh air moved freely while every pennant remained visible.",
        "lesson": "celebrations must leave safety equipment clear",
        "ending": "The fan settled to a whisper as six bright pennants pointed toward the stars.",
    },
    "microgravity": {
        "premise": "During a brief weightless practice, the banner folded around {hero}'s helmet like a floppy curtain.",
        "mistake": "{hero} added heavier tassels, forgetting that weight would not pull them down in microgravity.",
        "clue": "A checklist card stayed flat because magnets held all four of its corners.",
        "change": "They stretched the cloth over a light hoop and secured each edge with cabin-safe magnetic tabs.",
        "result": "The transformed banner held its shape even when the crew floated past it.",
        "lesson": "design for how objects actually move in their surroundings",
        "ending": "The round banner hovered like a small moon while the crew made one slow victory loop beneath it.",
    },
    "glare": {
        "premise": "Sunlight flashed from the metallic paint and hid the navigation display in the window's reflection.",
        "mistake": "{hero} turned the banner sideways, but the glare merely jumped onto another screen.",
        "clue": "{helper} held up a matte checklist and noticed that its dark ink made no troublesome reflection.",
        "change": "They covered the shiny paint with soft fabric symbols and moved the banner to a marked display rail.",
        "result": "The crew could read both the banner and every navigation number.",
        "lesson": "a beautiful design should never hide information people need",
        "ending": "A real sunrise filled the glass, and the matte stars on the banner stayed gently gold.",
    },
    "condensation": {
        "premise": "Near the seedling hatch, tiny beads of moisture blurred the banner's painted message.",
        "mistake": "{hero} wiped the letters with a sleeve, spreading silver streaks across the cloth.",
        "clue": "Drops gathered only beside the humid hatch, while a label farther down the corridor stayed dry.",
        "change": "They moved the display and remade its message with washable thread on moisture-safe fabric.",
        "result": "The seedlings kept their humid air, and the greeting remained crisp.",
        "lesson": "observe where a problem happens before choosing a repair",
        "ending": "A new leaf opened behind the hatch while the dry green letters welcomed it.",
    },
    "translation": {
        "premise": "The welcome banner used one huge word that the ship's newest families could not all read.",
        "mistake": "{hero} planned to make that same word bigger, assuming size would solve the problem.",
        "clue": "{helper} asked three crew members what they understood, and each pointed to the pictures instead.",
        "change": "They transformed the banner into a ring of greetings, tactile stars, and clear pictures contributed by the crew.",
        "result": "Everyone found a greeting or symbol they could understand.",
        "lesson": "ask the people who will use something what helps them belong",
        "ending": "Hands traced the raised stars as greetings circled the cabin in many voices.",
    },
    "tear": {
        "premise": "A training cart brushed the banner, opening a small tear that crept toward its painted planet.",
        "mistake": "{hero} pulled the cloth straight to inspect it, making the split grow another finger-width.",
        "clue": "{helper} showed how a patch on a cargo pouch spread strain around an old cut.",
        "change": "They stopped the tear with rounded stitches and turned the repair patches into a constellation.",
        "result": "The damaged corner became the strongest and most admired part of the banner.",
        "lesson": "pause and understand damage before pulling or patching",
        "ending": "The new stitched constellation framed Earth as a blue bead in the window.",
    },
    "alarm": {
        "premise": "A dangling red streamer looked so much like an emergency marker that two crew members stopped in alarm.",
        "mistake": "{hero} suggested adding a note beneath it, though the note could not be seen from the far corridor.",
        "clue": "{helper} compared it with the ship's safety chart and found the same color and triangle shape.",
        "change": "They recut the banner into curved violet waves and reserved red triangles for real warnings.",
        "result": "No one confused the celebration with an emergency signal again.",
        "lesson": "shared safety symbols must stay clear and unmistakable",
        "ending": "Violet waves rippled above the party while every red safety marker remained easy to spot.",
    },
    "noise": {
        "premise": "Hard clips tapped the wall whenever the ship adjusted course, spoiling the sleeping crew's quiet.",
        "mistake": "{hero} wedged the clips tighter, which made each tap sharper.",
        "clue": "A padded tool pouch beside the banner stayed silent through the next small turn.",
        "change": "They fitted soft loops, fabric-covered fasteners, and a tension cord to the banner's edge.",
        "result": "The mission banner remained firm without knocking against the wall.",
        "lesson": "a solution should be tested for effects on other people",
        "ending": "The banner glowed silently as a sleepy crewmate drifted past with a grateful wave.",
    },
    "countdown": {
        "premise": "With twelve minutes until the meteor watch, the enormous banner still covered half the viewing glass.",
        "mistake": "{hero} rushed to hang it anyway, believing a bigger display would make a bigger celebration.",
        "clue": "{helper} marked the clear viewing boundary shown on the observation-deck plan.",
        "change": "They folded the cloth into a compact starburst and clipped it beside, not across, the window.",
        "result": "The whole crew could see the meteor trail and the transformed banner together.",
        "lesson": "the purpose of a celebration matters more than making its decorations large",
        "ending": "Twelve meteors scratched white lines across the glass beside the little starburst.",
    },
    "memory": {
        "premise": "The banner listed famous captains but left no room for the cooks, cleaners, gardeners, and mechanics.",
        "mistake": "{hero} proposed squeezing in smaller names, which would still make many contributions seem small.",
        "clue": "{helper} opened the mission log and found that every safe voyage depended on dozens of different jobs.",
        "change": "They transformed the cloth into linked handprints, with each print naming one useful act.",
        "result": "Every crew member could add a contribution without anyone taking the center place.",
        "lesson": "honor teamwork by noticing quiet contributions as well as famous ones",
        "ending": "A ring of handprints surrounded the ship emblem while the night crew added the final print.",
    },
    "power": {
        "premise": "The banner's old light cord drew power from an outlet reserved for science instruments.",
        "mistake": "{hero} thought one brief celebration could not matter, but the power display dipped when the lights came on.",
        "clue": "{helper} traced the labeled cable to the instrument circuit and checked its yellow reserve warning.",
        "change": "They removed the cord and stitched the banner with reflective thread that needed no electricity.",
        "result": "The science instruments kept full power, and cabin lamps made the new symbols gleam.",
        "lesson": "check which resources a plan uses before switching it on",
        "ending": "The powerless banner flashed softly when a distant planet rolled into view.",
    },
}

ASP_RULES = r"""
ship(S) :- ship_name(S).
banner(B) :- banner_name(B).
lesson(L) :- lesson_name(L).
transformed(B) :- banner_state(B, transformed).
ready(B) :- banner_state(B, ready).
lesson_learned(H) :- hero(H), learned(H).
safe_hang(B) :- ready(B), clipped(B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ship_name in SHIP_REGISTRY:
        lines.append(asp.fact("ship_name", ship_name))
    lines.append(asp.fact("banner_name", "mission_banner"))
    lines.append(asp.fact("lesson_name", "use_space_tools"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("banner_state", "mission_banner", "plain"))
    lines.append(asp.fact("banner_state", "mission_banner", "transformed"))
    lines.append(asp.fact("banner_state", "mission_banner", "ready"))
    lines.append(asp.fact("clipped", "mission_banner"))
    lines.append(asp.fact("learned", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show safe_hang/1.\n#show lesson_learned/1.\n#show transformed/1."))
    atoms = set((sym.name, tuple(a.string if a.type == a.type.String else a.number if a.type == a.type.Number else a.name for a in sym.arguments)) for sym in model)
    want = {("safe_hang", ("mission_banner",)), ("lesson_learned", ("hero",)), ("transformed", ("mission_banner",))}
    if atoms == want:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(want))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure story world about a banner and a lesson learned.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    ship = args.ship or rng.choice(list(SHIP_REGISTRY))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != name])
    if helper == name:
        raise StoryError("The helper should be a different crew member from the hero.")
    return StoryParams(
        ship=ship,
        hero_name=name,
        helper_name=helper,
        mission=rng.choice(MISSIONS),
        incident=rng.choice(list(INCIDENTS)),
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    ship = SHIP_REGISTRY[params.ship]
    world = World(ship)
    if params.incident not in INCIDENTS:
        raise StoryError(f"Unknown incident: {params.incident}")
    incident = INCIDENTS[params.incident]
    rng = random.Random(params.seed if params.seed is not None else f"{params.ship}:{params.hero_name}:{params.helper_name}:{params.incident}")

    hero = world.add(Entity(id="hero", kind="character", label=params.hero_name, type="child"))
    helper = world.add(Entity(id="helper", kind="character", label=params.helper_name, type="crew"))
    banner = world.add(Entity(
        id="banner",
        kind="thing",
        label="banner",
        phrase=rng.choice([
            "a long celebration banner with silver paint",
            "a folded cloth banner painted with little planets",
            "a bright cabin banner edged with silver thread",
            "a wide festival banner covered in hand-painted stars",
        ]),
        type="banner",
        owner=hero.id,
        meters={"flutter": 0.0, "tear": 0.0, "glow": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "pride": 0.0},
    ))

    openings = {
        "mission log": f"The mission log of {ship.name} began with an unusual job: prepare the cabin for the {params.mission}.",
        "dialogue opening": f'“Will everyone see it?” {params.hero_name} asked aboard {ship.name}, lifting {banner.phrase}.',
        "mystery opening": f"Something was wrong with the decorations aboard {ship.name}, though at first {params.hero_name} could not see what.",
        "countdown opening": f"The {params.mission} would begin soon aboard {ship.name}, and {params.hero_name} still had one important job.",
        "quiet reflection": f"Stars rested beyond the windows of {ship.name} while {params.hero_name} unfolded {banner.phrase}.",
        "helper viewpoint": f"From across {ship.deck}, {params.helper_name} saw {params.hero_name} studying {banner.phrase}.",
        "problem first": incident["premise"].format(hero=params.hero_name, helper=params.helper_name),
        "celebration first": f"Music for the {params.mission} had begun when {params.hero_name} carried a banner onto {ship.deck}.",
    }
    world.say(openings[params.telling_mode])
    world.say(rng.choice([
        "What began as a decorating job was becoming a careful space adventure inside the spacecraft cabin.",
        "Their small space adventure would require observation as well as imagination aboard the spacecraft.",
        "On this space adventure, even a piece of cloth had to work safely with the spacecraft around it.",
        "The spacecraft was their home, so their space adventure began with caring for everyone who shared it.",
        "A good space adventure, they were about to discover, could begin with one puzzling cabin detail.",
        "This was a quiet sort of space adventure: understand the spacecraft, then improve what did not fit.",
        "The banner turned an ordinary spacecraft chore into a space adventure with a real mystery to solve.",
        "Before the celebration could begin, a practical space adventure unfolded aboard the spacecraft.",
    ]))
    if params.telling_mode != "problem first":
        world.say(f"The banner was meant to brighten the {params.mission} from a safe display rail beside {ship.outside}, inside the cabin.")
        world.say(incident["premise"].format(hero=params.hero_name, helper=params.helper_name))
    else:
        world.say(f"It happened while {params.hero_name} prepared {banner.phrase} for the {params.mission} aboard {ship.name}.")

    banner.meters["flutter"] += 1.0
    banner.meters["tear"] += 1.0
    banner.memes["worry"] += 1.0
    hero.memes["disappointment"] = 1.0
    world.say(incident["mistake"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(rng.choice([
        f'“Let us gather evidence before we change anything else,” {params.helper_name} said.',
        f'“A banner is part of the ship while it is hanging here,” {params.helper_name} reminded {params.hero_name}. “Let us learn what the ship needs.”',
        f'{params.helper_name} stopped the next hurried attempt. “We can turn this mistake into a clue.”',
        f'“What changed, and where?” {params.helper_name} asked. {params.hero_name} took a slow breath and looked again.',
    ]))
    world.say(rng.choice([
        f"{params.hero_name} described what had happened while {params.helper_name} wrote each observation on a slate.",
        f"They compared the troubled banner with an object nearby that was working properly.",
        f"Instead of guessing again, they watched through one full course adjustment.",
        f"{params.helper_name} checked the display guide while {params.hero_name} marked the exact place where the trouble began.",
        f"They agreed that neither of them would touch ship equipment; their job was to observe and redesign the decoration.",
        f"First they named what they knew, what they only suspected, and what they still needed to test.",
        f"{params.hero_name} sketched the problem from two angles, and {params.helper_name} checked the sketch against the cabin.",
        f"They asked a crew member responsible for the deck which parts of the area had to remain unchanged.",
        f"For their next test, they changed only one small thing so they could tell what made the difference.",
        f"They listened, looked, and checked the ship's labels before choosing another action.",
        f"{params.helper_name} guarded the work area while {params.hero_name} followed the evidence step by step.",
        f"Together they made a rule: the transformed banner must solve the problem without creating a new one.",
    ]))
    world.say(incident["clue"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(f"Together they carried the banner to the work table on {ship.deck} and checked the ship's display guide.")

    # Transformation
    banner.label = "mission banner"
    banner.phrase = "a transformed mission banner made for its place aboard the ship"
    banner.meters["tear"] = 0.0
    banner.meters["flutter"] = 0.0
    banner.meters["glow"] = 1.0
    banner.memes["pride"] += 1.0
    hero.memes["hope"] = 1.0
    hero.memes["lesson"] = 1.0
    world.say(incident["change"].format(hero=params.hero_name, helper=params.helper_name))
    world.say(f"What had been an unsuitable decoration became {banner.phrase}.")
    world.say(incident["result"].format(hero=params.hero_name, helper=params.helper_name))

    # Lesson learned
    reflections = [
        f'{params.hero_name} named the lesson learned: “{incident["lesson"].capitalize()}.”',
        f"The lesson learned by {params.hero_name} was simple: {incident['lesson']}.",
        f"Looking at their careful work, {params.hero_name} understood the lesson learned from the mistake: {incident['lesson']}.",
        f'{params.hero_name} recorded the lesson learned in the mission log: “{incident["lesson"].capitalize()}.”',
    ]
    world.say(rng.choice(reflections))
    world.say(rng.choice([
        f"Then {params.hero_name} and {params.helper_name} fastened the mission banner to its approved rail.",
        f"After one final safety check, the two friends opened the cabin doors for the celebration.",
        f"When the crew arrived, {params.hero_name} pointed out the clue that had guided their transformation.",
        f"The transformed banner was ready before the first celebration chime sounded.",
    ]))
    world.say(incident["ending"].format(hero=params.hero_name, helper=params.helper_name))

    world.facts.update(
        hero=hero,
        helper=helper,
        banner=banner,
        ship=ship,
        transformed=True,
        lesson=True,
        mission=params.mission,
        incident=params.incident,
        clue=incident["clue"].format(hero=params.hero_name, helper=params.helper_name),
        transformation=incident["change"].format(hero=params.hero_name, helper=params.helper_name),
        lesson_text=incident["lesson"],
        result=incident["result"].format(hero=params.hero_name, helper=params.helper_name),
    )

    prompts = [
        f"Write a gentle space adventure about {params.hero_name} preparing a banner for the {params.mission} aboard {ship.name}.",
        f"Tell how {params.hero_name} and {params.helper_name} use the clue '{incident['clue'].format(hero=params.hero_name, helper=params.helper_name)}' to transform a banner safely.",
        f"Write a child-facing story in a {params.telling_mode} style with a real problem, a causal transformation, and this lesson: {incident['lesson']}.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem interrupted the {params.mission} preparations?",
            answer=incident["premise"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question=f"What clue helped {params.hero_name} and {params.helper_name} understand the problem?",
            answer=incident["clue"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question="How did the crew transform the banner?",
            answer=incident["change"].format(hero=params.hero_name, helper=params.helper_name),
        ),
        QAItem(
            question=f"What lesson did {params.hero_name} learn from the adventure?",
            answer=f"{params.hero_name} learned this lesson: {incident['lesson']}.",
        ),
        QAItem(
            question="What proved that the transformed banner worked?",
            answer=incident["result"].format(hero=params.hero_name, helper=params.helper_name),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a banner?",
            answer="A banner is a long piece of cloth or paper with words or decorations on it, often used for celebrations.",
        ),
        QAItem(
            question="Why do things need clips in space?",
            answer="Inside a spacecraft cabin, clips keep loose objects from drifting during weightless periods or shifting when the ship moves.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful thing someone understands after trying, making a mistake, and then choosing a better way.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, ent in sample.world.entities.items():
            print(f"{key}: {ent.label} meters={ent.meters} memes={ent.memes}")
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_hang/1.\n#show lesson_learned/1.\n#show transformed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for ship_name in SHIP_REGISTRY:
            params = StoryParams(ship=ship_name, hero_name=HERO_NAMES[0], helper_name=HELPER_NAMES[0])
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
