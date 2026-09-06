#!/usr/bin/env python3
"""
storyworlds/worlds/progeny_cemetery_semi_sharing_magic_dialogue_comedy.py
=========================================================================

A tiny comedy storyworld about a family visit to a cemetery, a parked semi, and
a little bit of sharing magic that helps everyone solve a confused, polite mess.

Premise:
- A child and a parent visit a cemetery to leave flowers.
- A shiny semi truck is blocking the narrow lane near the gate.
- The child wants to help by using a shared "magic" trick: borrowing, splitting,
  and returning small things kindly.

Tension:
- The child wants to keep something magical instead of sharing it.
- The parent worries that the cemetery should stay quiet and respectful.
- The semi driver needs a way through, and the child keeps asking questions.

Turn:
- Dialogue reveals that the "magic" is just a friendly sharing rule: one
  lantern, two holders, and a soft way to walk together.

Resolution:
- The child shares the lantern, the semi gets enough room to back up, and the
  flowers reach the right grave without any fuss.
- The ending image proves what changed: the child is smiling, the parent is
  laughing, and the cemetery lane is calm again.
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

SETTINGS = {
    "cemetery_gate": {
        "place": "the cemetery gate",
        "detail": "The cemetery lane was narrow, and old stone markers stood quietly along the path.",
        "affords": {"visit"},
    },
}

NAMES = ["Maya", "Leo", "Nia", "Owen", "Iris", "Ben", "Mina", "Toby"]
NAME_GENDERS = {
    "Maya": "girl", "Leo": "boy", "Nia": "girl", "Owen": "boy",
    "Iris": "girl", "Ben": "boy", "Mina": "girl", "Toby": "boy",
}
PARENT_NAMES = ["Mom", "Dad", "Aunt Jo", "Uncle Ray"]
TRAITS = ["curious", "gentle", "silly", "cheerful", "careful", "bouncy"]

INCIDENTS = [
    {
        "id": "windy_cards",
        "arrival": "A gust skipped through the gate just as the semi delivered boxes of memorial cards.",
        "problem": "The cards whirled across two paths, and the driver stopped well short of them.",
        "mistake": "At first, the child tried to catch every card alone and caught only a leaf on their head.",
        "clue": "The lantern made the tiny leaf emblems on each family's cards shimmer in matching colors.",
        "plan": "The visitors shared empty flower trays, sorting one glowing family emblem into each tray while the adults kept the lane closed.",
        "driver_line": "I can wait; paper is quicker than a truck only when the wind is helping it!",
        "child_line": "Then our sharing magic needs more hands, not faster feet.",
        "result": "When the last card was safe, the caretaker signaled the driver to use the clear delivery bay.",
        "ending": "Behind them, four neat trays rested beside the office door, and one harmless leaf wore a name card like a hat.",
        "lesson": "asking others to share a careful job can work better than racing alone",
        "object": "memorial cards",
    },
    {
        "id": "pebble_latch",
        "arrival": "The semi arrived with young trees, but the cemetery's service gate would not open.",
        "problem": "The driver waited outside while the caretaker tugged the latch without forcing it.",
        "mistake": "The child announced that the enormous truck must have frightened the tiny gate shut.",
        "clue": "Shared lantern light revealed a round pebble wedged beneath the latch plate.",
        "plan": "The child held the light, the parent fetched the caretaker's brush, and the caretaker cleared the pebble and tested the gate.",
        "driver_line": "Good. My semi is big, but it has never won an argument with a pebble.",
        "child_line": "The pebble was small enough to be the boss for one minute.",
        "result": "Only the caretaker opened the gate; then the driver rolled slowly to the marked unloading place.",
        "ending": "At sunset, the new trees stood straight, and the famous pebble sat harmlessly in a little gravel bucket.",
        "lesson": "a small clue can solve a large-looking problem when people share what they notice",
        "object": "young trees",
    },
    {
        "id": "rolling_buckets",
        "arrival": "A delivery cart bumped a curb while a semi waited to bring soil to the cemetery garden.",
        "problem": "Three empty flower buckets rolled into the lane, so the driver parked and set the brake.",
        "mistake": "The child chased the loudest bucket, which curved away as if it had changed its mind.",
        "clue": "The lantern cast bright rings around the buckets whenever they crossed the flat paving stones.",
        "plan": "Everyone shared jobs: the child pointed from the path, the parent gathered buckets, and the caretaker checked the lane.",
        "driver_line": "Those buckets have wheels in their imaginations.",
        "child_line": "This one is pretending to be a very tiny semi.",
        "result": "The caretaker stacked the buckets, inspected the route, and waved the semi toward the garden bay.",
        "ending": "The smallest bucket ended upside down beside the flowers, looking quite proud of its parking job.",
        "lesson": "sharing clear roles keeps a funny scramble from becoming an unsafe one",
        "object": "flower buckets",
    },
    {
        "id": "mixed_tree_tags",
        "arrival": "The semi brought six memorial saplings whose rain-spotted labels had come loose.",
        "problem": "No one wanted a tree planted beside the wrong family marker, so unloading paused.",
        "mistake": "The child guessed that the tallest tree must belong to the family with the longest surname.",
        "clue": "Under the shared lantern, pressed leaf shapes on the labels matched leaves tied safely to each root wrap.",
        "plan": "The parent read the names, the child matched leaf shapes, and the caretaker checked every result against the cemetery map.",
        "driver_line": "A tree cannot read its tag, so I am glad this team can.",
        "child_line": "My first rule about tall trees and long names was extremely scientific-looking nonsense.",
        "result": "The adults confirmed all six matches before the driver and caretaker unloaded the saplings.",
        "ending": "Six correct tags fluttered beneath six young trees, each beside the family that had chosen it.",
        "lesson": "good evidence should be shared and checked instead of replaced by a confident guess",
        "object": "memorial saplings",
    },
    {
        "id": "backward_arrows",
        "arrival": "After rain, a semi carrying benches stopped at a fork inside the cemetery grounds.",
        "problem": "An arrow reflected in a puddle seemed to point the opposite way, confusing everyone for a moment.",
        "mistake": "The child leaned toward the puddle and declared that the road signs had turned upside down for lunch.",
        "clue": "When parent and child shared the lantern above the dry sign, its real arrow and the watery reflection became easy to compare.",
        "plan": "They stayed on the footpath and read the sign aloud while the caretaker radioed the approved route to the driver.",
        "driver_line": "My semi follows roads, not puddle roads.",
        "child_line": "Good, because the puddle route ends in one very damp cloud.",
        "result": "The caretaker guided the semi to the bench bay, far from visitors and grave markers.",
        "ending": "As they left, the puddle still pointed backward, but now it only fooled a curious robin.",
        "lesson": "sharing observations helps people tell a real direction from a misleading reflection",
        "object": "memorial benches",
    },
    {
        "id": "quiet_chime",
        "arrival": "A semi delivered a carved remembrance bell, wrapped so it would stay silent in the cemetery.",
        "problem": "A faint ding came from the cargo whenever the wind moved, and the driver worried that a strap was loose.",
        "mistake": "The child whispered that a very polite ghost might be ringing for room service.",
        "clue": "The shared lantern showed one ribbon end tapping a metal corner; the bell itself was secure.",
        "plan": "The child pointed from a safe distance while the driver and caretaker rewrapped the ribbon and checked every strap.",
        "driver_line": "Mystery solved: one ribbon, no ghost, and no room service.",
        "child_line": "Please tell the ribbon that breakfast ends at ten.",
        "result": "After the adults finished their safety check, the semi continued quietly to the installation area.",
        "ending": "The wrapped bell made no sound at all, though the ribbon gave one last embarrassed flutter.",
        "lesson": "a shared clue can replace a spooky guess with a calm, testable answer",
        "object": "remembrance bell",
    },
    {
        "id": "bench_pieces",
        "arrival": "The semi brought pieces for two new memorial benches to the cemetery workshop.",
        "problem": "Two matching crates had swapped chalk marks, and unloading the wrong one would waste time.",
        "mistake": "The child proposed choosing the crate that looked more bench-like, although both looked exactly like boxes.",
        "clue": "Lantern light picked out shallow carved numbers beneath the dusty handles.",
        "plan": "They shared a measuring tape and the order sheet: the child called numbers, the parent read dimensions, and the caretaker verified them.",
        "driver_line": "I have inspected both boxes. Neither one is willing to admit it is a bench.",
        "child_line": "They are shy benches. We must use mathematics.",
        "result": "The caretaker marked the correct crate, and trained adults moved it into the workshop.",
        "ending": "A week later, the finished bench held flowers, two visitors, and absolutely no shy cardboard box.",
        "lesson": "sharing measurements and checking labels makes teamwork more reliable",
        "object": "bench pieces",
    },
    {
        "id": "lost_photo",
        "arrival": "A family gathering began as a semi finished delivering stone safely near the cemetery office.",
        "problem": "An old family photograph slipped from the progeny album before anyone could identify the people in it.",
        "mistake": "The child searched inside the semi's enormous shadow, where every gray leaf looked like a photograph.",
        "clue": "The driver's mirror flashed shared lantern light onto a pale rectangle tucked behind the visitor map.",
        "plan": "The driver kept the semi parked, the parent held the lantern, and the child asked the caretaker to retrieve the photograph.",
        "driver_line": "My mirror has finally taken a picture of a picture.",
        "child_line": "That makes it the cemetery's fanciest detective.",
        "result": "The photograph returned to its sleeve, and the older relatives shared the names of the family members pictured there.",
        "ending": "By the gate, three generations bent over the album while the mirror reflected a neat square of evening sky.",
        "lesson": "family history grows clearer when progeny share memories and protect old records",
        "object": "family photograph",
    },
    {
        "id": "ribbon_map",
        "arrival": "The semi arrived with flat stones for a repaired path, but a map ribbon had torn free.",
        "problem": "Without the ribbon, the driver could not tell which service bay was open and wisely stayed parked.",
        "mistake": "The child offered to point toward whichever bay had the friendliest-looking wheelbarrow.",
        "clue": "The lantern made three tiny dots on the loose ribbon gleam beside three matching dots on the official map.",
        "plan": "Parent and child shared the ribbon ends while the caretaker aligned the dots and radioed the correct route.",
        "driver_line": "I trust a checked map more than a charming wheelbarrow.",
        "child_line": "The wheelbarrow will be disappointed, but it will recover.",
        "result": "The caretaker directed the semi to the open bay, and the closed path remained protected.",
        "ending": "The repaired ribbon lay flat on the map while the friendly wheelbarrow waited beside a stack of stone.",
        "lesson": "shared tools are most useful when people check them together",
        "object": "path stones",
    },
    {
        "id": "seed_packets",
        "arrival": "A semi brought garden soil while families placed seed packets beside the cemetery's remembrance beds.",
        "problem": "A breeze mixed packets meant for sunny beds with packets meant for shade.",
        "mistake": "The child suggested planting every seed halfway between sun and shade so nobody would complain.",
        "clue": "The shared lantern revealed little sun and moon stamps printed in pale ink on the packet corners.",
        "plan": "The progeny of several families formed a quiet line, sharing baskets while the gardener checked each stamp.",
        "driver_line": "Even my semi cannot deliver half a sunshine.",
        "child_line": "Then we should stop asking it to do advanced weather.",
        "result": "The packets reached the correct beds before the gardener signaled the semi into the soil bay.",
        "ending": "Sun packets and moon packets sat in separate baskets, each wearing a bright paper label.",
        "lesson": "many descendants can share a respectful task without losing track of careful details",
        "object": "seed packets",
    },
    {
        "id": "fallen_cones",
        "arrival": "A grounds crew's semi waited beyond the gate while families visited the cemetery after a storm.",
        "problem": "Orange safety cones had fallen over, so the service lane boundary was unclear.",
        "mistake": "The child tried to make one cone stand by whispering a magic command from the footpath.",
        "clue": "The lantern's shared beam showed muddy footprints leading from the cones to the caretaker's storage cart.",
        "plan": "The family reported the clue and waited; the caretaker reset the cones and inspected the entire boundary.",
        "driver_line": "That cone understood your magic perfectly and chose to keep napping.",
        "child_line": "It is a semi-professional napper near a professional semi.",
        "result": "Once the caretaker declared the lane safe, the driver moved at walking speed to the work area.",
        "ending": "Every cone stood bright and straight, except its long shadow, which continued lying down.",
        "lesson": "sharing a safety concern with the responsible adult is a brave and useful action",
        "object": "safety cones",
    },
    {
        "id": "memory_tiles",
        "arrival": "The semi delivered boxes of small memory tiles made by the progeny of local families.",
        "problem": "One box label had smeared, and the caretaker would not place any tile without confirming its garden.",
        "mistake": "The child sorted by favorite color until two blue tiles politely disagreed by having different flower symbols.",
        "clue": "When the lantern was shared over the box, hidden wax rubbings showed a rose, an oak leaf, or a star on every tile.",
        "plan": "The child grouped symbols, the parent read the garden list, and the caretaker checked names before adults moved the boxes.",
        "driver_line": "Those blue tiles have presented a strong argument.",
        "child_line": "I withdraw my case and appoint the flowers as judges.",
        "result": "Each box reached its proper garden, and no memorial name was separated from its family's design.",
        "ending": "Rose, oak, and star tiles formed three tidy rows beneath the lantern's warm circle.",
        "lesson": "respectful work means sharing evidence and correcting a mistake without embarrassment",
        "object": "memory tiles",
    },
]

ROUTES = [
    ("On a quiet visit", "That was when", "Soon"),
    ("Just inside the gate", "After the first idea failed,", "With everyone helping"),
    ("One gentle afternoon", "Then", "A few careful minutes later"),
    ("During a family visit", "Instead of guessing again,", "Once the plan was checked"),
    ("Near the cemetery office", "At last,", "By working in turns"),
    ("Beneath the old trees", "With the semi still safely parked,", "After a final safety check"),
    ("While visitors walked quietly", "A small detail finally mattered:", "Because each person had a job"),
    ("At the edge of the remembrance garden", "The better plan began with this clue:", "Before long"),
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearer: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "aunt"}
        male = {"boy", "father", "dad", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    incident: int = 0
    route: int = 0
    humor: int = 0
    cadence: int = 0
    beat: int = 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedy storyworld about a cemetery visit, a semi, and sharing magic."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "cemetery_gate"
    name = args.name or rng.choice(NAMES)
    gender = args.gender or NAME_GENDERS[name]
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        incident=rng.randrange(len(INCIDENTS)),
        route=rng.randrange(len(ROUTES)),
        humor=rng.randrange(8),
        cadence=rng.randrange(32),
        beat=rng.randrange(4096),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting for this storyworld.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The child must be a girl or a boy in this storyworld.")


def _activity_name() -> str:
    return "visit"


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    place_cfg = SETTINGS[params.place]
    world = World(place=place_cfg["place"])

    child_type = params.gender
    parent_type = {"Mom": "mother", "Dad": "father", "Aunt Jo": "aunt", "Uncle Ray": "uncle"}[params.parent]

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=child_type,
        label=params.name,
        meters={"curiosity": 1.0},
        memes={"joy": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=params.parent,
        meters={"patience": 1.0},
        memes={"warmth": 1.0},
    ))
    driver = world.add(Entity(
        id="Driver",
        kind="character",
        type="adult",
        label="the semi driver",
        meters={"worry": 1.0},
        memes={"politeness": 1.0},
    ))
    semi = world.add(Entity(
        id="Semi",
        kind="thing",
        type="semi",
        label="semi",
        phrase="a big red semi",
        meters={"parked": 1.0, "safe_to_move": 0.0},
    ))
    lantern = world.add(Entity(
        id="Lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase="a tiny brass lantern",
        owner=child.id,
        wearer=child.id,
        meters={"shine": 1.0},
        memes={"magic": 1.0},
    ))
    flowers = world.add(Entity(
        id="Flowers",
        kind="thing",
        type="flowers",
        label="flowers",
        phrase="a bunch of yellow flowers",
        owner=parent.id,
        plural=True,
    ))
    grave = world.add(Entity(
        id="Grave",
        kind="thing",
        type="grave",
        label="grave",
        phrase="a family grave",
    ))

    incident = INCIDENTS[params.incident % len(INCIDENTS)]
    opening, turn, resolution = ROUTES[params.route % len(ROUTES)]
    magic_descriptions = [
        "a brass lantern whose painted symbols glow when two people hold its handle",
        "a little lantern that reveals pale markings only when its light is shared",
        "a family lantern nicknamed Sharing Magic because it works best in two pairs of hands",
        "a warm lantern that never moves objects but often helps people notice the same clue",
        "a pocket lantern whose soft light becomes steadier when someone helps hold it",
        "an old brass lantern used by the family for shared searching",
        "a tiny light whose only spell is helping careful people look together",
        "a lantern with painted stars that brighten when its holder accepts help",
    ]
    chuckles = [
        "The driver's eyebrows rose so high that they seemed ready to inspect the truck roof.",
        "The child tried a solemn detective face, but one cheek kept turning into a grin.",
        "Parent hid a laugh behind the flower paper, which crinkled suspiciously.",
        "Even the caretaker smiled, though the stone angels remained excellent at keeping straight faces.",
        "A crow gave one doubtful caw, as if reviewing the plan from a nearby branch.",
        "The driver nodded gravely, then ruined the effect with a tiny snort of laughter.",
        "The child bowed to the clue, nearly losing a hat that was not actually being worn.",
        "Parent's quiet chuckle sounded like a zipper trying not to wake anyone.",
    ]
    family_notes = [
        "That made the visit part remembrance and part family-history lesson.",
        "The child liked knowing that one formal word could hold so many generations.",
        "They paused to read a few names and think about the families connected to them.",
        "The explanation made the old album in the parent's bag feel newly important.",
    ]
    cooperation_notes = [
        "Each person repeated their job before anyone began.",
        "They checked the plan once aloud and once with the caretaker.",
        "Nobody rushed; sharing also meant leaving room for another person to check.",
        "The child discovered that a useful helper can point, listen, and wait.",
    ]
    magic_notes = [
        "The warm circle joined their hands without pretending to replace good judgment.",
        "Its glow made the clue visible, while their shared thinking made the clue useful.",
        "The little light seemed brightest whenever someone said what they had noticed.",
        "Its painted stars shone over a plan that every helper understood.",
    ]
    farewell_notes = [
        "They thanked the caretaker and gave the driver a quiet wave.",
        "Before leaving, they checked that the visitor path was calm again.",
        "The family took one last peaceful look along the row of memorials.",
        "Their final whisper was a thank-you to everyone who had helped.",
    ]
    observations = [
        "paused at the path edge and looked from the problem to the caretaker",
        "counted the safe landmarks without stepping toward the service lane",
        "noticed which objects were still and which ones had changed",
        "listened for a full moment before offering another theory",
        "compared the driver's view with the view from the visitor path",
        "pointed out the smallest detail instead of making the biggest guess",
        "asked which part of the scene the caretaker wanted everyone to leave untouched",
        "described the puzzle aloud so each helper could add one observation",
    ]
    responses = [
        "said that careful noticing was already a useful share",
        "agreed that a safe plan should begin before anyone picked something up",
        "reminded everyone that waiting can be an active part of helping",
        "asked the caretaker to confirm which task a child could safely do",
        "suggested separating facts from funny guesses",
        "praised the question and asked for one piece of evidence",
        "made room for the driver to explain what could be seen from the cab",
        "turned the observations into a short checklist",
    ]
    cadence = params.cadence % 32
    family_note = family_notes[cadence & 3]
    cooperation_note = cooperation_notes[(cadence >> 2) & 3]
    magic_note = magic_notes[(cadence >> 3) & 3]
    farewell_note = farewell_notes[(cadence >> 1) & 3]
    observation = observations[params.beat & 7]
    response = responses[(params.beat >> 3) & 7]
    chuckle = chuckles[params.humor % len(chuckles)].replace("Parent", params.parent)
    clue = incident["clue"][0].lower() + incident["clue"][1:]
    plan = incident["plan"].replace("The child", params.name).replace("the child", params.name)
    plan = plan.replace("Parent and child", f"{params.parent} and {params.name}")
    plan = plan.replace("the parent", params.parent)

    world.say(
        f"{opening}, {params.name}, a {params.trait} {params.gender}, came with {params.parent} to {world.place} to leave yellow flowers."
    )
    world.say(
        f"{params.parent} explained that progeny means someone's children and later descendants; many families' progeny cared for the memorials there."
    )
    world.say(family_note)
    world.say(place_cfg["detail"])
    world.say(incident["arrival"])
    world.para()
    world.say(
        f"The family carried {magic_descriptions[params.humor % len(magic_descriptions)]}."
    )
    world.say(incident["problem"])
    world.say(incident["mistake"])
    world.say(f"Before acting again, {params.name} {observation}. {params.parent} {response}.")
    world.say(
        f'{params.parent} said, "We will stay on the visitor path. The driver and caretaker are the only people who decide when the semi moves."'
    )
    world.say(
        f'The driver called, "{incident["driver_line"]}"'
    )
    world.say(
        f'{params.name} replied, "{incident["child_line"]}"'
    )
    world.say(chuckle)
    world.para()
    world.say(f"{turn} {clue}")
    world.say(plan)
    world.say(cooperation_note)
    world.say(magic_note)
    world.say(f"Their dialogue stayed quiet and respectful, but the jokes made the careful work feel light.")
    world.para()
    world.say(f"{resolution}, {incident['result'][0].lower() + incident['result'][1:]}")
    world.say(
        f"They placed the yellow flowers at the family grave. {params.name} learned that {incident['lesson']}."
    )
    world.say(
        "That was the lantern's sharing magic: it did not push a semi or disturb a grave; it helped people share light, evidence, and responsibility."
    )
    world.say(farewell_note)
    world.say(incident["ending"])

    semi.meters["safe_to_move"] = 1.0
    semi.meters["parked"] = 0.0
    lantern.owner = child.id
    lantern.caretaker = parent.id
    child.memes["sharing"] = 1.0

    world.facts.update(
        child=child,
        parent=parent,
        driver=driver,
        semi=semi,
        lantern=lantern,
        flowers=flowers,
        grave=grave,
        place=place_cfg,
        params=params,
        incident=incident,
        plan=plan,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f'Write a funny, respectful story for a young child about {p.name}, a cemetery visit, and a parked semi carrying {incident["object"]}.',
        f"Tell a gentle comedy in which sharing a magic lantern helps people notice evidence and solve a practical problem safely.",
        f'Write a story with dialogue, family progeny, a cemetery, a semi truck, and the lesson that {incident["lesson"]}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    plan = world.facts["plan"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a {p.trait} {p.gender} who visits the cemetery with {p.parent} to leave flowers.",
        ),
        QAItem(
            question="What practical problem interrupted the cemetery visit?",
            answer=f"{incident['problem']} The adults kept the semi parked until the situation was checked.",
        ),
        QAItem(
            question="What clue did the shared lantern help everyone notice?",
            answer=incident["clue"],
        ),
        QAItem(
            question="How did everyone solve the problem safely?",
            answer=f"{plan} {incident['result']}",
        ),
        QAItem(
            question=f"What did {p.name} learn?",
            answer=f"{p.name} learned that {incident['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cemetery?",
            answer="A cemetery is a quiet place where people bury the dead and leave flowers or visit graves.",
        ),
        QAItem(
            question="What is a semi?",
            answer="A semi is a very big truck used to carry heavy things on the road.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something with you.",
        ),
        QAItem(
            question="What does progeny mean?",
            answer="Progeny means a person's children or descendants. It is a formal word often used when talking about family generations.",
        ),
        QAItem(
            question="What is a lantern for?",
            answer="A lantern is a light you can carry to help you see in the dark.",
        ),
    ]


ASP_RULES = r"""
#show compatible/1.
compatible(story) :- child_visit, blocked_lane, sharing_magic, dialogue_fix.
"""


def asp_facts() -> str:
    return "\n".join([
        "child_visit.",
        "blocked_lane.",
        "sharing_magic.",
        "dialogue_fix.",
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cemetery_gate", name="Maya", gender="girl", parent="Mom", trait="curious", incident=0, route=0, humor=0, cadence=2, beat=11),
    StoryParams(place="cemetery_gate", name="Leo", gender="boy", parent="Dad", trait="silly", incident=5, route=3, humor=5, cadence=17, beat=93),
    StoryParams(place="cemetery_gate", name="Nia", gender="girl", parent="Aunt Jo", trait="gentle", incident=11, route=6, humor=3, cadence=29, beat=201),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern: child_visit, blocked_lane, sharing_magic, dialogue_fix")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
            header = f"### {p.name}: cemetery comedy with a semi and magic"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
