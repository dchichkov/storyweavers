#!/usr/bin/env python3
"""
A small storyworld about a nursery-rhyme supper, a foreshadowed mix-up, a twist,
and a gentle problem-solving ending.

Seed-image premise:
- A child helps in a bright kitchen.
- Jambalaya and lasagne are both being prepared.
- A duplicate dish appears, and everyone must sort out what is what.

The story should read like a tiny rhyme-like tale with:
- Foreshadowing: a clue about a second tray or extra bowl
- Twist: the duplicate is not the dish anyone first expected
- Problem Solving: labels, smells, and care put the meal back in order
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, REPO_ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    first: object | None = None
    helper: object | None = None
    hero: object | None = None
    second: object | None = None
    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Kitchen:
    place: str = "the kitchen"
    glowing: bool = True
    tidy: bool = True
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    scent: str
    color: str
    kind: str = "food"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    case_id: str = "copied_labels"
    telling_mode: str = "clue_first"
    detail_id: int = 0
    seed: Optional[int] = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
KITCHENS = {
    "sunny": Kitchen(place="the sunny kitchen", glowing=True, tidy=True),
    "cozy": Kitchen(place="the cozy kitchen", glowing=False, tidy=True),
    "busy": Kitchen(place="the busy kitchen", glowing=True, tidy=False),
}

DISHES = {
    "jambalaya": Dish(
        id="jambalaya",
        label="jambalaya",
        phrase="a pot of jambalaya",
        scent="spicy",
        color="golden",
    ),
    "lasagne": Dish(
        id="lasagne",
        label="lasagne",
        phrase="a tray of lasagne",
        scent="cheesy",
        color="red-and-gold",
    ),
}

# The duplicate is the story's trick: a second dish can be mistaken for the first.
DUPLICATE_KINDS = ["label", "tray", "bowl", "lid"]


@dataclass(frozen=True)
class KitchenCase:
    case_id: str
    duplicate: str
    setup: str
    clue: str
    trouble: str
    first_guess: str
    test: str
    twist: str
    repair: str
    lesson: str
    ending: str


CASES = {
    case.case_id: case
    for case in [
        KitchenCase(
            case_id="copied_labels",
            duplicate="two identical food labels",
            setup="A label printer chattered beside the cooling dishes",
            clue="one label had a tiny blue ink crescent under its last letter",
            trouble="both labels said 'lasagne,' leaving the jambalaya pot unnamed",
            first_guess="that someone had cooked two trays of lasagne",
            test="compare the blue crescent with the printer's test strip and check each dish's ingredients",
            twist="the printer had copied a label, not the meal",
            repair="write one fresh jambalaya label and place both labels beside the correct dishes",
            lesson="copies can look convincing, so evidence matters more than a quick guess",
            ending="the blue-crescent misprint rested in the recycling basket beside two plainly named dishes",
        ),
        KitchenCase(
            case_id="recipe_cards",
            duplicate="two recipe cards with the same title",
            setup="Two flour-dusted cards peeked from beneath the mixing bowl",
            clue="only one card carried Nana's green note about when to add the rice",
            trouble="the cooks began following different jambalaya instructions while the lasagne sauce bubbled",
            first_guess="that Nana had written the recipe twice by mistake",
            test="line up the steps and match the green note to the simmering rice",
            twist="one card was an old draft saved for comparison, not a second finished recipe",
            repair="mark the draft 'practice,' keep the finished card by the jambalaya, and return to the correct step",
            lesson="a duplicate document may have a different purpose, so its details should be checked",
            ending="the practice card hung on a clip while the finished card stood cleanly beside the golden pot",
        ),
        KitchenCase(
            case_id="twin_timers",
            duplicate="two matching kitchen timers",
            setup="Two silver timers ticked in perfect unison on the shelf",
            clue="a strand of red yarn was tied around just one timer's foot",
            trouble="one bell rang early and made everyone think the lasagne was done",
            first_guess="that both timers measured the same oven",
            test="follow each timer's yarn tag and compare its remaining minutes with the written cooking plan",
            twist="the red-tagged timer belonged to the rice pot, while the other watched the lasagne",
            repair="set the timers beside their dishes and add large picture cards showing a pot and a tray",
            lesson="matching tools can have separate jobs, and clear links prevent rushed decisions",
            ending="the pot card and tray card stood upright as the two timers gave their bells at different, proper moments",
        ),
        KitchenCase(
            case_id="lookalike_trays",
            duplicate="two red-and-gold lasagne trays",
            setup="A second red-and-gold rectangle appeared at the far end of the counter",
            clue="it stayed cool and made no cheesy smell at all",
            trouble="the serving team nearly carried the real lasagne to the display table",
            first_guess="that an extra lasagne had somehow been baked",
            test="feel for warmth from a safe distance, notice the scent, and ask the helper who built the display",
            twist="the duplicate was a cardboard model for the menu board",
            repair="hang the model on the menu board and leave the warm tray on its heat-safe mat",
            lesson="appearance alone cannot tell what an object is or how it should be handled",
            ending="the cardboard lasagne smiled from the menu board while steam curled from the real supper below",
        ),
        KitchenCase(
            case_id="double_order",
            duplicate="two matching supper tickets",
            setup="The order rail held two slips numbered twelve",
            clue="one slip had a star punched through its corner",
            trouble="the team started packing the same jambalaya-and-lasagne meal twice while another table waited",
            first_guess="that table twelve had ordered a duplicate feast",
            test="ask the dining-room helper, compare the handwriting, and check the punched star against the practice pad",
            twist="the starred ticket was the helper's rehearsal copy from before supper",
            repair="file the rehearsal slip, finish one meal for table twelve, and prepare the waiting table's real order",
            lesson="confirming a duplicate prevents waste and makes sharing fair",
            ending="one neat tray traveled to table twelve as the starred practice slip slid into the lesson folder",
        ),
        KitchenCase(
            case_id="inventory_echo",
            duplicate="a repeated pantry entry",
            setup="The pantry tablet displayed 'rice: two sacks' on neighboring lines",
            clue="both lines carried the very same scan time down to the second",
            trouble="the cooks planned portions using rice that was not actually there",
            first_guess="that a new sack had arrived unnoticed",
            test="count the sealed sacks together and compare the two scan records",
            twist="one barcode scan had echoed into the list twice",
            repair="remove the duplicate entry, adjust the portions, and add a second-person check for future deliveries",
            lesson="a repeated record is not the same as a repeated real object",
            ending="a single rice sack stood beneath a corrected screen while every bowl still received a fair scoop",
        ),
        KitchenCase(
            case_id="vented_lids",
            duplicate="two round pot lids",
            setup="Two round lids gleamed beside the jambalaya pot",
            clue="one lid had a tiny steam vent shaped like a moon",
            trouble="the unvented lid trapped too much steam and made the pot rattle",
            first_guess="that the lids were safe duplicates and either one would do",
            test="turn off the heat with adult help, inspect both cooled lids, and read the pot maker's guide",
            twist="only the moon-vented lid was made for the jambalaya pot",
            repair="use the proper vented lid and label the other for its matching storage bowl",
            lesson="near-duplicates may work differently, especially around heat",
            ending="one quiet puff rose through the moon-shaped vent while the other lid waited on its clearly marked shelf",
        ),
        KitchenCase(
            case_id="spice_twins",
            duplicate="two jars marked 'mild spice'",
            setup="Twin spice jars stood shoulder to shoulder near the jambalaya",
            clue="one jar's paper seal showed a small cinnamon-colored thumbprint",
            trouble="the wrong jar would make the savory rice taste like sweet toast",
            first_guess="that the jars held duplicate batches of the same seasoning",
            test="read the ingredient lists and let the helper compare each scent away from the cooking steam",
            twist="a reused jar held cinnamon even though its old front label remained",
            repair="replace the stale label, return the cinnamon to the baking shelf, and season the jambalaya from the verified jar",
            lesson="containers can be reused, so their current contents must be identified carefully",
            ending="the cinnamon jar sat by the flour while the savory spice made a warm little cloud above the rice",
        ),
        KitchenCase(
            case_id="photo_plate",
            duplicate="a picture of the finished supper",
            setup="A glossy plate of jambalaya and lasagne seemed to appear in the serving hatch",
            clue="its steam never moved, even when the kitchen door swung open",
            trouble="the team paused, unsure which supper plate still needed serving",
            first_guess="that someone had prepared a duplicate plate",
            test="look from the side, trace the flat edge, and ask why the photographer had visited",
            twist="the duplicate meal was a life-size photograph for the recipe book",
            repair="mount the photograph on the wall and place the real meal on the serving cart",
            lesson="a duplicate image can preserve information without being the object itself",
            ending="the photograph shone above the sink while the real plate rolled away beneath a silver cover",
        ),
        KitchenCase(
            case_id="shopping_line",
            duplicate="a duplicated line on the shopping list",
            setup="The shopping list named tomatoes twice in a row",
            clue="the second line began with the same crooked letter and ended at the same torn fold",
            trouble="the cooks almost opened twice as many tomatoes and crowded the sauce pan",
            first_guess="that both jambalaya and lasagne required separate full baskets",
            test="check each recipe's amount, add the totals, and compare them with the unopened tins",
            twist="the folded paper had made one line show through and look duplicated",
            repair="rewrite one clear total and save the extra tomatoes for another meal",
            lesson="solving a duplicate can protect ingredients from being wasted",
            ending="the spare tomatoes formed a tidy red row in the pantry as one well-measured sauce simmered",
        ),
        KitchenCase(
            case_id="serving_spoons",
            duplicate="two long wooden spoons",
            setup="Two long spoons crossed like drumsticks between the dishes",
            clue="one handle bore three shallow measuring notches",
            trouble="using the larger spoon for both foods would give some guests far more than others",
            first_guess="that the spoons were interchangeable duplicates",
            test="compare their bowl sizes, count the notches, and make one practice scoop into empty cups",
            twist="the notched spoon was a portion measure while the plain spoon was only for stirring",
            repair="serve equal jambalaya portions with the notched spoon and use a flat server for the lasagne",
            lesson="tools that look alike can support fairness in different ways",
            ending="equal golden scoops circled the table while the plain spoon dried above the empty pot",
        ),
        KitchenCase(
            case_id="recipe_projection",
            duplicate="a second recipe projected on the wall",
            setup="A pale copy of the lasagne recipe floated beside the paper original",
            clue="the floating words vanished whenever someone covered the tablet lens",
            trouble="the reflected instructions appeared backward and sent the team toward the wrong shelf",
            first_guess="that a mysterious cook had posted duplicate directions",
            test="move the tablet, cover its lens once more, and read the paper card aloud together",
            twist="a shiny ladle had reflected the tablet's recipe onto the wall",
            repair="turn the ladle face down, prop the real recipe where everyone can see it, and resume the correct step",
            lesson="a duplicate can be a reflection, so tracing its source reveals what is real",
            ending="the wall turned blank again while the lasagne's bubbling corners matched the final picture on the card",
        ),
    ]
}

TELLING_MODES = (
    "clue_first",
    "bell_first",
    "dialogue_first",
    "question_first",
    "quiet_first",
    "helper_first",
    "rhyme_first",
    "result_first",
)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def story_reasonable(place: str) -> bool:
    return place in KITCHENS


def explain_rejection(place: str) -> str:
    return f"(No story: the place '{place}' is not part of this little kitchen tale.)"


# ---------------------------------------------------------------------------
# Narration and world building
# ---------------------------------------------------------------------------
OPENINGS = {
    "clue_first": "Before the first spoon clinked, {hero} noticed something that did not quite belong.",
    "bell_first": "Ding went the kitchen bell, and {hero} looked up from the supper table.",
    "dialogue_first": "'Two dishes, one careful plan,' said {helper}, as {hero} tied on an apron.",
    "question_first": "How could one supper seem to contain an extra copy? {hero} was about to find out.",
    "quiet_first": "For one quiet minute, the kitchen held only the burble of rice and the soft hiss of sauce.",
    "helper_first": "{helper} checked the oven while {hero} arranged bowls for the evening meal.",
    "rhyme_first": "Rice in a pot and pasta in rows; watch every copy, and follow what shows.",
    "result_first": "Later, everyone would remember the duplicate that nearly muddled supper.",
}

BRIDGES = (
    "The small detail seemed unimportant, yet {hero} tucked it away like a puzzle piece.",
    "{hero} pointed it out. 'That may matter later,' {helper} agreed.",
    "No one stopped cooking, but the clue stayed in {hero}'s thoughts.",
    "It was the sort of clue that whispers before a mystery speaks aloud.",
    "{helper} drew a tiny star beside the clue on the kitchen notepad.",
    "{hero} did not guess yet; careful problem solvers collect facts first.",
    "The clue waited while the jambalaya simmered and the lasagne browned.",
    "A quick rhyme helped {hero} remember: 'See it twice? Check it twice.'",
    "They left the clue untouched so they could compare it later.",
    "That odd detail made {hero} slow down and look again.",
    "The clue did not give the answer, but it promised one.",
    "{hero} asked {helper} to remember exactly where they had found it.",
    "They photographed the clue before moving anything nearby.",
)

REACTIONS = (
    "'Let's test that idea before we act,' said {hero}.",
    "{helper} nodded. 'A duplicate is a copy, but copies do not always have the same job.'",
    "'We have a guess, not an answer,' {hero} reminded everyone.",
    "They paused the serving line so a little confusion could not become a larger one.",
    "{hero} made two columns on the notepad: what matched and what differed.",
    "Instead of blaming anyone, {helper} asked, 'What can the clue prove?'",
    "They agreed to change nothing until they understood the duplicate.",
    "'Look, ask, compare,' {hero} chanted. 'That is how we'll repair.'",
    "The team took one calm breath and turned the mix-up into a question.",
    "{helper} moved both hot dishes to safe mats before the investigation began.",
    "They told the waiting guests there was a short puzzle to solve, not a disaster.",
)


def tell(params: StoryParams) -> World:
    kitchen = _safe_lookup(KITCHENS, params.place)
    case = _safe_lookup(CASES, params.case_id)
    mode = params.telling_mode if params.telling_mode in OPENINGS else TELLING_MODES[0]
    detail = params.detail_id
    world = World(kitchen)

    hero = world.add(Entity(id=params.hero_name, kind="character", label=params.hero_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", label=params.helper_name))
    first = world.add(Entity(id="dish_a", label="jambalaya", phrase="a pot of jambalaya"))
    second = world.add(Entity(id="dish_b", label="lasagne", phrase="a tray of lasagne"))

    world.facts.update(
        hero=hero,
        helper=helper,
        first=first,
        second=second,
        place=params.place,
        case=case,
        duplicate=case.duplicate,
        clue=case.clue,
        trouble=case.trouble,
        first_guess=case.first_guess,
        test=case.test,
        twist=case.twist,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
    )

    world.say(OPENINGS[mode].format(hero=hero.id, helper=helper.id))
    world.say(
        f"In {kitchen.place}, {hero.id} and {helper.id} were making spicy jambalaya and layered lasagne "
        "for a shared supper."
    )
    world.say(
        f"{case.setup}. It looked like {case.duplicate}. "
        f"The foreshadowing clue was plain once they looked closely: {case.clue}."
    )
    world.say(BRIDGES[detail % len(BRIDGES)].format(hero=hero.id, helper=helper.id))
    world.say(f"Soon the clue mattered because {case.trouble}.")
    world.say(f"At first, everyone guessed {case.first_guess}.")
    world.say(REACTIONS[(detail * 3 + 2) % len(REACTIONS)].format(hero=hero.id, helper=helper.id))
    world.say(
        f"To solve the problem, {hero.id} and {helper.id} decided to {case.test}. "
        "They compared the duplicate with the original instead of merely trusting the matching parts."
    )
    world.say(f"Then came the twist: {case.twist}.")
    world.say(
        f"That discovery changed their plan. Together they chose to {case.repair}. "
        f"'Copy found, problem unwound,' {hero.id} said, and {helper.id} answered, 'Check the clue, then follow through.'"
    )
    world.say(f"They learned that {case.lesson}.")
    world.say(
        f"At supper's end, {case.ending}. Jambalaya and lasagne reached the table correctly, "
        "and the solved duplicate had become part of the kitchen's story."
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    case: KitchenCase = world.facts["case"]  # type: ignore[assignment]
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    return [
        f"Write a child-friendly kitchen mystery in which {hero.id} helps prepare jambalaya and lasagne "
        f"and investigates {case.duplicate}.",
        f"Tell a rhyming supper tale that foreshadows trouble with this clue: {case.clue}. "
        "Include a fair test, a twist, and a concrete ending image.",
        f"Write a problem-solving story where a duplicate is narratively important because {case.trouble}. "
        "Let evidence reveal what the copy really means.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    case: KitchenCase = world.facts["case"]  # type: ignore[assignment]
    place: str = world.facts["place"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What duplicate did {hero.id} and {helper.id} investigate?",
            answer=f"They investigated {case.duplicate}. It mattered because {case.trouble}.",
        ),
        QAItem(
            question="What clue foreshadowed the kitchen problem?",
            answer=f"The foreshadowing clue was that {case.clue}. They remembered it when the trouble began.",
        ),
        QAItem(
            question="What did the cooks first believe?",
            answer=f"They first believed {case.first_guess}. They treated that as a guess and gathered evidence before acting.",
        ),
        QAItem(
            question="How did they test their idea?",
            answer=f"They tested it by choosing to {case.test}. That comparison revealed the duplicate's real role.",
        ),
        QAItem(
            question="What was the twist, and how did they repair the problem?",
            answer=f"The twist was that {case.twist}. Afterward, they chose to {case.repair}.",
        ),
        QAItem(
            question=f"Where did the final scene leave {hero.id}'s kitchen?",
            answer=f"The story ended in {_safe_lookup(KITCHENS, place).place}, where {case.ending}. The two foods reached the table correctly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is jambalaya?",
            answer="Jambalaya is a rice dish often cooked with spices and other tasty ingredients.",
        ),
        QAItem(
            question="What is lasagne?",
            answer="Lasagne is a baked pasta dish made in layers, often with sauce and cheese.",
        ),
        QAItem(
            question="What does a duplicate mean?",
            answer="A duplicate is an extra copy of something that looks very much like the original.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_place/1.
#show valid_story/1.

valid_place(P) :- kitchen(P).
valid_story(P) :- valid_place(P), has_jambalaya(P), has_lasagne(P), has_duplicate(P).

"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in KITCHENS:
        lines.append(asp.fact("kitchen", pid))
    lines.append(asp.fact("has_jambalaya", "sunny"))
    lines.append(asp.fact("has_lasagne", "sunny"))
    lines.append(asp.fact("has_duplicate", "sunny"))
    lines.append(asp.fact("has_jambalaya", "cozy"))
    lines.append(asp.fact("has_lasagne", "cozy"))
    lines.append(asp.fact("has_duplicate", "cozy"))
    lines.append(asp.fact("has_jambalaya", "busy"))
    lines.append(asp.fact("has_lasagne", "busy"))
    lines.append(asp.fact("has_duplicate", "busy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    asp_set = {p[0] for p in asp_valid_places()}
    py_set = set(KITCHENS)
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python registry ({len(py_set)} places).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme kitchen storyworld with jambalaya, lasagne, and a duplicate twist.")
    ap.add_argument("--place", choices=KITCHENS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: Optional[int] = None,
) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(KITCHENS))
    if not story_reasonable(place):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Mina", "Lulu", "Nico", "Toby", "Pip"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Mum", "Dad", "Nana", "Uncle Ben", "Aunt Joy"])
    index = sample_seed if sample_seed is not None else rng.randrange(2**31)
    case_id = tuple(CASES)[index % len(CASES)]
    telling_mode = TELLING_MODES[(index // len(CASES)) % len(TELLING_MODES)]
    detail_id = (index // (len(CASES) * len(TELLING_MODES))) % len(BRIDGES)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        helper_name=helper_name,
        case_id=case_id,
        telling_mode=telling_mode,
        detail_id=detail_id,
        seed=sample_seed,
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.kitchen.place}")
    for eid, ent in world.entities.items():
        lines.append(f"{eid}: kind={ent.kind} label={ent.label} meters={ent.meters} memes={ent.memes}")
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


CURATED = [
    StoryParams(
        place="sunny",
        hero_name="Mina",
        helper_name="Mum",
        case_id="copied_labels",
        telling_mode="clue_first",
        detail_id=0,
    ),
    StoryParams(
        place="cozy",
        hero_name="Pip",
        helper_name="Nana",
        case_id="twin_timers",
        telling_mode="dialogue_first",
        detail_id=3,
    ),
    StoryParams(
        place="busy",
        hero_name="Lulu",
        helper_name="Dad",
        case_id="lookalike_trays",
        telling_mode="rhyme_first",
        detail_id=7,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{p}" for p in sorted(asp_valid_places())))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed), seed)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
