#!/usr/bin/env python3
"""A rhyming friendship world that handles three awkward seed words kindly."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

WORDS = ("slob", "fatten", "helly")



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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    buddy: object | None = None
    hero: object | None = None
    snack: object | None = None
    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
class StoryParams:
    setting: str = "the little kitchen"
    hero: str = "Milo"
    buddy: str = "Helly"
    snack: str = "sticky buns"
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


SETTINGS = {
    "kitchen": "the little kitchen",
    "yard": "the sunny yard",
    "porch": "the bright porch",
}

HERO_NAMES = ["Milo", "Nina", "Pip", "Tara", "Jules"]
BUDDY_NAMES = ["Helly", "Henny", "Melly", "Lolly"]
SNACKS = ["sticky buns", "berry pie", "soft rolls", "honey cake"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming friendship story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--buddy", choices=BUDDY_NAMES)
    ap.add_argument("--snack", choices=SNACKS)
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
    setting_key = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    buddy = getattr(args, "buddy", None) or rng.choice(BUDDY_NAMES)
    if buddy == hero:
        buddy = rng.choice([b for b in BUDDY_NAMES if b != hero])
    snack = getattr(args, "snack", None) or rng.choice(SNACKS)
    return StoryParams(
        setting=_safe_lookup(SETTINGS, setting_key),
        hero=hero,
        buddy=buddy,
        snack=snack,
    )


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    w: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        return World(self.params, entities=_copy.deepcopy(self.entities), paragraphs=[[]], facts=dict(self.facts))
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


def _rhymes(a: str, b: str) -> bool:
    return a[-2:] == b[-2:]


@dataclass(frozen=True)
class Incident:
    name: str
    project: str
    fuller_target: str
    problem: str
    clue: str
    poor_idea: str
    hero_job: str
    buddy_job: str
    result: str
    ending_image: str


INCIDENTS = [
    Incident(
        "runaway rolls", "a picnic basket", "the basket's cloth cushion",
        "a loose basket latch sent the rolls tumbling under three chairs",
        "a crescent of flour pointed from the tray to the wobbly latch",
        "stack every roll on one plate and hope it stayed still",
        "gather the clean rolls with tongs", "mend the latch with ribbon",
        "the basket closed firmly and carried the rescued picnic",
        "three flour crescents shone beside the fastened blue bow",
    ),
    Incident(
        "leaning cake", "a cake-carrier", "the carrier's padded ring",
        "the honey cake leaned so far that its berry moon began to slide",
        "one side of the carrier had a flat patch beneath the plate",
        "hold the cake upright all afternoon with a wooden spoon",
        "steady the plate and trim a clean cardboard circle", "stuff the flat patch evenly",
        "the cake rode level while every berry stayed in its orbit",
        "the berry moon glowed through the carrier's round window",
    ),
    Incident(
        "porch puddle", "a dry-seat cushion", "the cushion's lumpy corner",
        "a tipped berry cup made a purple puddle creep toward the porch steps",
        "the cup had balanced on a napkin wrinkle instead of the table",
        "hide the puddle beneath the cushion before anyone noticed",
        "blot the spill from the center outward", "rinse the cloth and level the table",
        "the boards dried without a stain and the cup stood on a flat coaster",
        "a clean square of porch held one tiny purple sparkle",
    ),
    Incident(
        "buzzing tin", "a snack tin", "the tin's felt lining",
        "the snack tin buzzed and rattled whenever anyone took a step",
        "a lost spoon was trapped beneath its thin felt lining",
        "shake the tin harder until the mysterious noise surrendered",
        "lift the lining slowly and retrieve the spoon", "pad the bare corners with felt",
        "the tin traveled quietly except for one deliberate drumbeat",
        "the polished spoon rested on green felt like a silver canoe",
    ),
    Incident(
        "windy recipe", "a recipe-board pillow", "the board's little pillow",
        "a gust scattered the recipe cards across the sunny yard",
        "each card had a punched hole, and a spare cord lay by the tray",
        "chase every card alone while the wind kept changing direction",
        "sort the recovered cards by their painted numbers", "thread the cord through every hole",
        "the complete recipe hung in order and could turn without escaping",
        "the cards fluttered on their cord like a row of bright flags",
    ),
    Incident(
        "squeaky cart", "a serving cart", "the cart's bumper cushion",
        "the cart squeaked, swerved, and nudged a tower of empty cups",
        "a berry seed was wedged beside one front wheel",
        "push faster so the squeak would be left behind",
        "hold the cups and mark a safe stopping line", "remove the seed and test each wheel",
        "the cart rolled straight and stopped before the newly stacked cups",
        "four cups stood steady above a wheel clean as a button",
    ),
    Incident(
        "missing napkins", "a napkin pouch", "the pouch's soft divider",
        "the clean napkins vanished just before the neighbors arrived",
        "small square prints crossed the table and ended at a toy cupboard",
        "accuse the first person with crumbs on their sleeve",
        "follow the square prints and ask before opening doors", "check the toy picnic set",
        "they found the napkins serving a doll picnic and replaced them together",
        "real and toy napkins dried side by side on the little line",
    ),
    Incident(
        "jammed drawer", "a utensil drawer", "the drawer's cloth stop",
        "the utensil drawer stuck halfway open with the spoons out of reach",
        "a rolling pin handle peeked through the narrow gap at an angle",
        "yank the drawer until either it or the rolling pin gave up",
        "shine a lantern through the gap and guide the handle", "press the drawer sides evenly",
        "the rolling pin settled flat and the drawer glided shut",
        "the spoons lay in quiet rows beneath a lantern-shaped patch of light",
    ),
    Incident(
        "toppling sign", "a welcome sign", "the sign's weighted cloth base",
        "the welcome sign bowed whenever the kitchen door opened",
        "two empty pockets flapped at the back of its cloth base",
        "lean the sign against the snack tray and call the wobble decoration",
        "fill the pockets with smooth pebbles", "move the tray and test the doorway breeze",
        "the sign stood straight through three cheerful door swings",
        "its painted letters stayed upright above two hidden round stones",
    ),
    Incident(
        "echoing cupboard", "a cup cradle", "the cradle's quilted rim",
        "every closing cupboard made the cups answer with a nervous clatter",
        "tiny chalk marks showed where two cup handles touched",
        "wrap every cup in a napkin so nobody could use one",
        "space the cups by their handle marks", "sew a soft divider into the cradle",
        "the cupboard closed gently and the cups remained ready to share",
        "six handles curved apart like quiet question marks",
    ),
    Incident(
        "drooping banner", "a friendship banner", "the banner's padded center",
        "the friendship banner sagged and covered the punch-bowl label",
        "its center loop was stretched while both end loops remained snug",
        "cut off the drooping middle and make a very short banner",
        "measure a new center loop", "hold the banner level and tie the knot",
        "the whole message could be read above the uncovered bowl",
        "the final paper letter danced over a bright ladle",
    ),
    Incident(
        "crumb trail", "a bird-safe crumb box", "the box's mossy pad",
        "a trail of crumbs crossed the yard toward a busy anthill",
        "the box lid bore one fresh scrape where its clasp had missed",
        "sweep every crumb into the grass and forget where it went",
        "collect the crumbs without disturbing the ants", "realign the clasp and test the lid",
        "the path cleared and the sealed crumbs went to the proper bird table",
        "two sparrows perched above a clean path and a clicking brass clasp",
    ),
]


OPENINGS = [
    "Morning rang clear, and a small job drew near.",
    "Before the first bite, something would not sit right.",
    "A sunny-day plan began with a clatter from pan to pan.",
    "The table looked grand, till trouble made an unplanned stand.",
    "A snack-time cheer met one puzzle that would not disappear.",
    "They expected a treat, but first came a problem to meet.",
    "A quiet little chore soon knocked at the door.",
    "The room smelled sweet when a mystery rolled to their feet.",
    "Their friendly refrain was interrupted again.",
    "One ordinary tray started an extraordinary day.",
]

TURN_LINES = [
    "They paused their race and studied the place.",
    "Instead of a dash, they made a clue map from the mess and the crash.",
    "A joke broke the frown, but careful eyes tracked the trouble down.",
    "They counted to four, then looked once more.",
    "The quickest guess failed the test, so they chose the thoughtful best.",
    "They traded a grin and let patient noticing begin.",
    "One asked what changed; the other checked what had been rearranged.",
    "They stopped blaming fast and followed the evidence left from the past.",
    "They tried one small test before deciding the rest.",
    "Their rhyme became a plan: inspect, explain, and help where they can.",
]


def _incident_for(params: StoryParams) -> tuple[Incident, int]:
    seed = params.seed if params.seed is not None else 0
    return INCIDENTS[seed % len(INCIDENTS)], (seed // len(INCIDENTS)) % len(OPENINGS)


def tell(params: StoryParams) -> World:
    w = World(params=params)
    hero = w.add(Entity(id=params.hero, kind="character", label=params.hero, role="hero",
                        meters={"mess": 0.0, "hunger": 1.0, "joy": 1.0},
                        memes={"friendship": 0.0, "humor": 0.0, "helly": 0.0},
                        traits=["learning-to-tidy"]))
    buddy = w.add(Entity(id=params.buddy, kind="character", label=params.buddy, role="buddy",
                         meters={"care": 1.0},
                         memes={"friendship": 1.0, "humor": 1.0},
                         traits=["helly"]))
    snack = w.add(Entity(id="snack", kind="thing", label=params.snack, role="snack",
                         meters={"sweet": 1.0, "sticky": 1.0}))

    incident, telling_mode = _incident_for(params)
    place = w.params.setting
    w.say(OPENINGS[telling_mode])
    w.say(f"In {place}, {hero.label} and {buddy.label} were preparing {snack.label} when they found a torn cleanup label that read ‘slob.’")
    w.say(f"“That word judges a person,” said {buddy.label}. “Let’s name the problem, not a friend.”")
    w.say(f"{hero.label} nodded. “Crumbs can be swept, and nobody is a mess. That sounds kinder, I confess.”")

    w.para()
    w.say(f"Their task was {incident.project}, but {incident.problem}.")
    w.say(f"An old instruction said, “Fatten {incident.fuller_target}.” Here, fatten meant make an object fuller; it never described either friend.")
    w.say(f"{hero.label} spotted this clue: {incident.clue}.")
    hero.meters["mess"] += 1
    w.say(f"“Perhaps we should {incident.poor_idea},” {hero.label} joked.")
    w.say(f"“Funny, but no,” said {buddy.label}. “A shortcut that hides the cause gives tomorrow applause.”")

    w.para()
    w.say(TURN_LINES[telling_mode])
    w.say(f"“I’ll {incident.hero_job},” said {hero.label}. “You {incident.buddy_job}; two careful friends can set a muddle right.”")
    w.say(f"{buddy.label} grinned. “That is helly, our silly word for being eager to help. Side by side, we’ll finish before night.”")
    w.say(f"They checked each other’s work, changed course when needed, and {incident.result}.")
    hero.memes["friendship"] += 2
    buddy.memes["friendship"] += 2
    hero.memes["humor"] += 1
    buddy.memes["humor"] += 1
    hero.memes["helly"] += 1
    buddy.memes["helly"] += 1

    w.para()
    ending_leads = [
        "At last", "When the work was done", "As evening softened the light", "Before the final bite",
        "With the puzzle made plain", "After one final check", "When their shared rhyme fell still",
        "As the last laugh faded", "At the end of their plan", "Just as the first star appeared",
    ]
    w.say(f"{ending_leads[telling_mode]}, they shared the {snack.label} and cleaned the crumbs without naming anyone unkindly.")
    hero.meters["mess"] = max(0.0, hero.meters["mess"] - 1.0)
    hero.meters["joy"] += 1
    buddy.meters["care"] += 1
    w.say(f"“A friend tells the truth and then helps with the fix.” “And saves room for laughter!” They bumped spoons: click-click-click.")
    w.say(f"The lesson remained in one clear final sight: {incident.ending_image}.")

    w.facts.update(
        hero=hero,
        buddy=buddy,
        snack=snack,
        place=place,
        mess=True,
        rhyming=True,
        friendship=hero.memes["friendship"] >= 2,
        humor=hero.memes["humor"] >= 1,
        dialogue=True,
        helly=True,
        incident=incident.name,
        project=incident.project,
        problem=incident.problem,
        clue=incident.clue,
        hero_job=incident.hero_job,
        buddy_job=incident.buddy_job,
        result=incident.result,
        ending_image=incident.ending_image,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    buddy = _safe_fact(world, f, "buddy")
    snack = _safe_fact(world, f, "snack")
    return [
        f"Write a short rhyming story in which {hero.label} and {buddy.label} solve the {f['incident']} while preparing {snack.label}.",
        f"Tell a funny friendship story with dialogue where the clue is that {f['clue']}.",
        "Write a child-friendly tale using slob, fatten, and helly without insulting or body-shaming anyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    buddy = _safe_fact(world, f, "buddy")
    snack = _safe_fact(world, f, "snack")
    return [
        QAItem(
            question="Why did the friends object to the torn cleanup label?",
            answer=f"The label called someone a slob, and {hero.label} and {buddy.label} agreed to name the problem instead of judging a person.",
        ),
        QAItem(
            question=f"What clue helped {hero.label} and {buddy.label} solve the {f['incident']}?",
            answer=f"{hero.label} and {buddy.label} noticed that {f['clue']}, which pointed them toward the real cause of the problem.",
        ),
        QAItem(
            question=f"How did {hero.label} and {buddy.label} divide the work?",
            answer=f"{hero.label} worked to {f['hero_job']}, while {buddy.label} worked to {f['buddy_job']}.",
        ),
        QAItem(
            question=f"What proved that {hero.label} and {buddy.label}'s plan worked?",
            answer=f"Their plan for {f['project']} worked because {f['result']}. The final image showed that {f['ending_image']}.",
        ),
        QAItem(
            question=f"How did {hero.label} and {buddy.label} handle the unusual words while working on {f['project']}?",
            answer=f"{hero.label} and {buddy.label} used fatten only for making an object fuller and helly as a playful word for being eager to help. They rejected slob as an unkind label for a person.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be a friend?",
            answer="A friend is someone who is kind, shares, helps, and cares about you.",
        ),
        QAItem(
            question="Why can sticky snacks make a mess?",
            answer="Sticky snacks can leave crumbs or goo on hands and tables, so they often need cleaning up.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is something funny that makes people smile or laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={e.meters} memes={e.memes} traits={e.traits}")
    return "\n".join(out)


ASP_RULES = r"""
#show valid/1.
valid(kitchen).
valid(yard).
valid(porch).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", k) for k in SETTINGS]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    clingo_set = sorted(set(asp.atoms(model, "valid")))
    python_set = sorted((k,) for k in SETTINGS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches settings ({len(clingo_set)}).")
        return 0
    print("MISMATCH")
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
        print(format_qa(sample))


CURATED = [
    StoryParams(setting=SETTINGS["kitchen"], hero="Milo", buddy="Helly", snack="sticky buns"),
    StoryParams(setting=SETTINGS["yard"], hero="Nina", buddy="Melly", snack="berry pie"),
    StoryParams(setting=SETTINGS["porch"], hero="Pip", buddy="Lolly", snack="honey cake"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("3 valid settings:\n")
        for k in SETTINGS:
            print(f"  {k}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} and {p.buddy} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
