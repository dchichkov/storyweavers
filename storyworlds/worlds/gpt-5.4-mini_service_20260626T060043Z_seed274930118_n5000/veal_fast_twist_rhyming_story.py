#!/usr/bin/env python3
"""
storyworlds/worlds/veal_fast_twist_rhyming_story.py
====================================================

A tiny storyworld in a rhyming-story style about a child helping prepare a veal
dinner.  Twelve different kitchen problems turn "fast" into a question about
good judgment, and each problem has its own Twist, repair, and ending image.

Premise:
- A child loves helping in the kitchen.
- They want to help make the veal dinner ready fast.
- A parent handles the stove while the child takes on safe kitchen jobs.

Turn:
- A concrete kitchen problem defeats the first hurried idea.
- A clue reveals a different cause than the child expected.
- The Twist changes the plan rather than simply changing a garnish.

Resolution:
- The child and parent solve the actual problem together.
- A concrete final image proves how their choice changed supper.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    finish: str
    tags: set[str] = field(default_factory=set)


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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_rush(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("kid")
    if kid.memes.get("rush", 0.0) < THRESHOLD:
        return out
    sig = ("rush",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.meters["heat"] = kid.meters.get("heat", 0.0) + 1
    kid.memes["impatience"] = kid.memes.get("impatience", 0.0) + 1
    out.append("The pan got hot and the hurry felt harder to hide.")
    return out


def _r_tough(world: World) -> list[str]:
    kid = world.get("kid")
    stew = world.get("veal")
    if kid.meters.get("heat", 0.0) < THRESHOLD:
        return []
    sig = ("tough",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stew.meters["toughness"] = stew.meters.get("toughness", 0.0) + 1
    return ["A rushed kitchen made the plan harder to trust; being quick still had to be safe and just."]


def _r_soothe(world: World) -> list[str]:
    kid = world.get("kid")
    if kid.memes.get("calm", 0.0) < THRESHOLD:
        return []
    sig = ("soothe",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kid.meters["heat"] = max(0.0, kid.meters.get("heat", 0.0) - 1)
    kid.memes["joy"] = kid.memes.get("joy", 0.0) + 1
    return ["The hurry eased when clue met choice; careful thinking found its voice."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_rush, _r_tough, _r_soothe):
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the kitchen", affords={"cook"})
ACTIVITY = Activity(
    id="cook",
    verb="cook veal",
    gerund="cooking veal",
    rush="rush the pan",
    mess="scorch",
    soil="too dry",
    keyword="veal",
    tags={"veal", "fast", "cook"},
)
PRIZE = Prize(label="veal", phrase="a small veal cutlet", type="veal")
HELPERS = {
    "twist": Helper(
        id="twist",
        label="a lemon twist",
        prep="add a lemon twist",
        finish="the Twist made the dish taste light and bright",
        tags={"twist", "lemon"},
    )
}

GIRL_NAMES = ["Mia", "Luna", "Zoe", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben", "Max"]
TRAITS = ["cheerful", "curious", "brave", "spry", "playful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    incident: str
    telling_mode: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    premise: str
    conflict: str
    first_try: str
    clue: str
    action: str
    twist: str
    resolution: str
    lesson: str
    ending: str
    question: str
    answer: str


INCIDENTS = [
    Incident(
        "the quick clock",
        "The wall clock claimed the guests would arrive almost at once.",
        "A hurry began: napkins slid, spoons clattered, and every task felt late.",
        "The child tried to set all the places in one armful, but forks sprinkled across the floor.",
        "The small clock on the oven showed that the wall clock was twelve minutes fast.",
        "They washed the fallen forks, set one place at a time, and let the parent tend the pan.",
        "The Twist was time itself: the clock was fast, but the cooks did not need to be.",
        "The table was ready before the doorbell rang, and the veal dinner had the time it needed.",
        "Checking a fact can be faster than obeying a fright.",
        "The true clock ticked beside six straight forks and a calm blue cloth.",
        "What showed that the cooks were not actually late?",
        "The oven clock showed that the wall clock was twelve minutes fast, so there was time to work carefully.",
    ),
    Incident(
        "the spotted recipe",
        "A splash had blurred the timing line on the family's veal recipe card.",
        "The child read the smudge as a very short cooking time and announced a speedy plan.",
        "They reached for the timer before checking the rest of the card.",
        "A rhyming note on the card's clean back mentioned a gentle pace and a safety check.",
        "The parent checked the full recipe and cooking guidance while the child copied a clean new card.",
        "The Twist was on the reverse: the missing instruction had been behind the hurried guess.",
        "The parent cooked the veal properly, and the new card could no longer fool the next cook.",
        "A blurry instruction calls for checking, not guessing.",
        "The fresh recipe card dried on a clip, its clear last line shining under the lamp.",
        "Where did the child find the clue about the proper pace?",
        "The clue was a rhyming note on the clean back of the recipe card.",
    ),
    Incident(
        "the early knock",
        "A knock sounded while the parent was just beginning the veal dinner.",
        "The child thought the guests had arrived early and wanted the hot cooking rushed.",
        "They began dragging every dining chair toward the table at once, blocking the kitchen doorway.",
        "A second tap came from low on the door, followed by a familiar jingling tag.",
        "They cleared the doorway and opened it with the parent, then set out a cold salad safely.",
        "The Twist had a wagging tail: the visitor was the neighbor's lost dog, not the dinner guests.",
        "The dog went home, the path stayed clear, and the parent finished the veal without racing.",
        "Do not let an assumption turn safe work into a rush.",
        "A silver dog tag winked outside while the empty doorway framed a neatly set table.",
        "Who had made the early knock?",
        "The neighbor's lost dog had tapped at the door; the dinner guests had not arrived yet.",
    ),
    Incident(
        "the silent timer",
        "The kitchen timer flashed but made no sound beside the veal dinner.",
        "The child feared that silence meant supper would be forgotten.",
        "They proposed shouting a rhyme every minute, faster and louder each time.",
        "The display kept counting correctly, and a loose battery cover clicked under one finger.",
        "The parent secured the cover while the child placed a second timer where both could see it.",
        "The Twist was that the timer had not stopped keeping time; only its bell had lost its chime.",
        "Two checked timers guarded the cooking, and nobody had to shout or guess.",
        "A quiet tool may still be working, so inspect before replacing it.",
        "The two timers blinked together as one gave a crisp, cheerful ring.",
        "What was wrong with the silent timer?",
        "Its loose battery cover had stopped the bell, although the display was still counting correctly.",
    ),
    Incident(
        "the missing lemon",
        "The recipe suggested a lemon twist, but the fruit bowl held no lemon at all.",
        "The child worried that the whole veal dinner must wait for a trip to the shop.",
        "They searched every cupboard twice and made the same empty bowl rhyme with 'slow.'",
        "The recipe called the lemon optional, and a small orange sat behind the flour tin.",
        "The parent approved orange zest while the child tore herbs and arranged them on a cool plate.",
        "The Twist changed color: a curl of orange replaced the expected lemon spiral.",
        "The bright finish suited the meal, and no one made an unnecessary dash to the store.",
        "Flexible plans can keep care in place when one ingredient is missing.",
        "An orange curl rested beside green herbs like a tiny sunset on the plate.",
        "How did they replace the missing lemon twist?",
        "With the parent's approval, they used orange zest and fresh herbs instead.",
    ),
    Incident(
        "the mixed-up labels",
        "Two covered dishes waited in the refrigerator, one veal and one vegetable pie.",
        "Their labels had loosened, so the child could not tell which dinner needed which instructions.",
        "They nearly chose the dish nearest the door simply because it was fastest to reach.",
        "One container matched the blue shape and date recorded on the parent's meal-plan note.",
        "The parent identified both sealed dishes, relabeled them, and followed the correct directions.",
        "The Twist was a paper clue: the meal plan, not a peek or a guess, solved the mix-up.",
        "Both dishes were handled correctly, and each guest received the meal they expected.",
        "Labels and records protect people better than hurried guesses.",
        "Two firm labels sat squarely on the lids, one blue and one green.",
        "What safely solved the dish mix-up?",
        "The parent matched a container to the shape and date on the meal-plan note, then relabeled both dishes.",
    ),
    Incident(
        "the crowded counter",
        "Bowls, books, and a toy windmill crowded the counter needed for dinner preparation.",
        "The child wanted to sweep everything into one fast pile on the floor.",
        "The toy rolled toward the walkway, and a cookbook began to slide after it.",
        "Colored shelf marks showed that every object already had a safe home.",
        "They sorted books, toys, and bowls into separate places before the parent began cooking the veal.",
        "The Twist was not a quicker hand but a simple order: sort first, then start.",
        "A clear counter gave the parent room to work and the child room to prepare napkins.",
        "Making space carefully prevents a fast mess from becoming a slow accident.",
        "The toy windmill spun safely on its shelf above a wide, clean counter.",
        "Why did the child sort the counter instead of making one pile?",
        "Sorting put each object in a safe home and kept the walkway and cooking space clear.",
    ),
    Incident(
        "the sauce race",
        "The child planned a cold herb sauce while the parent cooked the veal.",
        "They tried to finish before a favorite song reached its fast final beat.",
        "The first hurried bowl held two spoonfuls of one herb and none of another.",
        "The written recipe used colored spoon symbols that matched the measuring spoons.",
        "They started a fresh small batch, matched each color, and tasted only after the parent checked it.",
        "The Twist was to stop racing the music and let the colored pattern set the pace.",
        "The balanced sauce was ready when the safely cooked veal came to the table.",
        "Accuracy makes a better partner than speed in a recipe.",
        "Three clean measuring spoons lay in a row beside a bowl flecked with green.",
        "What helped the child measure the second sauce correctly?",
        "Colored spoon symbols on the recipe matched the measuring spoons and guided each amount.",
    ),
    Incident(
        "the power blink",
        "The kitchen lights blinked just as the parent checked the veal dinner.",
        "The child wanted to finish fast before the room could go dark again.",
        "They offered a toy flashlight and began piling candles near the table.",
        "The parent noticed that the oven clock had reset, while the steady ceiling light had already returned.",
        "They moved the candles away, reset the timer, and verified the cooking progress with proper tools.",
        "The Twist was a lost clock, not lost power: the brief blink had erased the timer.",
        "The meal finished under bright lights after the parent completed every safety check.",
        "After an interruption, restore the missing information before carrying on.",
        "The reset clock glowed steadily above a table with no candles in its path.",
        "What had the brief power blink changed?",
        "It had reset the oven clock and timer, so the parent restored the timing information before continuing.",
    ),
    Incident(
        "the double order",
        "Two supper notes both seemed to request the same veal dinner.",
        "The child thought they must prepare twice as much food in half the time.",
        "They fetched a second stack of plates before counting who would actually eat.",
        "The notes carried the same date and a matching ink blot in the corner.",
        "They compared the notes, counted the guests, and recycled the accidental copy.",
        "The Twist was a duplicate: two papers described one dinner, not two.",
        "The right number of places was set, and no food or effort was wasted.",
        "Count people and check records before doubling a plan.",
        "One supper note stood on the board while the duplicate curled in the recycling bin.",
        "How did they know the second order was a duplicate?",
        "Both notes had the same date and the same ink blot, and the guest count confirmed there was only one dinner.",
    ),
    Incident(
        "the cool platter",
        "The serving platter for the veal dinner seemed to have vanished.",
        "The child wanted to use the first tray they could grab and serve fast.",
        "The chosen tray wobbled because it was a lightweight craft board, not serving ware.",
        "A round edge peeked from beneath a clean towel where bread dough had been resting.",
        "The parent moved the dough properly, washed the food-safe platter, and dried it while the child folded napkins.",
        "The Twist was under the towel: the missing platter had been helping with another kitchen job.",
        "Dinner reached the table on the proper platter, steady and clean.",
        "The nearest object is not always the right tool.",
        "The polished platter sat firm at the center of four folded napkins.",
        "Where was the missing serving platter?",
        "It was beneath a clean towel, where it had been used to support resting bread dough.",
    ),
    Incident(
        "the backwards rhyme",
        "A grandparent had left a rhyming checklist for the veal supper.",
        "The child read its lines from bottom to top and thought dessert came first.",
        "They rushed to open the treat tin before washing their hands or setting the table.",
        "Tiny arrows beside the verses pointed downward from the first line.",
        "They washed up, followed the arrows, set the table, and saved the treat for after dinner.",
        "The Twist was the rhyme's direction: the words were right, but the reading order was reversed.",
        "Every safe task happened in sequence while the parent prepared and cooked the veal.",
        "Even a catchy rhyme needs to be read in the intended order.",
        "The checklist hung upright, and its last arrow pointed to one closed treat tin.",
        "Why had the child misunderstood the rhyming checklist?",
        "The child had read it from bottom to top instead of following the tiny downward arrows.",
    ),
]


OPENINGS = [
    "Supper had a puzzle tucked under its hat.",
    "A quick little plan went tap-tap-tap.",
    "Before the first plate found its place, a problem challenged the kitchen race.",
    "The evening began with a clatter and chime.",
    "A dinner-day riddle arrived right on time.",
    "The table stood empty, the window shone gold, and a curious problem waited to be told.",
    "Fast feet paused at the kitchen door.",
    "One ordinary supper brought something new.",
    "A rhyme met a riddle at quarter to night.",
    "The kitchen was calm for exactly one beat.",
]


def can_story(place: str, activity: str, prize: str) -> bool:
    return place == "kitchen" and activity == "cook" and prize == "veal"


ASP_RULES = r"""
place(kitchen).
activity(cook).
prize(veal).
helper(twist).

compatible(P,A,R) :- place(P), activity(A), prize(R), P = kitchen, A = cook, R = veal.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "kitchen"),
            asp.fact("activity", "cook"),
            asp.fact("prize", "veal"),
            asp.fact("helper", "twist"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("kitchen", "cook", "veal")]


def tell(params: StoryParams) -> World:
    name = params.name
    gender = params.gender
    parent_type = params.parent
    trait = params.trait
    incident = INCIDENTS[int(params.incident.rsplit("_", 1)[1])]
    opening = OPENINGS[int(params.telling_mode.rsplit("_", 1)[1])]
    world = World(SETTING)
    kid = world.add(Entity(id="kid", kind="character", type=gender, label=name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    veal = world.add(Entity(id="veal", type="veal", label="veal", phrase="a small veal cutlet", owner="kid"))
    twist = world.add(Entity(id="twist", type="thing", label="lemon twist", phrase="a bright lemon twist"))
    world.facts.update(kid=kid, parent=parent, veal=veal, twist=twist, incident=incident)

    kid.memes["love"] = 1
    world.say(opening)
    world.say(f"{name}, a {trait} young {gender}, wanted to help make the veal dinner fast.")
    world.say(
        f"The {parent_type} would handle the stove and check that the meat was properly cooked; "
        f"{name} would do safe jobs away from the heat."
    )
    world.say("Veal was simply the kind of meat chosen for this meal; the tale stayed with supper, not where meat came from.")
    world.para()
    world.say(incident.premise)
    world.say(incident.conflict)
    world.say(f'"Fast will fix it," {name} said. "I will finish this task before one rhyme is read!"')
    kid.memes["rush"] = 1
    propagate(world, narrate=True)
    world.say(incident.first_try)
    world.say(f'"Pause and look; let facts be our guide," the {parent_type} replied.')
    world.para()
    world.say(incident.clue)
    world.say(incident.action)
    kid.memes["calm"] = 1
    propagate(world, narrate=True)
    world.say(incident.twist)
    world.say(f'"Quick can be clever, but safe must stay," {name} said. "We checked, then chose the better way."')
    world.para()
    world.say(incident.resolution)
    world.say(f"The lesson was plain in the last little rhyme: {incident.lesson}")
    world.say(incident.ending)

    world.facts.update(
        title=incident.title,
        clue=incident.clue,
        twist_text=incident.twist,
        resolution=incident.resolution,
        lesson=incident.lesson,
        ending=incident.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    incident = f["incident"]
    return [
        "Write a child-friendly rhyming story about veal, fast thinking, and a genuine Twist in a kitchen.",
        f"Tell a rhyming tale where {kid.label} helps safely with {incident.title} while a parent handles the cooking.",
        f"Write a kitchen story in which this clue changes the plan: {incident.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    parent = f["parent"]
    incident = f["incident"]
    return [
        QAItem(
            question=f"What did {kid.label} want to help make fast?",
            answer=f"{kid.label} wanted to help make the veal dinner fast while the {parent.type} handled the stove.",
        ),
        QAItem(
            question=f"During {kid.label}'s {incident.title} puzzle, {incident.question[0].lower() + incident.question[1:]}",
            answer=incident.answer,
        ),
        QAItem(
            question=f"What Twist changed {kid.label}'s plan during {incident.title}?",
            answer=incident.twist,
        ),
        QAItem(
            question=f"What did {kid.label} learn after solving {incident.title}?",
            answer=incident.lesson,
        ),
        QAItem(
            question=f"What final image showed {kid.label} that {incident.title} was settled?",
            answer=incident.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fast mean?",
            answer="Fast means happening quickly, with little waiting.",
        ),
        QAItem(
            question="Who should handle a hot stove in this child-facing story?",
            answer="A responsible adult should handle the hot stove while a child helps with safe jobs away from the heat.",
        ),
        QAItem(
            question="What can a Twist mean in a story?",
            answer="A Twist is a surprising discovery that changes what the characters understand or decide to do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if args.place and args.place != "kitchen":
        raise StoryError("This storyworld only supports the kitchen setting.")
    if args.activity and args.activity != "cook":
        raise StoryError("This storyworld only supports the cook activity.")
    if args.prize and args.prize != "veal":
        raise StoryError("This storyworld only supports veal as the prize ingredient.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Gender must be girl or boy.")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="kitchen",
        activity="cook",
        prize="veal",
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        incident=f"incident_{seed % len(INCIDENTS):02d}",
        telling_mode=f"mode_{(seed // len(INCIDENTS)) % len(OPENINGS):02d}",
        seed=seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming kitchen storyworld about veal, fast, and a Twist.")
    ap.add_argument("--place", choices=["kitchen"])
    ap.add_argument("--activity", choices=["cook"])
    ap.add_argument("--prize", choices=["veal"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = resolve_params(args, random.Random(base_seed), base_seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed), seed)
            sample = generate(params)
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
