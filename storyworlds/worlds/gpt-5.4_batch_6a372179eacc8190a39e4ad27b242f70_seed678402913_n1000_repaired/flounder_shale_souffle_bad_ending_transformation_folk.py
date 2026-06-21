#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flounder_shale_souffle_bad_ending_transformation_folk.py

A standalone storyworld for a small folk-tale domain built from the seed words
"flounder", "shale", and "souffle", with a bad ending and a magical
transformation.

Premise
-------
On a shale shore, a child frees a talking flounder and receives a pinch of sea
magic for one humble supper. If the child uses that gift for vanity or greed,
the souffle rises beyond need and the sea answers with a transformation.

This world prefers a tight, plausible moral logic over broad coverage:
each wish matches only the transformation that fits its vice.

Run it
------
python storyworlds/worlds/gpt-5.4/flounder_shale_souffle_bad_ending_transformation_folk.py
python storyworlds/worlds/gpt-5.4/flounder_shale_souffle_bad_ending_transformation_folk.py --wish gold
python storyworlds/worlds/gpt-5.4/flounder_shale_souffle_bad_ending_transformation_folk.py --transformation gull
python storyworlds/worlds/gpt-5.4/flounder_shale_souffle_bad_ending_transformation_folk.py --all
python storyworlds/worlds/gpt-5.4/flounder_shale_souffle_bad_ending_transformation_folk.py --qa --json
python storyworlds/worlds/gpt-5.4/flounder_shale_souffle_bad_ending_transformation_folk.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the nested worlds/gpt-5.4/ directory.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Shore:
    id: str
    label: str
    opening: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Wish:
    id: str
    label: str
    boast: str
    harm: str
    vice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    form_name: str
    vice: str
    strike: str
    ending: str
    qa: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_swelling(world: World) -> list[str]:
    out: list[str] = []
    souffle = world.entities.get("souffle")
    if not souffle or souffle.meters["sea_breath"] < THRESHOLD or souffle.meters["wish"] < THRESHOLD:
        return out
    sig = ("swelling",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    souffle.meters["rising"] += 2
    hero = world.get("hero")
    hero.memes["wonder"] += 1
    hero.memes["greed"] += 1
    out.append("__rise__")
    return out


def _r_omen(world: World) -> list[str]:
    out: list[str] = []
    souffle = world.entities.get("souffle")
    if not souffle or souffle.meters["rising"] < 2:
        return out
    sig = ("omen",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    house = world.get("house")
    house.meters["unease"] += 1
    hero = world.get("hero")
    hero.memes["warning"] += 1
    out.append("__omen__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    souffle = world.entities.get("souffle")
    if not hero or not souffle:
        return out
    if souffle.meters["rising"] < 2 or hero.meters["claimed"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["transformed"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule(name="swelling", tag="physical", apply=_r_swelling),
    Rule(name="omen", tag="folk", apply=_r_omen),
    Rule(name="transform", tag="folk", apply=_r_transform),
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
        for sent in produced:
            world.say(sent)
    return produced


def moral_match(wish: Wish, transformation: Transformation) -> bool:
    return wish.vice == transformation.vice


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for shore_id in SHORES:
        for wish_id, wish in WISHES.items():
            for trans_id, trans in TRANSFORMATIONS.items():
                if moral_match(wish, trans):
                    combos.append((shore_id, wish_id, trans_id))
    return combos


def explain_rejection(wish: Wish, transformation: Transformation) -> str:
    return (
        f"(No story: the wish '{wish.label}' carries {wish.vice}, but the "
        f"transformation '{transformation.form_name}' punishes {transformation.vice}. "
        f"This folk tale only allows punishments that fit the vice.)"
    )


def introduce(world: World, hero: Entity, elder: Entity, shore: Shore) -> None:
    trait = hero.traits[0] if hero.traits else "restless"
    world.say(
        f"In a village beside {shore.label}, there lived a {trait} child named "
        f"{hero.id}. {shore.opening}"
    )
    world.say(
        f"{hero.id} shared a low cottage with {hero.pronoun('possessive')} "
        f"{elder.label_word}, and that evening they had only a little butter, "
        f"three eggs, and enough flour for one small souffle."
    )


def shore_walk(world: World, hero: Entity, shore: Shore) -> None:
    world.say(
        f"At dusk {hero.id} went down {shore.path} to gather a few dry twigs for the fire. "
        f"There, among the shale stones, a flounder lay gasping in a trapped pool."
    )


def rescue_flounder(world: World, hero: Entity) -> None:
    hero.memes["kindness"] += 1
    fish = world.get("flounder")
    fish.memes["gratitude"] += 1
    world.say(
        f"{hero.id} slid both hands under the fish and set it back into a deeper stream. "
        f"The flounder blinked one gold eye and spoke like water under ice."
    )
    world.say(
        f'"For kindness," said the flounder, "I give you one breath of the sea. '
        f'Put it into your humble souffle, and it will rise enough for supper. '
        f'But do not ask it to rise for pride, or the tide will ask something of you."'
    )


def return_home(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f"{hero.id} hurried home and told {elder.label_word} what had happened. "
        f"{elder.label_word.capitalize()} crossed {elder.pronoun('possessive')} heart and said "
        f'the sea keeps sharp accounts, even when it gives gifts.'
    )


def mix_souffle(world: World, hero: Entity, wish: Wish) -> None:
    souffle = world.get("souffle")
    souffle.meters["mixed"] += 1
    world.say(
        f"When the eggs were beaten and the oven glowed red, {hero.id} tipped the sea-breath "
        f"into the bowl. The batter shimmered pale as moon foam."
    )
    hero.memes["desire"] += 1
    world.say(
        f'Yet as the dish went into the oven, a hot wish rose in {hero.id}\'s chest. '
        f'{wish.boast}'
    )
    souffle.meters["sea_breath"] += 1
    souffle.meters["wish"] += 1
    world.facts["wish_spoken"] = True
    propagate(world, narrate=False)


def omen(world: World, hero: Entity, elder: Entity, wish: Wish) -> None:
    world.say(
        f"The little souffle did not stop at the rim. It climbed higher and higher, "
        f"round and trembling, until it brushed the oven roof and breathed out "
        f"{wish.harm}."
    )
    world.say(
        f'{elder.label_word.capitalize()} stepped back. "Enough," {elder.pronoun()} whispered. '
        f'"The flounder asked for supper, not boasting."'
    )
    hero.memes["warning"] += 1


def claim_gift(world: World, hero: Entity, wish: Wish) -> None:
    hero.meters["claimed"] += 1
    hero.memes["greed"] += 1
    world.say(
        f"But the sight of it made {hero.id}'s heart run ahead of wisdom. "
        f'{hero.pronoun().capitalize()} stretched out both hands and cried, "{wish.label}!"'
    )
    propagate(world, narrate=False)


def transform(world: World, hero: Entity, transformation: Transformation) -> None:
    hero.attrs["form"] = transformation.form_name
    world.say(transformation.strike.replace("{name}", hero.id))
    world.say(transformation.ending)


def tell(
    shore: Shore,
    wish: Wish,
    transformation: Transformation,
    *,
    name: str = "Mara",
    gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "patient",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="hero",
            traits=[trait],
            tags={"child"},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            tags={"adult"},
        )
    )
    world.add(
        Entity(
            id="flounder",
            kind="character",
            type="fish",
            label="flounder",
            phrase="the talking flounder",
            role="helper",
            tags={"flounder", "magic"},
        )
    )
    world.add(
        Entity(
            id="souffle",
            kind="thing",
            type="food",
            label="souffle",
            phrase="the little supper souffle",
            tags={"souffle"},
        )
    )
    world.add(
        Entity(
            id="house",
            kind="thing",
            type="cottage",
            label="cottage",
        )
    )

    introduce(world, hero, elder, shore)
    shore_walk(world, hero, shore)

    world.para()
    rescue_flounder(world, hero)
    return_home(world, hero, elder)

    world.para()
    mix_souffle(world, hero, wish)
    omen(world, hero, elder, wish)

    world.para()
    claim_gift(world, hero, wish)
    transform(world, hero, transformation)

    world.facts.update(
        hero=hero,
        elder=elder,
        shore=shore,
        wish=wish,
        transformation=transformation,
        bad_ending=True,
        transformed=hero.meters["transformed"] >= THRESHOLD,
        final_form=hero.attrs.get("form", ""),
    )
    return world


SHORES = {
    "north_shale": Shore(
        id="north_shale",
        label="the North Shale Shore",
        opening="All day the waves worried the black shale into shining flakes, and the wind smelled of salt and peat.",
        path="the narrow goat path above the black shale beach",
        tags={"shale", "shore"},
    ),
    "gray_cove": Shore(
        id="gray_cove",
        label="Gray Cove",
        opening="Below the cliffs, the shale banks clicked softly whenever the tide turned.",
        path="the steep lane that ended at the shale cove",
        tags={"shale", "shore"},
    ),
    "widows_steps": Shore(
        id="widows_steps",
        label="Widow's Steps",
        opening="There the sea gnawed at layered shale and left dark shelves gleaming after sunset.",
        path="the weathered steps that led down to the shale ledges",
        tags={"shale", "shore"},
    ),
}

WISHES = {
    "praise": Wish(
        id="praise",
        label="Let all the village praise my souffle!",
        boast="\"Let it rise so high that all the village will praise my souffle,\" thought the child.",
        harm="a warm, vain smell that filled the cottage like a trumpet note",
        vice="vanity",
        tags={"pride", "souffle"},
    ),
    "gold": Wish(
        id="gold",
        label="Turn this souffle to gold for me!",
        boast="\"Let it rise and turn to gold, so we shall never be poor again,\" thought the child.",
        harm="a yellow gleam that made every cracked plate look hungry",
        vice="greed",
        tags={"gold", "souffle"},
    ),
    "more": Wish(
        id="more",
        label="Make this one souffle feed the whole fair and still leave me the first slice!",
        boast="\"Let one dish feed the whole fair, and still let the first rich slice be mine,\" thought the child.",
        harm="a salty steam that rolled through the room like a feast-day drum",
        vice="gluttony",
        tags={"feast", "souffle"},
    ),
}

TRANSFORMATIONS = {
    "gull": Transformation(
        id="gull",
        form_name="a gray gull",
        vice="vanity",
        strike="{name} felt a gust strike from inside the swelling crust. Arms flew white and narrow, the voice cracked into a hungry cry, and in a blink {name} had become a gray gull beating at the rafters.",
        ending="Out through the door the bird wheeled into the dusk, circling above the village and crying for praise that never satisfied its belly. And to this day, folk say the loudest gulls over the shale shore are children who wanted applause more than supper.",
        qa="The child became a gray gull and flew off crying above the shore.",
        tags={"gull", "transformation"},
    ),
    "shale": Transformation(
        id="shale",
        form_name="a shale pillar",
        vice="greed",
        strike="The golden shine hardened at once. {name}'s feet rooted to the floor, the skin darkened to layers and seams, and before the elder could speak again there stood a shale pillar shaped like a child, cold and still beside the oven.",
        ending="When dawn came, the tide-wind whistled through the cracks of that stone form, and the cottage never felt warm again. People afterward said that greed had made a heart as hard as shale, and the sea had only shown the truth.",
        qa="The child hardened into a shale pillar and stayed in the cottage like stone.",
        tags={"shale", "transformation"},
    ),
    "flounder": Transformation(
        id="flounder",
        form_name="a flounder",
        vice="gluttony",
        strike="At once the great souffle sank flat as a tide pool. {name}'s legs folded away, the mouth drew sideways, and with one slippery thump there lay a flounder on the tiles, blinking in terror at the very oven that had tempted {name}.",
        ending="The elder carried the fish back to the sea, but no human words came from it again. Fisherfolk still mutter that any flounder found staring too long at a baking window once asked for more than one stomach should hold.",
        qa="The child became a flounder and was carried back to the sea.",
        tags={"flounder", "transformation"},
    ),
}


KNOWLEDGE = {
    "flounder": [
        (
            "What is a flounder?",
            "A flounder is a flat fish that lives near the bottom of the sea. Both of its eyes end up on one side of its head as it grows."
        )
    ],
    "shale": [
        (
            "What is shale?",
            "Shale is a kind of rock made from thin layers pressed together. It often breaks into flat, flaky pieces."
        )
    ],
    "souffle": [
        (
            "What is a souffle?",
            "A souffle is a light baked dish made with whipped eggs so it puffs up in the oven. It can fall again if the air leaves it."
        )
    ],
    "greed": [
        (
            "What is greed?",
            "Greed is wanting more than you truly need, especially when you keep grabbing even after enough has been given."
        )
    ],
    "vanity": [
        (
            "What is vanity?",
            "Vanity is caring too much about praise and showing off. It makes a person chase claps instead of wisdom."
        )
    ],
    "gluttony": [
        (
            "What does it mean to be gluttonous?",
            "It means wanting too much food or too much for yourself, instead of taking a fair and sensible share."
        )
    ],
    "folk_magic": [
        (
            "Why do folk tales warn people about magic gifts?",
            "Because folk tales often teach that a gift with a rule must be used carefully. Breaking the rule shows your character, and the magic answers that choice."
        )
    ],
}
KNOWLEDGE_ORDER = ["flounder", "shale", "souffle", "vanity", "greed", "gluttony", "folk_magic"]


@dataclass
class StoryParams:
    shore: str
    wish: str
    transformation: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        shore="north_shale",
        wish="praise",
        transformation="gull",
        name="Mara",
        gender="girl",
        elder="grandmother",
        trait="patient",
    ),
    StoryParams(
        shore="gray_cove",
        wish="gold",
        transformation="shale",
        name="Tobin",
        gender="boy",
        elder="grandfather",
        trait="quick-handed",
    ),
    StoryParams(
        shore="widows_steps",
        wish="more",
        transformation="flounder",
        name="Elsie",
        gender="girl",
        elder="grandmother",
        trait="restless",
    ),
]

GIRL_NAMES = ["Mara", "Elsie", "Nell", "Ivy", "Bess", "Ruth", "Ada", "May"]
BOY_NAMES = ["Tobin", "Ewan", "Rowan", "Finn", "Hugh", "Giles", "Ned", "Orrin"]
TRAITS = ["patient", "restless", "quick-handed", "bright-eyed", "solemn", "eager"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    wish = f["wish"]
    transformation = f["transformation"]
    shore = f["shore"]
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the words "flounder", "shale", and "souffle", and ends badly with a transformation.',
        f"Tell a coastal folk tale where a child named {hero.id} receives sea magic from a flounder on {shore.label}, but uses it for {wish.vice} and becomes {transformation.form_name}.",
        f'Write a moral tale about a magical souffle gift that should have been used for supper, not boasting, and end with the warning carried in the child\'s transformation.',
    ]


def pair_article(form_name: str) -> str:
    if form_name.startswith(("a ", "an ")):
        return form_name
    if form_name[0].lower() in "aeiou":
        return f"an {form_name}"
    return f"a {form_name}"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    shore = f["shore"]
    wish = f["wish"]
    transformation = f["transformation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who lived beside {shore.label}, and {hero.pronoun('possessive')} {elder.label_word}. A talking flounder also changes the child's fate."
        ),
        (
            "Why did the flounder help the child?",
            f"The flounder helped because {hero.id} lifted it from a trapped pool and set it back into deeper water. The gift came as thanks for kindness."
        ),
        (
            "What warning did the flounder give?",
            f"The flounder said the sea-breath was for one humble souffle and one supper. It warned the child not to use the magic for pride."
        ),
        (
            "What went wrong with the souffle?",
            f"The child put the sea-breath into the batter, then asked for more than was needed. Because the wish came from {wish.vice}, the souffle rose in a strange, dangerous way instead of staying a simple meal."
        ),
        (
            "Why did the ending turn bad?",
            f"The ending turned bad because {hero.id} reached past enough and tried to claim magic for {wish.label.lower()} The folk-tale punishment fits the fault, so the sea changed the child instead of feeding the house."
        ),
        (
            f"What did {hero.id} become?",
            f"{transformation.qa} This proves the warning was real and that the sea kept its sharp account."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"flounder", "shale", "souffle", "folk_magic", f["wish"].vice}
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
moral_match(W, T) :- wish(W), transformation(T), vice_of_wish(W, V), vice_of_transformation(T, V).
valid(S, W, T)    :- shore(S), moral_match(W, T).

outcome(T)        :- chosen_wish(W), chosen_transformation(T), moral_match(W, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for shore_id in SHORES:
        lines.append(asp.fact("shore", shore_id))
    for wish_id, wish in WISHES.items():
        lines.append(asp.fact("wish", wish_id))
        lines.append(asp.fact("vice_of_wish", wish_id, wish.vice))
    for trans_id, trans in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", trans_id))
        lines.append(asp.fact("vice_of_transformation", trans_id, trans.vice))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_wish", params.wish),
            asp.fact("chosen_transformation", params.transformation),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a rescued flounder, a shale shore, a magical souffle, and a bad transforming end."
    )
    ap.add_argument("--shore", choices=SHORES)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (shore, wish, transformation) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run generation smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.wish and args.transformation:
        wish = WISHES[args.wish]
        transformation = TRANSFORMATIONS[args.transformation]
        if not moral_match(wish, transformation):
            raise StoryError(explain_rejection(wish, transformation))

    combos = [
        combo
        for combo in valid_combos()
        if (args.shore is None or combo[0] == args.shore)
        and (args.wish is None or combo[1] == args.wish)
        and (args.transformation is None or combo[2] == args.transformation)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shore_id, wish_id, trans_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        shore=shore_id,
        wish=wish_id,
        transformation=trans_id,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shore not in SHORES:
        raise StoryError(f"(Unknown shore: {params.shore})")
    if params.wish not in WISHES:
        raise StoryError(f"(Unknown wish: {params.wish})")
    if params.transformation not in TRANSFORMATIONS:
        raise StoryError(f"(Unknown transformation: {params.transformation})")

    wish = WISHES[params.wish]
    transformation = TRANSFORMATIONS[params.transformation]
    if not moral_match(wish, transformation):
        raise StoryError(explain_rejection(wish, transformation))

    world = tell(
        SHORES[params.shore],
        wish,
        transformation,
        name=params.name,
        gender=params.gender,
        elder_type=params.elder,
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
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    for params in CURATED:
        asp_result = asp_outcome(params)
        if asp_result != params.transformation:
            rc = 1
            print(
                f"MISMATCH in outcome for {params.wish}/{params.transformation}: "
                f"asp={asp_result} python={params.transformation}"
            )

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(7)))
    except StoryError as err:
        rc = 1
        print(f"SMOKE setup failed: {err}")
        smoke_cases = list(CURATED)

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            if sample.world is None:
                raise StoryError("missing world model on sample")
            print(f"OK: smoke story {idx} generated ({params.name}, {params.wish}, {params.transformation}).")
        except Exception as err:  # pragma: no cover - defensive verify path
            rc = 1
            print(f"SMOKE generation failed for {params}: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shore, wish, transformation) combos:\n")
        for shore_id, wish_id, trans_id in combos:
            print(f"  {shore_id:12} {wish_id:8} {trans_id}")
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
            header = f"### {p.name}: {p.wish} at {p.shore} -> {p.transformation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
