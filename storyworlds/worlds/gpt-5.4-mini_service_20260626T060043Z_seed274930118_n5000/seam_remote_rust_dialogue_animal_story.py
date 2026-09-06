#!/usr/bin/env python3
"""
A standalone storyworld for a small Animal Story domain centered on a seam,
a remote, and rust.

Premise:
- A small animal family lives near a shed full of old things.
- The child animal loves a shiny remote that helps the toys sing and dance.
- A torn seam in a soft blanket, plus a rusty remote battery door, creates a
  small problem.
- A helper explains the trouble in dialogue, then the animals fix it together.

The storyworld simulates the physical state of the remote, blanket seam, and
repair tools, plus the emotional state of the characters.  The prose is driven
by those state changes, not by a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"rust": 0.0, "broken": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "squirrel"}
        male = {"boy", "father", "dad", "man", "rabbit", "fox", "bear"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the shed"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ItemSpec:
    id: str
    label: str
    phrase: str
    region: str = ""
    plural: bool = False
    fragile: bool = False


@dataclass
class StoryParams:
    place: str
    hero_type: str
    friend_type: str
    name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    textile: str
    remote_job: str
    premise: str
    accident: str
    clue: str
    mistaken_try: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shed": Setting(place="the shed", indoor=True, affords={"fix_remote"}),
    "barn": Setting(place="the barn", indoor=True, affords={"fix_remote"}),
    "porch": Setting(place="the porch", indoor=False, affords={"fix_remote"}),
}

HERO_TYPES = ["rabbit", "fox", "bear", "squirrel"]
FRIEND_TYPES = ["rabbit", "fox", "bear", "squirrel"]

ITEMS = {
    "blanket": ItemSpec(
        id="blanket",
        label="blanket",
        phrase="a soft blue blanket",
        fragile=True,
    ),
    "remote": ItemSpec(
        id="remote",
        label="remote",
        phrase="a small toy remote with a springy button",
        fragile=True,
    ),
    "patch": ItemSpec(
        id="patch",
        label="patch",
        phrase="a square cloth patch",
    ),
    "oil": ItemSpec(
        id="oil",
        label="oil",
        phrase="a tiny bottle of oil",
    ),
}

CHARACTER_NAMES = {
    "rabbit": ["Pip", "Nina", "Milo"],
    "fox": ["Tara", "Finn", "Roo"],
    "bear": ["Benny", "Mara", "Tess"],
    "squirrel": ["Suki", "Jax", "Luna"],
}


INCIDENTS = [
    Incident(
        title="shadow-puppet rehearsal",
        textile="the moon-patterned puppet curtain",
        remote_job="change the little stage lights",
        premise="They were rehearsing a shadow-puppet show for the youngest animals",
        accident="a paper moon snagged the curtain seam just as the light remote began to rasp",
        clue="a rust-colored crescent beneath the battery-door hinge matched a damp ring on the shelf",
        mistaken_try="pressing harder only wrinkled the button and pulled the seam wider",
        repair="unpinned the moon, stitched a broad cloth patch behind the seam, and let the grown-up badger clean and oil only the rusty hinge",
        lesson="A careful look can solve two troubles that impatient paws only enlarge",
        ending="The patched moon sailed across the curtain while silver shadows danced without a wobble",
    ),
    Incident(
        title="sleepover story hour",
        textile="the striped reading quilt",
        remote_job="play gentle forest sounds",
        premise="They were arranging a quiet story corner for a rainy-night sleepover",
        accident="a basket wheel caught the quilt seam, and rain blown through the window reached the remote's metal latch",
        clue="one orange flake on the latch and a wet wheel track showed what had happened",
        mistaken_try="hiding the rip beneath a pillow left a cold draft and did nothing for the silent remote",
        repair="moved the basket, dried the shelf, reinforced the seam with a patch and strong backstitches, and asked Owl to loosen the cleaned latch with one careful drop of oil",
        lesson="Telling the truth early gives everyone time to make a lasting repair",
        ending="Rain tapped the roof as the mended quilt rose over two warm noses and the remote whispered cricket songs",
    ),
    Incident(
        title="seedling rescue",
        textile="the canvas sling used to carry seedlings",
        remote_job="guide a toy watering cart",
        premise="They were carrying tiny tomato plants from the shed to the sunny garden",
        accident="a heavy pot split the sling's side seam while old rust locked the remote's battery door",
        clue="the torn threads leaned toward the overloaded corner, and rusty dust fell when the door was tilted",
        mistaken_try="balancing every pot in one paw made the seedlings sway dangerously",
        repair="set the pots down, reinforced the seam with a wide patch, divided the load, and had Mole clean and oil the door hinge away from the batteries",
        lesson="Sharing a load protects both the helpers and the things in their care",
        ending="straight rows of seedlings glittered beside the patched sling while the watering cart clicked home",
    ),
    Incident(
        title="lost duckling signal",
        textile="the bright safety vest",
        remote_job="flash a beacon beside the reed pond",
        premise="They were helping Ranger Otter guide a lost duckling back through the reeds",
        accident="a thorn opened the vest seam, and pond mist had rusted the remote's outer switch hinge",
        clue="yellow thread clung to the thorn while a rusty squeak came from the hinge rather than the button",
        mistaken_try="calling in every direction frightened the duckling farther under the leaves",
        repair="stood quietly, patched the reflective seam, and let the ranger clean and oil the rusty hinge before testing the beacon",
        lesson="Quiet evidence is often more useful than a loud guess",
        ending="The repaired vest shone beside the pond as the duckling followed three soft flashes to its mother",
    ),
    Incident(
        title="museum dinosaur parade",
        textile="the felt tail of a model dinosaur",
        remote_job="make the exhibit walk and roar",
        premise="They were preparing the woodland museum's clockwork dinosaur for visiting cubs",
        accident="the long felt tail caught under a crate and split at its seam while rust stiffened the remote's metal slider",
        clue="a straight drag mark led to the crate, and reddish powder gathered beneath the slider",
        mistaken_try="tugging the tail free made the stuffing peek out like a white cloud",
        repair="lifted the crate together, tucked in the stuffing, patched the seam, and watched Curator Crow service the cleaned slider",
        lesson="Protecting an old treasure matters more than beginning a show on time",
        ending="The dinosaur took one grand patched-tail step and gave a tiny roar that made every cub grin",
    ),
    Incident(
        title="bakery delivery",
        textile="the insulated bun bag",
        remote_job="open the bakery's little delivery cart",
        premise="They were taking warm berry buns to neighbors after a windy morning",
        accident="a sharp crate corner split the bag seam, and salty road spray rusted the remote's key-ring hinge",
        clue="purple crumbs marked the short tear, while the key ring left an orange smudge on a napkin",
        mistaken_try="racing the stuck cart made two buns tumble toward a puddle",
        repair="caught the buns, rounded the crate corner, patched the bag, and asked Beaver to clean and oil the empty remote's key-ring hinge",
        lesson="Slowing down can be the quickest way to deliver something safely",
        ending="Steam curled from the saved buns as the patched bag rested in a cart that rolled smoothly down the lane",
    ),
    Incident(
        title="lantern trail",
        textile="the map pocket on a trail pack",
        remote_job="light marker lanterns along the path",
        premise="They were marking a twilight trail so the firefly choir could find the meadow",
        accident="a bramble tore the map-pocket seam, and rust froze the remote's folding antenna after a dewy night",
        clue="the missing map corner remained on the bramble, and dew beads outlined the rusty antenna joint",
        mistaken_try="following memory alone brought them twice to the same hollow stump",
        repair="returned to the last marker, patched the pocket, pieced together the map, and let an adult clean and oil the antenna joint before raising it",
        lesson="Good explorers retrace their steps when the evidence says they are lost",
        ending="Lanterns blinked one by one toward a meadow where the patched pocket held the map snug and dry",
    ),
    Incident(
        title="tide-pool census",
        textile="the waterproof notebook cover",
        remote_job="take pictures with a small shore camera",
        premise="They were counting anemones for the beach keeper without touching them",
        accident="a shell edge sliced the cover seam, and salty mist left rust on the remote shutter's outer hinge",
        clue="a shell-shaped nick fit the tear, and the orange stain stopped at the hinge instead of reaching the controls",
        mistaken_try="guessing the count from memory mixed up three red anemones and four green ones",
        repair="moved above the tide line, patched the cover, recopied the count, and let the keeper clean and oil the detached hinge",
        lesson="Patient records help small observations become trustworthy knowledge",
        ending="The final photograph showed seven bright anemones beside a notebook whose patched cover snapped shut",
    ),
    Incident(
        title="winter food shelf",
        textile="the grain sack",
        remote_job="raise a model storeroom door",
        premise="They were demonstrating how the animals shared grain during snowy weeks",
        accident="a rough nail opened the sack seam, and rust jammed the remote's little safety cover",
        clue="three kernels lay beneath the nail, and a rusty line followed the edge of the cover",
        mistaken_try="scooping grain while the sack still hung up only fed the spill",
        repair="lowered the sack, covered the nail, stitched on a double patch, and had Tortoise clean and oil the removed safety-cover hinge",
        lesson="Stop the cause of a problem before gathering what it spilled",
        ending="Not one kernel remained on the floor when the patched sack stood beneath the smoothly opening model door",
    ),
    Incident(
        title="river-cleanup raft",
        textile="the mesh collecting pouch",
        remote_job="steer a toy-sized cleanup raft",
        premise="They were collecting floating paper from a shallow stream",
        accident="a forked twig split the pouch seam, and damp storage had rusted the remote's metal wrist-loop pin",
        clue="the twig was still woven through the mesh, and the pin left orange dust on a dry leaf",
        mistaken_try="chasing loose paper downstream scattered it into smaller pieces",
        repair="anchored the raft, removed the twig, bound and patched the mesh, then asked Heron to clean and oil the pin before reattaching the loop",
        lesson="Secure your tools first, then work from one careful place",
        ending="The clear stream carried only reflected clouds past the patched pouch and the raft tied safely at shore",
    ),
    Incident(
        title="orchard weather watch",
        textile="the windsock's red tail",
        remote_job="turn the little weather vane",
        premise="They were checking the orchard before a strong afternoon breeze",
        accident="a sudden gust snapped the windsock seam, while rust gripped the remote's metal dial axle",
        clue="the tear pointed downwind, and the dial made a dry scrape even after the button was released",
        mistaken_try="holding the windsock high by hand nearly pulled the smaller animal off the ladder",
        repair="climbed down, patched the tail on a table, and let Gardener Goat clean and oil the dial axle before testing it from the ground",
        lesson="A safe plan is never spoiled by taking time to climb down",
        ending="The red patched tail streamed east while apples nodded beneath a vane turning freely above them",
    ),
    Incident(
        title="music-box welcome",
        textile="the embroidered welcome banner",
        remote_job="start a row of tiny music boxes",
        premise="They were welcoming a shy new hedgehog to the neighborhood supper",
        accident="the banner seam tore on a hook, and soup steam awakened rust in the remote's sliding cover",
        clue="a loop of gold thread hung from the hook, and an orange streak appeared where steam had cooled on metal",
        mistaken_try="singing louder to hide the broken music only made the new guest cover her ears",
        repair="lowered their voices, patched the banner, moved the remote away from steam, and let Aunt Hare clean and oil its empty cover hinge",
        lesson="Kindness begins by noticing what makes another person comfortable",
        ending="One music box chimed softly as the new hedgehog smiled beneath a banner with a neat golden patch",
    ),
]


# ---------------------------------------------------------------------------
# Reasoning / simulation
# ---------------------------------------------------------------------------

def seam_is_torn(blanket: Entity) -> bool:
    return blanket.meters.get("broken", 0.0) >= THRESHOLD


def remote_is_rusty(remote: Entity) -> bool:
    return remote.meters.get("rust", 0.0) >= THRESHOLD


def can_fix_remote(world: World) -> bool:
    return "patch" in world.entities and "oil" in world.entities


def apply_rust(world: World, remote: Entity) -> None:
    remote.meters["rust"] += 1.0


def repair_seam(world: World, blanket: Entity, patch: Entity) -> None:
    if ("repair_seam", blanket.id) in world.fired:
        return
    world.fired.add(("repair_seam", blanket.id))
    blanket.meters["broken"] = 0.0
    blanket.meters["clean"] += 1.0
    patch.meters["clean"] += 1.0


def oil_remote(world: World, remote: Entity, oil: Entity) -> None:
    if ("oil_remote", remote.id) in world.fired:
        return
    world.fired.add(("oil_remote", remote.id))
    remote.meters["rust"] = max(0.0, remote.meters["rust"] - 1.0)
    oil.meters["clean"] += 1.0


def predict_fix(world: World) -> dict[str, bool]:
    sim = world.copy()
    blanket = sim.get("blanket")
    remote = sim.get("remote")
    patch = sim.get("patch")
    oil = sim.get("oil")
    repair_seam(sim, blanket, patch)
    oil_remote(sim, remote, oil)
    return {
        "seam_fixed": not seam_is_torn(blanket),
        "rust_fixed": not remote_is_rusty(remote),
    }


# ---------------------------------------------------------------------------
# Story text helpers
# ---------------------------------------------------------------------------

OPENINGS = [
    "Morning light reached {place} when {hero}, a young {hero_type}, met {friend}, a {friend_type} with a patient ear.",
    "At {place}, {hero} the {hero_type} and {friend} the {friend_type} promised to finish one useful job before lunch.",
    "The smallest sounds carried through {place} as {hero} the {hero_type} and {friend} the {friend_type} prepared for {title}.",
    "Everyone else was busy when {hero}, a careful {hero_type}, asked {friend} the {friend_type} to help with {title}.",
    "A good plan was taking shape at {place}: {hero} the {hero_type} would watch the remote, and {friend} the {friend_type} would guard the cloth.",
    "Just after breakfast, {hero} the {hero_type} hurried to {place}, where {friend} the {friend_type} was laying out supplies for {title}.",
    "For days, {hero} the {hero_type} and {friend} the {friend_type} had looked forward to {title}; now everything was ready at {place}.",
    "At {place}, {friend} the {friend_type} heard {hero} the {hero_type} humming while they set up the cloth and tested the remote.",
]

REACTIONS = [
    "{hero} wanted to fix everything at once, but {friend} asked for one quiet minute to inspect the evidence.",
    "For a moment {friend}'s ears drooped. Then {hero} fetched a tray so no small part could roll away.",
    "{hero}'s stomach felt tight, because others were counting on them. {friend} reminded {hero} that careful help still counted as help.",
    "Neither animal blamed the other. They named what was damaged and what still worked.",
    "{friend} stopped the activity before anyone could trip or tear the cloth farther. {hero} marked the rusty part with a chalk arrow.",
    "The delay felt enormous to {hero}, yet {friend} noticed that the damage was small enough to mend.",
    "{hero} took one slow breath and placed the remote on a dry towel. {friend} folded the torn edges together without pulling them.",
    "Instead of hiding the accident, they called for the knowledgeable grown-up nearby and explained exactly what they had seen.",
    "{friend} guarded the scene while {hero} drew the clue in a pocket notebook.",
    "They compared the working parts with the damaged ones before choosing a tool.",
    "{hero} felt embarrassed by the first mistake. {friend} answered, \"Changing our plan is how we learn.\"",
    "The two animals made a rule: dry paws near the remote, gentle paws near the seam.",
]

DIALOGUES = [
    ('"The seam tells us where the pull happened," {friend} said. "And the rust tells us where water lingered," {hero} replied.'),
    ('"Should we push the remote again?" asked {hero}. "No," said {friend}. "First we find the cause, then we repair it."'),
    ('"Two problems do not always need one answer," {friend} observed. "Patch the cloth; service the rusty metal," said {hero}.'),
    ('"Let us say what we know," said {hero}. "A seam opened, a remote stuck, and this clue connects each accident," {friend} answered.'),
    ('"Can we still finish?" {hero} asked. {friend} nodded. "Yes, if finishing safely matters more than finishing first."'),
    ('"I nearly made it worse," {hero} admitted. "Then your next careful choice matters even more," {friend} said.'),
    ('"The remote is not a hammer, and thread is not glue," {friend} said. {hero} smiled. "So we choose the right tool for each job."'),
    ('"We need a patch, dry cleaning tools, and an adult for the metal hinge," {hero} counted. "That is a real plan," said {friend}.'),
]

REFLECTIONS = [
    "The repaired seam held when they tested it with a gentle pull.",
    "They tested the remote from a safe distance before returning it to the activity.",
    "They put every tool away and checked the floor for pins, drips, and loose parts.",
    "The first test failed softly, so they adjusted the patch instead of forcing the remote.",
    "A second inspection found no loose thread and no new orange dust.",
    "They wrote the repair date on a small tag so the equipment could be checked again.",
    "They showed a younger animal why the patch spread the pull across stronger cloth.",
    "Before celebrating, they thanked the grown-up who had handled the rusty metal safely.",
    "They moved the remote to a dry box and rolled the cloth instead of crumpling it.",
    "The trouble had cost them time, but it had also taught them how to care for shared things.",
    "They repeated the test once slowly and once during the real activity.",
    "At last, both animals could explain not only what they fixed, but why the damage had happened.",
]


def _stable_seed(*parts: str) -> int:
    return sum((i + 1) * ord(ch) for i, ch in enumerate("|".join(parts)))


def story_paragraphs(
    setting: Setting,
    hero: Entity,
    friend: Entity,
    incident: Incident,
    rng: random.Random,
) -> list[str]:
    values = {
        "place": setting.place,
        "hero": hero.id,
        "friend": friend.id,
        "hero_type": hero.type,
        "friend_type": friend.type,
        "title": incident.title,
    }
    opening = rng.choice(OPENINGS).format(**values)
    reaction = rng.choice(REACTIONS).format(**values)
    dialogue = rng.choice(DIALOGUES).format(**values)
    reflection = rng.choice(REFLECTIONS).format(**values)
    premise = f"{incident.premise}. The remote could {incident.remote_job}, and {incident.textile} needed to hold firm."
    accident = f"Trouble arrived when {incident.accident}."
    clue = f"They looked closely: {incident.clue}."
    mistake = f"At first, {incident.mistaken_try}."
    repair = f"Together they {incident.repair}."
    result = f"The seam held, the remote moved freely again, and no rust remained on its serviced outer part."
    lesson = f'"{incident.lesson}," {friend.id} said.'
    ending_detail = incident.ending[:1].lower() + incident.ending[1:]
    ending = f"As the day settled, {ending_detail}."

    mode = rng.randrange(6)
    if mode == 0:
        return [f"{opening} {premise}", f"{accident} {reaction} {clue} {dialogue}", f"{mistake} {repair} {result}", f"{reflection} {lesson} {ending}"]
    if mode == 1:
        return [f"{opening} {premise}", f"{accident} {mistake} {reaction}", f"{dialogue} {clue}", f"{repair} {result} {lesson} {reflection} {ending}"]
    if mode == 2:
        return [f"{opening} {premise} {accident}", f"{reaction} {dialogue}", f"{clue} {mistake}", f"{repair} {reflection} {result}", f"{lesson} {ending}"]
    if mode == 3:
        return [f"{opening} {premise}", f"{accident} {clue}", f"{mistake} {reaction} {dialogue}", f"{repair} {result}", f"{reflection} {lesson} {ending}"]
    if mode == 4:
        return [f"{opening} {premise}", f"{accident} {dialogue} {mistake}", f"{reaction} {clue} {repair}", f"{result} {reflection} {lesson}", ending]
    return [f"{opening} {premise} {accident}", f"{mistake} {reaction}", f"{clue} {dialogue} {repair}", f"{result} {lesson} {reflection} {ending}"]


# ---------------------------------------------------------------------------
# World screenplay
# ---------------------------------------------------------------------------

def tell(
    setting: Setting,
    hero_type: str,
    friend_type: str,
    hero_name: str,
    friend_name: str,
    seed: Optional[int] = None,
) -> World:
    world = World(setting)
    story_seed = seed if seed is not None else _stable_seed(setting.place, hero_type, friend_type, hero_name, friend_name)
    rng = random.Random(story_seed)
    incident = rng.choice(INCIDENTS)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))

    blanket = world.add(Entity(id="blanket", type="blanket", label=incident.textile, phrase=incident.textile))
    remote = world.add(Entity(id="remote", type="remote", label="remote", phrase=f"a remote used to {incident.remote_job}"))
    patch = world.add(Entity(id="patch", type="patch", label="patch", phrase="a sturdy cloth patch"))
    oil = world.add(Entity(id="oil", type="oil", label="oil", phrase="a drop of oil for an outer metal hinge"))

    hero.memes["love"] += 1.0
    hero.memes["curiosity"] += 1.0
    friend.memes["joy"] += 1.0

    blanket.meters["broken"] += 1.0
    apply_rust(world, remote)
    hero.memes["worry"] += 1.0
    friend.memes["worry"] += 1.0

    if not can_fix_remote(world):
        raise StoryError("This story needs both a patch and oil so the animals can fix the seam and the rust.")

    repair_seam(world, blanket, patch)
    oil_remote(world, remote, oil)
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0

    for paragraph in story_paragraphs(setting, hero, friend, incident, rng):
        world.say(paragraph)
        world.para()

    world.facts = {
        "hero": hero,
        "friend": friend,
        "blanket": blanket,
        "remote": remote,
        "patch": patch,
        "oil": oil,
        "setting": setting,
        "seam_fixed": not seam_is_torn(blanket),
        "rust_fixed": not remote_is_rusty(remote),
        "incident": incident,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    incident: Incident = f["incident"]  # type: ignore[assignment]
    return [
        f"Write a short Animal Story about {incident.title}, a torn seam, a rusty remote, and a careful repair.",
        f"Tell a gentle story where {hero.id} and {friend.id} use dialogue and evidence to solve the trouble during {incident.title}.",
        f"Write a child-friendly story in which the animals learn that {incident.lesson.lower()}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    friend: Entity = f["friend"]  # type: ignore[assignment]
    blanket: Entity = f["blanket"]  # type: ignore[assignment]
    remote: Entity = f["remote"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    incident: Incident = f["incident"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What were {hero.id} and {friend.id} preparing for?",
            answer=f"They were preparing for {incident.title} at {setting.place}. {incident.premise}.",
        ),
        QAItem(
            question=f"What damaged {blanket.label} and the remote?",
            answer=f"The trouble began when {incident.accident}. That opened the seam and left a rusty remote part stuck.",
        ),
        QAItem(
            question=f"What clue helped the two animals understand the trouble?",
            answer=f"They discovered that {incident.clue}. The clue showed them where to focus the repair.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} repair both problems safely?",
            answer=f"Together they {incident.repair}. The repaired seam held, and the remote's serviced outer part moved freely again.",
        ),
        QAItem(
            question=f"What lesson did {friend.id} express after the repair?",
            answer=f'{friend.id} said, "{incident.lesson}." Their final careful test showed why that lesson mattered.',
        ),
        QAItem(
            question="What final image showed that the animals' work succeeded?",
            answer=f"The story ended with this image: {incident.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a seam?",
            answer="A seam is the line where two pieces of cloth are stitched together.",
        ),
        QAItem(
            question="What is rust?",
            answer="Rust is a reddish, flaky coating that can form on metal when it gets wet for a long time.",
        ),
        QAItem(
            question="What does a remote do?",
            answer="A remote lets you control a toy or machine from a little distance away.",
        ),
        QAItem(
            question="Why can oil help a stuck part?",
            answer="With an adult's help, a suitable oil can help a cleaned outer hinge move freely. It should not be dripped into a remote's electronics or battery compartment.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A seam is torn when a blanket is broken.
torn_seam(B) :- blanket(B), broken(B).

% A remote is rusty when it has rust.
rusty_remote(R) :- remote(R), rust(R).

% A fix is reasonable when the world contains both a patch and oil.
has_fix :- patch(P), oil(O), blanket(B), remote(R), torn_seam(B), rusty_remote(R).

valid_story(Place, HeroType, FriendType) :-
    setting(Place),
    animal(HeroType),
    animal(FriendType),
    has_fix.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for t in HERO_TYPES:
        lines.append(asp.fact("animal", t))
    for t in FRIEND_TYPES:
        lines.append(asp.fact("animal", t))
    lines.append(asp.fact("blanket", "blanket"))
    lines.append(asp.fact("remote", "remote"))
    lines.append(asp.fact("patch", "patch"))
    lines.append(asp.fact("oil", "oil"))
    lines.append(asp.fact("broken", "blanket"))
    lines.append(asp.fact("rust", "remote"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(place, h, f) for place in SETTINGS for h in HERO_TYPES for f in FRIEND_TYPES}
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: ASP gate matches Python expectations ({len(got)} combos).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("only in ASP:", sorted(got - expected))
    print("only in Python:", sorted(expected - got))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="shed", hero_type="rabbit", friend_type="fox", name="Pip", friend_name="Tara"),
    StoryParams(place="barn", hero_type="squirrel", friend_type="bear", name="Suki", friend_name="Benny"),
    StoryParams(place="porch", hero_type="fox", friend_type="rabbit", name="Finn", friend_name="Nina"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with a seam, a remote, and rust.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    name = args.name or rng.choice(CHARACTER_NAMES[hero_type])
    friend_name = args.friend_name or rng.choice(CHARACTER_NAMES[friend_type])

    if name == friend_name:
        friend_name = rng.choice([n for n in CHARACTER_NAMES[friend_type] if n != friend_name])

    return StoryParams(
        place=place,
        hero_type=hero_type,
        friend_type=friend_type,
        name=name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        params.hero_type,
        params.friend_type,
        params.name,
        params.friend_name,
        params.seed,
    )
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} compatible story triples:")
        for row in asp_valid_stories():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} ({p.hero_type} + {p.friend_type})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
