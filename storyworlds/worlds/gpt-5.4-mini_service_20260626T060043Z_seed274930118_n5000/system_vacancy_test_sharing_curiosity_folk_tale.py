#!/usr/bin/env python3
"""
A folk-tale storyworld about a village system, a vacancy, and a test of
curiosity, with sharing as the gentle resolution.

The seed premise:
- A small village has a well-ordered system for tending the lantern path.
- A helper role becomes vacant when the old lantern-keeper grows tired.
- A curious child wants to take the test for the vacancy.
- The child first learns to share tools and attention, then passes the test and
  joins the village system.

The story is generated from stateful simulation, not a frozen paragraph:
- physical meters track carried items, light, and readiness
- emotional memes track curiosity, worry, pride, and trust
- the ending proves what changed in the village system
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village green"
    affords: set[str] = field(default_factory=set)


@dataclass
class Trial:
    id: str
    verb: str
    gerund: str
    clue: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vacancy:
    id: str
    title: str
    tool: str
    tool_phrase: str
    shareable: str
    test_item: str
    reward: str
    threshold_kind: str = "readiness"


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    obstacle: str
    hasty_choice: str
    clue: str
    shared_item: str
    helper: str
    careful_action: str
    result: str
    system_change: str
    lesson: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter(e, key) + amt


def add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme(e, key) + amt


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in [e for e in world.entities.values() if e.kind == "character"]:
            if meme(actor, "curiosity") >= THRESHOLD and meme(actor, "worry") >= THRESHOLD:
                sig = ("focus", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    add_meme(actor, "focus", 1.0)
                    out.append(f"{actor.id} grew quiet and looked closely at the work.")
                    changed = True

            if meter(actor, "sharing") >= THRESHOLD and meme(actor, "trust") < THRESHOLD:
                sig = ("trust", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    add_meme(actor, "trust", 1.0)
                    out.append(f"That made the others trust {actor.id} more.")
                    changed = True

            if meter(actor, "ready") >= THRESHOLD and meme(actor, "focus") >= THRESHOLD:
                sig = ("pass", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    add_meme(actor, "pride", 1.0)
                    out.append(f"{actor.id} was ready for the test at last.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTING = Setting(
    place="the village green",
    affords={"listening", "sharing", "test"},
)

TRIALS = {
    "lantern_test": Trial(
        id="lantern_test",
        verb="take the lantern test",
        gerund="taking the lantern test",
        clue="a bright wick and a careful hand",
        risk="the flame could go out",
        weather="foggy",
        keyword="test",
        tags={"test", "light"},
    )
}

VACANCIES = {
    "lantern_keeper": Vacancy(
        id="lantern_keeper",
        title="lantern keeper",
        tool="lantern",
        tool_phrase="the old brass lantern",
        shareable="oil and matches",
        test_item="wick",
        reward="the key to the lamp shed",
    )
}

GIRL_NAMES = ["Mira", "Nela", "Tova", "Lina", "Sera", "Rin"]
BOY_NAMES = ["Ivo", "Pavel", "Borin", "Marek", "Tarin", "Jori"]
ADJ = ["curious", "kind", "patient", "brave", "gentle", "lively"]

SCENARIOS = [
    Scenario(
        "fog_markers",
        "Fog swallowed the white stones that marked the safest bends in the path.",
        "Three lanterns looked equally bright, yet one bend remained dark enough to hide the millstream.",
        "The child nearly chose the biggest flame and hurried on alone.",
        "A bead of water leaned away from the lantern whose air holes faced the wind.",
        "a dry matchbox and a strip of blue ribbon",
        "the miller's youngest child",
        "turned the air holes from the wind and tied the ribbon where every helper could see the safe bend",
        "the smallest flame burned steadily and the millstream crossing became visible",
        "blue guide ribbons were added to the evening lantern route",
        "a question can reveal what brightness alone conceals",
        "Along the millstream, blue ribbons fluttered beside twelve calm circles of light.",
    ),
    Scenario(
        "missing_oil",
        "On market night, the oil measure came back empty before half the lamps were filled.",
        "The final jar held too little oil for both the bridge lamp and the square lamp.",
        "The child first reached for the jar without asking who still needed it.",
        "A soot mark showed that the square's broad wick had been drinking twice its proper share.",
        "the measuring cup and the remaining lamp oil",
        "a patient baker",
        "trimmed the wasteful wick, measured equal portions, and invited two helpers to check the marks",
        "both lamps lasted until the market carts were safely home",
        "every oil jar received a marked sharing cup",
        "fair portions can make a small supply serve a whole village",
        "At midnight, one gold lamp shone over the bridge and another over the empty market baskets.",
    ),
    Scenario(
        "moth_glass",
        "A cloud of pale moths gathered when the orchard lanterns were lit.",
        "Their wings tapped the hot glass, and frightened children began waving branches at them.",
        "The child almost carried the lanterns closer to chase the moths away with brighter light.",
        "The moths settled whenever a lamp was shaded and a bowl of moonflowers stood nearby.",
        "a cool lantern shade and a basket of moonflowers",
        "the orchard keeper",
        "shared the flowers among the dark trees and fitted cool shades while everyone stood quietly",
        "the moths drifted to the blossoms and the path stayed safely lit",
        "orchard lamps were given cool shades and flower stations",
        "careful curiosity protects small lives instead of frightening them",
        "Moths rested on white petals while shaded lanterns glimmered beneath the apple trees.",
    ),
    Scenario(
        "bell_rope",
        "Just before dusk, the warning bell rang twice though nobody had pulled its rope.",
        "Villagers could not tell whether the west path was ready to open.",
        "The child wanted to declare the bell broken and begin the test elsewhere.",
        "Each gust made a loose rope-end brush the bronze rim with a tiny ting.",
        "a coil of cord and the good step stool",
        "a short shepherd",
        "held the stool steady for the shepherd, then used the shared cord to secure the loose rope",
        "the bell stayed silent until the proper opening signal was pulled",
        "bell ropes became part of the lantern keeper's afternoon check",
        "listening to a small sound can prevent a large confusion",
        "When the true bell rang, sheep and children crossed beneath a neat row of lights.",
    ),
    Scenario(
        "puddle_reflection",
        "After a storm, puddles copied every lantern and made the lane seem full of false lights.",
        "Travelers followed a reflection toward a muddy ditch instead of the hill road.",
        "The child first tried to stamp out each reflected flame with a boot.",
        "A dropped apple rolled past the false lights but cast a shadow beside every real post.",
        "chalk, a broom, and the driest cloak",
        "a rain-soaked apple seller",
        "shared the cloak, swept a narrow route, and chalked arrows beside posts that cast real shadows",
        "travelers could distinguish the hill road even while the puddles still gleamed",
        "real lantern posts were marked with bright arrows after rain",
        "testing an idea is wiser than fighting an appearance",
        "Behind the last cart, puddles held upside-down stars while the chalk arrows pointed home.",
    ),
    Scenario(
        "owl_signal",
        "An owl began hooting whenever the north lantern went dark.",
        "Some villagers feared the calls were an omen and refused to use the herb path.",
        "The child nearly rang every bell to scare the owl away.",
        "A loose shutter pinched the wick only when the owl landed on the lamp roof.",
        "a wooden peg and a handful of safe perch straw",
        "the herb gatherer",
        "shared the straw for a nearby perch and replaced the shutter peg without disturbing the nest",
        "the owl perched safely and the north lantern no longer winked out",
        "wildlife perches were placed away from the working lamps",
        "curiosity turns fearful guesses into kind solutions",
        "The owl watched from its straw perch as the herb path glowed silver-green below.",
    ),
    Scenario(
        "snow_tunnel",
        "The first snow banked against the low lanterns on the school lane.",
        "Clearing one lamp buried the next, and the children could not see where the path ended.",
        "The child began digging the widest tunnel without asking for help.",
        "A thin crust cracked in a straight line above the stones warmed by buried lanterns.",
        "two small shovels and a red wool scarf",
        "a pair of schoolchildren",
        "gave one shovel to the children, marked the warm stones with the scarf, and cleared short breathing wells",
        "the lamps shone through safe round openings all the way to the school door",
        "snow teams were paired so no lantern keeper dug alone",
        "shared work can be both quicker and safer than a grand solo effort",
        "Round lantern windows dotted the snow like warm buttons on a white coat.",
    ),
    Scenario(
        "festival_colors",
        "For the seed festival, families brought colored glass to dress the village lanterns.",
        "When every pane was fitted at once, the path turned too dim to read the stepping stones.",
        "The child wanted to remove all the decorations and disappoint the families.",
        "One clear pane cast enough light when it alternated with two colored panes.",
        "the clear panes and a box of colored glass",
        "three festival painters",
        "invited each painter to share a color, then arranged clear spaces between their designs",
        "the stepping stones stayed visible beneath a cheerful ribbon of color",
        "festival lanterns followed a shared clear-pane pattern",
        "a good system can make room for beauty and safety together",
        "Red, green, and clear squares danced across the stepping stones until the music ended.",
    ),
    Scenario(
        "lost_key",
        "At sunset, the lamp-shed key vanished from its peg.",
        "Without the spare wicks inside, the eastern lamps would fail before moonrise.",
        "The child suspected the last helper and almost accused him in the square.",
        "A trail of brass-colored scratches ended beneath the communal tool cart.",
        "a hand mirror and the last candle stub",
        "the helper who had been blamed",
        "apologized, shared the candle, and angled the mirror under the cart while the helper held it still",
        "they found the key caught beside a loose wheel and replaced every eastern wick",
        "the key gained a bright wooden tag and a signed return hook",
        "evidence and cooperation are better guides than suspicion",
        "The tagged key swung on its hook while the eastern lamps brightened one by one.",
    ),
    Scenario(
        "goat_gate",
        "A nimble goat learned to nose open the lamp-shed gate each afternoon.",
        "It scattered clean wicks through the grass and left muddy hoofprints near the oil jars.",
        "The child planned to tie the gate so tightly that smaller helpers could not enter.",
        "The goat ignored the latch whenever fresh clover waited beside its own pen.",
        "a basket of clover and a low wooden latch",
        "the smallest stable helper",
        "shared the clover, asked the helper to test the latch, and moved the tempting feed away from the shed",
        "the goat trotted to its pen while every helper could still open the safe latch",
        "shed latches were tested by the shortest member of each work team",
        "a solution should serve the smallest helper as well as stop the biggest nuisance",
        "The goat munched clover behind its gate as clean wicks dried in the sunset.",
    ),
    Scenario(
        "fireflies",
        "Hundreds of fireflies appeared beside the marsh path on the longest summer evening.",
        "Their moving sparks made it hard to tell which distant lights marked firm ground.",
        "The child proposed catching the fireflies in jars to make the test easier.",
        "The village lamps stayed at one height, while every living spark bobbed above the reeds.",
        "a measuring cord and two polished reflectors",
        "the marsh guide",
        "shared the cord, set the reflectors at a single low height, and left the fireflies free",
        "travelers followed the steady reflected line without stepping into the marsh",
        "marsh lamps received low reflectors that did not disturb wildlife",
        "patient observation can solve a problem without taking freedom away",
        "Fireflies rose over the reeds while a quiet silver line led the last traveler home.",
    ),
    Scenario(
        "clock_delay",
        "The tower clock began striking sunset several minutes too early.",
        "Helpers lit the lamps before the oil carts arrived and wasted a precious portion each day.",
        "The child thought the simplest answer was to ignore the clock forever.",
        "The clock lost exactly one beat whenever its stiff gear passed a patch of old dust.",
        "a soft brush and the little bottle of clock oil",
        "the apprentice clockmaker",
        "shared the brush, counted beats aloud with the apprentice, and oiled only the sticking pin",
        "the clock struck with the sunset and the carts reached every lamp on time",
        "the clock and lantern teams began comparing their records each week",
        "systems improve when neighbors share observations instead of guarding them",
        "The final chime floated over carts whose lantern jars shone full and amber.",
    ),
]

DIALOGUES = [
    "What changes when we look from down here?",
    "Could the trouble be showing us its own answer?",
    "Let us each tell what we noticed before we decide.",
    "What can we share so nobody has to guess alone?",
    "Suppose the loudest answer is not the truest one.",
    "May we test one small idea before changing everything?",
    "Who has seen this happen at another hour?",
    "What would make the path safe for the smallest traveler?",
]

REFLECTIONS = [
    "Curiosity is not merely wanting the answer; it is staying long enough to notice.",
    "A keeper must make light for others, not collect all the tools nearby.",
    "Passing a test should prove what a person will do when no prize is watching.",
    "A village system works because many careful hands can correct one another.",
    "Sharing attention can matter as much as sharing an object.",
    "The vacancy needed someone willing to revise a first idea.",
    "Useful questions leave room for another person's knowledge.",
    "Care is the part of cleverness that remembers who may be affected.",
    "The work belonged to the whole path, not to the person carrying the key.",
    "Wonder became wisdom only after it was shared.",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("village", "lantern_test", "lantern_keeper")]


@dataclass
class StoryParams:
    place: str
    trial: str
    vacancy: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale world about sharing, curiosity, and a vacant village role."
    )
    ap.add_argument("--place", choices=["village"])
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--vacancy", choices=VACANCIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
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
    trial = args.trial or "lantern_test"
    vacancy = args.vacancy or "lantern_keeper"
    if args.trial and args.trial not in TRIALS:
        raise StoryError("Unknown trial.")
    if args.vacancy and args.vacancy not in VACANCIES:
        raise StoryError("Unknown vacancy.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(ADJ)
    return StoryParams("village", trial, vacancy, name, gender, elder, trait)


def reasonableness_gate(params: StoryParams) -> None:
    if params.trial != "lantern_test" or params.vacancy != "lantern_keeper":
        raise StoryError("This tale only grows around the lantern test and the lantern-keeper vacancy.")


def tell(world: World, params: StoryParams) -> World:
    variant = params.seed if params.seed is not None else sum(
        (i + 1) * ord(ch)
        for i, ch in enumerate(
            f"{params.name}|{params.gender}|{params.elder}|{params.trait}"
        )
    )
    scenario = SCENARIOS[variant % len(SCENARIOS)]
    telling_mode = (variant // len(SCENARIOS)) % 8
    dialogue = DIALOGUES[(variant // (len(SCENARIOS) * 8)) % len(DIALOGUES)]
    reflection = REFLECTIONS[
        (variant // (len(SCENARIOS) * 8 * len(DIALOGUES))) % len(REFLECTIONS)
    ]

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    elder = world.add(Entity(id="Elder", kind="character", type=params.elder, label=params.elder))
    helper = world.add(Entity(id="Helper", kind="character", type="person", label=scenario.helper))
    vacancy = VACANCIES[params.vacancy]
    trial = TRIALS[params.trial]
    lantern = world.add(Entity(
        id="Lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase=vacancy.tool_phrase,
        owner=elder.id,
        caretaker=elder.id,
    ))

    add_meme(hero, "curiosity", 1.0)
    openings = [
        f"Long ago, the village green kept an evening system: each lantern helper checked one light and reported to the {vacancy.title}.",
        f"In an old village between hill and marsh, the path-lighting system was treated like a promise renewed every dusk.",
        f"Every evening, bells sent the village lantern team from the green to bridge, orchard, school, and marsh.",
        f"The village had no king of lamplight; it had a system in which neighbors checked and shared the work.",
        f"Grandparents said the path lamps were a necklace the whole village fastened together at sunset.",
        f"On the green stood a lamp shed, and inside it hung a chart showing how the village lighting system worked.",
        f"Before moonrise, the village always tested its lamps in pairs so no dark corner was forgotten.",
        f"This folk tale begins with a brass lantern, a careful village system, and one unanswered question.",
    ]
    world.say(openings[telling_mode])
    world.say(
        f"{hero.id}, a {params.trait} {params.gender}, followed the keepers because curiosity made ordinary details feel like clues."
    )
    world.say(
        f"The oldest keeper, {params.elder}, cared for {vacancy.tool_phrase} and taught that light belonged to everyone who used the path."
    )
    world.para()

    add_meme(hero, "desire", 1.0)
    world.say(
        f"When a vacancy opened for a new {vacancy.title}, {hero.id} asked to take the test."
    )
    world.say(
        f"Instead of reciting rules, {params.elder} made the evening's real trouble the test: {scenario.opening}"
    )
    add_meme(hero, "worry", 1.0)
    world.say(scenario.obstacle)
    world.say(scenario.hasty_choice)

    mode_turns = [
        f'Before acting, {hero.id} asked {scenario.helper}, "{dialogue}"',
        f'"{dialogue}" {hero.id} asked, kneeling where the smallest marks were easiest to see.',
        f"The other helpers argued until {hero.id} raised one hand and asked, \"{dialogue}\"",
        f"Remembering that a test reveals choices, {hero.id} stopped and said, \"{dialogue}\"",
        f"Rather than hide the first mistake, {hero.id} admitted it to {scenario.helper} and asked, \"{dialogue}\"",
        f"The elder offered no answer. After a thoughtful silence, {hero.id} asked, \"{dialogue}\"",
        f"A younger child tugged {hero.id}'s sleeve. That interruption prompted the question, \"{dialogue}\"",
        f"First {hero.id} drew the problem in the dust; then came the question, \"{dialogue}\"",
    ]
    world.say(mode_turns[telling_mode])

    world.para()
    add_meter(hero, "sharing", 1.0)
    add_meme(hero, "curiosity", 1.0)
    world.say(
        f"Together they noticed the decisive clue: {scenario.clue}"
    )
    world.say(
        f"For the next part of the test, {hero.id} practiced sharing {scenario.shared_item} with {scenario.helper}."
    )
    world.say(f"Then {hero.id} {scenario.careful_action}.")
    propagate(world)

    add_meter(hero, "ready", 1.0)
    world.say(f"The result proved the plan: {scenario.result}.")
    add_meter(lantern, "light", 1.0)
    add_meter(helper, "helped", 1.0)
    propagate(world)

    world.para()
    add_meme(hero, "pride", 1.0)
    add_meme(elder, "trust", 1.0)
    world.say(
        f"The elder awarded {hero.id} {vacancy.reward}, but asked what should change after one successful test."
    )
    world.say(f"The village lighting system adopted a new rule: {scenario.system_change}.")
    world.say(f"The lesson was plain: {scenario.lesson}. {reflection}")
    world.say(scenario.ending)

    world.facts.update(
        hero=hero,
        elder=elder,
        helper=helper,
        vacancy=vacancy,
        trial=trial,
        lantern=lantern,
        scenario=scenario,
        dialogue=dialogue,
        reflection=reflection,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    world = tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trial = f["trial"]
    vacancy = f["vacancy"]
    scenario = f["scenario"]
    return [
        f'Write a short folk tale for young children about a village system, a vacancy, and a curiosity test that includes the word "{trial.keyword}".',
        f"Tell a gentle story where {hero.id} wants to {trial.verb} for the {vacancy.title} vacancy, but learns to share first.",
        f"Write a simple village tale about {hero.id}, a lantern, and this problem: {scenario.obstacle}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    vacancy = f["vacancy"]
    trial = f["trial"]
    scenario = f["scenario"]
    return [
        QAItem(
            question=f"Who wanted to take the {trial.keyword} for the vacant village job?",
            answer=f"{hero.id}, a curious child in the village, wanted to take the test for the vacant {vacancy.title} job.",
        ),
        QAItem(
            question=f"What problem became {hero.id}'s test?",
            answer=f"The test was to solve this village problem: {scenario.obstacle}",
        ),
        QAItem(
            question=f"What clue changed {hero.id}'s first plan?",
            answer=f"{hero.id} noticed this clue: {scenario.clue} That evidence pointed toward a more careful plan.",
        ),
        QAItem(
            question=f"What did {hero.id} share during the test?",
            answer=f"{hero.id} shared {scenario.shared_item} with {scenario.helper}, so they could work on the problem together.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} {scenario.careful_action}. As a result, {scenario.result}.",
        ),
        QAItem(
            question="How did the village system improve afterward?",
            answer=f"After the test, the village adopted a new rule: {scenario.system_change}. The improvement preserved what everyone had learned.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn about curiosity and sharing?",
            answer=f"{hero.id} learned that {scenario.lesson}. Curiosity helped most when observations and tools were shared.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vacancy?",
            answer="A vacancy is an open place or job that no one is filling yet, so someone new may be chosen for it.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing helps because it lets everyone use what they need, and it can make people trust one another more.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions and learn how things work.",
        ),
        QAItem(
            question="Why do lanterns help people at night?",
            answer="Lanterns give light in the dark, so people can see the path more clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(village, lantern_test, lantern_keeper).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "village"),
        asp.fact("trial", "lantern_test"),
        asp.fact("vacancy", "lantern_keeper"),
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
        print(f"OK: ASP matches Python ({len(py)} combo).")
        return 0
    print("MISMATCH")
    return 1


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


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
    StoryParams("village", "lantern_test", "lantern_keeper", "Mira", "girl", "grandmother", "curious"),
    StoryParams("village", "lantern_test", "lantern_keeper", "Ivo", "boy", "grandfather", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.trial} / {p.vacancy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
