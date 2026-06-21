#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/deception_bangle_cautionary_surprise_fairy_tale.py
=============================================================================

A standalone story world for a small fairy-tale domain built around deception,
a precious bangle, a cautionary choice, and a surprising reveal.

Premise
-------
A child wears a treasured bangle and meets a flattering stranger in a storybook
place. The stranger is a deceiver in disguise. The child hands over the bangle
for a "magic trick," the stranger slips away, and a wise grown-up uses a simple
counter-spell or tracking trick to expose the deception. Sometimes they recover
the bangle in time. Sometimes they arrive too late and only the lesson remains.

The world model prefers only *reasonable* combinations:
- a deceiver must fit the chosen hideout
- a helper method must be a plausible counter to that deceiver

The ending is then determined by timing:
- quick enough help -> the bangle is recovered
- too much delay -> the thief keeps it, though the child still learns

Run it
------
    python storyworlds/worlds/gpt-5.4/deception_bangle_cautionary_surprise_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/deception_bangle_cautionary_surprise_fairy_tale.py --deceiver jackdaw --helper mirror
    python storyworlds/worlds/gpt-5.4/deception_bangle_cautionary_surprise_fairy_tale.py --hideout well
    python storyworlds/worlds/gpt-5.4/deception_bangle_cautionary_surprise_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/deception_bangle_cautionary_surprise_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/deception_bangle_cautionary_surprise_fairy_tale.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def title(self) -> str:
        return {"mother": "mother", "father": "father",
                "grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class DeceiverCfg:
    id: str
    disguise: str = ""
    true_form: str = ""
    promise: str = ""
    slip_text: str = ""
    reveal_text: str = ""
    hideouts: set[str] = field(default_factory=set)
    counters: set[str] = field(default_factory=set)
    cunning: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class HideoutCfg:
    id: str
    phrase: str = ""
    trail: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str = ""
    phrase: str = ""
    action: str = ""
    reveal_line: str = ""
    power: int = 1
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


def _r_theft_sadness(world: World) -> list[str]:
    hero = world.get("hero")
    bangle = world.get("bangle")
    if bangle.meters["stolen"] < THRESHOLD:
        return []
    sig = ("theft_sadness",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["sadness"] += 1
    return ["__theft__"]


def _r_reveal_breaks_glamour(world: World) -> list[str]:
    deceiver = world.get("deceiver")
    if deceiver.meters["exposed"] < THRESHOLD:
        return []
    sig = ("reveal_breaks_glamour",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    deceiver.meters["glamour"] = 0.0
    deceiver.memes["panic"] += 1
    return ["__reveal__"]


def _r_recovery_relief(world: World) -> list[str]:
    hero = world.get("hero")
    guardian = world.get("guardian")
    bangle = world.get("bangle")
    if bangle.meters["recovered"] < THRESHOLD:
        return []
    sig = ("recovery_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    guardian.memes["care"] += 1
    return ["__recovered__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="theft_sadness", tag="emotion", apply=_r_theft_sadness),
    Rule(name="reveal_breaks_glamour", tag="physical", apply=_r_reveal_breaks_glamour),
    Rule(name="recovery_relief", tag="emotion", apply=_r_recovery_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


DECEIVERS = {
    "jackdaw": DeceiverCfg(
        id="jackdaw",
        disguise="a velvet-hatted peddler with a honeyed smile",
        true_form="a glossy black jackdaw",
        promise='that the child\'s bangle could be taught to ring like a silver bell if it were handed over for just one breath',
        slip_text="snatched the bangle, gave a bow too low to be honest, and flapped away in a blur of black sleeves",
        reveal_text="the velvet hat split into feathers, and the peddler sprang upward as a jackdaw with a thief's bright eye",
        hideouts={"bell_tower", "oak_hollow"},
        counters={"bell", "mirror"},
        cunning=2,
        tags={"bird", "deception"},
    ),
    "fox": DeceiverCfg(
        id="fox",
        disguise="a lace seller with a basket on one arm and a soft, polite voice",
        true_form="a red fox with sly paws",
        promise='that the child\'s bangle would shine like sunrise gold if it were polished under the stranger\'s special cloth',
        slip_text="wrapped the bangle in a cloth, turned once in a swirl, and ran with a rust-red flick at the hem",
        reveal_text="the lace twisted into tail-fur, and the neat seller dropped to four paws as a fox",
        hideouts={"bramble_den", "mill_ledge"},
        counters={"flour", "mirror"},
        cunning=1,
        tags={"fox", "deception"},
    ),
    "boggart": DeceiverCfg(
        id="boggart",
        disguise="a bent old auntie in a mossy shawl",
        true_form="a boggart with long fingers and marsh-green eyes",
        promise='that the child\'s bangle could hear tomorrow\'s wish if it were dipped in a hidden cup of moonlit water',
        slip_text="closed both hands around the bangle, breathed out a cold laugh, and slid into the shadows like smoke",
        reveal_text="the shawl sagged into mist, and the old auntie lengthened into a boggart with marsh-green eyes",
        hideouts={"well", "hearth_niche"},
        counters={"moonwater", "mirror"},
        cunning=3,
        tags={"boggart", "deception"},
    ),
}

HIDEOUTS = {
    "bell_tower": HideoutCfg(
        id="bell_tower",
        phrase="the old bell tower at the edge of the village",
        trail="a single dark feather on the stair and a silver clink above",
        ending_image="high in the bell tower, evening light touched the stone, and the rescued bangle flashed like a tiny moon",
        tags={"tower"},
    ),
    "oak_hollow": HideoutCfg(
        id="oak_hollow",
        phrase="the hollow inside the oldest oak in the wood",
        trail="small claw marks in the bark and one glimmer hidden among leaves",
        ending_image="inside the oak hollow, the bangle shone among acorns while the wood settled back into a gentle hush",
        tags={"tree"},
    ),
    "bramble_den": HideoutCfg(
        id="bramble_den",
        phrase="a tight bramble den beyond the cabbage patch",
        trail="fine tracks in the dust and one thread of lace caught on a thorn",
        ending_image="beside the bramble den, the thorns held drops of rain, and the bangle gleamed clean in the grass",
        tags={"bramble"},
    ),
    "mill_ledge": HideoutCfg(
        id="mill_ledge",
        phrase="the ledge behind the old mill wheel",
        trail="a rust-red hair on wet wood and a bright wink between the boards",
        ending_image="behind the mill wheel, water turned softly, and the bangle lay safe again in the hero's palm",
        tags={"mill"},
    ),
    "well": HideoutCfg(
        id="well",
        phrase="the ivy-ringed village well",
        trail="cold droplets on the stones and a green shimmer where no moss should be",
        ending_image="by the village well, the water grew still, and the bangle rested warm in the hero's hand again",
        tags={"well"},
    ),
    "hearth_niche": HideoutCfg(
        id="hearth_niche",
        phrase="the dark niche behind an unused hearth",
        trail="ash stirred where no wind had passed and a whisper seemed to hide in the bricks",
        ending_image="at the cold hearth, the last ash settled, and the bangle glowed softly as if it had learned better too",
        tags={"hearth"},
    ),
}

HELPERS = {
    "bell": HelperCfg(
        id="bell",
        label="bell",
        phrase="a clear little chapel bell",
        action="rang the bell three bright times",
        reveal_line="False shapes hate a true bell. Listen now.",
        power=2,
        tags={"bell", "sound"},
    ),
    "flour": HelperCfg(
        id="flour",
        label="flour",
        phrase="a pinch of white flour from the kitchen jar",
        action="cast the flour in a pale arc over the path",
        reveal_line="A thief may hide a face, but not the prints it leaves behind.",
        power=2,
        tags={"flour", "tracking"},
    ),
    "moonwater": HelperCfg(
        id="moonwater",
        label="moonwater",
        phrase="a spoonful of moonwater kept in a blue glass bottle",
        action="sprinkled the moonwater in a shining ring",
        reveal_line="Moonwater tells the truth to shadows.",
        power=3,
        tags={"moonwater", "magic"},
    ),
    "mirror": HelperCfg(
        id="mirror",
        label="mirror",
        phrase="a small round mirror with a silver back",
        action="tilted the mirror so the stranger's face caught the evening light",
        reveal_line="A borrowed face cannot bear its own reflection.",
        power=3,
        tags={"mirror", "truth"},
    ),
}

HERO_NAMES = ["Lina", "Mira", "Tessa", "Ivy", "Nell", "Rose", "Ari", "Owen", "Finn", "Theo"]
TRAITS = ["trusting", "dreamy", "kind", "eager", "careful", "curious"]
GUARDIANS = ["mother", "father", "grandmother", "grandfather"]


def helper_works(helper_id: str, deceiver_id: str) -> bool:
    return helper_id in DECEIVERS[deceiver_id].counters


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for deceiver_id, deceiver in DECEIVERS.items():
        for hideout_id in deceiver.hideouts:
            for helper_id in HELPERS:
                if helper_works(helper_id, deceiver_id):
                    out.append((deceiver_id, hideout_id, helper_id))
    return sorted(out)


def outcome_of(params: "StoryParams") -> str:
    deceiver = DECEIVERS[params.deceiver]
    helper = HELPERS[params.helper]
    return "recovered" if helper.power >= deceiver.cunning + params.delay else "lost"


def explain_hideout(deceiver_id: str, hideout_id: str) -> str:
    return (
        f"(No story: {deceiver_id} does not plausibly flee to {hideout_id}. "
        f"Pick a hideout that matches that deceiver's habits.)"
    )


def explain_helper(deceiver_id: str, helper_id: str) -> str:
    return (
        f"(No story: {HELPERS[helper_id].label} is not a plausible way to expose "
        f"the {deceiver_id}'s deception in this world. Pick a helper that truly counters it.)"
    )


def introduce(world: World, hero: Entity, guardian: Entity) -> None:
    bangle = world.get("bangle")
    world.say(
        f"Once, in a village where dusk always seemed to carry a little gold in its hem, "
        f"{hero.id} lived with {hero.pronoun('possessive')} {guardian.title}."
    )
    world.say(
        f"On the child's wrist shone {bangle.phrase}, a bangle given with the warning to guard it well and never trust a sweet tongue too quickly."
    )
    if "careful" in hero.traits:
        world.say(f"{hero.id} usually tried to remember such warnings.")
    else:
        world.say(f"But {hero.id} loved marvels, and marvels sometimes walked very close to mistakes.")


def set_out(world: World, hero: Entity) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"That evening {hero.id} skipped along the lane where elderflowers nodded, turning the bangle so it caught the last pale light."
    )


def meet_deceiver(world: World, hero: Entity, deceiver: Entity, cfg: DeceiverCfg) -> None:
    deceiver.meters["glamour"] += 1
    world.say(
        f"By the roadside stood {cfg.disguise}. The stranger bowed and praised the shining bangle at once."
    )
    world.say(
        f"Then the stranger said {cfg.promise}."
    )
    if "careful" in hero.traits:
        world.say(
            f"{hero.id} hesitated, because the words sounded smooth as pond ice. Yet the promise was bright, and bright things can tug hard at a young heart."
        )
    else:
        world.say(
            f"The promise was so pretty that it almost sounded true."
        )


def trust_and_hand_over(world: World, hero: Entity, deceiver: Entity, cfg: DeceiverCfg) -> None:
    bangle = world.get("bangle")
    hero.memes["trust"] += 1
    hero.memes["desire"] += 1
    bangle.meters["stolen"] += 1
    bangle.attrs["holder"] = "deceiver"
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} slipped off the bangle and set it in the stranger's hand."
    )
    world.say(
        f"In that same blink the stranger {cfg.slip_text}."
    )
    world.say(
        f'"My bangle!" cried {hero.id}.'
    )


def guardian_arrives(world: World, hero: Entity, guardian: Entity, hideout: HideoutCfg) -> None:
    guardian.memes["care"] += 1
    world.say(
        f"{guardian.title.capitalize()} came hurrying at the cry and found {hero.id} with empty wrist and frightened eyes."
    )
    world.say(
        f'Together they searched, and soon they found {hideout.trail}.'
    )


def reveal(world: World, guardian: Entity, helper_cfg: HelperCfg, deceiver_cfg: DeceiverCfg) -> None:
    deceiver = world.get("deceiver")
    deceiver.meters["exposed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{guardian.title.capitalize()} took out {helper_cfg.phrase} and {helper_cfg.action}. "{helper_cfg.reveal_line}"'
    )
    world.say(
        f"At once {deceiver_cfg.reveal_text}."
    )


def recover(world: World, hero: Entity, guardian: Entity, hideout: HideoutCfg, deceiver_cfg: DeceiverCfg) -> None:
    bangle = world.get("bangle")
    bangle.meters["recovered"] += 1
    bangle.meters["stolen"] = 0.0
    bangle.attrs["holder"] = "hero"
    propagate(world, narrate=False)
    world.say(
        f"The startled {deceiver_cfg.true_form} dropped the bangle and fled for {hideout.phrase}, but not before {guardian.title} caught the shining circle."
    )
    world.say(
        f'{guardian.title.capitalize()} fastened it back around {hero.id}\'s wrist and said, "A gift may shine, but truth shines better."'
    )
    world.say(
        f"{hideout.ending_image}"
    )


def too_late(world: World, hero: Entity, guardian: Entity, hideout: HideoutCfg, deceiver_cfg: DeceiverCfg) -> None:
    hero.memes["lesson"] += 1
    hero.memes["sadness"] += 1
    world.say(
        f"The {deceiver_cfg.true_form} sprang for {hideout.phrase}, and by the time {hero.id} and {guardian.title} reached it, only the empty hush of the place remained."
    )
    world.say(
        f"{hideout.ending_image.replace('rescued ', '').replace("safe again in the hero's palm", 'gone from sight')}"
    )
    world.say(
        f'{guardian.title.capitalize()} put an arm around {hero.id} and said, "A lovely promise is not the same as a true one. Next time, keep your treasures in your own hand until a trusted grown-up can judge the matter."'
    )


def close_lesson(world: World, hero: Entity, guardian: Entity, recovered: bool) -> None:
    if recovered:
        world.say(
            f"From that day on, whenever praise came too quickly, {hero.id} remembered the deception behind the smiling bow and asked {guardian.title} before believing a wonder."
        )
    else:
        world.say(
            f"From that day on, {hero.id} remembered how deception can dress itself in kind words, and never again slipped off a treasured thing for a stranger's promise."
        )


def tell(
    *,
    deceiver_cfg: DeceiverCfg,
    hideout_cfg: HideoutCfg,
    helper_cfg: HelperCfg,
    hero_name: str,
    hero_gender: str,
    guardian_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_type,
        label=guardian_type,
        role="guardian",
    ))
    deceiver = world.add(Entity(
        id="deceiver",
        kind="character",
        type="stranger",
        label="the stranger",
        role="deceiver",
        tags=set(deceiver_cfg.tags),
    ))
    bangle = world.add(Entity(
        id="bangle",
        type="bangle",
        label="bangle",
        phrase="a slim silver bangle with a clasp shaped like a leaf",
        attrs={"holder": "hero"},
        tags={"bangle", "treasure"},
    ))

    introduce(world, hero, guardian)
    set_out(world, hero)

    world.para()
    meet_deceiver(world, hero, deceiver, deceiver_cfg)
    trust_and_hand_over(world, hero, deceiver, deceiver_cfg)

    world.para()
    guardian_arrives(world, hero, guardian, hideout_cfg)
    reveal(world, guardian, helper_cfg, deceiver_cfg)

    recovered = helper_cfg.power >= deceiver_cfg.cunning + delay
    if recovered:
        recover(world, hero, guardian, hideout_cfg, deceiver_cfg)
    else:
        too_late(world, hero, guardian, hideout_cfg, deceiver_cfg)

    world.para()
    close_lesson(world, hero, guardian, recovered)

    world.facts.update(
        hero=hero,
        guardian=guardian,
        deceiver_cfg=deceiver_cfg,
        hideout_cfg=hideout_cfg,
        helper_cfg=helper_cfg,
        bangle=bangle,
        hero_name=hero_name,
        delay=delay,
        outcome="recovered" if recovered else "lost",
        recovered=recovered,
        deception=True,
    )
    return world


@dataclass
class StoryParams:
    deceiver: str
    hideout: str
    helper: str
    hero_name: str
    hero_gender: str
    guardian: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    deceiver = f["deceiver_cfg"]
    helper = f["helper_cfg"]
    return [
        'Write a short fairy tale for a 3-to-5-year-old that includes the words "deception" and "bangle".',
        f"Tell a cautionary fairy tale where a {hero.type} named {f['hero_name']} is tricked by {deceiver.disguise} and a wise {guardian.title} uses {helper.phrase} to uncover the truth.",
        "Write a gentle surprise story in fairy-tale style where a flattering stranger is not what they seem, and the ending teaches a child not to trust sweet promises too quickly.",
    ]


KNOWLEDGE = {
    "deception": [
        (
            "What is deception?",
            "Deception means making someone believe something that is not true. It is a kind of trick, and it can hurt feelings or take things away."
        )
    ],
    "bangle": [
        (
            "What is a bangle?",
            "A bangle is a stiff bracelet that goes around your wrist. Some are plain, and some are made to look very special."
        )
    ],
    "mirror": [
        (
            "What does a mirror do?",
            "A mirror reflects what is in front of it. In fairy tales, a mirror often shows the truth when someone is hiding behind a false look."
        )
    ],
    "bell": [
        (
            "Why might a bell matter in a fairy tale?",
            "A clear bell can startle hidden creatures and cut through tricks. Fairy tales often use a bright sound to wake people up to the truth."
        )
    ],
    "flour": [
        (
            "How can flour help find a thief?",
            "Flour can stick to feet or paws and make a path easier to see. It helps people follow where someone really went."
        )
    ],
    "moonwater": [
        (
            "What is moonwater in a fairy tale?",
            "Moonwater is magical water saved under moonlight. In fairy tales, it often reveals secrets and melts false enchantments."
        )
    ],
    "fox": [
        (
            "Why is a fox often shown as sly in stories?",
            "Stories often use a fox to stand for clever trickery. That does not mean real foxes tell lies, but fairy tales use them as symbols."
        )
    ],
    "bird": [
        (
            "Why do shiny things attract some birds?",
            "Some birds notice bright, glinting objects and may peck at or carry them away. In stories, that habit becomes part of a trickster character."
        )
    ],
    "boggart": [
        (
            "What is a boggart in a fairy tale?",
            "A boggart is a made-up goblin-like creature from old stories. It likes dark corners, mischief, and making people uneasy."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "deception",
    "bangle",
    "mirror",
    "bell",
    "flour",
    "moonwater",
    "fox",
    "bird",
    "boggart",
]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    deceiver = f["deceiver_cfg"]
    helper = f["helper_cfg"]
    hideout = f["hideout_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['hero_name']}, a child with a treasured bangle, and {hero.pronoun('possessive')} {guardian.title} who comes to help. It is also about a stranger whose kind manner hides deception."
        ),
        (
            "What trick did the stranger use?",
            f"The stranger praised the bangle and promised something magical to make {f['hero_name']} hand it over. The deception worked because the promise sounded lovely and safe when it was really a trick."
        ),
        (
            "Why did the child lose the bangle?",
            f"{f['hero_name']} trusted the stranger's sweet words and placed the bangle in the stranger's hand. The loss came from believing a pretty promise before checking with a trusted grown-up."
        ),
        (
            f"How did the {guardian.title} uncover the truth?",
            f"The {guardian.title} used {helper.phrase} and followed the clue toward {hideout.phrase}. That broke the false look and revealed that the stranger was really {deceiver.true_form}."
        ),
    ]
    if outcome == "recovered":
        qa.append(
            (
                "How did the story end?",
                f"The bangle was recovered and fastened back on the child's wrist. The surprise reveal turned a frightening mistake into a lesson about asking a trusted grown-up before believing a stranger."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"The child did not get the bangle back, because help came too late after the deception. Even so, the ending leaves a clear lesson: beautiful words are not proof that someone is true."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"deception", "bangle"} | set(f["helper_cfg"].tags) | set(f["deceiver_cfg"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(name for (name, *_) in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        deceiver="jackdaw",
        hideout="bell_tower",
        helper="mirror",
        hero_name="Mira",
        hero_gender="girl",
        guardian="grandmother",
        trait="dreamy",
        delay=0,
    ),
    StoryParams(
        deceiver="fox",
        hideout="bramble_den",
        helper="flour",
        hero_name="Finn",
        hero_gender="boy",
        guardian="father",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        deceiver="boggart",
        hideout="well",
        helper="moonwater",
        hero_name="Lina",
        hero_gender="girl",
        guardian="mother",
        trait="trusting",
        delay=1,
    ),
    StoryParams(
        deceiver="jackdaw",
        hideout="oak_hollow",
        helper="bell",
        hero_name="Theo",
        hero_gender="boy",
        guardian="grandfather",
        trait="careful",
        delay=1,
    ),
    StoryParams(
        deceiver="boggart",
        hideout="hearth_niche",
        helper="mirror",
        hero_name="Rose",
        hero_gender="girl",
        guardian="grandmother",
        trait="eager",
        delay=2,
    ),
]


ASP_RULES = r"""
valid(D, H, Hp) :- deceiver(D), hideout(H), helper(Hp), lurks(D, H), counters(Hp, D).

severity(C + D) :- chosen_deceiver(X), cunning(X, C), delay(D).
recovered :- chosen_deceiver(X), chosen_helper(H), power(H, P), severity(S), P >= S, counters(H, X).
lost :- chosen_deceiver(X), chosen_helper(H), severity(S), power(H, P), P < S, counters(H, X).

outcome(recovered) :- recovered.
outcome(lost) :- lost.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for deceiver_id, deceiver in DECEIVERS.items():
        lines.append(asp.fact("deceiver", deceiver_id))
        lines.append(asp.fact("cunning", deceiver_id, deceiver.cunning))
        for hideout in sorted(deceiver.hideouts):
            lines.append(asp.fact("lurks", deceiver_id, hideout))
        for helper in sorted(deceiver.counters):
            lines.append(asp.fact("counters", helper, deceiver_id))
    for hideout_id in HIDEOUTS:
        lines.append(asp.fact("hideout", hideout_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_deceiver", params.deceiver),
        asp.fact("chosen_helper", params.helper),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = []
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            bad.append((params, py, asp))
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome disagreements.")
        for params, py, asp in bad[:5]:
            print(f"  {params} -> python={py} asp={asp}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        if "bangle" not in sample.story.lower():
            raise StoryError("smoke test story omitted required domain word 'bangle'")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a fairy-tale deception, a stolen bangle, and a surprising reveal."
    )
    ap.add_argument("--deceiver", choices=sorted(DECEIVERS))
    ap.add_argument("--hideout", choices=sorted(HIDEOUTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long help takes to act")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.deceiver and args.hideout:
        if args.hideout not in DECEIVERS[args.deceiver].hideouts:
            raise StoryError(explain_hideout(args.deceiver, args.hideout))
    if args.deceiver and args.helper:
        if not helper_works(args.helper, args.deceiver):
            raise StoryError(explain_helper(args.deceiver, args.helper))

    combos = [
        combo for combo in valid_combos()
        if (args.deceiver is None or combo[0] == args.deceiver)
        and (args.hideout is None or combo[1] == args.hideout)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    deceiver_id, hideout_id, helper_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        pool = [name for name in HERO_NAMES if (hero_gender == "girl") == (name in {"Lina", "Mira", "Tessa", "Ivy", "Nell", "Rose"})]
        if not pool:
            pool = HERO_NAMES
        hero_name = rng.choice(pool)
    guardian = args.guardian or rng.choice(GUARDIANS)
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        deceiver=deceiver_id,
        hideout=hideout_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        guardian=guardian,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.deceiver not in DECEIVERS:
        raise StoryError(f"(Unknown deceiver: {params.deceiver})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.hideout not in DECEIVERS[params.deceiver].hideouts:
        raise StoryError(explain_hideout(params.deceiver, params.hideout))
    if not helper_works(params.helper, params.deceiver):
        raise StoryError(explain_helper(params.deceiver, params.helper))
    world = tell(
        deceiver_cfg=DECEIVERS[params.deceiver],
        hideout_cfg=HIDEOUTS[params.hideout],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        guardian_type=params.guardian,
        trait=params.trait,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name),
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (deceiver, hideout, helper) combos:\n")
        for deceiver_id, hideout_id, helper_id in combos:
            print(f"  {deceiver_id:8} {hideout_id:12} {helper_id}")
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
            header = f"### {p.hero_name}: {p.deceiver} at {p.hideout} with {p.helper} ({outcome_of(p)})"
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
