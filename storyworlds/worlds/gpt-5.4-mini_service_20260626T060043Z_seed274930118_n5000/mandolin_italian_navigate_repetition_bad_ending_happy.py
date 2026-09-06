#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mandolin_italian_navigate_repetition_bad_ending_happy.py
==============================================================================================================

A small space-adventure storyworld about a navigation problem, a repeating
signal, and a musical fix.

Seed image:
---
A little starship is trying to navigate through a drifting asteroid lane. The
ship keeps hearing the same mandolin tune over and over on its radio, and the
crew can barely understand the instructions because the message is in Italian.
The first try goes badly, then the crew changes course, repeats the tune in a
new way, and reaches a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pilot", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "engineer"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    pilot_type: str = "pilot"
    partner_name: str = "Nico"
    partner_type: str = "engineer"
    ship_name: str = "the Comet Lily"


NAMES = ["Mina", "Aria", "Luna", "Theo", "Nico", "Pia", "Ravi", "Elio"]
SHIP_NAMES = ["the Comet Lily", "the Blue Orbit", "the Star Lantern", "the Little Helix"]


INCIDENTS = [
    {
        "title": "the echoing moon gate",
        "place": "a gate between two blue moons",
        "signal": "three quick notes and one long note",
        "wrong": "counted every radio echo as a new instruction and turned too soon",
        "setback": "the ship settled on a quiet service ledge while the gate closed for the night",
        "clue": "each true phrase began with the Italian word 'ascolta,' meaning 'listen'",
        "meaning": "Listen once, then follow the long note toward the left moon",
        "action": "muted the echoes, played the four-note phrase once on the mandolin, and marked the left moon on the chart",
        "recovery": "the morning gate recognized the clean phrase and opened a silver path",
        "ending": "dew-bright moon dust trembled on the ledge as the ship sailed between the moons",
        "lesson": "Repetition helps only when you know which part is the original message",
    },
    {
        "title": "the drifting lantern buoys",
        "place": "a current of lantern-shaped navigation buoys",
        "signal": "a rising mandolin scale",
        "wrong": "followed the brightest buoy instead of the notes and entered a harmless loop",
        "setback": "the ship returned to the same green buoy just as its travel clock chimed bedtime",
        "clue": "the Italian message said 'dal basso all'alto,' or 'from low to high'",
        "meaning": "Visit the buoys in the same low-to-high order as the melody",
        "action": "sorted the glowing buoys by pitch, then shared the piloting and music-counting jobs",
        "recovery": "the final high note lit a straight lane out of the current",
        "ending": "the buoys winked behind them in a staircase of green, gold, and white",
        "lesson": "A pattern can be a map when a crew tests it carefully together",
    },
    {
        "title": "the sleepy comet crossing",
        "place": "the path of a slow, powdery comet",
        "signal": "a soft tune with a pause after every second bar",
        "wrong": "treated the pauses as broken radio gaps and sped into the comet's dusty wake",
        "setback": "the dust cloud hid every landmark, so the crew parked safely and missed the evening crossing",
        "clue": "the repeated Italian word 'pausa' meant that each silence was part of the directions",
        "meaning": "Move during the music and wait during each pause",
        "action": "tapped the pauses on the mandolin case and navigated in careful start-and-stop steps",
        "recovery": "the dust cleared between pauses, revealing one marker at a time",
        "ending": "a pale comet tail curled beyond the window while the final chord faded",
        "lesson": "Silence can carry useful information too",
    },
    {
        "title": "the mirror-ice fork",
        "place": "a fork lined with flat mirrors of space ice",
        "signal": "two notes that seemed to answer one another",
        "wrong": "steered toward a reflected beacon and reached a smooth dead-end cove",
        "setback": "the cove's ice door froze shut until the next warm starlight cycle",
        "clue": "the message repeated 'vero, non riflesso' - 'real, not reflected'",
        "meaning": "Choose the beacon whose light does not copy the mandolin's rhythm",
        "action": "played alternating notes, watched which beacon stayed steady, and recorded the real one",
        "recovery": "warm starlight opened the cove and the steady beacon guided them through",
        "ending": "the false beacons shattered into harmless rainbows across the retreating ice",
        "lesson": "Good navigation depends on evidence, not merely on what shines brightest",
    },
    {
        "title": "the garden satellite maze",
        "place": "a maze of small satellites carrying seed gardens",
        "signal": "a bouncy five-note refrain",
        "wrong": "chased the refrain's loudest broadcast and circled the same tomato satellite",
        "setback": "the last delivery hatch closed, leaving the seed parcel aboard until morning",
        "clue": "the phrase 'quinta serra' meant 'fifth greenhouse,' not five turns",
        "meaning": "Navigate to greenhouse number five and wait beside its purple lamp",
        "action": "labeled each refrain on the chart, found the fifth greenhouse, and played the tune at half volume",
        "recovery": "the gardeners reopened the hatch early when they heard the careful reply",
        "ending": "tiny leaves turned toward the ship as the parcel floated into the purple-lit greenhouse",
        "lesson": "Translating the whole phrase prevents a confident but mistaken guess",
    },
    {
        "title": "the bell-shaped asteroid lane",
        "place": "a lane of hollow, bell-shaped asteroids",
        "signal": "a brisk mandolin rhythm mixed with ringing stone",
        "wrong": "matched the stone echoes instead of the broadcast and zigzagged into a sheltered pocket",
        "setback": "a gentle field held the ship there while the supply convoy passed without them",
        "clue": "the Italian instruction 'segui il ritmo calmo' meant 'follow the calm rhythm'",
        "meaning": "Ignore the asteroid ringing and follow the steady background beat",
        "action": "laid a hand on the mandolin body to feel the steady beat while the other crew member plotted it",
        "recovery": "the field released them when their engines matched the calm rhythm",
        "ending": "the hollow rocks rang a friendly farewell, each bell softer than the last",
        "lesson": "The most useful signal is not always the loudest one",
    },
    {
        "title": "the upside-down star chart",
        "place": "a crossing where north and south markers had been swapped",
        "signal": "a tune that repeated backward every other time",
        "wrong": "trusted the old chart without comparing it to the changing melody",
        "setback": "the ship reached an empty picnic station after its kitchen had closed",
        "clue": "the broadcast alternated 'avanti' and 'indietro,' meaning 'forward' and 'backward'",
        "meaning": "Turn the chart around whenever the melody reverses",
        "action": "rotated the chart, hummed each direction aloud, and checked every turn with the station lights",
        "recovery": "a caretaker reopened the little kitchen after hearing why the crew was late",
        "ending": "warm rolls steamed beside the window as the corrected chart pointed home",
        "lesson": "Plans should be checked when the world no longer matches the map",
    },
    {
        "title": "the migrating starwhales",
        "place": "a protected crossing used by enormous starwhales",
        "signal": "a low mandolin phrase repeated beneath whale song",
        "wrong": "mistook the whale song for permission to cross and entered the waiting zone",
        "setback": "a patrol asked the ship to dock, so the crew missed the festival's opening lanterns",
        "clue": "the Italian message repeated 'aspettate,' which means 'please wait'",
        "meaning": "Wait through three complete phrases before navigating behind the herd",
        "action": "counted three phrases together, dimmed the engines, and gave the animals plenty of room",
        "recovery": "the patrol then escorted the patient crew along a safe wake",
        "ending": "the last starwhale lifted a shining fin while distant festival lanterns came into view",
        "lesson": "Arriving later is worthwhile when waiting protects someone else's path",
    },
    {
        "title": "the clockwork repair ring",
        "place": "a repair ring whose docking arms moved like clock hands",
        "signal": "twelve plucked notes followed by the word 'sette'",
        "wrong": "heard 'sette' as 'seven turns' and circled until the docking appointment ended",
        "setback": "the ring switched off its welcoming lights and the ship had to spend the night outside",
        "clue": "in this instruction, 'sette' named docking arm seven",
        "meaning": "Navigate to arm seven when the seventh note repeats",
        "action": "numbered the mandolin notes, called the ring to confirm the translation, and approached arm seven slowly",
        "recovery": "the morning mechanic honored the missed appointment after seeing their careful notes",
        "ending": "the repaired ship reflected twelve neat lights as the docking arms folded away",
        "lesson": "Asking for confirmation can repair a misunderstanding before it grows",
    },
    {
        "title": "the paper-star library",
        "place": "an orbiting library marked by folded paper stars",
        "signal": "a nursery melody repeated in four different keys",
        "wrong": "followed the first key each time and arrived at the returns chute instead of the entrance",
        "setback": "the library doors closed, and the crew could not attend that night's story circle",
        "clue": "the final Italian line said 'l'ultima tonalita,' meaning 'the last key'",
        "meaning": "Use only the fourth version of the melody to find the entrance",
        "action": "listened through every repetition, copied the fourth key on the mandolin, and followed its paper stars",
        "recovery": "the librarian invited them to the morning story circle and saved their seats",
        "ending": "paper stars spun over the breakfast table while children opened the first book",
        "lesson": "Patience can reveal the one detail that repetition changes",
    },
    {
        "title": "the solar-kite harbor",
        "place": "a harbor crowded with bright solar kites",
        "signal": "a clipped dance tune interrupted by harbor whistles",
        "wrong": "turned at every whistle and tangled the ship's harmless guide ribbon around an empty buoy",
        "setback": "the ribbon tore, so their place in the welcoming parade went to another ship",
        "clue": "the repeated phrase 'solo corde' meant 'strings only'",
        "meaning": "Navigate by mandolin strings and disregard the whistles",
        "action": "untied the ribbon, offered the buoy keeper an apology, and followed only the string notes",
        "recovery": "the harbor gave them a quieter place leading the cleanup boats instead",
        "ending": "their mended ribbon fluttered above a spotless wake while solar kites filled the sky",
        "lesson": "A changed plan can still become a happy ending when people make amends",
    },
    {
        "title": "the firefly nebula",
        "place": "a dark nebula dotted with firefly-like lights",
        "signal": "one mandolin chord repeated at uneven intervals",
        "wrong": "rushed toward each flash without measuring the time between chords",
        "setback": "the ship used its spare fuel and had to cancel a promised moon-side picnic",
        "clue": "the Italian numbers in the message counted seconds between safe flashes",
        "meaning": "Wait the named number of seconds, then navigate to the next light",
        "action": "translated each number, counted together, and used the mandolin chord to begin every wait",
        "recovery": "the measured route saved enough power to reach a nearby observation deck",
        "ending": "the crew shared their picnic indoors while the whole nebula blinked beyond the glass",
        "lesson": "A disappointment can lead to a different joy when a crew responds thoughtfully",
    },
]


TELLING_MODES = [
    ("The navigation log began with a confident flourish.", "Only after checking the evidence did the crew understand the turn."),
    ("At first, the voyage sounded as neat as a practiced song.", "The mistake made the next careful choice matter."),
    ("The trouble announced itself before anyone saw it.", "Instead of guessing again, the crew compared sound, map, and meaning."),
    ("A quiet trip became a puzzle in the space of one chord.", "The pause gave both crew members time to challenge their first idea."),
    ("The chart promised an easy crossing, but the radio disagreed.", "They treated the setback as evidence rather than defeat."),
    ("From the cockpit window, the route looked almost ordinary.", "One translated phrase changed how they read the whole route."),
    ("The mandolin message arrived before the destination appeared.", "Working aloud kept either crew member from making the next decision alone."),
    ("This voyage was remembered for the instruction nobody understood at first.", "Once the pattern had a meaning, repetition became useful."),
    ("The crew expected a map, not music.", "Their second plan began with listening instead of steering."),
    ("Long afterward, the crew could still hum the tune that delayed them.", "What rescued the journey was not luck but a better test."),
]


# ---------------------------------------------------------------------------
# Narrative instruments: repetition, bad ending, happy ending
# ---------------------------------------------------------------------------
@dataclass
class Repetition:
    signal: str = "mandolin"
    language: str = "italian"
    count: int = 0


@dataclass
class BadEnding:
    drift: int = 0
    stuck: bool = False


@dataclass
class HappyEnding:
    course_fixed: bool = False
    song_solved: bool = False


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def _setup(world: World, params: StoryParams) -> None:
    pilot = world.add(Entity(id=params.name, kind="character", type=params.pilot_type, label=params.name))
    partner = world.add(Entity(id=params.partner_name, kind="character", type=params.partner_type, label=params.partner_name))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label=params.ship_name, phrase=params.ship_name))
    radio = world.add(Entity(id="radio", kind="thing", type="radio", label="radio"))
    score = world.add(Entity(id="mandolin", kind="thing", type="instrument", label="mandolin"))
    chart = world.add(Entity(id="chart", kind="thing", type="chart", label="star chart"))

    pilot.meters["courage"] = 1.0
    pilot.memes["worry"] = 0.0
    partner.meters["skill"] = 1.0
    ship.meters["fuel"] = 3.0
    ship.meters["drift"] = 0.0
    radio.memes["signal"] = 0.0
    score.meters["strings"] = 1.0
    chart.meters["stars"] = 1.0

    world.facts.update(pilot=pilot, partner=partner, ship=ship, radio=radio, score=score, chart=chart)


def _selection_token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.name}|{params.partner_name}|{params.ship_name}"
    return sum((i + 1) * ord(char) for i, char in enumerate(text))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    rep = Repetition()
    bad = BadEnding()
    happy = HappyEnding()

    pilot = world.facts["pilot"]
    partner = world.facts["partner"]
    ship = world.facts["ship"]
    radio = world.facts["radio"]
    token = _selection_token(params)
    incident = INCIDENTS[token % len(INCIDENTS)]
    mode = TELLING_MODES[(token // len(INCIDENTS)) % len(TELLING_MODES)]

    world.say(mode[0])
    world.say(
        f"{pilot.id} and {partner.id} flew {ship.label} toward {incident['place']}, "
        f"where they had to navigate without disturbing nearby travelers."
    )
    world.say(
        f"The radio repeated {incident['signal']} on a mandolin, followed by calm instructions in Italian. "
        "Neither crew member knew enough Italian to trust a quick guess."
    )

    world.para()
    world.say(
        f"Again came {incident['signal']}; again came the Italian message. "
        f"After the third repetition, {pilot.id} {incident['wrong']}."
    )
    world.say(
        f'"This route is not matching our chart," {partner.id} said. '
        f'"Stop safely, and let us find out why."'
    )
    world.say(mode[1])

    world.para()
    world.say(f"The result was disappointing but nobody was hurt: {incident['setback']}.")
    world.say(
        "If the story had stopped there, it would have been a bad ending. "
        "The crew had made a real mistake, and wishing could not undo its consequence."
    )

    world.para()
    world.say(
        f"They replayed the recording slowly and consulted the ship's Italian phrase guide. "
        f"The useful clue was that {incident['clue']}."
    )
    world.say(f'"The whole instruction means: {incident["meaning"]}," {partner.id} explained.')
    world.say(
        f"This time {pilot.id} and {partner.id} {incident['action']}. "
        "They repeated the translated plan to each other before touching the controls."
    )

    world.para()
    world.say(f"Their careful change worked: {incident['recovery']}.")
    world.say(
        f'"Next time, we translate first and navigate second," {pilot.id} said. '
        f'"And we listen for what changes inside the repetition," {partner.id} replied.'
    )
    world.say(f"{incident['lesson']}.")
    world.say(f"The voyage found a happy ending: {incident['ending']}.")

    rep.count = 4
    radio.memes["signal"] = float(rep.count)
    bad.drift = 1
    bad.stuck = True
    ship.meters["drift"] = 0
    ship.meters["fuel"] = 2
    pilot.memes["worry"] = 0
    happy.song_solved = True
    happy.course_fixed = True
    world.facts.update(
        rep=rep,
        bad=bad,
        happy=happy,
        params=params,
        incident=incident,
        incident_index=token % len(INCIDENTS),
        mode_index=(token // len(INCIDENTS)) % len(TELLING_MODES),
    )
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story() -> bool:
    return True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a child-friendly space adventure about {incident['title']}, a repeated mandolin signal, and an Italian navigation message.",
        f"Tell how {p.name} and {p.partner_name} make the mistake '{incident['wrong']}', accept its consequence, and solve the route together.",
        f"Write a story in which a possible bad ending at {incident['place']} becomes a happy ending through translation, careful repetition, and navigation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    pilot = world.facts["pilot"]
    partner = world.facts["partner"]
    ship = world.facts["ship"]
    incident = world.facts["incident"]

    return [
        QAItem(
            question=f"What did {pilot.id} and {partner.id} have to do with {p.ship_name}?",
            answer=f"They had to navigate {p.ship_name} through {incident['place']} without disturbing nearby travelers.",
        ),
        QAItem(
            question="What mistake did the crew make after hearing the repeated signal?",
            answer=f"They {incident['wrong']}. The repeated music was not enough without an accurate translation of the Italian message.",
        ),
        QAItem(
            question="What made the first ending bad?",
            answer=f"{incident['setback'].capitalize()}. Nobody was hurt, but the crew had to accept that disappointing consequence.",
        ),
        QAItem(
            question="Which clue helped the crew understand the Italian directions?",
            answer=f"They discovered that {incident['clue']}. That clue changed how they understood the repeated mandolin signal.",
        ),
        QAItem(
            question="How did the crew repair its navigation plan?",
            answer=f"{pilot.id} and {partner.id} {incident['action']}. Their careful change worked because {incident['recovery']}.",
        ),
        QAItem(
            question="How could the story have both a bad ending and a happy ending?",
            answer=f"The bad ending was a real but non-cruel setback: {incident['setback']}. The later happy ending came after the crew learned that {incident['lesson'].lower()}.",
        ),
        QAItem(
            question=f"What final image showed that the voyage of {ship.label} ended happily?",
            answer=f"At the end, {incident['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mandolin?",
            answer="A mandolin is a small stringed instrument that makes a bright, plucky sound when someone strums it.",
        ),
        QAItem(
            question="What does it mean to navigate?",
            answer="To navigate means to find a safe path from one place to another, especially when the way is tricky.",
        ),
        QAItem(
            question="What is Italian?",
            answer="Italian is a language people speak in Italy and in many other places, and it has its own words and sounds.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A crew is confused when the signal repeats and the message language is Italian.
confused_story(S) :- repeats(S), italian_message(S).

% A bad ending happens when the ship is stuck after a wrong navigation choice.
bad_ending(S) :- confused_story(S), wrong_turn(S), ship_stuck(S).

% A happy ending happens when the message is translated and the course is fixed.
happy_ending(S) :- translated(S), course_fixed(S).

% A valid story needs both endings in sequence.
valid_story(S) :- bad_ending(S), happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("repeats", "story1"),
        asp.fact("italian_message", "story1"),
        asp.fact("wrong_turn", "story1"),
        asp.fact("ship_stuck", "story1"),
        asp.fact("translated", "story1"),
        asp.fact("course_fixed", "story1"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("story1",)} if valid_story() else set()
    if atoms == py:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(atoms))
    print("Python:", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about mandolin repetition, Italian instructions, and navigation.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--partner-name", choices=NAMES)
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
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
    name = args.name or rng.choice(NAMES)
    partner = args.partner_name or rng.choice([n for n in NAMES if n != name])
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    return StoryParams(seed=None, name=name, partner_name=partner, ship_name=ship)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Mina", partner_name="Nico", ship_name="the Comet Lily"),
    StoryParams(name="Aria", partner_name="Elio", ship_name="the Star Lantern"),
    StoryParams(name="Theo", partner_name="Pia", ship_name="the Blue Orbit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
