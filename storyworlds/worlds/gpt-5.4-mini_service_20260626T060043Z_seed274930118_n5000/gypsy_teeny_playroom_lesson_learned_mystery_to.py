#!/usr/bin/env python3
"""
Story world: a teeny Romani child's playroom mystery with a tall-tale feel.

Premise:
- A teeny Romani child is in a playroom full of toy props. The source term
  "gypsy" is acknowledged as an old, often hurtful label rather than used as a
  costume, personality, or stereotype.
- A shiny puzzle piece goes missing.
- The child follows clues, but the wrong shortcut leads to a bad ending.
- A lesson is learned: a mystery can be solved best by careful looking and asking for help.

The world is intentionally small and constraint-checked.  It generates one
complete story with a beginning, a middle turn, and a hard-earned ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    label: str
    age_word: str = "teeny"
    role: str = "child"
    meters: dict[str, float] = field(default_factory=lambda: {"location": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "worry": 0.0, "pride": 0.0, "lesson": 0.0})
    traits: list[str] = field(default_factory=list)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Object:
    name: str
    label: str
    kind: str
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"touched": 0.0, "moved": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"value": 0.0})


@dataclass
class World:
    setting: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.name] = ch
        return ch

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.name] = obj
        return obj


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    object_name: str = "glimmer chip"
    helper_name: str = "Auntie"
    culprit_name: str = "wind-up mouse"
    clue_name: str = "blue block"
    setting: str = "playroom"


@dataclass(frozen=True)
class MysteryArc:
    key: str
    premise: str
    clue_detail: str
    mistaken_action: str
    consequence: str
    careful_action: str
    cause: str
    resolution: str
    lesson: str
    ending: str


SETTINGS = {
    "playroom": {
        "place": "the playroom",
        "texture": "bright rugs, toy shelves, and a lopsided little table",
        "affords": {"search", "hide", "play", "ask"},
    }
}

NAMES = ["Mina", "Lina", "Tavi", "Rosa", "Junie", "Pip", "Ivy"]
HELPERS = ["Auntie", "Grandpa", "Mama", "Papa", "Cousin"]
CULPRITS = ["wind-up mouse", "sock monkey", "wooden bear", "rag doll"]
OBJECTS = ["glimmer chip", "gold star token", "tiny brass key", "silver button"]
CLUES = ["blue block", "red scarf", "yellow cup", "striped basket"]
TRAITS = ["bold", "curious", "quick-footed", "bright-eyed", "stubborn", "cheerful"]

MYSTERY_ARCS = [
    MysteryArc(
        key="wobbly_floorboard",
        premise="the dress-up trunk gave a tiny click each time someone crossed the rug",
        clue_detail="a trail of square dents led from the clue toward one springy floorboard",
        mistaken_action="pulled every costume from the trunk, certain the prize was wrapped in a cape",
        consequence="the capes buried the trail and left the trunk lid propped dangerously open",
        careful_action="matched the clue's bent corner to the square dents and pressed each floorboard with one careful finger",
        cause="a loose board had tipped when the toy rolled across it, dropping the prize into a shallow gap",
        resolution="held the board while the helper lifted it safely and recovered the prize",
        lesson="evidence is more useful than the first exciting guess",
        ending="the repaired board lay flat beneath a neat row of bright costumes",
    ),
    MysteryArc(
        key="magnet_wagon",
        premise="a toy wagon kept turning by itself beside the block castle",
        clue_detail="the clue trembled whenever it came near the wagon's painted red wheel",
        mistaken_action="chased the wagon in circles and accused the nearest toy of stealing",
        consequence="the block castle toppled, while the wagon rolled farther from the truth",
        careful_action="asked everyone to stand still and tested the clue near each wheel without touching anything else",
        cause="a craft magnet under the wagon had pulled the metal prize against its axle",
        resolution="slid a wooden ruler beneath the axle and freed the prize without pinching a finger",
        lesson="a fair investigator tests a suspicion before blaming anyone",
        ending="the wagon rested beside a rebuilt castle with the harmless magnet in a labeled cup",
    ),
    MysteryArc(
        key="puppet_pocket",
        premise="the puppet theater whispered whenever its curtain swayed",
        clue_detail="one thread from the clue was caught on the curtain's brass hook",
        mistaken_action="shook every puppet and made their wooden heads knock together",
        consequence="a puppet's hat fell off, but the missing prize did not",
        careful_action="followed the loose thread from hook to curtain to the deep pocket sewn along its hem",
        cause="the toy had bumped the prize off the table and the swaying curtain had scooped it into its pocket",
        resolution="unhooked the curtain with the helper and eased the prize from the hidden pocket",
        lesson="small connected clues can tell a complete story",
        ending="the curtain opened on a puppet bowing beside the recovered prize",
    ),
    MysteryArc(
        key="marble_maze",
        premise="a soft rolling sound traveled beneath the cardboard marble maze",
        clue_detail="a chalky streak matching the clue curved around the maze's last tunnel",
        mistaken_action="tilted the whole maze steeply and shouted for the prize to roll out",
        consequence="the marbles jammed together and hid the sound completely",
        careful_action="drew the tunnel route on paper and opened its numbered flaps in order",
        cause="the toy had nudged the prize into the maze, where it lodged behind two marbles",
        resolution="removed the marbles one at a time until the prize slid into the helper's palm",
        lesson="a complicated problem becomes manageable when it is divided into steps",
        ending="three marbles clicked through the clear maze while the prize gleamed beside the route map",
    ),
    MysteryArc(
        key="shadow_lantern",
        premise="a star-shaped shadow blinked across the ceiling although the paper lantern was still",
        clue_detail="a bright speck on the clue flashed only when the lantern faced the puzzle shelf",
        mistaken_action="switched off every lamp and crawled after the shadow in the dark",
        consequence="the searcher bumped a cushion fort and frightened themself with its collapse",
        careful_action="rebuilt the fort, dimmed one lamp at a time, and traced the reflected beam backward",
        cause="sunlight had struck the prize where the toy left it atop the puzzle shelf",
        resolution="used the helper's step stool and two steady hands to bring the prize down",
        lesson="changing one thing at a time makes a puzzling pattern easier to understand",
        ending="one calm beam made a little star above the tidy cushion fort",
    ),
    MysteryArc(
        key="music_box",
        premise="the music box played one extra plink after its tune had ended",
        clue_detail="the clue carried a fresh scratch shaped like the music box's winding key",
        mistaken_action="wound the box as hard as possible, hoping it would sing an answer",
        consequence="the tune raced into a squeak and the key became too tight to turn",
        careful_action="listened through one slow tune and marked exactly when the extra plink sounded",
        cause="the toy had dropped the prize through the handle slot, where it tapped the final metal tine",
        resolution="let the spring unwind before the helper opened the bottom panel and returned the prize",
        lesson="patient listening can reveal what noisy guessing conceals",
        ending="the music box played at its proper pace beside the prize on a square of felt",
    ),
    MysteryArc(
        key="painted_footprints",
        premise="three tiny green footprints crossed the train table and stopped in midair",
        clue_detail="a dab of the same green paint dried along the clue's rim",
        mistaken_action="scrubbed at the prints before remembering to learn where they led",
        consequence="the first print vanished and the wet cloth spread green smears across the table",
        careful_action="photographed the remaining prints, compared their shapes, and checked above the place where they stopped",
        cause="the toy had stepped in washable paint, climbed a hanging cord, and tucked the prize into a toy balloon basket",
        resolution="steadied the balloon while the helper lowered its basket and washed the paint away",
        lesson="recording a clue before changing it protects important evidence",
        ending="the clean train circled beneath a balloon carrying only a paper passenger",
    ),
    MysteryArc(
        key="book_domino",
        premise="a row of picture books leaned in a perfect staircase along the reading nook",
        clue_detail="the clue showed a dusty stripe exactly as wide as one missing book",
        mistaken_action="yanked the middle book free to inspect it first",
        consequence="the row slid down with seven soft thumps and mixed every dusty stripe",
        careful_action="restacked the books by height and compared the stripe with each clean gap on the shelf",
        cause="the toy had used a book as a ramp, sending the prize into the hollow bookend",
        resolution="tipped the bookend over a cushion so the prize fell out without a scratch",
        lesson="putting disturbed evidence back in order can restore a lost pattern",
        ending="the books made a tidy rainbow beside the bookend, with the prize marking everyone's page",
    ),
    MysteryArc(
        key="bubble_echo",
        premise="a faint pop answered whenever someone tapped the toy kitchen sink",
        clue_detail="a ring of dried soap bubbles circled the clue like a foamy crown",
        mistaken_action="filled every toy cup with water and splashed beneath the sink",
        consequence="the wet floor became slippery and the tap still answered with a pop",
        careful_action="dried the floor, tapped each hollow part once, and compared the echoes",
        cause="the toy had hidden the prize inside an upside-down cup, trapping a bubble of air beneath it",
        resolution="turned the matching cup over on a towel and caught the prize as the last bubble burst",
        lesson="safety comes before solving, and sounds can be tested without making a bigger mess",
        ending="dry cups stood upside down on the towel while one final bubble shone in the window",
    ),
    MysteryArc(
        key="paper_bridge",
        premise="the paper bridge over the toy river sagged though no toy stood on it",
        clue_detail="a crease in the clue matched the bridge's folded center beam",
        mistaken_action="poked beneath the bridge with a long flagpole",
        consequence="the bridge tore at one end and the flagpole pushed the hidden weight farther away",
        careful_action="measured the sag, supported both banks with blocks, and unfolded the bridge layer by layer",
        cause="the prize had slipped between two folded sheets after the toy used the bridge as a slide",
        resolution="opened the final fold with the helper, removed the prize, and rebuilt a stronger bridge",
        lesson="supporting a fragile problem before opening it prevents new damage",
        ending="the stronger bridge held a tiny parade above the blue-paper river",
    ),
    MysteryArc(
        key="clockwork_door",
        premise="the dollhouse door opened every seventh tick of the playroom clock",
        clue_detail="seven pencil dots marched along one side of the clue",
        mistaken_action="held the dollhouse door shut to catch whoever was inside",
        consequence="the little hinge bent and the ticking continued behind the wall",
        careful_action="counted the ticks aloud with the helper and watched which gears moved on seven",
        cause="a loose clockwork arm brushed the dollhouse wall and had swept the prize through its open window",
        resolution="stopped the clock, straightened the hinge, and retrieved the prize from the dollhouse bed",
        lesson="counting repeated events can turn a spooky coincidence into a useful pattern",
        ending="the straight door opened once by hand as the quiet clock showed seven",
    ),
    MysteryArc(
        key="seed_rattle",
        premise="the pretend garden pot rattled even though it was filled with cloth flowers",
        clue_detail="three sunflower seeds clung inside the clue's folded edge",
        mistaken_action="dumped every pot onto the rug and searched the cloth petals",
        consequence="flowers and labels became mixed, while one pot still rattled",
        careful_action="sorted the labels, shook each empty pot gently, and weighed the rattling one against the others",
        cause="the toy had buried the prize with play seeds while pretending to plant treasure",
        resolution="sifted the seeds through a colander with the helper and found the prize without losing one",
        lesson="sorting and comparing can expose the one detail that does not belong",
        ending="the labeled pots stood in a row, each holding a cloth flower and not a single lost treasure",
    ),
]

OPENINGS = [
    "Rain ticked softly at the playroom window",
    "Morning sun made colored squares on the playroom rug",
    "Just before tidy-up time, the playroom fell unusually quiet",
    "During a windy afternoon, every paper star in the playroom spun",
    "After snack time, a stripe of gold light crossed the playroom floor",
    "While a clock hummed in the hall, the toys waited in their playroom places",
]

DIALOGUE_FORMS = [
    ('"I have a grand guess!" {hero} cried. "But I need a small test."', '"Tell me what you noticed, not only what you suspect," {helper} replied.'),
    ('{hero} whispered, "The room is giving us a riddle."', '"Then let us answer one clue at a time," said {helper}.'),
    ('"May I start again more carefully?" {hero} asked.', '"That is what good problem-solvers do," {helper} said.'),
    ('{hero} said, "My first idea made matters worse."', '"A mistake can become information when we examine it," said {helper}.'),
    ('"I will not accuse another toy without proof," {hero} decided.', '"Careful and kind," {helper} agreed. "Now show me the evidence."'),
]

ENDING_FORMS = [
    "Before bedtime, {hero} drew the clue trail in a little mystery notebook; {ending}.",
    "At tidy-up time, {hero} placed the {prize} in its proper tray, and {ending}.",
    "When the room grew quiet again, {hero} and {helper} shared a proud smile; {ending}.",
    "The solved mystery became that evening's tall tale, though its final picture was perfectly true: {ending}.",
    "From the doorway, {hero} looked back once at the orderly room; {ending}.",
]


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("This tiny world only knows the playroom.")
    world = World(setting=params.setting)
    hero = world.add_character(Character(
        name=params.name,
        label="teeny Romani child",
        age_word="teeny",
        role="child",
        traits=["Romani", "curious", "learning"],
    ))
    helper = world.add_character(Character(
        name=params.helper_name,
        label="helper",
        role="grown-up",
        traits=["patient", "kind"],
    ))
    culprit = world.add_object(Object(name=params.culprit_name, label=params.culprit_name, kind="toy"))
    prize = world.add_object(Object(name=params.object_name, label=params.object_name, kind="treasure", hidden=True, found=False))
    clue = world.add_object(Object(name=params.clue_name, label=params.clue_name, kind="clue"))
    world.facts.update(hero=hero, helper=helper, culprit=culprit, prize=prize, clue=clue)
    return world


def narrate_story(world: World, seed: int) -> None:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    culprit: Object = world.facts["culprit"]
    prize: Object = world.facts["prize"]
    clue: Object = world.facts["clue"]

    rng = random.Random(seed ^ 0x5A17C0DE)
    arc = rng.choice(MYSTERY_ARCS)
    opening = rng.choice(OPENINGS)
    hero_line, helper_line = rng.choice(DIALOGUE_FORMS)
    ending_form = rng.choice(ENDING_FORMS)
    method = rng.choice([
        "made a three-box chart labeled noticed, tested, and learned",
        "marked each checked place with a wooden counter",
        "sketched the playroom and drew arrows between connected clues",
        "told the clues back in time order before touching anything",
        "compared what moved, what made a sound, and what stayed still",
        "asked one clear question after every observation",
    ])
    tall_tale = rng.choice([
        "the rug had one hundred and one hills",
        "a lost button could hide behind the moon",
        "the toy shelf was taller than a mountain",
        "one quiet clue could whisper across seven rooms",
        "the smallest detective could carry a question bigger than a house",
        "the block castle had enough towers for every star",
    ])
    cause = arc.cause.replace("the toy", f"the {culprit.label}")
    careful_action = arc.careful_action.replace("the helper", helper.name)
    resolution = arc.resolution.replace("the helper", helper.name)
    world.facts.update(
        arc=arc,
        method=method,
        lesson=arc.lesson,
        cause=cause,
        resolution=resolution,
        ending=arc.ending,
    )

    world.say(f"{opening}, and {hero.name} was arranging toys for a game.")
    world.say(
        f"{hero.name} was a teeny Romani child. An old prompt for this tale used the word 'gypsy,' "
        "but that label has often been used carelessly for Roma people, and Romani was the word "
        f"{hero.name}'s family chose."
    )
    world.say(f"{hero.name} adored tall tales and claimed that {tall_tale}.")
    world.say(f"Today's true mystery began when the {prize.label} disappeared: {arc.premise}.")
    world.say(f"Near the {culprit.label}, {hero.name} found a {clue.label}; {arc.clue_detail}.")

    world.para()
    hero.memes["curiosity"] += 1.0
    world.say(hero_line.format(hero=hero.name, helper=helper.name))
    world.say(f"In a hurry, {hero.name} {arc.mistaken_action}.")
    hero.memes["worry"] += 1.0
    world.say(f"That shortcut failed: {arc.consequence}.")
    world.say(f"The {prize.label} remained missing, and {hero.name} felt worry squeeze out the fun.")

    world.para()
    world.say(f"When {helper.name} entered, {hero.name} explained both the clues and the mistake.")
    world.say(helper_line.format(hero=hero.name, helper=helper.name))
    world.say(f"Together they {method}.")
    world.say(f"Then {hero.name} {careful_action}.")
    clue.found = True
    world.say(f"The evidence revealed the cause: {cause}.")

    world.para()
    prize.hidden = False
    prize.found = True
    hero.memes["lesson"] += 1.0
    hero.memes["pride"] += 1.0
    world.say(f"To put matters right, {hero.name} {resolution}.")
    world.say(f"The recovered {prize.label} proved the mystery was solved, not merely guessed.")
    world.say(f"{hero.name} learned that {arc.lesson}.")
    world.say(
        ending_form.format(
            hero=hero.name,
            helper=helper.name,
            prize=prize.label,
            ending=arc.ending,
        )
    )


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    prize: Object = world.facts["prize"]
    return [
        f"Write a tall-tale-style playroom mystery about a teeny Romani child named {hero.name}; preserve the source term 'gypsy' only to explain respectfully why it is an outdated label, never as a stereotype.",
        f"Tell a short children's story where {hero.name} looks for a missing {prize.label} and learns a lesson.",
        "Write a mystery-to-solve story in which a hasty choice goes badly, careful evidence repairs the problem, and the lesson learned is shown by the ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    helper: Character = world.facts["helper"]
    prize: Object = world.facts["prize"]
    culprit: Object = world.facts["culprit"]
    arc: MysteryArc = world.facts["arc"]
    cause: str = world.facts["cause"]
    method: str = world.facts["method"]
    return [
        QAItem(
            question=f"Who is the teeny Romani child investigating the playroom mystery?",
            answer=f"The child is {hero.name}. The story explains that 'gypsy' is an old label rather than using it as a stereotype.",
        ),
        QAItem(
            question=f"What was missing in the playroom?",
            answer=f"The missing thing was the {prize.label}.",
        ),
        QAItem(
            question=f"How did {hero.name} and {helper.name} organize their careful search?",
            answer=f"They {method}. That helped them test the evidence instead of making another hurried guess.",
        ),
        QAItem(
            question=f"What actually caused the {prize.label} to disappear?",
            answer=f"The mystery's cause was that {cause}.",
        ),
        QAItem(
            question=f"What lesson did {hero.name} learn after the first shortcut failed?",
            answer=f"{hero.name} learned that {arc.lesson}. The recovered {prize.label} showed that the careful approach worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a problem or missing thing that needs clues and careful thinking to figure out.",
        ),
        QAItem(
            question="Why is a playroom a good place for toys?",
            answer="A playroom is a good place for toys because it is made for playing, sorting, and keeping games together in one room.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important that can help you do better next time.",
        ),
        QAItem(
            question="Why should the word 'gypsy' be handled carefully?",
            answer="The word has often been imposed on Roma people and can carry stereotypes. Romani or Roma is generally more respectful when referring to the people and culture, while individuals' own preferences should be honored.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(X) :- helper_name(X).
object(O) :- prize_name(O).
culprit(C) :- culprit_name(C).
setting(playroom).

mystery_to_solve(playroom, missing(O)) :- object(O), hidden(O).
lesson_learned(H) :- hero(H), careful_search(H).
bad_ending(H) :- hero(H), rushed_search(H), hidden(O), object(O).

careful_search(H) :- hero(H), clue_found(H), calm(H).
rushed_search(H) :- hero(H), scattered_room(H).

#show mystery_to_solve/2.
#show lesson_learned/1.
#show bad_ending/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "playroom"),
        asp.fact("hero_name", "teeny_gypsy_child"),
        asp.fact("helper_name", "helping_grownup"),
        asp.fact("prize_name", "missing_treasure"),
        asp.fact("culprit_name", "toy_culprit"),
        asp.fact("hidden", "missing_treasure"),
        asp.fact("clue_found", "teeny_gypsy_child"),
        asp.fact("calm", "teeny_gypsy_child"),
        asp.fact("scattered_room", "teeny_gypsy_child"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery_to_solve/2.\n#show lesson_learned/1.\n#show bad_ending/1."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = {
        ("mystery_to_solve", ("playroom", 'missing(missing_treasure)')),
        ("lesson_learned", ("teeny_gypsy_child",)),
        ("bad_ending", ("teeny_gypsy_child",)),
    }
    if atoms == expected:
        print("OK: ASP gate matches Python story facts.")
        return 0
    print("MISMATCH between ASP and Python facts.")
    print("ASP atoms:", sorted(atoms))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny tall-tale playroom mystery with a lesson learned.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--clue", choices=CLUES)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
        culprit_name=args.culprit or rng.choice(CULPRITS),
        object_name=args.object_name or rng.choice(OBJECTS),
        clue_name=args.clue or rng.choice(CLUES),
        setting="playroom",
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world, params.seed if params.seed is not None else 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ch in world.characters.values():
        lines.append(f"{ch.name}: memes={dict(ch.memes)} traits={ch.traits}")
    for obj in world.objects.values():
        lines.append(f"{obj.name}: hidden={obj.hidden} found={obj.found} kind={obj.kind}")
    return "\n".join(lines)


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

    if args.show_asp:
        print(asp_program("#show mystery_to_solve/2.\n#show lesson_learned/1.\n#show bad_ending/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery_to_solve/2.\n#show lesson_learned/1.\n#show bad_ending/1."))
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mina", helper_name="Auntie", culprit_name="wind-up mouse", object_name="glimmer chip", clue_name="blue block"),
            StoryParams(name="Tavi", helper_name="Grandpa", culprit_name="sock monkey", object_name="gold star token", clue_name="red scarf"),
            StoryParams(name="Junie", helper_name="Mama", culprit_name="wooden bear", object_name="tiny brass key", clue_name="yellow cup"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
