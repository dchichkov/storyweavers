#!/usr/bin/env python3
"""
storyworlds/worlds/switch_checker_conflict_detective_story.py
=============================================================

A compact detective-style storyworld about a switch, a checker, and a conflict.

Premise:
A careful checker notices that an important switch is in the wrong position.
That causes a small conflict: lights, signs, or sounds stop behaving as they
should, and the detective has to figure out who moved it.

World model:
- Physical meters track the switch position and the state of the place.
- Emotional memes track suspicion, worry, conflict, relief, and pride.
- The story is driven by simulated state, not by a frozen template.

The story is deliberately small and classical:
beginning -> clue -> conflict -> resolution -> closing image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    dark_when_off: bool = False


@dataclass
class StoryParams:
    place: str
    detector: str
    checker: str
    switch_name: str
    switch_kind: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    problem: str
    consequence: str
    clue: str
    false_lead: str
    test: str
    cause: str
    repair: str
    lesson: str
    ending: str


INCIDENTS = [
    Incident(
        "a book cart stood crooked beside the wall",
        "the reading lamps blinked out while a child was choosing a book",
        "a curved chalk mark crossed the floor beside one cart wheel",
        "a cold draft from the door",
        "rolled the cart back along the chalk curve without touching the lever",
        "the cart's loose wheel had swung wide and nudged the switch down",
        "tightened the wheel and marked a safe parking line",
        "A good detective tests a clue before blaming anyone.",
        "a row of open books shone beneath steady lamps",
    ),
    Incident(
        "a costume cape hung from a peg near the panel",
        "the rehearsal sign vanished just before the youngest actors entered",
        "one blue thread curled around the switch",
        "the caretaker who had locked the prop cupboard",
        "lifted the cape slowly and watched its long hem sweep the wall",
        "the cape had snagged the lever when someone carried it past",
        "moved the costume peg and shortened the dangling loop",
        "Evidence can settle a conflict more kindly than a quick accusation.",
        "the blue cape hung safely while the rehearsal sign glowed",
    ),
    Incident(
        "a parcel waited below the control panel",
        "the welcome display went dark as families arrived",
        "a clean square remained in the dust around the parcel",
        "a cat whose pawprints ended far from the wall",
        "matched the parcel's upper corner to the square beside the lever",
        "the tall parcel had tipped against the switch before sliding upright",
        "laid the parcel flat and added a low delivery shelf",
        "Shapes and positions can tell a story when witnesses cannot.",
        "the bright welcome display reflected in the parcel's silver tape",
    ),
    Incident(
        "a paper label lay face-down under the switch",
        "the direction arrows stopped glowing and two visitors chose opposite paths",
        "a curl of sticky backing clung to the lever",
        "a prank by one of the visitors",
        "held the fallen label against the wall and followed its bent corner",
        "the label had peeled loose and dragged the switch down as it fell",
        "cleaned the wall and fastened a new label away from the controls",
        "Small physical clues are stronger than exciting guesses.",
        "fresh arrows pointed the same way across the bright floor",
    ),
    Incident(
        "a festival poster flapped beside an open window",
        "the colored lanterns went out in the middle of decorating",
        "the poster's torn corner carried a gray streak shaped like the lever",
        "a late visitor seen near the window",
        "asked the checker to fan the poster while watching its corner",
        "a gust had slapped the poster across the switch",
        "closed the window halfway and pinned all four poster corners",
        "Recreating an event can reveal a harmless cause.",
        "colored lanterns glimmered over a poster that no longer fluttered",
    ),
    Incident(
        "a cleaning cloth rested on a hook above the panel",
        "the safety light went dark during the checker's final round",
        "a yellow fiber and a faint lemon scent remained on the lever",
        "the cleaner, who seemed to have touched the controls on purpose",
        "compared the fiber with the cloth and measured how far it could swing",
        "the damp cloth had sagged from its hook and caught the switch",
        "placed the hook lower and farther from the panel",
        "A clue may identify an object without proving a person's intent.",
        "the folded cloth dried on its new hook under a calm green light",
    ),
    Incident(
        "a model train rattled on a display table",
        "the station clock and platform lights stopped together",
        "the switch trembled each time the train crossed one loose rail joint",
        "someone secretly flicking the control between train laps",
        "set a coin beside the lever and watched it quiver with each passing car",
        "repeated vibration had shaken a worn switch downward",
        "tightened the rail joint and fitted a firm guard around the lever",
        "Patterns repeated in time can expose a mechanical cause.",
        "the little train circled beneath a clock ticking exactly on time",
    ),
    Incident(
        "three beanbags were piled too high near the wall",
        "the game scoreboard went blank during a close final round",
        "green threads on the switch matched a split beanbag seam",
        "the losing team trying to erase the score",
        "stacked the beanbags again and gently tapped the bottom one",
        "the top beanbag had tumbled against the switch",
        "sewed the split seam and stored the beanbags in a floor basket",
        "Fair solutions come from checking evidence, especially during conflict.",
        "both teams cheered beneath the restored score as the beanbags sat snug below",
    ),
    Incident(
        "a puppet theater had been rolled beside the wall",
        "the tiny stage lamps failed before the final scene",
        "a red puppet string was looped loosely around the lever",
        "the puppeteer forgetting to turn the lights on",
        "pulled the theater back inch by inch and traced the string's path",
        "the trailing string had tugged the switch off when the theater moved",
        "coiled every string and painted a parking mark for the theater",
        "Tracing a clue backward can uncover the whole chain of events.",
        "a red dragon puppet bowed in a circle of golden stage light",
    ),
    Incident(
        "a silver kite tail poked through a high window",
        "the weather signal disappeared while rain clouds gathered",
        "a narrow silver ribbon was pinched beneath the switch",
        "a bird fluttering outside the glass",
        "loosened the ribbon and followed it from the lever to the window latch",
        "the wind had pulled the kite tail tight enough to lower the switch",
        "freed the kite, shut the window, and checked the weather lamp",
        "Following a clue from end to end prevents a mystery from becoming a quarrel.",
        "the weather lamp glowed amber as the rescued kite rested by the door",
    ),
    Incident(
        "the checker's clipboard leaned beneath the panel",
        "the closing bell and hallway light both fell silent",
        "a fresh brass-colored dent marked the clipboard's top clip",
        "a hurried messenger who had passed moments earlier",
        "lined up the dent with the lever and replayed the checker's last turn",
        "the checker had accidentally bumped the switch while writing a note",
        "hung the clipboard on the opposite wall and corrected the record",
        "Admitting your own mistake is part of solving a case honestly.",
        "the checker added a truthful final tick beneath the glowing light",
    ),
    Incident(
        "an emergency-practice card sat behind the panel",
        "the ordinary chime stayed silent after the practice ended",
        "the card said OFF FOR PRACTICE, but its bottom line was hidden",
        "a helper ignoring the rules",
        "slid the card free and read the covered instruction aloud",
        "a helper had safely turned the switch off for practice but missed the reminder to restore it",
        "turned it on together and added a bright return-check box to the card",
        "Clear instructions keep responsible actions from causing later confusion.",
        "the completed practice card hung beside a softly shining chime lamp",
    ),
]

OPENINGS = [
    "The case began with a silence that did not belong.",
    "The checker noticed the trouble before anyone else did.",
    "A tiny change turned an ordinary afternoon into a detective story.",
    "Just as the room grew busy, one familiar signal disappeared.",
    "No alarm rang; the first warning was the checker's puzzled face.",
    "The mystery arrived quietly, with one switch pointing the wrong way.",
    "At first the problem looked simple, but the nearby objects told a longer tale.",
    "The detective was halfway through tidying the clue notebook when the checker called.",
]

DISAGREEMENTS = [
    '"We should ask before we accuse," the detective said.',
    '"That guess fits part of the scene, but not every clue," the checker replied.',
    'The checker wanted a quick answer; the detective wanted one careful test.',
    '"A suspicion is a question, not a verdict," the detective reminded them both.',
    'They disagreed about the false lead, then agreed to let the evidence decide.',
    'The conflict sharpened until the checker took a breath and read the clue aloud.',
    '"Let us prove what happened," said the checker, setting blame aside.',
    'For a moment each defended a different theory, and neither theory explained the whole scene.',
]

CLOSING_LEADS = [
    "After they checked their repair twice,",
    "With the mystery recorded in the casebook,",
    "Once apologies had replaced suspicion,",
    "When the restored signal held steady,",
    "Before they put away the magnifying glass,",
    "At closing time,",
    "Their final check found everything working, and",
    "The room settled back into its ordinary rhythm;",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _label(name: str) -> str:
    return name


def _switch_state(world: World) -> str:
    sw = world.get("switch")
    pos = int(sw.meters.get("position", 0))
    return "on" if pos >= THRESHOLD else "off"


def _room_state(world: World) -> str:
    room = world.get("room")
    return "bright" if room.meters.get("bright", 0) >= THRESHOLD else "dark"


def _apply_switch_state(world: World) -> None:
    sw = world.get("switch")
    room = world.get("room")
    if sw.meters.get("position", 0) >= THRESHOLD:
        room.meters["bright"] = 1
    else:
        room.meters["bright"] = 0


def detect_conflict(world: World) -> None:
    checker = world.get("checker")
    detective = world.get("detective")
    sw = world.get("switch")
    room = world.get("room")
    if sw.meters.get("position", 0) < THRESHOLD and room.meters.get("bright", 0) < THRESHOLD:
        checker.memes["worry"] = 1
        detective.memes["suspicion"] = 1
        detective.memes["conflict"] = 1
        checker.memes["conflict"] = 1
        world.fired.add(("conflict",))
        return


def solve_case(world: World) -> None:
    detective = world.get("detective")
    checker = world.get("checker")
    sw = world.get("switch")
    room = world.get("room")
    detective.memes["conflict"] = 0
    checker.memes["conflict"] = 0
    detective.memes["pride"] = 1
    checker.memes["relief"] = 1
    sw.meters["position"] = 1
    room.meters["bright"] = 1
    world.fired.add(("resolved",))


def tell(world: World, params: StoryParams) -> World:
    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum((i + 1) * ord(ch) for i, ch in enumerate(
            f"{params.place}|{params.detector}|{params.checker}|{params.switch_name}|{params.switch_kind}"
        ))
    rng = random.Random(stable_seed ^ 0x5A17C)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    disagreement = rng.choice(DISAGREEMENTS)
    closing_lead = rng.choice(CLOSING_LEADS)
    notice_style = rng.randrange(6)
    search_style = rng.randrange(6)
    solve_style = rng.randrange(6)

    detective = world.add(Entity(id="detective", kind="character", type="boy", label=params.detector))
    checker = world.add(Entity(id="checker", kind="character", type="girl", label=params.checker))
    switch = world.add(Entity(id="switch", type="switch", label=params.switch_name, phrase=params.switch_kind))
    room = world.add(Entity(id="room", type="room", label=params.place))

    switch.meters["position"] = 0
    room.meters["bright"] = 0
    detector_name = detective.label
    checker_name = checker.label

    intros = [
        f"{detector_name}, a young detective, kept a pencil and a folded clue card ready.",
        f"Young detective {detector_name} liked questions that could be tested.",
        f"Whenever a small mystery appeared, detective {detector_name} began by listening.",
        f"{detector_name} was the {params.place}'s patient young detective.",
        f"A magnifying glass was useful, but detective {detector_name} trusted careful experiments more.",
        f"Detective {detector_name} knew that neat answers had to fit every clue.",
    ]
    checker_intros = [
        f"The checker was {checker_name}, who recorded each light, sign, and sound.",
        f"{checker_name}, the day's checker, noticed even the smallest change.",
        f"Beside the checklist stood {checker_name}, a checker who took details seriously.",
        f"Checker {checker_name} made one slow round of the {params.place} each hour.",
        f"The careful checker, {checker_name}, knew how the room should look and sound.",
        f"{checker_name} carried the checker sheet and marked only what could be seen.",
    ]
    world.say(opening)
    world.say(intros[notice_style])
    world.say(checker_intros[(notice_style + rng.randrange(6)) % 6])
    world.say(
        f"Their most important control was a {params.switch_kind} labeled {params.switch_name}."
    )

    world.para()
    problem_leads = [
        f"In the {params.place}, {incident.consequence}.",
        f"Trouble showed itself when {incident.consequence}.",
        f"The checker looked up: {incident.consequence}.",
        f"Without warning, {incident.consequence}.",
        f"The first fact in the case was plain: {incident.consequence}.",
        f"Everyone paused because {incident.consequence}.",
    ]
    world.say(problem_leads[(notice_style + search_style) % 6])
    world.say(
        f"The checker found the {params.switch_name} off; nearby, {incident.problem}."
    )

    detect_conflict(world)
    if checker.memes.get("conflict", 0) >= THRESHOLD:
        conflict_lines = [
            f"Worried, {checker_name} started a conflict by proposing {incident.false_lead} as the cause.",
            f"The conflict began when {checker_name} pointed to {incident.false_lead}.",
            f"Because the problem felt urgent, {checker_name}'s suspicion of {incident.false_lead} caused a conflict.",
            f"{checker_name} insisted on {incident.false_lead}; the detective disagreed, and a conflict began.",
            f"A tense conflict grew around one guess: perhaps it was {incident.false_lead}.",
            f"A conflict shook their teamwork when the checker blamed {incident.false_lead}.",
        ]
        world.say(conflict_lines[solve_style])
    if detective.memes.get("suspicion", 0) >= THRESHOLD:
        world.say(disagreement)

    world.para()
    clue_lines = [
        f"Under a low beam of light, they found their best clue: {incident.clue}.",
        f"They searched from floor to wall until {checker_name} spotted that {incident.clue}.",
        f"Instead of questioning anyone, they sketched the scene and noted that {incident.clue}.",
        f"Three ordinary details led nowhere; then the checker saw that {incident.clue}.",
        f"The detective compared every nearby object with the lever. One fact mattered: {incident.clue}.",
        f"They paused, looked from a new angle, and discovered that {incident.clue}.",
    ]
    test_lines = [
        f"To test it, they {incident.test}.",
        f"Their next step was an experiment: they {incident.test}.",
        f"{detector_name} asked everyone to stand clear while they {incident.test}.",
        f"The checker wrote down what happened as they {incident.test}.",
        f"They predicted what should happen, then {incident.test}.",
        f"Carefully and without causing damage, they {incident.test}.",
    ]
    world.say(clue_lines[search_style])
    world.say(test_lines[(search_style + solve_style) % 6])
    cause_lines = [
        f"The result revealed the full chain: {incident.cause}.",
        f"Now every clue agreed. {incident.cause.capitalize()}.",
        f"That proved no secret culprit was needed; {incident.cause}.",
        f"The false lead fell apart, and the real explanation was clear: {incident.cause}.",
        f"Their test worked exactly once, showing that {incident.cause}.",
        f"{checker_name} crossed out the accusation. The evidence showed that {incident.cause}.",
    ]
    world.say(cause_lines[(notice_style + solve_style) % 6])

    solve_case(world)
    world.para()
    repair_lines = [
        f"Together they flipped the {params.switch_name} on and {incident.repair}.",
        f"After restoring the switch, they {incident.repair} so the trouble would not repeat.",
        f"{checker_name} turned the switch on while {detector_name} {incident.repair}.",
        f"The switch was back on; to prevent a repeat, they {incident.repair}.",
        f"They made the {params.place} bright again and {incident.repair}.",
        f"First came light; next, they {incident.repair}.",
    ]
    world.say(repair_lines[solve_style])
    world.say(f'{detector_name} closed the clue notebook. "{incident.lesson}"')
    world.say(f"{closing_lead} {incident.ending}.")

    world.facts.update(
        detective=detective,
        checker=checker,
        switch=switch,
        room=room,
        place=params.place,
        switch_kind=params.switch_kind,
        incident=incident,
        false_lead=incident.false_lead,
        clue=incident.clue,
        test=incident.test,
        cause=incident.cause,
        repair=incident.repair,
        lesson=incident.lesson,
        consequence=incident.consequence,
        ending=incident.ending,
    )
    return world


PLACES = {
    "hall": Setting(place="the hall"),
    "station": Setting(place="the station"),
    "library": Setting(place="the library"),
    "workshop": Setting(place="the workshop"),
}

SWITCH_KINDS = {
    "lamp switch": "lamp switch",
    "signal switch": "signal switch",
    "power switch": "power switch",
    "panel switch": "panel switch",
}

DETECTOR_NAMES = ["Mina", "Iris", "Theo", "Noah", "Lena", "Owen", "Ruby", "Finn"]
CHECKER_NAMES = ["Pip", "June", "Kit", "Tessa", "Milo", "Nora", "Jules", "Ada"]


ASP_RULES = r"""
% A case is in conflict when the switch is off and the room is dark.
conflict(C) :- switch(C), off(C), dark(C).

% The detective can solve the case if the switch is the only reason for darkness.
solved(C) :- conflict(C), switch(C), checked(C), turned_on(C).

#show conflict/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SWITCH_KINDS:
        lines.append(asp.fact("switch", sid))
        lines.append(asp.fact("checked", sid))
        lines.append(asp.fact("turned_on", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld about a switch, a checker, and a conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--switch-kind", choices=SWITCH_KINDS)
    ap.add_argument("--detector")
    ap.add_argument("--checker")
    ap.add_argument("--switch-name")
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
    place = args.place or rng.choice(list(PLACES))
    switch_kind = args.switch_kind or rng.choice(list(SWITCH_KINDS))
    detector = args.detector or rng.choice(DETECTOR_NAMES)
    checker = args.checker or rng.choice(CHECKER_NAMES)
    switch_name = args.switch_name or rng.choice(["main switch", "big switch", "brass switch", "wall switch"])
    return StoryParams(
        place=place,
        detector=detector,
        checker=checker,
        switch_name=switch_name,
        switch_kind=switch_kind,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child that includes the words "switch" and "checker".',
        f"Tell a gentle mystery where {f['checker'].label} notices that {f['consequence']} and {f['detective'].label} helps solve the conflict.",
        f"Write an evidence-led detective tale set in {f['place']} where the clue is that {f['clue']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = world.facts["detective"]
    c = world.facts["checker"]
    sw = world.facts["switch"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who noticed the problem with the switch in {place}?",
            answer=f"The checker, {c.label}, noticed that the {sw.label} was off after {world.facts['consequence']}.",
        ),
        QAItem(
            question=f"What clue helped {d.label} and {c.label} move beyond their first guess?",
            answer=f"They found that {world.facts['clue']}.",
        ),
        QAItem(
            question=f"What really caused the {sw.label} to turn off?",
            answer=f"They discovered that {world.facts['cause']}.",
        ),
        QAItem(
            question=f"How did the detectives keep the same problem from happening again?",
            answer=f"After restoring the {sw.label}, they {world.facts['repair']}.",
        ),
        QAItem(
            question=f"Why did a conflict arise between {d.label} and {c.label}?",
            answer=f"The urgent problem led them to disagree about {world.facts['false_lead']} before they tested the evidence.",
        ),
        QAItem(
            question="What lesson did the young detectives take from the case?",
            answer=world.facts["lesson"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a switch do?",
            answer="A switch can turn something on or off, like a light or a machine.",
        ),
        QAItem(
            question="What does a checker do?",
            answer="A checker looks carefully for details and notices when something is not right.",
        ),
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks for clues and solves mysteries.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str]]:
    return sorted((place, sw) for place in PLACES for sw in SWITCH_KINDS)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show switch/1.\n#show place/1.\n"))
    return sorted(set(asp.atoms(model, "switch"))), sorted(set(asp.atoms(model, "place")))


def asp_verify() -> int:
    import asp
    # Basic parity check: the ASP facts and Python registry should name the same sets.
    py_places = set(PLACES)
    py_switches = set(SWITCH_KINDS)
    model = asp.one_model(asp_program("#show place/1.\n#show switch/1.\n"))
    asp_places = {a[0] for a in asp.atoms(model, "place")}
    asp_switches = {a[0] for a in asp.atoms(model, "switch")}
    ok = py_places == asp_places and py_switches == asp_switches
    if ok:
        print(f"OK: ASP/Python registry parity ({len(py_places)} places, {len(py_switches)} switches).")
        return 0
    print("MISMATCH:")
    print(" places only in python:", sorted(py_places - asp_places))
    print(" places only in asp:", sorted(asp_places - py_places))
    print(" switches only in python:", sorted(py_switches - asp_switches))
    print(" switches only in asp:", sorted(asp_switches - py_switches))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show switch/1.\n#show place/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show switch/1.\n#show place/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="hall", detector="Mina", checker="Pip", switch_name="main switch", switch_kind="lamp switch"),
            StoryParams(place="station", detector="Theo", checker="June", switch_name="signal switch", switch_kind="signal switch"),
            StoryParams(place="library", detector="Lena", checker="Ada", switch_name="wall switch", switch_kind="power switch"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
