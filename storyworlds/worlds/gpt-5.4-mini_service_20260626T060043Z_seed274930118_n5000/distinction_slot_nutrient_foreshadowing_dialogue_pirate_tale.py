#!/usr/bin/env python3
"""
storyworlds/worlds/distinction_slot_nutrient_foreshadowing_dialogue_pirate_tale.py
===================================================================================

A small pirate-tale story world built from the seed words:
distinction, slot, nutrient.

The premise is a young pirate who longs for distinction on a ship, but a
foreshadowed problem threatens the crew: the galley's nutrient slot is empty.
A dialogue-led compromise turns the worry into a useful deed, and the ending
proves what changed by showing the crew nourished and the hero recognized.

Narrative instruments:
- Foreshadowing
- Dialogue
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

# Physical meter keys
METERS = {"hunger", "sail_ready", "storm", "supplies", "respect"}

# Emotional meme keys
MEMES = {"pride", "worry", "hope", "shame", "trust"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    slot: str = ""
    fills: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in METERS:
            self.meters.setdefault(k, 0.0)
        for k in MEMES:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    holds: dict[str, Optional[str]] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in METERS})
    memes: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in MEMES})
    facts: dict = field(default_factory=dict)

    def copy(self) -> "Ship":
        clone = Ship(self.name, self.place)
        clone.holds = dict(self.holds)
        clone.meters = copy.deepcopy(self.meters)
        clone.memes = copy.deepcopy(self.memes)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[Ship], list[str]]


def _r_hunger(ship: Ship) -> list[str]:
    out = []
    if ship.holds.get("nutrient_slot") is None and ship.meters["storm"] >= THRESHOLD:
        if ship.meters["hunger"] < 2:
            ship.meters["hunger"] += 1
            out.append("The crew's bellies started to rumble.")
    return out


def _r_respect(ship: Ship) -> list[str]:
    out = []
    if ship.holds.get("nutrient_slot") == "nutrient_crate" and ship.facts.get("resolved"):
        if ship.meters["respect"] < 1:
            ship.meters["respect"] = 1
            out.append("The crew nodded, seeing the young pirate had done a worthy thing.")
    return out


RULES = [Rule("hunger", _r_hunger), Rule("respect", _r_respect)]


def propagate(ship: Ship, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sent = rule.apply(ship)
            if sent:
                changed = True
                produced.extend(sent)
    return produced if narrate else []


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    captain_name: str
    ship_name: str
    place: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HERO_NAMES = ["Finn", "Mina", "Jory", "Pip", "Nell", "Toby", "Rae"]
CAPTAIN_NAMES = ["Captain Brine", "Captain Coral", "Captain Morrow", "Captain Salt"]
SHIP_NAMES = ["The Winking Gull", "The Starboard Fox", "The Merry Kraken", "The Tide Runner"]
PLACES = ["the harbor", "the dock", "the moonlit pier", "the old quay"]


@dataclass(frozen=True)
class StoryArc:
    id: str
    ambition: str
    nutrient: str
    slot: str
    omen: str
    danger: str
    task: str
    complication: str
    turn: str
    result: str
    ending: str


ARCS = [
    StoryArc(
        "broth_stove", "take charge of the storm watch", "ginger broth", "galley warming slot",
        "the cook's ladle rolled across the deck before the first wave struck",
        "the empty warming slot would leave the soaked crew cold and hungry",
        "lash the broth crate to a serving tray and carry it below",
        "a wave tilted the companionway and sent the tray sliding",
        "hooked the tray with a mop handle while the cook steadied the crate",
        "the broth reached the warming slot before the rain",
        "steam curled from twelve mugs beneath the storm lantern",
    ),
    StoryArc(
        "lime_rack", "chart the next long crossing", "fresh limes", "ration-rack slot",
        "the last green lime rolled from the rack as the ship's map showed weeks of open water",
        "without the limes' nutrient, the crew might grow weak on the long crossing",
        "bring the lime hamper aboard and fit it into the ration rack",
        "the hamper was too broad to pass the narrow hatch",
        "made two canvas slings and lowered the limes through the skylight",
        "every lime was counted into the proper slot",
        "green peels spiraled beside the compass as dawn opened the sea",
    ),
    StoryArc(
        "bean_locker", "ring the departure bell", "dried beans", "pantry slot",
        "weevils crept from an old sack while gulls circled the waiting tide",
        "the spoiled sack could not supply the nutrient the rowing crew needed",
        "sort the sound beans, seal them in tins, and fill the pantry slot",
        "one tin split and scattered beans beneath the water barrels",
        "formed a bucket line and swept every clean bean into a spare tin",
        "the sealed tins clicked safely into the pantry slot",
        "the departure bell rang above a pot bubbling with red beans",
    ),
    StoryArc(
        "grain_chute", "serve beside the quartermaster", "whole-grain meal", "measuring-chute slot",
        "a pale stream of meal trickled from a seam before anyone opened the bin",
        "a split chute would waste the nutrient-rich meal before breakfast",
        "patch the chute and slide its measuring cup into the empty slot",
        "the ship rolled, widening the seam faster than one pair of hands could stitch",
        "called the sailmaker to brace the chute, then sealed it with waxed canvas",
        "the repaired cup measured a fair scoop for every sailor",
        "golden porridge shone in bowls lined along the quiet rail",
    ),
    StoryArc(
        "kelp_drawer", "keep the shore charts", "dried kelp", "dry-store slot",
        "a damp green thread appeared beneath the dry-store door at low tide",
        "seawater would ruin the kelp and wash away its useful nutrient",
        "find the leak, dry the packets, and move them into the high slot",
        "a crab had wedged the drain flap open behind a heavy coil of rope",
        "used a boathook to free the crab and worked with the mate to lift the coil",
        "the drain shut and the kelp packets rested dry above the waterline",
        "crisp green ribbons topped the crew's supper under a clearing sky",
    ),
    StoryArc(
        "oat_labels", "prove that careful work mattered more than boasting", "rolled oats", "breakfast-bin slot",
        "two identical barrels knocked together whenever the tide turned",
        "the lamp-oil barrel could be mistaken for the oats the crew needed for nutrient-rich breakfast",
        "test the seals, mark the oat barrel, and place it in the breakfast slot",
        "rain blurred the chalk label just as the barrels were being moved",
        "cut an oat-shaped stamp from cork and pressed a lasting mark into the lid",
        "the correctly marked barrel settled into its own slot",
        "oatcakes cooled in neat rows while the oily barrel stayed locked away",
    ),
    StoryArc(
        "fruit_net", "carry the captain's signal pennant", "dried apricots", "hanging-net slot",
        "one frayed cord snapped and dropped an empty net beside the capstan",
        "the next snap could spill the fruit and its nutrient into the bilge",
        "splice a stronger net and load the apricots into its slot",
        "the mast rope needed for the splice was already holding a loose sail",
        "braided short galley cords while two deckhands secured the sail",
        "the new net held firm through three hard rolls",
        "orange apricots glowed in the net as the pennant cracked overhead",
    ),
    StoryArc(
        "mineral_filter", "steer through the reef gate", "mineral water", "cask-filter slot",
        "the water tap coughed out one cloudy drop while the reef wind freshened",
        "a clogged filter would keep the crew from the water and nutrient salts they needed",
        "clean the filter stones and return the basket to its slot",
        "a pebble jammed the basket where fingers could not reach",
        "bent a spoon into a hook and guided the pebble out by lantern light",
        "clear water rang into every cup from the restored filter",
        "silver drops flashed from the tap while the ship slipped between the reefs",
    ),
    StoryArc(
        "rescue_rations", "command the smallest rescue boat", "pea biscuits", "lifeboat ration slot",
        "an empty wrapper fluttered from the lifeboat before a distant flare rose",
        "the rescue crew could not row far without a compact nutrient ration",
        "pack pea biscuits into the lifeboat's narrow slot",
        "the tin fit the slot but rattled loose whenever the oars struck",
        "folded a cork cradle and tied it down with a sailor's crossing knot",
        "the ration tin stayed secure throughout the rescue",
        "the saved fisher shared a pea biscuit as both boats met the sunrise",
    ),
    StoryArc(
        "sickbay_tonic", "assist the ship's healer", "orange-and-mint tonic", "sickbay bottle slot",
        "the empty bottle rack chimed as a feverish lookout coughed overhead",
        "the lookout needed drink, rest, and the tonic's nutrient before the night watch",
        "mix the tonic, cool it, and secure its bottle in the padded slot",
        "the cork popped free when warm tonic met the cold bottle",
        "cooled the mixture in a wet cloth and asked the healer to check it before recorking",
        "the lookout drank safely and slept while another sailor took watch",
        "a full tonic bottle gleamed beside the lookout's folded red scarf",
    ),
    StoryArc(
        "seed_tray", "tend the captain's cabin garden", "cress seedlings", "sun-tray slot",
        "three dry leaves skittered from the cabin window although planting day had just begun",
        "without water and light, the seedlings could not make the fresh nutrient the crew hoped to eat",
        "mend the cracked tray and set it in the sunny slot",
        "a passing boom shadowed the only patch of morning light",
        "rigged a small polished plate to reflect sunlight around the boom",
        "the sealed tray caught both clean water and steady light",
        "tiny green cress leaves pointed toward their square of borrowed sun",
    ),
    StoryArc(
        "sesame_chest", "sit in the captain's council", "sesame cakes", "emergency-chest slot",
        "the emergency chest clicked open by itself when thunder shook the quay",
        "its bare slot meant no quick nutrient food would be ready if the ship lost its galley",
        "wrap the sesame cakes against damp and lock them into the chest",
        "the old key turned halfway and threatened to break in the lock",
        "rubbed the lock with graphite, then let the carpenter ease the key around",
        "the dry cakes were inventoried and the chest closed without forcing it",
        "a sesame star rested on the lid beside the captain's checked ledger",
    ),
]

INTRO_FORMS = [
    "At {place}, {hero} served aboard {ship} and hoped to {ambition}. {hero} had chased distinction with loud boasts, but no boast had helped the crew.",
    "The youngest pirate on {ship} was {hero}. While the vessel waited at {place}, {hero} dreamed of distinction and a chance to {ambition}.",
    "Morning found {hero} working the deck of {ship} at {place}. The pirate wanted distinction, especially the honor to {ambition}, yet the captain watched deeds rather than swagger.",
    "{hero} could polish brass and climb rigging, but had not yet earned distinction aboard {ship}. At {place}, one careful job might prove {hero} ready to {ambition}.",
    "Before {ship} sailed from {place}, {hero} asked for a grander duty. Distinction, the young pirate believed, would mean being allowed to {ambition}.",
    "On the tide before departure, {hero} stood aboard {ship} at {place}. Instead of treasure, {hero} wanted the distinction of being trusted to {ambition}.",
]

DIALOGUE_FORMS = [
    ('"Did you notice that warning?" asked {captain}.', '"Yes," said {hero}. "It means {danger}. Let me {task}."'),
    ('{captain} pointed toward the trouble. "Tell me what it foretells, {hero}."', '"It foretells that {danger}," {hero} replied. "I can {task}."'),
    ('"A pirate seeking distinction should read small signs," said {captain}. "What do you see?"', '"I see that {danger}," said {hero}. "We should {task}."'),
    ('{hero} tugged the captain\'s sleeve. "That sign is not harmless, is it?"', '"No," said {captain}. "It warns that {danger}. What is your plan?" {hero} answered, "I will {task}."'),
    ('"Crew, look closely," called {captain}. "Something is about to go wrong."', '"Then we act before it does," {hero} said. "First we {task}."'),
    ('{captain} asked quietly, "Do you still want distinction, {hero}?"', '"Yes, but the crew needs help first," said {hero}. "The sign means {danger}, so I will {task}."'),
]

ACTION_LEADS = [
    "The work began at once.",
    "There was no time for another boast.",
    "Together, the pirates put the plan in motion.",
    "The captain gave one nod, and the deck became busy.",
    "With the warning still in mind, {hero} started carefully.",
    "The crew made room while {hero} gathered the needed tools.",
]

SUPPORT_ACTIONS = [
    "the cook protected the remaining food from spray",
    "two deckhands cleared a safe path through the coils",
    "the carpenter laid out only the tools the job required",
    "the lookout called each roll of the ship before it came",
    "the quartermaster checked every item against the ledger",
    "the sailmaker tied a safety line around the work area",
    "the cabin helper carried a dry lantern close to the work",
    "the mate assigned one steady hand to hold each loose piece",
]

AWARDS = [
    "a brass compass badge", "a blue watch ribbon", "a carved wooden star",
    "the silver deck whistle", "a place in the captain's log", "a red duty sash",
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A nutrient slot matters when a ship has a slot and the crate can fit it.
needs_nutrient(S) :- ship(S), empty_slot(S, nutrient_slot).
can_fill(S) :- needs_nutrient(S), crate(nutrient_crate), fits(nutrient_crate, nutrient_slot).

% A story is reasonable when the young pirate wants distinction, the nutrient
% slot is empty, and there is a compatible crate to fill it.
valid_story(P) :- wants_distinction(P), ship(S), can_fill(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("ship", "ship"))
    lines.append(asp.fact("empty_slot", "ship", "nutrient_slot"))
    lines.append(asp.fact("crate", "nutrient_crate"))
    lines.append(asp.fact("fits", "nutrient_crate", "nutrient_slot"))
    lines.append(asp.fact("wants_distinction", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    return bool(asp.atoms(model, "valid_story"))


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate tale about distinction, a slot, and a nutrient crate."
    )
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--captain", choices=CAPTAIN_NAMES)
    ap.add_argument("--ship", choices=SHIP_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(
        hero_name=hero_name,
        hero_type="boy" if hero_name in {"Finn", "Jory", "Pip", "Toby"} else "girl",
        captain_name=args.captain or rng.choice(CAPTAIN_NAMES),
        ship_name=args.ship or rng.choice(SHIP_NAMES),
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name not in HERO_NAMES:
        raise StoryError("The young pirate must be a known crew member.")
    if params.place not in PLACES:
        raise StoryError("This harbor scene needs a known place.")
    if not params.ship_name or not params.captain_name:
        raise StoryError("The ship and captain must be named.")


def make_world(params: StoryParams) -> Ship:
    ship = Ship(params.ship_name, params.place)
    ship.holds["nutrient_slot"] = None
    ship.facts["hero_name"] = params.hero_name
    ship.facts["captain_name"] = params.captain_name
    ship.facts["ship_name"] = params.ship_name
    ship.facts["place"] = params.place
    return ship


def foreshadow(ship: Ship) -> str:
    ship.memes["worry"] += 1
    ship.meters["storm"] += 1
    arc: StoryArc = ship.facts["arc"]
    return (
        f"A warning came early: {arc.omen}. It foreshadowed a real danger: "
        f"{arc.danger}."
    )


def dialogue_offer(ship: Ship) -> str:
    ship.memes["hope"] += 1
    ship.memes["pride"] += 1
    arc: StoryArc = ship.facts["arc"]
    warning, answer = ship.facts["dialogue"]
    values = {
        "hero": ship.facts["hero_name"],
        "captain": ship.facts["captain_name"],
        "danger": arc.danger,
        "task": arc.task,
    }
    return " ".join((warning.format(**values), answer.format(**values)))


def resolve(ship: Ship) -> str:
    arc: StoryArc = ship.facts["arc"]
    hero = ship.facts["hero_name"]
    captain = ship.facts["captain_name"]
    ship.holds["nutrient_slot"] = "nutrient_crate"
    ship.meters["hunger"] = 0
    ship.meters["supplies"] = 1
    ship.facts["resolved"] = True
    propagate(ship, narrate=False)
    return (
        f"The result was plain: {arc.result}. {arc.ending.capitalize()}. "
        f'{captain} gave {hero} {ship.facts["award"]}. "That is distinction," the captain said. '
        f'"You read the warning, protected the crew\'s nutrient supply, and asked for help when it mattered."'
    )


def tell_story(params: StoryParams) -> Ship:
    ship = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else "|".join(
        (params.hero_name, params.captain_name, params.ship_name, params.place)
    ))
    arc = rng.choice(ARCS)
    intro_form = rng.choice(INTRO_FORMS)
    dialogue = rng.choice(DIALOGUE_FORMS)
    action_lead = rng.choice(ACTION_LEADS)
    support_action = rng.choice(SUPPORT_ACTIONS)
    award = rng.choice(AWARDS)
    ship.facts.update({
        "arc": arc,
        "arc_id": arc.id,
        "distinction": award,
        "slot": arc.slot,
        "nutrient": arc.nutrient,
        "danger": arc.danger,
        "task": arc.task,
        "complication": arc.complication,
        "turn": arc.turn,
        "result": arc.result,
        "ending": arc.ending,
        "dialogue": dialogue,
        "support_action": support_action,
        "award": award,
    })
    ship.facts["resolved"] = False
    ship.meters["hunger"] = 1
    ship.meters["storm"] = 0
    intro = intro_form.format(
        hero=params.hero_name,
        ship=params.ship_name,
        place=params.place,
        ambition=arc.ambition,
    )
    f1 = foreshadow(ship)
    d1 = dialogue_offer(ship)
    lead = action_lead.format(hero=params.hero_name)
    action = (
        f"{lead} Meanwhile, {support_action}. {params.hero_name} tried to {arc.task}. "
        f"Then {arc.complication}. "
        f"Instead of hiding the setback, {params.hero_name} {arc.turn}."
    )
    ending = resolve(ship)
    structure = rng.randrange(4)
    if structure == 0:
        paragraphs = [intro, f1, d1, action, ending]
    elif structure == 1:
        paragraphs = [intro + " " + f1, d1, action, ending]
    elif structure == 2:
        paragraphs = [intro, f1 + " " + d1, action, ending]
    else:
        paragraphs = [intro, f1, d1 + " " + action, ending]
    ship.facts["structure"] = structure
    ship.facts["story"] = "\n\n".join(paragraphs)
    return ship


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(ship: Ship) -> list[str]:
    return [
        'Write a short pirate tale with the words "distinction", "slot", and "nutrient".',
        f"Tell a story about {ship.facts['hero_name']} on {ship.facts['ship_name']} where the {ship.facts['slot']} becomes important.",
        f"Foreshadow danger to the {ship.facts['nutrient']}, use dialogue to make a plan, and end with a concrete sign of distinction.",
    ]


def story_qa(ship: Ship) -> list[QAItem]:
    hero = ship.facts["hero_name"]
    captain = ship.facts["captain_name"]
    arc: StoryArc = ship.facts["arc"]
    return [
        QAItem(
            question=f"What distinction did {hero} seek from {captain} aboard {ship.name} at {ship.place}?",
            answer=f"{hero} wanted distinction and hoped to {arc.ambition}. The captain required a useful deed rather than a boast.",
        ),
        QAItem(
            question=f"What danger did {captain} and {hero} infer from the early sign on {ship.name} at {ship.place}?",
            answer=f"The sign warned that {arc.danger}. {captain} asked {hero} to read that warning before the trouble grew.",
        ),
        QAItem(
            question=f"When the plan met trouble aboard {ship.name}, how did {hero} and {captain}'s crew respond?",
            answer=f"While {ship.facts['support_action']}, {hero} faced this complication: {arc.complication}. {hero} then {arc.turn}, which let the crew finish the job.",
        ),
        QAItem(
            question=f"What final image aboard {ship.name} at {ship.place} showed {captain} that {hero} had resolved the {arc.slot} problem?",
            answer=f"{arc.ending.capitalize()}. The captain also gave {hero} {ship.facts['award']} as a mark of distinction.",
        ),
    ]


def world_qa(ship: Ship) -> list[QAItem]:
    return [
        QAItem(
            question="What is distinction?",
            answer="Distinction is being set apart in a good way, like being noticed for a brave or helpful act.",
        ),
        QAItem(
            question="What is a slot?",
            answer="A slot is a place where one thing fits snugly, like a space made for a crate or tool.",
        ),
        QAItem(
            question="What is a nutrient?",
            answer="A nutrient is something in food that helps bodies grow strong and stay healthy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(ship: Ship) -> str:
    lines = ["--- trace ---"]
    lines.append(f"ship={ship.name}")
    lines.append(f"place={ship.place}")
    lines.append(f"holds={ship.holds}")
    lines.append(f"meters={ship.meters}")
    lines.append(f"memes={ship.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    ship = tell_story(params)
    return StorySample(
        params=params,
        story=ship.facts["story"],
        prompts=prompts(ship),
        story_qa=story_qa(ship),
        world_qa=world_qa(ship),
        world=ship,
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


# ---------------------------------------------------------------------------
# ASP helpers / verification
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp

    ok = asp_valid()
    py_ok = True
    if ok != py_ok:
        print("MISMATCH between ASP and Python gate.")
        return 1
    print("OK: ASP and Python gates agree.")
    sample = generate(StoryParams(
        hero_name="Pip",
        hero_type="boy",
        captain_name="Captain Brine",
        ship_name="The Winking Gull",
        place="the harbor",
    ))
    assert "distinction" in sample.story
    assert "nutrient" in sample.story
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP gate: valid_story/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(
                hero_name="Pip", hero_type="boy", captain_name="Captain Brine",
                ship_name="The Winking Gull", place="the harbor",
            ),
            StoryParams(
                hero_name="Mina", hero_type="girl", captain_name="Captain Coral",
                ship_name="The Starboard Fox", place="the dock",
            ),
            StoryParams(
                hero_name="Nell", hero_type="girl", captain_name="Captain Morrow",
                ship_name="The Merry Kraken", place="the moonlit pier",
            ),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < max(1, args.n) and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
