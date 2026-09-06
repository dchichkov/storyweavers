#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/narrative_specify_coupon_teamwork_foreshadowing_tall_tale.py
================================================================================

A small tall-tale storyworld about a crew finding a coupon, teaming up, and
using a careful clue from the start to solve a big, harmless problem.

The source tale this world grows from:

A tall fellow named Gus found an extra-big coupon tucked in a cereal box.
The coupon promised a free kite, but only if Gus could bring three things to
the corner shop: a spool, a ribbon, and a smile from someone willing to help.
Gus could not carry everything alone. He asked his sister Dot and their friend
Milo to help.

First they nearly forgot the ribbon, then a shop sign pointed them back to it.
That little sign was the foreshadowing clue: the ribbon had to be tied just
right, or the kite would wobble like a spoon in a thunderstorm. Together they
specify the needed parts, work as a team, and trade the coupon for the kite.
By sunset, the whole block could see the kite riding the wind like a tiny ship.

This script models:
- a coupon with a condition list
- a crew that can split the labor
- a foreshadowed clue that points to the missing item
- a tall-tale ending image proving the change
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402

FORESHADOW_THRESHOLD = 1.0
TEAM_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    needed: list[str]
    clue: str
    tall_image: str


@dataclass
class Coupon:
    id: str
    label: str
    phrase: str
    requires: list[str]
    prize: str
    redeem_at: str
    valid_if: str


@dataclass
class StoryParams:
    place: str
    task: str
    coupon: str
    name: str
    helper1: str
    helper2: str
    seed: Optional[int] = None
    arc: str = "windmill"
    telling: str = "porch"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = world.crew()
    leader = world.facts.get("hero")
    if not leader:
        return out
    helpers = [c for c in crew if c.id != leader.id]
    if len(helpers) < 2:
        return out
    if any(c.memes.get("helping", 0) < TEAM_THRESHOLD for c in helpers):
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get(leader.id)
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    out.append(world.facts["team_line"])
    return out


def _r_coupon_ready(world: World) -> list[str]:
    out: list[str] = []
    coupon: Entity = world.facts.get("coupon")
    task: Task = world.facts.get("task")
    hero: Entity = world.facts.get("hero")
    if not coupon or not task or not hero:
        return out
    if coupon.meters.get("complete", 0) < 1:
        return out
    sig = ("coupon_ready", coupon.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(world.facts["ready_line"].format(hero=hero.id))
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_seen", False)
    ribbon = world.entities.get("ribbon")
    if not clue or not ribbon:
        return out
    sig = ("foreshadow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ribbon.memes["noticed"] = ribbon.memes.get("noticed", 0) + 1
    out.append(world.facts["reveal_line"])
    return out


RULES = [_r_teamwork, _r_coupon_ready, _r_foreshadow]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld about a coupon, teamwork, and a foreshadowed clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--coupon", choices=COUPONS)
    ap.add_argument("--name")
    ap.add_argument("--helper1")
    ap.add_argument("--helper2")
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


PLACES = {
    "corner_shop": Place("the corner shop", outdoor=False, affords={"kite"}),
    "county_fair": Place("the county fair", outdoor=True, affords={"kite"}),
    "boardwalk": Place("the boardwalk", outdoor=True, affords={"kite"}),
}

TASKS = {
    "kite": Task(
        id="kite",
        verb="trade the coupon for a kite",
        gerund="trading the coupon for a kite",
        needed=["spool", "ribbon", "smile"],
        clue="a sign pointed to the ribbon bin",
        tall_image="the kite rose so high it could have tickled the moon",
    ),
    "jam": Task(
        id="jam",
        verb="trade the coupon for jam",
        gerund="trading the coupon for jam",
        needed=["jar", "lid", "smile"],
        clue="the jar shelf groaned like an old porch",
        tall_image="the jam shone red as a sunset in a rain barrel",
    ),
}

COUPONS = {
    "kite_coupon": Coupon(
        id="kite_coupon",
        label="kite coupon",
        phrase="a coupon for one free kite",
        requires=["spool", "ribbon", "smile"],
        prize="kite",
        redeem_at="the corner shop",
        valid_if="the helpers bring every needed thing",
    ),
    "jam_coupon": Coupon(
        id="jam_coupon",
        label="jam coupon",
        phrase="a coupon for one free jar of berry jam",
        requires=["jar", "lid", "smile"],
        prize="jam",
        redeem_at="the boardwalk stand",
        valid_if="the helpers bring every needed thing",
    ),
}

NAMES = ["Gus", "Dot", "Milo", "Nell", "Ivy", "Mabel", "Bert", "Walt"]
HELPERS = ["Dot", "Milo", "Nell", "Ivy", "Bert", "Walt", "Pip", "June"]

NAME_TYPES = {
    "Gus": "boy", "Milo": "boy", "Bert": "boy", "Walt": "boy", "Pip": "boy",
    "Dot": "girl", "Nell": "girl", "Ivy": "girl", "Mabel": "girl", "June": "girl",
}

# Each arc has a different problem, clue payoff, division of labor, and repair.
# They are authored as complete causal paths rather than interchangeable adjectives.
ARCS = {
    "windmill": {
        "premise": "A west wind was rattling every shutter, so the shopkeeper planned to close before noon.",
        "hint": "A ribbon painted on the weather vane pointed toward the narrow blue bin.",
        "obstacle": "A gust snatched the spool and rolled it under a delivery cart before they could reach the counter.",
        "jobs": "{h1} blocked the wheels with a brick, {h2} crawled under for the spool, and {hero} tied the ribbon around it while all three traded a relieved smile.",
        "turn": "The painted ribbon had specified where the real ribbon was stored, and its knot now kept the rescued spool from unwinding.",
        "finish": "The clerk reopened the shutter long enough to honor the coupon.",
        "image": "the kite tugged so hard that three chimney clouds lined up behind it like sheep",
    },
    "parade": {
        "premise": "The noon parade had filled the street, and the crew had only until the brass band reached the shop door.",
        "hint": "The drummer's sash had a spool, a ribbon, and a smiling sun stitched in that order.",
        "obstacle": "The crowd separated the helpers, leaving each child with one needed thing and no clear way across.",
        "jobs": "{h1} lifted the spool on a broom, {h2} waved the ribbon from a bench, and {hero} called a marching count that brought them together on every fourth beat.",
        "turn": "The stitched order was a route as well as a list; by following it, they reunited before the band arrived.",
        "finish": "They specified each item to the clerk, who stamped the coupon on the final drumbeat.",
        "image": "the kite sailed above the parade and its tail seemed long enough to underline the whole town",
    },
    "goat": {
        "premise": "At the county fair, a prize goat kept nosing anything made of paper.",
        "hint": "A tiny bite mark beside the coupon's ribbon picture looked unimportant at first.",
        "obstacle": "The goat swallowed the loose end of the ribbon and chased {hero} toward the judging tent.",
        "jobs": "{h1} offered the goat an apple, {h2} caught the freed ribbon, and {hero} protected the coupon inside the empty spool.",
        "turn": "That first bite mark had foreshadowed the goat's appetite, so the crew knew kindness and an apple would work better than a tug-of-war.",
        "finish": "The judge laughed, verified all three requirements, and walked them to the redemption booth.",
        "image": "the kite climbed over the fair until the goat's blue ribbon looked like a shoelace below",
    },
    "puddle": {
        "premise": "Last night's rain had turned the road to the shop into a chain of silver puddles.",
        "hint": "Three dry stepping-stones bore faint pictures of a spool, a bow, and a grin.",
        "obstacle": "The deepest puddle soaked the coupon's corner and stranded the ribbon on the opposite bank.",
        "jobs": "{h1} laid down boards, {h2} ferried the ribbon in a lunch tin, and {hero} dried the coupon by winding it gently around the spool.",
        "turn": "The pictures had specified a safe crossing all along, and the spool's dry paper tube saved the damp coupon.",
        "finish": "The clerk could still read the offer, so the careful team earned the prize.",
        "image": "the kite's reflection crossed every puddle, making a blue road all the way home",
    },
    "bell": {
        "premise": "The shop's enormous doorbell rang whenever anyone stepped on the porch, startling the clerk into dropping things.",
        "hint": "A chalk arrow beneath the bell pointed to a hook shaped like a bow.",
        "obstacle": "When the crew arrived, the bell shook the ribbon from {h1}'s hand and onto a high awning.",
        "jobs": "{hero} steadied the spool as a pulley, {h2} guided its string over the hook, and {h1} used the loop to lower the ribbon safely.",
        "turn": "The bow-shaped hook from the opening clue became their pulley point, just as the chalk arrow had promised.",
        "finish": "They entered softly, named every coupon condition, and received the kite without one more crash.",
        "image": "the kite rang the breeze so sweetly that even the enormous bell seemed to listen",
    },
    "magpie": {
        "premise": "A magpie on the boardwalk had begun collecting every bright scrap it saw.",
        "hint": "One silver feather lay beside the ribbon bin before the children chose their jobs.",
        "obstacle": "Halfway to the stand, the ribbon vanished and flashed from the bird's nest atop a lamp.",
        "jobs": "{h1} made a safe loop from the spool, {h2} held it steady, and {hero} offered a shiny bottle cap in exchange for the ribbon.",
        "turn": "The silver feather had foreshadowed the collector, and teamwork let them bargain without frightening it.",
        "finish": "At the stand they specified the returned ribbon, the spool, and their very genuine smile.",
        "image": "the kite wheeled beside the magpie until bird and paper shadow danced together on the planks",
    },
    "clock": {
        "premise": "The coupon expired when the old shop clock struck twelve, and its minute hand was already climbing.",
        "hint": "A ribbon tied around the number eleven fluttered each time the clock lost a minute.",
        "obstacle": "The clock jumped forward when a loose gear fell out, leaving too little time to search separately.",
        "jobs": "{h1} found the gear beside the spool rack, {h2} used the ribbon to lift it into place, and {hero} kept the pendulum still until both were clear.",
        "turn": "The fluttering ribbon had marked the loose part; fixing it restored the missing minutes instead of stealing extra time.",
        "finish": "The true clock chimed only after the team presented the coupon and its three specified requirements.",
        "image": "the kite rose at noon and its shadow swept the square like the hand of a joyful clock",
    },
    "wagon": {
        "premise": "The children loaded their supplies into a red wagon whose left wheel squeaked at every turn.",
        "hint": "A neat ribbon knot on the handle sat directly above that wobbling wheel.",
        "obstacle": "On the hill, the wheel pin slipped out and the spool began rolling toward the creek.",
        "jobs": "{hero} stopped the wagon, {h1} caught the spool with a boot, and {h2} untied the ribbon to lash the wheel pin firmly in place.",
        "turn": "The opening knot had specified an emergency tie; using it turned a decoration into the repair they needed.",
        "finish": "They pulled the mended wagon to the shop and redeemed the coupon together.",
        "image": "the kite lifted the empty wagon handle until it looked ready to follow them into the clouds",
    },
    "whistle": {
        "premise": "Fog covered the boardwalk so thickly that even the candy-striped shop sign disappeared.",
        "hint": "The coupon showed three tiny whistle marks beside its picture of the ribbon.",
        "obstacle": "The helpers lost sight of one another, and the spool string tangled around a bench.",
        "jobs": "{hero} gave three whistles, {h1} answered while freeing the spool, and {h2} followed their voices with the ribbon held high.",
        "turn": "Those printed marks had specified a signal, not a decoration, and the shared signal gathered the team in the fog.",
        "finish": "Their footsteps reached the stand together, where the seller accepted the coupon.",
        "image": "the kite climbed through the fog and opened a blue window wide enough for sunlight to pour through",
    },
    "cat": {
        "premise": "A sleepy shop cat had chosen the ribbon basket for its morning bed.",
        "hint": "Three loose blue threads clung to its whiskers when {hero} first read the coupon.",
        "obstacle": "The cat woke, sprang onto a flour shelf, and carried the ribbon beyond the children's reach.",
        "jobs": "{h1} rolled the spool gently like a toy, {h2} waited with open hands, and {hero} praised the cat until it pounced down and released the ribbon.",
        "turn": "The threads had foreshadowed where the ribbon would go, and the team solved the trouble patiently instead of chasing.",
        "finish": "The clerk brushed off the flour, checked every specified item, and honored the coupon.",
        "image": "the kite purred in the wind while the cat watched its tail stitch zigzags across the sky",
    },
    "bridge": {
        "premise": "A toy-sized bridge crossed the ditch before the corner shop, but one plank was missing.",
        "hint": "A ribbon around the railing marked two holes exactly one spool-width apart.",
        "obstacle": "The children could not carry their supplies across without tipping them into the ditch.",
        "jobs": "{h2} found a flat board, {h1} measured it with the spool, and {hero} threaded the ribbon through both marked holes to hold it.",
        "turn": "The railing clue had specified the size and fastening for a replacement plank, so each child's task mattered.",
        "finish": "They crossed their little repair and gave the waiting clerk the coupon.",
        "image": "the kite arched over the ditch like a second bridge, only taller than the courthouse",
    },
    "sneeze": {
        "premise": "A pepper wagon rattled past just as the crew gathered the coupon supplies.",
        "hint": "The ribbon bin's lid carried a painted warning: HOLD TIGHT WHEN THE RED WAGON COMES.",
        "obstacle": "One enormous sneeze sent the ribbon sailing, the spool bouncing, and everyone's smiles away.",
        "jobs": "{h1} trapped the spool under a basket, {h2} caught the ribbon on a rake, and {hero} told such a silly sneeze joke that all three smiles returned.",
        "turn": "The painted warning had foreshadowed the pepper cloud; because they remembered it, no needed item escaped for long.",
        "finish": "Still laughing, they specified the three recovered requirements and redeemed the coupon.",
        "image": "the kite sneezed once in the high wind and blew every cloud into a perfect white ring",
    },
}

TELLINGS = {
    "porch": {
        "opening": "On a morning bright enough to polish every window, {hero} found {coupon} beneath a porch cup.",
        "invite": "\"Two hands can hold things, but six hands can solve things,\" {hero} said, calling {h1} and {h2}.",
        "team": "The three moved as one team: nobody's small job was treated as small.",
        "ready": "{hero} flattened the coupon on the counter and named each requirement clearly.",
    },
    "whopper": {
        "opening": "Folks claim {hero}'s pocket was deep enough for a canoe; that is where {hero} discovered {coupon}.",
        "invite": "{hero} could lift a fence, perhaps, but admitted that this job needed {h1}'s judgment and {h2}'s quick hands.",
        "team": "Their teamwork was so tidy that even their three shadows took turns helping.",
        "ready": "{hero} raised the coupon, while the helpers specified every item they had brought.",
    },
    "fireside": {
        "opening": "Listen close: this narrative began when {hero} unfolded {coupon} beside the warm stove.",
        "invite": "Before taking one step, {hero}, {h1}, and {h2} agreed that each voice would count.",
        "team": "They paused, listened, and fitted their ideas together like boards in a strong floor.",
        "ready": "{hero} placed the coupon down, and all three checked its conditions once more.",
    },
    "quick": {
        "opening": "Snap! A cereal box opened, and {coupon} landed in {hero}'s hand.",
        "invite": "\"Team, specify what we need,\" cried {hero}; {h1} read the list and {h2} planned the route.",
        "team": "One called, one carried, and one checked; then they swapped whenever a friend needed help.",
        "ready": "At the counter, {hero} presented the coupon while the others showed the complete set.",
    },
    "quiet": {
        "opening": "While the town still whispered in its sleep, {hero} found {coupon} folded inside a library book.",
        "invite": "{hero} asked {h1} and {h2} quietly, and they made a careful plan before the streets grew busy.",
        "team": "No one boasted; each child simply noticed what the others needed and helped.",
        "ready": "{hero} slid the coupon forward and let the helpers explain how the team had completed it.",
    },
    "newspaper": {
        "opening": "The morning paper would later call it astonishing, but first {hero} found {coupon} under the doorstep.",
        "invite": "{hero} recruited {h1} to track the list and {h2} to guard the supplies.",
        "team": "Witnesses agreed that the crew's teamwork was faster than a headline crossing town.",
        "ready": "{hero} showed the coupon to the clerk and reported every completed condition.",
    },
    "question": {
        "opening": "Could one little coupon cause a town-sized adventure? It did when {hero} found {coupon}.",
        "invite": "{hero} asked, \"Who can help me do this properly?\" and {h1} and {h2} answered together.",
        "team": "Whenever one child asked a question, the other two answered with an idea and a hand.",
        "ready": "\"What does the coupon specify?\" asked the clerk, and the team displayed every answer.",
    },
    "ledger": {
        "opening": "The town ledger records that {hero} found {coupon} on the most blustery day of the year.",
        "invite": "In the margin, {hero} wrote three names: {hero}, {h1}, and {h2}, a crew with shared responsibility.",
        "team": "Their plan changed when trouble changed, but their promise to help one another did not.",
        "ready": "{hero} set the coupon beside the supplies so the clerk could verify each one.",
    },
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, c) for p, place in PLACES.items() for t, task in TASKS.items() for c, coupon in COUPONS.items() if t == "kite" and coupon.prize == "kite" and task.id in place.affords]


ASP_RULES = r"""
task(T) :- task_name(T).
coupon(C) :- coupon_name(C).

needs(C, R) :- coupon_item(C, R).
needed(T, R) :- task_item(T, R).

compatible(P, T, C) :- place(P), task(T), coupon(C),
                       affords(P, T),
                       same_prize(T, C),
                       all_needed(T, C).

same_prize(T, C) :- task_prize(T, X), coupon_prize(C, X).
all_needed(T, C) :- needed(T, R), needs(C, R).
valid_story(P, T, C) :- compatible(P, T, C).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.outdoor:
            lines.append(asp.fact("outdoor", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task_name", tid))
        lines.append(asp.fact("task_prize", tid, tid))
        for r in task.needed:
            lines.append(asp.fact("task_item", tid, r))
    for cid, c in COUPONS.items():
        lines.append(asp.fact("coupon_name", cid))
        lines.append(asp.fact("coupon_prize", cid, c.prize))
        for r in c.requires:
            lines.append(asp.fact("coupon_item", cid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.coupon is None or c[2] == args.coupon)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, coupon = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper1 = args.helper1 or rng.choice([n for n in HELPERS if n != name])
    helper2 = args.helper2 or rng.choice([n for n in HELPERS if n not in {name, helper1}])
    return StoryParams(
        place=place,
        task=task,
        coupon=coupon,
        name=name,
        helper1=helper1,
        helper2=helper2,
        arc=rng.choice(sorted(ARCS)),
        telling=rng.choice(sorted(TELLINGS)),
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    coupon = COUPONS[params.coupon]
    arc = ARCS[params.arc]
    telling = TELLINGS[params.telling]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=NAME_TYPES.get(params.name, "child"), label=params.name))
    h1 = world.add(Entity(id=params.helper1, kind="character", type=NAME_TYPES.get(params.helper1, "child"), label=params.helper1))
    h2 = world.add(Entity(id=params.helper2, kind="character", type=NAME_TYPES.get(params.helper2, "child"), label=params.helper2))
    cp = world.add(Entity(id="coupon", type="coupon", label=coupon.label, phrase=coupon.phrase, owner=hero.id))
    ribbon = world.add(Entity(id="ribbon", type="thing", label="ribbon"))
    spool = world.add(Entity(id="spool", type="thing", label="spool"))
    smile = world.add(Entity(id="smile", type="thing", label="smile"))

    fields = {
        "hero": hero.id,
        "h1": h1.id,
        "h2": h2.id,
        "coupon": coupon.phrase,
        "place": place.name,
    }
    rendered_arc = {key: value.format(**fields) for key, value in arc.items()}
    rendered_telling = {key: value.format(**fields) for key, value in telling.items()}
    world.facts.update(
        hero=hero,
        helpers=[h1, h2],
        coupon=cp,
        task=task,
        clue_seen=True,
        clue=rendered_arc["hint"],
        obstacle=rendered_arc["obstacle"],
        jobs=rendered_arc["jobs"],
        consequence=rendered_arc["turn"],
        ending_image=rendered_arc["image"],
        team_line=rendered_telling["team"],
        ready_line=rendered_telling["ready"],
        reveal_line=rendered_arc["turn"],
        arc=params.arc,
        telling=params.telling,
    )

    # Beginning
    world.say(rendered_telling["opening"])
    world.say(rendered_arc["premise"])
    world.say(
        f"The coupon specified three requirements: {', '.join(coupon.requires[:-1])}, "
        f"and {coupon.requires[-1]}."
    )
    world.say(rendered_arc["hint"])

    # Middle
    world.para()
    world.say(rendered_telling["invite"])
    h1.memes["helping"] = 1
    h2.memes["helping"] = 1
    world.say(rendered_arc["obstacle"])
    world.say(rendered_arc["jobs"])
    propagate(world, narrate=True)

    # Resolution
    world.para()
    if all(req in {"spool", "ribbon", "smile"} for req in coupon.requires):
        cp.meters["complete"] = 1
    world.say(
        f"Together they brought the {spool.label}, the {ribbon.label}, and a real {smile.label} "
        f"to {coupon.redeem_at}."
    )
    propagate(world, narrate=True)
    world.say(rendered_arc["finish"])
    world.say(f"When they finally flew the kite, {rendered_arc['image']}.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    task: Task = f["task"]
    coupon: Entity = f["coupon"]
    return [
        'Write a short tall-tale story for a child about a coupon, teamwork, and a clue that was foreshadowed.',
        f"Tell a story where {hero.id} and two helpers solve this trouble together: {f['obstacle']}",
        f"Write a narrative that specifies the needed items, pays off the clue '{f['clue']}', uses the word 'coupon', and ends with a tall-tale image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    task: Task = f["task"]
    coupon: Entity = f["coupon"]
    helpers = f["helpers"]
    return [
        QAItem(
            question=f"What did {hero.id} find at the start of the story?",
            answer=f"{hero.id} found {coupon.phrase}, which promised a prize if the needed things were brought in.",
        ),
        QAItem(
            question=f"Who helped {hero.id} get everything ready?",
            answer=f"{helpers[0].id} and {helpers[1].id} helped, and the three of them worked as a team.",
        ),
        QAItem(
            question=f"What clue foreshadowed the missing item?",
            answer=f"The early clue was this: {f['clue']} Later, it helped the team understand what to do.",
        ),
        QAItem(
            question="How did the three children divide the work?",
            answer=f"They divided it this way: {f['jobs']} Their separate actions solved one shared problem.",
        ),
        QAItem(
            question="Why did the clue matter later?",
            answer=f"It mattered because {f['consequence']} The early detail therefore helped cause the solution.",
        ),
        QAItem(
            question=f"What happened at the end after they used the coupon?",
            answer=f"They traded the coupon and got the kite. At the end, {f['ending_image']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a coupon?", answer="A coupon is a paper or card that can be traded for a deal, discount, or prize."),
        QAItem(question="What does teamwork mean?", answer="Teamwork means people help each other do a job together."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a hint that gives you a small clue about what will matter later."),
    ]


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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired if x))}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="corner_shop", task="kite", coupon="kite_coupon", name="Gus", helper1="Dot", helper2="Milo"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
