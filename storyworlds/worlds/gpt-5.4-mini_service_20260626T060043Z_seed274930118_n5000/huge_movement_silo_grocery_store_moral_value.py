#!/usr/bin/env python3
"""
storyworlds/worlds/huge_movement_silo_grocery_store_moral_value.py
===================================================================

A small folk-tale storyworld set in a grocery store, where a huge movement of
goods, a silo-like grain bin, friendship, conflict, and a moral choice shape a
complete little story.

The seed image is simple:
- a grocery store with a grain silo/bin for scooping dry food
- a huge movement of crates and carts through the aisles
- a friendship strained by conflict
- a moral value: sharing work, telling the truth, and helping a friend

The world simulates a few physical and emotional state changes so the prose is
driven by events rather than template swapping.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_by: Optional[str] = None
    location: str = ""
    plural: bool = False
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the grocery store"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character" or actor.meters.get("movement", 0) < THRESHOLD:
            continue
        carrier = world.facts.get("carrier")
        if not carrier:
            continue
        if actor.id == carrier.id:
            continue
        if actor.location != carrier.location:
            continue
        sig = ("bump", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["anger"] = actor.memes.get("anger", 0) + 1
        out.append(f"People began to grumble as the carts crowded the aisle.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    c1 = world.facts.get("friend_a")
    c2 = world.facts.get("friend_b")
    if not c1 or not c2:
        return out
    if c1.memes.get("anger", 0) < THRESHOLD:
        return out
    sig = ("conflict", c1.id, c2.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    c1.memes["conflict"] = c1.memes.get("conflict", 0) + 1
    c2.memes["conflict"] = c2.memes.get("conflict", 0) + 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [_r_bump, _r_conflict]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)


def show_qa_item(q: QAItem) -> str:
    return f"Q: {q.question}\nA: {q.answer}"


@dataclass
class StoryParams:
    name_a: str
    name_b: str
    helper: str
    incident: str
    choice: str
    reflection: str
    ending: str
    telling: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    occasion: str
    movement: str
    first_sign: str
    danger: str
    dispute: str
    plan: str
    task_a: str
    task_b: str
    result: str
    changed_fact: str


@dataclass(frozen=True)
class MoralChoice:
    temptation: str
    mistake: str
    consequence: str
    admission: str
    counsel: str
    amends: str
    lesson: str


@dataclass(frozen=True)
class Ending:
    image: str
    final_line: str


SETTINGS = {
    "grocery": Setting(place="the grocery store", affords={"movement"}),
}

ACTIVITIES = {
    "movement": Activity(
        id="movement",
        verb="move the heavy carts",
        gerund="moving the heavy carts",
        rush="rush the carts through the aisle",
        mess="crowded",
        zone="aisle",
        keyword="movement",
        tags={"movement", "conflict"},
    ),
}

PRIZES = {
    "silo": Prize(
        label="silo bin",
        phrase="the tall grain silo bin",
        type="silo",
        location="back wall",
    ),
}

NAMES = ["Mina", "Jory", "Lena", "Tomas", "Nell", "Ravi", "Iris", "Bram"]
HELPERS = ["the clerk", "the baker", "the porter"]


INCIDENTS = {
    "runaway_oats": Incident(
        occasion="a wagon delivered enough oats to fill the silo before noon",
        movement="a long train of loaded carts rolled from the doors toward the back wall",
        first_sign="one cart's brass latch began to chatter",
        danger="The latch sprang open, and oat sacks leaned toward a pyramid of tomato tins",
        dispute="who should leave the line to catch the sacks",
        plan="halt every cart, brace the loose load, and restart the line one cart at a time",
        task_a="wedged a wooden doorstop beneath the runaway wheel",
        task_b="held the leaning sacks while the loose latch was tied shut",
        result="the oat sacks reached the silo without toppling a single tin",
        changed_fact="the runaway oat cart was secured",
    ),
    "storm_rush": Incident(
        occasion="dark clouds sent half the neighborhood shopping at once",
        movement="families, baskets, and flour carts surged through every aisle",
        first_sign="the bell above the door rang without a pause",
        danger="A flour cart blocked the clear path to the exit just as thunder shook the windows",
        dispute="whether speed mattered more than keeping the exit clear",
        plan="open a safe lane first, then relay the flour to the silo in smaller loads",
        task_a="guided families through the cleared lane",
        task_b="divided the flour into two steady carts",
        result="the exit stayed open and the flour arrived dry at the silo",
        changed_fact="the storm crowd could move safely",
    ),
    "donation_day": Incident(
        occasion="the store was packing grain for the town pantry",
        movement="volunteers pushed dozens of donation carts past the silo",
        first_sign="blue pantry labels appeared on two customers' baskets",
        danger="The mixed labels would send paid groceries away and leave pantry sacks behind",
        dispute="whether to hide the mix-up so the line would keep moving",
        plan="stop the convoy, read every label aloud, and rebuild the two groups",
        task_a="checked the customer receipts against the blue labels",
        task_b="counted the pantry sacks beside the silo",
        result="every family and every pantry box received the right food",
        changed_fact="the donation loads were sorted honestly",
    ),
    "split_rice": Incident(
        occasion="a festival order brought a mountain of rice to the store",
        movement="hand trucks carried white sacks toward the silo in a rumbling stream",
        first_sign="a thin trail of rice shone behind the last truck",
        danger="A torn sack was spilling grains under rolling wheels, making the floor slippery",
        dispute="who had dragged the sack after noticing the tear",
        plan="ring the aisle bell, sweep the loose rice, and cradle the torn sack in an empty crate",
        task_a="stood at the aisle mouth and turned the carts aside",
        task_b="swept the grains before anyone could slip",
        result="the floor became safe and the rescued rice was measured into the silo",
        changed_fact="the spill was cleaned and the rice was saved",
    ),
    "freezer_relay": Incident(
        occasion="the freezer motor failed during the hottest afternoon of summer",
        movement="workers rushed chilled food in carts toward the cool storeroom beyond the silo",
        first_sign="drops of water gathered beneath a crate of berries",
        danger="The heavy grain carts were crowding out the lighter food that would spoil first",
        dispute="whether their own oat delivery deserved the shortest route",
        plan="give the melting food the clear lane and park the grain safely beside the silo",
        task_a="marked a cool-food lane with bright floor cones",
        task_b="steered the grain carts into a waiting row",
        result="the berries stayed cold, and the patient grain moved after the freezer was repaired",
        changed_fact="the perishable food reached safety first",
    ),
    "harvest_stack": Incident(
        occasion="the first autumn harvest arrived in golden burlap sacks",
        movement="carts circled the silo while neighbors passed sacks from hand to hand",
        first_sign="the bottom sack in a tall stack bulged like a pillow",
        danger="The stack tilted over the narrow aisle where a shopper was approaching",
        dispute="whether to shout blame or warn the shopper first",
        plan="warn everyone, lower the top sacks, and rebuild the stack with a broad base",
        task_a="called a clear warning and stopped the approaching shopper",
        task_b="lowered each top sack into a waiting cart",
        result="the rebuilt stack stood low and firm beside the silo",
        changed_fact="the leaning harvest stack was made stable",
    ),
    "school_pantry": Incident(
        occasion="children were collecting breakfast food for their school pantry",
        movement="small carts decorated with paper suns streamed toward the weighing scale",
        first_sign="the scale needle jumped each time two carts arrived together",
        danger="No one could tell whether the school had enough oats, and the crowded carts began to bump",
        dispute="who should claim credit for the largest donation",
        plan="form one line, weigh each cart alone, and record every gift under the whole class",
        task_a="called the carts forward in order",
        task_b="wrote each weight on a shared chalkboard",
        result="the final total filled the pantry goal exactly",
        changed_fact="the school donations were counted fairly",
    ),
    "high_water": Incident(
        occasion="a drain overflowed outside after three days of rain",
        movement="everyone lifted food from low shelves and rolled it toward higher ground by the silo",
        first_sign="a silver ribbon of water slipped under the front door",
        danger="Two carts met nose to nose in the only dry aisle",
        dispute="whose cart had the right to pass first",
        plan="back up the lighter cart, make one-way signs, and move the lowest food before the rest",
        task_a="carried the one-way signs from aisle to aisle",
        task_b="backed the lighter cart into a dry alcove",
        result="the low shelves were emptied before the water reached them",
        changed_fact="the food was protected from the rising water",
    ),
    "stuck_wheel": Incident(
        occasion="the weekly grain shipment arrived while the store was busiest",
        movement="six carts creaked in a close line toward the silo",
        first_sign="the lead cart began hopping instead of rolling",
        danger="A strip of packing cord had wound around its wheel and the carts behind kept coming",
        dispute="whether to tug harder or admit that the line must stop",
        plan="signal the rear carts, unload the stuck cart, and cut away the cord with the clerk's scissors",
        task_a="raised both hands until every driver stopped",
        task_b="carried the top sacks to a safe pallet",
        result="the freed wheel turned quietly and the line resumed at walking speed",
        changed_fact="the jammed wheel was freed without a crash",
    ),
    "lost_list": Incident(
        occasion="the store prepared one enormous order for the senior center",
        movement="pickers crossed the aisles with carts full of beans, oats, and fruit",
        first_sign="two teams reached the silo carrying identical oat sacks",
        danger="The master list was missing, so the order might be doubled while other food was forgotten",
        dispute="who had last held the list",
        plan="pause the carts, reconstruct the order from shelf marks, and search the route together",
        task_a="read the empty shelf marks from the first aisle",
        task_b="found the folded list beneath the silo scale",
        result="the center received one complete order with nothing doubled or missing",
        changed_fact="the senior-center order was rebuilt correctly",
    ),
    "quiet_hour": Incident(
        occasion="the store held a quiet shopping hour for neighbors who disliked noise",
        movement="a late delivery nevertheless sent a huge procession of grain carts indoors",
        first_sign="the first metal cart rattled sharply over a cracked tile",
        danger="The clatter frightened a small customer and echoed around the silo",
        dispute="whether the delivery schedule excused breaking the quiet promise",
        plan="pad the cart beds, slow the wheels, and unload the sacks by hand near the cracked tile",
        task_a="folded clean cardboard beneath the noisy cart beds",
        task_b="walked beside each cart and steadied every loose handle",
        result="the grain reached the silo with only a soft whisper of wheels",
        changed_fact="the quiet hour remained peaceful",
    ),
    "power_outage": Incident(
        occasion="the lights went out during the evening restock",
        movement="shadowy carts were still rolling from the loading door toward the silo",
        first_sign="a wheel struck a display and sent one apple across the floor",
        danger="Without light, the next carts could hit workers or crush the fallen fruit",
        dispute="whether finishing quickly was worth moving in darkness",
        plan="stop in place, make a lantern path, and send one guide ahead of each cart",
        task_a="set battery lanterns along the aisle edge",
        task_b="walked ahead and called out every turn",
        result="the carts reached the silo slowly, and even the fallen apple was recovered",
        changed_fact="the dark aisle became a safe lantern path",
    ),
}


CHOICES = {
    "truth": MoralChoice(
        temptation="pretend neither of them had noticed the warning sign",
        mistake="They each blamed the other and let one more cart enter the aisle",
        consequence="That choice tightened the jam and put other people at risk",
        admission='"I saw the trouble first and stayed quiet," {a} admitted. "That was wrong."',
        counsel='"Truth clears a path faster than blame," {helper} replied.',
        amends="tell everyone exactly what happened and take the first difficult jobs",
        lesson="honesty gives people the facts they need to help",
    ),
    "share_work": MoralChoice(
        temptation="race for the easiest job and leave the awkward work to a friend",
        mistake="Both grabbed the same easy handle while the harder task went undone",
        consequence="The moving line lost its balance because cooperation had become a contest",
        admission='"I was choosing comfort instead of helping," {b} said.',
        counsel='"A shared burden grows lighter; a shared prize grows larger," {helper} told them.',
        amends="divide the jobs by need and switch places when either friend grew tired",
        lesson="fair teamwork matters more than getting the pleasant task",
    ),
    "protect_others": MoralChoice(
        temptation="save their own cart before warning anyone else",
        mistake="For one moment they guarded their load and forgot the people behind it",
        consequence="The danger spread beyond their cart while precious seconds slipped away",
        admission='"Our groceries are not more important than our neighbors," {a} said.',
        counsel='"The strongest choice protects whoever is most exposed," {helper} answered.',
        amends="warn the aisle first and return to their own load only after others were safe",
        lesson="care for people must come before pride or possessions",
    ),
    "listen": MoralChoice(
        temptation="shout competing plans without hearing each other",
        mistake="Their instructions collided, and helpers pulled in opposite directions",
        consequence="Good effort was wasted because nobody knew which plan to follow",
        admission='"I heard only my own idea," {b} confessed. "Please say yours again."',
        counsel='"Listening is also a kind of work," {helper} said.',
        amends="repeat the plan together and give each helper one clear instruction",
        lesson="respectful listening turns many hands into one team",
    ),
    "patience": MoralChoice(
        temptation="force a quick way through the crowd",
        mistake="They pushed harder when the aisle plainly needed time and space",
        consequence="Hurry made the huge movement slower and less safe",
        admission='"I treated waiting as weakness," {a} said, lowering the cart handle.',
        counsel='"Patience is how careful work keeps moving," {helper} explained.',
        amends="stop, count to ten, and restart only when the route was clear",
        lesson="patient action can solve a problem that force only worsens",
    ),
    "return_credit": MoralChoice(
        temptation="claim the clever warning as their own idea",
        mistake="They accepted praise that belonged to a quiet shopper nearby",
        consequence="The shopper turned away, hurt, while the real clue went unexplained",
        admission='"That warning was not ours," {b} announced. "We should have said so at once."',
        counsel='"Giving credit is one way of giving thanks," {helper} said.',
        amends="invite the shopper to explain the clue and thank them before the whole aisle",
        lesson="gratitude and fairness keep trust from being lost",
    ),
    "keep_promise": MoralChoice(
        temptation="break the store's safety promise because the task looked urgent",
        mistake="They crossed the marked line after promising to wait",
        consequence="Their shortcut confused everyone who was following the agreed route",
        admission='"Urgency did not erase our promise," {a} told {b}.',
        counsel='"A promise is most useful when keeping it is inconvenient," {helper} said.',
        amends="return behind the line and carry out the safe plan they had agreed upon",
        lesson="reliability means doing what you promised under pressure",
    ),
    "ask_help": MoralChoice(
        temptation="hide their uncertainty so they would look capable",
        mistake="They wrestled with the problem alone even as it grew beyond them",
        consequence="Pride delayed the many willing hands already nearby",
        admission='"We do not know how to manage this safely," {b} called. "Will you help us?"',
        counsel='"Asking wisely is courage, not failure," {helper} answered.',
        amends="assign small, safe parts of the plan to the neighbors who volunteered",
        lesson="humility lets a community solve what two people cannot",
    ),
    "replace_damage": MoralChoice(
        temptation="hide a small thing they had damaged during the rush",
        mistake="They tucked the bent marker aside and hoped nobody would notice",
        consequence="Without the marker, the next workers could not read the safe route",
        admission='"We bent this, and hiding it made the problem worse," {a} said.',
        counsel='"Making amends means repairing more than your reputation," {helper} replied.',
        amends="replace the marker, explain the missing sign, and help anyone it had delayed",
        lesson="responsibility includes repairing the harm caused by a mistake",
    ),
    "include_newcomer": MoralChoice(
        temptation="ignore a new volunteer whose voice they did not recognize",
        mistake="They talked over the newcomer and missed an important warning",
        consequence="The overlooked knowledge left their plan with a dangerous gap",
        admission='"We decided who mattered before we listened," {b} said.',
        counsel='"Wisdom does not wear a name tag you already know," {helper} reminded them.',
        amends="ask the newcomer to explain the warning and give them a real part in the repair",
        lesson="including unfamiliar voices can make the whole community wiser",
    ),
}


ENDINGS = {
    "lamplight": Ending("Under the evening lamps, the safe carts stood in a neat crescent around the silo", "The two friends went home knowing that good character is easiest to see when the aisle is hardest to cross."),
    "chalk": Ending("Before closing, they wrote the day's lesson on the chalkboard beside the scale", "In the morning, the first shoppers paused to read it before taking a cart."),
    "last_scoop": Ending("At sunset, they poured the last bright scoop of grain into the silo together", "Neither asked who had poured more."),
    "quiet_wheels": Ending("The final empty cart rolled back through a wide, quiet aisle", "Its gentle wheels sounded like the store breathing out."),
    "shared_bread": Ending("The baker brought one warm roll and split it into three equal pieces", "Crumbs shone on their palms while the tall silo cast a peaceful shadow."),
    "paper_sign": Ending("They hung a small sign on the silo: MOVE TOGETHER, SPEAK THE TRUTH", "The sign fluttered whenever a cart passed safely beneath it."),
    "window": Ending("In the dark shop window, their reflections walked side by side past orderly rows of food", "Behind them, the silo was full and the dangerous aisle was empty."),
    "seed_pouch": Ending("The clerk gave each friend a tiny pouch of oats rescued from the trouble", "They planted the grains at home and remembered that careful choices can grow."),
}

REFLECTIONS = {
    "check_neighbor": "Before moving on, {a} asked a nearby shopper whether the aisle felt safe from their side too",
    "trade_jobs": "For the final cart, the friends traded jobs and discovered that each task required care",
    "thank_helper": "They thanked {helper} for correcting them, even though hearing the correction had been hard",
    "teach_next": "When a new volunteer arrived, {b} calmly explained both the safe route and the mistake they had repaired",
    "walk_route": "The friends walked the whole route once more, checking that their solution had not shifted trouble elsewhere",
    "invite_question": "They invited everyone in the aisle to question the plan before the final cart moved",
    "restore_marker": "They returned every cone, sign, and tool to its proper place so the next crew would begin safely",
    "quiet_test": "Then they stood quietly for a moment and watched one cart complete the route without confusion",
}

TELLINGS = tuple(f"telling_{i}" for i in range(8))


def valid_combos() -> list[tuple[str, str, str]]:
    return [("grocery", "movement", "silo")]


def explain_rejection() -> str:
    return "(No story: this world only tells the grocery-store tale of movement around the silo bin.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale grocery store storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--helper", choices=HELPERS)
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
    if any([args.place, args.activity, args.prize]) and not (
        args.place in (None, "grocery")
        and args.activity in (None, "movement")
        and args.prize in (None, "silo")
    ):
        raise StoryError(explain_rejection())
    name_a = args.name_a or rng.choice(NAMES)
    name_b = args.name_b or rng.choice([name for name in NAMES if name != name_a])
    if name_a == name_b:
        raise StoryError("The two friends need different names.")
    return StoryParams(
        name_a=name_a,
        name_b=name_b,
        helper=args.helper or rng.choice(HELPERS),
        incident=rng.choice(tuple(INCIDENTS)),
        choice=rng.choice(tuple(CHOICES)),
        reflection=rng.choice(tuple(REFLECTIONS)),
        ending=rng.choice(tuple(ENDINGS)),
        telling=rng.choice(TELLINGS),
    )


def tell(params: StoryParams) -> World:
    incident = INCIDENTS[params.incident]
    choice = CHOICES[params.choice]
    ending = ENDINGS[params.ending]
    world = World(SETTINGS["grocery"])
    a = world.add(Entity(id=params.name_a, kind="character", type="girl", location="aisle"))
    b = world.add(Entity(id=params.name_b, kind="character", type="boy", location="aisle"))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=params.helper, location="aisle"))
    silo = world.add(Entity(id="silo", type="silo", label="grain silo bin", phrase="a tall silo bin of oats", location="back wall"))
    cart = world.add(Entity(id="cart", type="cart", label="cart", location="aisle"))

    world.facts.update(
        friend_a=a,
        friend_b=b,
        helper=helper,
        silo=silo,
        cart=cart,
        incident=incident,
        choice=choice,
        ending=ending,
    )

    introductions = [
        f"Once, in {world.setting.place}, {a.id} and {b.id} were friends who liked to make hard work feel light beside the grain silo.",
        f"The tall grain silo at the back of {world.setting.place} was the place where {a.id} and {b.id} worked best together.",
        f"On most mornings, {a.id} watched the front aisles while {b.id} helped measure oats at the store's tall silo.",
        f"{params.helper.capitalize()} trusted two young helpers, {a.id} and {b.id}, with the busy path between the loading door and the grain silo.",
        f"Before the grocery store opened, friends {a.id} and {b.id} checked the cart path around the tall grain silo.",
        f"At the grocery store's grain silo, {a.id} could lift quickly and {b.id} could spot small dangers; together, they made a fine team.",
        f"Every cart bound for the grocery store's grain silo passed the corner where {a.id} and {b.id} worked side by side.",
        f"The busiest corner of the grocery store lay beside its grain silo, and that was where friends {a.id} and {b.id} offered to help.",
    ]
    introduction = introductions[int(params.telling.rsplit("_", 1)[1])]
    world.facts["introduction"] = introduction
    world.say(introduction)
    world.say(f"That day, {incident.occasion}.")
    world.say(f"Soon {incident.movement}--a huge movement of goods that made the grocery store seem to sway.")

    world.para()
    a.meters["movement"] = 1
    b.meters["movement"] = 1
    cart.meters["movement"] = 1
    world.say(f"{a.id} noticed that {incident.first_sign}.")
    world.say(f"{incident.danger}.")
    propagate(world, narrate=True)

    world.para()
    a.memes["want"] = 1
    b.memes["want"] = 1
    world.say(f"The friends argued about {incident.dispute}, and each felt tempted to {choice.temptation}.")
    world.say(f"{choice.mistake}. {choice.consequence}.")
    a.memes["anger"] = 1
    propagate(world, narrate=True)

    world.para()
    admission = choice.admission.format(a=a.id, b=b.id, helper=params.helper)
    counsel = choice.counsel.format(a=a.id, b=b.id, helper=params.helper)
    if int(params.telling.rsplit("_", 1)[1]) % 2:
        world.say("The friends lowered their voices and looked at the trouble their choice had caused.")
    world.say(admission)
    world.say(counsel)
    a.memes["guilt"] = 1
    b.memes["guilt"] = 1
    a.memes["anger"] = 0
    b.memes["anger"] = 0
    a.memes["friendship"] = 1
    b.memes["friendship"] = 1
    world.say(f"They apologized and agreed to {choice.amends}.")
    world.say(f"Together they made a careful plan: {incident.plan}.")
    if int(params.telling.rsplit("_", 1)[1]) % 4 in (0, 3):
        world.say(f"{a.id} {incident.task_a}; {b.id} {incident.task_b}.")
    else:
        world.say(f"While {b.id} {incident.task_b}, {a.id} {incident.task_a}.")
    world.say(f"Because they followed the plan, {incident.result}.")
    world.say(REFLECTIONS[params.reflection].format(a=a.id, b=b.id, helper=params.helper) + ".")

    world.para()
    world.say(f"They understood then that {choice.lesson}.")
    world.say(f"{ending.image}.")
    world.say(ending.final_line)

    world.facts.update(
        resolved=True,
        moral=choice.lesson,
        changed_fact=incident.changed_fact,
        plan=incident.plan,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    a = world.facts["friend_a"]
    b = world.facts["friend_b"]
    incident = world.facts["incident"]
    return [
        f"Write a short folk tale in a grocery store where {incident.movement} near a grain silo.",
        f"Tell how {a.id} and {b.id} quarrel during a huge movement of goods, make a moral choice, and repair the harm.",
        f"Write a child-friendly friendship story about this problem: {incident.danger}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["friend_a"]
    b = world.facts["friend_b"]
    helper = world.facts["helper"]
    incident = world.facts["incident"]
    choice = world.facts["choice"]
    return [
        QAItem(
            question=f"Who faced the trouble when {incident.occasion}?",
            answer=f"The two friends were {a.id} and {b.id}, assisted by {helper.label}. They first argued, but then took responsibility for the store together.",
        ),
        QAItem(
            question=f"What warning did {a.id} notice before the movement became dangerous?",
            answer=f"{a.id} noticed that {incident.first_sign}. Soon afterward, {incident.danger.casefold()}.",
        ),
        QAItem(
            question=f"How did {a.id} and {b.id} repair the problem after being tempted to {choice.temptation}?",
            answer=f"They chose to {world.facts['plan']}. As a result, {incident.result}.",
        ),
        QAItem(
            question="What lesson did the friends carry into the story's final scene?",
            answer=f"With help from {helper.label}, they learned that {world.facts['moral']}. Their changed behavior meant that {world.facts['changed_fact']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a grocery store?",
            answer="A grocery store is a shop where people buy food and other things they need for home.",
        ),
        QAItem(
            question="What is a silo used for?",
            answer="A silo or grain bin is used to store dry food like oats or grain so it stays ready to scoop or measure.",
        ),
        QAItem(
            question="Why can crowded aisles cause trouble?",
            answer="Crowded aisles can cause trouble because people and carts may bump into each other and make it hard to move safely.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(grocery).
activity(movement).
prize(silo).
affords(grocery,movement).

valid(grocery,movement,silo).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "grocery"),
        asp.fact("activity", "movement"),
        asp.fact("prize", "silo"),
        asp.fact("affords", "grocery", "movement"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
        for i, p in enumerate(sample.prompts, 1):
            print(f"[Prompt {i}] {p}")
        for q in sample.story_qa:
            print()
            print(show_qa_item(q))
        for q in sample.world_qa:
            print()
            print(show_qa_item(q))


CURATED = [
    StoryParams(name_a="Mina", name_b="Jory", helper="the clerk", incident="runaway_oats", choice="truth", reflection="walk_route", ending="last_scoop", telling="telling_0"),
    StoryParams(name_a="Lena", name_b="Tomas", helper="the porter", incident="quiet_hour", choice="listen", reflection="quiet_test", ending="quiet_wheels", telling="telling_5"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
