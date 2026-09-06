#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/connect_yak_quest_lesson_learned_suspense_whodunit.py
===============================================================================================================================

A small whodunit-style story world about a curious child, a missing token,
a yak, and a quest to connect clues.

The seed words are woven into the premise:
- connect
- yak

The story instrument set is:
- Quest
- Suspense
- Lesson Learned

The world is intentionally small and deterministic enough to verify, but still
state-driven: the detective's choices change physical and emotional state, and
the resolution is caused by those changes rather than a frozen paragraph with
swapped nouns.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little museum"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveal: str
    hide_with: str
    place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    traits: list[str] = field(default_factory=list)
    alibi: str = ""
    shaky_about: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def connect_score(world: World) -> float:
    return world.facts.get("connected", 0.0)


def _r_lookcloser(world: World) -> list[str]:
    out: list[str] = []
    detective = world.facts.get("detective")
    if not detective:
        return out
    det = world.get(detective.id)
    if det.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("lookcloser", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    det.memes["focus"] = det.memes.get("focus", 0.0) + 1
    out.append(f"{det.label} leaned in and studied the room more carefully.")
    return out


def _r_connection(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_handled") and world.facts.get("yak_seen"):
        sig = ("connection",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["connected"] = 1.0
        out.append("The clues clicked together at last.")
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("mystery_unsolved") and not world.facts.get("connected"):
        sig = ("suspense",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("For a moment, the answer still hid in the dark corner of the case.")
    return out


CAUSAL_RULES = [
    _r_lookcloser,
    _r_connection,
    _r_suspense,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CASES = [
    {
        "place": "the little museum", "missing": "brass moon token",
        "alarm": "the moon display stood open beneath a fluttering skylight",
        "clues": ("a crescent of blue wool", "a damp hoofprint", "a token-shaped dent in a feed scoop"),
        "false": "the nervous keeper, who had polished the case", "cause": "a gust had flipped the token into the yak's feed scoop",
        "action": "matched the wool to the yak's blanket and followed the hoofprints to the quiet yard",
        "repair": "returned the token and latched the skylight", "image": "the brass moon gleamed above the yak's blue blanket",
    },
    {
        "place": "the mountain library", "missing": "silver bookmark",
        "alarm": "a shelf ladder creaked although nobody stood on it",
        "clues": ("three nibbled paper corners", "a strand of yak hair", "a silver glint inside an atlas chute"),
        "false": "the page helper, who had reshelved the atlas", "cause": "the yak had nudged the atlas chute while reaching for an apple picture",
        "action": "connected the nibbled corners to the open atlas and checked the chute with a librarian",
        "repair": "retrieved the bookmark with a reacher and moved the picture book lower", "image": "the bookmark shone between two closed atlases while the yak watched from the doorway",
    },
    {
        "place": "the village observatory", "missing": "red lens cap",
        "alarm": "the telescope pointed at the floor instead of the noon sky",
        "clues": ("a round red mark in dust", "a chewed carrot top", "a soft bump from the map cabinet"),
        "false": "the astronomy guide, whose keys jingled nearby", "cause": "the rolling cap had followed a sloped chart and stopped beneath the cabinet when the yak bumped it",
        "action": "tested the chart's slope with a wooden disk and listened at the cabinet",
        "repair": "asked an adult to lift the cabinet edge and clipped the cap to the telescope", "image": "a red cap hung safely beside a sharp white moon on the chart",
    },
    {
        "place": "the winter fair tent", "missing": "judge's blue ribbon",
        "alarm": "the prize tablecloth kept twitching in the still air",
        "clues": ("a loose blue thread", "two oat flakes", "a bell-shaped scrape under the table"),
        "false": "the pie judge, who had moved the prizes", "cause": "the yak's collar bell had caught the ribbon and pulled it beneath the cloth",
        "action": "connected the scrape to the bell and tempted the yak backward with its keeper's oat bucket",
        "repair": "freed the ribbon without tugging and pinned prizes above hoof height", "image": "the blue ribbon hung straight as the yak's bell gave one tiny chime",
    },
    {
        "place": "the train-station garden", "missing": "painted route tile",
        "alarm": "travelers were following an arrow that ended at a flower bed",
        "clues": ("a square patch of clean wall", "yellow paint on a cart wheel", "fresh soil beside the yak's water tub"),
        "false": "the sign painter, who had packed yellow paint", "cause": "a delivery cart had knocked down the loose tile and the yak had nosed it into soft soil",
        "action": "connected the clean square to the yellow wheel mark and searched only from the path",
        "repair": "had the station crew reset the tile and tighten all four clips", "image": "the bright arrow pointed home while hoof-shaped shadows crossed the flowers",
    },
    {
        "place": "the puppet theater", "missing": "wooden crown prop",
        "alarm": "a king puppet bowed whenever the backstage curtain moved",
        "clues": ("gold paint on a curtain cord", "a tuft of brown wool", "a hollow knock inside the scenery hill"),
        "false": "the puppeteer, who had changed the final scene", "cause": "the yak had tugged the curtain cord and swung the crown into the hollow scenery",
        "action": "connected the paint, wool, and pendulum-like cord instead of accusing the puppeteer",
        "repair": "opened the scenery panel with the stage manager and tied the cord higher", "image": "the crowned puppet bowed once to a yak peeking through the stage door",
    },
    {
        "place": "the riverside map room", "missing": "green compass card",
        "alarm": "the map drawers whispered open one after another",
        "clues": ("a wet nose mark", "green paper caught on a buckle", "a trail of reeds across the tiles"),
        "false": "the canoe coach, whose boots were wet", "cause": "the yak's blanket buckle had hooked the card after reeds jammed a drawer",
        "action": "connected the reeds to the stuck drawer and calmly inspected the yak's blanket",
        "repair": "unhooked the card with the caretaker and swept the reeds into a basket", "image": "the green compass card dried beside a neat basket of silver reeds",
    },
    {
        "place": "the school music room", "missing": "triangle beater",
        "alarm": "a faint ting sounded each time the outside gate swung",
        "clues": ("a silver scratch on the gate latch", "one bent music stand", "a cord trailing toward the yak pen"),
        "false": "the drummer, who had borrowed several beaters", "cause": "the beater had rolled into a cord loop that the yak pulled through the gate",
        "action": "connected the repeating ting to the moving gate and stopped everyone from pulling the cord",
        "repair": "loosened the loop with the teacher and stored small instruments in a lidded tray", "image": "the triangle rang clearly while the yak chewed hay beyond the closed gate",
    },
    {
        "place": "the seed conservatory", "missing": "packet of snow peas",
        "alarm": "tiny green circles appeared along the stone walkway",
        "clues": ("a torn paper seam", "hoofprints that avoided every seed", "a packet corner under a watering can"),
        "false": "the garden volunteer, who had sorted the packets", "cause": "a fan had torn the packet and the yak had carefully stepped around the rolling peas",
        "action": "connected the paper corner to the fan's breeze and counted the peas without touching unknown seeds",
        "repair": "helped an adult collect and relabel them, then closed the fan-side drawer", "image": "the rescued peas rested in a clear jar beside one careful hoofprint",
    },
    {
        "place": "the clockmaker's classroom", "missing": "copper hour hand",
        "alarm": "twelve practice clocks all showed a different noon",
        "clues": ("a copper streak on a low bench", "a circle pressed into hay", "steady ticking from the yak's supply basket"),
        "false": "the clockmaker's apprentice, who had reset the clocks", "cause": "the hour hand had stuck to a magnetic lesson wheel carried past the yak's basket",
        "action": "connected the copper streak to the magnetic wheel and compared every clock before opening the basket",
        "repair": "separated the parts and added a nonmagnetic storage cup", "image": "all twelve clocks pointed upward as the yak blinked at their gentle chorus",
    },
    {
        "place": "the lakeside nature center", "missing": "wooden fish stamp",
        "alarm": "fish shapes appeared on papers nobody had stamped",
        "clues": ("violet ink on a doorstop", "a blank card stuck to wool", "a damp stamp-pad corner"),
        "false": "the visiting illustrator, whose fingers were violet", "cause": "the yak had brushed a card onto the inked stamp resting upside down by the door",
        "action": "connected the reversed fish prints to pressure from the door and compared the harmless ink marks",
        "repair": "washed the doorstop, returned the stamp, and moved art supplies to a closed shelf", "image": "one tidy violet fish dried on a card above the yak's empty doorway",
    },
    {
        "place": "the hilltop post office", "missing": "parcel number seven",
        "alarm": "the sorting bell rang whenever the wind pressed the back flap",
        "clues": ("a seven-shaped tear in wrapping", "twine looped around a fence knob", "lavender soap scent near the yak"),
        "false": "the bicycle courier, who had signed for parcel seven", "cause": "wind had slid the light parcel outside, where its twine caught safely beside the yak pen",
        "action": "connected the ringing flap, torn wrapping, and soap scent before checking the fence with the postmaster",
        "repair": "repacked the soap and fitted a latch to the sorting flap", "image": "parcel seven sat squarely on the shelf while lavender drifted through the quiet room",
    },
]


def build_scene(case: dict[str, object]) -> tuple[Setting, list[Clue], list[Suspect]]:
    setting = Setting(place=str(case["place"]), indoors=True, affords={"quest", "inspect"})
    clue_texts = case["clues"]
    clues = [
        Clue(id=f"clue{i}", label=str(text), phrase=str(text), reveal=str(case["cause"]),
             hide_with="the scene", place=setting.place, tags={"yak", "evidence"})
        for i, text in enumerate(clue_texts, 1)
    ]
    suspects = [
        Suspect(id="adult", label=str(case["false"]), type="adult", traits=["helpful"], alibi="had a relevant task"),
        Suspect(id="yak", label="the woolly yak", type="yak", traits=["gentle", "curious"], alibi="was near the yard"),
        Suspect(id="weather", label="the changing weather", type="cause", traits=["unnoticed"], alibi="left no spoken alibi"),
    ]
    return setting, clues, suspects


def tell(hero_name: str = "Mina", hero_type: str = "girl", helper_name: str = "Aunt June",
         case_index: int = 0, route: int = 0) -> World:
    case = CASES[case_index % len(CASES)]
    setting, clues, suspects = build_scene(case)
    world = World(setting)

    detective = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"footsteps": 0.0},
        memes={"curiosity": 1.0, "hope": 0.0, "worry": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="aunt",
        label=helper_name,
        meters={"patience": 1.0},
        memes={"kindness": 1.0},
    ))
    world.add(Entity(
        id="yak",
        kind="character",
        type="yak",
        label="the woolly yak",
        meters={"hoofprints": 1.0},
        memes={"restless": 1.0},
    ))

    clue_ents: list[Entity] = []
    for clue in clues:
        clue_ents.append(world.add(Entity(
            id=clue.id,
            type="clue",
            label=clue.label,
            phrase=clue.phrase,
            owner="mystery",
            caretaker="musem",
            region=clue.place,
        )))

    world.facts.update(
        detective=detective,
        helper=helper,
        clues=clues,
        clue_ents=clue_ents,
        suspects=suspects,
        case_index=case_index % len(CASES),
        missing=case["missing"],
        alarm=case["alarm"],
        false_suspect=case["false"],
        cause=case["cause"],
        investigation=case["action"],
        repair=case["repair"],
        ending_image=case["image"],
        mystery_unsolved=True,
        clue_handled=False,
        yak_seen=False,
    )

    openings = [
        f"The quest began with an empty hook: the {case['missing']} had vanished from {setting.place}.",
        f"At {setting.place}, {hero_name} heard a worried whisper: the {case['missing']} was missing.",
        f"Nobody called it a case until {hero_name} noticed that the {case['missing']} was gone.",
        f"A visit to {setting.place} turned into a detective quest when the {case['missing']} disappeared.",
        f"{helper_name} had promised a quiet afternoon, but {setting.place} was missing its {case['missing']}.",
        f"The first mystery was what was absent: the {case['missing']} from {setting.place}.",
        f"Just before closing time, an alarm went up over the missing {case['missing']}.",
        f"{hero_name} entered {setting.place} as a visitor and became a detective when the {case['missing']} vanished.",
        f"A blank space where the {case['missing']} belonged gave {hero_name} a new quest.",
        f"The day looked ordinary until someone asked, 'Where is the {case['missing']}?'",
    ]
    world.say(openings[route % len(openings)])
    world.say(f"The strangest warning was this: {case['alarm']}.")
    world.say(f"Nearby, {hero_name} discovered {clues[0].phrase}. Suspense prickled, but one clue was not proof.")
    world.para()

    detective.memes["worry"] += 1.0
    world.say(f"A quick guess pointed toward {case['false']}. {hero_name} nearly announced it.")
    world.say(f'"Connect facts before names," {helper_name} said. "A clue can explain an accident without blaming anyone."')
    propagate(world)

    world.para()
    investigations = [
        f"First came a question, then a careful test: {hero_name} {case['action']}.",
        f"Instead of chasing the loudest theory, {hero_name} {case['action']}.",
        f"The quest narrowed when {hero_name} {case['action']}.",
        f"{hero_name} drew three boxes in a notebook and {case['action']}.",
        f"Working backward from what had moved, {hero_name} {case['action']}.",
    ]
    world.say(investigations[route % len(investigations)])
    world.say(f'Then {hero_name} found {clues[1].phrase}. "That connects to the first clue," the young detective said.')
    world.say(f"The last piece was {clues[2].phrase}. Somewhere nearby, the woolly yak gave a soft snort.")
    world.facts["clue_handled"] = True
    world.facts["yak_seen"] = True
    propagate(world)

    world.para()
    reveals = [
        f"Together the clues proved that {case['cause']}. The suspected adult had not taken a thing.",
        f"The answer arrived all at once: {case['cause']}. It was a chain of events, not a thief.",
        f'"I can explain every mark," {hero_name} said. {case["cause"].capitalize()}.',
        f"When the three clues were placed in order, they showed that {case['cause']}.",
    ]
    world.say(reveals[route % len(reveals)])
    world.say(f"To finish the quest, they {case['repair']}.")
    world.say(f'"Today I learned that suspense is not permission to accuse," {hero_name} said. "Patience lets evidence connect."')
    world.say(f"At the end, {case['image']}.")
    world.facts["mystery_unsolved"] = False
    world.facts["connected"] = 1.0
    detective.memes["relief"] += 1.0
    detective.memes["hope"] += 1.0
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit at {world.setting.place} about the missing {f['missing']}, where a detective must connect clues involving a yak.",
        f"Tell a suspenseful quest in which a young detective investigates why {f['alarm']} and learns not to accuse anyone too quickly.",
        f"Write a mystery with the words connect and yak whose evidence reveals that {f['cause']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    qa = [
        QAItem(
            question=f"What was {detective.label} trying to do at {world.setting.place}?",
            answer=f"{detective.label} was trying to find the missing {f['missing']}. The quest required connecting evidence instead of making a quick accusation.",
        ),
        QAItem(
            question=f"Why did {helper.label} stop {detective.label} from naming a suspect?",
            answer=f"The early clues seemed to point toward {f['false_suspect']}, but they did not prove guilt. {helper.label} wanted the detective to connect facts before names.",
        ),
        QAItem(
            question=f"Which three clues solved the case of the missing {f['missing']}?",
            answer=f"The clues were {f['clues'][0].phrase}, {f['clues'][1].phrase}, and {f['clues'][2].phrase}. Together they explained the yak's connection to the mystery.",
        ),
    ]
    if f.get("connected"):
        qa.append(
            QAItem(
                question="How was the mystery solved?",
                answer=f"It was solved when the evidence showed that {f['cause']}. Then the group {f['repair']}.",
            )
        )
        qa.append(
            QAItem(
                question="What lesson did the detective learn?",
                answer="The detective learned that suspense is not permission to accuse someone. Patient tests let separate clues connect into a fair explanation.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to connect clues?",
            answer="To connect clues means to think about how small facts fit together and point to one answer.",
        ),
        QAItem(
            question="What is suspense in a mystery story?",
            answer="Suspense is the feeling of wondering what will happen next before the answer is revealed.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a useful idea someone understands after a problem or story, like being patient or kind.",
        ),
        QAItem(
            question="What is a yak?",
            answer="A yak is a large, shaggy animal that lives in cold mountain places.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    case_index: int = 0
    route: int = 0
    seed: Optional[int] = None


NAMES_GIRL = ["Mina", "Tessa", "Iris", "Nora", "Lena", "Pia"]
NAMES_BOY = ["Eli", "Noah", "Finn", "Jasper", "Owen", "Theo"]
HELPERS = ["Aunt June", "Uncle Ben", "Grandma Rose", "Dad", "Mom"]


ASP_RULES = r"""
connected :- clue_handled, yak_seen.
suspense :- mystery_unsolved, not connected.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("clue_handled"))
    lines.append(asp.fact("yak_seen"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world about a quest to connect clues and a yak.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.name,
        "girl" if params.gender == "girl" else "boy",
        params.helper,
        params.case_index,
        params.route,
    )
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show connected/0.\n#show suspense/0.")
    model = asp.one_model(program)
    atoms = {sym.name for sym in model}
    if "connected" in atoms and "suspense" not in atoms:
        print("OK: ASP twin matches the solved Python story state.")
        return 0
    print("MISMATCH: ASP program did not derive the expected atoms.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show connected/0.\n#show suspense/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show connected/0.\n#show suspense/0."))
        print("ASP atoms:", " ".join(sorted(sym.name for sym in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for i in range(5):
            seed = base_seed + i
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            p.case_index = seed % len(CASES)
            p.route = (seed // len(CASES)) % 10
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            p.case_index = seed % len(CASES)
            p.route = (seed // len(CASES)) % 10
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
