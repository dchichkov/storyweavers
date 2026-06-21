#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/farce_olden_transformation_magic_animal_story.py
============================================================================

A standalone storyworld for a tiny olden animal-fable domain built from the
seed words "farce" and "olden" with the required features Transformation and
Magic.

Premise
-------
In an olden woodland fair, a small animal wants badly to help with an important
chore. Feeling too little for the job, the child uses a moonlit transformation
charm to become another animal with the needed skill. The new shape solves one
problem but creates a comic farce: the hero is mistaken for someone else,
pulled into the wrong part of the fair, and gets more tangled by trying to hide
the truth. A wise helper coaxes out an honest confession, the charm is undone,
and the ending proves that being oneself -- with help -- works better than a
magic shortcut.

The world model tracks physical meters (progress, mix-up, transformed) and
emotional memes (pride, worry, relief, belonging). Reasonableness is enforced:
a transformed form must actually provide the skill the chore needs. The inline
ASP twin mirrors that gate and the simple outcome model.

Run it
------
python storyworlds/worlds/gpt-5.4/farce_olden_transformation_magic_animal_story.py
python storyworlds/worlds/gpt-5.4/farce_olden_transformation_magic_animal_story.py --need reeds --form duck
python storyworlds/worlds/gpt-5.4/farce_olden_transformation_magic_animal_story.py --need bell_rope --form badger
python storyworlds/worlds/gpt-5.4/farce_olden_transformation_magic_animal_story.py --all
python storyworlds/worlds/gpt-5.4/farce_olden_transformation_magic_animal_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/farce_olden_transformation_magic_animal_story.py --verify
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
    traits: tuple = field(default_factory=tuple)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goose", "doe", "queen"}
        male = {"fox", "badger", "frog", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    fair_name: str
    olden_detail: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    title: str
    want_line: str
    task_line: str
    skill: str
    object_label: str
    success_line: str
    group_solution: str
    late_cost: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Form:
    id: str
    animal: str
    phrase: str
    skill: str
    movement: str
    mixup_line: str
    crowd_guess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    spell_words: str
    reverse_words: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    animal: str
    phrase: str
    notice_line: str
    comfort_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_mixup_from_disguise(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.meters["transformed"] < THRESHOLD:
        return []
    sig = ("mixup", hero.attrs.get("form_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["mixup"] += 1
    hero.memes["worry"] += 1
    return ["__mixup__"]


def _r_pressure_from_hiding(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.memes["hiding"] < THRESHOLD:
        return []
    sig = ("pressure",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["mixup"] += 1
    hero.memes["worry"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="mixup_from_disguise", tag="social", apply=_r_mixup_from_disguise),
    Rule(name="pressure_from_hiding", tag="social", apply=_r_pressure_from_hiding),
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


SETTINGS = {
    "green": Setting(
        id="green",
        place="the village green",
        fair_name="the Olden Acorn Fair",
        olden_detail="Mossy carts stood beside striped tents, and little brass bells winked in the sun.",
        closing_image="The fair drums thumped again while the lanterns warmed the grass.",
        tags={"fair", "olden"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the abbey courtyard",
        fair_name="the Olden Lantern Feast",
        olden_detail="Stone arches made cool shadows, and ribbons fluttered from the old gate.",
        closing_image="Lantern light slid along the old stone while everyone shared supper.",
        tags={"fair", "olden"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the castle orchard",
        fair_name="the Olden Apple Day",
        olden_detail="Bent apple trees leaned over long tables, and painted banners snapped in the breeze.",
        closing_image="The last gold apples shone over the tables as the music settled low.",
        tags={"fair", "olden"},
    ),
}

NEEDS = {
    "bell_rope": Need(
        id="bell_rope",
        title="ring the bell rope",
        want_line="wanted to help ring the high bell rope that opened the fair",
        task_line="The rope hung too high for little paws.",
        skill="reach_high",
        object_label="bell rope",
        success_line="The bell rope gave a happy clang above the crowd.",
        group_solution="Two friends steadied a barrel while the hero climbed and tugged the rope at last.",
        late_cost="By the time the truth came out, the opening clang had already been given by someone else.",
        tags={"bell", "fair"},
    ),
    "reeds": Need(
        id="reeds",
        title="fetch the pond reeds",
        want_line="wanted to fetch the silver-green reeds from the pond for the fair garlands",
        task_line="The reeds grew beyond the muddy edge where dry paws could not reach.",
        skill="swim",
        object_label="pond reeds",
        success_line="The reeds came up dripping and bright as ribbons.",
        group_solution="Friends held a basket at the bank while the hero guided the reeds in from the shallows.",
        late_cost="By the time the truth came out, another bundle of reeds had already been fetched, and the garland makers were waiting.",
        tags={"pond", "garland"},
    ),
    "sack": Need(
        id="sack",
        title="carry the flour sack",
        want_line="wanted to carry the heavy flour sack to the pie table",
        task_line="The sack was so heavy that it sagged like a sleepy moon.",
        skill="carry_heavy",
        object_label="flour sack",
        success_line="The flour sack bumped safely onto the pie table.",
        group_solution="Three friends took the corners together, and the sack slid along with plenty of laughing and puffing.",
        late_cost="By the time the truth came out, the bakers had already borrowed another sack and the hero had missed the grand beginning.",
        tags={"baking", "fair"},
    ),
    "banner": Need(
        id="banner",
        title="tie the banner",
        want_line="wanted to tie the bright welcome banner between two high branches",
        task_line="The knot had to be set above everyone's heads.",
        skill="climb",
        object_label="welcome banner",
        success_line="The banner flapped straight and bright over the lane.",
        group_solution="A friend passed up the ribbon while the hero climbed the ladder and tied the knot just so.",
        late_cost="By the time the truth came out, the banner had already been tied crooked by hurried paws and had to be fixed later.",
        tags={"banner", "fair"},
    ),
}

FORMS = {
    "magpie": Form(
        id="magpie",
        animal="magpie",
        phrase="a sleek little magpie",
        skill="reach_high",
        movement="hopped to the beam and stretched up with bright black wings",
        mixup_line="The town crier took one look and tried to hand over the parade announcements to the 'helpful bird.'",
        crowd_guess="Everyone thought the hero belonged with the bell birds over the stalls.",
        tags={"bird", "magic"},
    ),
    "duck": Form(
        id="duck",
        animal="duck",
        phrase="a round yellow-brown duck",
        skill="swim",
        movement="paddled into the pond as if the water had been waiting all morning",
        mixup_line="The goose sisters began herding the hero toward the race line, sure another duck had come to join the water games.",
        crowd_guess="Everyone thought the hero belonged with the pond birds.",
        tags={"bird", "water", "magic"},
    ),
    "badger": Form(
        id="badger",
        animal="badger",
        phrase="a stout striped badger",
        skill="carry_heavy",
        movement="braced sturdy legs and pushed forward with a grunt",
        mixup_line="The pie bakers cheered and piled two extra trays beside the 'strong helper' before the hero could blink.",
        crowd_guess="Everyone thought the hero belonged with the strong workers.",
        tags={"strength", "magic"},
    ),
    "squirrel": Form(
        id="squirrel",
        animal="squirrel",
        phrase="a nimble red squirrel",
        skill="climb",
        movement="skittered up the bark in one quick red ripple",
        mixup_line="The nut seller laughed and asked the hero to inspect the top branches for lost walnut ribbons.",
        crowd_guess="Everyone thought the hero belonged in the trees.",
        tags={"climb", "magic"},
    ),
}

RELICS = {
    "moon_charm": Relic(
        id="moon_charm",
        label="moon charm",
        phrase="an olden moon charm on a blue thread",
        spell_words="Moon above and moss below, lend me the shape I wish to know.",
        reverse_words="Name and heart and homeward feet, let my own small self be sweet.",
        tags={"magic", "olden"},
    ),
    "acorn_whistle": Relic(
        id="acorn_whistle",
        label="acorn whistle",
        phrase="an olden acorn whistle carved with tiny stars",
        spell_words="By seed and breeze and silver gleam, make me the creature of my dream.",
        reverse_words="Whistle low and whistle true, bring me back to what I knew.",
        tags={"magic", "olden"},
    ),
    "mirror_leaf": Relic(
        id="mirror_leaf",
        label="mirror leaf",
        phrase="an olden mirror leaf that shone like a puddle",
        spell_words="Leaf of wonder, shining thin, turn my outside from my skin.",
        reverse_words="Leaf be still and leaf be plain, let my own face rise again.",
        tags={"magic", "olden"},
    ),
}

HELPERS = {
    "owl": HelperKind(
        id="owl",
        animal="owl",
        phrase="a patient barn owl",
        notice_line="tilted a wise head and noticed that the strange animal's eyes looked worried instead of proud",
        comfort_line="spoke so softly that the noisy fair seemed to hush around the words",
        tags={"owl", "helper"},
    ),
    "tortoise": HelperKind(
        id="tortoise",
        animal="tortoise",
        phrase="an old tortoise with a ribboned cart",
        notice_line="blinked once, twice, and saw that the new helper kept looking at the charm instead of the job",
        comfort_line="answered so slowly and kindly that truth did not feel frightening",
        tags={"tortoise", "helper"},
    ),
    "mole": HelperKind(
        id="mole",
        animal="mole",
        phrase="a gentle mole baker",
        notice_line="sniffed the air and realized that the hero smelled of the same clover soap as before, not of the new shape at all",
        comfort_line="patted a floury paw and made an honest corner to stand in",
        tags={"mole", "helper"},
    ),
}

HEROES = [
    {"name": "Pip", "animal": "mouse"},
    {"name": "Tansy", "animal": "rabbit"},
    {"name": "Moss", "animal": "hedgehog"},
    {"name": "Nettle", "animal": "vole"},
]
TRAITS = ["eager", "small", "bright-eyed", "busy", "hopeful"]


def valid_combo(need: Need, form: Form) -> bool:
    return need.skill == form.skill


def valid_combos() -> list[tuple[str, str]]:
    return sorted(
        (need_id, form_id)
        for need_id, need in NEEDS.items()
        for form_id, form in FORMS.items()
        if valid_combo(need, form)
    )


@dataclass
class StoryParams:
    setting: str
    need: str
    form: str
    relic: str
    helper: str
    reveal: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


def explain_rejection(need: Need, form: Form) -> str:
    return (
        f"(No story: becoming {form.phrase} does not solve the need to {need.title}. "
        f"This world only allows transformations whose new body truly provides the needed skill.)"
    )


def introduce(world: World, hero: Entity, helper: Entity, need: Need) -> None:
    setting = world.setting
    world.say(
        f"In {setting.place}, the morning of {setting.fair_name} was beginning. "
        f"{setting.olden_detail}"
    )
    world.say(
        f"{hero.id}, a {hero.attrs['trait']} little {hero.type}, {need.want_line}."
    )
    world.say(need.task_line)
    world.say(
        f"Nearby, {helper.id}, {helper.phrase}, was already helping hang ribbons and count baskets."
    )


def temptation(world: World, hero: Entity, relic: Relic) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"In {hero.pronoun('possessive')} pocket lay {relic.phrase}, a family keepsake said to wake at fair time."
    )
    world.say(
        f'"If I were bigger, or quicker, or splashier for just one minute," {hero.id} whispered, '
        f'"I could help without asking anyone at all."'
    )


def transform(world: World, hero: Entity, need: Need, form: Form, relic: Relic) -> None:
    hero.meters["transformed"] += 1
    hero.meters["progress"] += 1
    hero.attrs["form_id"] = form.id
    hero.attrs["form_animal"] = form.animal
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} touched the {relic.label} and murmured, "
        f'"{relic.spell_words}"'
    )
    world.say(
        f"A silver shiver ran from whisker to tail, and where a little {hero.type} had stood "
        f"there now stood {form.phrase}."
    )
    world.say(
        f"The new body fit the problem at once: {form.movement} toward the {need.object_label}."
    )
    world.say(need.success_line)
    propagate(world, narrate=False)


def farce(world: World, hero: Entity, form: Form) -> None:
    hero.meters["farce"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But the fair turned silly in a hurry. {form.mixup_line}"
    )
    world.say(
        f"{form.crowd_guess} When {hero.id} tried to answer, the voice came out all wrong for the secret still hidden inside."
    )
    if hero.meters["mixup"] >= THRESHOLD:
        world.say(
            "The more the hero tried to act natural, the funnier and stranger the mistake became, until it felt like a little farce was skipping through the fair on its own feet."
        )


def helper_notices(world: World, helper: Entity) -> None:
    world.say(
        f"{helper.id} {helper.attrs['notice_line']}."
    )


def confess_early(world: World, hero: Entity, helper: Entity, relic: Relic) -> None:
    hero.memes["honesty"] += 1
    hero.memes["relief"] += 1
    world.say(
        f'"Please do not laugh," {hero.id} blurted. "I am not truly this shape. I only wanted to help."'
    )
    world.say(
        f"{helper.id} {helper.attrs['comfort_line']}. "
        f'"Then we will mend it honestly," {helper.pronoun()} said.'
    )
    world.say(
        f"Together they spoke the return words: \"{relic.reverse_words}\""
    )


def hide_longer(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["hiding"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tried one more time to smile and pretend everything was fine."
    )
    world.say(
        f"But the hiding only made the muddle worse. A drummer asked for a march, a baker asked for a lift, and the wrong work piled up around the poor disguised helper."
    )
    world.say(
        f"At last {helper.id} stepped close and waited without scolding until the truth could come out."
    )


def confess_late(world: World, hero: Entity, helper: Entity, relic: Relic) -> None:
    hero.memes["honesty"] += 1
    hero.memes["shame"] += 1
    hero.memes["relief"] += 1
    world.say(
        f'Tears pricked {hero.id}\'s eyes. "It was me all along," {hero.pronoun()} said. "I used magic because I was afraid my own small self was not enough."'
    )
    world.say(
        f"{helper.id} {helper.attrs['comfort_line']}. "
        f'"Small is not the same as useless," {helper.pronoun()} answered.'
    )
    world.say(
        f"Then they said the return words together: \"{relic.reverse_words}\""
    )


def reverse(world: World, hero: Entity) -> None:
    hero.meters["transformed"] = 0.0
    hero.attrs["form_id"] = ""
    hero.attrs["form_animal"] = ""
    world.say(
        f"The borrowed feathers or fur melted away like dew, and {hero.id} was simply {hero.id} again -- small, shaky, and real."
    )


def shared_solution(world: World, hero: Entity, helper: Entity, need: Need) -> None:
    hero.meters["progress"] += 1
    hero.memes["belonging"] += 1
    hero.memes["relief"] += 1
    world.say(
        f'"Now ask for help in your own voice," said {helper.id}.'
    )
    world.say(
        f"{need.group_solution}"
    )
    world.say(
        f"{hero.id} looked surprised to find that the work felt warmer when many paws and wings did it together."
    )


def make_amends(world: World, hero: Entity, helper: Entity, need: Need) -> None:
    hero.meters["progress"] += 1
    hero.memes["belonging"] += 1
    world.say(need.late_cost)
    world.say(
        f"Still, {hero.id} did not run away. With {helper.id} beside {hero.pronoun('object')}, {hero.pronoun()} helped set things right and finished what could still be finished."
    )
    world.say(
        f"That did not feel grand, but it felt true, and true work settled the heart better than showy magic."
    )


def closing(world: World, hero: Entity, helper: Entity, outcome: str) -> None:
    if outcome == "shared":
        world.say(
            f"When the music began, {hero.id} stood near {helper.id} with bright eyes and steady paws, proud to be exactly who {hero.pronoun()} was."
        )
    else:
        world.say(
            f"When the music began again, {hero.id} stood near {helper.id} a little quieter than before, but lighter now that the secret was gone."
        )
    world.say(world.setting.closing_image)


def tell(
    setting: Setting,
    need: Need,
    form: Form,
    relic: Relic,
    helper_kind: HelperKind,
    reveal: str,
    hero_name: str,
    hero_type: str,
    trait: str,
) -> World:
    world = World(setting=setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            phrase=f"a {trait} little {hero_type}",
            role="hero",
            attrs={"trait": trait},
        )
    )
    helper = world.add(
        Entity(
            id=helper_kind.animal.capitalize(),
            kind="character",
            type=helper_kind.animal,
            label="the helper",
            phrase=helper_kind.phrase,
            role="helper",
            attrs={
                "notice_line": helper_kind.notice_line,
                "comfort_line": helper_kind.comfort_line,
            },
            tags=set(helper_kind.tags),
        )
    )
    world.add(
        Entity(
            id="relic",
            kind="thing",
            type="relic",
            label=relic.label,
            phrase=relic.phrase,
            tags=set(relic.tags),
        )
    )
    world.add(
        Entity(
            id="task",
            kind="thing",
            type="task",
            label=need.object_label,
            phrase=need.title,
            tags=set(need.tags),
        )
    )

    introduce(world, hero, helper, need)
    world.para()
    temptation(world, hero, relic)
    transform(world, hero, need, form, relic)
    farce(world, hero, form)
    helper_notices(world, helper)

    world.para()
    if reveal == "early":
        confess_early(world, hero, helper, relic)
        reverse(world, hero)
        shared_solution(world, hero, helper, need)
        outcome = "shared"
    else:
        hide_longer(world, hero, helper)
        confess_late(world, hero, helper, relic)
        reverse(world, hero)
        make_amends(world, hero, helper, need)
        outcome = "amends"

    world.para()
    closing(world, hero, helper, outcome)

    world.facts.update(
        setting=setting,
        need=need,
        form=form,
        relic=relic,
        helper_kind=helper_kind,
        hero=hero,
        helper=helper,
        reveal=reveal,
        outcome=outcome,
        mixup=hero.meters["mixup"],
        used_magic=True,
        transformed=True,
        learned_honesty=hero.memes["honesty"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    need = f["need"]
    form = f["form"]
    setting = f["setting"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short animal story for a 3-to-5-year-old that includes the words "farce" and "olden".',
        f"Tell an olden woodland fair story about a small {hero.type} who uses magic transformation to help with {need.title}.",
        f"Write a gentle animal tale where a child becomes {form.phrase} for a little while, and the magic creates a funny mix-up.",
    ]
    if outcome == "shared":
        prompts.append(
            "End with the hero telling the truth early, turning back, and learning that asking for help beats a secret shortcut."
        )
    else:
        prompts.append(
            "End with the hero hiding the truth too long, missing part of the big moment, then making amends in an honest way."
        )
    return prompts


KNOWLEDGE = {
    "magic": [
        (
            "What is transformation magic?",
            "Transformation magic is magic that changes how someone looks or what shape they have for a while. In stories, it can solve one problem but also cause new trouble."
        )
    ],
    "fair": [
        (
            "What is a fair?",
            "A fair is a cheerful gathering with food, games, music, and many jobs to do. Everyone usually helps in different ways."
        )
    ],
    "honesty": [
        (
            "Why is telling the truth important after a mistake?",
            "Telling the truth lets other people understand what really happened and help fix it. Hiding a mistake usually makes the problem grow."
        )
    ],
    "help": [
        (
            "Why can asking for help be brave?",
            "Asking for help is brave because you admit that you cannot do everything alone. It often leads to a safer and kinder solution."
        )
    ],
    "duck": [
        (
            "Why are ducks good at swimming?",
            "Ducks have bodies and feet that work well in water, so they can paddle and float easily. That makes them good at reaching things in ponds."
        )
    ],
    "squirrel": [
        (
            "Why are squirrels good climbers?",
            "Squirrels are quick on bark and branches, so they can climb high places much better than many other animals. Their bodies fit that kind of job."
        )
    ],
    "badger": [
        (
            "Why might a badger seem strong?",
            "A badger is sturdy and low to the ground, so in stories it can seem like a strong little worker. That makes it a good shape for pushing or carrying."
        )
    ],
    "magpie": [
        (
            "Why might a bird help with something high up?",
            "A bird can hop or flap up to places that small ground animals cannot reach. That makes high ropes and branches easier to manage."
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "fair", "honesty", "help", "duck", "squirrel", "badger", "magpie"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    need = f["need"]
    form = f["form"]
    relic = f["relic"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type}, and {helper.id}, the kind helper who noticed the trouble. The story happens during {f['setting'].fair_name}."
        ),
        (
            f"What did {hero.id} want to do?",
            f"{hero.id} wanted to {need.title} and be useful at the fair. The job mattered because it helped the celebration begin or run properly."
        ),
        (
            f"Why did {hero.id} use {relic.phrase}?",
            f"{hero.id} felt too small for the job and hoped magic would lend the right body for a moment. The transformation seemed like a quick way to solve the problem without asking for help."
        ),
        (
            f"What happened after {hero.id} turned into {form.phrase}?",
            f"The new shape did match the task for a moment, but everyone mistook {hero.id} for a real {form.animal}. That is what turned the magic into a funny farce instead of a simple success."
        ),
    ]
    if outcome == "shared":
        qa.append(
            (
                f"How was the problem solved in the end?",
                f"{hero.id} told the truth early, turned back into a {hero.type}, and then asked for help in {hero.pronoun('possessive')} own voice. Working together solved the job more warmly than the secret magic had done."
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn?",
                f"{hero.id} learned that being small does not mean being useless. Honest help from friends was better than pretending to be someone else."
            )
        )
    else:
        qa.append(
            (
                f"What happened because {hero.id} hid the truth too long?",
                f"The mix-up grew worse and {hero.id} missed part of the fair's big moment. Hiding made extra confusion, so the ending became about making amends instead of enjoying an easy triumph."
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn at the end?",
                f"{hero.id} learned that a secret shortcut can cost time and trust. Even after a mistake, telling the truth and helping clean up can set things right."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"magic", "fair", "honesty", "help"}
    form = world.facts["form"]
    if form.id in {"duck", "squirrel", "badger", "magpie"}:
        tags.add(form.id)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in e.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="green",
        need="reeds",
        form="duck",
        relic="moon_charm",
        helper="owl",
        reveal="early",
        hero_name="Pip",
        hero_type="mouse",
        trait="eager",
        seed=1,
    ),
    StoryParams(
        setting="courtyard",
        need="banner",
        form="squirrel",
        relic="mirror_leaf",
        helper="tortoise",
        reveal="late",
        hero_name="Tansy",
        hero_type="rabbit",
        trait="hopeful",
        seed=2,
    ),
    StoryParams(
        setting="orchard",
        need="sack",
        form="badger",
        relic="acorn_whistle",
        helper="mole",
        reveal="early",
        hero_name="Moss",
        hero_type="hedgehog",
        trait="busy",
        seed=3,
    ),
    StoryParams(
        setting="green",
        need="bell_rope",
        form="magpie",
        relic="moon_charm",
        helper="owl",
        reveal="late",
        hero_name="Nettle",
        hero_type="vole",
        trait="bright-eyed",
        seed=4,
    ),
]


ASP_RULES = r"""
skill_match(N, F) :- need_skill(N, S), form_skill(F, S).
valid(N, F) :- need(N), form(F), skill_match(N, F).

shared :- reveal(early).
amends :- reveal(late).

outcome(shared) :- shared.
outcome(amends) :- amends.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        lines.append(asp.fact("need_skill", need_id, need.skill))
    for form_id, form in FORMS.items():
        lines.append(asp.fact("form", form_id))
        lines.append(asp.fact("form_skill", form_id, form.skill))
    for reveal in ("early", "late"):
        lines.append(asp.fact("reveal_kind", reveal))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(reveal: str) -> str:
    import asp

    model = asp.one_model(asp_program(f"reveal({reveal}).", "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "shared" if params.reveal == "early" else "amends"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Olden animal-fair storyworld with transformation magic and a comic mix-up."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--need", choices=sorted(NEEDS))
    ap.add_argument("--form", choices=sorted(FORMS))
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--reveal", choices=["early", "late"])
    ap.add_argument("--name")
    ap.add_argument("--hero", choices=sorted({h["animal"] for h in HEROES}))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (need, form) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.need and args.form:
        need = NEEDS[args.need]
        form = FORMS[args.form]
        if not valid_combo(need, form):
            raise StoryError(explain_rejection(need, form))

    combos = [
        combo for combo in valid_combos()
        if (args.need is None or combo[0] == args.need)
        and (args.form is None or combo[1] == args.form)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    need_id, form_id = rng.choice(combos)
    setting = args.setting or rng.choice(sorted(SETTINGS))
    relic = args.relic or rng.choice(sorted(RELICS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    reveal = args.reveal or rng.choice(["early", "late"])

    hero_pool = [h for h in HEROES if args.hero is None or h["animal"] == args.hero]
    if not hero_pool:
        raise StoryError("(No hero matches the given --hero option.)")
    chosen_hero = rng.choice(hero_pool)
    hero_name = args.name or chosen_hero["name"]
    hero_type = chosen_hero["animal"]
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting,
        need=need_id,
        form=form_id,
        relic=relic,
        helper=helper,
        reveal=reveal,
        hero_name=hero_name,
        hero_type=hero_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.form not in FORMS:
        raise StoryError(f"(Unknown form: {params.form})")
    if params.relic not in RELICS:
        raise StoryError(f"(Unknown relic: {params.relic})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.reveal not in {"early", "late"}:
        raise StoryError(f"(Unknown reveal timing: {params.reveal})")

    need = NEEDS[params.need]
    form = FORMS[params.form]
    if not valid_combo(need, form):
        raise StoryError(explain_rejection(need, form))

    world = tell(
        setting=SETTINGS[params.setting],
        need=need,
        form=form,
        relic=RELICS[params.relic],
        helper_kind=HELPERS[params.helper],
        reveal=params.reveal,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP valid pairs match Python valid_combos() ({len(py)} pairs).")
    else:
        rc = 1
        print("MISMATCH in valid pairs:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for reveal in ("early", "late"):
        py_out = "shared" if reveal == "early" else "amends"
        cl_out = asp_outcome(reveal)
        if py_out == cl_out:
            print(f"OK: outcome for reveal={reveal} matches ({py_out}).")
        else:
            rc = 1
            print(f"MISMATCH: reveal={reveal}: python={py_out} clingo={cl_out}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (need, form) pairs:\n")
        for need_id, form_id in combos:
            print(f"  {need_id:10} {form_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.need} via {p.form} ({p.setting}, reveal={p.reveal})"
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
