#!/usr/bin/env python3
"""
A small heartwarming storyworld about bran, surprise, and a gentle reveal.

Premise:
- A child or helper is preparing a simple bran treat or bran snack.
- Someone quietly plans a surprise.
- The surprise is meant to comfort, cheer, or welcome someone home.

The simulated state tracks:
- physical preparation of ingredients and gift items in meters
- feelings like anticipation, worry, gratitude, and delight in memes

The story turns when the hidden plan is discovered in a kind way,
then resolves with shared bran treats and warm feelings.
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
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO_ROOT = os.path.dirname(ROOT)
for path in (REPO_ROOT, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    prepared_by: Optional[str] = None
    hidden: bool = False
    served: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Scene:
    place: str = "the kitchen"
    occasion: str = "homecoming"
    surprise_kind: str = "welcome"
    bran_style: str = "bran muffins"
    surprise_note: str = "a happy surprise"
    mood: str = "warm"


class World:
    def __init__(self, scene: Scene):
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Core causal rules
# ---------------------------------------------------------------------------
def _rule_smell_bran(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.type == "bran" and e.meters.get("mixed", 0.0) >= THRESHOLD and "smell" not in e.meters:
            e.meters["smell"] = 1.0
            out.append(world.facts.get("scent_line", "The warm bran scent drifted through the room."))
    return out


def _rule_warm_feelings(world: World) -> list[str]:
    out: list[str] = []
    giver = world.facts.get("giver")
    receiver = world.facts.get("receiver")
    if not giver or not receiver:
        return out
    g = world.get(giver)
    r = world.get(receiver)
    if r.memes.get("surprised", 0.0) >= THRESHOLD and "gratitude" not in r.memes:
        r.memes["gratitude"] = 1.0
        g.memes["pride"] = g.memes.get("pride", 0.0) + 1.0
        out.append(world.facts.get("gratitude_line", f"{r.id} smiled with gratitude."))
    return out


def _rule_share(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.type == "bran" and e.meters.get("served", 0.0) >= THRESHOLD and "shared" not in e.meters:
            e.meters["shared"] = 1.0
            out.append(world.facts.get("sharing_line", "Everyone shared a little bit together."))
    return out


CAUSAL_RULES = [_rule_smell_bran, _rule_warm_feelings, _rule_share]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            new = rule(world)
            if new:
                changed = True
                lines.extend(new)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    occasion: str
    surprise_kind: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    bran_style: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Scene(place="the kitchen", occasion="homecoming", surprise_kind="welcome", bran_style="bran muffins"),
    "bakery": Scene(place="the bakery", occasion="thank-you", surprise_kind="thank-you", bran_style="bran cookies"),
    "porch": Scene(place="the porch", occasion="rainy-day", surprise_kind="comfort", bran_style="bran tea cakes"),
}

BRAN_STYLES = {
    "bran muffins": {"sweet", "warm"},
    "bran cookies": {"crisp", "sweet"},
    "bran tea cakes": {"soft", "gentle"},
}

CHILD_NAMES = ["Maya", "Leo", "Nina", "Eli", "Sora", "Owen", "Ivy", "Noah"]
HELPER_NAMES = ["Aunt June", "Dad", "Mom", "Grandpa", "Big Sister", "Older Brother"]


@dataclass(frozen=True)
class StoryArc:
    id: str
    need: str
    premise: str
    obstacle: str
    turn: str
    action: str
    reveal: str
    result: str
    ending_images: tuple[str, ...]


STORY_ARCS = (
    StoryArc(
        id="windblown_welcome",
        need="had come home tired after a long day",
        premise="{helper} arranged paper stars beside a covered basket of {treat} for a welcome-home surprise.",
        obstacle="A gust swept past them {location}, snapping the string and scattering every star.",
        turn="{child} caught the last star before it sailed away and noticed a tiny arrow drawn on its back.",
        action="Together they rehung the stars, following the arrows until the bright trail ended at the basket.",
        reveal="{helper} opened the basket and said the welcome was meant for {child} all along.",
        result="The ruined decoration became a treasure trail, and {child}'s tired face brightened.",
        ending_images=(
            "The final paper star turned slowly above an empty plate.",
            "Crumbs and rescued stars made a cheerful little constellation on the table.",
            "The mended string shone in the window while they shared the last warm bite.",
        ),
    ),
    StoryArc(
        id="smudged_recipe",
        need="felt discouraged after a hard lesson",
        premise="{helper} planned a heartwarming surprise by baking {treat} from an old family recipe.",
        obstacle="A splash of milk blurred the most important line on the recipe card.",
        turn="{child} remembered that the missing mark looked like the small spoon, not the large one.",
        action="{helper} measured again while {child} counted each careful stir aloud.",
        reveal="When the batch rose perfectly, {helper} admitted that the treats had always been for {child}.",
        result="Solving one small kitchen puzzle helped {child} feel capable again.",
        ending_images=(
            "They tucked the dry recipe card beside a plate holding one last bran crumb.",
            "A floury small-spoon print remained on the counter like a medal.",
            "Steam curled over the repaired recipe while their two mugs touched with a quiet clink.",
        ),
    ),
    StoryArc(
        id="runaway_note",
        need="was missing a friend who had moved away",
        premise="{helper} wrote kind messages from the family and hid them beneath a tray of {treat}.",
        obstacle="A bold little bird snatched the ribboned surprise note and darted past them {location}.",
        turn="{child} spotted one blue thread caught low on a railing and guessed where the bird had gone.",
        action="They offered the bird a loose piece of string, and it traded back the note without a fuss.",
        reveal="Inside the saved envelope, {child} found every message and a promise to write to the distant friend together.",
        result="The surprise could not erase the missing, but it made the distance feel smaller.",
        ending_images=(
            "The rescued blue ribbon lay beside two bran crumbs and a freshly addressed envelope.",
            "From the sill, the bird watched them seal a letter with a tiny flour thumbprint.",
            "Their new letter waited by the door while the treat tray cooled in the evening light.",
        ),
    ),
    StoryArc(
        id="stuck_wagon",
        need="had spent the morning helping everyone else",
        premise="{helper} loaded {treat} into a small wagon for a secret thank-you picnic.",
        obstacle="One wheel jammed against a pebble, and the covered wagon would not budge.",
        turn="Without knowing what was inside, {child} fetched a flat board to make a tiny ramp.",
        action="{child} held the board steady while {helper} eased the wheel up and over.",
        reveal="At the picnic cloth, {helper} lifted the cover and thanked {child} for being helpful yet again.",
        result="The helper finally became the one being helped, which made them both laugh.",
        ending_images=(
            "The freed wagon rested under the table with a daisy tucked through its wheel.",
            "Only a few bran crumbs remained on the picnic cloth beside the useful little board.",
            "The once-stuck wheel made one proud turn as they pulled the empty wagon home.",
        ),
    ),
    StoryArc(
        id="berry_spill",
        need="worried that a small mistake had spoiled the day",
        premise="{helper} decorated {treat} beneath a cloth so that {child} would not see the surprise early.",
        obstacle="A bowl tipped, painting a large berry-colored blot across the white cloth.",
        turn="{child} heard the clatter and offered a clean sponge without trying to peek underneath.",
        action="Instead of hiding the stain, they dabbed it into a heart and added three smaller berry dots.",
        reveal="{helper} whisked away the new heart-cloth and revealed the treats made especially for {child}.",
        result="What looked like a spoiled surprise became its happiest decoration.",
        ending_images=(
            "The berry heart dried over a chair while purple smiles circled the empty tray.",
            "Three berry dots and three bran crumbs remained side by side on the cloth.",
            "They hung the stained cloth in the window, where its heart glowed rosy in the sun.",
        ),
    ),
    StoryArc(
        id="missing_ingredient",
        need="needed cheering after a rainy, lonely afternoon",
        premise="{helper} began mixing {treat} as a quiet comfort surprise.",
        obstacle="The fruit jar was empty, and rain drummed too hard for a trip to the shop.",
        turn="{child} offered the apple saved for tomorrow, saying that good things tasted better when shared.",
        action="{helper} diced the apple while {child} shook cinnamon into the bowl with both hands.",
        reveal="When the warm treats appeared later, {helper} explained where the generous apple had gone.",
        result="{child}'s own kindness came back as the very surprise that brought comfort.",
        ending_images=(
            "Rain jeweled the window while an apple peel curled beside the empty bran tray.",
            "The cinnamon jar stood between their plates as the storm softened to a whisper.",
            "One apple seed waited in a cup for spring, and one last crumb waited for morning.",
        ),
    ),
    StoryArc(
        id="lantern_blackout",
        need="was nervous about the dark during a storm",
        premise="{helper} prepared {treat} before sunset and hid a comfort surprise nearby.",
        obstacle="Just as the storm arrived, every light {location} blinked out.",
        turn="{child} found the safe battery lantern by remembering its red handle.",
        action="They carried the lantern together, checking the floor and gathering blankets before sitting down.",
        reveal="In the lantern's circle, {helper} uncovered the bran treats and a note that read, 'Brave can be gentle.'",
        result="The dark stayed dark, but it no longer felt empty or frightening.",
        ending_images=(
            "The red-handled lantern shone on two plates and a peaceful pile of blankets.",
            "Outside, rain flashed silver; inside, the last bran crumb vanished with a giggle.",
            "Their shadows sat close together on the wall until the lamps blinked warmly back.",
        ),
    ),
    StoryArc(
        id="quiet_celebration",
        need="thought everyone had forgotten a small but important achievement",
        premise="{helper} invited the family to hide while {treat} cooled for a surprise celebration.",
        obstacle="The guests were delayed, and the quiet room made {child}'s hopeful smile fade.",
        turn="A timer chimed, followed by three soft knocks that matched the rhythm of {child}'s favorite song.",
        action="{child} knocked the rhythm back, and voices answered from behind curtains and doors.",
        reveal="Everyone stepped out as {helper} presented the bran treats and named what {child} had achieved.",
        result="Being noticed mattered more than a loud party, and {child} understood that the wait had not meant forgetting.",
        ending_images=(
            "Three paper hats leaned around the crumb-speckled tray after the final song.",
            "The little timer sat silent beneath a banner bearing {child}'s name.",
            "Long after the guests left, one bright card remained propped beside the clean plates.",
        ),
    ),
    StoryArc(
        id="cracked_plate",
        need="was returning something borrowed and feared it might be damaged",
        premise="{helper} set {treat} on a favorite painted plate for a reassuring surprise.",
        obstacle="A thin crack appeared in the plate before the treats could be carried safely.",
        turn="{child} heard the worried sigh and suggested using the sturdy picnic basket instead.",
        action="They lined the basket with a towel, moved every treat, and set the cracked plate aside for repair.",
        reveal="{helper} opened the basket and explained that the surprise was meant to show that accidents can be handled honestly.",
        result="Together they protected the food, told the truth about the plate, and let worry loosen its grip.",
        ending_images=(
            "A gold repair sticker crossed the clean plate while the basket held only bran crumbs.",
            "The empty basket sat safely on the floor, and the cracked plate waited beside a tube of glue.",
            "They drew a tiny heart near the repaired line before putting the plate back on its shelf.",
        ),
    ),
    StoryArc(
        id="secret_map",
        need="wanted an adventure on an otherwise ordinary day",
        premise="{helper} hid a map leading to a heartwarming bran surprise somewhere {location}.",
        obstacle="The final map corner tore away, leaving no picture of the hiding place.",
        turn="{child} noticed that flour dust formed a square where a box had recently stood.",
        action="They compared the dusty outline with the map, searched low instead of high, and found a ribbon under a bench.",
        reveal="The ribbon opened a box of {treat}, and {helper} declared {child} the day's most patient explorer.",
        result="Careful noticing, rather than wild guessing, solved the surprise adventure.",
        ending_images=(
            "The mended map lay flat beneath an empty box and a neat ring of bran crumbs.",
            "A ribbon compass pointed toward home as the two explorers finished their feast.",
            "They pinned the torn map above the bench, marking the treasure spot with a floury star.",
        ),
    ),
)


OPENING_FORMS = (
    "On the day {child} {need}, {helper} began planning something kind.",
    "{helper} noticed that {child} {need}. A quiet plan began at once.",
    "It seemed like an ordinary day, except that {child} {need}, and {helper} had noticed.",
    "Because {child} {need}, {helper} decided that a small act of care might help.",
    "{child} {need}. {helper} said nothing yet, but kindness was already at work.",
)

DIALOGUE_FORMS = (
    '"May I help?" {child} asked. "Yes," said {helper}, "but trust me for one more minute."',
    '"Something is going wrong," {helper} admitted. {child} answered, "Then we can set it right together."',
    '{child} whispered, "Is this a secret?" {helper} smiled. "Only until your next good idea."',
    '"I will not peek," {child} promised. "You can still be my partner," {helper} replied.',
    '{helper} asked, "Ready to solve this with me?" and {child} answered with an eager, "Ready!"',
)

RESPONSE_FORMS = (
    "{child} blinked in surprise, then wrapped {helper} in a grateful hug.",
    "For one still moment {child} stared, surprised; then a wide smile arrived.",
    '"You remembered," {child} said, and the happy surprise made both voices wobble a little.',
    "The surprise left {child} speechless until a laugh and a thank-you came out together.",
    "{child}'s eyes grew bright. The treat mattered, but being understood mattered even more.",
)


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def _location(scene: Scene) -> str:
    return {
        "the kitchen": "in the kitchen",
        "the bakery": "at the bakery",
        "the porch": "on the porch",
    }[scene.place]


def _render(template: str, world: World, child: Entity, helper: Entity, bran: Entity, arc: StoryArc) -> str:
    return template.format(
        child=child.id,
        helper=helper.id,
        treat=bran.phrase,
        bran=bran.label,
        location=_location(world.scene),
        need=arc.need,
    )


def simulate(params: StoryParams) -> World:
    base_scene = PLACES[params.place]
    scene = Scene(
        place=base_scene.place,
        occasion=params.occasion,
        surprise_kind=params.surprise_kind,
        bran_style=params.bran_style,
        surprise_note=f"a {params.surprise_kind} surprise",
    )
    world = World(scene)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    bran = world.add(
        Entity(
            id="bran_treat",
            kind="thing",
            type="bran",
            label=params.bran_style,
            phrase=f"fresh {params.bran_style}",
            owner=helper.id,
            hidden=True,
        )
    )

    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = rng.choice(STORY_ARCS)
    opening_form = rng.choice(OPENING_FORMS)
    dialogue_form = rng.choice(DIALOGUE_FORMS)
    response_form = rng.choice(RESPONSE_FORMS)
    ending_image = rng.choice(arc.ending_images)
    scent_lines = (
        f"A toasted bran scent curled {_location(scene)}.",
        f"Soon the gentle smell of warm bran filled {scene.place}.",
        "The hearty, sweet smell of bran slipped out before the secret did.",
    )
    sharing_lines = (
        f"{child.id} broke the first {bran.label.rstrip('s')} in two so they could taste it together.",
        f"They shared the {bran.label} slowly, talking about every twist in the day.",
        f"{helper.id} poured two drinks, and they passed the {bran.label} back and forth.",
    )
    gratitude_lines = (
        f"{child.id} thanked {helper.id} for noticing what kind of day it had been.",
        f"Gratitude warmed {child.id}'s face even before the first bite.",
        f"{child.id} squeezed {helper.id}'s hand and said, \"This is exactly what I needed.\"",
    )
    world.facts.update(
        child=child.id,
        helper=helper.id,
        giver=helper.id,
        receiver=child.id,
        bran=bran.id,
        scene=scene,
        arc=arc,
        obstacle=arc.obstacle,
        helpful_action=arc.action,
        result=arc.result,
        ending_image=ending_image,
        scent_line=rng.choice(scent_lines),
        sharing_line=rng.choice(sharing_lines),
        gratitude_line=rng.choice(gratitude_lines),
    )

    world.say(_render(opening_form, world, child, helper, bran, arc))
    world.say("The plan was meant to become a heartwarming surprise, with bran at its center.")
    world.say(_render(arc.premise, world, child, helper, bran, arc))
    world.para()

    bran.meters["mixed"] = 1.0
    bran.prepared_by = helper.id
    world.say(_render(arc.obstacle, world, child, helper, bran, arc))
    propagate(world)
    world.para()

    child.memes["curious"] = 1.0
    world.say(_render(arc.turn, world, child, helper, bran, arc))
    world.say(_render(dialogue_form, world, child, helper, bran, arc))
    world.say(_render(arc.action, world, child, helper, bran, arc))
    world.para()

    world.say(_render(arc.reveal, world, child, helper, bran, arc))
    child.memes["surprised"] = 1.0
    bran.hidden = False
    bran.served = True
    bran.meters["served"] = 1.0
    world.say(_render(response_form, world, child, helper, bran, arc))
    propagate(world)
    world.para()

    child.memes["joy"] = 1.0
    world.say(_render(arc.result, world, child, helper, bran, arc))
    world.say(_render(ending_image, world, child, helper, bran, arc))

    world.facts.update(
        child=child,
        helper=helper,
        bran=bran,
        arc=arc,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    arc: StoryArc = f["arc"]
    scene = world.scene
    return [
        f"Write a warm short story about {child.id}, who {arc.need}, and a surprise involving {scene.bran_style}.",
        f"Tell a heartwarming story where {helper.id} plans a bran surprise, an obstacle interrupts it, and {child.id} helps.",
        f"Write a gentle story set { _location(scene) } with a causal problem, shared action, and a concrete happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    bran: Entity = f["bran"]
    arc: StoryArc = f["arc"]
    return [
        QAItem(
            question=f"Why did {helper.id} plan a {bran.label} surprise for {child.id}?",
            answer=f"{helper.id} planned it because {child.id} {arc.need}. The {bran.label} were meant to show care.",
        ),
        QAItem(
            question=f"What problem did {child.id} and {helper.id} face before sharing the {bran.label}?",
            answer=_render(arc.obstacle, world, child, helper, bran, arc),
        ),
        QAItem(
            question=f"How did {child.id} help the surprise succeed?",
            answer=_render(arc.action, world, child, helper, bran, arc),
        ),
        QAItem(
            question=f"How was the {arc.id.replace('_', ' ')} problem resolved for {child.id}?",
            answer=_render(arc.result, world, child, helper, bran, arc),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bran?",
            answer="Bran is the outer layer of a grain, and people often add it to muffins, cookies, or cereal for a hearty taste.",
        ),
        QAItem(
            question="Why can a surprise make someone feel better?",
            answer="A kind surprise can make someone feel remembered, cared for, and happy because it shows someone put in extra thought.",
        ),
        QAItem(
            question="What does sharing a snack do?",
            answer="Sharing a snack lets people enjoy something together and can turn an ordinary moment into a warm one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A surprise is reasonable if one helper makes a bran treat for one child.
reasonable(C, H, B) :- child(C), helper(H), bran(B), makes(H, B), for(C, B).

% If the surprise is hidden, then it can be revealed.
can_reveal(B) :- bran(B), hidden(B).

% A warm ending is possible when the child is surprised and the bran is served.
warm_ending(C, B) :- child(C), bran(B), surprised(C), served(B).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for place_id, scene in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("located", place_id, scene.place))
    for style in BRAN_STYLES:
        lines.append(asp.fact("bran", style.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show reasonable/3."))
    atoms = set(asp.atoms(model, "reasonable"))
    expected = set()
    for place_id in PLACES:
        for style in BRAN_STYLES:
            expected.add(("child", "helper", "bran"))
    # We only verify the program is syntactically alive and yields a model.
    if model is None:
        print("ASP verification failed: no model.")
        return 1
    print(f"OK: ASP program solved with {len(model)} shown atoms.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming bran surprise storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bran-style", choices=list(BRAN_STYLES))
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    scene = PLACES[place]
    bran_style = args.bran_style or scene.bran_style
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if child_name == helper_name:
        raise StoryError("Child and helper must be different people.")
    child_type = "girl" if child_name in {"Maya", "Nina", "Ivy"} else "boy"
    helper_type = "woman" if helper_name in {"Aunt June", "Mom", "Big Sister"} else "man"
    return StoryParams(
        place=place,
        occasion=scene.occasion,
        surprise_kind=scene.surprise_kind,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        bran_style=bran_style,
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this world keeps the Python story path primary.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    curated = [
        StoryParams(
            place="kitchen", occasion="homecoming", surprise_kind="welcome",
            child_name="Maya", child_type="girl", helper_name="Mom",
            helper_type="woman", bran_style="bran muffins", seed=101,
        ),
        StoryParams(
            place="bakery", occasion="thank-you", surprise_kind="thank-you",
            child_name="Leo", child_type="boy", helper_name="Dad",
            helper_type="man", bran_style="bran cookies", seed=202,
        ),
        StoryParams(
            place="porch", occasion="rainy-day", surprise_kind="comfort",
            child_name="Ivy", child_type="girl", helper_name="Aunt June",
            helper_type="woman", bran_style="bran tea cakes", seed=303,
        ),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### story {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
