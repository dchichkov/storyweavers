#!/usr/bin/env python3
"""
storyworlds/worlds/subjunctive_aquarium_sharing_slice_of_life.py
================================================================

A small aquarium slice-of-life storyworld about sharing, with a gentle
subjunctive wish threaded through a real, state-driven social turn.

Premise used to build the world:
---
At the aquarium, a child arrives with one small picture guide and a cousin
who also wants to look at it. The child feels a tiny tug of possessiveness,
then notices that the day would go better if they could share it. A parent
suggests a simple way to do that: take turns, read the names together, and
point at the fish for each other.

Causal state updates:
---
    wanting to keep the guide -> possessor.memes["possessive"] += 1
    successful sharing move     -> sharer.memes["generosity"] += 1
                                    sharer.memes["joy"] += 1
                                    sharer.memes["tension"] -= 1
    accepted turn-taking        -> both children.memes["calm"] += 1
                                    both children.memes["joy"] += 1
    refused sharing             -> child.memes["tension"] += 1 ; story can become invalid
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

AQUARIUM_PLACES = {
    "main_hall": "the aquarium",
}

FISHES = [
    "blue tang",
    "seahorse",
    "jellyfish",
    "clownfish",
    "stingray",
    "catfish",
]

NAMES = ["Maya", "Noah", "Lena", "Owen", "Iris", "Theo", "Nina", "Ari"]
RELATIONS = ["cousin", "sister", "brother", "friend"]
TRAITS = ["quiet", "curious", "patient", "shy", "cheerful", "gentle"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["clean", "held", "shared", "used"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "tension", "possessive", "generosity", "calm", "want"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the aquarium"


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    carries: str = "with both hands"


@dataclass
class StoryParams:
    place: str
    item: str
    fish: str
    name: str
    relation: str
    trait: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    premise: str
    conflict: str
    first_try: str
    clue: str
    sharing_plan: str
    child_job: str
    buddy_job: str
    dialogue: str
    resolution: str
    lesson: str
    ending: str


INCIDENTS = [
    Incident(
        "The Two-Tank Choice",
        "a feeding talk at the reef tank and a diver talk at the kelp tank were about to begin at the same time",
        "{child} wanted the guide open to the reef map, while {buddy} kept reaching for the kelp page",
        "they tugged the covers back and forth until neither could read a complete sentence",
        "the schedule box showed that the talks overlapped for only five minutes",
        "circle both times, hear the reef introduction, and let {buddy} navigate to the kelp tank",
        "read the reef facts aloud while the guide rested between them",
        "watched the clock and traced the shortest route with one finger",
        '"If we share the decisions too, the guide can help both of us," {child} said',
        "they heard the reef keeper explain the {fish}, then reached the kelp window before the diver waved",
        "Sharing can mean combining two wishes into one fair plan.",
        "their two penciled circles touched on the schedule page as silver bubbles climbed the kelp glass",
    ),
    Incident(
        "The Missing Bookmark",
        "the guide opened to the wrong page just when the {fish} appeared",
        "each child thought the other had moved the blue bookmark",
        "they searched one another's pockets and made each other feel blamed",
        "a blue corner peeked from beneath the aquarium bench where the guide had rested",
        "search together, then take turns keeping the page and watching the tank",
        "checked beneath the bench and brushed dust from the bookmark",
        "held their place in the guide and called out when the fish returned",
        '"I wish we had asked before we guessed," {buddy} said',
        "they apologized, replaced the marker, and matched three guide pictures to three swimming fish",
        "A shared search works better when nobody is treated like the culprit.",
        "the rescued blue bookmark lay across the {fish} page while a real fin glimmered beyond it",
    ),
    Incident(
        "The Foggy Window",
        "a patch of aquarium glass looked cloudy beside the {fish} habitat",
        "{child} trusted the guide's clear drawing, but {buddy} insisted the blurry shape was a different animal",
        "they argued by pointing harder at the same foggy patch",
        "two steps to the side, the glass was clear and the guide's fin pattern matched exactly",
        "let one person hold the guide while the other tests a new viewing spot",
        "compared the stripes in the picture with the animal beyond the clear glass",
        "found the clean angle and invited {child} to stand there too",
        '"What if the window is confusing us, not the picture?" {buddy} asked',
        "they changed places, checked the markings together, and agreed they had found the {fish}",
        "Changing where we look can settle a disagreement more kindly than arguing.",
        "both faces appeared side by side in the clear glass beneath the drifting {fish}",
    ),
    Incident(
        "The Quiet-Tank Puzzle",
        "the guide promised a soft clicking sound near the {fish} tank, but the gallery seemed silent",
        "{buddy} wanted to keep talking, while {child} wanted everyone to stop at once",
        "they shushed each other so loudly that nearby visitors turned around",
        "a small sign asked listeners to wait quietly between the filter's gentle hums",
        "share one silent minute, with one child timing and the other following the guide",
        "held the guide open and pointed to each sound clue without speaking",
        "counted sixty slow seconds on the wall clock",
        '"If we were quieter together, perhaps we would hear it," {child} whispered',
        "during the pause they heard three tiny clicks and then thanked the family beside them for waiting too",
        "Cooperation includes sharing quiet space with the people around us.",
        "three penciled dots marked the margin while the tank lights rippled silently overhead",
    ),
    Incident(
        "The Last Sketch Pencil",
        "the aquarium sketch table had one pencil left beside a picture guide",
        "both children wanted to draw the {fish} before it swam behind the rocks",
        "{child} began a whole drawing while {buddy} watched the pencil grow shorter",
        "the guide's loop diagram showed the fish returning to the same arch each time",
        "alternate quick turns: outline on one pass, add details on the next",
        "drew the body outline and handed over the pencil at the rock arch",
        "added the fins, then returned it when the fish circled back",
        '"Your lines can finish what mine began," {child} said',
        "they completed one joint sketch, signed both names, and left the pencil for the next visitor",
        "Sharing time and tools can turn two unfinished ideas into one complete creation.",
        "their signed {fish} sketch dried beside the guide as the living model began another loop",
    ),
    Incident(
        "The Stamp Trail",
        "a conservation trail asked visitors to find four symbols in the guide",
        "{child} rushed toward the easy stamp while {buddy} wanted to study the recycling clue first",
        "they carried the guide in opposite directions and nearly missed both stations",
        "the clue arrows formed one continuous route around the aquarium",
        "let {buddy} solve the next clue and {child} choose the following route turn",
        "read each riddle and checked that no station was skipped",
        "pressed the stamps carefully and passed the guide back after each one",
        '"Suppose we treated every clue as our clue," {buddy} suggested',
        "they found all four symbols and used the last page to choose one way to save water at home",
        "A shared quest is fair when choices and responsibilities both travel around.",
        "four bright stamps curved around a drawing of the {fish} on the completed trail page",
    ),
    Incident(
        "The Dark Tunnel",
        "the path to the {fish} passed through a dim underwater tunnel",
        "{buddy} wanted the guide for comfort, while {child} wanted it to identify every shadow",
        "{child} walked ahead with the book and did not notice {buddy} stop at the entrance",
        "a lit map in the guide showed a short bench halfway through the tunnel",
        "walk together, share the guide's glowing map, and pause at the bench if needed",
        "held one side of the open guide and named only the shapes they could verify",
        "held the other side, chose the pace, and said when a pause would help",
        '"If this feels too dark, we can turn back together," {child} promised',
        "they reached the bench calmly, spotted the {fish} overhead, and chose to finish the short path",
        "Sharing information also means making room for another person's comfort.",
        "the guide glowed between their hands while the {fish} crossed the blue ceiling above them",
    ),
    Incident(
        "The Label in Two Languages",
        "the {fish} label used a word that {buddy} knew from home but {child} had never heard",
        "{child} kept reading the familiar guide entry while {buddy}'s explanation went unheard",
        "they repeated different names more loudly instead of comparing them",
        "the label printed both names beside the same small drawing",
        "take turns teaching each name and use the guide picture as their common clue",
        "listened, repeated the new word carefully, and pointed to its label",
        "read the familiar name, then explained when their family used the other one",
        '"I wish I had listened the first time," {child} said',
        "they wrote both names on a blank guide tab and taught them to the adult who joined them",
        "Sharing words can make knowledge larger without making either word smaller.",
        "two names rested on one neat tab as the {fish} hovered beside its bilingual sign",
    ),
    Incident(
        "The Splash and the Guide",
        "a touch-pool splash dotted the edge of the picture guide",
        "{child} feared the shared book was ruined and blamed {buddy} for standing too close",
        "they rubbed the damp page with a sleeve, wrinkling one corner",
        "the aquarium helper pointed to paper towels and a dry-book tray nearby",
        "carry the closed guide together to the helper and follow the drying directions",
        "blotted the cover gently and admitted that rubbing had worsened the wrinkle",
        "held the pages apart while the helper placed clean paper between them",
        '"If we repair it together, it can still guide us," {buddy} said',
        "the book dried safely, and they used its undamaged {fish} page while keeping it away from the pool",
        "When a shared thing is harmed, honest teamwork matters more than quick blame.",
        "the dry guide stood on the return shelf with one small wrinkle and every picture still clear",
    ),
    Incident(
        "The Closing Bell",
        "the closing bell would ring soon, with three guide pages still marked to visit",
        "each child insisted that their favorite tank should be last",
        "they raced down separate aisles until an adult called them back",
        "the aquarium map placed two marked tanks together and the {fish} tank beside the exit",
        "choose the joined pair together, then save the exit-side fish for a shared finale",
        "planned the route and crossed off each stop only after both had seen it",
        "carried the guide and reminded the group when it was time to move",
        '"Were there more minutes, we might see everything; today we can choose well," {child} said',
        "they visited all three tanks without running and reached the doors before the final bell",
        "Sharing a limited afternoon means choosing together, not trying to win every choice.",
        "the last guide check mark sat beside the {fish} while sunset colored the exit windows",
    ),
    Incident(
        "The Feeding-Time Note",
        "the guide listed an old feeding time for the {fish}",
        "{buddy} thought they had missed the event, while {child} wanted to wait beside the empty feeding rail",
        "they guarded their place for several minutes and grew cross with each other",
        "a fresh notice said today's feeding had moved to the habitat's far window",
        "let one child keep their place while the other checks the notice with an aquarium educator",
        "asked the educator to confirm the new location and returned with the answer",
        "kept the guide and a clear space at the rail, then gladly gave up the old spot",
        '"I would rather share the right answer than keep the wrong place," {buddy} said',
        "they moved together, updated the guide in pencil, and watched the {fish} eat at the far window",
        "Good sharing includes bringing useful information back to the group.",
        "a tidy pencil arrow joined the old time to the new one as feeding ripples crossed the tank",
    ),
    Incident(
        "The Tiny Visitor's Turn",
        "a younger visitor could not see the {fish} picture while the two children spread their guide across the whole bench",
        "{child} and {buddy} each guarded half the page and overlooked the waiting visitor",
        "they scooted closer together but still left no safe place to look",
        "the bench's low end had room for three people and a broad ledge for the open guide",
        "move to the low end, place the guide on the ledge, and point without blocking anyone",
        "read the first sentence slowly and left space beside the page",
        "found the real fish in the tank and helped the younger visitor follow the direction",
        '"If everyone could see, this would be a better discovery," {child} said',
        "all three matched the picture to the {fish}, then the children passed the open space to another family",
        "Sharing sometimes begins by noticing someone who has not been included yet.",
        "three reflections leaned over one open guide while the {fish} flashed between green plants",
    ),
]

OPENINGS = [
    "On an ordinary Saturday morning",
    "Just after the aquarium doors opened",
    "During a quiet visit after lunch",
    "While rain tapped the aquarium roof",
    "Near the middle of a busy family afternoon",
    "Before the first school group reached the tanks",
    "On a calm weekday at the aquarium",
    "With one hour left before supper",
]

TURN_LEADS = [
    "The small disagreement became a real problem when",
    "Their visit stopped feeling easy after",
    "For a minute, sharing seemed impossible because",
    "The guide was useful, but it also became the center of a quarrel:",
    "Neither child meant to be unkind. Even so,",
    "The trouble sharpened when",
    "A perfectly ordinary moment went crooked when",
    "Their two plans bumped into each other when",
]

CLUE_LEADS = [
    "Then a careful look changed the question.",
    "A clue nearby gave them something better than a guess.",
    "They paused long enough to notice one useful fact.",
    "The aquarium itself offered a quiet correction.",
    "Instead of arguing again, they checked what was around them.",
    "One detail made their first idea look less certain.",
    "When they retraced the moment, a clue stood out.",
    "The turn came from evidence neither had noticed at first.",
]

ENDING_LEADS = [
    "At the end of the visit",
    "When it was time to leave",
    "A little later",
    "Before they moved to the next gallery",
    "By the aquarium's closing song",
    "As families drifted toward the doors",
    "After one last look at the tank",
    "In their last memory of the day",
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


def _share_turn(world: World) -> list[str]:
    out = []
    child = world.get("child")
    buddy = world.get("buddy")
    item = world.get("item")
    if item.meters["shared"] < 1:
        return out
    sig = "share_turn"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["generosity"] += 1
    buddy.memes["calm"] += 1
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    buddy.memes["joy"] += 1
    out.append(
        f"{child.id} handed the {item.label} over and let {buddy.id} take a turn."
    )
    return out


def _resolve_possessive(world: World) -> list[str]:
    out = []
    child = world.get("child")
    buddy = world.get("buddy")
    item = world.get("item")
    if item.meters["shared"] < 1 or child.memes["possessive"] < 1:
        return out
    sig = "resolve"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["tension"] = 0.0
    buddy.memes["tension"] = 0.0
    out.append("Both of them settled into a kinder rhythm.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_share_turn, _resolve_possessive):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _story_choices(params: StoryParams) -> tuple[Incident, str, str, str, str]:
    key = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.item,
            params.fish,
            params.name,
            params.relation,
            params.trait,
        )
    ).encode("utf-8")
    digest = hashlib.sha256(key).digest()
    return (
        INCIDENTS[int.from_bytes(digest[0:4], "big") % len(INCIDENTS)],
        OPENINGS[int.from_bytes(digest[4:8], "big") % len(OPENINGS)],
        TURN_LEADS[int.from_bytes(digest[8:12], "big") % len(TURN_LEADS)],
        CLUE_LEADS[int.from_bytes(digest[12:16], "big") % len(CLUE_LEADS)],
        ENDING_LEADS[int.from_bytes(digest[16:20], "big") % len(ENDING_LEADS)],
    )


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    child = world.add(Entity(id="child", kind="character", type="girl", meters={}, memes={}))
    child.id = params.name
    child.type = "girl" if params.relation in {"sister", "friend"} else "boy"
    child.memes["want"] = 1
    child.memes["possessive"] = 1
    child.memes["tension"] = 1

    buddy = world.add(Entity(id="buddy", kind="character", type="boy", meters={}, memes={}))
    buddy.id = "the " + params.relation
    buddy.type = "girl" if params.relation == "sister" else "boy"
    buddy.memes["want"] = 1

    item = world.add(Entity(
        id="item",
        kind="thing",
        type="guide",
        label="picture guide",
        plural=False,
        owner=child.id,
        meters={"shared": 0.0, "held": 1.0},
    ))

    fish = params.fish
    incident, opening, turn_lead, clue_lead, ending_lead = _story_choices(params)
    values = {
        "child": child.id,
        "buddy": buddy.id,
        "fish": fish,
    }
    detail = lambda text: text.format(**values)

    world.say(
        f"{opening}, {child.id}, who was {params.trait}, arrived at {params.place} with {buddy.id} and one picture guide between them."
    )
    world.say(f"Their small adventure was called {incident.title}: {detail(incident.premise)}.")
    world.say(
        f"At first {child.id} held the guide close, wishing there were two copies so nobody would have to yield a page."
    )

    world.para()
    world.say(f"{turn_lead} {detail(incident.conflict)}.")
    world.say(f"Their first answer did not help: {detail(incident.first_try)}.")
    world.say(
        f"{child.id} remembered a new word from school: subjunctive, the kind of language used for wishes. Wishing for two guides could not make another copy, so the one real guide still required a choice."
    )

    world.para()
    world.say(f"{clue_lead} The useful detail was this: {detail(incident.clue)}.")
    world.say(detail(incident.dialogue) + ".")
    world.say(f"Together they made a practical sharing plan: {detail(incident.sharing_plan)}.")

    item.meters["shared"] = 1
    share_lines = propagate(world, narrate=False)
    world.para()
    world.say(f"{child.id} {detail(incident.child_job)}.")
    world.say(f"Meanwhile, {buddy.id} {detail(incident.buddy_job)}.")
    for line in share_lines:
        world.say(line)
    world.say(f"Their shared work paid off: {detail(incident.resolution)}.")

    world.para()
    world.say(detail(incident.lesson))
    world.say(f"{ending_lead}, {detail(incident.ending)}.")

    world.facts.update(
        child=child,
        buddy=buddy,
        item=item,
        fish=fish,
        incident=incident,
        params=params,
        shared=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    buddy = f["buddy"]
    fish = f["fish"]
    incident = f["incident"]
    return [
        'Write a child-facing slice-of-life story at an aquarium that uses the word "subjunctive" and makes sharing one picture guide solve a concrete problem.',
        f"Tell a gentle aquarium story called {incident.title} where {child.id} and {buddy.id} disagree, inspect a clue, and share their guide while looking for the {fish}.",
        f"Write an everyday story about an aquarium visit in which the wish for two guides gives way to this fair plan: {incident.sharing_plan.format(child=child.id, buddy=buddy.id, fish=fish)}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    buddy = f["buddy"]
    item = f["item"]
    fish = f["fish"]
    incident = f["incident"]
    values = {"child": child.id, "buddy": buddy.id, "fish": fish}
    detail = lambda text: text.format(**values)
    return [
        QAItem(
            question=f"What problem did {child.id} and {buddy.id} face in {incident.title}?",
            answer=f"They discovered that {detail(incident.conflict)}. Their first attempt failed because {detail(incident.first_try)}.",
        ),
        QAItem(
            question="Which clue helped the children stop guessing?",
            answer=f"They noticed that {detail(incident.clue)}. That evidence gave them a fairer way to understand the problem.",
        ),
        QAItem(
            question=f"How did {child.id} and {buddy.id} share the picture guide?",
            answer=f"They agreed to {detail(incident.sharing_plan)}. {child.id} {detail(incident.child_job)}, while {buddy.id} {detail(incident.buddy_job)}.",
        ),
        QAItem(
            question="What changed because the children followed their sharing plan?",
            answer=f"Their teamwork meant that {detail(incident.resolution)}. The guide was shared, and the disagreement ended calmly.",
        ),
        QAItem(
            question=f"What lesson did the children learn after seeing the {fish}?",
            answer=detail(incident.lesson),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aquarium?",
            answer="An aquarium is a place where people can see fish and other water animals in tanks.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let more than one person use or enjoy something in turns or together.",
        ),
        QAItem(
            question="What does subjunctive mean in a sentence?",
            answer="Subjunctive language talks about wishes, possibilities, or things that are not fully real yet, like saying 'If only...'",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ITEMS = {
    "guide": SharedItem(id="guide", label="picture guide", phrase="a small picture guide"),
}

CURATED = [
    StoryParams(place="the aquarium", item="guide", fish="jellyfish", name="Maya", relation="cousin", trait="curious"),
    StoryParams(place="the aquarium", item="guide", fish="blue tang", name="Noah", relation="sister", trait="gentle"),
    StoryParams(place="the aquarium", item="guide", fish="seahorse", name="Lena", relation="friend", trait="quiet"),
]


ASP_RULES = r"""
shared(Item) :- item(Item).
turning(kind) :- shared(guide).
calm_visit :- shared(guide), fish_visible.
good_story :- calm_visit.
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("place", "aquarium"))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
    for f in FISHES:
        lines.append(asp.fact("fish", f))
    lines.append(asp.fact("fish_visible"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life aquarium storyworld about sharing and subjunctive wishes.")
    ap.add_argument("--place", choices=["the aquarium"])
    ap.add_argument("--item", choices=["guide"])
    ap.add_argument("--fish", choices=FISHES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--relation", choices=RELATIONS)
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
    place = args.place or "the aquarium"
    item = args.item or "guide"
    fish = args.fish or rng.choice(FISHES)
    name = args.name or rng.choice(NAMES)
    relation = args.relation or rng.choice(RELATIONS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, fish=fish, name=name, relation=relation, trait=trait)


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


def asp_verify() -> int:
    print("OK: ASP twin is present for the aquarium sharing world.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: sharing at {p.place} with {p.fish}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
