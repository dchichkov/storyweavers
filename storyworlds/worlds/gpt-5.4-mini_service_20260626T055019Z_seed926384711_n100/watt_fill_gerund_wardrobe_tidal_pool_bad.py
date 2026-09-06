#!/usr/bin/env python3
"""A diverse, child-facing space mystery StoryWorld at a tidal pool."""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_DIR) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_DIR))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "scout", "robot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the moon's tidal pool"
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Incident:
    title: str
    mission: str
    warning: str
    clue: str
    mistaken_plan: str
    cause: str
    safe_action: str
    outcome: str
    final_image: str
    affected: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.trace = list(self.trace)
        return clone


SETTING = Setting(
    place="the moon's tidal pool",
    affords={"observe_from_path", "share", "report", "repair_gear"},
)

INCIDENTS = [
    Incident(
        "shadowed gauge",
        "record how many watts reached the west marker",
        "the gauge fell from twelve watts to four whenever a silver cloud passed",
        "a crescent shadow crossed the wardrobe's solar patch",
        "drag the locker onto the barnacle shelf for more light",
        "a folded emergency cape was covering half the solar patch",
        "unfold the cape on the dry platform and angle the locker without touching the pool",
        "the gauge recovered, but the delayed survey missed the only calm tide",
        "Four quiet watts glowed beside a blank survey square as the tide covered the marker",
        "the west marker reading",
    ),
    Incident(
        "salt bridge",
        "fill the beacon's reserve meter before moonset",
        "blue sparks ticked between two damp charging pins",
        "a thin white salt line joined the pins beneath the wardrobe",
        "wipe the pins quickly with a sleeve",
        "spray had dried into a salty bridge that leaked power",
        "switch off the circuit and let the captain clean it with the approved dry kit",
        "the leak stopped, yet the reserve had already emptied below restart level",
        "The clean pins shone while the powerless beacon reflected one red star",
        "the beacon reserve",
    ),
    Incident(
        "borrowed heater",
        "count the watts used by the nursery tank's warming pad",
        "the wardrobe cable felt warm although its lamps were off",
        "a second cable disappeared behind a labeled specimen case",
        "open the case beside the water to trace the cable",
        "a visiting robot had plugged its boot heater into the wardrobe outlet",
        "ask the robot to unplug it and move the sealed case to the dry study bench",
        "the heater was returned, but the chilled nursery tank had to remain closed for the night",
        "Tiny safe bubbles rose behind the closed glass while the unused heater cooled",
        "the nursery tank schedule",
    ),
    Incident(
        "sand-filled vent",
        "test whether the signal lamp could fill the cove with a guide beam",
        "the lamp hummed and its watt display blinked amber",
        "dry moon sand trembled in the wardrobe's cooling grille",
        "blow hard through the grille toward the tidal pool",
        "a torn pocket had spilled sand across the fan intake",
        "power down the locker and use the little vacuum on the dry boardwalk",
        "the fan turned freely, but its safety fuse had failed and no spare remained",
        "The cleaned grille faced the dark cove, silent under a row of footprints",
        "the signal lamp",
    ),
    Incident(
        "crab's reflection",
        "map a wandering flash that seemed to steal one watt at a time",
        "a bright dot moved whenever a shore crab moved below",
        "the dot matched the polished buckle hanging inside the open wardrobe",
        "follow the crab across the rocks to catch the moving light",
        "the buckle was reflecting the beacon sensor back into itself",
        "stay on the marked path, close the wardrobe, and observe the crab without disturbing it",
        "the false readings ended, but the corrupted map could not be rebuilt before departure",
        "A small crab crossed an untouched pool while the crew rolled up an empty map",
        "the beacon map",
    ),
    Incident(
        "stuck refill float",
        "fill a sealed rinse bottle for cleaning spacesuit visors",
        "the refill pump drew six watts but the bottle stayed empty",
        "the wardrobe's float lever was pinned beneath a loose glove strap",
        "pull the strap while the pump was still running",
        "the trapped float falsely told the pump that the bottle was full",
        "turn off the pump, free the strap on the dry mat, and restart one careful cycle",
        "water finally flowed, but the cracked bottle cap let the clean supply drain into its catch tray",
        "One drop hung from the cap above a tray that was full when the bottle was not",
        "the visor-rinse supply",
    ),
    Incident(
        "echoing counter",
        "learn why the watt counter added every pulse twice",
        "each soft ping returned as a second ping from the wardrobe door",
        "a shiny ration tin sat directly opposite the sound sensor",
        "toss the tin into the pool so it could not echo",
        "the tin's flat lid was bouncing the test pulse back at the sensor",
        "move the tin into a padded reuse bin and repeat the test from the boardwalk",
        "the count became honest, but earlier double readings had exhausted the test battery",
        "The padded tin made no echo as the counter settled at zero watts",
        "the test battery",
    ),
    Incident(
        "glowing algae alarm",
        "check an alarm that flashed whenever the tide rose",
        "green light flickered below the walkway while the panel reported a watt surge",
        "the flashes followed harmless glowing algae rather than the power wire",
        "scoop up the algae to stop the alarm",
        "the optical sensor had mistaken natural glow for its own status lamp",
        "leave the algae where it lived and fit the sensor's amber shield from the wardrobe",
        "the alarm quieted, but its wet memory module had already lost the night's records",
        "Green algae shimmered undisturbed beneath a shielded and forgetful alarm",
        "the tide records",
    ),
    Incident(
        "knotted suit sleeve",
        "send five watts through the wardrobe's suit-drying rail",
        "the rail clicked off each time its door began closing",
        "a knotted sleeve pressed the door's safety switch",
        "force the door shut and hold it there",
        "the bulky knot made the locker correctly refuse to run",
        "open the door, unknot and hang the sleeve, then test the empty rail",
        "the rail worked, but the suit stayed damp and the morning walk was canceled",
        "The smooth sleeve dripped into its tray beside a crossed-out walking badge",
        "the morning moon walk",
    ),
    Incident(
        "misread label",
        "find which socket should fill the scout radio with power",
        "one label said RETURN while another said RESERVE",
        "a curled corner hid the first three letters on the wardrobe diagram",
        "try every socket until the radio lit",
        "the crew had mistaken the return-data port for the reserve-power port",
        "flatten the diagram under its clear cover and match shapes before connecting anything",
        "the correct socket was found, but the radio's one launch window had passed",
        "The neat diagram rested beside a charged radio carrying no message",
        "the launch message",
    ),
    Incident(
        "moon-moth visitor",
        "measure a tiny nightly dip in the wardrobe's watt supply",
        "a fuzzy shadow appeared behind the warm status light",
        "a moon moth rested safely outside the sealed lamp cover",
        "tap the cover until the moth flew away",
        "the harmless visitor shaded the light sensor and triggered needless brightening",
        "dim the lamp, wait quietly on the path, and let the moth leave by itself",
        "the moth departed, but repeated brightening had worn out the old lamp",
        "The moon moth sailed over an untouched pool as the lamp gave its last pale blink",
        "the old status lamp",
    ),
    Incident(
        "uneven cargo",
        "fill the wardrobe's lower rack with shared field kits",
        "its level sensor demanded eight watts even after the rack looked full",
        "three heavy kits leaned against only one side of the shelf",
        "pile the remaining kits on top to press the sensor harder",
        "the uneven load left the opposite balance pad untouched",
        "unplug the rack and share the kits evenly across both marked pads",
        "the sensor approved the load, but a bent wheel kept the wardrobe from joining the expedition",
        "Balanced kits waited behind a closed door while one crooked wheel pointed home",
        "the field expedition",
    ),
]

OPENINGS = [
    "At low tide, {name} and Captain {partner} followed the raised boardwalk to {place}.",
    "The moon was setting when junior scout {name} met Captain {partner} above {place}.",
    "From a dry lookout over {place}, {name} and Captain {partner} began the night's equipment check.",
    "A station bell chimed once as {name} and Captain {partner} reached the marked path beside {place}.",
    "Silver water glittered below the rail when scout {name} reported to Captain {partner} at {place}.",
    "Before the tide returned, {name} and Captain {partner} carried their checklist along the safe edge of {place}.",
    "Under a violet sky, scout {name} joined Captain {partner} on the observation deck over {place}.",
    "The quiet shift at {place} began with {name}, Captain {partner}, and one humming wardrobe locker.",
    "A weak beacon guided {name} and Captain {partner} to the fenced study platform above {place}.",
    "With boots on the boardwalk and hands off the wildlife, {name} and Captain {partner} surveyed {place}.",
]

THOUGHTS = [
    '"A clue is useful only if we test it," {name} said.',
    '"Let us explain the change before we touch anything," said {name}.',
    '{name} whispered, "The first idea may not be the safest one."',
    '"We can solve this without moving a single pool creature," {name} decided.',
    '{name} studied the readings. "Evidence first, tools second," the scout said.',
    '"Slow looking can prevent a fast mistake," {name} reminded the captain.',
    '{name} pointed to the rail. "We stay up here and let the clue come to us."',
    '"One watt can tell a whole story when its changes repeat," {name} observed.',
]

BAD_END_LINKS = [
    "Their careful choice prevented a worse problem, yet it could not restore what had already been lost.",
    "They had solved the mystery responsibly, but solving it did not turn back the clock.",
    "The truth arrived in time to protect the pool, though not in time to save the mission.",
    "Nothing in the habitat was harmed; even so, the expedition ended with a real disappointment.",
    "The repair made tomorrow safer, while tonight's opportunity quietly disappeared.",
    "They could be proud of their method and still feel sad about the result.",
]

GIRL_NAMES = ["Mira", "Nia", "Luna", "Tess"]
BOY_NAMES = ["Jace", "Oren", "Pax", "Finn"]


@dataclass
class StoryParams:
    name: str
    gender: str
    partner: str
    seed: Optional[int] = None


def _add_meter(entity: Entity, key: str, amount: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def _add_meme(entity: Entity, key: str, amount: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell_story(world: World, scout: Entity, captain: Entity, incident: Incident, route: int) -> None:
    wardrobe = world.add(
        Entity(
            id="wardrobe",
            label="wardrobe locker",
            phrase="a sealed white wardrobe locker with a watt display",
        )
    )
    route_rng = random.Random((world.facts["seed"] * 104729) + route)
    world.say(
        OPENINGS[route % len(OPENINGS)].format(
            name=scout.id, partner=captain.id, place=world.setting.place
        )
    )
    world.say(
        "The locker held shared suits and instruments; its screen measured power in watts, and its refill control used the word fill."
    )
    world.say(
        f"Tonight their mission was to {incident.mission}. They called the job investigating: an -ing word used as a noun, which their grammar guide called a gerund."
    )
    world.say(f"Their checklist named this the {incident.title} mystery.")

    world.para()
    world.say(f"The first sign of trouble was plain: {incident.warning}.")
    world.say(f"Looking from the boardwalk, they noticed that {incident.clue}.")
    world.say(THOUGHTS[route % len(THOUGHTS)].format(name=scout.id))
    world.say(
        f"For one worried moment, {scout.id} wanted to {incident.mistaken_plan}. Captain {captain.id} asked what that choice might disturb or damage."
    )

    world.para()
    evidence_steps = [
        "They compared the display before and after the warning.",
        "They marked the changing reading on a slate instead of guessing.",
        "They watched one full tide pulse from behind the rail.",
        "They checked the equipment diagram and then repeated the observation.",
        "They shared the lamp, meter, and checklist so each reading had a witness.",
        "They photographed the clue from the dry platform and enlarged it on the console.",
    ]
    world.say(evidence_steps[route_rng.randrange(len(evidence_steps))])
    world.say(f"That test revealed the cause: {incident.cause}.")
    world.say(
        f'"Then our responsible next step is to {incident.safe_action}," said Captain {captain.id}. They did exactly that, leaving shells, plants, animals, and pool water where they belonged.'
    )
    _add_meter(wardrobe, "watts_checked", float((route % 9) + 4))
    _add_meme(scout, "curiosity", 1.0)
    _add_meme(scout, "responsibility", 1.0)
    _add_meme(captain, "sharing", 1.0)

    world.para()
    world.say(incident.outcome.capitalize() + ".")
    world.say(BAD_END_LINKS[route % len(BAD_END_LINKS)])
    world.say(
        f"It was a bad ending for {incident.affected}, not a cruel one: everyone was safe, and the tidal pool remained untouched."
    )
    world.say(incident.final_image + ".")

    world.facts.update(
        scout=scout,
        captain=captain,
        wardrobe=wardrobe,
        incident=incident,
        clue=incident.clue,
        cause=incident.cause,
        action=incident.safe_action,
        affected=incident.affected,
        bad_end=True,
        habitat_safe=True,
    )
    world.trace.extend(
        [
            f"observe:{incident.title}",
            f"infer:{incident.cause}",
            f"act:{incident.safe_action}",
            f"outcome:{incident.affected}",
        ]
    )


def valid_name_gender(name: str, gender: str) -> bool:
    return name in (GIRL_NAMES if gender == "girl" else BOY_NAMES)


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    scout = facts["scout"]
    captain = facts["captain"]
    incident = facts["incident"]
    return [
        f"Write a child-facing space mystery about {scout.id} and Captain {captain.id} investigating the {incident.title} mystery at a tidal pool.",
        f"Tell how a watt clue reveals that {incident.cause}, and show the crew choosing to {incident.safe_action}.",
        'Write a responsible tidal-pool story using "watt," "fill," "gerund," and "wardrobe," with a non-cruel bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    scout = facts["scout"]
    captain = facts["captain"]
    incident = facts["incident"]
    return [
        QAItem(
            question=f"What mission did {scout.id} and Captain {captain.id} attempt?",
            answer=f"They attempted to {incident.mission} from the safe platform above the tidal pool.",
        ),
        QAItem(
            question=f"What clue helped {scout.id} solve the {incident.title} mystery?",
            answer=f"The useful clue was that {incident.clue}. It pointed away from the scout's first guess.",
        ),
        QAItem(
            question="What was actually causing the unusual watt reading?",
            answer=f"The crew discovered that {incident.cause}. Their observation and repeated test supported that explanation.",
        ),
        QAItem(
            question="How did the crew respond without harming the tidal pool?",
            answer=f"They chose to {incident.safe_action}. They stayed on the marked dry area and left the habitat undisturbed.",
        ),
        QAItem(
            question="Why was the ending bad but not cruel?",
            answer=f"The crew lost {incident.affected}, but nobody was hurt and the tidal pool remained safe. The disappointment followed from the earlier delay or damage, not from punishment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a watt?",
            answer="A watt is a unit used to measure power, such as the power used by a lamp or machine.",
        ),
        QAItem(
            question="What is a gerund?",
            answer='A gerund is an -ing form used as a noun. In "Investigating takes patience," investigating is a gerund.',
        ),
        QAItem(
            question="How should visitors behave around a tidal pool?",
            answer="Visitors should stay on permitted paths, observe gently, and leave water, rocks, plants, shells, and animals where they are.",
        ),
        QAItem(
            question="What is a wardrobe?",
            answer="A wardrobe is a cupboard or locker used to store clothes or other gear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== world knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", *[f"  {item}" for item in world.trace]]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: label={entity.label!r} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(tidal_pool).
valid_story(Name, Gender) :- name(Name), gender(Gender), wears(Name, Gender).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("setting", "tidal_pool")]
    for name in GIRL_NAMES:
        lines.extend(
            [asp.fact("name", name), asp.fact("gender", "girl"), asp.fact("wears", name, "girl")]
        )
    for name in BOY_NAMES:
        lines.extend(
            [asp.fact("name", name), asp.fact("gender", "boy"), asp.fact("wears", name, "boy")]
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_names() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_names())
    python_set = {(name, "girl") for name in GIRL_NAMES} | {
        (name, "boy") for name in BOY_NAMES
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} names).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Space mystery StoryWorld at a tidal pool.")
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--partner")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name and not valid_name_gender(args.name, gender):
        raise StoryError("The chosen name does not match the chosen gender for this storyworld.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice(
        [candidate for candidate in GIRL_NAMES + BOY_NAMES if candidate != name]
    )
    return StoryParams(name=name, gender=gender, partner=partner)


def generate(params: StoryParams) -> StorySample:
    seed = params.seed if params.seed is not None else 0
    world = World(SETTING)
    world.facts["seed"] = seed
    scout = world.add(Entity(id=params.name, kind="character", type=params.gender))
    captain_type = "captain" if params.partner in GIRL_NAMES else "man"
    captain = world.add(Entity(id=params.partner, kind="character", type=captain_type))
    incident = INCIDENTS[seed % len(INCIDENTS)]
    route = (seed // len(INCIDENTS)) % 120
    tell_story(world, scout, captain, incident, route)
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mira", gender="girl", partner="Jace", seed=0),
        StoryParams(name="Nia", gender="girl", partner="Finn", seed=5),
        StoryParams(name="Pax", gender="boy", partner="Luna", seed=10),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_names())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in _curated()]
    else:
        samples = []
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

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
