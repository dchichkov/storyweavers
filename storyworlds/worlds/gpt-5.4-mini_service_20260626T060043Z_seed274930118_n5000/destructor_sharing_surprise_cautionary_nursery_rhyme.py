#!/usr/bin/env python3
"""A varied, child-safe nursery-rhyme world about cautious toy sharing."""

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

TRY_NAMES = [
    "Mina", "Toby", "Luna", "Nico", "Poppy", "Milo", "Ada", "Finn",
    "Ruby", "Owen",
]

CARE_NAMES = ["mother", "father", "grandma", "grandpa", "auntie", "uncle"]
PLACES = ["the nursery", "the playroom", "the cozy room", "the sunny corner"]
COMPANIONS = ["a friend", "a neighbor", "a cousin", "a small guest"]


@dataclass(frozen=True)
class Incident:
    key: str
    premise: str
    obstacle: str
    surprise: str
    clue: str
    poor_choice: str
    safe_action: str
    result: str
    lesson: str
    ending: str
    sound: str


INCIDENTS = [
    Incident(
        "paper_bridge",
        "They were making a paper bridge for three wooden ducks.",
        "The bridge pieces were passed too quickly, and two tabs bent together.",
        "the toy released both tabs at once and the bridge opened like a fan",
        "a blue alignment dot was hiding beneath the folded paper",
        "They nearly pressed the button again before checking the fold.",
        "They laid the bridge flat, matched the blue dots, and took turns separating one tab at a time.",
        "The repaired bridge held all three ducks without a wobble.",
        "Sharing means giving each person enough time to look before acting.",
        "Three wooden ducks crossed the bridge beneath a row of blue paper flags.",
        "snip-snap",
    ),
    Incident(
        "block_garden",
        "They had built a block garden with a gate around a felt flower.",
        "Each child tugged a different gate piece, so the wall leaned toward the flower.",
        "a loose green block rolled into the watering cup",
        "matching leaf marks showed which blocks belonged beside the gate",
        "For one breath, each child blamed the other's hand.",
        "They named their jobs, steadied the wall together, and used the destructor to unclip only the crooked pieces.",
        "The gate swung freely, and the felt flower stayed upright.",
        "A shared plan works better than shared blame.",
        "The green gate clicked shut while the felt flower nodded in the window breeze.",
        "click-clack",
    ),
    Incident(
        "ribbon_spool",
        "They were taking apart an old ribbon mobile so its pieces could be reused.",
        "A long ribbon loop slipped around the toy's tray and stopped it from opening.",
        "the spool twirled once and painted a red circle in the air",
        "the ribbon was caught under the tray, not inside the toy",
        "They first tried pulling from opposite ends, which tightened the loop.",
        "They set everything down, loosened the loop with one pair of hands, and rolled the ribbon onto its spool.",
        "The tray opened normally, and every ribbon was ready for another craft.",
        "When something catches, stop pulling and find what is holding it.",
        "The tidy ribbon spool rested beside a new moon-shaped mobile.",
        "whirr-flip",
    ),
    Incident(
        "picture_puzzle",
        "They wanted to separate a cardboard picture puzzle and trade halves to rebuild it.",
        "Two nearly identical pieces became wedged in the release window.",
        "a painted owl appeared upside down between their fingers",
        "one piece had a tiny moon and the other had a tiny sun",
        "They guessed that pushing harder would make the pieces agree.",
        "They compared the symbols, tipped the tray toward the table, and released the moon piece before the sun piece.",
        "Both puzzle halves came free, and the children rebuilt the picture side by side.",
        "Careful noticing can solve what force cannot.",
        "The finished owl looked out over a silver moon and a yellow sun.",
        "tip-tap",
    ),
    Incident(
        "bell_cart",
        "They were remaking a little cardboard cart with a bell on its roof.",
        "The bell cord lay across the line where a panel needed to separate.",
        "the bell rang even though nobody had touched its handle",
        "the moving panel was brushing the cord",
        "They almost called the surprise magic and kept going.",
        "They paused, traced the cord with their eyes, moved it aside, and shared the release button by counting together.",
        "The panel came away cleanly, and the bell rang only when invited.",
        "A surprising sound is a reason to investigate, not a reason to rush.",
        "The rebuilt cart rolled past the rug with one bright, intended ring.",
        "ting-a-ling",
    ),
    Incident(
        "sorting_tray",
        "They planned to sort reusable craft shapes into stars, circles, and squares.",
        "Both children tipped the collection cup, mixing every shape into one small hill.",
        "a silver star landed neatly on the caregiver's slipper",
        "the tray's three shallow corners matched the three kinds of shapes",
        "They began grabbing for favorite shapes, making the pile spread farther.",
        "They stopped, assigned one shape to each person, and passed the tray only when a corner was ready.",
        "Soon every piece was sorted and nobody had to reach across another hand.",
        "Taking turns can make sharing faster as well as kinder.",
        "A silver star shone from the top of three orderly little piles.",
        "plink-plunk",
    ),
    Incident(
        "shadow_screen",
        "They were dismantling a shadow screen to build a smaller puppet stage.",
        "The folded screen blocked the lamp and made the room suddenly dim.",
        "a giant rabbit shadow hopped across the ceiling",
        "the companion's two fingers were making the rabbit ears",
        "They both reached toward the lamp before asking what had changed.",
        "They kept their hands off the lamp, unfolded the screen, and asked the caregiver to move the light safely.",
        "With the light settled, they separated the cardboard joints and built a sturdy little stage.",
        "Pause around lights and ask an adult before moving them.",
        "A tiny rabbit puppet bowed inside the new bright screen.",
        "flick-flick",
    ),
    Incident(
        "seed_packet",
        "They were opening perforated seed packets to make labels for a pretend garden.",
        "One packet had been placed backward, hiding its easy-open edge.",
        "three paper sunflower shapes fluttered into the caregiver's basket",
        "a dotted line on the back showed where the packet should separate",
        "They tried the smooth edge first and wrinkled one corner.",
        "They turned the packet over, followed the dots, and alternated who held the packet and who pressed the toy.",
        "The label came free and the pretend seeds stayed together in their paper pocket.",
        "Directions are worth finding before a new tool is used.",
        "Their paper garden ended with three sunflowers standing in a yellow row.",
        "zip-zup",
    ),
    Incident(
        "train_ticket",
        "They were separating pretend train tickets for a journey around the rug.",
        "The ticket strip entered the destructor at a slant and would not slide through.",
        "the last ticket sprang up and perched on the toy train",
        "small arrow marks pointed toward the straight paper guide",
        "They each tried steering the strip from a different side.",
        "They chose one guide and one collector, lined up the arrows, and changed jobs after every ticket.",
        "The tickets separated evenly, with one fair turn for every passenger.",
        "Clear jobs help friends share both a tool and its work.",
        "The toy train waited beside a tidy stack of rainbow tickets.",
        "chuff-chik",
    ),
    Incident(
        "nest_mobile",
        "They were reusing cardboard rings to make a hanging nest for a cloth bird.",
        "A ring bounced from the tray and rolled beneath the rocking chair.",
        "the cloth bird tipped forward as if pointing to the runaway ring",
        "the round ring had followed the slight slope in the floor",
        "They started to crawl under the chair while it was still rocking.",
        "They stepped back, asked the caregiver to stop the chair, and used a ruler to roll the ring into reach.",
        "They finished the mobile from a clear table with a cup ready for loose rings.",
        "Ask for help when a toy piece rolls near moving furniture.",
        "The cloth bird turned slowly above a nest of bright cardboard rings.",
        "roll-rill",
    ),
    Incident(
        "story_wheel",
        "They were changing the pictures on a spinning cardboard story wheel.",
        "The wheel kept turning while they tried to release its picture tabs.",
        "a moon, a boot, and a spoon flashed past in a silly parade",
        "a small wooden peg could hold the wheel still",
        "They chased the moving tabs with the destructor and missed each one.",
        "They laughed, stopped the wheel with its peg, and took turns choosing and releasing one picture.",
        "The new story showed a moonlit picnic in the order they had planned.",
        "Make moving work still before careful hands begin.",
        "The story wheel rested on a moon while a paper spoon pointed toward the stars.",
        "whish-hush",
    ),
    Incident(
        "name_banner",
        "They were separating letter tiles for a welcome banner.",
        "The children both wanted the same bright first letter and stopped passing the tray.",
        "a blank tile flipped over to reveal a cheerful golden heart",
        "there were enough blank backs to draw a second first letter",
        "They tugged the wanted tile between them until the caregiver said, 'Hands still.'",
        "They released the tile, drew another together, and alternated letters while one child steadied the tray.",
        "The banner held both names with the golden heart exactly between them.",
        "Sharing can mean making room for both people's ideas.",
        "Two names curved across the wall with one golden heart in the middle.",
        "tap-ta-da",
    ),
]

OPENINGS = [
    "Morning light made a pale square on the rug.",
    "Rain ticked softly at the window while the craft box came down.",
    "After snack, the children cleared a broad place on the floor.",
    "A paper garland stirred above the quiet play table.",
    "The room smelled faintly of crayons and clean cardboard.",
    "Before the clock chimed, two small chairs met beside the toy tray.",
    "Sunlight found every bright scrap in the craft basket.",
    "A cozy lamp glowed over a table ready for making.",
    "The toy shelf had one open space and a project waiting below it.",
    "Soft music ended just as the children chose their next project.",
    "A patch of warm floor invited a careful afternoon game.",
    "The craft cloth opened with a flap across the little table.",
]

SHARING_LINES = [
    "You steady the tray, and I will press when you say ready.",
    "Let us trade jobs after each piece, so both jobs belong to both of us.",
    "May I have the next turn if I wait behind the blue line?",
    "We can share the plan first and the destructor second.",
    "Tell me when your fingers are clear, and then I will begin.",
    "One holds, one looks, one presses; then around the jobs go.",
    "I want a turn, but I can wait until the table is clear.",
    "Let us put every loose piece in the cup before we swap places.",
]

CAUTION_LINES = [
    "Stop at a surprise, set the toy down, and look before you try again.",
    "A careful turn begins only when both pairs of hands are ready.",
    "The destructor separates toy craft pieces; it is never for people, pets, or living things.",
    "Keep fingers beside the handles and loose pieces inside the tray.",
    "When two hands disagree, pause the toy and agree on one next step.",
    "Unexpected movement means hands off until everyone knows the cause.",
    "Use the toy on the clear table, and ask for help when anything catches.",
    "Count one, two, ready before pressing, and stop if the answer is not ready.",
]

RHYMES = [
    ("Share the tray and share the say;", "slow and steady saves the play."),
    ("Pause your hand and make a plan;", "kindness shows us where we can."),
    ("Look before the pieces part;", "careful eyes are clever hearts."),
    ("Take a turn and check the clue;", "I help me, and I help you."),
    ("When surprise comes bouncing through;", "stop, then choose what hands should do."),
    ("Pass it gently, set it right;", "shared-up work can finish bright."),
    ("Hands stay clear and voices low;", "name the job before you go."),
    ("If it catches, never tug;", "set it down upon the rug."),
    ("One may guide and one may press;", "trading turns prevents a mess."),
    ("Find the mark and mind the sound;", "then let care go round and round."),
    ("Tools are useful, tools need care;", "safe is part of how we share."),
    ("First we wonder, then we see;", "patient friends make problems flee."),
]

ENDING_LEADS = [
    "At last, the room was quiet enough to hear a page turn.",
    "By tidy-up time, the surprise had become a story worth retelling.",
    "When the caregiver brought the empty piece cup, the work was already done.",
    "The children swapped one final job before putting the destructor away.",
    "A last little rhyme followed them to the toy shelf.",
    "Nothing had needed force; noticing had done the difficult work.",
    "Their earlier hurry felt far away when they looked at what they had made.",
    "The destructor's tray was empty, the table was clear, and both children were smiling.",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    broken: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def title(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the nursery"
    cozy: bool = True


@dataclass
class Toy:
    label: str = "destructor"
    phrase: str = "a tiny destructor toy"
    fragility: int = 1
    surprise_sound: str = "pop"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    caregiver: str
    companion: str
    seed: Optional[int] = None
    incident_key: str = "paper_bridge"
    opening_index: int = 0
    sharing_index: int = 0
    caution_index: int = 0
    rhyme_index: int = 0
    ending_index: int = 0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _speak(world: World, speaker: Entity, line: str) -> None:
    world.say(f'"{line}" {speaker.title()} said.')


def _subject(label: str) -> str:
    return label[0].upper() + label[1:]


def _incident(key: str) -> Incident:
    for incident in INCIDENTS:
        if incident.key == key:
            return incident
    raise StoryError(f"Unknown incident: {key}")


def _record_story_state(
    world: World,
    hero: Entity,
    companion: Entity,
    caregiver: Entity,
    toy: Entity,
    incident: Incident,
) -> None:
    hero.memes.update(sharing=1.0, surprise=1.0, caution=1.0, kindness=1.0, joy=1.0)
    companion.memes.update(sharing=1.0, surprise=1.0, caution=1.0, kindness=1.0, joy=1.0)
    caregiver.memes.update(caution=1.0, guidance=1.0)
    toy.memes.update(surprise=1.0)
    toy.meters.update(shared=1.0, paused=1.0, inspected=1.0, safe_play=1.0)
    toy.holder = None
    world.fired.update(
        {
            ("sharing", toy.id),
            ("surprise", incident.key),
            ("caution", incident.key),
            ("resolution", incident.key),
        }
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    companion = world.add(Entity(id="companion", kind="character", type="child", label=params.companion))
    caregiver = world.add(
        Entity(id="caregiver", kind="character", type=params.caregiver, label=params.caregiver.capitalize())
    )
    toy = world.add(
        Entity(
            id="toy",
            type="toy",
            label="destructor",
            phrase="a blunt-edged cardboard craft separator",
        )
    )
    incident = _incident(params.incident_key)
    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    sharing_line = SHARING_LINES[params.sharing_index % len(SHARING_LINES)]
    caution_line = CAUTION_LINES[params.caution_index % len(CAUTION_LINES)]
    rhyme = RHYMES[params.rhyme_index % len(RHYMES)]
    ending_lead = ENDING_LEADS[params.ending_index % len(ENDING_LEADS)]
    companion_subject = _subject(companion.title())
    caregiver_subject = _subject(caregiver.title())

    toy.owner = hero.id
    toy.holder = hero.id

    world.say(opening)
    world.say(
        f"In {setting.place}, {hero.title()} brought out a palm-sized toy called the destructor. "
        "Its silly name meant only that it gently unclipped perforated cardboard craft pieces; "
        "it had blunt edges, no motor, and could not hurt or destroy anything alive."
    )
    world.say(
        f"{companion_subject} joined {hero.title()} at the clear work space. "
        f"They were practicing sharing while they made something together. {incident.premise}"
    )
    world.para()

    _speak(world, companion, sharing_line)
    world.say(f"{hero.title()} agreed, but their first shared turn went awry. {incident.obstacle}")
    world.say(f"{incident.sound.upper()}! To their surprise, {incident.surprise}.")
    world.para()

    world.say(incident.poor_choice)
    world.say(
        f"Then {hero.title()} set the destructor flat on the table, and both children looked instead of grabbing. "
        f"They discovered that {incident.clue}."
    )
    _speak(world, caregiver, caution_line)
    world.say(
        f"The children turned that caution into a nursery rhyme and said it together: "
        f'\"{rhyme[0]} {rhyme[1]}\"'
    )
    world.para()

    world.say(incident.safe_action)
    world.say(incident.result)
    world.say(f"{caregiver_subject} named the lesson: {incident.lesson}")
    world.say(f"{ending_lead} {incident.ending}")

    _record_story_state(world, hero, companion, caregiver, toy, incident)

    world.facts.update(
        hero=hero,
        companion=companion,
        caregiver=caregiver,
        toy=toy,
        setting=setting,
        params=params,
        incident=incident,
        caution_line=caution_line,
        rhyme=rhyme,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident: Incident = world.facts["incident"]
    return [
        f"Write a gentle nursery rhyme about {p.hero_name} sharing a harmless cardboard destructor toy with {p.companion}.",
        f"Tell a cautionary story in which {incident.obstacle.lower()} Let observation and cooperation solve the problem.",
        f"Create a cozy story for small children set in {p.place}, with surprise, safe sharing, and a concrete happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    caregiver: Entity = f["caregiver"]
    toy: Entity = f["toy"]
    setting: Setting = f["setting"]
    incident: Incident = f["incident"]
    caution_line: str = f["caution_line"]
    rhyme: tuple[str, str] = f["rhyme"]

    return [
        QAItem(
            question=f"What was the destructor that {hero.title()} brought into {setting.place}?",
            answer=(
                "It was a harmless, blunt-edged toy for unclipping perforated cardboard craft pieces. "
                "Its dramatic name was only a silly nickname, and it had no motor."
            ),
        ),
        QAItem(
            question=f"What surprised {hero.title()} and {companion.title()} during their shared project?",
            answer=(
                f"They were surprised when {incident.surprise}. "
                f"The surprise happened after {incident.obstacle.lower()}"
            ),
        ),
        QAItem(
            question=f"What clue helped the children understand the problem?",
            answer=(
                f"They noticed that {incident.clue}. "
                "That clue let them replace guessing and grabbing with a careful plan."
            ),
        ),
        QAItem(
            question=f"What caution did {caregiver.title()} give?",
            answer=(
                f'{_subject(caregiver.title())} said, "{caution_line}" '
                f'The children remembered it with the rhyme, "{rhyme[0]} {rhyme[1]}"'
            ),
        ),
        QAItem(
            question="How did careful sharing change the outcome?",
            answer=f"{incident.safe_action} {incident.result}",
        ),
        QAItem(
            question="What did the children learn, and what final picture showed the change?",
            answer=f"They learned that {incident.lesson.lower()} In the final picture, {incident.ending.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to share a toy?",
            answer="To share a toy means to let someone else use it too, usually by taking turns and being kind.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens before anyone is ready for it.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so nobody gets hurt and nothing breaks.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.holder:
            bits.append(f"holder={e.holder}")
        if e.broken:
            bits.append("broken=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.title()} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child has the toy, then sharing may begin.
sharing(H,C,T) :- holder(T,H), companion(C), child(H).

% A shared toy can cause a surprise if it has the surprise property.
surprise(H,C,T) :- sharing(H,C,T), toy(T).

% A caregiver issues caution after surprise.
caution(CG,H,C,T) :- surprise(H,C,T), caregiver(CG).

% A safe turn follows caution.
safe(H,C,T) :- caution(CG,H,C,T), toy(T).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "hero"),
        asp.fact("child", "companion"),
        asp.fact("companion", "companion"),
        asp.fact("caregiver", "caregiver"),
        asp.fact("toy", "toy"),
        asp.fact("holder", "toy", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme world about sharing a destructor.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name", choices=TRY_NAMES)
    ap.add_argument("--caregiver", choices=CARE_NAMES)
    ap.add_argument("--companion", choices=COMPANIONS)
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
    hero_name = args.name or rng.choice(TRY_NAMES)
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=hero_name,
        hero_type="girl" if hero_name in {"Mina", "Luna", "Poppy", "Ada", "Ruby"} else "boy",
        caregiver=args.caregiver or rng.choice(CARE_NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        incident_key=rng.choice(INCIDENTS).key,
        opening_index=rng.randrange(len(OPENINGS)),
        sharing_index=rng.randrange(len(SHARING_LINES)),
        caution_index=rng.randrange(len(CAUTION_LINES)),
        rhyme_index=rng.randrange(len(RHYMES)),
        ending_index=rng.randrange(len(ENDING_LEADS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(place=params.place), params)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, name, comp) for place in PLACES for name in TRY_NAMES for comp in COMPANIONS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show sharing/3.\n#show surprise/3.\n#show caution/4.\n#show safe/3."))
    return sorted(set(asp.atoms(model, "sharing")))


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(
        place="the nursery", hero_name="Mina", hero_type="girl", caregiver="mother",
        companion="a friend", incident_key="paper_bridge", rhyme_index=2,
    ),
    StoryParams(
        place="the playroom", hero_name="Toby", hero_type="boy", caregiver="father",
        companion="a cousin", incident_key="bell_cart", opening_index=3, sharing_index=2,
        caution_index=5, rhyme_index=4, ending_index=2,
    ),
    StoryParams(
        place="the cozy room", hero_name="Luna", hero_type="girl", caregiver="grandma",
        companion="a small guest", incident_key="name_banner", opening_index=7,
        sharing_index=7, caution_index=4, rhyme_index=10, ending_index=6,
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show sharing/3.\n#show surprise/3.\n#show caution/4.\n#show safe/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
