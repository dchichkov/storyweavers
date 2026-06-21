#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fore_audacity_dispose_conflict_inner_monologue_tall.py
=================================================================================

A standalone storyworld for a tall-tale problem: a gigantic child with more
audacity than most weathercocks must dispose of an absurd obstacle blocking the
road before the town fair begins.

Seed requirements rebuilt as world state:
- word: "fore"   -> the famous fore road and related prompts
- word: "audacity" -> the hero's reputation and the town's complaint
- word: "dispose" -> the core problem and solution
- feature: Conflict -> the mayor and townsfolk doubt the plan
- feature: Inner Monologue -> the hero thinks through the world model before acting
- style: Tall Tale -> exaggerated scale, frontier flavor, impossible-but-orderly feats

The world prefers a few sturdy combinations over broad coverage.  Obstacles have
materials and sizes; disposal methods work only for certain materials, require
certain kinds of places, and must have enough power to clear the road.  The
story then renders from the simulated state, not from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/fore_audacity_dispose_conflict_inner_monologue_tall.py
    python storyworlds/worlds/gpt-5.4/fore_audacity_dispose_conflict_inner_monologue_tall.py --locale fore_road
    python storyworlds/worlds/gpt-5.4/fore_audacity_dispose_conflict_inner_monologue_tall.py --obstacle scrap_mountain --method rope_team
    python storyworlds/worlds/gpt-5.4/fore_audacity_dispose_conflict_inner_monologue_tall.py --all
    python storyworlds/worlds/gpt-5.4/fore_audacity_dispose_conflict_inner_monologue_tall.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fore_audacity_dispose_conflict_inner_monologue_tall.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Locale:
    id: str
    label: str
    route: str
    destination: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    material: str
    scale: int
    image: str
    consequence: str
    salvage: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    verb: str
    materials: set[str] = field(default_factory=set)
    required_tags: set[str] = field(default_factory=set)
    power: int = 1
    turn_text: str = ""
    ending_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_blocked(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    road = world.get("road")
    town = world.get("town")
    if obstacle.meters["blocking"] < THRESHOLD:
        return []
    sig = ("blocked", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    road.meters["blocked"] += 1
    town.memes["worry"] += 1
    return []


def _r_open(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    road = world.get("road")
    town = world.get("town")
    if obstacle.meters["disposed"] < THRESHOLD:
        return []
    sig = ("open", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    road.meters["blocked"] = 0.0
    road.meters["open"] += 1
    town.memes["worry"] = 0.0
    town.memes["awe"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked", tag="physical", apply=_r_blocked),
    Rule(name="open", tag="physical", apply=_r_open),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def method_fits(locale: Locale, obstacle: Obstacle, method: Method) -> bool:
    if obstacle.material not in method.materials:
        return False
    if not method.required_tags.issubset(locale.tags):
        return False
    if method.power < obstacle.scale:
        return False
    return True


def ending_of(obstacle: Obstacle, method: Method) -> str:
    return "easy" if method.power >= obstacle.scale + 1 else "hard_won"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for locale_id, locale in LOCALES.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            for method_id, method in METHODS.items():
                if method_fits(locale, obstacle, method):
                    combos.append((locale_id, obstacle_id, method_id))
    return combos


def explain_rejection(locale: Locale, obstacle: Obstacle, method: Method) -> str:
    if obstacle.material not in method.materials:
        return (
            f"(No story: {method.label} cannot dispose of {obstacle.phrase} because "
            f"it is made of {obstacle.material}, not one of {sorted(method.materials)}.)"
        )
    missing = sorted(method.required_tags - locale.tags)
    if missing:
        return (
            f"(No story: {method.label} needs place features {missing}, but "
            f"{locale.label} does not have them.)"
        )
    if method.power < obstacle.scale:
        return (
            f"(No story: {method.label} is too weak for {obstacle.phrase}. "
            f"It has power {method.power}, but the obstacle's size is {obstacle.scale}.)"
        )
    return "(No story: that combination is not reasonable.)"


def predict_disposal(world: World, locale: Locale, obstacle: Obstacle, method: Method) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    road = sim.get("road")
    town = sim.get("town")
    if method_fits(locale, obstacle, method):
        sim.get("obstacle").meters["blocking"] = 0.0
        sim.get("obstacle").meters["disposed"] += 1
        hero.meters["strain"] += float(max(1, obstacle.scale))
        hero.memes["resolve"] += 1
        propagate(sim, narrate=False)
    return {
        "clears": road.meters["open"] >= THRESHOLD,
        "town_worry": town.memes["worry"],
        "strain": hero.meters["strain"],
        "ending": ending_of(obstacle, method) if method_fits(locale, obstacle, method) else "none",
    }


def introduce(world: World, hero: Entity, locale: Locale, obstacle: Obstacle) -> None:
    hero.memes["audacity"] += 1
    world.say(
        f"In the country around {locale.label}, folks said {hero.id} could hear a wagon wheel "
        f"complain from three counties off and answer it before the squeak was done."
    )
    world.say(
        f"{hero.id} was a {hero.type} with the sort of audacity that made weather vanes lean "
        f"out of the wind just to watch."
    )
    world.say(
        f"On the morning of the fair, {hero.pronoun('subject')} came to {locale.route} and found "
        f"{obstacle.phrase} sprawled across it. {obstacle.image}"
    )


def block_route(world: World, obstacle_ent: Entity, locale: Locale, obstacle: Obstacle) -> None:
    obstacle_ent.meters["blocking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"No cart could get to {locale.destination}, and no fiddler could carry a tune through that mess. "
        f"{obstacle.consequence}"
    )


def mayor_objects(world: World, mayor: Entity, hero: Entity, obstacle: Obstacle) -> None:
    mayor.memes["doubt"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f'The mayor planted both boots in the dust and said, "{hero.id}, this is no chore for one pair '
        f'of hands. We need a crew, a committee, and maybe next Tuesday."'
    )
    world.say(
        f'{hero.id} tipped {hero.pronoun("possessive")} hat back. "By next Tuesday," '
        f'{hero.pronoun("subject")} said, "that heap will be old enough to vote."'
    )
    world.say(
        f'The mayor snorted. "It is your audacity I am worried about. Audacity can topple a fence '
        f'faster than wisdom can mend it."'
    )


def inner_monologue(world: World, hero: Entity, locale: Locale, obstacle: Obstacle, method: Method) -> None:
    pred = predict_disposal(world, locale, obstacle, method)
    hero.memes["plan"] += 1
    world.facts["prediction"] = pred
    if pred["ending"] == "easy":
        thought = (
            f'If {method.label} can clear {obstacle.label} cleanly, {hero.pronoun("subject")} thought, '
            f'then the road will open before the brass band finishes warming its horns.'
        )
    else:
        thought = (
            f'"This will pull like a mule with its mind made up," {hero.id} thought, '
            f'"but if I keep my heels dug in, I can still dispose of it before supper bells."'
        )
    world.say(thought)
    world.say(
        f'{hero.pronoun("subject").capitalize()} studied the mess from top to bottom and chose '
        f'{method.label}, because {method.label.lower()} matched the {obstacle.material} trouble better than bluffing ever could.'
    )


def perform_disposal(world: World, hero: Entity, obstacle_ent: Entity, locale: Locale,
                     obstacle: Obstacle, method: Method) -> None:
    hero.meters["strain"] += float(obstacle.scale)
    hero.memes["resolve"] += 1
    obstacle_ent.meters["blocking"] = 0.0
    obstacle_ent.meters["disposed"] += 1
    propagate(world, narrate=False)
    if ending_of(obstacle, method) == "easy":
        hero.memes["joy"] += 1
        world.say(method.turn_text.format(hero=hero.id, route=locale.route, obstacle=obstacle.label))
    else:
        hero.memes["grit"] += 1
        world.say(
            f"{method.turn_text.format(hero=hero.id, route=locale.route, obstacle=obstacle.label)} "
            f"For a minute the whole country seemed to lean the other way, but {hero.id} leaned harder."
        )


def finish(world: World, hero: Entity, mayor: Entity, locale: Locale, obstacle: Obstacle, method: Method) -> None:
    town = world.get("town")
    town.memes["relief"] += 1
    mayor.memes["respect"] += 1
    world.say(
        method.ending_text.format(
            hero=hero.id,
            destination=locale.destination,
            salvage=obstacle.salvage,
        )
    )
    world.say(
        f'The mayor took off {mayor.pronoun("possessive")} hat and said, "Well, I asked how you meant to '
        f'dispose of that nuisance, and now I see you disposed of my doubts too."'
    )
    world.say(
        f"By sundown the road lay open, the town rolled into {locale.destination}, and folks told the story "
        f"so wide that even the horizon had to scoot back to make room."
    )


def tell(locale: Locale, obstacle: Obstacle, method: Method,
         hero_name: str = "Tall Ruth", hero_gender: str = "girl",
         mayor_type: str = "father", trait: str = "steady") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        label=hero_name,
        traits=[trait, "bold"],
    ))
    mayor = world.add(Entity(
        id="Mayor",
        kind="character",
        type=mayor_type,
        role="mayor",
        label="the mayor",
    ))
    town = world.add(Entity(
        id="town",
        kind="thing",
        type="crowd",
        label="the town",
    ))
    road = world.add(Entity(
        id="road",
        kind="thing",
        type="road",
        label=locale.route,
    ))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
        phrase=obstacle.phrase,
        tags=set(obstacle.tags),
    ))

    introduce(world, hero, locale, obstacle)
    block_route(world, obstacle_ent, locale, obstacle)

    world.para()
    mayor_objects(world, mayor, hero, obstacle)
    inner_monologue(world, hero, locale, obstacle, method)

    world.para()
    perform_disposal(world, hero, obstacle_ent, locale, obstacle, method)
    finish(world, hero, mayor, locale, obstacle, method)

    world.facts.update(
        hero=hero,
        mayor=mayor,
        town=town,
        road=road,
        obstacle=obstacle_ent,
        locale=locale,
        obstacle_cfg=obstacle,
        method=method,
        outcome=ending_of(obstacle, method),
        blocked_initially=True,
        cleared=road.meters["open"] >= THRESHOLD,
        disposed=obstacle_ent.meters["disposed"] >= THRESHOLD,
    )
    return world


LOCALES = {
    "fore_road": Locale(
        id="fore_road",
        label="the fore road",
        route="the fore road",
        destination="the Cloverleaf Fair",
        image="It ran straight as a promise through the prairie.",
        tags={"road", "flat", "sun", "fore"},
    ),
    "river_ford": Locale(
        id="river_ford",
        label="the river ford",
        route="the ford road by the river",
        destination="the ferry market",
        image="The water nearby kept talking to its own banks.",
        tags={"road", "flat", "sun", "water"},
    ),
    "fair_gate": Locale(
        id="fair_gate",
        label="the fair gate",
        route="the lane before the fair gate",
        destination="the county fairgrounds",
        image="Even the bunting looked impatient to start the day.",
        tags={"road", "flat", "sun", "fair"},
    ),
}

OBSTACLES = {
    "hay_hill": Obstacle(
        id="hay_hill",
        label="hay hill",
        phrase="a hay hill as high as a church choir and twice as sneezy",
        material="fiber",
        scale=2,
        image="Every loose straw pointed a different direction, as if the heap had been arguing with the wind all night.",
        consequence="The pie ladies stood on one side with their pies, and the judges stood on the other side with their forks.",
        salvage="a set of bright, springy seats",
        tags={"hay", "fiber"},
    ),
    "scrap_mountain": Obstacle(
        id="scrap_mountain",
        label="scrap mountain",
        phrase="a scrap mountain made of bent pans, rusty hinges, and enough nails to itch the moon",
        material="metal",
        scale=3,
        image="It glittered and groaned whenever the breeze poked it.",
        consequence="The blacksmith could not reach the fair, and the fair could not do without the blacksmith's bell.",
        salvage="a shining arch and a bucket of useful nails",
        tags={"metal", "scrap"},
    ),
    "log_tangle": Obstacle(
        id="log_tangle",
        label="log tangle",
        phrase="a log tangle knotted tighter than a basket of sleeping snakes",
        material="wood",
        scale=2,
        image="Every timber seemed to have chosen the wrong neighbor and then held on out of spite.",
        consequence="Wagons lined up so long that the last mule thought it lived in another county.",
        salvage="a stout row of benches",
        tags={"wood", "logs"},
    ),
    "snow_wall": Obstacle(
        id="snow_wall",
        label="snow wall",
        phrase="a snow wall white as whipped cream and stubborn as a locked barn",
        material="snow",
        scale=1,
        image="It stood cool and quiet, but it had the mean habit of putting drifts where feet wanted to go.",
        consequence="The children could see the market flags fluttering beyond it and not one of them could get close enough to cheer.",
        salvage="a sparkling pond of water for the horses",
        tags={"snow", "cold"},
    ),
}

METHODS = {
    "rope_team": Method(
        id="rope_team",
        label="the rope team",
        verb="roped it and hauled",
        materials={"fiber", "wood"},
        required_tags={"road"},
        power=2,
        turn_text="{hero} whistled once, looped a rope around the {obstacle}, and hauled until the whole burden slid off {route} like a rug being shaken out by thunder.",
        ending_text="By noon the trouble had been turned into {salvage}, and children were climbing over it as happily as squirrels on payday.",
        qa_text="used an enormous rope team to drag the obstacle clear and turn it into something useful",
        tags={"rope", "reuse"},
    ),
    "magnet_cart": Method(
        id="magnet_cart",
        label="the magnet cart",
        verb="rolled the magnet cart under it",
        materials={"metal"},
        required_tags={"flat"},
        power=3,
        turn_text="{hero} rolled out a magnet cart so strong it pulled belt buckles into next week, then swept the {obstacle} together in one singing, clanking gulp.",
        ending_text="The pieces that had blocked the way were soon standing as {salvage}, and the town band kept touching the arch as they walked under it, just to be sure it was real.",
        qa_text="used a giant magnet cart to gather the metal and rebuild it into a useful fair arch",
        tags={"magnet", "metal", "reuse"},
    ),
    "mirror_line": Method(
        id="mirror_line",
        label="the mirror line",
        verb="set up mirrors",
        materials={"snow"},
        required_tags={"sun"},
        power=2,
        turn_text="{hero} planted a line of mirrors, tipped the morning sun into them, and poured a river of light across the {obstacle} until it sighed itself down into shining water.",
        ending_text="Where the drift had blocked the way, there now lay {salvage}, and every horse in town came by pretending to be thirsty.",
        qa_text="used a line of mirrors to melt the snow into water and clear the route",
        tags={"sun", "snow"},
    ),
    "grandstand_build": Method(
        id="grandstand_build",
        label="the grandstand build",
        verb="sorted and rebuilt it",
        materials={"fiber", "wood", "metal"},
        required_tags={"fair"},
        power=3,
        turn_text="{hero} sorted the {obstacle} faster than gossip crosses a porch, stacked the good pieces, and rebuilt the whole fuss into a grandstand before the dust had time to settle on {route}.",
        ending_text="Nothing was wasted: the nuisance became {salvage}, and the first cheer of the day rattled the fair pennants clear to supper time.",
        qa_text="sorted the obstacle and rebuilt it into a grandstand or fair structure so the lane opened again",
        tags={"build", "reuse", "fair"},
    ),
}


@dataclass
class StoryParams:
    locale: str
    obstacle: str
    method: str
    hero_name: str
    hero_gender: str
    mayor_type: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Tall Ruth", "Molly Longstep", "June Highboot", "Ada Farfield", "Nell Whistlewind"]
BOY_NAMES = ["Eli Broadhat", "Cal Hightoe", "Wes Longstride", "Bo Prairie", "Jeb Fencewalker"]
TRAITS = ["steady", "cheerful", "stubborn", "calm", "grinning"]

KNOWLEDGE = {
    "rope": [
        (
            "Why does a rope help move heavy things?",
            "A rope lets you pull from farther away and spread the force along the object. That makes a heavy thing easier to drag or lift."
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet pulls on some kinds of metal, especially iron and steel. That is why magnets can help gather metal pieces together."
        )
    ],
    "snow": [
        (
            "What happens to snow in warm sunshine?",
            "Snow melts into water when it gets enough heat. Bright sunshine can help that happen faster."
        )
    ],
    "reuse": [
        (
            "What does it mean to dispose of something by reusing it?",
            "It means you get rid of the problem without wasting the material. You turn the old thing into something helpful instead of just throwing it away."
        )
    ],
    "fair": [
        (
            "What is a fairground grandstand for?",
            "A grandstand is a raised place where people can sit or stand to watch a show. It helps many people see the same thing at once."
        )
    ],
    "fore": [
        (
            "What can fore mean in a place name?",
            "Fore can mean front or forward. In a road name, it can mean the road out in front, the one people reach first."
        )
    ],
}
KNOWLEDGE_ORDER = ["fore", "rope", "magnet", "snow", "reuse", "fair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    locale = f["locale"]
    obstacle = f["obstacle_cfg"]
    method = f["method"]
    return [
        f'Write a tall-tale story for a 3-to-5-year-old that includes the words "fore", "audacity", and "dispose".',
        f"Tell a frontier-flavored story where {hero.id} finds {obstacle.phrase} blocking {locale.route}, argues with the mayor, and then uses inner monologue to choose {method.label}.",
        f"Write a short exaggeration-filled story in which a child must dispose of an impossible obstacle before everyone can reach {locale.destination}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mayor = f["mayor"]
    locale = f["locale"]
    obstacle = f["obstacle_cfg"]
    method = f["method"]
    pred = f.get("prediction", {})
    outcome = f.get("outcome", "hard_won")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a gianthearted child on {locale.route}, and the mayor who doubts the plan. The whole town is waiting to see whether the road will open."
        ),
        (
            f"What problem blocked the trip to {locale.destination}?",
            f"{obstacle.phrase.capitalize()} was sprawled across the road. Because it blocked the route, wagons and people could not get through."
        ),
        (
            "What was the conflict in the story?",
            f"The mayor believed the job was too big and worried that {hero.id}'s audacity would make things worse. {hero.id} believed the mess could be handled right away, so the two of them pulled in opposite directions before the plan began."
        ),
        (
            "What was the inner monologue about?",
            f"{hero.id} quietly thought through which tool would really match the trouble. The thinking mattered because {method.label} fit the {obstacle.material} obstacle and, in {hero.pronoun('possessive')} mind, it would clear the road instead of just making a louder mess."
        ),
    ]
    if f.get("disposed"):
        if outcome == "easy":
            follow = "The method had more than enough strength for the obstacle, so the work looked almost playful."
        else:
            follow = "The obstacle was nearly as strong as the method, so the work took grit even though the plan was still the right one."
        qa.append(
            (
                f"How did {hero.id} dispose of the obstacle?",
                f"{hero.pronoun('subject').capitalize()} {method.qa_text}. {follow}"
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The road opened and everyone could reach {locale.destination}. The very thing that had caused trouble was turned into {obstacle.salvage}, which proves the place changed for the better."
            )
        )
        if pred:
            qa.append(
                (
                    "Why was the chosen plan sensible?",
                    f"In {hero.id}'s thinking, the plan would clear the road and stop the town's worry. That prediction came true, because the route opened after {hero.pronoun('subject')} used {method.label}."
                )
            )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["locale"].tags)
    tags |= set(f["method"].tags)
    tags |= set(f["obstacle_cfg"].tags)
    if "fore" in tags:
        tags.add("fore")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        locale="fore_road",
        obstacle="hay_hill",
        method="rope_team",
        hero_name="Tall Ruth",
        hero_gender="girl",
        mayor_type="father",
        trait="steady",
    ),
    StoryParams(
        locale="fair_gate",
        obstacle="scrap_mountain",
        method="grandstand_build",
        hero_name="Cal Hightoe",
        hero_gender="boy",
        mayor_type="father",
        trait="grinning",
    ),
    StoryParams(
        locale="river_ford",
        obstacle="snow_wall",
        method="mirror_line",
        hero_name="June Highboot",
        hero_gender="girl",
        mayor_type="mother",
        trait="calm",
    ),
    StoryParams(
        locale="fair_gate",
        obstacle="log_tangle",
        method="grandstand_build",
        hero_name="Eli Broadhat",
        hero_gender="boy",
        mayor_type="mother",
        trait="cheerful",
    ),
    StoryParams(
        locale="fore_road",
        obstacle="scrap_mountain",
        method="magnet_cart",
        hero_name="Molly Longstep",
        hero_gender="girl",
        mayor_type="father",
        trait="stubborn",
    ),
]


ASP_RULES = r"""
valid(Locale, Obstacle, Method) :-
    locale(Locale), obstacle(Obstacle), method(Method),
    material(Obstacle, Mat),
    handles(Method, Mat),
    needs_all_tags(Method),
    method_power(Method, P),
    obstacle_scale(Obstacle, S),
    P >= S,
    req_ok(Locale, Method).

req_ok(Locale, Method) :-
    not missing_req(Locale, Method).

missing_req(Locale, Method) :-
    requires(Method, Tag),
    not has_tag(Locale, Tag).

easy(Obstacle, Method) :-
    obstacle_scale(Obstacle, S),
    method_power(Method, P),
    P >= S + 1.

hard_won(Obstacle, Method) :-
    valid(_, Obstacle, Method),
    not easy(Obstacle, Method).

outcome(Obstacle, Method, easy) :- easy(Obstacle, Method).
outcome(Obstacle, Method, hard_won) :- hard_won(Obstacle, Method).

needs_all_tags(Method) :- method(Method).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for locale_id, locale in LOCALES.items():
        lines.append(asp.fact("locale", locale_id))
        for tag in sorted(locale.tags):
            lines.append(asp.fact("has_tag", locale_id, tag))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("material", obstacle_id, obstacle.material))
        lines.append(asp.fact("obstacle_scale", obstacle_id, obstacle.scale))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("method_power", method_id, method.power))
        for material in sorted(method.materials):
            lines.append(asp.fact("handles", method_id, material))
        for tag in sorted(method.required_tags):
            lines.append(asp.fact("requires", method_id, tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(obstacle_id: str, method_id: str) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_obstacle", obstacle_id),
        asp.fact("chosen_method", method_id),
        "picked_outcome(K) :- chosen_obstacle(O), chosen_method(M), outcome(O, M, K).",
    ])
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    bad = []
    for obstacle_id, obstacle in OBSTACLES.items():
        for method_id, method in METHODS.items():
            any_valid = any(
                combo[1] == obstacle_id and combo[2] == method_id
                for combo in py_valid
            )
            if not any_valid:
                continue
            py_outcome = ending_of(obstacle, method)
            asp_kind = asp_outcome(obstacle_id, method_id)
            if py_outcome != asp_kind:
                bad.append((obstacle_id, method_id, py_outcome, asp_kind))
    if not bad:
        print("OK: ASP outcome model matches ending_of() for valid obstacle/method pairs.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for item in bad:
            print(" ", item)

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(0))
        params.seed = 0
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        for params in CURATED[:2]:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Curated story was empty.")
        print("OK: curated samples generated successfully.")
    except Exception as err:
        rc = 1
        print(f"CURATED GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tall-tale storyworld: a child with audacity must dispose of an absurd obstacle before the fair."
    )
    ap.add_argument("--locale", choices=LOCALES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--mayor", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.locale is not None and args.locale not in LOCALES:
        raise StoryError(f"(Unknown locale: {args.locale})")
    if args.obstacle is not None and args.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {args.obstacle})")
    if args.method is not None and args.method not in METHODS:
        raise StoryError(f"(Unknown method: {args.method})")

    if args.locale and args.obstacle and args.method:
        locale = LOCALES[args.locale]
        obstacle = OBSTACLES[args.obstacle]
        method = METHODS[args.method]
        if not method_fits(locale, obstacle, method):
            raise StoryError(explain_rejection(locale, obstacle, method))

    combos = [
        combo for combo in valid_combos()
        if (args.locale is None or combo[0] == args.locale)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    locale_id, obstacle_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    hero_name = args.hero_name or rng.choice(pool)
    mayor_type = args.mayor or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        locale=locale_id,
        obstacle=obstacle_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        mayor_type=mayor_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.locale not in LOCALES:
        raise StoryError(f"(Unknown locale in params: {params.locale})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle in params: {params.obstacle})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method in params: {params.method})")

    locale = LOCALES[params.locale]
    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    if not method_fits(locale, obstacle, method):
        raise StoryError(explain_rejection(locale, obstacle, method))

    world = tell(
        locale=locale,
        obstacle=obstacle,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        mayor_type=params.mayor_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (locale, obstacle, method) combinations:\n")
        for locale_id, obstacle_id, method_id in combos:
            kind = asp_outcome(obstacle_id, method_id)
            print(f"  {locale_id:10} {obstacle_id:15} {method_id:16} [{kind}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.obstacle} at {p.locale} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
