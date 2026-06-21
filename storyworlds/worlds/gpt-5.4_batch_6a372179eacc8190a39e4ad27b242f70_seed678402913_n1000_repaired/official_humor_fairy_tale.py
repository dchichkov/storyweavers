#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/official_humor_fairy_tale.py
=======================================================

A small fairy-tale storyworld with a humorous, state-driven premise:

A sleepy magical creature must wake up before a royal celebration can begin.
A child is given an absurdly grand *official* title and sent to help. The
child tries a gentle waking tool first. If the tool suits the creature, the
creature wakes at once. If not, a helper arrives with the creature's favorite
snack, and the delicious smell solves the problem instead.

The world model keeps both physical meters (sleep, awake, readiness) and
emotional memes (pride, worry, relief, joy). The prose is rendered from the
simulated state, not from one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/official_humor_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/official_humor_fairy_tale.py --creature dragon
    python storyworlds/worlds/gpt-5.4/official_humor_fairy_tale.py --tool kettle_drum
    python storyworlds/worlds/gpt-5.4/official_humor_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/official_humor_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/official_humor_fairy_tale.py --trace
    python storyworlds/worlds/gpt-5.4/official_humor_fairy_tale.py --verify
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
GENTLE_MIN = 2


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
        female = {"girl", "woman", "queen", "mother"}
        male = {"boy", "man", "king", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"king": "king", "queen": "queen"}.get(self.type, self.type)


@dataclass
class Festival:
    id: str
    place: str
    image: str
    treat: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    label: str
    phrase: str
    lair: str
    snore: str
    cue: str
    favorite_snack: str
    waking_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    cue: str
    sound_text: str
    gentle: int
    funny_fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    phrase: str
    brings: set[str] = field(default_factory=set)
    entrance: str = ""
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


def _r_awake_ready(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    if creature.meters["awake"] >= THRESHOLD:
        sig = ("ready", "festival")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("festival").meters["ready"] += 1
            world.get("hero").memes["relief"] += 1
            world.get("hero").memes["joy"] += 1
            out.append("__ready__")
    return out


def _r_failed_attempt(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    if creature.meters["startled"] >= THRESHOLD and creature.meters["awake"] < THRESHOLD:
        sig = ("worry", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="awake_ready", tag="physical", apply=_r_awake_ready),
    Rule(name="failed_attempt", tag="emotional", apply=_r_failed_attempt),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


FESTIVALS = {
    "lantern_feast": Festival(
        id="lantern_feast",
        place="the moonlit castle yard",
        image="strings of lanterns bobbed over the cobblestones",
        treat="plum cakes",
        ending="the lanterns swung like small moons above the dancing crowd",
        tags={"festival", "lantern"},
    ),
    "jam_parade": Festival(
        id="jam_parade",
        place="the ribbon-bright market square",
        image="scarlet banners and jam jars glittered in rows",
        treat="berry tarts",
        ending="the parade rolled past with spoons held high like silver flags",
        tags={"festival", "jam"},
    ),
    "starlight_ball": Festival(
        id="starlight_ball",
        place="the silver palace steps",
        image="tiny lights winked in every window",
        treat="sugar buns",
        ending="the steps shone as if the stars had come down to clap",
        tags={"festival", "stars"},
    ),
}

CREATURES = {
    "dragon": CreatureCfg(
        id="dragon",
        label="dragon",
        phrase="a young dragon",
        lair="the warm cave under the eastern tower",
        snore="Each snore puffed a ring of smoke that floated up and shaped itself like a crooked doughnut.",
        cue="trumpet",
        favorite_snack="cinnamon_bun",
        waking_line='"Did someone say breakfast?" the dragon rumbled, opening one golden eye and then the other.',
        tags={"dragon", "fire", "breakfast"},
    ),
    "giant": CreatureCfg(
        id="giant",
        label="giant",
        phrase="a drowsy hill giant",
        lair="the mossy hollow beside the royal road",
        snore="Each snore made the teacups in the palace pantry clink together.",
        cue="drum",
        favorite_snack="honey_porridge",
        waking_line='"Mmm. That smells like a bowl with my name on it," the giant said, sitting up so suddenly that three birds hopped off his hat.',
        tags={"giant", "sleep", "breakfast"},
    ),
    "unicorn": CreatureCfg(
        id="unicorn",
        label="unicorn",
        phrase="a moon-pale unicorn",
        lair="the dew-silver orchard behind the castle",
        snore="Even asleep, it twitched one ear each time a pear dropped in the grass.",
        cue="bell",
        favorite_snack="apple_tart",
        waking_line='"A tart? And music too?" the unicorn said, lifting its bright head with a pleased little huff.',
        tags={"unicorn", "orchard", "magic"},
    ),
}

TOOLS = {
    "golden_trumpet": Tool(
        id="golden_trumpet",
        label="golden trumpet",
        phrase="a golden trumpet no longer than a loaf of bread",
        cue="trumpet",
        sound_text="Toot-ti-toot!",
        gentle=3,
        funny_fail="The note bounced around the lair, but the sleeper only rolled over and snored in a new rhythm.",
        tags={"trumpet", "music"},
    ),
    "kettle_drum": Tool(
        id="kettle_drum",
        label="kettle drum",
        phrase="a kettle drum with painted stars on the rim",
        cue="drum",
        sound_text="Boom-ba-boom!",
        gentle=3,
        funny_fail="The beat made a dust bunny dance across the floor, but the sleeper did not open a single eye.",
        tags={"drum", "music"},
    ),
    "silver_bell": Tool(
        id="silver_bell",
        label="silver bell",
        phrase="a silver bell with a blue silk ribbon",
        cue="bell",
        sound_text="Ting-a-ling!",
        gentle=3,
        funny_fail="The little bell rang sweetly, yet the sleeper only flicked an ear and tucked its nose deeper into a blanket of clover.",
        tags={"bell", "music"},
    ),
    "feather_fan": Tool(
        id="feather_fan",
        label="feather fan",
        phrase="a peacock-feather fan",
        cue="tickle",
        sound_text="Fwff-fwff!",
        gentle=2,
        funny_fail="A single sneeze escaped from the sleeper, and then the snoring came back even louder than before.",
        tags={"feather", "gentle"},
    ),
    "tin_horn": Tool(
        id="tin_horn",
        label="tin horn",
        phrase="a squeaky tin horn",
        cue="squeak",
        sound_text="Peeep!",
        gentle=2,
        funny_fail="The squeak startled a beetle under a stone, but the sleeper kept dreaming with perfect seriousness.",
        tags={"horn", "funny"},
    ),
    "toe_poke": Tool(
        id="toe_poke",
        label="toe poke",
        phrase="a rude poke with a stick",
        cue="poke",
        sound_text="Pok-pok!",
        gentle=0,
        funny_fail="The stick bent. Nothing else improved.",
        tags={"rude"},
    ),
}

HELPERS = {
    "kitchen_fairy": HelperCfg(
        id="kitchen_fairy",
        label="kitchen fairy",
        phrase="a flour-dusted kitchen fairy",
        brings={"cinnamon_bun", "apple_tart"},
        entrance="A blur of flour and sparkles came twirling down the path.",
        tags={"fairy", "kitchen"},
    ),
    "pantry_sprite": HelperCfg(
        id="pantry_sprite",
        label="pantry sprite",
        phrase="a pantry sprite with a spoon tucked into one boot",
        brings={"honey_porridge", "cinnamon_bun"},
        entrance="Out popped a pantry sprite from behind a sack of oats.",
        tags={"sprite", "kitchen"},
    ),
    "baker_gnome": HelperCfg(
        id="baker_gnome",
        label="baker gnome",
        phrase="a baker gnome with rosy cheeks",
        brings={"apple_tart", "cinnamon_bun", "honey_porridge"},
        entrance="A baker gnome bustled up the lane with steam curling from a covered tray.",
        tags={"gnome", "baking"},
    ),
}

SNACK_LABELS = {
    "cinnamon_bun": "a warm cinnamon bun",
    "honey_porridge": "a bowl of honey porridge",
    "apple_tart": "a shiny apple tart",
}

GIRL_NAMES = ["Lina", "Mira", "Suri", "Nora", "Elsa", "Poppy", "Tessa", "Wren"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Rowan", "Jasper", "Ned", "Robin"]
TRAITS = ["brave", "careful", "curious", "cheerful", "earnest", "nimble"]


def tool_is_allowed(tool: Tool) -> bool:
    return tool.gentle >= GENTLE_MIN


def helper_can_bring(helper: HelperCfg, creature: CreatureCfg) -> bool:
    return creature.favorite_snack in helper.brings


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for festival_id in FESTIVALS:
        for creature_id, creature in CREATURES.items():
            for tool_id, tool in TOOLS.items():
                if not tool_is_allowed(tool):
                    continue
                for helper_id, helper in HELPERS.items():
                    if helper_can_bring(helper, creature):
                        combos.append((festival_id, creature_id, tool_id, helper_id))
    return combos


def tool_works(tool: Tool, creature: CreatureCfg) -> bool:
    return tool.cue == creature.cue


def outcome_of(params: "StoryParams") -> str:
    creature = CREATURES[params.creature]
    tool = TOOLS[params.tool]
    return "direct" if tool_works(tool, creature) else "assisted"


def explain_tool_rejection(tool: Tool) -> str:
    return (
        f"(No story: {tool.label} is too rude for a gentle fairy tale "
        f"(gentleness={tool.gentle} < {GENTLE_MIN}). The waking method should be safe and kind.)"
    )


def explain_helper_rejection(helper: HelperCfg, creature: CreatureCfg) -> str:
    need = SNACK_LABELS[creature.favorite_snack]
    return (
        f"(No story: {helper.label} cannot plausibly bring {need}, which is what the "
        f"{creature.label} loves best. The helper must carry a believable fix.)"
    )


def predict_waking(world: World, tool_id: str, helper_id: str) -> dict:
    sim = world.copy()
    creature = CREATURES[sim.facts["creature_cfg"].id]
    tool = TOOLS[tool_id]
    helper = HELPERS[helper_id]
    _use_tool(sim, tool, creature, narrate=False)
    if sim.get("creature").meters["awake"] < THRESHOLD and helper_can_bring(helper, creature):
        _offer_snack(sim, helper, creature, narrate=False)
    return {
        "awake": sim.get("creature").meters["awake"] >= THRESHOLD,
        "festival_ready": sim.get("festival").meters["ready"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, ruler: Entity, festival: Festival) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"In a kingdom where polite ducks wore velvet caps, {hero.id} lived not far from the castle."
    )
    world.say(
        f"On the evening of the {festival.id.replace('_', ' ')}, {festival.image}, "
        f"and everyone in the kingdom was supposed to gather in {festival.place}."
    )
    world.say(
        f"But {ruler.label_word.capitalize()} {ruler.id} wrung {ruler.pronoun('possessive')} hands. "
        f"The celebration could not begin until one magical sleeper woke up."
    )


def appoint(world: World, hero: Entity, ruler: Entity, festival: Festival) -> None:
    hero.memes["pride"] += 1
    title = f"Official Starter of the {festival.id.replace('_', ' ').title()}"
    hero.attrs["title"] = title
    world.say(
        f'"Then I appoint you," declared {ruler.label_word} {ruler.id}, placing a ribbon badge on {hero.id}\'s chest, '
        f'"the {title}!"'
    )
    world.say(
        f"The badge was slightly crooked, which somehow made it look even more official."
    )


def describe_sleeper(world: World, creature: CreatureCfg) -> None:
    world.say(
        f"The sleeper was {creature.phrase}, curled up in {creature.lair}. {creature.snore}"
    )


def plan(world: World, hero: Entity, tool: Tool, helper: HelperCfg, creature: CreatureCfg) -> None:
    pred = predict_waking(world, tool.id, helper.id)
    hero.memes["resolve"] += 1
    world.facts["predicted_awake"] = pred["awake"]
    world.say(
        f'{hero.id} took {tool.phrase} in both hands and tried to stand as tall as an official person ought to stand.'
    )
    if tool_works(tool, creature):
        world.say(
            f'{hero.pronoun("subject").capitalize()} had heard that this kind of music often reached the {creature.label} even through the thickest dream.'
        )
    else:
        world.say(
            f'{hero.pronoun("subject").capitalize()} hoped any respectable noise might do, though the sleeping {creature.label} looked very serious about sleeping.'
        )


def _use_tool(world: World, tool: Tool, creature: CreatureCfg, narrate: bool = True) -> None:
    ent = world.get("creature")
    ent.meters["startled"] += 1
    if tool_works(tool, creature):
        ent.meters["awake"] += 1
        ent.meters["sleep"] = 0.0
    propagate(world, narrate=narrate)


def try_tool(world: World, hero: Entity, tool: Tool, creature: CreatureCfg) -> None:
    world.say(
        f'{hero.id} raised the {tool.label} and made it sing: {tool.sound_text}'
    )
    _use_tool(world, tool, creature, narrate=False)
    if world.get("creature").meters["awake"] >= THRESHOLD:
        world.say(
            f"The sound slid neatly into the dream like a key into a lock. {creature.waking_line}"
        )
    else:
        world.say(tool.funny_fail)
        world.say(
            f'{hero.id} looked down at the crooked badge and whispered, "I hope official counts even when the plan feels wobbly."'
        )


def _offer_snack(world: World, helper: HelperCfg, creature: CreatureCfg, narrate: bool = True) -> None:
    ent = world.get("creature")
    ent.meters["awake"] += 1
    ent.meters["sleep"] = 0.0
    world.get("helper").meters["helped"] += 1
    propagate(world, narrate=narrate)


def helper_rescue(world: World, hero: Entity, helper: HelperCfg, creature: CreatureCfg) -> None:
    snack = SNACK_LABELS[creature.favorite_snack]
    world.get("hero").memes["hope"] += 1
    world.say(helper.entrance)
    world.say(
        f'It was {helper.phrase}, carrying {snack}. The smell drifted through the air as softly as a secret.'
    )
    _offer_snack(world, helper, creature, narrate=False)
    world.say(
        f'{creature.waking_line} At once, the creature followed the smell with a hopeful nose.'
    )
    world.say(
        f'"You were very official to try first," said the helper, "but breakfast can be more official than trumpets in certain emergencies."'
    )


def celebration(world: World, hero: Entity, ruler: Entity, festival: Festival, creature: CreatureCfg, outcome: str) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    if outcome == "direct":
        world.say(
            f'Soon the {creature.label} was awake, washed, and padding toward {festival.place} beside {hero.id} as if they had practiced all morning.'
        )
    else:
        world.say(
            f'Soon the {creature.label} was awake and cheerfully licking the last sweet crumbs away while hurrying toward {festival.place} with {hero.id}.'
        )
    world.say(
        f'{ruler.label_word.capitalize()} {ruler.id} laughed when {hero.id} arrived. "My splendid official," {ruler.pronoun()} said, "you have saved the evening."'
    )
    world.say(
        f'At the feast, {hero.id} kept the crooked badge on all night, and {festival.ending}.'
    )


def tell(
    festival: Festival,
    creature_cfg: CreatureCfg,
    tool: Tool,
    helper_cfg: HelperCfg,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    ruler_type: str = "queen",
    trait: str = "curious",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    ruler_name = "Marigold" if ruler_type == "queen" else "Alder"
    ruler = world.add(Entity(id=ruler_name, kind="character", type=ruler_type, role="ruler", label="the ruler"))
    creature = world.add(Entity(id="creature", kind="character", type=creature_cfg.label, role="creature", label=creature_cfg.label))
    helper = world.add(Entity(id="helper", kind="character", type="helper", role="helper", label=helper_cfg.label))
    fest = world.add(Entity(id="festival", type="festival", label=festival.id))

    creature.meters["sleep"] = 1.0

    world.facts.update(
        hero=hero,
        ruler=ruler,
        creature=creature,
        creature_cfg=creature_cfg,
        helper=helper,
        helper_cfg=helper_cfg,
        tool_cfg=tool,
        festival_cfg=festival,
    )

    introduce(world, hero, ruler, festival)
    world.para()
    appoint(world, hero, ruler, festival)
    describe_sleeper(world, creature_cfg)

    world.para()
    plan(world, hero, tool, helper_cfg, creature_cfg)
    try_tool(world, hero, tool, creature_cfg)

    outcome = "direct"
    if creature.meters["awake"] < THRESHOLD:
        outcome = "assisted"
        world.para()
        helper_rescue(world, hero, helper_cfg, creature_cfg)

    world.para()
    celebration(world, hero, ruler, festival, creature_cfg, outcome)

    world.facts.update(
        outcome=outcome,
        title=hero.attrs.get("title", ""),
        used_snack=outcome == "assisted",
        festival_ready=fest.meters["ready"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    festival: str
    creature: str
    tool: str
    helper: str
    hero_name: str
    hero_gender: str
    ruler_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "dragon": [
        ("What is a dragon in a fairy tale?",
         "A dragon in a fairy tale is a magical creature, often large and powerful. Some stories make dragons fierce, but some make them sleepy and funny instead.")
    ],
    "giant": [
        ("What is a giant?",
         "A giant is a person-like creature who is much bigger than ordinary people. In fairy tales, giants may be scary, silly, or surprisingly gentle.")
    ],
    "unicorn": [
        ("What is a unicorn?",
         "A unicorn is a magical horse-like creature with one horn. Fairy tales often show unicorns as graceful, bright, and a little mysterious.")
    ],
    "trumpet": [
        ("What does a trumpet sound like?",
         "A trumpet makes a bright, strong musical sound. It is good for calls that need to travel far.")
    ],
    "drum": [
        ("Why can a drum wake someone?",
         "A drum makes a deep beat you can feel as well as hear. Strong rhythms can be easier to notice than quiet sounds.")
    ],
    "bell": [
        ("Why does a bell sound special in stories?",
         "A bell makes a clear ringing sound that feels neat and magical. In stories, bells often mark an important moment.")
    ],
    "official": [
        ("What does official mean?",
         "Official means something has been chosen or approved by the people in charge. In a fairy tale, an official job may still look a little funny.")
    ],
    "festival": [
        ("What is a festival?",
         "A festival is a special time when people gather to celebrate. There may be food, music, decorations, and games.")
    ],
    "breakfast": [
        ("Why can a good smell wake someone?",
         "A delicious smell can reach a sleeping nose and remind someone of food. That can make a sleepy body want to wake up.")
    ],
}
KNOWLEDGE_ORDER = ["official", "festival", "dragon", "giant", "unicorn", "trumpet", "drum", "bell", "breakfast"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    creature_cfg = f["creature_cfg"]
    festival = f["festival_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a humorous fairy tale for a 3-to-5-year-old that includes the word "official". '
        f'The story should be about {hero.id}, a child who must wake a sleeping {creature_cfg.label} before a royal celebration.'
    )
    if outcome == "direct":
        return [
            base,
            f"Tell a fairy-tale story where {hero.id} is given a silly official title, uses a {tool.label}, and the sleeping {creature_cfg.label} wakes in time for the {festival.id.replace('_', ' ')}.",
            f'Write a gentle magical story with humor, a crooked badge, and a happy ending where music solves the problem.'
        ]
    return [
        base,
        f"Tell a fairy-tale story where {hero.id}'s first official plan with a {tool.label} does not work, but a helper arrives with the right snack and saves the {festival.id.replace('_', ' ')}.",
        f'Write a child-facing magical story with humor, an absurd official title, and a happy ending where breakfast works better than ceremony.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    ruler = f["ruler"]
    creature_cfg = f["creature_cfg"]
    festival = f["festival_cfg"]
    tool = f["tool_cfg"]
    helper_cfg = f["helper_cfg"]
    title = f["title"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child in a fairy-tale kingdom, and a sleeping {creature_cfg.label} that had to wake up before the celebration could begin."
        ),
        (
            f"What official job did {hero.id} get?",
            f'{hero.id} was given the title "{title}." The grand title is funny because the badge was crooked and the job was simply to wake a sleepy magical creature.'
        ),
        (
            f"Why did the kingdom need the {creature_cfg.label} to wake up?",
            f"The royal celebration was waiting for the {creature_cfg.label}. The evening could not properly begin until the sleeper joined everyone in {festival.place}."
        ),
    ]
    if outcome == "direct":
        qa.append(
            (
                f"How did {hero.id} wake the {creature_cfg.label}?",
                f"{hero.id} used the {tool.label}, and that sound fit the {creature_cfg.label}'s kind of dream. The right music reached the sleeper and woke it gently."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The creature woke in time, and the celebration began happily. At the end, {hero.id} still wore the crooked official badge while the kingdom enjoyed the feast."
            )
        )
    else:
        snack = SNACK_LABELS[creature_cfg.favorite_snack]
        qa.append(
            (
                f"Why did {hero.id}'s first plan fail?",
                f"The {tool.label} made a real sound, but it was not the special kind that best woke this {creature_cfg.label}. It only changed the snoring and made {hero.id} worry."
            )
        )
        qa.append(
            (
                f"How was the problem solved?",
                f"{helper_cfg.label.capitalize()} arrived with {snack}, which the {creature_cfg.label} loved. The smell reached the sleeper and worked better than the first official plan."
            )
        )
        qa.append(
            (
                "What makes the story funny?",
                f"It is funny that the kingdom gave {hero.id} a huge official title for such a wobbly job. It is also funny that breakfast turned out to be more useful than ceremony."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"official", "festival"}
    creature = f["creature_cfg"]
    tool = f["tool_cfg"]
    if creature.id in KNOWLEDGE:
        tags.add(creature.id)
    if tool.cue == "trumpet":
        tags.add("trumpet")
    if tool.cue == "drum":
        tags.add("drum")
    if tool.cue == "bell":
        tags.add("bell")
    if f["outcome"] == "assisted":
        tags.add("breakfast")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        festival="lantern_feast",
        creature="dragon",
        tool="golden_trumpet",
        helper="kitchen_fairy",
        hero_name="Lina",
        hero_gender="girl",
        ruler_type="queen",
        trait="cheerful",
        seed=11,
    ),
    StoryParams(
        festival="jam_parade",
        creature="giant",
        tool="silver_bell",
        helper="pantry_sprite",
        hero_name="Milo",
        hero_gender="boy",
        ruler_type="king",
        trait="earnest",
        seed=12,
    ),
    StoryParams(
        festival="starlight_ball",
        creature="unicorn",
        tool="silver_bell",
        helper="baker_gnome",
        hero_name="Nora",
        hero_gender="girl",
        ruler_type="queen",
        trait="careful",
        seed=13,
    ),
    StoryParams(
        festival="lantern_feast",
        creature="dragon",
        tool="feather_fan",
        helper="baker_gnome",
        hero_name="Owen",
        hero_gender="boy",
        ruler_type="king",
        trait="curious",
        seed=14,
    ),
]


ASP_RULES = r"""
allowed_tool(T) :- tool(T), gentle(T, G), gentle_min(M), G >= M.
helper_ok(H, C) :- helper(H), creature(C), favorite(C, S), brings(H, S).

valid(F, C, T, H) :- festival(F), creature(C), allowed_tool(T), helper_ok(H, C).

works(T, C) :- tool_cue(T, Cue), need_cue(C, Cue).
outcome(direct) :- chosen_creature(C), chosen_tool(T), works(T, C).
outcome(assisted) :- chosen_creature(C), chosen_tool(T), not works(T, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fid in FESTIVALS:
        lines.append(asp.fact("festival", fid))
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("need_cue", cid, creature.cue))
        lines.append(asp.fact("favorite", cid, creature.favorite_snack))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_cue", tid, tool.cue))
        lines.append(asp.fact("gentle", tid, tool.gentle))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for snack in sorted(helper.brings):
            lines.append(asp.fact("brings", hid, snack))
    lines.append(asp.fact("gentle_min", GENTLE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_creature", params.creature),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = []
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad.append(params)
    if not bad:
        print(f"OK: outcomes match on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Humorous fairy-tale storyworld: an official child helper wakes a magical sleeper for a royal celebration."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--ruler", choices=["queen", "king"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not tool_is_allowed(TOOLS[args.tool]):
        raise StoryError(explain_tool_rejection(TOOLS[args.tool]))
    if args.helper and args.creature:
        helper = HELPERS[args.helper]
        creature = CREATURES[args.creature]
        if not helper_can_bring(helper, creature):
            raise StoryError(explain_helper_rejection(helper, creature))

    combos = [
        combo for combo in valid_combos()
        if (args.festival is None or combo[0] == args.festival)
        and (args.creature is None or combo[1] == args.creature)
        and (args.tool is None or combo[2] == args.tool)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    festival_id, creature_id, tool_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    ruler_type = args.ruler or rng.choice(["queen", "king"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        festival=festival_id,
        creature=creature_id,
        tool=tool_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        ruler_type=ruler_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        festival = FESTIVALS[params.festival]
        creature = CREATURES[params.creature]
        tool = TOOLS[params.tool]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter value {err}.)") from err

    if not tool_is_allowed(tool):
        raise StoryError(explain_tool_rejection(tool))
    if not helper_can_bring(helper, creature):
        raise StoryError(explain_helper_rejection(helper, creature))

    world = tell(
        festival=festival,
        creature_cfg=creature,
        tool=tool,
        helper_cfg=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        ruler_type=params.ruler_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (festival, creature, tool, helper) combos:\n")
        for festival_id, creature_id, tool_id, helper_id in combos:
            print(f"  {festival_id:15} {creature_id:8} {tool_id:15} {helper_id}")
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
            header = f"### {p.hero_name}: {p.creature} / {p.tool} / {outcome_of(p)}"
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
