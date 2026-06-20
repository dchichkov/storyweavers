#!/usr/bin/env python3
"""A mythic dentist-office storyworld about a candle, vivid signs, and moral change.

Seed:
    Words: candle, vivid
    Setting: dentist office
    Features: Moral Value, Transformation, Misunderstanding
    Style: Myth

Source tale used for the simulation:
    Long ago, people said every tooth held a little moon inside it, and the old
    dentist office kept a candle so those moons would not lose heart. A child
    sees a vivid sign in the office and misunderstands it as a curse or beast.
    The sign is not punishment at all. It is a crooked picture cast by fear and
    a small hidden problem. When the child chooses the right moral act such as
    truth, trust, or stillness, the dentist helps reveal the real cause, the
    misunderstanding dissolves, and the candle wax transforms into a gentle
    token that proves fear has become wisdom.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass(frozen=True)
class Chamber:
    id: str
    label: str
    scene: str
    entry_line: str
    exit_line: str
    candle_line: str
    affords: set[str]
    tags: set[str]


@dataclass(frozen=True)
class Omen:
    id: str
    label: str
    vision: str
    mistaken_belief: str
    hidden_cause: str
    need: str
    transform_kind: str
    transform_sentence: str
    dentist_reveal: str
    final_image: str
    tags: set[str]


@dataclass(frozen=True)
class Virtue:
    id: str
    label: str
    grants: str
    action: str
    teaching: str
    dentist_help: str
    moral: str
    tags: set[str]


@dataclass(frozen=True)
class HeroSeed:
    id: str
    name: str
    gender: str
    trait: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: Optional[str] = None
    meters: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    states: set[str] = field(default_factory=set)
    note: str = ""


class World:
    def __init__(self, params: "StoryParams") -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.events: list[str] = []
        self.facts: dict[str, str] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def break_para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event: str) -> None:
        self.events.append(event)

    def render(self) -> str:
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)

    def trace(self) -> str:
        lines = [
            (
                "params: "
                f"chamber={self.params.chamber} omen={self.params.omen} "
                f"virtue={self.params.virtue} hero={self.params.hero}"
            ),
            f"facts: {self.facts}",
            "events:",
        ]
        if self.events:
            for event in self.events:
                lines.append(f"  - {event}")
        else:
            lines.append("  - none")
        lines.append("entities:")
        for ent in self.entities.values():
            bits = [f"  {ent.id} | {ent.kind} | {ent.label}"]
            if ent.location:
                bits.append(f"location={ent.location}")
            if ent.states:
                bits.append(f"states={sorted(ent.states)}")
            if ent.note:
                bits.append(f"note={ent.note}")
            lines.append(" | ".join(bits))
            if ent.meters:
                lines.append(f"    meters={dict(ent.meters)}")
            if ent.memes:
                lines.append(f"    memes={dict(ent.memes)}")
        return "\n".join(lines)


@dataclass(frozen=True)
class StoryParams:
    chamber: str
    omen: str
    virtue: str
    hero: str
    seed: Optional[int] = None


CHAMBERS = {
    "mirror_chair": Chamber(
        "mirror_chair",
        "the mirror chair",
        "the tall enamel chair beside the silver mouth mirror",
        "climbed into the tall enamel chair beside the silver mouth mirror",
        "stepped down from the chair",
        "Beside the chair, a vivid candle burned in a blue-glazed cup, and its flame moved as steadily as a watchful eye.",
        {"lion_shadow"},
        {"mirror", "chair", "candle"},
    ),
    "basin_altar": Chamber(
        "basin_altar",
        "the rinse basin",
        "the round rinse basin under a shelf of mint cups",
        "stood beside the round rinse basin under a shelf of mint cups",
        "set the cup down and stepped back from the basin",
        "A vivid candle stood near the basin, and its gold light trembled across the water like a tiny sunrise.",
        {"ruby_basin"},
        {"basin", "water", "candle"},
    ),
    "screen_niche": Chamber(
        "screen_niche",
        "the shadow screen",
        "the little shadow screen where tooth pictures were shown",
        "sat before the little shadow screen where tooth pictures were shown",
        "slid gently down from the picture stool",
        "At the foot of the screen, a vivid candle made a soft white pool on its brass saucer.",
        {"mountain_shadow"},
        {"screen", "xray", "candle"},
    ),
}


OMENS = {
    "lion_shadow": Omen(
        "lion_shadow",
        "the lion shadow",
        "the candle threw a wide lion jaw across the tiny dentist mirror",
        "the Tooth Lion had come to bite because a secret had been hidden",
        "a sticky fig seed was caught near the back tooth, and the mirror stem crossed the flame at just the wrong angle",
        "truth",
        "sleeping_lion",
        "At the candle's foot, a fold of wax softened, curled, and became a tiny white lion lying down with its teeth tucked away.",
        "Doctor Sen lifted the seed free with a small hook and turned the mirror so the fierce jaw broke apart into plain light and silver.",
        "The little wax lion slept beside the clean mirror, and no shadow in the room looked hungry anymore.",
        {"mirror", "shadow", "truth", "lion"},
    ),
    "ruby_basin": Omen(
        "ruby_basin",
        "the ruby basin",
        "the rinse water glowed red under the candle as if a bright jewel had melted into it",
        "a tooth curse had opened and the basin was catching its blood",
        "pomegranate syrup still colored the child's tongue and gums, so the water only borrowed that color for a moment",
        "trust",
        "pearl_drop",
        "One round bead of wax cooled into a pearl-white drop on the tray, bright and still as a tear that no longer needed to fall.",
        "Doctor Sen mixed mint water, let the child rinse slowly, and showed how the red glow faded as soon as the syrup washed clean away.",
        "The basin held clear water at last, and the wax pearl gleamed beside it like a promise of calm.",
        {"basin", "water", "trust", "red"},
    ),
    "mountain_shadow": Omen(
        "mountain_shadow",
        "the mountain tooth",
        "a tooth picture on the screen rose up like a cracked white mountain",
        "a giant tooth spirit was splitting the jaw from inside",
        "the first picture had bent when the child wriggled, and the real tooth was only a baby tooth ready to come loose in its season",
        "stillness",
        "crescent_boat",
        "The wax along the saucer stretched into a little crescent boat carrying a white tooth-seed in its middle.",
        "Doctor Sen took a second picture while the child sat still as stone, and the broken mountain settled into one small tooth ready for its ordinary journey.",
        "The wax boat stood by the quiet screen, and the once-terrible mountain had become a gentle leaving.",
        {"screen", "xray", "stillness", "mountain"},
    ),
}


VIRTUES = {
    "speak_truth": Virtue(
        "speak_truth",
        "speak the plain truth",
        "truth",
        "opened a brave mouth and admitted the sweet fig bun eaten on the walk to the office",
        '"The candle of teeth dislikes hidden fear more than sticky crumbs," Doctor Sen said. "Speak plainly, and the room will show its true shape."',
        "Then Doctor Sen cleaned the tooth with careful hands instead of haste.",
        "truth makes frightening signs smaller, because it gives them their real name",
        {"truth", "speech", "moral"},
    ),
    "accept_help": Virtue(
        "accept_help",
        "accept gentle help",
        "trust",
        "held the cup with both hands and trusted the slow rinse instead of pulling away",
        '"Not every red sign is a wound," Doctor Sen said. "Sometimes trust is the bridge that lets us see clearly."',
        "Then Doctor Sen guided the rinse one calm breath at a time.",
        "trust turns panic into understanding, because help can wash away what fear makes large",
        {"trust", "help", "moral"},
    ),
    "hold_still": Virtue(
        "hold_still",
        "hold still with courage",
        "stillness",
        "pressed both feet to the chair rung and stayed still long enough for a true picture to be made",
        '"A shaking body makes a shaking omen," Doctor Sen said. "Stillness is a kind of courage, and courage lets truth stand still."',
        "Then Doctor Sen made a second picture in the quiet.",
        "stillness can be brave, because patience lets a frightened mind see what is really there",
        {"stillness", "courage", "moral"},
    ),
}


HEROES = {
    "mira": HeroSeed("mira", "Mira", "girl", "thoughtful"),
    "theo": HeroSeed("theo", "Theo", "boy", "restless"),
    "lina": HeroSeed("lina", "Lina", "girl", "bright-eyed"),
    "finn": HeroSeed("finn", "Finn", "boy", "careful"),
}


CURATED = [
    StoryParams("mirror_chair", "lion_shadow", "speak_truth", "mira", 901),
    StoryParams("basin_altar", "ruby_basin", "accept_help", "theo", 902),
    StoryParams("screen_niche", "mountain_shadow", "hold_still", "lina", 903),
    StoryParams("mirror_chair", "lion_shadow", "speak_truth", "finn", 904),
]


NEED_EXPLANATIONS = {
    "truth": "the child needed to name the hidden cause plainly before the room could stop looking fierce",
    "trust": "the child needed to accept careful help before the red glow could be understood",
    "stillness": "the child needed one calm moment before the shadow could become a true picture",
}


def pronoun_subject(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def pronoun_possessive(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def valid_combo(chamber_id: str, omen_id: str, virtue_id: str, hero_id: str) -> bool:
    if chamber_id not in CHAMBERS or omen_id not in OMENS or virtue_id not in VIRTUES or hero_id not in HEROES:
        return False
    chamber = CHAMBERS[chamber_id]
    omen = OMENS[omen_id]
    virtue = VIRTUES[virtue_id]
    return omen.id in chamber.affords and virtue.grants == omen.need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for chamber_id in sorted(CHAMBERS):
        for omen_id in sorted(OMENS):
            for virtue_id in sorted(VIRTUES):
                for hero_id in sorted(HEROES):
                    if valid_combo(chamber_id, omen_id, virtue_id, hero_id):
                        combos.append((chamber_id, omen_id, virtue_id, hero_id))
    return combos


def explain_rejection(chamber_id: str, omen_id: str, virtue_id: str, hero_id: str) -> str:
    if chamber_id not in CHAMBERS:
        return f"Unknown dentist-office chamber {chamber_id!r}."
    if omen_id not in OMENS:
        return f"Unknown omen {omen_id!r}."
    if virtue_id not in VIRTUES:
        return f"Unknown virtue {virtue_id!r}."
    if hero_id not in HEROES:
        return f"Unknown hero {hero_id!r}."
    chamber = CHAMBERS[chamber_id]
    omen = OMENS[omen_id]
    virtue = VIRTUES[virtue_id]
    if omen.id not in chamber.affords:
        return f"{chamber.label} does not plausibly produce {omen.label}."
    if virtue.grants != omen.need:
        return (
            f"{virtue.label} cannot resolve {omen.label}; "
            f"this omen needs {omen.need}."
        )
    return "That mythic dentist-office story is outside the valid set."


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.chamber, params.omen, params.virtue, params.hero):
        raise StoryError(explain_rejection(params.chamber, params.omen, params.virtue, params.hero))

    world = World(params)
    hero_seed = HEROES[params.hero]
    chamber = CHAMBERS[params.chamber]
    omen = OMENS[params.omen]
    virtue = VIRTUES[params.virtue]

    hero = world.add(Entity("hero", "child", hero_seed.name, location=chamber.id))
    hero.note = hero_seed.trait
    hero.meters["fear"] = 0.0
    hero.meters["calm"] = 0.4
    hero.meters["truth"] = 0.0
    hero.meters["trust"] = 0.0
    hero.meters["stillness"] = 0.0
    hero.memes["wonder"] = 0.6
    hero.memes["misunderstanding"] = 0.0

    dentist = world.add(Entity("dentist", "dentist", "Doctor Sen", location=chamber.id))
    dentist.note = "keeper of the little tooth moons"
    dentist.memes["patience"] = 1.0
    dentist.memes["wisdom"] = 1.0

    candle = world.add(Entity("candle", "object", "vivid candle", location=chamber.id))
    candle.states.add("burning")
    candle.meters["glow"] = 1.0
    candle.meters["wax"] = 1.0
    candle.meters["transformed"] = 0.0
    candle.memes["guidance"] = 1.0

    sign = world.add(Entity("omen", "omen", omen.label, location=chamber.id))
    sign.states.add("misread")
    sign.meters["fearsome"] = 1.0
    sign.meters["understood"] = 0.0
    sign.note = omen.hidden_cause

    tooth = world.add(Entity("tooth", "tooth", "the sore tooth", location="mouth"))
    tooth.states.add("troubled")
    tooth.meters["trouble"] = 1.0
    tooth.meters["eased"] = 0.0

    token = world.add(Entity("token", "token", "plain wax", location=chamber.id))
    token.meters["formed"] = 0.0
    token.note = omen.transform_kind

    world.facts["chamber"] = chamber.id
    world.facts["omen"] = omen.id
    world.facts["virtue"] = virtue.id
    world.facts["moral"] = virtue.moral
    return world


def introduce(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    chamber = CHAMBERS[params.chamber]

    world.say(
        f"Long ago, in the old dentist office above the market square, {hero_seed.name}, a {hero_seed.trait} child, {chamber.entry_line}."
    )
    world.say(chamber.candle_line)
    world.say(
        "People in that town said each tooth carried a small moon inside it, and Doctor Sen was the keeper who helped those moons shine cleanly."
    )
    world.record("scene_introduced")


def misunderstanding(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    omen = OMENS[params.omen]
    hero = world.get("hero")

    world.break_para()
    world.say(f"Then {omen.vision}.")
    world.say(
        f"{hero_seed.name} drew in a breath and thought {omen.mistaken_belief}."
    )
    world.say(
        f"Fear ran through {pronoun_possessive(hero_seed.gender)} chest so quickly that even the brave little moons in {pronoun_possessive(hero_seed.gender)} mouth seemed to hide."
    )
    hero.meters["fear"] = 1.0
    hero.meters["calm"] = 0.0
    hero.memes["misunderstanding"] = 1.0
    world.record("omen_misread")


def teaching(world: World) -> None:
    params = world.params
    virtue = VIRTUES[params.virtue]

    world.say(virtue.teaching)
    world.say(
        "The child listened, because the office did not feel cruel anymore. It felt like a place where strange signs could be translated."
    )
    world.record("teaching_given")


def choose_virtue(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    virtue = VIRTUES[params.virtue]
    hero = world.get("hero")

    world.break_para()
    world.say(f"So {hero_seed.name} {virtue.action}.")
    world.say(virtue.dentist_help)
    hero.meters[virtue.grants] = 1.0
    hero.meters["calm"] = 1.0
    hero.meters["fear"] = 0.0
    hero.memes["misunderstanding"] = 0.0
    hero.memes["wonder"] += 0.6
    world.record("virtue_chosen")


def reveal_and_transform(world: World) -> None:
    params = world.params
    omen = OMENS[params.omen]
    hero_seed = HEROES[params.hero]
    candle = world.get("candle")
    sign = world.get("omen")
    tooth = world.get("tooth")
    token = world.get("token")

    world.say(
        f"Then the true cause stood in the open: {omen.hidden_cause}."
    )
    world.say(omen.dentist_reveal)
    world.say(omen.transform_sentence)
    world.say(
        f"{hero_seed.name} saw that the room had not been sending a threat at all. It had only been waiting for the right kind of goodness to clear the picture."
    )

    candle.meters["wax"] = 0.3
    candle.meters["transformed"] = 1.0
    candle.label = "vivid candle with a changed base"
    sign.states.discard("misread")
    sign.states.add("understood")
    sign.meters["fearsome"] = 0.0
    sign.meters["understood"] = 1.0
    tooth.states.discard("troubled")
    tooth.states.add("eased")
    tooth.meters["trouble"] = 0.0
    tooth.meters["eased"] = 1.0
    token.label = {
        "sleeping_lion": "wax lion",
        "pearl_drop": "wax pearl",
        "crescent_boat": "wax crescent boat",
    }[omen.transform_kind]
    token.meters["formed"] = 1.0
    world.facts["transformation"] = omen.transform_kind
    world.record("cause_revealed")
    world.record("candle_transformed")


def ending(world: World) -> None:
    params = world.params
    hero_seed = HEROES[params.hero]
    chamber = CHAMBERS[params.chamber]
    omen = OMENS[params.omen]
    virtue = VIRTUES[params.virtue]
    hero = world.get("hero")

    world.break_para()
    world.say(
        f"When the visit ended, {hero_seed.name} {chamber.exit_line}, feeling taller than when {pronoun_subject(hero_seed.gender)} had first come in."
    )
    world.say(omen.final_image)
    world.say(
        f"And from that day on, {hero_seed.name} remembered that {virtue.moral}."
    )
    hero.memes["wisdom"] += 1.0
    world.record("ending_image")


def tell(world: World) -> str:
    introduce(world)
    misunderstanding(world)
    teaching(world)
    choose_virtue(world)
    reveal_and_transform(world)
    ending(world)
    return world.render()


def generation_prompts(params: StoryParams) -> list[str]:
    hero = HEROES[params.hero]
    omen = OMENS[params.omen]
    virtue = VIRTUES[params.virtue]
    return [
        'Write a myth set in a dentist office that includes the words "candle" and "vivid".',
        f"Tell a child-sized myth where {hero.name} misunderstands {omen.label} and is changed by {virtue.label}.",
        "Write a story where a frightening sign becomes gentle once a child chooses the right moral act.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.params
    hero = HEROES[params.hero]
    omen = OMENS[params.omen]
    virtue = VIRTUES[params.virtue]
    return [
        QAItem(
            f"What did {hero.name} misunderstand in the dentist office?",
            f"{hero.name} saw how {omen.vision} and believed that {omen.mistaken_belief}. The sign felt dangerous only because fear reached the story before truth did.",
        ),
        QAItem(
            f"What was really causing the frightening sign?",
            f"The frightening sign was really caused because {omen.hidden_cause}. Once Doctor Sen helped carefully, the omen turned back into an ordinary sight with a clear cause.",
        ),
        QAItem(
            f"How did {hero.name} help solve the problem?",
            f"{hero.name} helped by choosing to {virtue.label}. That moral act gave Doctor Sen the chance to reveal the true cause instead of letting the misunderstanding grow.",
        ),
        QAItem(
            "How did the ending prove that the child had changed?",
            f"The ending proved it with a clear image: {omen.final_image} The transformed wax token showed that fear had turned into understanding inside the same room.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    params = world.params
    omen = OMENS[params.omen]
    virtue = VIRTUES[params.virtue]
    items = [
        QAItem(
            "What does a dentist do for children?",
            "A dentist checks teeth, helps clean them, and explains what is happening inside a child's mouth. That calm explanation can stop fear before it grows into a bigger story.",
        ),
        QAItem(
            "Why can a shadow or reflection look scary at first?",
            "Light can stretch small things into large shapes, especially when someone is already worried. A frightened mind often fills in danger before the eyes have all the facts.",
        ),
        QAItem(
            f"Why was {virtue.label} the right choice here?",
            f"It was the right choice because {NEED_EXPLANATIONS[omen.need]}. The moral action matched the problem instead of fighting the wrong thing.",
        ),
        QAItem(
            "Why is a transformed token a good ending image in a myth?",
            "A transformed token lets children see that an inner change has become physical and memorable. The object keeps the lesson visible after the fear is gone.",
        ),
        QAItem(
            "Why might a candle appear in a healing story?",
            "A candle can stand for clear seeing, patience, and care in a small room. Its steady light makes it a natural symbol for understanding arriving gently.",
        ),
    ]
    tags = set().union(OMENS[params.omen].tags, VIRTUES[params.virtue].tags, CHAMBERS[params.chamber].tags)
    selected: list[QAItem] = []
    for item in items:
        text = f"{item.question} {item.answer}".lower()
        if "shadow" in text and "shadow" not in tags and "screen" not in tags and "mirror" not in tags:
            continue
        if "reflection" in text and "water" not in tags and "mirror" not in tags:
            continue
        selected.append(item)
    return selected[:4]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = tell(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(C,O,V,H) :-
    chamber(C),
    omen(O),
    virtue(V),
    hero(H),
    affords(C,O),
    needs(O,N),
    grants(V,N).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for chamber in CHAMBERS.values():
        facts.append(asp.fact("chamber", chamber.id))
        for omen_id in chamber.affords:
            facts.append(asp.fact("affords", chamber.id, omen_id))
    for omen in OMENS.values():
        facts.append(asp.fact("omen", omen.id))
        facts.append(asp.fact("needs", omen.id, omen.need))
    for virtue in VIRTUES.values():
        facts.append(asp.fact("virtue", virtue.id))
        facts.append(asp.fact("grants", virtue.id, virtue.grants))
    for hero in HEROES.values():
        facts.append(asp.fact("hero", hero.id))
    return "\n".join(facts) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str]] = set()
    for model in asp.solve(asp_facts() + ASP_RULES):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(x) for x in atom))  # type: ignore[arg-type]
    return sorted(combos)


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        print("ASP/Python mismatch")
        print("Only Python:", sorted(py - lp))
        print("Only ASP:", sorted(lp - py))
        return 1
    for combo in sorted(py):
        generate(StoryParams(*combo, seed=17))
    print(f"OK: Python and ASP agree on {len(py)} valid mythic dentist-office stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chamber", choices=sorted(CHAMBERS))
    parser.add_argument("--omen", choices=sorted(OMENS))
    parser.add_argument("--virtue", choices=sorted(VIRTUES))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if (args.chamber is None or combo[0] == args.chamber)
        and (args.omen is None or combo[1] == args.omen)
        and (args.virtue is None or combo[2] == args.virtue)
        and (args.hero is None or combo[3] == args.hero)
    ]
    if not choices:
        chamber = args.chamber or sorted(CHAMBERS)[0]
        omen = args.omen or sorted(OMENS)[0]
        virtue = args.virtue or sorted(VIRTUES)[0]
        hero = args.hero or sorted(HEROES)[0]
        raise StoryError(explain_rejection(chamber, omen, virtue, hero))
    chamber, omen, virtue, hero = rng.choice(choices)
    seed = (args.seed if args.seed is not None else 1000) + index
    return StoryParams(chamber, omen, virtue, hero, seed)


def format_qa(title: str, items: list[QAItem]) -> list[str]:
    lines = [title]
    for item in items:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return lines


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print("PROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print()
        print("\n".join(format_qa("STORY QA", sample.story_qa)))
        print()
        print("\n".join(format_qa("WORLD KNOWLEDGE QA", sample.world_qa)))
    if trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        base_seed = args.seed if args.seed is not None else 900
        return [
            generate(StoryParams(chamber, omen, virtue, hero, base_seed + i))
            for i, (chamber, omen, virtue, hero) in enumerate(valid_combos(), start=1)
        ]

    target = max(1, args.n)
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    i = 0
    while len(samples) < target and attempts < target * 40:
        seed = base_seed + i
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed), index=i)
        sample = generate(params)
        i += 1
        attempts += 1
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Could not generate enough unique mythic dentist-office stories with those constraints.")
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_asp:
        print(asp_facts() + ASP_RULES)
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
        return 0

    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        print(str(exc))
        return 2

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples, start=1):
        header = ""
        if len(samples) > 1:
            header = (
                "=== candle_vivid_dentist_office_moral_value_transformation "
                f"#{idx} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
