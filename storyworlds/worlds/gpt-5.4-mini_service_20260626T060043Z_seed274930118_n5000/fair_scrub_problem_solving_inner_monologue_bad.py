#!/usr/bin/env python3
"""A child-safe fairground mystery about scrubbing, reasoning, and setbacks."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Place:
    name: str
    noise: str
    suspects: tuple[str, ...]


@dataclass(frozen=True)
class Incident:
    key: str
    area: str
    disturbance: str
    first_clue: str
    false_guess: str
    test: str
    second_clue: str
    cause: str
    safe_plan: str
    bad_result: str
    final_image: str
    lesson: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Mina"
    hero_type: str = "girl"
    helper: str = "Aunt June"
    suspect: str = "the clown"
    missing: str = "ticket booklet"
    place: str = "fair"
    mood: str = "windy"
    incident: str = "soap_bubbles"
    narrative_mode: int = 0
    thought_mode: int = 0
    dialogue_mode: int = 0
    turn_mode: int = 0


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


FAIRS = {
    "fair": Place(
        name="the fair",
        noise="bells, laughter, and carousel music",
        suspects=("the clown", "the prize seller", "the balloon twister"),
    )
}

MISSING_ITEMS = {
    "ticket booklet": "small red ticket booklet",
    "blue ribbon": "blue ribbon with a silver star",
    "toy fox": "soft toy fox with a green scarf",
}

HERO_TYPES = {"Mina": "girl", "Nico": "boy", "Tess": "girl", "Owen": "boy"}

INCIDENTS = {
    incident.key: incident
    for incident in (
        Incident(
            "soap_bubbles", "carousel gate",
            "a bucket of gray rinse water stood beside a freshly scrubbed rail",
            "a chain of soap bubbles drifted toward the carousel",
            "the bubbles followed the balloon twister",
            "compare their landing places with the direction of the breeze",
            "clean water marks ended beneath the rail, opposite the balloon stall",
            "a gust had slid the missing item under the rail before the cleaner arrived",
            "ask the attendant to stop the gate while the adult helper uses a litter grabber",
            "the grabber nudges it into the locked machinery enclosure until morning",
            "one bright corner remains visible beyond the gate as the last carousel horse goes dark",
            "A moving clue may point with the wind instead of toward a culprit.",
        ),
        Incident(
            "painted_bench", "picnic row",
            "a custodian was scrubbing washable paint from a bench after the craft show",
            "three blue streaks crossed the damp paving stones",
            "the marks came from the prize seller's cart",
            "compare the width of each streak with the wheels from behind the safety rope",
            "the wheels were narrow, while a wide cleaning brush made every streak",
            "the brush had swept the missing item into a bag of used cleaning cloths",
            "tell the gloved custodian, who searches the bag on a covered table",
            "plain rinse water tips over and leaves the item too wet to use tonight",
            "it lies in a drying tray beneath a handwritten FOUND sign",
            "Measurements are stronger evidence than a hurried resemblance.",
        ),
        Incident(
            "confetti_drain", "parade corner",
            "paper confetti clung to a grate that adults were preparing to scrub",
            "a silver star flashed between the paper scraps",
            "the flash came from the clown's coat",
            "shine the helper's flashlight from the dry curb and study the shape",
            "the clown's stars were round, but this flash had the missing item's outline",
            "parade shoes had kicked the missing item to the edge of the storm grate",
            "mark the spot and have maintenance lift the grate with proper tools",
            "a sudden shower carries it deeper before maintenance can close the drain",
            "a silver glimmer disappears while raindrops drum on the empty parade route",
            "Recognizing a shape can correct an exciting but unfair guess.",
        ),
        Incident(
            "mirror_maze", "mirror-maze exit",
            "fingerprints covered one low mirror waiting for its nightly scrub",
            "the missing item's reflection appeared beside the suspect",
            "the suspect held the item",
            "move along the public path and see whether the image follows the person",
            "the image stayed still after the suspect walked away",
            "the real item was caught behind a safety panel and only appeared beside people in reflection",
            "report the exact panel so a trained attendant can open it after closing",
            "an electrical check seals the maze early, leaving the item inside overnight",
            "its reflection repeats down an empty corridor after the EXIT lamp clicks off",
            "A reflection can place two things together even when they are far apart.",
        ),
        Incident(
            "lemon_scent", "ring-toss booth",
            "the counter smelled of lemon soap after a careful scrub",
            "a sticky yellow thumbprint marked the game ledger",
            "the mark came from the prize seller's lemonade",
            "ask which products were used and compare their colors without touching them",
            "the custodian's soap matched; the lemonade cups had red lids and no spills",
            "the missing item had stuck to a damp notice and traveled to the supply cabinet",
            "have the custodian unlock the cabinet and separate the papers over a dry tray",
            "the damp paper tears harmlessly before the item can be returned",
            "the pieces rest in careful rows beside a lemon-scented notice",
            "Asking about ordinary causes can keep an innocent person from being blamed.",
        ),
        Incident(
            "foam_footprints", "fun-house porch",
            "white cleaning foam covered half the porch behind a safety rope",
            "small footprints began near the missing item's last known spot",
            "the prints led toward the clown's wagon",
            "count the toes from the dry side and compare them with shoe prints",
            "each mark had four round toes and a straight wheel line",
            "a raccoon-shaped cleaning robot had carried the item beneath its foam pad",
            "let the attendant switch it off while the gloved adult helper removes the pad",
            "its return cycle locks it in the charging cabinet before they finish",
            "four foamy prints stop at the cabinet with the item tucked safely inside",
            "Detailed observation can turn a worrying trail into a mechanical clue.",
        ),
        Incident(
            "ticket_stamp", "admission arch",
            "an attendant was scrubbing old stamp ink from a rubber mat",
            "a purple square appeared on the suspect's sleeve",
            "the suspect had handled today's missing tickets",
            "compare it with today's round stamp and yesterday's square practice stamp",
            "the sleeve and mat both carried yesterday's washable practice ink",
            "the missing item had fallen beneath the mat before cleaning began",
            "keep off the damp mat while the attendant lifts it by its handles",
            "the final admission bell rings before recovery, so the planned ride is missed",
            "the recovered item sits unused beside the silent turnstile",
            "A clue needs a time as well as a shape before it proves anything.",
        ),
        Incident(
            "feather_duster", "prop tent",
            "a worker had scrubbed the shelves and left them roped off to dry",
            "a green thread clung to a long feather duster",
            "it had snagged on the balloon twister's apron",
            "compare its texture under the helper's magnifier with nearby fabrics",
            "the apron was smooth, but the thread was fuzzy like the toy fox's scarf",
            "the duster had brushed the missing item behind a lightweight prop moon",
            "ask the prop manager to steady the moon while the children wait outside",
            "the display is packed for transport before the correct crate is found",
            "the crate rolls away while one green thread waves from its latch",
            "A matching color is only a beginning; texture may tell another story.",
        ),
        Incident(
            "chalk_arrows", "pony-ring fence",
            "old chalk arrows remained where a water-only scrub was scheduled",
            "one arrow pointed straight toward the suspect's stall",
            "the arrow showed where the missing item had gone",
            "read every arrow from its starting circle instead of following one",
            "together they marked yesterday's lost-and-found practice route",
            "a volunteer had already taken the missing item to the fair office",
            "walk with the helper and identify it by its description and owner",
            "the office window closes seconds before they arrive and cannot reopen",
            "the item waits behind dark glass beside a card bearing the hero's name",
            "A direction without its context can send a thinker the wrong way.",
        ),
        Incident(
            "sawdust_sweep", "puppet-stage aisle",
            "clean sawdust absorbed a small water spill before the aisle was scrubbed",
            "a sawdust trail ended beside the suspect's shoes",
            "the suspect had crossed the spill",
            "look for broom marks from behind the barrier and find the trail's widest end",
            "parallel bristle lines showed that a broom, not shoes, pushed it",
            "the missing item had been swept beneath the stage with the sawdust",
            "have the stage manager use a flashlight and long-handled grabber",
            "a closing scenery panel traps the grabber and item until the next show day",
            "the handle points under the quiet stage like an arrow toward the lost prize",
            "Patterns made by tools should not be mistaken for people's tracks.",
        ),
        Incident(
            "music_spill", "bandstand steps",
            "an adult cleaner was scrubbing a dried juice splash from the lowest step",
            "sticky notes carried pieces of the suspect's song request",
            "the suspect had searched the steps",
            "fit the torn edges together on a dry clipboard and read the message",
            "the full message asked the band to announce a found item",
            "a musician had placed the missing item in the locked instrument office",
            "ask the bandleader to fetch it while everyone stays below the rope",
            "the bus leaves with the office key before the door can open",
            "the last music note fades in the office window's reflection",
            "Putting fragments together can turn suspicion into helpful intent.",
        ),
        Incident(
            "waxed_floor", "prize pavilion",
            "a scrubbed and waxed floor gleamed behind warning cones",
            "the suspect's reflection crossed a scuff near the empty display hook",
            "the suspect's hand had taken the missing item",
            "photograph the scuff from the dry threshold and compare it after the suspect moves",
            "the supposed hand was a spinning pinwheel reflected from outside",
            "a drying fan had blown the missing item into a locked prize cabinet",
            "give the photograph and cabinet number to the manager without crossing the wet floor",
            "the cabinet key is broken and a locksmith cannot come until tomorrow",
            "the item rests behind glass while warning cones glow in the closing lights",
            "Solving a cause does not always mean it can be fixed immediately.",
        ),
    )
}

OPENINGS = (
    "The mystery began just before the evening parade.",
    "At the noisiest hour of the fair, a small absence felt enormous.",
    "The fair looked cheerful, but one detail was wrong.",
    "A cleaning bell chimed as the day's strangest case began.",
    "Between two bursts of carousel music, trouble quietly appeared.",
    "The case started where bright lights met a freshly cleaned walkway.",
    "Nobody expected a whodunit during the fair's nightly scrub.",
    "One missing possession turned a fair visit into an investigation.",
    "The final rides were filling when the clue trail began.",
    "A gust shook the bunting, and the fair offered up a puzzle.",
)

THOUGHTS = (
    '"A clue tells me where to look, not whom to blame," {hero} reminded {self_word}.',
    '{hero} thought, "What else could have made that mark? I need a test."',
    'Inside, {hero} counted the facts: "I saw a clue, but I have not proved a culprit."',
    '"Slow down," {hero} thought. "A fair guess still needs fair evidence."',
    '{hero}\'s first idea felt neat. Then came the inner question: "What would prove it wrong?"',
    'In {possessive} head, {hero} drew two columns: what the clue showed, and what it did not.',
    '{hero} silently asked, "If my guess is true, what should I find next?"',
    'The answer seemed obvious, which made {hero} suspicious of {possessive} own answer.',
)

DIALOGUES = (
    '"Let us test the clue before we question anyone," said {helper}.',
    '"Good detectives protect people as carefully as evidence," {helper} said.',
    '"We can investigate without crossing any cleaning ropes," said {helper}.',
    '"Tell me what you observed, not what you guessed," {helper} suggested.',
    '"One fact at a time, and adults handle the cleaning tools," said {helper}.',
    '"A mistake in reasoning can be scrubbed away by a better test," {helper} said.',
    '"We will ask, compare, and stay on the dry path," {helper} promised.',
    '"The suspect deserves a question, not an accusation," said {helper}.',
)

TURN_BRIDGES = (
    "The next clue changed the whole shape of the case.",
    "Their test did something useful: it proved the first idea wrong.",
    "Once they separated the mark from the person, another cause became visible.",
    "The mystery turned not on a confession, but on one ordinary physical detail.",
    "A careful comparison replaced suspicion with a cause they could check.",
    "That was the moment the whodunit became a how-did-it-happen.",
    "The clue trail stopped pointing at a person and began pointing at an accident.",
    "Their failed theory left behind a better question.",
)

ASP_RULES = r"""
missing_item(X) :- item(X).
incident(I) :- incident_fact(I).
suspect(S) :- suspect_fact(S).
safe_investigation(I) :- incident_fact(I), adult_supervised(I).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("item", key) for key in MISSING_ITEMS]
    lines += [asp.fact("incident_fact", key) for key in INCIDENTS]
    lines += [asp.fact("adult_supervised", key) for key in INCIDENTS]
    lines += [asp.fact("suspect_fact", name) for name in FAIRS["fair"].suspects]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fair whodunit with safe scrubbing and a bad ending.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--suspect")
    parser.add_argument("--missing", choices=sorted(MISSING_ITEMS))
    parser.add_argument("--place", choices=sorted(FAIRS))
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
    hero = args.hero or rng.choice(list(HERO_TYPES))
    place = args.place or "fair"
    return StoryParams(
        seed=args.seed,
        hero=hero,
        hero_type=HERO_TYPES.get(hero, "child"),
        helper=args.helper or rng.choice(["Aunt June", "Grandpa Sol", "Ms. Peta", "Uncle Ren"]),
        suspect=args.suspect or rng.choice(FAIRS[place].suspects),
        missing=args.missing or rng.choice(list(MISSING_ITEMS)),
        place=place,
        mood=rng.choice(["windy", "bright", "drizzly", "breezy", "cool"]),
        incident=rng.choice(list(INCIDENTS)),
        narrative_mode=rng.randrange(len(OPENINGS)),
        thought_mode=rng.randrange(len(THOUGHTS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        turn_mode=rng.randrange(len(TURN_BRIDGES)),
    )


def _possessive(name: str) -> str:
    return name + "'" if name.endswith("s") else name + "'s"


def _investigate(
    world: World,
    params: StoryParams,
    hero: Entity,
    helper: Entity,
    suspect: Entity,
    incident: Incident,
) -> None:
    self_word = "herself" if hero.type == "girl" else "himself" if hero.type == "boy" else "themself"
    thought = THOUGHTS[params.thought_mode].format(
        hero=hero.id, self_word=self_word, possessive=hero.pronoun("possessive")
    )
    dialogue = DIALOGUES[params.dialogue_mode].format(helper=helper.id)
    routes = (
        [f"The first clue was that {incident.first_clue}.", f"At first, {hero.id} wondered whether {incident.false_guess}.", thought, dialogue, f"Together they decided to {incident.test}.", f"That check revealed that {incident.second_clue}."],
        [f"Because {incident.first_clue}, {hero.id} almost blamed {suspect.label}.", dialogue, thought, f"Their safer test was to {incident.test}.", f"Instead, it showed that {incident.second_clue}."],
        [f"{hero.id} began with a theory: {incident.false_guess}.", f"It came from one detail: {incident.first_clue}.", thought, dialogue, f"They chose to {incident.test}.", f"The result mattered: {incident.second_clue}."],
        [f"Near the {incident.area}, {hero.id} saw that {incident.first_clue}.", thought, f"A quick guess said {incident.false_guess}; a careful plan said to {incident.test}.", dialogue, f"Care won. They discovered that {incident.second_clue}."],
        [f"Clue one looked persuasive: {incident.first_clue}.", f"It suggested that {incident.false_guess}.", dialogue, f"Before accusing {suspect.label}, {hero.id} paused. {thought}", f"The pair chose to {incident.test}, and learned that {incident.second_clue}."],
        [f"{hero.id} told {helper.id} the observation and the guess: {incident.first_clue}, so perhaps {incident.false_guess}.", dialogue, thought, f"They tested the idea by choosing to {incident.test}.", f"The guess failed usefully: {incident.second_clue}."],
        [f"The trail began when {incident.first_clue}.", f"{hero.id}'s inner voice leaped to a conclusion: {incident.false_guess}.", dialogue, thought, f"They stayed outside the cleaning rope and chose to {incident.test}.", f"The next fact was clearer: {incident.second_clue}."],
        [f"What did they know? That {incident.first_clue}.", f"What did they only suspect? That {incident.false_guess}.", thought, dialogue, f"What could they test safely? They could {incident.test}.", f"What did they learn? That {incident.second_clue}."],
        [dialogue, f"{hero.id} agreed. Still, {incident.first_clue}, so perhaps {incident.false_guess}.", thought, f"Their problem-solving step was to {incident.test}.", f"It overturned the theory because {incident.second_clue}."],
        [f"One clue tempted {hero.id} into a mistake: {incident.first_clue}. Perhaps {incident.false_guess}.", thought, dialogue, f"So they chose to {incident.test}.", f"The evidence corrected them: {incident.second_clue}."],
    )
    for sentence in routes[params.narrative_mode]:
        world.say(sentence)


def tell(params: StoryParams) -> World:
    place = FAIRS[params.place]
    incident = INCIDENTS[params.incident]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper))
    suspect = world.add(Entity(id=params.suspect, kind="character", type="adult", label=params.suspect))
    missing = world.add(Entity(id=params.missing, label=params.missing, phrase=MISSING_ITEMS[params.missing], owner=hero.id))

    world.say(OPENINGS[params.narrative_mode])
    world.say(f"On a {params.mood} evening, {hero.id} and {helper.id} reached {place.name}, where {place.noise} surrounded the nightly fair scrub.")
    world.say(f"At the {incident.area}, {hero.id} discovered that {_possessive(hero.id)} {missing.phrase} was missing. Nearby, {incident.disturbance}.")
    world.para()
    _investigate(world, params, hero, helper, suspect, incident)
    world.say(TURN_BRIDGES[params.turn_mode])

    world.para()
    world.say(f"The clues finally fit: {incident.cause}.")
    world.say(f'"Then nobody stole it," {hero.id} told {suspect.label}. "I am sorry I nearly blamed you."')
    world.say(f"Their problem-solving plan was to {incident.safe_plan}.")
    world.say(f"The plan was sensible, but the ending was still bad: {incident.bad_result}.")
    world.say("No one was hurt, and no child handled cleaning liquid or crossed a safety barrier.")
    world.say(f'{hero.id} thought, "I solved what happened, but solving a mystery cannot always undo it."')
    world.say(incident.lesson)
    world.say(f"As they left, {incident.final_image}.")

    hero.memes.update(focus=2.0, fairness=1.0, resilience=1.0)
    missing.hidden_in = incident.area
    world.facts.update(
        hero=hero, helper=helper, suspect=suspect, missing=missing, place=place,
        incident=incident, first_theory=incident.false_guess, test=incident.test,
        cause=incident.cause, safe_plan=incident.safe_plan, bad_result=incident.bad_result,
        bad_ending=True, suspect_cleared=True, cleaning_safe=True,
    )
    world.trace.extend((f"missing:{missing.id}", f"incident:{incident.key}", f"test:{incident.test}", f"cause:{incident.cause}", f"bad_result:{incident.bad_result}"))
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    missing: Entity = world.facts["missing"]
    incident: Incident = world.facts["incident"]
    return [
        f"Write a child-friendly fair mystery in which {hero.id} searches for a {missing.label} near the {incident.area}.",
        "Tell a problem-solving story about a fair scrub, inner monologue, mistaken suspicion, and non-cruel bad ending.",
        f"Use the clue that {incident.first_clue}, then reveal that {incident.cause}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    suspect: Entity = world.facts["suspect"]
    missing: Entity = world.facts["missing"]
    incident: Incident = world.facts["incident"]
    return [
        QAItem(question=f"What went missing near the {incident.area}?", answer=f"{hero.id}'s {missing.phrase} went missing near the {incident.area}."),
        QAItem(question=f"Why did {hero.id}'s first theory seem possible?", answer=f"It seemed possible because {incident.first_clue}. That made {hero.id} wonder whether {incident.false_guess}."),
        QAItem(question=f"How did {hero.id} and {helper.id} test the theory safely?", answer=f"They chose to {incident.test}. They stayed outside cleaning barriers and left cleaning equipment to adults."),
        QAItem(question=f"What actually happened to the {missing.label}?", answer=f"They discovered that {incident.cause}. This cleared {suspect.label} of taking it."),
        QAItem(question="Why is the ending bad even though the mystery is solved?", answer=f"It is disappointing because {incident.bad_result}. No one is hurt, but the loss cannot be fixed that evening."),
        QAItem(question=f"What did {hero.id} learn?", answer=incident.lesson),
    ]


def world_qa(world: World) -> list[QAItem]:
    incident: Incident = world.facts["incident"]
    return [
        QAItem(question="Why should a child stay outside an area being scrubbed?", answer="A freshly scrubbed area may be slippery or contain cleaning supplies. Children should stay behind barriers and let trained adults handle the work."),
        QAItem(question="What makes an investigation fair to a suspect?", answer="The investigator separates observations from guesses, tests other causes, and asks questions without accusing anyone prematurely."),
        QAItem(question=f"Which evidence mattered in the {incident.area} case?", answer=f"The decisive evidence was that {incident.second_clue}. It explained the clue without assuming that a person was guilty."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", *(f"  {entry}" for entry in world.trace)]
    for entity in world.entities.values():
        bits = []
        if entity.hidden_in:
            bits.append(f"hidden_in={entity.hidden_in}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.kind}/{entity.type}) {' '.join(bits)}")
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== World questions =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(incident="soap_bubbles"),
    StoryParams(hero="Nico", hero_type="boy", helper="Grandpa Sol", suspect="the prize seller", missing="toy fox", incident="mirror_maze", narrative_mode=3, thought_mode=4, dialogue_mode=2, turn_mode=5),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    show = "#show missing_item/1.\n#show incident/1.\n#show suspect/1.\n#show safe_investigation/1.\n"
    if asp.one_model(asp_program(show)) is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP program solved.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


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
    show = "#show missing_item/1.\n#show incident/1.\n#show suspect/1.\n#show safe_investigation/1.\n"
    if args.show_asp:
        print(asp_program(show))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for offset in range(args.n):
            params = resolve_params(args, random.Random(base_seed + offset))
            params.seed = base_seed + offset
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
